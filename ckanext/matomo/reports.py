from ckan.common import OrderedDict
from ckanext.matomo.model import PackageStats, ResourceStats, AudienceLocationDate, SearchStats
from datetime import datetime, timedelta


def last_week():
    today = datetime.today()
    end_date = today - timedelta(days=1)
    start_date = end_date - timedelta(days=7)
    return start_date, end_date


def last_month():
    today = datetime.today()
    end_date = today - timedelta(days=1)
    start_date = end_date - timedelta(days=30)
    return start_date, end_date


def last_year():
    today = datetime.today()
    end_date = today - timedelta(days=1)
    start_date = end_date - timedelta(days=365)
    return start_date, end_date


def last_calendar_period(period):
    if period == 'week':
        return last_week()
    elif period == 'month':
        return last_month()
    elif period == 'year':
        return last_year()
    else:
        raise ValueError("The period parameter should be either 'week', 'month' or 'year'")


def matomo_dataset_report(time):
    '''
    Generates report based on matomo data. number of views per package
    '''

    start_date, end_date = last_calendar_period(time)

    # get package objects corresponding to popular GA content
    top_packages = PackageStats.get_total_visits(start_date=start_date, end_date=end_date, limit=None)
    top_20 = top_packages[:20]

    return {
        'table': top_packages,
        'top': top_20
    }


def matomo_dataset_option_combinations():
    options = ['week', 'month', 'year']
    for option in options:
        yield {'time': option}


matomo_dataset_report_info = {
    'name': 'matomo-dataset',
    'title': 'Most popular datasets',
    'description': 'Matomo showing top datasets with most views',
    'option_defaults': OrderedDict((('time', 'month'),)),
    'option_combinations': matomo_dataset_option_combinations,
    'generate': matomo_dataset_report,
    'template': 'report/dataset_analytics.html',
}


def matomo_dataset_least_popular_report(time):
    '''
    Generates report based on matomo data. number of views per package
    '''

    start_date, end_date = last_calendar_period(time)

    # get package objects corresponding to popular GA content
    top_packages = PackageStats.get_total_visits(start_date=start_date, end_date=end_date, limit=None, descending=False)
    top_20 = top_packages[:20]

    return {
        'table': top_packages,
        'top': top_20
    }


def matomo_dataset_least_popular_option_combinations():
    options = ['week', 'month', 'year']
    for option in options:
        yield {'time': option}


matomo_dataset_least_popular_report_info = {
    'name': 'matomo-dataset-least-popular',
    'title': 'Least popular datasets',
    'description': 'Matomo showing top datasets with least views',
    'option_defaults': OrderedDict((('time', 'month'),)),
    'option_combinations': matomo_dataset_least_popular_option_combinations,
    'generate': matomo_dataset_least_popular_report,
    'template': 'report/dataset_analytics.html',
}


def matomo_resource_report(last):
    '''
    Generates report based on matomo data. number of views per package
    '''
    # get resource objects corresponding to popular GA content
    top_resources = ResourceStats.get_top(limit=last)

    return {
        'table': top_resources.get("resources")
    }


def matomo_resource_option_combinations():
    options = [20, 25, 30, 35, 40, 45, 50]
    for option in options:
        yield {'last': option}


matomo_resource_report_info = {
    'name': 'matomo-resource',
    'title': 'Most popular resources',
    'description': 'Matomo showing most downloaded resources',
    'option_defaults': OrderedDict((('last', 20),)),
    'option_combinations': matomo_resource_option_combinations,
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


matomo_location_report_info = {
    'name': 'matomo-location',
    'title': 'Audience locations',
    'description': 'Matomo showing most audience locations (bot traffic is filtered out)',
    'option_defaults': None,
    'option_combinations': None,
    'generate': matomo_location_report,
    'template': 'report/location_analytics.html'
}


def matomo_organizations_with_most_popular_datasets(time):
    start_date, end_date = last_calendar_period(time)
    most_popular_organizations = PackageStats.get_organizations_with_most_popular_datasets(start_date, end_date)
    return {
        'table': most_popular_organizations
    }


matomo_organizations_with_most_popular_datasets_info = {
    'name': 'matomo-most-popular-organizations',
    'title': 'Most popular organizations',
    'description': 'Matomo showing most popular organizations by visited datasets',
    'option_defaults': OrderedDict((('time', 'month'),)),
    'option_combinations': matomo_dataset_option_combinations,
    'generate': matomo_organizations_with_most_popular_datasets,
    'template': 'report/organization_analytics.html'
}


def matomo_most_popular_search_terms(time):
    start_date, end_date = last_calendar_period(time)
    most_popular_search_terms = SearchStats.get_most_popular_search_terms(start_date, end_date)
    return {
        'table': most_popular_search_terms
    }


matomo_most_popular_search_terms_info = {
    'name': 'matomo-most-popular-search-terms',
    'title': 'Most popular search terms',
    'description': 'Matomo showing most popular search terms',
    'option_defaults': OrderedDict((('time', 'month'),)),
    'option_combinations': matomo_dataset_option_combinations,
    'generate': matomo_most_popular_search_terms,
    'template': 'report/search_term_analytics.html'
}
