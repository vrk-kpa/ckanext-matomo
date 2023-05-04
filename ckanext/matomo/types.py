from typing import Dict, List, TypedDict, Literal, Optional
from ckanext.report.types import LocalizationObject

VisitsByPackage = TypedDict('VisitsByPackage', {'package_id': str,
                                                'package_name': Optional[str],
                                                'package_title_translated': Optional[LocalizationObject],
                                                'owner_org': Optional[str],
                                                'visits': int, 'entrances': int, 'downloads': int,
                                                'visit_date': str}, total=False)
Visit = TypedDict(
    'Visit', {'visits': int, 'entrances': int, 'downloads': int}, total=False)
Visits = TypedDict('Visits', {'packages': List[VisitsByPackage], 'visits': List[Dict[str, int]], 'total_visits': int,
                              'total_downloads': int}, total=False)

Time = Dict[Literal['time'], str]
OrganizationAndTime = Dict[Literal['organization', 'time'], Optional[str]]
VisitsByOrganization = TypedDict('OrganizationsVisits', {
    'organization_name': str,
    'organization_title': str,
    'organization_title_translated': LocalizationObject,
    'visits': int,
    'entrances': int,
    'downloads': int
})
GroupedVisits = Dict[str, Visit]
