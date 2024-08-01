import logging
import datetime

from concurrent.futures import ThreadPoolExecutor

from ckan.views.api import action as ckan_action
import ckan.plugins.toolkit as toolkit

from ckanext.matomo.matomo_api import MatomoAPI

MAX_EVENTS_PER_MATOMO_REQUEST = 32
log = logging.getLogger(__name__)
tracking_executor = ThreadPoolExecutor(max_workers=1)


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


    headers = {}
    if toolkit.request.headers.get('DNT'):
        headers = {'dnt': toolkit.request.headers.get('DNT')}

    log.info('Logging tracking event: %s', event)
    tracking_executor.submit(matomo_track, event, headers)


# Required to be a free function to work with background jobs
def matomo_track(event, extra_headers=None):
    if extra_headers is None:
        extra_headers = {}

    # Gather events to send
    log = logging.getLogger('ckanext.matomo.tracking')
    test_mode = toolkit.config.get('ckanext.matomo.test_mode', False)

    if test_mode:
        log.info(f"Would send API event to Matomo: {event}")
        return

    log.info(f"Sending API event to Matomo: {event}")
    matomo_url = toolkit.config.get(u'ckanext.matomo.domain')
    matomo_site_id = toolkit.config.get(u'ckanext.matomo.site_id')
    token_auth = toolkit.config.get('ckanext.matomo.token_auth')
    api = MatomoAPI(matomo_url, matomo_site_id, token_auth=token_auth)
    r = api.tracking(event, extra_headers=extra_headers)
    if not r.ok:
        log.warn('Error when posting tracking events to matomo: %s %s' % (r.status_code, r.reason))
        log.warn('With request: %s' % r.url)
