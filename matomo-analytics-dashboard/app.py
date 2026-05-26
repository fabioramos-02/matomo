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
    load_services_trend_daily,
    load_service_cards_month,
)
from utils.data_processor import identify_service_cards


def _load_trend_monthly_chunks(api, start_date, end_date, top5, sid):
    """Chunking mensal para ranges >60 dias. Cada mês é cacheado individualmente."""
    start = dt_date.fromisoformat(start_date)
    end = dt_date.fromisoformat(end_date)
    today = dt_date.today()

    months = []
    cur = start.replace(day=1)
    while cur <= end and cur <= today:
        months.append(cur)
        m, y = cur.month + 1, cur.year
        if m > 12:
            m, y = 1, y + 1
        cur = dt_date(y, m, 1)

    if not months:
        return pd.DataFrame()

    rows = []
    progress = st.progress(0, text=f"Carregando tendência: 0/{len(months)} meses...")
    for i, month_start in enumerate(months):
        month_str = month_start.strftime("%Y-%m-%d")
        records = load_service_cards_month(api, month_str, sid, top5)
        for rec in records:
            rows.append({
                'Data': pd.to_datetime(month_str),
                'Serviço': rec['Nome do Serviço'],
                'Visitas': rec['Visitas'],
            })
        progress.progress((i + 1) / len(months), text=f"Carregando tendência: {i+1}/{len(months)} meses...")
    progress.empty()

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(['Data', 'Serviço']).reset_index(drop=True)

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
from views.portal.tab5_usuarios import render_tab5_usuarios

# Views MS Digital (GA4)
from views.ms_digital.tab1_overview import render_ga_tab1_overview
from views.ms_digital.tab2_funcionalidades import render_ga_tab2_funcionalidades
from views.ms_digital.tab3_perfil import render_ga_tab3_perfil
from views.ms_digital.tab4_jornada import render_ga_tab4_jornada

# Views Cartas de Serviço (PostgreSQL)
from views.cartas.tab1_visao_geral import render_tab1_visao_geral
from views.cartas.tab2_por_orgao import render_tab2_por_orgao
from views.cartas.tab3_qualidade import render_tab3_qualidade
from views.cartas.tab4_satisfacao import render_tab4_satisfacao
from views.cartas.tab5_cruzamentos import render_tab5_cruzamentos
from utils.cartas_data_loaders import (
    load_service_cards_inventory,
    load_service_cards_errors,
    load_service_cards_votes,
    load_service_cards_info_reviews,
)

st.set_page_config(page_title="Analytics Dashboard", page_icon="📊", layout="wide")


def get_api():
    from config import MATOMO_URL, MATOMO_TOKEN, MATOMO_SITE_ID
    if not MATOMO_TOKEN:
        st.error("Token do Matomo não configurado. Adicione MATOMO_TOKEN em secrets.toml.")
        st.stop()
    return MatomoAPI(base_url=MATOMO_URL, token=MATOMO_TOKEN, site_id=MATOMO_SITE_ID)

@st.cache_data(ttl=3600)
def _load_sites(_api):
    return _api.get_sites()


def get_ga_api():
    if not GOOGLE_CLIENT_ID or not GOOGLE_REFRESH_TOKEN:
        st.error("Credenciais OAuth2 GA4 não configuradas. Adicione GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET e GOOGLE_REFRESH_TOKEN em secrets.toml.")
        st.stop()
    from api.google_analytics_client import GoogleAnalyticsAPI
    return GoogleAnalyticsAPI(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN, GOOGLE_PROPERTY_ID)


def to_ga4_date_range(period: str, date_str: str) -> tuple[str, str]:
    d = dt_date.fromisoformat(date_str.split(",")[0])
    today = dt_date.today()
    
    if period == "day":
        return d.isoformat(), d.isoformat()
    if period == "week":
        monday = d - timedelta(days=d.weekday())
        sunday = monday + timedelta(days=6)
        return monday.isoformat(), min(sunday, today).isoformat()
    if period == "month":
        last_day = calendar.monthrange(d.year, d.month)[1]
        start = d.replace(day=1)
        end = d.replace(day=last_day)
        return start.isoformat(), min(end, today).isoformat()
    if period == "year":
        start = dt_date(d.year, 1, 1)
        end = dt_date(d.year, 12, 31)
        return start.isoformat(), min(end, today).isoformat()
    if period == "range":
        parts = date_str.split(",")
        start_s, end_s = parts[0].strip(), parts[1].strip()
        return start_s, end_s
    return d.isoformat(), d.isoformat()


