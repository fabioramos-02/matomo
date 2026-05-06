import streamlit as st
import pandas as pd
import calendar
from datetime import date as dt_date, timedelta

from config import DEFAULT_PERIOD, DEFAULT_DATE, MATOMO_SITE_ID, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN, GOOGLE_PROPERTY_ID
from api.matomo_client import MatomoAPI

# Loaders Matomo
from utils.data_loaders import (
    load_page_data,
    load_search_data,
    load_geography_data,
    load_visit_time_data,
    load_devices_data,
    load_ms_geojson,
    load_visits_summary_data,
)

# Loaders GA4
from utils.ga_data_loaders import (
    load_ga_screens,
    load_ga_geography,
    load_ga_devices,
    load_ga_visit_time,
    load_ga_events,
    load_ga_overview,
    load_ga_platform,
    load_ga_funnel,
    load_ga_services,
    load_ga_services_trend,
    load_ga_external_links,
    load_ga_country_map,
)

# Views Portal (Matomo)
from views.portal.tab1_perfil import render_tab1_perfil
from views.portal.tab2_busca import render_tab2_busca
from views.portal.tab3_servicos import render_tab3_servicos
from views.portal.tab4_jornada import render_tab4_jornada

# Views MS Digital (GA4)
from views.ms_digital.tab1_overview import render_ga_tab1_overview
from views.ms_digital.tab2_funcionalidades import render_ga_tab2_funcionalidades
from views.ms_digital.tab3_perfil import render_ga_tab3_perfil
from views.ms_digital.tab4_jornada import render_ga_tab4_jornada

st.set_page_config(page_title="Analytics Dashboard", page_icon="📊", layout="wide")


def get_api():
    from config import MATOMO_URL, MATOMO_TOKEN, MATOMO_SITE_ID
    if not MATOMO_TOKEN:
        st.error("Token do Matomo não configurado. Adicione MATOMO_TOKEN em secrets.toml.")
        st.stop()
    return MatomoAPI(base_url=MATOMO_URL, token=MATOMO_TOKEN, site_id=MATOMO_SITE_ID)


def get_ga_api():
    if not GOOGLE_CLIENT_ID or not GOOGLE_REFRESH_TOKEN:
        st.error("Credenciais OAuth2 GA4 não configuradas. Adicione GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET e GOOGLE_REFRESH_TOKEN em secrets.toml.")
        st.stop()
    from api.google_analytics_client import GoogleAnalyticsAPI
    return GoogleAnalyticsAPI(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN, GOOGLE_PROPERTY_ID)


def to_ga4_date_range(period: str, date_str: str) -> tuple[str, str]:
    d = dt_date.fromisoformat(date_str.split(",")[0])
    if period == "day":
        return d.isoformat(), d.isoformat()
    if period == "week":
        monday = d - timedelta(days=d.weekday())
        return monday.isoformat(), (monday + timedelta(days=6)).isoformat()
    if period == "month":
        last_day = calendar.monthrange(d.year, d.month)[1]
        return d.replace(day=1).isoformat(), d.replace(day=last_day).isoformat()
    if period == "year":
        return f"{d.year}-01-01", f"{d.year}-12-31"
    if period == "range":
        parts = date_str.split(",")
        return parts[0].strip(), parts[1].strip()
    return d.isoformat(), d.isoformat()


# ==========================================
# BARRA LATERAL
# ==========================================
st.sidebar.title("Filtros")

fonte = st.sidebar.radio("Fonte de Dados", ["Portal (Matomo)", "MS Digital (GA4)"])
st.sidebar.markdown("---")

selected_site_id = int(MATOMO_SITE_ID)

if fonte == "Portal (Matomo)":
    api = get_api()
    with st.spinner("Carregando sites..."):
        sites_data = api.get_sites()
    if not sites_data:
        st.sidebar.error("Erro ao buscar sites.")
        st.stop()
    sites_map = {site["name"]: site["idsite"] for site in sites_data}
    sites_map["Portal de Serviços MS"] = int(MATOMO_SITE_ID)
    default_idx = next((i for i, id_ in enumerate(sites_map.values()) if str(id_) == str(MATOMO_SITE_ID)), 0)
    selected_site_name = st.sidebar.selectbox("Site", list(sites_map.keys()), index=default_idx)
    selected_site_id = sites_map[selected_site_name]
else:
    pass

st.sidebar.markdown("---")

period_map = {"Dia": "day", "Semana": "week", "Mês": "month", "Ano": "year", "Intervalo de datas": "range"}
period_label = st.sidebar.radio("Período", list(period_map.keys()), index=2)
period = period_map[period_label]

if period == "range":
    date_range = st.sidebar.date_input(
        "De - Até",
        value=(dt_date.today() - timedelta(days=30), dt_date.today()),
        max_value=dt_date.today(),
        format="DD/MM/YYYY",
    )
    if len(date_range) != 2:
        st.sidebar.warning("⚠️ Selecione início e fim.")
        st.stop()
    start_d, end_d = date_range
    if start_d > end_d:
        st.sidebar.error("❌ Data início > data fim.")
        st.stop()
    date = f"{start_d},{end_d}"
