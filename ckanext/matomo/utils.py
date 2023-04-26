
from ckan.plugins.toolkit import get_action
import itertools

log = __import__('logging').getLogger(__name__)

def package_generator(query, page_size, fq='', fl=None, context={'ignore_auth': True}, dataset_type='dataset'):
    package_search = get_action('package_search')

    # Loop through all items. Each page has {page_size} items.
    # Stop iteration when all items have been looped.
    for index in itertools.count(start=0, step=page_size):
        data_dict = {'rows': page_size, 'q': query, 'start': index,
                     'fq': '+dataset_type:' + dataset_type + ' ' + fq,
                     'fl': fl}
        data = package_search(context, data_dict)
        packages = data.get('results', [])
        for package in packages:
            yield package

        # Stop iteration all query results have been looped through
        if data["count"] < (index + page_size):
            return
