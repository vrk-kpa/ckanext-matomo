from datetime import datetime
from operator import itemgetter
import ckan.plugins.toolkit as toolkit
from ckanext.matomo.model import PackageStats
from ckanext.matomo.types import Visits

@toolkit.side_effect_free
def most_visited_packages(context, data_dict) -> Visits:

    start_date = data_dict.get('start_date', None)
    end_date = data_dict.get('end_date', None)
    limit = data_dict.get('limit', None)

    dataset_type = data_dict.get('type', 'dataset')
    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
    if end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

    result = PackageStats.get_top(start_date=start_date,
                            end_date=end_date,
                            dataset_type=dataset_type,
                            limit=limit)
    packages = []

    for package in result.get('packages', []):
        package_with_extras = toolkit.get_action('package_show')(context, {'id': package.get('package_id')})
        package_with_extras['visits'] = package.get('visits', 0)
        package_with_extras['visit_date'] = package.get('visit_date')
        packages.append(package_with_extras)
    result['packages'] = sorted(packages, key=itemgetter('visits'), reverse=True)
    return result
