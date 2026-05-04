import requests
import urllib.parse
from config import MATOMO_URL, MATOMO_SITE_ID, MATOMO_TOKEN

class MatomoAPI:
    def __init__(self, base_url=MATOMO_URL, site_id=MATOMO_SITE_ID, token=MATOMO_TOKEN):
        self.base_url = base_url
        self.site_id = site_id
        self.token = token

    def _build_url(self, method, period=None, date=None, extra_params=None, site_id=None):
        sid = site_id if site_id is not None else self.site_id
        params = {
            'module': 'API',
            'method': method,
            'idSite': sid,
            'format': 'JSON',
            'token_auth': self.token,
            'expanded': 1,
            'showMetadata': 0,
            'force_api_session': 1
        }
        
        if period:
            params['period'] = period
        if date:
            params['date'] = date
            
        if extra_params:
            params.update(extra_params)
        
        query_string = urllib.parse.urlencode(params)
        return f"{self.base_url}index.php?{query_string}"

    def get_data(self, method, period=None, date=None, extra_params=None, site_id=None):
        url = self._build_url(method, period, date, extra_params, site_id)
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição para {method}: {e}")
            return []

    def get_sites(self):
        return self.get_data('SitesManager.getSitesWithViewAccess')

    def get_page_urls(self, period, date, site_id=None, limit=100):
        return self.get_data('Actions.getPageUrls', period, date, {'filter_limit': limit}, site_id)

    def get_site_search_keywords(self, period, date, site_id=None, limit=50):
        return self.get_data('Actions.getSiteSearchKeywords', period, date, {'filter_limit': limit}, site_id)

    def get_transitions(self, period, date, page_url, site_id=None):
        return self.get_data('Transitions.getTransitionsForPageUrl', period, date, {'pageUrl': page_url}, site_id)

    def get_city(self, period, date, site_id=None, limit=100):
        return self.get_data('UserCountry.getCity', period, date, {'filter_limit': limit}, site_id)

    def get_visit_time(self, period, date, site_id=None):
        return self.get_data('VisitTime.getVisitInformationPerServerTime', period, date, None, site_id)

    def get_browsers(self, period, date, site_id=None, limit=20):
        return self.get_data('DevicesDetection.getBrowsers', period, date, {'filter_limit': limit}, site_id)

    def get_device_type(self, period, date, site_id=None):
        return self.get_data('DevicesDetection.getType', period, date, None, site_id)

    def get_outlinks(self, period, date, site_id=None, limit=50):
        return self.get_data('Actions.getOutlinks', period, date, {'filter_limit': limit}, site_id)

    def get_last_visits(self, period, date, site_id=None, segment=None, limit=10):
        params = {'filter_limit': limit}
        if segment:
            params['segment'] = segment
        return self.get_data('Live.getLastVisitsDetails', period, date, params, site_id)
