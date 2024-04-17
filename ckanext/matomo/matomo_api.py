import requests
import datetime
import uuid

from typing import Dict, Any

log = __import__('logging').getLogger(__name__)

class MatomoException(RuntimeError):
    pass


class MatomoAPI(object):
    def __init__(self, matomo_url, id_site, token_auth):
        self.matomo_url = matomo_url
        self.tracking_url = '{}/matomo.php'.format(matomo_url)
        self.id_site = id_site
        self.token_auth = token_auth
        self.default_params = {'idSite': self.id_site,
                               'token_auth': self.token_auth,
                               'module': 'API',
                               'format': 'JSON',
                               'filter_limit': -1}
        self.tracking_params = {'idsite': self.id_site,
                                'rec': 1}

    def get(self, extra_params):
        if self.token_auth is None:
            raise MatomoException('Matomo authentication token is not set!')

        params = self.default_params.copy()
        params.update(extra_params)
        result = requests.get(self.matomo_url, params=params).json()
        if isinstance(result, dict) and result.get('result') == 'error':
            raise MatomoException(result.get('message'))

        return result

    def resource_download_statistics(self, period='month', date='today', dataset=None) -> Dict[str, Any]:
        pattern = '/data/([^/]+/)?dataset/[^/]+/resource/[^/]+/download/[^/]+$'
        if dataset:
            pattern = '/data/([^/]+/)?dataset/{dataset}/resource/[^/]+/download/[^/]+$'.format(dataset=dataset)

        data: Dict[str, Any] = self.get({'method': 'Actions.getDownloads',
                         'period': period,
                         'date': date,
                         'flat': 1,
                         'filter_column': 'label',
                         'filter_pattern': pattern })

        def handle(data) -> Dict[str, Any]:
            result: Dict[str, Any] = {}
            for datum in data:
                # Request filter pattern ensures this is correct
                dataset_id: str = datum['label'].split('/')[-5]
                resource_id: str = datum['label'].split('/')[-3]

                result.setdefault(dataset_id, {}).setdefault(resource_id, []).append(datum)

            return result

        return _process_one_or_more_dates_result(data, handle)

    def dataset_page_statistics(self, period='month', date='today', dataset=None) -> Dict[str, Any]:
        # TODO: /data/ should be config based, fine for our projects for now
        pattern = '[^/]*/data/([^/]+/)?dataset/[^/]+$'
        if dataset:
            pattern = '[^/]*/data/([^/]+/)?dataset/{dataset}$'.format(dataset=dataset)

        data: Dict[str, Any] = self.get({'method': 'Actions.getPageUrls',
                         'period': period,
                         'date': date,
                         'flat': 1,
                         'filter_column': 'label',
                         'filter_pattern': pattern})

        def handle(data) -> Dict[str, Any]:
            result: Dict[str, Any] = {}

            for datum in data:
                # Request filter pattern ensures this is correct
                dataset_name: str = datum['label'].split('/')[-1]
                result.setdefault(dataset_name, []).append(datum)

            return result

        return _process_one_or_more_dates_result(data, handle)

    def resource_page_statistics(self, period='month', date='today', dataset=None) -> Dict[str, Any]:
        pattern = '[^/]*/data/([^/]+/)?dataset/[^/]+/resource/[^/]+$'
        if dataset:
            pattern = '[^/]*/data/([^/]+/)?dataset/{dataset}/resource/[^/]+$'.format(dataset=dataset)

        data: Dict[str, Any] = self.get({'method': 'Actions.getPageUrls',
                         'period': period,
                         'date': date,
                         'flat': 1,
                         'filter_column': 'label',
                         'filter_pattern': pattern})

        def handle(data) -> Dict[str, Any]:
            result: Dict[str, Any] = {}

            for datum in data:
                # Request filter pattern ensures this is correct
                resource_id: str = datum['label'].split('/')[-1].split('?', 1)[0]
                result.setdefault(resource_id, []).append(datum)

            return result

        return _process_one_or_more_dates_result(data, handle)

    def visits_by_country(self, period='month', date='today') -> Dict[str, Any]:
        data: Dict[str, Any] = self.get({'method': 'UserCountry.getCountry',
                         'period': period,
                         'date': date,
                         'flat': 1})

        def handle(data) -> Dict[str, Any]:
            return data

        return _process_one_or_more_dates_result(data, handle)

    def search_terms(self, period='month', date='today') -> Dict[str, Any]:
        data: Dict[str, Any] = self.get({'method': 'Actions.getSiteSearchKeywords',
                         'period': period,
                         'date': date,
                         'flat': 1})

        def handle(data) -> Dict[str, Any]:
            return data

        return _process_one_or_more_dates_result(data, handle)

    def events(self, period='month', date='today', filter_column='Events_EventAction', filter_pattern=None) -> Dict[str, Any]:
        filter = {
            'filter_column': filter_column,
        }
        if filter_pattern:
            filter['filter_pattern'] = filter_pattern
        data: Dict[str, Any] = self.get({'method': 'Events.getAction',
                         'period': period,
                         'date': date,
                         'flat': 1,
                        'filter_limit': -1,
                         **filter})

        def handle(data) -> Dict[str, Any]:
            return data

        return _process_one_or_more_dates_result(data, handle)

    @classmethod
    def date_range(cls, start, end):
        if isinstance(start, datetime.date):
            start = start.strftime('%Y-%m-%d')
        if isinstance(end, datetime.date):
            end = end.strftime('%Y-%m-%d')
        return '{},{}'.format(start, end)

    def tracking(self, extra_params):
        params = self.tracking_params.copy()
        params.update(extra_params)
        params['rand'] = str(uuid.uuid4())

        if self.token_auth is not None:
            params['token_auth'] = self.token_auth

        return requests.get(self.tracking_url, params=params)


def _process_one_or_more_dates_result(data, handler) -> Dict[str, Any]:
    # Single date
    if isinstance(data, list):
        result = handler(data)
    # Multiple dates
    else:
        result: Dict[str, Any] = {}
        for date, date_data in data.items():
            result[date] = handler(date_data)

    return result
