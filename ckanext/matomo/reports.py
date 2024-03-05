from datetime import datetime, timedelta
from typing import List, Generator, Dict, Any, Optional
from ckan.plugins.toolkit import get_action
from ckanext.report import lib as report
from ckanext.matomo.model import PackageStats, ResourceStats, AudienceLocationDate, SearchStats
from ckanext.matomo.utils import package_generator, get_report_years, last_calendar_period
from ckanext.matomo.types import VisitsByOrganization, VisitsByPackage, VisitsByResource, GroupedVisits, TimeOptions, \
                                 OrganizationAndTimeOptions, Report

log = __import__('logging').getLogger(__name__)


try:
    from ckan.common import OrderedDict
except ImportError:
    from collections import OrderedDict


def time_option_combinations() -> Generator[TimeOptions, None, None]:
    time_options: list[str] = ['week', 'month', 'year']
    time_options.extend(get_report_years())
    for time in time_options:
        yield {'time': time}


def org_and_time_option_combinations() -> Generator[OrganizationAndTimeOptions, None, None]:
    time_options: list[str] = ['week', 'month', 'year']
    time_options.extend(get_report_years())
    org_options = report.all_organizations(include_none=True)
    for org in org_options:
        for time in time_options:
            yield {'organization': org, 'time': time}


def matomo_organization_list(start_date: datetime,
                             end_date: datetime,
                             descending=True,
                             sort_by="visits",
                             report_type="dataset") -> List[VisitsByOrganization]:
    # Fetch all organizations which have at least 1 dataset
    organizations_with_datasets = report.get_all_organizations(
        only_orgs_with_packages=True)


    totals_by_organization: GroupedVisits = {}
    if report_type == 'dataset':
        # Fetch total visits per dataset within given date range
        package_stats: List[VisitsByPackage] = PackageStats.get_total_visits(
            start_date, end_date, descending)

        # Count org specific sums
        for stat in package_stats:
            organization_id: Optional[str] = stat.get('owner_org', None)
            if organization_id:
                is_new = not bool(totals_by_organization.get(organization_id))
                if is_new:
                    totals_by_organization[organization_id] = {}
                totals_by_organization[organization_id]['visits'] = totals_by_organization[organization_id].get(
                    'visits', 0) + stat.get('visits', 0)
                totals_by_organization[organization_id]['entrances'] = totals_by_organization[organization_id].get(
                    'entrances', 0) + stat.get('entrances', 0)
                totals_by_organization[organization_id]['downloads'] = totals_by_organization[organization_id].get(
                    'downloads', 0) + stat.get('downloads', 0)
                totals_by_organization[organization_id]['events'] = totals_by_organization[organization_id].get(
                    'events', 0) + stat.get('events', 0)

    elif report_type == 'resource':
        # Fetch total visits per resource within given date range
        resource_stats: List[VisitsByResource] = ResourceStats.get_total_downloads(
            start_date, end_date, descending)

        # Count org specific sums
        for stat in resource_stats:
            organization_id: Optional[str] = stat.get('owner_org', None)
            if organization_id:
                is_new = not bool(totals_by_organization.get(organization_id))
                if is_new:
                    totals_by_organization[organization_id] = {}
                totals_by_organization[organization_id]['visits'] = totals_by_organization[organization_id].get(
                    'visits', 0) + stat.get('visits', 0)
                totals_by_organization[organization_id]['downloads'] = totals_by_organization[organization_id].get(
                    'downloads', 0) + stat.get('downloads', 0)
                totals_by_organization[organization_id]['events'] = totals_by_organization[organization_id].get(
                    'events', 0) + stat.get('events', 0)

    # Format into list of org dicts with stats totals
    organizations: List[VisitsByOrganization] = []
    for organization in organizations_with_datasets:
        org_id: str = organization.get('id', '')
        stats = totals_by_organization.get(org_id, {})
        org: VisitsByOrganization = {
            "organization_name": organization.get('name', ''),
            "organization_title": organization.get('title', ''),
            "organization_title_translated": organization.get('title_translated'),
            "visits": stats.get('visits', 0),
            "downloads": stats.get('downloads', 0),
            "events": stats.get('events', 0)
        }

        if report_type == 'dataset':
            org['entrances'] = stats.get('entrances', 0)

        organizations.append(org)

    return sorted(organizations, key=lambda organization: organization[sort_by], reverse=descending)


