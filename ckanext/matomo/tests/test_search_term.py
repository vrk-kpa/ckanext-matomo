import pytest
from datetime import datetime, timedelta
from ckanext.matomo.model import SearchStats
from ckanext.matomo.commands import init_db
import logging
log = logging.getLogger(__name__)


@pytest.mark.usefixtures("clean_db")
def test_search_term_update_count(app):
    init_db()
    search_term = 'SearchTerm'
    stat_date = datetime.strptime('2022-11-10', '%Y-%m-%d')
    SearchStats.update_search_term_count(search_term, stat_date, 10)
    most_popular_search_terms = SearchStats.get_most_popular_search_terms(
        stat_date - timedelta(days=1), stat_date + timedelta(days=1))
    assert most_popular_search_terms[0].get('count') == 10
    assert most_popular_search_terms[0].get('search_term') == search_term


@pytest.mark.usefixtures("clean_db")
def test_most_popular_search_term_sorting(app):
    init_db()
    search_term_base = 'SearchTerm'
    stat_date = datetime.strptime('2022-11-10', '%Y-%m-%d')

    # Loop for 31 days
    for day in range(1, 31):
        # Loop for 10 searchterm
        for term in range(1, 11):
            SearchStats.update_search_term_count('{}-{}'.format(search_term_base, term), stat_date, 20 - term)
        stat_date = stat_date - timedelta(days=1)

    most_popular_search_terms = SearchStats.get_most_popular_search_terms(
        stat_date - timedelta(days=1), stat_date + timedelta(days=32))

    assert most_popular_search_terms[0].get('count') == 570
    assert most_popular_search_terms[0].get('search_term') == '{}-1'.format(search_term_base)
    assert most_popular_search_terms[0].get('count') > most_popular_search_terms[1].get('count')
