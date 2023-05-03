from typing import Dict, List, TypedDict

Visit = TypedDict('Visit', {'package_name': str, 'package_title_translated': str, 'package_id': str, 'owner_org': str,
                            'visits': int, 'entrances': int, 'downloads': int, 'visit_date': str}, total=False)
Visits = TypedDict('Visits', {'packages': List[Visit], 'visits': List[Dict[str, int]], 'total_visits': int,
                              'total_downloads': int}, total=False)