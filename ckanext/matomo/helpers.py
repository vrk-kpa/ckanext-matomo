from ckan.plugins.toolkit import render_snippet, config
import datetime
from ckan.plugins import toolkit as tk


def matomo_snippet():
    data = {
        "matomo_domain": config.get('ckanext.matomo.domain'),
        "matomo_script_domain": config.get('ckanext.matomo.script_domain', config.get('ckanext.matomo.domain')),
        "matomo_site_id": config.get('ckanext.matomo.site_id')
    }

    return render_snippet("matomo/snippets/matomo.html", data)


# Get the organization specific report url
def get_organization_url(organization):
    from flask import request
    if not organization:
        return request.path
    organization_path = "%s/%s" % (request.path, organization)
    params = dict(list(request.args.items()))
    time = params.get('time')
    if time:
        organization_path = "%s?time=%s" % (organization_path, time)
    return tk.url_for(organization_path)


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


def get_download_count_for_dataset_during_last_12_months(id):
    # Downloads are visits for the Resource object.
    # This is why a 'get_visits' method is called.
    from ckanext.matomo.model import ResourceStats

    return ResourceStats.get_download_count_for_dataset_during_last_12_months(id)


def get_download_count_for_dataset_during_last_30_days(id):
    # Downloads are visits for the Resource object.
    # This is why a 'get_visits' method is called.
    from ckanext.matomo.model import ResourceStats

    return ResourceStats.get_download_count_for_dataset_during_last_30_days(id)


def get_visit_count_for_dataset_during_last_12_months(id):
    # Downloads are visits for the Resource object.
    # This is why a 'get_visits' method is called.
    from ckanext.matomo.model import PackageStats

    return PackageStats.get_visit_count_for_dataset_during_last_12_months(id)


def get_visit_count_for_dataset_during_last_30_days(id):
    # Downloads are visits for the Resource object.
    # This is why a 'get_visits' method is called.
    from ckanext.matomo.model import PackageStats

    return PackageStats.get_visit_count_for_dataset_during_last_30_days(id)


def get_visit_count_for_resource_during_last_12_months(id):
    from ckanext.matomo.model import ResourceStats

    return ResourceStats.get_visit_count_for_resource_during_last_12_months(id)


def get_visit_count_for_resource_during_last_30_days(id):
    from ckanext.matomo.model import ResourceStats

    return ResourceStats.get_visit_count_for_resource_during_last_30_days(id)


def get_download_count_for_resource_during_last_12_months(id):
    from ckanext.matomo.model import ResourceStats

    return ResourceStats.get_download_count_for_resource_during_last_12_months(id)


def get_download_count_for_resource_during_last_30_days(id):
    from ckanext.matomo.model import ResourceStats

    return ResourceStats.get_download_count_for_resource_during_last_30_days(id)


def format_date(datestr):
    date = datetime.date.fromisoformat(datestr)
    return date.strftime('%d-%m-%Y')