else:
    single_date = st.sidebar.date_input("Data de referência", value=dt_date.today(),
                                         max_value=dt_date.today(), format="DD/MM/YYYY")
    date = single_date.strftime("%Y-%m-%d")

# ==========================================
# CABEÇALHO
# ==========================================
fonte_label = "Portal ms.gov.br" if fonte == "Portal (Matomo)" else "MS Digital App (GA4)"
periodo_str = (
    f"Intervalo: {start_d.strftime('%d/%m/%Y')} a {end_d.strftime('%d/%m/%Y')}"
    if period == "range"
    else f"Data Base: {single_date.strftime('%d/%m/%Y')} | Recorte: {period_label}"
)

st.title(f"📊 Dashboard Analítico — {fonte_label}")
st.markdown(f"**🗓️ Período:** {periodo_str}")

# ==========================================
# CARREGAMENTO E RENDERIZAÇÃO
# ==========================================
if fonte == "Portal (Matomo)":
    with st.spinner("Buscando dados no Matomo..."):
        df_pages = load_page_data(api, period, date, selected_site_id)
        df_search = load_search_data(api, period, date, selected_site_id)
        df_cities = load_geography_data(api, period, date, selected_site_id)
        df_time = load_visit_time_data(api, period, date, selected_site_id)
        df_browsers, df_device_types = load_devices_data(api, period, date, selected_site_id)
        visits_summary = load_visits_summary_data(api, period, date, selected_site_id)
        ms_geojson = load_ms_geojson()

    if df_pages.empty:
        st.error("Nenhum dado retornado do Matomo.")
        st.stop()

    tab1, tab2, tab3, tab4 = st.tabs([
        "1. Perfil do Cidadão",
        "2. Intenção de Busca",
        "3. Serviços Consumidos",
        "4. Fluxo de Navegação",
    ])
    with tab1:
        render_tab1_perfil(df_cities, df_browsers, df_device_types, df_time, ms_geojson, visits_summary=visits_summary)
    with tab2:
        render_tab2_busca(df_search)
    with tab3:
        render_tab3_servicos(df_pages)
    with tab4:
        render_tab4_jornada(df_pages, api, period, date, selected_site_id)

else:
    ga_api = get_ga_api()
    ga_start, ga_end = to_ga4_date_range(period, date)

    with st.spinner(f"Buscando dados no Google Analytics ({ga_start} → {ga_end})..."):
        ga_overview = load_ga_overview(ga_api, ga_start, ga_end, GOOGLE_PROPERTY_ID)
        df_platform = load_ga_platform(ga_api, ga_start, ga_end, GOOGLE_PROPERTY_ID)
        df_screens = load_ga_screens(ga_api, ga_start, ga_end, GOOGLE_PROPERTY_ID)
        df_events = load_ga_events(ga_api, ga_start, ga_end, GOOGLE_PROPERTY_ID)
        df_cities = load_ga_geography(ga_api, ga_start, ga_end, GOOGLE_PROPERTY_ID)
        df_time = load_ga_visit_time(ga_api, ga_start, ga_end, GOOGLE_PROPERTY_ID)
        df_os, df_device_types = load_ga_devices(ga_api, ga_start, ga_end, GOOGLE_PROPERTY_ID)
        df_funnel = load_ga_funnel(ga_api, ga_start, ga_end, GOOGLE_PROPERTY_ID)
        df_services = load_ga_services(ga_api, ga_start, ga_end, GOOGLE_PROPERTY_ID)
        top5 = df_services["Serviço"].head(5).tolist() if not df_services.empty else []
        df_services_trend = load_ga_services_trend(ga_api, ga_start, ga_end, GOOGLE_PROPERTY_ID, tuple(top5))
        df_external_links = load_ga_external_links(ga_api, ga_start, ga_end, GOOGLE_PROPERTY_ID)
        df_country_map = load_ga_country_map(ga_api, ga_start, ga_end, GOOGLE_PROPERTY_ID)
        ms_geojson = load_ms_geojson()

    if ga_overview["total_users"] == 0 and df_screens.empty:
        st.error("Nenhum dado retornado do Google Analytics. Verifique as credenciais e o acesso à propriedade.")
        st.stop()

    tab1, tab2, tab3, tab4 = st.tabs([
        "1. Visão Geral",
        "2. Funcionalidades",
        "3. Perfil Técnico",
        "4. Jornada do Usuário",
    ])
    with tab1:
        render_ga_tab1_overview(ga_overview, df_platform, df_funnel)
    with tab2:
        render_ga_tab2_funcionalidades(df_services, df_services_trend, df_external_links)
    with tab3:
        render_ga_tab3_perfil(df_cities, df_os, df_device_types, df_time, ms_geojson, df_country_map)
    with tab4:
        render_ga_tab4_jornada(df_funnel)
