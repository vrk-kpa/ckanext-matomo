import datetime
from urllib.parse import unquote
import re
import ckan.plugins.toolkit as toolkit
from ckanext.matomo.matomo_api import MatomoAPI
from ckanext.matomo.model import PackageStats, ResourceStats, AudienceLocationDate, SearchStats
from typing import Dict, Any, List

DATE_FORMAT = '%Y-%m-%d'

log = __import__('logging').getLogger(__name__)

def fetch(dryrun, since, until, dataset):
    if since:
        since_date = datetime.datetime.strptime(since, DATE_FORMAT).date()
    else:
        latest_update_datetime = PackageStats.get_latest_update_date()
        if latest_update_datetime is not None:
            since_date = latest_update_datetime.date()
        else:
            since_date = 'lastYear'

    until_date = datetime.datetime.strptime(until, DATE_FORMAT).date() if until else datetime.date.today()

    if isinstance(since_date, datetime.date) and isinstance(until_date, datetime.date) and since_date > until_date:
        log.info('Start date must not be greater than end date')
        return

    matomo_url = toolkit.config.get('ckanext.matomo.api_domain') or toolkit.config.get('ckanext.matomo.domain')
    matomo_site_id = toolkit.config.get('ckanext.matomo.site_id')
    matomo_token_auth = toolkit.config.get('ckanext.matomo.token_auth')
    api = MatomoAPI(matomo_url, matomo_site_id, matomo_token_auth)
    params = {'period': 'day', 'date': MatomoAPI.date_range(since_date, until_date)}
    package_show = toolkit.get_action('package_show')
    resource_show = toolkit.get_action('resource_show')

    # Dataset stats

    dataset_page_statistics: Dict[str, Any] = api.dataset_page_statistics(**params, dataset=dataset)

    pkg = None
    if dataset:
        try:
            pkg = package_show({'ignore_auth': True}, {'id': dataset})
        except toolkit.ObjectNotFound:
            log.info("Given dataset: %s not found" % dataset)
            pass


    # Resource downloads use package id in its url
    resource_download_statistics: Dict[str, Any] = api.resource_download_statistics(**params,
                                                                                    dataset=pkg['id'] if pkg else None)
    package_show_events: Dict[str, Any] = api.events(**params, filter_pattern='package_show')

    updated_package_ids_by_date = {}

    # Parse visits for datasets
    for date_str, date_statistics in dataset_page_statistics.items():
        date = datetime.datetime.strptime(date_str, DATE_FORMAT)
        updated_package_ids = set()
        updated_package_ids_by_date[date_str] = updated_package_ids

        for package_name, stats_list in date_statistics.items():
            package_name = package_name.split('?')[0]
            if not package_name.strip():
                continue

            try:
                try:
                    package = package_show({'ignore_auth': True}, {'id': package_name})
                except toolkit.ObjectNotFound:
                    log.info('Package "{}" not found, skipping...'.format(package_name))
                    continue
                if package.get('type') == 'dataset':
                    package_id: str = package['id']
                    visits: int = sum(int(stats.get('nb_hits', 0)) for stats in stats_list)
                    entrances: int = sum(int(stats.get('entry_nb_visits', 0)) for stats in stats_list)

                    # Check if there's download stats for resources included in this package
                    package_resources_statistics: Dict[str, Any] = resource_download_statistics.get(date_str, {})\
                        .get(package_id, {})
                    downloads: int = sum(int(stats.get('nb_hits', 0))
                                    for resource_stats_list in package_resources_statistics.values()
                                    for stats in resource_stats_list)

                    # Check if there's event stats (API usage / 'package_show') for this package
                    package_event_statistics: List[Dict[str, Any]] = [event for event in package_show_events.get(date_str, [])
                                                                       if package_name in event.get('Events_EventName')
                                                                        or package_id in event.get('Events_EventName')]
                    events: int = sum(int(stats.get('nb_events', 0))
                                    for stats in package_event_statistics)

                    if dryrun:
                        log.info('Would create or update: package_id={}, date={}, visits={}, '
                                 'entrances={}, downloads={}, events={}'
                            .format(package_id, date, visits, entrances, downloads, events))
                    else:
                        PackageStats.create_or_update(package_id, date, visits, entrances, downloads, events)

                    updated_package_ids.add(package_id)
            except Exception as e:
                log.exception('Error updating dataset statistics for {}: {}'.format(package_name, e))

    # Loop resources download stats (as a fallback if dataset had no stats)
    for date_str, date_statistics in resource_download_statistics.items():
        date = datetime.datetime.strptime(date_str, DATE_FORMAT)
        updated_package_ids = updated_package_ids_by_date.get(date_str, set())

        for package_id, stats_list in date_statistics.items():
            try:
                package = package_show({'ignore_auth': True}, {'id': package_id})
            except toolkit.ObjectNotFound:
                log.info('Package "{}" not found, skipping...'.format(package_id))
                continue

            # Add download-stats for every resources
            for resource_id, resource_stats in stats_list.items():
                try:
                    resource_show({'ignore_auth': True}, {'id': resource_id})
                except toolkit.ObjectNotFound:
                    log.info('Resource "{}" not found, skipping...'.format(resource_id))
                    continue
                try:
                    downloads = sum(int(stats.get('nb_hits', 0)) for stats in resource_stats)
                    if dryrun:
                        log.info('Would update downloads stats for resource: package_id={}, '
                                 'resource_id={}, date={}, downloads={}'
                              .format(package_id, resource_id, date, downloads))
                    else:
                        ResourceStats.update_downloads(resource_id, date, downloads)
                except Exception as e:
                    log.exception('Error updating resource statistics for {}: {}'.format(resource_id, e))

            # Dataset had no analytics for the day, parse download statistics for package
            if package_id not in updated_package_ids:

                try:
                    downloads = sum(int(stats.get('nb_hits', 0)) for stats_lists in stats_list.values()
                                    for stats in stats_lists)

                    if dryrun:
                        log.info('Would update download stats: package_id={}, date={}, downloads={}'
                            .format(package_id, date, downloads))
                    else:
                        PackageStats.update_downloads(package_id, date, downloads)
                except Exception as e:
                    log.exception('Error updating download statistics for {}: {}'.format(package_id, e))

    # Loop API event stats (as a fallback if dataset had no stats)
    for date_str, date_statistics in package_show_events.items():
        date = datetime.datetime.strptime(date_str, DATE_FORMAT)
        updated_package_ids = updated_package_ids_by_date.get(date_str, set())

        for stats in date_statistics:
            regex = re.compile('.*id=([a-zA-Z0-9-_]*)&?.*$', re.I)
            match = regex.match(stats.get('Events_EventName'))
            if match and match[1]:
                if dataset and dataset != match[1]:
                    continue
                package_id_or_name = match[1]
                try:
                    package = package_show({'ignore_auth': True}, {'id': package_id_or_name})
                except toolkit.ObjectNotFound:
                    log.info('Package "{}" not found, skipping...'.format(package_id_or_name))
                    continue
                package_id = package.get('id')
                if package_id and package_id not in updated_package_ids:
                    # Add event-stats for package
                    try:
                        events = stats.get('nb_events', 0)
                        if dryrun:
                            log.info('Would create or update: package_id={}, date={}, events={}'
                                .format(package_id, date, events))
                        else:
                            PackageStats.update_events(package_id, date, events)
                    except Exception as e:
                        log.exception('Error updating API event statistics for {}: {}'.format(package_id, e))

    # Resource page statistics
    resource_page_statistics = api.resource_page_statistics(**params, dataset=dataset)
    # pattern is used as regex so it includes both datastore_search and datastore_search_sql
    datastore_search_sql_events: Dict[str, Any] = api.events(**params, filter_pattern='datastore_search')

    for date_str, date_statistics in resource_page_statistics.items():
        date = datetime.datetime.strptime(date_str, DATE_FORMAT)
        for resource_id, stats_list in date_statistics.items():
            try:
                resource_show({'ignore_auth': True}, {'id': resource_id})
            except toolkit.ObjectNotFound:
                log.info('Resource "{}" not found, skipping...'.format(resource_id))
                continue
            try:
                visits = sum(int(stats.get('nb_hits', 0)) for stats in stats_list)
                if dryrun:
                    log.info('Would create or update: resource_id={}, date={}, visits={}'.format(resource_id, date, visits))
                else:
                    ResourceStats.update_visits(resource_id, date, visits)
            except Exception as e:
                log.exception('Error updating resource statistics for {}: {}'.format(resource_id, e))

    # Resource datastore search sql events (API events)
    for date_str, date_statistics in datastore_search_sql_events.items():
        date = datetime.datetime.strptime(date_str, DATE_FORMAT)

        for event in date_statistics:
            resource_id = None
            if event.get('Events_EventAction') == "datastore_search_sql":
                regex = re.compile('^.*FROM "([a-zA-Z0-9-_]*)".*$', re.I|re.M)
                match = regex.search(unquote(event.get('Events_EventName')))
                if match and match[1]:
                    resource_id = match[1]
            elif event.get('Events_EventAction') == "datastore_search":
                regex = re.compile('.*resource_id=([a-zA-Z0-9-_]*)&?.*$', re.I)
                match = regex.search(unquote(event.get('Events_EventName')))
                if match and match[1]:
                    resource_id = match[1]
            else:
                log.info("No resource_id found from EventName, skipping...")
                continue

            try:
                resource = resource_show({'ignore_auth': True}, {'id': resource_id})
                if pkg:
                    if pkg['id'] != resource['package_id']:
                        continue
            except toolkit.ObjectNotFound:
                log.info('Resource "{}" not found, skipping...'.format(resource_id))
                continue
            # Add event stats for resourcee
            try:
                events = event.get('nb_events', 0)
                if dryrun:
                    log.info('Would create or update: resource_id={}, date={}, events={}'
                        .format(resource_id, date, events))
                else:
                    ResourceStats.update_events(resource_id, date, events)
            except Exception as e:
                log.exception('Error updating API event statistics for resource {}: {}'.format(resource_id, e))

    if not dataset:
        # Visits by country
        visits_by_country = api.visits_by_country(**params)

        for date_str, date_statistics in visits_by_country.items():
            date = datetime.datetime.strptime(date_str, DATE_FORMAT)
            for country_stats in date_statistics:
                country_name = country_stats.get('label', '(not set)')
                visits = country_stats.get('nb_visits', 0)

                try:
                    if dryrun:
                        log.info("Would update country statistics: date={}, country={}, visits={}"
                              .format(date, country_name, visits))
                    else:
                        AudienceLocationDate.update_visits(country_name, date, visits)
                except Exception as e:
                    log.exception('Error updating country statistics for {}: {}'.format(country_name, e))

        # Search terms
        search_terms = api.search_terms(**params)

        for date_str, date_statistics in search_terms.items():
            date = datetime.datetime.strptime(date_str, DATE_FORMAT)
            for search_term_stats in date_statistics:
                search_term = search_term_stats.get('label', '(not set)')
                count = search_term_stats.get('nb_visits', 0)

                try:
                    if dryrun:
                        log.info("Would search term statistics: date={}, search_term={}, count={}"
                              .format(date, search_term, count))
                    else:
                        SearchStats.update_search_term_count(search_term, date, count)
                except Exception as e:
                    log.exception('Error updating search term statistics for {}: {}'.format(search_term, e))


def init_db():
    from ckanext.matomo.model import init_tables
    import ckan.model as model
    init_tables(model.meta.engine)
