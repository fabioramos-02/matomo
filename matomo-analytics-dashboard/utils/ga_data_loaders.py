import streamlit as st
from utils.ga_data_processor import (
    process_ga_screens,
    process_ga_search,
    process_ga_cities,
    process_ga_devices,
    process_ga_visit_time,
    process_ga_events,
)


@st.cache_data(ttl=3600)
def load_ga_screens(_ga_api, start_date, end_date, property_id):
    data = _ga_api.get_screen_views(start_date, end_date)
    return process_ga_screens(data)


@st.cache_data(ttl=3600)
def load_ga_search(_ga_api, start_date, end_date, property_id):
    data = _ga_api.get_search_keywords(start_date, end_date)
    return process_ga_search(data)


@st.cache_data(ttl=3600)
def load_ga_geography(_ga_api, start_date, end_date, property_id):
    data = _ga_api.get_geography(start_date, end_date)
    return process_ga_cities(data)


@st.cache_data(ttl=3600)
def load_ga_devices(_ga_api, start_date, end_date, property_id):
    data = _ga_api.get_devices(start_date, end_date)
    return process_ga_devices(data)


@st.cache_data(ttl=3600)
def load_ga_visit_time(_ga_api, start_date, end_date, property_id):
    data = _ga_api.get_visit_time(start_date, end_date)
    return process_ga_visit_time(data)


@st.cache_data(ttl=3600)
def load_ga_events(_ga_api, start_date, end_date, property_id):
    data = _ga_api.get_top_events(start_date, end_date)
    return process_ga_events(data)