def matomo_datasets_by_organization(organization_name: str,
                                    start_date: datetime,
                                    end_date: datetime,
                                    descending=True,
                                    sort_by='visits') -> List[VisitsByPackage]:
    organization = get_action('organization_show')(
        {}, {'id': organization_name})
    organization_id: str = organization.get('id')

    datasets: Generator[Dict[str, Any], None, None] = package_generator('*:*', 1000,
                                                                        fq='+owner_org:%s' % organization_id,
                                                                        fl='id,name,title,extras_title_translated')

    # Fetch total visits per package within given date range
    package_stats: List[VisitsByPackage] = PackageStats.get_total_visits(start_date=start_date,
                                                                         end_date=end_date,
                                                                         descending=True,
                                                                         organization_id=organization_id)

    visits_by_dataset: GroupedVisits = {
        pkg.get('package_id', ''): {'visits': pkg.get('visits', 0),
                                    'entrances': pkg.get('entrances', 0),
                                    'downloads': pkg.get('downloads', 0),
                                    'events': pkg.get('events', 0)}
        for pkg in package_stats}

    # Map the visit data onto relevant datasets
    result: List[VisitsByPackage] = []
    for dataset in datasets:
        id: str = dataset.get('id', '')
        visit = visits_by_dataset.get(id, {})
        result.append({
            "package_id": id,
            "package_name": dataset.get('name'),
            "package_title_translated": dataset.get('title_translated', None),
            "visits": visit.get('visits', 0),
            "entrances": visit.get('entrances', 0),
            "downloads": visit.get('downloads', 0),
            "events": visit.get('events', 0)
        })

    return sorted(result, key=lambda dataset: dataset[sort_by], reverse=descending)


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
            'table': matomo_organization_list(start_date, end_date, descending=True, sort_by='visits', report_type='dataset')
        }
    else:
        # get given organizations datasets with the popularity statistics
        return {
            'report_name': 'matomo-dataset',
            'table': matomo_datasets_by_organization(organization_name=organization_name, start_date=start_date,
                                                     end_date=end_date, descending=True, sort_by='visits')
        }


def matomo_dataset_report_info():
    return {
        'name': 'matomo-dataset',
        'title': 'Most popular datasets',
        'description': 'Matomo showing top datasets with most views by organization',
        'description_template': 'report/dataset_analytics_description.html',
        'option_defaults': OrderedDict((('organization', None),
                                        ('time', 'month'),)),
        'option_combinations': org_and_time_option_combinations,
        'generate': matomo_dataset_report,
        'template': 'report/dataset_analytics.html',
    }


def matomo_resources_by_organization(organization_name: str,
                                     start_date: datetime,
                                     end_date: datetime,
                                     descending=True,
                                     sort_by='downloads') -> List[VisitsByResource]:
    organization = get_action('organization_show')(
        {}, {'id': organization_name})
    organization_id: str = organization.get('id')

    packages: Generator[Dict[str, Any], None, None] = package_generator('*:*', 1000,
                                                                        fq='+owner_org:%s' % organization_id)
    # Fetch total visits per package within given date range
    resource_stats: List[VisitsByResource] = ResourceStats.get_total_downloads(start_date=start_date,
                                                                               end_date=end_date,
                                                                               descending=True,
                                                                               organization_id=organization_id)

    visits_by_resource: GroupedVisits = {
        res.get('resource_id', ''): {'visits': res.get('visits', 0),
                                     'downloads': res.get('downloads', 0),
                                     'events': res.get('events', 0),
                                     'visit_date': res.get('visit_date', '')}
        for res in resource_stats}

    # Map the visit data onto relevant resources
    result: List[VisitsByResource] = []
    for package in packages:
        package_id: str = package.get('id', '')
        for resource in package.get('resources', []):
            resource_id = resource.get('id')
            visit = visits_by_resource.get(resource_id, {})
            result.append(
                {'resource_id': resource_id, 'resource_name': resource.get('name', ''),
                 'resource_name_translated': resource.get('name_translated'),
                 'package_id': package_id, 'package_name': package.get('name', ''), 'package_title': package.get('title', ''),
                 'package_title_translated': package.get('title_translated'),
                 'owner_org': package.get('owner_org'),
                 'visits': visit.get('visits', 0),
                 'downloads': visit.get('downloads', 0),
                 'events': visit.get('events', 0),
                 'visit_date': visit.get('visit_date', '')})

    return sorted(result, key=lambda dataset: dataset[sort_by], reverse=descending)


def matomo_resource_report(organization: str, time: str) -> Report:
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
            'table': matomo_organization_list(start_date, end_date, descending=True,
                                              sort_by='downloads', report_type='resource')
        }

    return {
        'report_name': 'matomo-resource',
        'table': matomo_resources_by_organization(organization_name=organization_name, start_date=start_date,
                                                  end_date=end_date, descending=True, sort_by='downloads')
    }


def matomo_resource_report_info():
    return {
        'name': 'matomo-resource',
        'title': 'Most popular resources',
        'description': 'Matomo showing most downloaded resources',
        'description_template': 'report/resource_analytics_description.html',
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

    data_for_export = AudienceLocationDate.special_total_by_months(
        datetime(2000, 1, 1), last_month_end)

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
    most_popular_search_terms = SearchStats.get_most_popular_search_terms(
        start_date, end_date)
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
