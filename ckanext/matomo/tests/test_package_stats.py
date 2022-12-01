import pytest
from datetime import datetime
from ckanext.matomo.model import PackageStats
from ckanext.matomo.commands import init_db
import logging
log = logging.getLogger(__name__)


@pytest.mark.usefixtures("clean_db")
def test_package_update_downloads(app):
    init_db()
    package_id = '16364c67-251c-45dc-98d9-9e91105d1928'
    stat_date = datetime.strptime('2022-11-10', '%Y-%m-%d')
    PackageStats.update_downloads(package_id, stat_date, 3)
    package_stats = PackageStats.get(package_id)
    assert package_stats.__dict__.get('downloads') == 3
    PackageStats.update_downloads(package_id, stat_date, 2)
    package_stats = PackageStats.get(package_id)
    assert package_stats.__dict__.get('downloads') == 2


@pytest.mark.usefixtures("clean_db")
def test_package_update_visits(app):
    init_db()
    package_id = '16364c67-251c-45dc-98d9-9e91105d1928'
    stat_date = datetime.strptime('2022-11-10', '%Y-%m-%d')
    PackageStats.update_visits(package_id, stat_date, 3)
    package_stats = PackageStats.get(package_id)
    assert package_stats.__dict__.get('visits') == 3
    PackageStats.update_visits(package_id, stat_date, 2)
    package_stats = PackageStats.get(package_id)
    assert package_stats.__dict__.get('visits') == 2
