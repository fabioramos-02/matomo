from datetime import date as _dt_date, timedelta as _timedelta

import streamlit as st
from utils.ga_data_processor import (
    process_ga_screens,
    process_ga_search,
    process_ga_cities,
    process_ga_devices,
    process_ga_visit_time,
    process_ga_events,
    process_ga_overview,
    process_ga_platform,
    process_ga_funnel,
    process_ga_services,
    process_ga_services_trend,
    process_ga_external_links,
    process_ga_country_map,
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


@st.cache_data(ttl=3600)
def load_ga_overview(_ga_api, start_date, end_date, property_id):
    data = _ga_api.get_overview(start_date, end_date)
    return process_ga_overview(data)


@st.cache_data(ttl=3600)
def load_ga_platform(_ga_api, start_date, end_date, property_id):
    data = _ga_api.get_platform(start_date, end_date)
    return process_ga_platform(data)


@st.cache_data(ttl=3600)
def load_ga_funnel(_ga_api, start_date, end_date, property_id):
    data = _ga_api.get_funnel_events(start_date, end_date)
    return process_ga_funnel(data)


@st.cache_data(ttl=3600)
def load_ga_services(_ga_api, start_date, end_date, property_id):
    data = _ga_api.get_services(start_date, end_date)
    return process_ga_services(data)


@st.cache_data(ttl=3600)
def load_ga_services_trend(_ga_api, start_date, end_date, property_id, top_services):
    data = _ga_api.get_services_trend(start_date, end_date)
    return process_ga_services_trend(data, top_services)


@st.cache_data(ttl=3600)
def load_ga_external_links(_ga_api, start_date, end_date, property_id):
    data = _ga_api.get_external_links(start_date, end_date)
    return process_ga_external_links(data)


@st.cache_data(ttl=3600)
def load_ga_country_map(_ga_api, start_date, end_date, property_id):
    data = _ga_api.get_country_map(start_date, end_date)
    return process_ga_country_map(data)


def _sum_first_open(funnel_df) -> tuple[int, int]:
    if funnel_df is None or funnel_df.empty:
        return 0, 0
    row = funnel_df[funnel_df["Evento"] == "first_open"]
    if row.empty:
        return 0, 0
    users = int(row.iloc[0].get("Usuários", 0) or 0)
    events = int(row.iloc[0].get("Ocorrências", 0) or 0)
    return users, events


@st.cache_data(ttl=21600)
def load_ga_downloads_lifetime(_ga_api, property_id, lifetime_start: str = "2020-01-01"):
    today = _dt_date.today().isoformat()
    data = _ga_api.get_funnel_events(lifetime_start, today)
    df = process_ga_funnel(data)
    users, events = _sum_first_open(df)
    return {"start": lifetime_start, "end": today, "users": users, "events": events}


@st.cache_data(ttl=21600)
def load_ga_downloads_last12m(_ga_api, property_id):
    end = _dt_date.today()
    start = end - _timedelta(days=365)
    data = _ga_api.get_funnel_events(start.isoformat(), end.isoformat())
    df = process_ga_funnel(data)
    users, events = _sum_first_open(df)
    return {"start": start.isoformat(), "end": end.isoformat(), "users": users, "events": events}
