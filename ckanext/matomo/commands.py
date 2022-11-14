import datetime
import ckan.plugins.toolkit as toolkit


try:
    from collections import OrderedDict  # from python 2.7
except ImportError:
    from sqlalchemy.util import OrderedDict

from ckanext.matomo.matomo_api import MatomoAPI
from ckanext.matomo.model import PackageStats, ResourceStats, AudienceLocationDate, SearchStats
import logging
log = logging.getLogger(__name__)

DATE_FORMAT = '%Y-%m-%d'


def fetch(dryrun, since, until):
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
        print('Start date must not be greater than end date')
        return

    matomo_url = toolkit.config.get('ckanext.matomo.domain')
    matomo_site_id = toolkit.config.get('ckanext.matomo.site_id')
    matomo_token_auth = toolkit.config.get('ckanext.matomo.token_auth')

    api = MatomoAPI(matomo_url, matomo_site_id, matomo_token_auth)
    params = {'period': 'day', 'date': MatomoAPI.date_range(since_date, until_date)}
    package_show = toolkit.get_action('package_show')

    # Dataset stats

    dataset_page_statistics = api.dataset_page_statistics(**params)
    resource_download_statistics = api.resource_download_statistics(**params)
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
                    print('Package "{}" not found, skipping...'.format(package_name.encode('iso-8859-1')))
                    continue
                package_id = package['id']
                visits = sum(stats.get('nb_hits', 0) for stats in stats_list)
                entrances = sum(int(stats.get('entry_nb_visits', 0)) for stats in stats_list)

                # Check if there's download stats for resources included in this package
                package_resources_statistics = resource_download_statistics.get(date_str, {}).get(package_id, {})
                downloads = sum(stats.get('nb_hits', 0)
                                for resource_stats_list in package_resources_statistics.values()
                                for stats in resource_stats_list)

                if dryrun:
                    print('Would create or update: package_id={}, date={}, visits={}, entrances={}, downloads={}'
                          .format(package_id, date, visits, entrances, downloads))
                else:
                    PackageStats.create_or_update(package_id, date, visits, entrances, downloads)

                updated_package_ids.add(package_id)
            except Exception as e:
                print('Error updating dataset statistics for {}: {}'.format(package_name, e))

    # Loop resources download stats (as a fallback if dataset had no stats)
    for date_str, date_statistics in resource_download_statistics.items():
        date = datetime.datetime.strptime(date_str, DATE_FORMAT)
        updated_package_ids = updated_package_ids_by_date.get(date_str, set())

        for package_id, stats_list in date_statistics.items():
            if package_id in updated_package_ids:
                # Add download-stats for every resources
                for resource_id, resource_stats in stats_list.items():
                    try:
                        downloads = sum(stats.get('nb_hits', 0) for stats in resource_stats)
                        if dryrun:
                            print('Would create or update: resource_id={}, date={}, downloads={}'
                                  .format(resource_id, date, visits))
                        else:
                            ResourceStats.update_downloads(resource_id, date, downloads)
                    except Exception as e:
                        print('Error updating resource statistics for {}: {}'.format(resource_id, e))

                # If dataset is already handled, don't parse again package stats
                continue

            try:
                downloads = sum(stats.get('nb_hits', 0) for stats_lists in stats_list.values() for stats in stats_lists)

                if dryrun:
                    print('Would update download stats: package_id={}, date={}, downloads={}'
                          .format(package_id, date, downloads))
                else:
                    PackageStats.update_downloads(package_id, date, downloads)
            except Exception as e:
                print('Error updating download statistics for {}: {}'.format(package_id, e))

    # Resource page views

    resource_page_statistics = api.resource_page_statistics(**params)

    for date_str, date_statistics in resource_page_statistics.items():
        date = datetime.datetime.strptime(date_str, DATE_FORMAT)
        for resource_id, stats_list in date_statistics.items():
            try:
                visits = sum(stats.get('nb_hits', 0) for stats in stats_list)
                if dryrun:
                    print('Would create or update: resource_id={}, date={}, visits={}'.format(resource_id, date, visits))
                else:
                    ResourceStats.update_visits(resource_id, date, visits)
            except Exception as e:
                print('Error updating resource statistics for {}: {}'.format(resource_id, e))

    # Visits by country

    visits_by_country = api.visits_by_country(**params)

    for date_str, date_statistics in visits_by_country.items():
        date = datetime.datetime.strptime(date_str, DATE_FORMAT)
        for country_stats in date_statistics:
            country_name = country_stats.get('label', '(not set)')
            visits = country_stats.get('nb_visits', 0)

            try:
                if dryrun:
                    print("Would update country statistics: date={}, country={}, visits={}"
                          .format(date, country_name, visits))
                else:
                    AudienceLocationDate.update_visits(country_name, date, visits)
            except Exception as e:
                print('Error updating country statistics for {}: {}'.format(country_name, e))

    # Search terms

    search_terms = api.search_terms(**params)

    for date_str, date_statistics in search_terms.items():
        date = datetime.datetime.strptime(date_str, DATE_FORMAT)
        for search_term_stats in date_statistics:
            search_term = search_term_stats.get('label', '(not set)')
            count = search_term_stats.get('nb_hits', 0)

            try:
                if dryrun:
                    print("Would search term statistics: date={}, search_term={}, count={}"
                          .format(date, search_term, count))
                else:
                    SearchStats.update_search_term_count(search_term, date, count)
            except Exception as e:
                print('Error updating search term statistics for {}: {}'.format(search_term, e))


def init_db():
    from ckanext.matomo.model import init_tables
    import ckan.model as model
    init_tables(model.meta.engine)