# ==========================================
# BARRA LATERAL
# ==========================================
st.sidebar.title("Filtros")

fonte = st.sidebar.radio(
    "Fonte de Dados",
    ["Portal (Matomo)", "MS Digital (GA4)", "Cartas de Serviço"],
)
st.sidebar.markdown("---")

selected_site_id = int(MATOMO_SITE_ID)

if fonte == "Portal (Matomo)":
    api = get_api()
    with st.spinner("Carregando sites..."):
        sites_data = _load_sites(api)
    if not sites_data:
        st.sidebar.error("Erro ao buscar sites.")
        st.stop()

        
    sites_map = {site["name"]: site["idsite"] for site in sites_data}
    sites_map["Portal de Serviços MS"] = int(MATOMO_SITE_ID)
    default_idx = next((i for i, id_ in enumerate(sites_map.values()) if str(id_) == str(MATOMO_SITE_ID)), 0)
    selected_site_name = st.sidebar.selectbox("Site", list(sites_map.keys()), index=default_idx)
    selected_site_id = sites_map[selected_site_name]
elif fonte == "Cartas de Serviço":
    st.sidebar.info("🗄️ Dados lidos direto do banco PostgreSQL da SETDIG.")
else:
    pass

st.sidebar.markdown("---")

period_map = {"Dia": "day", "Semana": "week", "Mês": "month", "Ano": "year", "Intervalo de datas": "range"}
period_label = st.sidebar.radio("Período", list(period_map.keys()), index=2)
period = period_map[period_label]

if period == "range":
    col1, col2 = st.sidebar.columns(2)
    with col1:
        start_d = st.date_input(
            "Data Início",
            value=dt_date.today() - timedelta(days=30),
            max_value=dt_date.today(),
            format="DD/MM/YYYY",
        )
    with col2:
        end_d = st.date_input(
            "Data Fim",
            value=dt_date.today(),
            max_value=dt_date.today(),
            format="DD/MM/YYYY",
        )
    
    if start_d > end_d:
        st.sidebar.error("❌ A data de início não pode ser maior que a data fim.")
        st.stop()
        
    date = f"{start_d},{end_d}"
else:
    single_date = st.sidebar.date_input("Data de referência", value=dt_date.today(),
                                         max_value=dt_date.today(), format="DD/MM/YYYY")
    date = single_date.strftime("%Y-%m-%d")
    if fonte == "MS Digital (GA4)" and period == "day" and single_date == dt_date.today():
        st.sidebar.warning("⚠️ Dados de hoje podem não estar disponíveis no GA4 (atraso de até 48h).")

# ==========================================
# CABEÇALHO
# ==========================================
_fonte_labels = {
    "Portal (Matomo)": "Portal ms.gov.br",
    "MS Digital (GA4)": "MS Digital App",
    "Cartas de Serviço": "Cartas de Serviço",
}
fonte_label = _fonte_labels.get(fonte, fonte)
periodo_str = (
    f"Intervalo: {start_d.strftime('%d/%m/%Y')} a {end_d.strftime('%d/%m/%Y')}"
    if period == "range"
    else f"Data Base: {single_date.strftime('%d/%m/%Y')} | Recorte: {period_label}"
)

st.title(f"📊 Dashboard Analítico — {fonte_label}")
st.markdown(f"**🗓️ Período:** {periodo_str}")
if fonte == "Cartas de Serviço":
    st.markdown("*Nota: O filtro de data se aplica aos Erros e Votos. O Inventário exibe o retrato global atual.*")

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

    matomo_start, matomo_end = to_ga4_date_range(period, date)
    df_services_trend = pd.DataFrame()
    trend_granularity = 'day'

    df_svc_all = identify_service_cards(df_pages)
    st.session_state["df_svc_all"] = df_svc_all
    top5_matomo = tuple(df_svc_all['Nome do Serviço'].head(5).tolist()) if not df_svc_all.empty else ()

    if period != "day" and matomo_start != matomo_end and top5_matomo:
        _delta = (dt_date.fromisoformat(matomo_end) - dt_date.fromisoformat(matomo_start)).days
        if _delta <= 60:
            trend_granularity = 'day'
            with st.spinner("Carregando evolução temporal dos serviços..."):
                df_services_trend = load_services_trend_daily(api, matomo_start, matomo_end, selected_site_id, top5_matomo)
        elif _delta <= 730:
            trend_granularity = 'month'
            df_services_trend = _load_trend_monthly_chunks(api, matomo_start, matomo_end, top5_matomo, selected_site_id)
        # > 730 dias: df_services_trend permanece vazio, exibe mensagem na view

    # Se for o Portal de Serviços (Site ID 298), adicionamos a aba de acessos identificados
    show_tab5 = (selected_site_id == int(MATOMO_SITE_ID))
    
    if show_tab5:
        tab_list = [
            "1. Perfil do Cidadão",
            "2. Intenção de Busca",
            "3. Serviços Consumidos",
            "4. Fluxo de Navegação",
            "5. Acessos Identificados",
        ]
    else:
        tab_list = [
            "1. Perfil do Cidadão",
            "2. Intenção de Busca",
            "3. Serviços Consumidos",
            "4. Fluxo de Navegação",
        ]
        
    tabs = st.tabs(tab_list)
    
    with tabs[0]:
        render_tab1_perfil(df_cities, df_browsers, df_device_types, df_time, ms_geojson, visits_summary=visits_summary)
    with tabs[1]:
        render_tab2_busca(df_search)
    with tabs[2]:
        render_tab3_servicos(df_pages, df_services=df_svc_all, df_services_trend=df_services_trend, trend_granularity=trend_granularity or 'day')
    with tabs[3]:
        render_tab4_jornada(df_pages, api, period, date, selected_site_id)
    if show_tab5:
        with tabs[4]:
            render_tab5_usuarios(matomo_start, matomo_end)

