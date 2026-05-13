"""
Aba 1 — Visão Geral das Cartas de Serviço
KPIs: Total, Ativos, Inativos, Digitais, Presenciais, Híbridos, % Digital
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def render_tab1_visao_geral(df: pd.DataFrame):
    """
    df: resultado de load_service_cards_inventory()
    Colunas esperadas: idservico, servico_ativo, digital, online, agendavel,
                       acesso_externo, data_criacao_servico, siglaorgao
    """
    st.subheader("📋 Visão Geral do Inventário de Serviços")

    if df.empty:
        st.info("Nenhum dado de inventário disponível.")
        return

    # ------------------------------------------------------------------ #
    # Normalização de tipos                                                #
    # ------------------------------------------------------------------ #
    for col in ["servico_ativo", "digital", "online", "agendavel", "acesso_externo"]:
        if col in df.columns:
            df[col] = df[col].astype(bool)

    total = len(df)
    ativos = df["servico_ativo"].sum()
    inativos = total - ativos
    df_ativos = df[df["servico_ativo"]]

    digitais = df_ativos[df_ativos["digital"] | df_ativos["online"]].shape[0]
    presenciais = df_ativos[~df_ativos["digital"] & ~df_ativos["online"]].shape[0]
    hibridos = df_ativos[
        (df_ativos["digital"] | df_ativos["online"]) &
        (df_ativos["agendavel"] | df_ativos["acesso_externo"])
    ].shape[0]
    pct_digital = (digitais / ativos * 100) if ativos > 0 else 0

    # ------------------------------------------------------------------ #
    # KPIs                                                                 #
    # ------------------------------------------------------------------ #
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    col1.metric("📦 Total", f"{int(total)}")
    col2.metric("✅ Ativos", f"{int(ativos)}")
    col3.metric("❌ Inativos", f"{int(inativos)}")
    col4.metric("💻 Digitais", f"{int(digitais)}")
    col5.metric("🏢 Presenciais", f"{int(presenciais)}")
    col6.metric("🔀 Híbridos", f"{int(hibridos)}")
    col7.metric("📊 % Digital", f"{pct_digital:.1f}%")

    st.markdown("---")

    col_left, col_right = st.columns(2)

    # ------------------------------------------------------------------ #
    # Gráfico de Pizza: Distribuição por Canal                            #
    # ------------------------------------------------------------------ #
    with col_left:
        st.markdown("#### Distribuição por Canal (serviços ativos)")
        apenas_presencial = presenciais - hibridos
        apenas_presencial = max(0, apenas_presencial)
        apenas_digital = digitais - hibridos
        apenas_digital = max(0, apenas_digital)

        canal_df = pd.DataFrame({
            "Canal": ["Apenas Digital", "Apenas Presencial", "Híbrido"],
            "Quantidade": [apenas_digital, apenas_presencial, hibridos],
        })
        canal_df = canal_df[canal_df["Quantidade"] > 0]

        fig_pizza = px.pie(
            canal_df,
            names="Canal",
            values="Quantidade",
            color_discrete_sequence=["#2563EB", "#64748B", "#F59E0B"],
            hole=0.4,
        )
        fig_pizza.update_traces(textposition="outside", textinfo="percent+label")
        fig_pizza.update_layout(
            showlegend=True,
            height=340,
            margin=dict(t=20, b=20, l=10, r=10),
        )
        st.plotly_chart(fig_pizza, use_container_width=True)

    # ------------------------------------------------------------------ #
    # Gráfico de Barras: Criação de Serviços por Ano                      #
    # ------------------------------------------------------------------ #
    with col_right:
        st.markdown("#### Novos Serviços por Ano")
        if "data_criacao_servico" in df.columns:
            df_temp = df.copy()
            df_temp["data_criacao_servico"] = pd.to_datetime(df_temp["data_criacao_servico"], errors="coerce", utc=True)
            df_temp["Ano"] = df_temp["data_criacao_servico"].dt.year.dropna().astype(int)
            df_ano = df_temp.groupby("Ano").size().reset_index(name="Serviços")
            df_ano = df_ano[df_ano["Ano"] > 2010]

            fig_bar = px.bar(
                df_ano,
                x="Ano",
                y="Serviços",
                color_discrete_sequence=["#2563EB"],
                text="Serviços",
            )
            fig_bar.update_traces(textposition="outside")
            fig_bar.update_layout(
                height=340,
                margin=dict(t=20, b=20, l=10, r=10),
                xaxis_title="",
                yaxis_title="Serviços criados",
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Coluna data_criacao_servico não disponível.")

    # ------------------------------------------------------------------ #
    # Tabela: Distribuição por Órgão                                      #
    # ------------------------------------------------------------------ #
    st.markdown("---")
    st.markdown("#### Distribuição por Órgão")
    if "siglaorgao" in df.columns and "nome_orgao" in df.columns:
        df_orgao = (
            df.groupby(["siglaorgao", "nome_orgao"])
            .agg(
                Total=("idservico", "count"),
                Ativos=("servico_ativo", "sum"),
            )
            .reset_index()
        )
        df_orgao["Inativos"] = df_orgao["Total"] - df_orgao["Ativos"]
        df_orgao["% do Total de ativos"] = (df_orgao["Ativos"] / ativos * 100).round(1).astype(str) + "%"
        df_orgao = df_orgao.sort_values("Total", ascending=False).rename(
            columns={"siglaorgao": "Sigla", "nome_orgao": "Órgão"}
        )
        st.dataframe(df_orgao[["Sigla", "Órgão", "Total", "Ativos", "Inativos", "% do Total de ativos"]],
                     use_container_width=True, hide_index=True)
