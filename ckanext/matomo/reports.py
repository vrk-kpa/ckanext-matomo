from datetime import datetime, timedelta
from typing import List, Generator, Dict, Union, Any
from ckanext.report import lib as report
from ckanext.report.helpers import organization_list as report__organization_list
from ckanext.matomo.model import PackageStats, ResourceStats, AudienceLocationDate, SearchStats
from ckanext.matomo.utils import get_report_years, last_calendar_period

log = __import__('logging').getLogger(__name__)


try:
    from ckan.common import OrderedDict
except ImportError:
    from collections import OrderedDict


def time_option_combinations() -> Generator[Dict[str, str], None, None]:
    time_options: list[str] = ['week', 'month', 'year']
    time_options.extend(get_report_years())
    for time in time_options:
        yield {'time': time}


def org_and_time_option_combinations() -> Generator[Dict[str, Union[str, None]], None, None]:
    time_options: list[str] = ['week', 'month', 'year']
    time_options.extend(get_report_years())
    org_options: Generator[Union[Any, None], None, None] = report.all_organizations(include_none=True)
    for org in org_options:
        for time in time_options:
            yield {'organization': org, 'time': time}


def matomo_organization_list(start_date, end_date, descending=True, sort_by="total_visits") -> List[Any]:
    # Fetch all organizations which have at least 1 dataset
    organizations_with_datasets = report__organization_list(only_orgs_with_packages=True)
    # Fetch total visits per package within given date range
    package_stats: List[Dict[str, Any]] = PackageStats.get_total_visits(start_date, end_date, descending)

    # Count org specific sums
    totals_by_organization: Dict[str, Any] = {}
    for stat in package_stats:
        org: Union[Dict[str, Any], None] = totals_by_organization.get(stat['owner_org'])
        if org:
            org['visits'] += stat['visits']
            org['entrances'] += stat['entrances']
            org['downloads'] += stat['downloads']
        else:
            totals_by_organization[stat['owner_org']] = {'visits': stat['visits'],
                                                         'entrances': stat['entrances'],
                                                         'downloads': stat['downloads']}

    # Format into list of org dicts with stats totals
    organizations: List[Dict[str, Any]] = []
    for organization in organizations_with_datasets:
        org_id: str = organization.get('id', '')
        stats: Dict[str, Any] = totals_by_organization.get(org_id, {})
        organizations.append({
            "organization_name": organization.get('name'),
            "organization_title": organization.get('title'),
            "organization_title_translated": organization.get('title_translated'),
            "total_visits": stats.get('visits', 0),
            "total_downloads": stats.get('downloads', 0),
            "total_entrances": stats.get('entrances', 0)
            })

    return sorted(organizations, key=lambda organization: organization[sort_by], reverse=descending)


def matomo_dataset_report(organization: str, time: str) -> Dict[str, Any]:
    '''
    Generates report based on matomo data.
    Total sum of package visits per organization or number of views per package for selected organization
    '''
    organization_name: str = organization
    start_date, end_date = last_calendar_period(time)

    # Return list of all organizations with packages if an organization is not given
    if organization_name is None:
        return {
            'report_name': 'matomo-dataset',
            'table': matomo_organization_list(start_date, end_date, descending=True, sort_by='total_visits')
        }
    else:
        # get given organizations datasets with the popularity statistics
        packages = PackageStats.get_total_visits_for_organization(
            organization_name,
            start_date=start_date,
            end_date=end_date)

        return {
            'report_name': 'matomo-dataset',
            'table': packages
        }


def matomo_dataset_report_info():
    return {
        'name': 'matomo-dataset',
        'title': 'Most popular datasets',
        'description': 'Matomo showing top datasets with most views by organization',
        'option_defaults': OrderedDict((('organization', None),
                                        ('time', 'month'),)),
        'option_combinations': org_and_time_option_combinations,
        'generate': matomo_dataset_report,
        'template': 'report/dataset_analytics.html',
    }


def matomo_resource_report(organization: str, time: str):
    '''
    Generates report based on matomo data.
    Total sum of resource dowloands per organization (all resources of all organization's packages)
    or number of downloads per resource for selected organization
    '''
    organization_name: str = organization
    start_date, end_date = last_calendar_period(time)

    # Return list of all organizations with packages if an organization is not given
    if organization_name is None:
        return {
            'report_name': 'matomo-resource',
            'table': matomo_organization_list(start_date, end_date, descending=True, sort_by='total_downloads')
            }

    # Get the resources for the organization
    resources = ResourceStats.get_resource_stats_for_organization(organization_name, start_date, end_date)

    return {
        'report_name': 'matomo-resource',
        'table': resources
    }


def matomo_resource_report_info():
    return {
        'name': 'matomo-resource',
        'title': 'Most popular resources',
        'description': 'Matomo showing most downloaded resources',
        'option_defaults': OrderedDict((('organization', None),
                                        ('time', 'month'),)),
        'option_combinations': org_and_time_option_combinations,
        'generate': matomo_resource_report,
        'template': 'report/resource_analytics.html'
    }


def matomo_location_report():
    '''
    Generates report based on matomo data. number of sessions per location
    '''

    top_locations = AudienceLocationDate.get_total_top_locations(20)

    last_month_end = datetime.today().replace(day=1) - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    finland_vs_world_last_month = AudienceLocationDate.special_total_location_to_rest(last_month_start, last_month_end,
                                                                                      'Finland')

    finland_vs_world_all = AudienceLocationDate.special_total_location_to_rest(datetime(2000, 1, 1), datetime.today(),
                                                                               'Finland')

    sessions_by_month = AudienceLocationDate.special_total_by_months()

    data_for_export = AudienceLocationDate.special_total_by_months(datetime(2000, 1, 1), last_month_end)

    first_date = AudienceLocationDate.get_first_date()

    # first item in table list will be available for export
    return {
        'table': data_for_export,
        'data': {
            'first_date': first_date.date().isoformat() if first_date is not None else '-',
            'top_locations': top_locations,
            'finland_vs_world_last_month': finland_vs_world_last_month,
            'finland_vs_world_all': finland_vs_world_all,
            'sessions_by_month': sessions_by_month,
        }
    }


def matomo_location_report_info():
    return {
        'name': 'matomo-location',
        'title': 'Audience locations',
        'description': 'Matomo showing most audience locations (bot traffic is filtered out)',
        'option_defaults': None,
        'option_combinations': None,
        'generate': matomo_location_report,
        'template': 'report/location_analytics.html'
    }


def matomo_most_popular_search_terms(time):
    start_date, end_date = last_calendar_period(time)
    most_popular_search_terms = SearchStats.get_most_popular_search_terms(start_date, end_date)
    return {
        'table': most_popular_search_terms
    }


def matomo_most_popular_search_terms_info():
    return {
        'name': 'matomo-most-popular-search-terms',
        'title': 'Most popular search terms',
        'description': 'Matomo showing most popular search terms',
        'option_defaults': OrderedDict((('time', 'month'),)),
        'option_combinations': time_option_combinations,
        'generate': matomo_most_popular_search_terms,
        'template': 'report/search_term_analytics.html'
    }
