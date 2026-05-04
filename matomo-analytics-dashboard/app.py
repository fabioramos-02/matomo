import streamlit as st
import pandas as pd
import plotly.express as px
from config import DEFAULT_PERIOD, DEFAULT_DATE
from api.matomo_client import MatomoAPI
from utils.data_processor import (
    process_page_urls, identify_service_cards, process_search_keywords, process_transitions,
    process_cities_ms, process_visit_time, process_browsers, process_device_types
)

st.set_page_config(page_title="Dashboard Matomo - MS.GOV.BR", layout="wide", page_icon="📊")

# Inicializa API
@st.cache_resource
def get_api():
    return MatomoAPI()

api = get_api()

from datetime import date as dt_date, timedelta

# Sidebar para Filtros
st.sidebar.title("Filtros")

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

st.title("📊 Análise de Jornada do Usuário - Portal de Serviços MS")
st.markdown("""
Este painel consome a API do Matomo para extrair informações sobre acessos, 
buscas e transições (jornada) nas **Cartas de Serviço** do portal.
""")

# Funções com cache para não sobrecarregar a API
@st.cache_data(ttl=3600) # Cache de 1 hora
def load_page_data(p, d):
    data = api.get_page_urls(p, d, limit=500)
    return process_page_urls(data)

@st.cache_data(ttl=3600)
def load_search_data(p, d):
    data = api.get_site_search_keywords(p, d, limit=100)
    return process_search_keywords(data)

@st.cache_data(ttl=3600)
def load_transitions_data(p, d, url):
    data = api.get_transitions(p, d, url)
    return process_transitions(data)

@st.cache_data(ttl=3600)
def load_geography_data(p, d):
    data = api.get_city(p, d, limit=500)
    return process_cities_ms(data)

@st.cache_data(ttl=3600)
def load_visit_time_data(p, d):
    data = api.get_visit_time(p, d)
    return process_visit_time(data)

@st.cache_data(ttl=3600)
def load_devices_data(p, d):
    data_browsers = api.get_browsers(p, d)
    data_types = api.get_device_type(p, d)
    return process_browsers(data_browsers), process_device_types(data_types)

@st.cache_data(ttl=86400) # Cache de 1 dia para o mapa
def load_ms_geojson():
    import urllib.request, json
    url = "https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-50-mun.json"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())

# Carregamento de Dados Principais
with st.spinner("Buscando dados no Matomo... Isso pode demorar para períodos longos como 'year'."):
    df_pages = load_page_data(period, date)
    df_search = load_search_data(period, date)
    df_cities = load_geography_data(period, date)
    df_time = load_visit_time_data(period, date)
    df_browsers, df_device_types = load_devices_data(period, date)
    
if df_pages.empty:
    st.error("Nenhum dado retornado da API ou ocorreu um erro na conexão.")
    st.stop()

# Dividindo em abas
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Visão Executiva", 
    "🗺️ Geografia (MS)", 
    "📝 Cartas de Serviço & Jornada", 
    "🔍 Pesquisas e Geral"
])

with tab1:
    st.header("Resumo Executivo")
    st.markdown("Visualização de alto nível sobre como e quando os usuários acessam o portal.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Picos de Acesso por Horário")
        if not df_time.empty:
            fig_time = px.bar(df_time, x='Hora', y='Visitas', color_discrete_sequence=['#ff7f0e'])
            st.plotly_chart(fig_time, use_container_width=True)
        else:
            st.info("Sem dados de horário disponíveis.")
            
    with col2:
        st.subheader("Tipos de Dispositivo")
        if not df_device_types.empty:
            fig_devices = px.pie(df_device_types, names='Dispositivo', values='Visitas', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_devices, use_container_width=True)
        else:
            st.info("Sem dados de dispositivos disponíveis.")
            
    st.subheader("Top Navegadores")
    if not df_browsers.empty:
        fig_browsers = px.bar(df_browsers, x='Visitas', y='Navegador', orientation='h', color='Visitas', color_continuous_scale='Purples')
        fig_browsers.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_browsers, use_container_width=True)

with tab2:
    st.header("Distribuição Geográfica (Mato Grosso do Sul)")
    st.markdown("Cidades do MS que mais acessaram o portal no período selecionado.")
    if not df_cities.empty:
        col1, col2 = st.columns([2, 1])
        with col1:
            try:
                ms_geojson = load_ms_geojson()
                # O Matomo as vezes retorna 'Unknown' que não mapeia no mapa, vamos ignorar na renderização do mapa
                df_map = df_cities[df_cities['Cidade'] != 'Unknown'].copy()
                
                # Plotly Map
                fig_cities = px.choropleth_mapbox(
                    df_map, 
                    geojson=ms_geojson, 
                    locations='Cidade', 
                    featureidkey='properties.name',
                    color='Visitas',
                    color_continuous_scale='Greens',
                    mapbox_style='carto-positron',
                    zoom=5, 
                    center={'lat': -20.44278, 'lon': -54.64639},
                    opacity=0.7,
                    title="Acessos por Município (MS)"
                )
                fig_cities.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
                st.plotly_chart(fig_cities, use_container_width=True)
            except Exception as e:
                st.warning(f"Não foi possível carregar o mapa interativo. Exibindo gráfico de barras como fallback. ({e})")
                fig_cities = px.bar(df_cities.head(15), x='Cidade', y='Visitas', color='Visitas', color_continuous_scale='Greens', title="Top 15 Cidades do MS")
                st.plotly_chart(fig_cities, use_container_width=True)
        with col2:
            st.dataframe(df_cities, height=400)
    else:
        st.info("Nenhum dado de cidade encontrado para o MS no período.")

with tab3:
    st.header("Top Cartas de Serviço Mais Acessadas")
    st.markdown("*Identificadas automaticamente via análise de padrão nas URLs.*")
    
    df_services = identify_service_cards(df_pages)
    
    if not df_services.empty:
        # Gráfico
        fig = px.bar(df_services.head(10), x='Visitas', y='URL', orientation='h', 
                     title="Top 10 Cartas de Serviço", color='Visitas', color_continuous_scale='Blues')
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
        
        # Detalhe / Jornada do Top 1
        st.subheader("Jornada da Principal Carta de Serviço")
        top_service_url = df_services.iloc[0]['URL']
        st.write(f"Analisando a URL: `{top_service_url}`")
        
        transitions = load_transitions_data(period, date, top_service_url)
        
        col_origem, col_destino = st.columns(2)
        with col_origem:
            st.write("⬅️ **De onde vieram (Páginas Anteriores)**")
            if transitions.get('origens'):
                st.table(pd.DataFrame(transitions['origens']))
            else:
                st.info("Sem dados suficientes.")
                
        with col_destino:
            st.write("➡️ **Para onde foram (Próximas Páginas)**")
            if transitions.get('destinos'):
                st.table(pd.DataFrame(transitions['destinos']))
            else:
                st.info("Sem dados suficientes.")
    else:
        st.warning("Não foi possível identificar Cartas de Serviço no padrão de URLs para este período.")

with tab4:
    col1, col2 = st.columns(2)
    with col1:
        st.header("O que os cidadãos buscam?")
        if not df_search.empty:
            fig_search = px.bar(df_search.head(15), x='Buscas', y='Palavra-chave', orientation='h',
                                title="Top 15 Termos", color='Buscas', color_continuous_scale='Teal')
            fig_search.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_search, use_container_width=True)
        else:
            st.info("Nenhum dado de busca.")
            
    with col2:
        st.header("Páginas Mais Acessadas (Geral)")
        st.dataframe(df_pages.head(50), height=400)
