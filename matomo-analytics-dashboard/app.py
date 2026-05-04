import streamlit as st
from datetime import date as dt_date, timedelta

# Importa configurações e inicialização de API
from config import DEFAULT_PERIOD, DEFAULT_DATE, MATOMO_SITE_ID
from api.matomo_client import MatomoAPI

# Importa Loaders (que possuem o cache do Streamlit)
from utils.data_loaders import (
    load_page_data,
    load_search_data,
    load_geography_data,
    load_visit_time_data,
    load_devices_data,
    load_ms_geojson
)

# Importa as Views (Abas)
from views.tab1_perfil import render_tab1_perfil
from views.tab2_busca import render_tab2_busca
from views.tab3_servicos import render_tab3_servicos
from views.tab4_jornada import render_tab4_jornada

# Configuração da Página
st.set_page_config(page_title="Matomo Analytics", page_icon="📊", layout="wide")

# Instancia a API sem cache para evitar problemas de versão na nuvem
def get_api():
    from config import MATOMO_URL, MATOMO_TOKEN, MATOMO_SITE_ID
    if not MATOMO_TOKEN:
        st.error("Token do Matomo não configurado. Por favor, adicione-o nas configurações.")
        st.stop()
    return MatomoAPI(base_url=MATOMO_URL, token=MATOMO_TOKEN, site_id=MATOMO_SITE_ID)

api = get_api()

# ==========================================
# BARRA LATERAL (Filtros)
# ==========================================
st.sidebar.title("Filtros")

# Seleção Dinâmica de Sites
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
if period == "range":
    periodo_str = f"Intervalo: {start_d.strftime('%d/%m/%Y')} a {end_d.strftime('%d/%m/%Y')}"
else:
    periodo_str = f"Data Base: {single_date.strftime('%d/%m/%Y')} | Recorte: {period_label}"

st.title(f"📊 Dashboard Analítico - {selected_site_name}")
st.markdown(f"**🗓️ Período Analisado:** {periodo_str}")
st.markdown("""
Este painel consome a API do Matomo para extrair informações sobre acessos, 
buscas e transições (jornada) nas **Cartas de Serviço** do portal.
""")

# ==========================================
# CARREGAMENTO GLOBAL DE DADOS
# ==========================================
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
    render_tab1_perfil(df_cities, df_browsers, df_device_types, df_time, ms_geojson)

with tab2:
    render_tab2_busca(df_search)

with tab3:
    render_tab3_servicos(df_pages)

with tab4:
    render_tab4_jornada(df_pages, api, period, date, selected_site_id)