elif fonte == "Cartas de Serviço":
    from utils.pg_connector import is_db_available
    if not is_db_available():
        st.toast("Operando em modo offline (CSV).")
        
    with st.spinner("Carregando dados das Cartas de Serviço..."):
        df_cs_inventory = load_service_cards_inventory()
        df_cs_errors = load_service_cards_errors()
        df_cs_votes = load_service_cards_votes()
        df_cs_info = load_service_cards_info_reviews()

    # --- Filtros Dinâmicos ---
    cs_start_str, cs_end_str = to_ga4_date_range(period, date)
    start_ts = pd.to_datetime(cs_start_str).tz_localize('UTC')
    end_ts = pd.to_datetime(cs_end_str).tz_localize('UTC') + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

    orgaos_disp = sorted(df_cs_inventory["siglaorgao"].dropna().unique().tolist()) if not df_cs_inventory.empty else []
    selected_orgaos = st.sidebar.multiselect("Filtrar por Órgão", options=orgaos_disp, default=[])

    if selected_orgaos:
        df_cs_inventory = df_cs_inventory[df_cs_inventory["siglaorgao"].isin(selected_orgaos)]
        if not df_cs_errors.empty:
            df_cs_errors = df_cs_errors[df_cs_errors["siglaorgao"].isin(selected_orgaos)]
        if not df_cs_votes.empty:
            df_cs_votes = df_cs_votes[df_cs_votes["siglaorgao"].isin(selected_orgaos)]

    if not df_cs_errors.empty and "data_criacao_erro" in df_cs_errors.columns:
        df_cs_errors["data_criacao_erro"] = pd.to_datetime(df_cs_errors["data_criacao_erro"], utc=True)
        df_cs_errors = df_cs_errors[(df_cs_errors["data_criacao_erro"] >= start_ts) & (df_cs_errors["data_criacao_erro"] <= end_ts)]
        
    if not df_cs_votes.empty and "data_voto" in df_cs_votes.columns:
        df_cs_votes["data_voto"] = pd.to_datetime(df_cs_votes["data_voto"], utc=True)
        df_cs_votes = df_cs_votes[(df_cs_votes["data_voto"] >= start_ts) & (df_cs_votes["data_voto"] <= end_ts)]


    tab_cs1, tab_cs2, tab_cs3, tab_cs4, tab_cs5 = st.tabs([
        "1. Visão Geral",
        "2. Por Órgão",
        "3. Qualidade / Erros",
        "4. Satisfação",
        "5. Cruzamentos Estratégicos",
    ])
    with tab_cs1:
        render_tab1_visao_geral(df_cs_inventory.copy())
    with tab_cs2:
        render_tab2_por_orgao(df_cs_inventory.copy())
    with tab_cs3:
        render_tab3_qualidade(df_cs_errors.copy())
    with tab_cs4:
        render_tab4_satisfacao(df_cs_votes.copy())
    with tab_cs5:
        # Tenta passar dados do Matomo se disponíveis na sessão
        _matomo_pages = st.session_state.get("df_svc_all", None)
        render_tab5_cruzamentos(df_cs_inventory.copy(), df_cs_errors.copy(), df_cs_votes.copy(), _matomo_pages)

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
