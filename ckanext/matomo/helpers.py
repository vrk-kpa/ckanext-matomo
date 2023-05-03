from datetime import date, datetime
from flask import request
from typing import Dict, Any, Union, List, Tuple
from ckan.plugins.toolkit import render_snippet, config
from ckan.plugins import toolkit as tk
from ckanext.matomo.reports import last_calendar_period, get_report_years
from ckanext.matomo.model import PackageStats, ResourceStats


def matomo_snippet():
    data = {
        "matomo_domain": config.get('ckanext.matomo.domain'),
        "matomo_script_domain": config.get('ckanext.matomo.script_domain', config.get('ckanext.matomo.domain')),
        "matomo_site_id": config.get('ckanext.matomo.site_id')
    }

    return render_snippet("matomo/snippets/matomo.html", data)


# Get the organization specific report url
def get_organization_url(organization: str) -> str:
    if not organization:
        return request.path
    organization_path: str = "%s/%s" % (request.path, organization)
    params = dict(list(request.args.items()))
    time: Union[str, None] = params.get('time')
    if time:
        organization_path = "%s?time=%s" % (organization_path, time)
    return tk.url_for(organization_path)


def get_visits_for_resource(id: str) -> Dict[str, Any]:
    return ResourceStats.get_all_visits(id)


def get_visits_for_dataset(id: str) -> Dict[str, Any]:
    return PackageStats.get_all_visits(id)


def get_download_count_for_dataset(id: str, time: str) -> int:
    start_date, end_date = get_date_range(time)
    return ResourceStats.get_download_count_for_dataset(id, start_date, end_date)


def get_visit_count_for_dataset(id: str, time: str) -> int:
    start_date, end_date = get_date_range(time)
    return PackageStats.get_visit_count_for_dataset(id, start_date, end_date)


def format_date(datestr) -> str:
    dateobj: date = date.fromisoformat(datestr)
    return dateobj.strftime('%d-%m-%Y')


def get_date_range(time: Union[str, None] = None) -> Tuple[datetime, datetime]:
    if not time:
        params = dict(list(request.args.items()))
        time = params.get('time', 'month')
    return last_calendar_period(time)


def get_years() -> List[str]:
    return get_report_years()
