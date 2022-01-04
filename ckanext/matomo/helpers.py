from ckan.plugins.toolkit import render_snippet, config
import datetime


def matomo_snippet():
    data = {
        "matomo_domain": config.get('ckanext.matomo.domain'),
        "matomo_script_domain": config.get('ckanext.matomo.script_domain', config.get('ckanext.matomo.domain')),
        "matomo_site_id": config.get('ckanext.matomo.site_id')
    }

    return render_snippet("matomo/snippets/matomo.html", data)


def get_visits_for_resource(id):
    from ckanext.matomo.model import ResourceStats

    return ResourceStats.get_all_visits(id)


def get_visits_for_dataset(id):

    from ckanext.matomo.model import PackageStats

    return PackageStats.get_all_visits(id)


def get_visits_count_for_dataset_during_last_year(id):

    from ckanext.matomo.model import PackageStats

    return len(PackageStats.get_visits_during_year(id, datetime.datetime.now().year - 1))


def get_download_count_for_dataset_during_last_year(id):
    # Downloads are visits for the Resource object.
    # This is why a 'get_visits' method is called.
    from ckanext.matomo.model import ResourceStats
    return len(ResourceStats.get_visits_during_last_calendar_year_by_dataset_id(id))
