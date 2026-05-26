"""
Aba 5 — Análise de Acessos e Usuários do Portal (PostgreSQL)
Métricas de login único dinâmicas com base no período selecionado.
"""
import streamlit as st
import pandas as pd
import plotly.express as px

from utils.pg_connector import is_db_controlador_available
from utils.cartas_data_loaders import load_portal_users_consolidated, load_portal_users_trend


def render_tab5_usuarios(start_date: str, end_date: str):
    st.subheader("🔒 Análise de Acessos e Usuários Identificados (Portal de Serviços)")
    st.markdown(
        "Esta seção apresenta uma análise estratégica dos logins de cidadãos identificados "
        "no Portal de Serviços (app_id=36) através do banco de dados relacional da SETDIG."
    )

    if not is_db_controlador_available():
        st.warning(
            "⚠️ **Conexão com o Banco de Dados Indisponível**\n\n"
            "O banco de dados PostgreSQL `controlador_prd` está offline ou as credenciais de acesso não "
            "estão configuradas no arquivo `secrets.toml`. Esta aba necessita de uma conexão ativa "
            "para realizar as consultas dinâmicas de login."
        )
        return

    # 1. Carregar Dados Consolidados
    with st.spinner("Consultando dados de acessos consolidados..."):
        df_consolidated = load_portal_users_consolidated(start_date, end_date)

    if df_consolidated.empty:
        st.info("Nenhum registro de acesso encontrado para o período selecionado ou erro na consulta.")
        return

    # Normaliza colunas para minúsculas (compatibilidade garantida)
    df_consolidated.columns = [c.lower() for c in df_consolidated.columns]

    try:
        total_usuarios = int(df_consolidated["qtde_total_usuarios_portal"].iloc[0])
        ativos_periodo = int(df_consolidated["qtde_acessos_periodo"].iloc[0])
        pct_uso = float(df_consolidated["percentual_acesso_periodo"].iloc[0])
    except Exception as e:
        st.error(f"Erro ao processar as colunas de métricas: {e}")
        return

    # ------------------------------------------------------------------ #
    # KPIs                                                                 #
    # ------------------------------------------------------------------ #
    st.markdown("### 📊 Métricas de Utilização do Portal")
    col1, col2, col3 = st.columns(3)
    
    col1.metric(
        "👥 Total de Usuários Cadastrados",
        f"{total_usuarios:,}".replace(",", "."),
        help="Quantidade acumulada histórica de usuários únicos que já se autenticaram no Portal de Serviços."
    )
    col2.metric(
        "🎯 Usuários Ativos no Período",
        f"{ativos_periodo:,}".replace(",", "."),
        help="Quantidade de usuários únicos que realizaram pelo menos um login dentro do período selecionado."
    )
  

    st.markdown("---")

    # 2. Carregar Dados de Tendência Diária
    st.markdown("### 📈 Evolução de Acessos Únicos no Período")
    st.caption("Acompanhe o engajamento diário medido por usuários autenticados únicos.")

    with st.spinner("Buscando tendência de acessos diários..."):
        df_trend = load_portal_users_trend(start_date, end_date)

    if not df_trend.empty:
        df_trend.columns = [c.lower() for c in df_trend.columns]
        
        # Criação do gráfico de linha com visual premium
        fig_trend = px.line(
            df_trend,
            x="data_acesso",
            y="qtde_usuarios",
            markers=True,
            labels={"qtde_usuarios": "Usuários Únicos", "data_acesso": "Data"},
            color_discrete_sequence=["#2563EB"]  # Azul Premium
        )
        
        fig_trend.update_layout(
            hovermode="x unified",
            xaxis_title="",
            yaxis_title="Usuários Únicos Ativos",
            margin=dict(t=10, b=10, l=10, r=10),
            height=380,
            separators=',.'
        )
        fig_trend.update_traces(
            line=dict(width=3),
            marker=dict(size=6, symbol="circle")
        )
        
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Não há dados de tendência disponíveis para o intervalo selecionado.")
