from datetime import date, datetime, timedelta
from flask import request
from typing import List, Tuple, Optional
from ckan.plugins.toolkit import render_snippet, config
from ckan.plugins import toolkit as tk
from ckanext.matomo.utils import last_calendar_period, get_report_years
from ckanext.matomo.model import PackageStats, ResourceStats, get_end_of_last_week, get_beginning_of_next_week
from ckanext.matomo.types import Visits


def matomo_snippet():
    data = {
        "matomo_domain": config.get('ckanext.matomo.domain'),
        "matomo_script_domain": config.get('ckanext.matomo.script_domain', config.get('ckanext.matomo.domain')),
        "matomo_site_id": config.get('ckanext.matomo.site_id'),
        "matomo_tracker_filename": config.get('ckanext.matomo.tracker_filename', "matomo.php"),
        "matomo_script_filename": config.get('ckanext.matomo.script_filename', "matomo.js")
    }

    return render_snippet("matomo/snippets/matomo.html", data)


# Get the organization specific report url
def get_organization_url(organization: str) -> str:
    if not organization:
        return request.path
    organization_path: str = "%s/%s" % (request.path, organization)
    params = dict(list(request.args.items()))
    time: Optional[str] = params.get('time')
    if time:
        organization_path = "%s?time=%s" % (organization_path, time)
    return tk.url_for(organization_path)


def get_visits_for_dataset(id: str) -> Visits:
    return PackageStats.get_all_visits(id)


def get_visits_for_resource(id: str) -> Visits:
    return ResourceStats.get_all_visits(id)

def get_downloads_in_date_range_for_resource(id: str) -> Visits:
    end_of_last_week = get_end_of_last_week(datetime.now())
    start_date = get_beginning_of_next_week(end_of_last_week.replace(hour=0, minute=0, second=0, microsecond=0)
                                            - timedelta(days=365))
    return ResourceStats.get_downloads_in_date_range_by_id(id, start_date, end_of_last_week)

def get_download_count_for_dataset(id: str, time: str) -> int:
    start_date, end_date = get_date_range(time)
    return ResourceStats.get_download_count_for_dataset(id, start_date, end_date)


def get_visit_count_for_dataset(id: str, time: str) -> int:
    start_date, end_date = get_date_range(time)
    return PackageStats.get_visit_count_for_dataset(id, start_date, end_date)


def get_download_count_for_resource(id: str, time: str) -> int:
    start_date, end_date = get_date_range(time)
    return ResourceStats.get_stat_counts_by_id_and_date_range(id, start_date, end_date).get('downloads', 0)


def get_visit_count_for_resource(id: str, time: str) -> int:
    start_date, end_date = get_date_range(time)
    return ResourceStats.get_stat_counts_by_id_and_date_range(id, start_date, end_date).get('visits', 0)


def format_date(datestr) -> str:
    dateobj: date = date.fromisoformat(datestr)
    return dateobj.strftime('%d-%m-%Y')


def get_date_range(time: Optional[str] = None) -> Tuple[datetime, datetime]:
    if not time:
        params = dict(list(request.args.items()))
        time = params.get('time', 'month')
    return last_calendar_period(time)


def get_years() -> List[str]:
    return get_report_years()


def show_download_graph():
    return tk.asbool(config.get('ckanext-matomo.show_download_graph', True))


def get_current_date() -> datetime:
    return datetime.now()

