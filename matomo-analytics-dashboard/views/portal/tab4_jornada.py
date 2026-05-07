import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils.data_loaders import load_transitions_data, load_outlinks_data, load_entry_pages_data

def _range_is_long(date_str, threshold_days=60):
    try:
        parts = date_str.split(",")
        delta = datetime.strptime(parts[1], "%Y-%m-%d") - datetime.strptime(parts[0], "%Y-%m-%d")
        return delta.days > threshold_days
    except Exception:
        return False

def _render_tab4_ga4(df_events):
    st.header("Eventos do App (Jornada)")
    st.markdown("O GA4 não possui API de Transições como o Matomo. A análise de jornada usa **eventos rastreados** pelo app.")

    if df_events is None or df_events.empty:
        st.warning("Sem dados de eventos para este período.")
        return

    col_chart, col_table = st.columns([1.2, 1])
    with col_chart:
        st.subheader("Top Eventos por Volume")
        fig = px.bar(
            df_events.head(15),
            x="Acessos", y="Evento", orientation="h",
            color="Acessos", color_continuous_scale="Purples"
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, width="stretch")

    with col_table:
        st.subheader("Tabela de Eventos")
        df_show = df_events.head(20).copy()
        df_show.insert(0, "#", df_show.index + 1)
        st.dataframe(df_show[["#", "Evento", "Acessos"]], hide_index=True, width="stretch")

    st.info("💡 Para análise de funil e sequência de telas, acesse diretamente o GA4 em Analytics > Exploração > Funil.")


def render_tab4_jornada(df_pages, api, period, date, selected_site_id, fonte="Portal (Matomo)", df_events=None):
    if fonte == "MS Digital (GA4)":
        _render_tab4_ga4(df_events)
        return

    st.header("Fluxo de Navegação (Jornada)")
    st.markdown("O portal do governo atua muitas vezes como um **Hub**: o cidadão entra, pesquisa e é direcionado para o serviço real em outro sistema (Detran, Sefaz, etc).")
    
    st.markdown("---")
    
    col_entry, col_out = st.columns(2)
    
    # 1. PORTAS DE ENTRADA
    with col_entry:
        st.subheader("🚪 Portas de Entrada (Landing Pages)")
        st.markdown("Por onde os cidadãos começaram a navegação?")
        with st.spinner("Carregando entradas..."):
            entradas = load_entry_pages_data(api, period, date, selected_site_id)
            if entradas:
                df_entry = pd.DataFrame(entradas)
                if 'label' in df_entry.columns and 'nb_visits' in df_entry.columns:
                    df_entry = df_entry[['label', 'nb_visits']].rename(columns={'label': 'Página Inicial', 'nb_visits': 'Entradas'})
                    df_entry['Página Inicial'] = df_entry['Página Inicial'].apply(lambda x: "Home (Index)" if x == "/" else x)
                    
                    fig_entry = px.bar(df_entry.head(10), x='Entradas', y='Página Inicial', orientation='h', color='Entradas', color_continuous_scale='Greens')
                    fig_entry.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_entry, width="stretch")
            else:
                st.info("Sem dados de entrada no período.")

    # 2. OUTLINKS
    with col_out:
        st.subheader("✈️ Fuga do Hub (Links Externos)")
        st.markdown("Para onde os cidadãos vão ao sair do portal?")
        with st.spinner("Analisando destinos..."):
            outlinks = load_outlinks_data(api, period, date, selected_site_id)
            if outlinks:
                df_out = pd.DataFrame(outlinks)
                if 'label' in df_out.columns and 'nb_visits' in df_out.columns:
                    df_out = df_out[['label', 'nb_visits']].rename(columns={'label': 'Domínio de Destino', 'nb_visits': 'Saídas'})
                    df_out = df_out[~df_out['Domínio de Destino'].str.contains('ms.gov.br/login')]
                    
                    fig_out = px.bar(df_out.head(10), x='Saídas', y='Domínio de Destino', orientation='h', color='Saídas', color_continuous_scale='Reds')
                    fig_out.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_out, width="stretch")
            else:
                st.info("Sem dados de saída no período.")

    st.markdown("---")

    # 3. MACRO-FLUXO DA HOME
    st.subheader("🛣️ Padrão Comportamental: A partir da Página Principal")
    st.markdown("O que o cidadão acessa logo após entrar na Home (`/index`)?")

    url_home = "https://www.ms.gov.br/"

    # Períodos pesados exigem confirmação do usuário para evitar timeout silencioso
    is_heavy_period = period in ("year",) or (period == "range" and "," in date and _range_is_long(date))

    if is_heavy_period:
        st.info("⚠️ Período longo selecionado. A análise de transições pode demorar até 3 minutos.")
        carregar = st.button("Carregar análise de macro-fluxo (pode ser lento)", key="btn_transitions")
    else:
        carregar = True

    def _render_transitions(transitions):
        if transitions is None:
            st.error("Timeout ao consultar a API de transições (>180s). Tente um período menor como 'Mês' ou 'Semana'.")
            return
        if not transitions or not transitions.get('followingPages'):
            st.warning("Sem dados de transição para este período.")
            return

        df_trans = pd.DataFrame(transitions['followingPages'])
        df_trans = df_trans.rename(columns={'label': 'Página de Destino', 'referrals': 'Acessos'})
        df_trans['Página de Destino'] = df_trans['Página de Destino'].str.replace('ms.gov.br', '', regex=False)

        def classificar_jornada(url):
            if not url or url == '/': return 'Recargas/Outros'
            parts = [p for p in url.split('/') if p]
            if len(parts) == 0: return 'Recargas/Outros'
            first = parts[0].lower()
            if first == 'buscar' or 'q=' in url: return 'Busca Interna no Portal'
            if first in ['workspace', 'login']: return 'Acesso a Sistemas (Login/Workspace)'
            if first in ['noticias']: return 'Notícias'
            if len(parts) == 1: return 'Exploração por Categoria/Órgão'
            if len(parts) >= 2: return 'Acesso Direto ao Serviço'
            return 'Outros'

        df_trans['Tipo de Jornada'] = df_trans['Página de Destino'].apply(classificar_jornada)

        col_chart, col_table = st.columns([1, 1.2])
        with col_chart:
            df_group = df_trans.groupby('Tipo de Jornada')['Acessos'].sum().reset_index()
            fig_macro = px.pie(df_group, values='Acessos', names='Tipo de Jornada', hole=0.5,
                               color_discrete_sequence=px.colors.qualitative.Prism)
            fig_macro.update_traces(textposition='inside', textinfo='percent')
            fig_macro.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5))
            st.plotly_chart(fig_macro, width="stretch")
        with col_table:
            st.write("**Top 10 Destinos Específicos a partir da Home:**")
            df_show = df_trans[~df_trans['Tipo de Jornada'].isin(['Recargas/Outros'])].head(10)
            st.dataframe(
                df_show[['Página de Destino', 'Tipo de Jornada', 'Acessos']],
                hide_index=True,
                width="stretch"
            )

    if carregar:
        with st.spinner("Analisando macro-fluxo... (até 3 min para períodos longos)"):
            transitions = load_transitions_data(api, period, date, url_home, selected_site_id)
        _render_transitions(transitions)
