from api.matomo_client import MatomoAPI
from config import MATOMO_URL, MATOMO_TOKEN, MATOMO_SITE_ID
from utils.data_processor import process_page_urls, identify_service_cards

api = MatomoAPI(base_url=MATOMO_URL, token=MATOMO_TOKEN, site_id=MATOMO_SITE_ID)
pages = api.get_page_urls('month', 'today', site_id=298, limit=500)
df_pages = process_page_urls(pages)
df_services = identify_service_cards(df_pages)

if not df_services.empty:
    for i in range(min(5, len(df_services))):
        print(f"Nome: {df_services.iloc[i]['Nome do Serviço']}")
        print(f"URL Original: {df_services.iloc[i]['URL_Original']}")
        
        url = df_services.iloc[i]['URL_Original']
        res_raw = api.get_transitions('month', 'today', url, site_id=298)
        print('Raw URL transitions:', res_raw.get('message') if res_raw and 'message' in res_raw else 'OK')
        
        if url.startswith('/'):
            url_abs = 'http://ms.gov.br' + url
            res_abs = api.get_transitions('month', 'today', url_abs, site_id=298)
            print('http://ms.gov.br URL transitions:', res_abs.get('message') if res_abs and 'message' in res_abs else 'OK')
            
            url_abs2 = 'https://www.ms.gov.br' + url
            res_abs2 = api.get_transitions('month', 'today', url_abs2, site_id=298)
            print('https://www.ms.gov.br URL transitions:', res_abs2.get('message') if res_abs2 and 'message' in res_abs2 else 'OK')
            
            url_abs3 = 'https://webanalytics.ms.gov.br' + url
            res_abs3 = api.get_transitions('month', 'today', url_abs3, site_id=298)
            print('https://webanalytics.ms.gov.br URL transitions:', res_abs3.get('message') if res_abs3 and 'message' in res_abs3 else 'OK')
            
        print('-'*30)
