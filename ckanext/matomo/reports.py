from ckanext.matomo.model import PackageStats, ResourceStats, AudienceLocationDate, SearchStats
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from ckanext.report import lib as report

log = __import__('logging').getLogger(__name__)


try:
    from ckan.common import OrderedDict
except ImportError:
    from collections import OrderedDict


def get_report_years():
    start_year = 2014
    current_year = date.today().year
    return sorted(list(range(start_year, current_year+1)), reverse=True)


# Set end_date explicitly to be the second before midnight on previous day
# and start_date to be at 00:00:00 week, month or year from that
# Example on 2023-03-21 14:11:42
# week = 2023-03-14 00:00:00 - 2023-03-20 23:59:59
# month = 2023-02-20 00:00:00 - 2023-03-20 23:59:59
# year = 2022-03-20 00:00:00 - 2023-03-20 23:59:59
def last_week():
    today = datetime.today()
    end_date = today - relativedelta(days=1, hour=23, minute=59, second=59)
    start_date = today - relativedelta(weeks=1, hour=0, minute=0, second=0)
    return start_date, end_date


def last_month():
    today = datetime.today()
    end_date = today - relativedelta(days=1, hour=23, minute=59, second=59)
    start_date = end_date - relativedelta(months=1, hour=0, minute=0, second=0)
    return start_date, end_date


def last_year():
    today = datetime.today()
    end_date = today - relativedelta(days=1, hour=23, minute=59, second=59)
    start_date = end_date - relativedelta(years=1, hour=0, minute=0, second=0)
    return start_date, end_date


def selected_year(year):
    start_date = datetime(year, 1, 1, 0, 0, 0, 0)
    end_date = datetime(year, 12, 31, 23, 59, 59, 0)
    return start_date, end_date


def last_calendar_period(period):
    report_years = get_report_years()
    if period == 'week':
        return last_week()
    elif period == 'month':
        return last_month()
    elif period == 'year':
        return last_year()
    elif (isinstance(period, int) or (isinstance(period, str) and period.isdigit())) and int(period) in report_years:
        return selected_year(int(period))
    else:
        raise ValueError("The period parameter should be either 'week', 'month' or 'year'")


def matomo_dataset_report(organization, time):
    '''
    Generates report based on matomo data. number of views per package
    '''

    # Return matomo_organizations_with_most_popular_datasets list if an organization is not given
    if organization is None:
        return matomo_organizations_with_most_popular_datasets(time)

    start_date, end_date = last_calendar_period(time)

    # get package objects corresponding to popular GA content
    most_visited_packages = PackageStats.get_total_visits_for_organization(
        organization,
        start_date=start_date,
        end_date=end_date)

    return {
        'report_name': 'matomo-dataset',
        'table': most_visited_packages
    }


def matomo_time_option_combinations():
    time_options = ['week', 'month', 'year']
    time_options.extend(get_report_years())
    for time in time_options:
        yield {'time': time}


def matomo_org_and_time_option_combinations():
    time_options = ['week', 'month', 'year']
    time_options.extend(get_report_years())
    org_options = report.all_organizations(include_none=True)
    for org in org_options:
        for time in time_options:
            yield {'organization': org, 'time': time}


def matomo_dataset_report_info():
    return {
        'name': 'matomo-dataset',
        'title': 'Most popular datasets',
        'description': 'Matomo showing top datasets with most views by organization',
        'option_defaults': OrderedDict((('organization', None),
                                        ('time', 'month'),)),
        'option_combinations': matomo_org_and_time_option_combinations,
        'generate': matomo_dataset_report,
        'template': 'report/dataset_analytics.html',
    }


def matomo_resource_report(organization, time):
    '''
    Generates report based on matomo data. Number of downloads per package (sum of package's resource downloads)
    '''

    # Return matomo_organizations_with_most_popular_datasets list if an organization is not given
    if organization is None:
        most_viewed_datasets = matomo_organizations_with_most_popular_datasets(time)

        return {'table': sorted(most_viewed_datasets['table'],
                                key=lambda organization: organization["total_downloads"],
                                reverse=True)}

    start_date, end_date = last_calendar_period(time)

    # Get the most downloaded resources for the organization
    most_downloaded_resources = ResourceStats.get_top_downloaded_resources_for_organization(organization, start_date, end_date)

    return {
        'report_name': 'matomo-resource',
        'table': most_downloaded_resources.get("resources")
    }


def matomo_resource_report_info():
    return {
        'name': 'matomo-resource',
        'title': 'Most popular resources',
        'description': 'Matomo showing most downloaded resources',
        'option_defaults': OrderedDict((('organization', None),
                                        ('time', 'month'),)),
        'option_combinations': matomo_org_and_time_option_combinations,
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


def matomo_organizations_with_most_popular_datasets(time, descending=True):
    start_date, end_date = last_calendar_period(time)
    most_popular_organizations = PackageStats.get_organizations_with_most_popular_datasets(start_date,
                                                                                           end_date, descending=descending)

    return {
        'table': most_popular_organizations
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
        'option_combinations': matomo_time_option_combinations,
        'generate': matomo_most_popular_search_terms,
        'template': 'report/search_term_analytics.html'
    }
