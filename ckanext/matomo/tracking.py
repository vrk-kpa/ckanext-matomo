import logging
import datetime

from ckan.views.api import action as ckan_action
import ckan.plugins.toolkit as toolkit

from matomo_api import MatomoAPI

log = logging.getLogger(__name__)


def tracked_action(logic_function, ver=3):
    post_analytics('API / Action / {}'.format(logic_function))
    return ckan_action(logic_function, ver)


def post_analytics(action_name, download=False):
    now = datetime.datetime.now()
    event = {'action_name': action_name,
             'url': toolkit.request.url,
             'h': now.hour,
             'm': now.minute,
             's': now.second
             }
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
        api = MatomoAPI(matomo_url, matomo_site_id, token_auth=None)
        api.tracking(event)
