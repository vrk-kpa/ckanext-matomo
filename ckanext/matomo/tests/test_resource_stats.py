import pytest
import ckan.tests.factories as factories
from datetime import datetime
from ckanext.matomo.model import ResourceStats
from ckanext.matomo.commands import init_db
import logging
log = logging.getLogger(__name__)


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
    stat_date = datetime.strptime('2021-12-16', '%Y-%m-%d')
    ResourceStats.update_downloads(resource_id, stat_date, 21)
    stat_date = datetime.strptime('2021-10-16', '%Y-%m-%d')
    ResourceStats.update_downloads(resource_id, stat_date, 21)
    downloads_during_last_12_months = ResourceStats.get_download_count_for_dataset_during_last_12_months(package_id)

    assert downloads_during_last_12_months == 26
