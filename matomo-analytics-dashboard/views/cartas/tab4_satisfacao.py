"""
Aba 4 — Satisfação dos Usuários
KPIs: total de votos, satisfação, insatisfação, neutros.
Gráfico: evolução de satisfação por período.
Gauge: NPS simplificado.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def _classify_vote(v) -> str:
    try:
        v = int(v)
    except Exception:
        return "Neutro"
    if v >= 4:
        return "Satisfeito"
    elif v <= 2:
        return "Insatisfeito"
    return "Neutro"


def render_tab4_satisfacao(df_votes: pd.DataFrame):
    """
    df_votes: resultado de load_service_cards_votes()
    Colunas esperadas: id_voto, idservico, titulo_servico, data_voto,
                       avaliacao_voto_servico
    """
    st.subheader("⭐ Satisfação dos Usuários")

    if df_votes.empty:
        st.info("Nenhum dado de satisfação disponível.")
        return

    df = df_votes.copy()
    df["data_voto"] = pd.to_datetime(df["data_voto"], errors="coerce", utc=True)
    df["Classificacao"] = df["avaliacao_voto_servico"].apply(_classify_vote)

    total_votos = len(df)
    satisfeitos = (df["Classificacao"] == "Satisfeito").sum()
    insatisfeitos = (df["Classificacao"] == "Insatisfeito").sum()
    neutros = (df["Classificacao"] == "Neutro").sum()
    pct_sat = (satisfeitos / total_votos * 100) if total_votos else 0
    pct_insat = (insatisfeitos / total_votos * 100) if total_votos else 0
    nota_media = df["avaliacao_voto_servico"].mean()

    # ------------------------------------------------------------------ #
    # KPIs                                                                 #
    # ------------------------------------------------------------------ #
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("🗳️ Total de Votos", f"{int(total_votos)}")
    c2.metric("😊 Satisfeitos", f"{int(satisfeitos)}", f"{pct_sat:.1f}%")
    c3.metric("😐 Neutros", f"{int(neutros)}")
    c4.metric("😞 Insatisfeitos", f"{int(insatisfeitos)}", f"-{pct_insat:.1f}%", delta_color="inverse")
    c5.metric("⭐ Nota Média", f"{nota_media:.2f}/5" if not pd.isna(nota_media) else "N/A")

    st.markdown("---")
    col_gauge, col_ev = st.columns([1, 2])

    # ------------------------------------------------------------------ #
    # Gauge — NPS simplificado                                            #
    # ------------------------------------------------------------------ #
    with col_gauge:
        st.markdown("#### Índice de Satisfação")
        # Escala: satisfeitos - insatisfeitos (como NPS)
        nps_score = pct_sat - pct_insat
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=pct_sat,
            delta={"reference": 70, "increasing": {"color": "#22C55E"}, "decreasing": {"color": "#EF4444"}},
            title={"text": "% Satisfeitos", "font": {"size": 16}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": "#2563EB"},
                "steps": [
                    {"range": [0, 40], "color": "#FEE2E2"},
                    {"range": [40, 70], "color": "#FEF9C3"},
                    {"range": [70, 100], "color": "#DCFCE7"},
                ],
                "threshold": {
                    "line": {"color": "#1D4ED8", "width": 4},
                    "thickness": 0.75,
                    "value": 70,
                },
            },
            number={"suffix": "%", "font": {"size": 28}},
        ))
        fig_gauge.update_layout(height=300, margin=dict(t=30, b=10, l=30, r=30))
        st.plotly_chart(fig_gauge, use_container_width=True)

        # Distribuição
        dist_df = pd.DataFrame({
            "Classificação": ["Satisfeito", "Neutro", "Insatisfeito"],
            "Votos": [satisfeitos, neutros, insatisfeitos],
        })
        fig_dist = px.bar(
            dist_df,
            x="Classificação",
            y="Votos",
            color="Classificação",
            color_discrete_map={
                "Satisfeito": "#22C55E",
                "Neutro": "#F59E0B",
                "Insatisfeito": "#EF4444",
            },
            text="Votos",
        )
        fig_dist.update_traces(textposition="outside")
        fig_dist.update_layout(
            height=220,
            margin=dict(t=10, b=10, l=10, r=10),
            showlegend=False,
        )
        st.plotly_chart(fig_dist, use_container_width=True)

    # ------------------------------------------------------------------ #
    # Evolução Mensal da Satisfação                                       #
    # ------------------------------------------------------------------ #
    with col_ev:
        st.markdown("#### Evolução da Satisfação por Mês")
        df_ev = df.copy()
        df_ev["Mês"] = df_ev["data_voto"].dt.to_period("M").astype(str)

        df_group = (
            df_ev.groupby(["Mês", "Classificacao"])
            .size()
            .reset_index(name="Votos")
        )

        fig_ev = px.bar(
            df_group,
            x="Mês",
            y="Votos",
            color="Classificacao",
            barmode="stack",
            color_discrete_map={
                "Satisfeito": "#22C55E",
                "Neutro": "#F59E0B",
                "Insatisfeito": "#EF4444",
            },
            labels={"Classificacao": "Classificação"},
        )
        fig_ev.update_layout(
            height=300,
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis_title="",
            yaxis_title="Votos",
            legend_title_text="Classificação",
        )
        st.plotly_chart(fig_ev, use_container_width=True)

        # Evolução da nota média
        st.markdown("#### Nota Média por Mês")
        df_nota = df_ev.groupby("Mês")["avaliacao_voto_servico"].mean().reset_index()
        df_nota.columns = ["Mês", "Nota Média"]

        fig_nota = px.line(
            df_nota,
            x="Mês",
            y="Nota Média",
            markers=True,
            color_discrete_sequence=["#2563EB"],
        )
        fig_nota.update_layout(
            height=220,
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis_title="",
            yaxis=dict(range=[1, 5]),
            yaxis_title="Nota (1–5)",
        )
        # Linha de referência em 4 (satisfatório)
        fig_nota.add_hline(y=4, line_dash="dot", line_color="#22C55E", annotation_text="Meta ≥ 4")
        st.plotly_chart(fig_nota, use_container_width=True)

    # ------------------------------------------------------------------ #
    # Visão por Órgão                                                     #
    # ------------------------------------------------------------------ #
    st.markdown("---")
    st.markdown("#### 🏛️ Satisfação por Órgão")
    
    if "siglaorgao" in df.columns:
        df_orgao = (
            df.groupby("siglaorgao")
            .agg(
                Votos=("id_voto", "count"),
                Nota_Media=("avaliacao_voto_servico", "mean"),
                Satisfeitos=("Classificacao", lambda x: (x == "Satisfeito").sum()),
            )
            .reset_index()
        )
        df_orgao["% Satisfeitos"] = (df_orgao["Satisfeitos"] / df_orgao["Votos"] * 100).round(1)
        df_orgao = df_orgao.sort_values("Nota_Media", ascending=False)

        col_rank, col_table_sat = st.columns([2, 1])

        with col_rank:
            fig_rank = px.bar(
                df_orgao.head(15),
                x="Nota_Media",
                y="siglaorgao",
                orientation="h",
                color="Nota_Media",
                color_continuous_scale="RdYlGn",
                range_color=[1, 5],
                text="Nota_Media",
                labels={"siglaorgao": "Órgão", "Nota_Media": "Nota Média"},
            )
            fig_rank.update_traces(texttemplate='%{text:.2f}', textposition="outside")
            fig_rank.update_layout(
                height=450,
                margin=dict(t=10, b=10, l=10, r=30),
                yaxis=dict(autorange="reversed"),
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig_rank, use_container_width=True)

        with col_table_sat:
            st.dataframe(
                df_orgao[["siglaorgao", "Votos", "Nota_Media", "% Satisfeitos"]]
                .rename(columns={
                    "siglaorgao": "Órgão",
                    "Nota_Media": "Nota Média",
                }),
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.info("Informação de órgão não disponível nos dados de votos.")
