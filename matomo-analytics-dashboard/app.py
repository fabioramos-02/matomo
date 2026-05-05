import streamlit as st
import pandas as pd
import calendar
from datetime import date as dt_date, timedelta

from config import DEFAULT_PERIOD, DEFAULT_DATE, MATOMO_SITE_ID, GOOGLE_CREDENTIALS_JSON, GOOGLE_PROPERTY_ID
from api.matomo_client import MatomoAPI
from utils.data_loaders import (
    load_page_data,
    load_search_data,
    load_geography_data,
    load_visit_time_data,
    load_devices_data,
    load_ms_geojson,
)
from utils.ga_data_loaders import (
    load_ga_screens,
    load_ga_search,
    load_ga_geography,
    load_ga_devices,
    load_ga_visit_time,
    load_ga_events,
)
from views.tab1_perfil import render_tab1_perfil
from views.tab2_busca import render_tab2_busca
from views.tab3_servicos import render_tab3_servicos
from views.tab4_jornada import render_tab4_jornada

st.set_page_config(page_title="Matomo Analytics", page_icon="📊", layout="wide")


def get_api():
    from config import MATOMO_URL, MATOMO_TOKEN, MATOMO_SITE_ID
    if not MATOMO_TOKEN:
        st.error("Token do Matomo não configurado. Por favor, adicione-o nas configurações.")
        st.stop()
    return MatomoAPI(base_url=MATOMO_URL, token=MATOMO_TOKEN, site_id=MATOMO_SITE_ID)


def get_ga_api():
    if not GOOGLE_CREDENTIALS_JSON:
        st.error("Credenciais do Google Analytics não configuradas. Adicione GOOGLE_CREDENTIALS_JSON em secrets.toml.")
        st.stop()
    if not GOOGLE_PROPERTY_ID:
        st.error("GOOGLE_PROPERTY_ID não configurado em secrets.toml.")
        st.stop()
    from api.google_analytics_client import GoogleAnalyticsAPI
    return GoogleAnalyticsAPI(GOOGLE_CREDENTIALS_JSON, GOOGLE_PROPERTY_ID)


def to_ga4_date_range(period: str, date_str: str) -> tuple[str, str]:
    d = dt_date.fromisoformat(date_str.split(",")[0])
    if period == "day":
        return d.isoformat(), d.isoformat()
    if period == "week":
        monday = d - timedelta(days=d.weekday())
        sunday = monday + timedelta(days=6)
        return monday.isoformat(), sunday.isoformat()
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
# BARRA LATERAL (Filtros)
# ==========================================
st.sidebar.title("Filtros")

fonte = st.sidebar.radio("Fonte de Dados", ["Portal (Matomo)", "MS Digital (GA4)"])
st.sidebar.markdown("---")

# Seleção Dinâmica de Sites (somente Matomo)
selected_site_id = int(MATOMO_SITE_ID)
if fonte == "Portal (Matomo)":
    api = get_api()
    with st.spinner("Carregando sites..."):
        sites_data = api.get_sites()

    if not sites_data:
        st.sidebar.error("Erro ao buscar sites.")
        st.stop()

    sites_map = {site['name']: site['idsite'] for site in sites_data}
    sites_map["Portal de Serviços MS"] = int(MATOMO_SITE_ID)

    default_site_index = 0
    for i, (name, idsite) in enumerate(sites_map.items()):
        if str(idsite) == str(MATOMO_SITE_ID):
            default_site_index = i
            break

    selected_site_name = st.sidebar.selectbox("Site", list(sites_map.keys()), index=default_site_index)
    selected_site_id = sites_map[selected_site_name]
else:
    st.sidebar.info("Propriedade: MS Digital App")

st.sidebar.markdown("---")

period_map = {
    "Dia": "day",
    "Semana": "week",
    "Mês": "month",
    "Ano": "year",
    "Intervalo de datas": "range"
}
period_label = st.sidebar.radio("Período", list(period_map.keys()), index=2)
period = period_map[period_label]

