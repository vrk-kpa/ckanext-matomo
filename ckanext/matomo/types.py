from typing import Dict, List, TypedDict, Literal, Optional, Union

LocalizationObject = Dict[str, str]
VisitsByPackage = TypedDict('VisitsByPackage', {'package_id': str,
                                                'package_name': Optional[str],
                                                'package_title_translated': Optional[LocalizationObject],
                                                'owner_org': Optional[str],
                                                'visits': int, 'entrances': int, 'downloads': int, 'events': int,
                                                'visit_date': str}, total=False)
VisitsByResource = TypedDict('VisitsByResource', {'resource_id': str, 'resource_name': str,
                                                  'resource_name_translated': Optional[LocalizationObject],
                                                  'package_id': str,
                                                  'package_name': Optional[str],
                                                  'package_title': str,
                                                  'package_title_translated': Optional[LocalizationObject],
                                                  'owner_org': Optional[str],
                                                  'visits': int, 'entrances': int, 'downloads': int, 'events': int,
                                                  'visit_date': str}, total=False)
Visit = TypedDict(
    'Visit', {'visits': int, 'entrances': int, 'downloads': int, 'events': int, 'visit_date': str}, total=False)
Visits = TypedDict('Visits', {'packages': List[VisitsByPackage], 'resources': List[VisitsByResource],
                              'visits': List[Dict[str, int]],
                              'total_visits': int,
                              'total_downloads': int}, total=False)

TimeOptions = Dict[Literal['time'], str]
OrganizationAndTimeOptions = Dict[Literal['organization',
                                          'time'], Optional[str]]
VisitsByOrganization = TypedDict('VisitsByOrganization', {
    'organization_name': str,
    'organization_title': str,
    'organization_title_translated': Optional[LocalizationObject],
    'visits': Optional[int],
    'entrances': Optional[int],
    'downloads': int,
    'events': int
}, total=False)
GroupedVisits = Dict[str, Visit]
Report = TypedDict('Report', {'report_name': str,
                   'table': Union[List[VisitsByOrganization], List[VisitsByPackage], List[VisitsByResource]]}, total=False)
Resource = TypedDict('Resource', {'resource_id': str, 'resource_name': str,
                                  'resource_name_translated': Optional[LocalizationObject], 'package_id': str,
                                  'package_name': str, 'package_title': str,
                                  'package_title_translated': Optional[LocalizationObject],
                                  'owner_org': Optional[str]})
