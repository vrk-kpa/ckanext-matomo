import datetime
import ckan.plugins.toolkit as toolkit
from ckanext.matomo.matomo_api import MatomoAPI
from ckanext.matomo.model import PackageStats, ResourceStats, AudienceLocationDate, SearchStats


DATE_FORMAT = '%Y-%m-%d'


def fetch(dryrun, since, until):
    since_date = (datetime.datetime.strptime(since, DATE_FORMAT) if since else
                  PackageStats.get_latest_update_date()).date()
    until_date = datetime.datetime.strptime(until, DATE_FORMAT).date() if until else datetime.date.today()

    if since_date > until_date:
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

    for date_str, date_statistics in dataset_page_statistics.items():
        date = datetime.datetime.strptime(date_str, DATE_FORMAT)
        updated_package_ids = set()
        updated_package_ids_by_date[date_str] = updated_package_ids

        for package_name, stats_list in date_statistics.items():
            try:
                package = package_show({'ignore_auth': True}, {'id': package_name})
            except toolkit.ObjectNotFound:
                print('Package "{}" not found, skipping...'.format(package_name))
                continue
            package_id = package['id']
            visits = sum(stats.get('nb_hits', 0) for stats in stats_list)
            entrances = sum(int(stats.get('entry_nb_visits', 0)) for stats in stats_list)
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

    for date_str, date_statistics in resource_download_statistics.items():
        date = datetime.datetime.strptime(date_str, DATE_FORMAT)
        updated_package_ids = updated_package_ids_by_date.get(date_str, set())

        for package_id, stats_list in date_statistics.items():
            if package_id in updated_package_ids:
                continue

            downloads = sum(stats.get('nb_hits', 0) for stats in stats_list)
            if dryrun:
                print('Would update download stats: package_id={}, date={}, downloads={}'
                      .format(package_id, date, downloads))
            else:
                PackageStats.update_downloads(package_id, date, downloads)

    # Resource page views

    resource_page_statistics = api.resource_page_statistics(**params)

    for date_str, date_statistics in resource_page_statistics.items():
        date = datetime.datetime.strptime(date_str, DATE_FORMAT)
        for resource_id, stats_list in date_statistics.items():
            visits = sum(stats.get('nb_hits', 0) for stats in stats_list)
            if dryrun:
                print('Would create or update: resource_id={}, date={}, visits={}'.format(resource_id, date, visits))
            else:
                ResourceStats.update_visits(resource_id, date, visits)

    # Visits by country

    visits_by_country = api.visits_by_country(**params)

    for date_str, date_statistics in visits_by_country.items():
        date = datetime.datetime.strptime(date_str, DATE_FORMAT)
        for country_stats in date_statistics:
            country_name = country_stats.get('label', '(not set)')
            visits = country_stats.get('nb_visits', 0)

            if dryrun:
                print("Would update country statistics: date={}, country={}, visits={}"
                      .format(date, country_name, visits))
            else:
                AudienceLocationDate.update_visits(country_name, date, visits)

    # Search terms

    search_terms = api.search_terms(**params)

    for date_str, date_statistics in search_terms.items():
        date = datetime.datetime.strptime(date_str, DATE_FORMAT)
        for search_term_stats in date_statistics:
            search_term = search_term_stats.get('label', '(not set)')
            count = search_term_stats.get('nb_hits', 0)

            if dryrun:
                print("Would search term statistics: date={}, search_term={}, count={}"
                      .format(date, search_term, count))
            else:
                SearchStats.update_search_term_count(search_term, date, count)


def init_db():
    from ckanext.matomo.model import init_tables
    import ckan.model as model
    init_tables(model.meta.engine)
