import requests
import urllib.parse
from config import MATOMO_URL, MATOMO_SITE_ID, MATOMO_TOKEN

class MatomoAPI:
    def __init__(self, base_url=MATOMO_URL, site_id=MATOMO_SITE_ID, token=MATOMO_TOKEN):
        self.base_url = base_url
        self.site_id = site_id
        self.token = token

    def _build_url(self, method, period, date, extra_params=None):
        params = {
            'module': 'API',
            'method': method,
            'idSite': self.site_id,
            'period': period,
            'date': date,
            'format': 'JSON',
            'token_auth': self.token,
            'expanded': 1,
            'showMetadata': 0,
            'force_api_session': 1
        }
        if extra_params:
            params.update(extra_params)
        
        query_string = urllib.parse.urlencode(params)
        return f"{self.base_url}index.php?{query_string}"

    def get_data(self, method, period, date, extra_params=None):
        url = self._build_url(method, period, date, extra_params)
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição para {method}: {e}")
            return []

    def get_page_urls(self, period, date, limit=100):
        return self.get_data('Actions.getPageUrls', period, date, {'filter_limit': limit})

    def get_site_search_keywords(self, period, date, limit=50):
        return self.get_data('Actions.getSiteSearchKeywords', period, date, {'filter_limit': limit})

    def get_transitions(self, period, date, page_url):
        return self.get_data('Transitions.getTransitionsForPageUrl', period, date, {'pageUrl': page_url})

    def get_city(self, period, date, limit=100):
        return self.get_data('UserCountry.getCity', period, date, {'filter_limit': limit})

    def get_visit_time(self, period, date):
        return self.get_data('VisitTime.getVisitInformationPerServerTime', period, date)

    def get_browsers(self, period, date, limit=20):
        return self.get_data('DevicesDetection.getBrowsers', period, date, {'filter_limit': limit})

    def get_device_type(self, period, date):
        return self.get_data('DevicesDetection.getType', period, date)