if period == "range":
    date_range = st.sidebar.date_input(
        "Selecione o período (De - Até)",
        value=(dt_date.today() - timedelta(days=30), dt_date.today()),
        max_value=dt_date.today(),
        format="DD/MM/YYYY"
    )
    if len(date_range) != 2:
        st.sidebar.warning("⚠️ Selecione a data de início e a data de fim no calendário.")
        st.stop()
    start_d, end_d = date_range
    if start_d > end_d:
        st.sidebar.error("❌ A data de início não pode ser maior que a data de fim.")
        st.stop()
    date = f"{start_d},{end_d}"
else:
    single_date = st.sidebar.date_input(
        "Data de referência",
        value=dt_date.today(),
        max_value=dt_date.today(),
        format="DD/MM/YYYY"
    )
    date = single_date.strftime("%Y-%m-%d")

# ==========================================
# CABEÇALHO DO DASHBOARD
# ==========================================
fonte_label = "Portal ms.gov.br" if fonte == "Portal (Matomo)" else "MS Digital App (GA4)"

if period == "range":
    periodo_str = f"Intervalo: {start_d.strftime('%d/%m/%Y')} a {end_d.strftime('%d/%m/%Y')}"
else:
    periodo_str = f"Data Base: {single_date.strftime('%d/%m/%Y')} | Recorte: {period_label}"

st.title(f"📊 Dashboard Analítico — {fonte_label}")
st.markdown(f"**🗓️ Período Analisado:** {periodo_str}")

# ==========================================
# CARREGAMENTO DE DADOS (condicional por fonte)
# ==========================================
df_ga_events = pd.DataFrame()

if fonte == "Portal (Matomo)":
    with st.spinner("Buscando dados no Matomo... Isso pode demorar para períodos longos como 'year'."):
        df_pages = load_page_data(api, period, date, selected_site_id)
        df_search = load_search_data(api, period, date, selected_site_id)
        df_cities = load_geography_data(api, period, date, selected_site_id)
        df_time = load_visit_time_data(api, period, date, selected_site_id)
        df_browsers, df_device_types = load_devices_data(api, period, date, selected_site_id)
        ms_geojson = load_ms_geojson()

    if df_pages.empty:
        st.error("Nenhum dado retornado da API ou ocorreu um erro na conexão.")
        st.stop()

else:
    ga_api = get_ga_api()
    ga_start, ga_end = to_ga4_date_range(period, date)

    with st.spinner(f"Buscando dados no Google Analytics ({ga_start} → {ga_end})..."):
        df_pages = load_ga_screens(ga_api, ga_start, ga_end, GOOGLE_PROPERTY_ID)
        df_search = load_ga_search(ga_api, ga_start, ga_end, GOOGLE_PROPERTY_ID)
        df_cities = load_ga_geography(ga_api, ga_start, ga_end, GOOGLE_PROPERTY_ID)
        df_time = load_ga_visit_time(ga_api, ga_start, ga_end, GOOGLE_PROPERTY_ID)
        df_browsers, df_device_types = load_ga_devices(ga_api, ga_start, ga_end, GOOGLE_PROPERTY_ID)
        df_ga_events = load_ga_events(ga_api, ga_start, ga_end, GOOGLE_PROPERTY_ID)
        ms_geojson = load_ms_geojson()

    if df_pages.empty:
        st.error("Nenhum dado retornado do Google Analytics. Verifique as credenciais e o Property ID.")
        st.stop()

# ==========================================
# RENDERIZAÇÃO DAS ABAS (VIEWS)
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "1. Perfil do Cidadão",
    "2. Intenção de Busca",
    "3. Serviços Consumidos",
    "4. Fluxo de Navegação"
])

with tab1:
    render_tab1_perfil(df_cities, df_browsers, df_device_types, df_time, ms_geojson, fonte=fonte)

with tab2:
    render_tab2_busca(df_search)

with tab3:
    render_tab3_servicos(df_pages, fonte=fonte)

with tab4:
    render_tab4_jornada(df_pages, api if fonte == "Portal (Matomo)" else None,
                        period, date, selected_site_id, fonte=fonte, df_events=df_ga_events)
