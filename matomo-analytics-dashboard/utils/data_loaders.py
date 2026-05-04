import streamlit as st
import json
import urllib.request
from utils.data_processor import (
    process_page_urls, 
    process_search_keywords, 
    process_transitions,
    process_cities_ms, 
    process_visit_time, 
    process_browsers, 
    process_device_types
)

@st.cache_data(ttl=3600)
def load_page_data(_api, p, d, sid):
    data = _api.get_page_urls(p, d, site_id=sid, limit=500)
    return process_page_urls(data)

@st.cache_data(ttl=3600)
def load_search_data(_api, p, d, sid):
    data = _api.get_site_search_keywords(p, d, site_id=sid, limit=100)
    return process_search_keywords(data)

@st.cache_data(ttl=3600)
def load_transitions_data(_api, p, d, url, sid):
    data = _api.get_transitions(p, d, url, site_id=sid)
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

@st.cache_data(ttl=86400)
def load_ms_geojson():
    url = "https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-50-mun.json"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())
