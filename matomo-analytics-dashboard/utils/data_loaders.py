
import pandas as pd
import streamlit as st
import json
import urllib.request
from utils.data_processor import (
    process_page_urls,
    process_search_keywords,
    extract_search_from_page_urls,
    process_transitions,
    process_cities_ms,
    process_visit_time,
    process_browsers,
    process_device_types,
    process_services_trend,
)

@st.cache_data(ttl=3600)
def load_page_data(_api, p, d, sid):
    data = _api.get_page_urls(p, d, site_id=sid, limit=500)
    return process_page_urls(data)

@st.cache_data(ttl=3600)
def load_search_data(_api, p, d, sid):
    # Fonte 1: SiteSearch nativo do Matomo
    raw = _api.get_site_search_keywords(p, d, site_id=sid, limit=100)
    df_site_search = process_search_keywords(raw)

    # Fonte 2: chamada dedicada flat=1 + filter_pattern=q= — pega TODOS os termos sem truncar
    raw_q = _api.get_search_page_urls(p, d, site_id=sid)
    df_url_search = extract_search_from_page_urls(
        process_page_urls(raw_q) if isinstance(raw_q, list) else pd.DataFrame()
    )

    combined = pd.concat([df_site_search, df_url_search], ignore_index=True)
    if combined.empty:
        return combined
    combined = combined.groupby('Palavra-chave', as_index=False)['Buscas'].sum()
    combined = combined.sort_values('Buscas', ascending=False).reset_index(drop=True)
    return combined

@st.cache_data(ttl=3600)
def load_transitions_data(_api, p, d, url, sid):
    data = _api.get_transitions(p, d, url, site_id=sid)
    if data is None:
        return None  # Timeout — sinaliza diferente de dados vazios
    return process_transitions(data)

@st.cache_data(ttl=3600)
def load_geography_data(_api, p, d, sid):
    data = _api.get_city(p, d, site_id=sid, limit=500)
    return process_cities_ms(data)

@st.cache_data(ttl=3600)
def load_visit_time_data(_api, p, d, sid):
    data = _api.get_visit_time(p, d, site_id=sid)
    return process_visit_time(data)

@st.cache_data(ttl=3600)
def load_devices_data(_api, p, d, sid):
    data_browsers = _api.get_browsers(p, d, site_id=sid)
    data_types = _api.get_device_type(p, d, site_id=sid)
    return process_browsers(data_browsers), process_device_types(data_types)

@st.cache_data(ttl=3600)
def load_outlinks_data(_api, p, d, sid):
    return _api.get_outlinks(p, d, site_id=sid, limit=50)

@st.cache_data(ttl=3600)
def load_entry_pages_data(_api, p, d, sid):
    return _api.get_entry_pages(p, d, site_id=sid, limit=20)

@st.cache_data(ttl=3600)
def load_last_visits_data(_api, p, d, sid, segment):
    return _api.get_last_visits(p, d, site_id=sid, segment=segment, limit=10)

@st.cache_data(ttl=3600)
def load_visits_summary_data(_api, p, d, sid):
    return _api.get_visits_summary(p, d, site_id=sid)

@st.cache_data(ttl=3600)
def load_services_trend_daily(_api, start_date, end_date, sid, top_services):
    """Tendência diária — processa em blocos de 7 dias para evitar erro 500 da API do Matomo."""
    from datetime import date as dt_date, timedelta
    
    start = dt_date.fromisoformat(start_date)
    end = dt_date.fromisoformat(end_date)
    
    raw = {}
    current = start
    
    while current <= end:
        chunk_end = current + timedelta(days=6)
        if chunk_end > end:
            chunk_end = end
            
        chunk_raw = _api.get_page_urls_trend(
            current.isoformat(), 
            chunk_end.isoformat(), 
            site_id=sid, 
            granularity='day'
        )
        if chunk_raw and isinstance(chunk_raw, dict):
            raw.update(chunk_raw)
            
        current = chunk_end + timedelta(days=1)

    if not raw:
        return pd.DataFrame()
        
    return process_services_trend(raw, list(top_services))


@st.cache_data(ttl=3600)
def load_service_cards_month(_api, month_date, sid, top_services):
    """Cartas de serviço para um único mês — cacheável individualmente."""
    from utils.data_processor import identify_service_cards
    raw = _api.get_page_urls('month', month_date, site_id=sid, limit=100)
    df = process_page_urls(raw)
    if df.empty:
        return []
    df_cards = identify_service_cards(df)
    top_set = set(top_services)
    df_top = df_cards[df_cards['Nome do Serviço'].isin(top_set)]
    return df_top[['Nome do Serviço', 'Visitas']].to_dict('records')


@st.cache_data(ttl=86400)
def load_ms_geojson():
    url = "https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-50-mun.json"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())
