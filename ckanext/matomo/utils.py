

from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from typing import Dict, Any, List, Generator, Union, Tuple
import itertools
from ckan.plugins.toolkit import get_action

log = __import__('logging').getLogger(__name__)

def package_generator(query, page_size, fq='', fl=None,
                      context={'ignore_auth': True},
                      dataset_type='dataset') -> Generator[Any, None, None]:
    package_search = get_action('package_search')

    # Loop through all items. Each page has {page_size} items.
    # Stop iteration when all items have been looped.
    for index in itertools.count(start=0, step=page_size):
        data_dict: Dict[str, Any] = {'rows': page_size, 'q': query, 'start': index,
                     'fq': '+dataset_type:' + dataset_type + ' ' + fq,
                     'fl': fl}
        data: Dict[str, Any] = package_search(context, data_dict)
        packages: List[Any] = data.get('results', [])
        for package in packages:
            yield package

        # Stop iteration all query results have been looped through
        if data["count"] < (index + page_size):
            return


def get_report_years() -> List[str]:
    start_year = 2014
    current_year: int = date.today().year
    years: list[int] = sorted(list(range(start_year, current_year+1)), reverse=True)
    return [str(year) for year in years]


# Set end_date explicitly to be the second before midnight on previous day
# and start_date to be at 00:00:00 week, month or year from that
# Example on 2023-03-21 14:11:42
# week = 2023-03-14 00:00:00 - 2023-03-20 23:59:59
# month = 2023-02-20 00:00:00 - 2023-03-20 23:59:59
# year = 2022-03-20 00:00:00 - 2023-03-20 23:59:59
def last_week() -> Tuple[datetime, datetime]:
    today: datetime = datetime.today()
    end_date: datetime = today - relativedelta(days=1, hour=23, minute=59, second=59)
    start_date: datetime = today - relativedelta(weeks=1, hour=0, minute=0, second=0)
    return start_date, end_date


def last_month() -> Tuple[datetime, datetime]:
    today: datetime = datetime.today()
    end_date: datetime = today - relativedelta(days=1, hour=23, minute=59, second=59)
    start_date: datetime = end_date - relativedelta(months=1, hour=0, minute=0, second=0)
    return start_date, end_date


def last_year() -> Tuple[datetime, datetime]:
    today: datetime = datetime.today()
    end_date: datetime = today - relativedelta(days=1, hour=23, minute=59, second=59)
    start_date: datetime = end_date - relativedelta(years=1, hour=0, minute=0, second=0)
    return start_date, end_date


def selected_year(year) -> Tuple[datetime, datetime]:
    start_date: datetime = datetime(year, 1, 1, 0, 0, 0, 0)
    end_date: datetime = datetime(year, 12, 31, 23, 59, 59, 0)
    return start_date, end_date


def last_calendar_period(period: Union[str, int]) -> Tuple[datetime, datetime]:
    report_years: List[str] = get_report_years()
    if period == 'week':
        return last_week()
    elif period == 'month':
        return last_month()
    elif period == 'year':
        return last_year()
    elif (isinstance(period, int) or (isinstance(period, str) and period.isdigit())) and str(period) in report_years:
        return selected_year(int(period))
    else:
        raise ValueError("The period parameter should be either 'week', 'month', 'year' \
                          or a 4 digit representation of a specific year between 2014 and \
                          the current year as int or str (2023 or '2023')")
