import logging
import datetime

from ckan.views.api import action as ckan_action
import ckan.plugins.toolkit as toolkit

from ckanext.matomo.matomo_api import MatomoAPI

log = logging.getLogger(__name__)


def tracked_action(logic_function, ver=3):
    post_analytics('API', '{}'.format(logic_function), toolkit.request.url)
    return ckan_action(logic_function, ver)


def post_analytics(category, action, name, download=False):
    now = datetime.datetime.now()

    user_agent = toolkit.request.user_agent.string
    if toolkit.config.get(u'ckanext.matomo.ignored_user_agents', '') == user_agent:
        return

    referrer = toolkit.request.referrer or ''

    event = {'e_c': category,
             'e_a': action,
             'e_n': name,
             'url': toolkit.request.url,
             'h': now.hour,
             'm': now.minute,
             's': now.second,
             'ua': user_agent,
             'urlref': referrer
             }

    # Overriding ip address requires write access to matomo
    if toolkit.config.get('ckanext.matomo.token_auth', '') != '':
        visitor_ip = toolkit.request.headers.get('X-Forwarded-For')
        if visitor_ip:
            # X-Forwarded-For might have multiple ip addresses separated by comma
            visitor_ip = visitor_ip.split(',')[0]
        else:
            visitor_ip = toolkit.request.remote_addr

        event.update({'cip': visitor_ip})

    user_id = next((v for k, v in toolkit.request.cookies.items() if k.startswith('_pk_id')), None)
    if user_id:
        event['_id'] = user_id.split('.', 1)[0]
    if download:
        event['download'] = event['url']

    matomo_url = toolkit.config.get(u'ckanext.matomo.domain')
    matomo_site_id = toolkit.config.get(u'ckanext.matomo.site_id')
    test_mode = toolkit.config.get('ckanext.matomo.test_mode', False)

    log.info('Logging tracking event: %s', event)
    toolkit.enqueue_job(matomo_track, [matomo_url, matomo_site_id, event, test_mode], queue='priority')


# Required to be a free function to work with background jobs
def matomo_track(matomo_url, matomo_site_id, event, test_mode):
    log = logging.getLogger('ckanext.matomo')
    if test_mode:
        log.warn("Would send API event to Matomo: %s", event)
    else:
        log.warn("Sending API event to Matomo: %s", event)
        api = MatomoAPI(matomo_url, matomo_site_id, token_auth=toolkit.config.get('ckanext.matomo.token_auth'))
        api.tracking(event)
