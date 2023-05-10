import pytest
import ckan.tests.factories as factories
from datetime import datetime, timedelta
from ckanext.matomo.model import ResourceStats
from ckanext.matomo.commands import init_db
from ckanext.matomo.utils import last_calendar_period
import uuid


@pytest.mark.freeze_time('2022-11-11')
@pytest.mark.usefixtures("clean_db")
def test_resource_update_downloads(app):
    init_db()
    resource_id = '16364c67-251c-45dc-98d9-9e91105d1928'
    stat_date = datetime.strptime('2022-11-10', '%Y-%m-%d')
    ResourceStats.update_downloads(resource_id, stat_date, 3)
    resource_stats = ResourceStats.get(resource_id)
    assert resource_stats.__dict__.get('downloads') == 3
    ResourceStats.update_downloads(resource_id, stat_date, 2)
    resource_stats = ResourceStats.get(resource_id)
    assert resource_stats.__dict__.get('downloads') == 2


@pytest.mark.freeze_time('2022-11-11')
@pytest.mark.usefixtures("clean_db")
def test_resource_update_visits(app):
    init_db()
    resource_id = '16364c67-251c-45dc-98d9-9e91105d1928'
    stat_date = datetime.strptime('2022-11-10', '%Y-%m-%d')
    ResourceStats.update_visits(resource_id, stat_date, 3)
    resource_stats = ResourceStats.get(resource_id)
    assert resource_stats.__dict__.get('visits') == 3
    ResourceStats.update_visits(resource_id, stat_date, 2)
    resource_stats = ResourceStats.get(resource_id)
    assert resource_stats.__dict__.get('visits') == 2


@pytest.mark.freeze_time('2022-11-11')
@pytest.mark.usefixtures("clean_db")
def test_resource_get_download_count_for_dataset_during_last_12_months(app):
    init_db()
    package_id = '06364c67-251c-45dc-98d9-9e91105d1928'
    resource_id = '16364c67-251c-45dc-98d9-9e91105d1928'
    factories.Dataset(id=package_id)
    factories.Resource(id=resource_id, package_id=package_id)
    stat_date = datetime.strptime('2022-11-10', '%Y-%m-%d')
    ResourceStats.update_downloads(resource_id, stat_date, 3)
    stat_date = datetime.strptime('2022-11-09', '%Y-%m-%d')
    ResourceStats.update_downloads(resource_id, stat_date, 2)
    stat_date = datetime.strptime('2021-12-24', '%Y-%m-%d')
    ResourceStats.update_downloads(resource_id, stat_date, 21)
    stat_date = datetime.strptime('2021-10-16', '%Y-%m-%d')
    ResourceStats.update_downloads(resource_id, stat_date, 21)
    start_date, end_date = last_calendar_period('year')
    downloads_during_last_12_months = ResourceStats.get_download_count_for_dataset(package_id, start_date, end_date)

    assert downloads_during_last_12_months == 26


@pytest.mark.freeze_time('2022-11-11')
@pytest.mark.usefixtures("clean_db")
def test_resource_get_top(app):
    init_db()
    number_of_resources = 30
    resource_range = range(0, number_of_resources - 1)
    resource_ids = [str(uuid.uuid4()) for number in resource_range]
    base_count_downloads = 40
    base_count_visits = 40
    package_id = '06364c67-251c-45dc-98d9-9e91105d1928'
    factories.Dataset(id=package_id)

    for i_resource in resource_range:
        stat_date = datetime.strptime('2022-11-10', '%Y-%m-%d')
        resource_id = resource_ids[i_resource]
        factories.Resource(id=resource_id, package_id=package_id)

        # Loop for 10 dates with interval -1 week for each
        for i_day in range(0, 5):
            ResourceStats.update_downloads(resource_id, stat_date, base_count_downloads - i_resource)
            ResourceStats.update_visits(resource_id, stat_date, base_count_visits - i_resource)
            stat_date = stat_date - timedelta(weeks=1)

    top_resources = ResourceStats.get_top()
    resources = top_resources.get('resources', [])

    assert resources[0].get('resource_id') == resource_ids[0]
    assert resources[0].get('downloads') == 200
    assert resources[5].get('resource_id') == resource_ids[5]
    assert len(resources) == 20
