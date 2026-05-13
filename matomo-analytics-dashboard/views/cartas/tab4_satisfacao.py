"""
Aba 4 - Satisfacao dos Usuarios
KPIs: total de votos, satisfacao, insatisfacao, neutros.
Grafico: evolucao de satisfacao por periodo.
Gauge: NPS simplificado.
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def _classify_vote(v) -> str:
    try:
        v = int(v)
    except Exception:
        return "Neutro"
    if v >= 4:
        return "Satisfeito"
    if v <= 2:
        return "Insatisfeito"
    return "Neutro"


def render_tab4_satisfacao(df_votes: pd.DataFrame):
    """
    df_votes: resultado de load_service_cards_votes()
    Colunas esperadas: id_voto, idservico, titulo_servico, data_voto,
                       avaliacao_voto_servico
    """
    st.subheader("⭐ Satisfacao dos Usuarios")

    if df_votes.empty:
        st.info("Nenhum dado de satisfacao disponivel.")
        return

    df = df_votes.copy()
    df["data_voto"] = pd.to_datetime(df["data_voto"], errors="coerce", utc=True)
    df["Classificacao"] = df["avaliacao_voto_servico"].apply(_classify_vote)

    st.markdown("---")
    if "siglaorgao" in df.columns:
        orgaos_disp = ["Geral (Todos)"] + sorted(df["siglaorgao"].dropna().unique().tolist())
        orgao_sel = st.selectbox("Analisar Aba de Satisfacao por Orgao", orgaos_disp)
        if orgao_sel != "Geral (Todos)":
            df = df[df["siglaorgao"] == orgao_sel]

    if df.empty:
        st.warning("Nenhum dado encontrado para o filtro selecionado.")
        return

    total_votos = len(df)
    satisfeitos = (df["Classificacao"] == "Satisfeito").sum()
    insatisfeitos = (df["Classificacao"] == "Insatisfeito").sum()
    neutros = (df["Classificacao"] == "Neutro").sum()
    pct_sat = (satisfeitos / total_votos * 100) if total_votos else 0
    pct_insat = (insatisfeitos / total_votos * 100) if total_votos else 0
    nota_media = df["avaliacao_voto_servico"].mean()

    soma_notas_global = df["avaliacao_voto_servico"].sum()
    max_possivel_global = total_votos * 5
    csat_score_global = (soma_notas_global / max_possivel_global) * 100 if max_possivel_global > 0 else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("🗳️ Total de Votos", f"{int(total_votos)}")
    c2.metric("📊 Indice CSAT", f"{csat_score_global:.1f}%")
    c3.metric("😊 Satisfeitos", f"{int(satisfeitos)}", f"{pct_sat:.1f}%")
    c4.metric("😐 Neutros", f"{int(neutros)}")
    c5.metric("😞 Insatisfeitos", f"{int(insatisfeitos)}", f"-{pct_insat:.1f}%", delta_color="inverse")
    c6.metric("⭐ Nota Media", f"{nota_media:.2f}/5" if not pd.isna(nota_media) else "N/A")

    st.markdown("---")
    col_gauge, col_ev = st.columns([1, 2])

    with col_gauge:
        st.markdown("#### Indice de Satisfacao (CSAT)")
        st.markdown("##### 📖 O que significa este indice?")

        if total_votos == 0:
            st.info("Nao ha avaliacoes suficientes para calcular o indice neste recorte.")
        elif csat_score_global >= 80:
            st.success(
                f"O nivel de aprovacao e **Excelente ({csat_score_global:.1f}%)**. "
                "A grande maioria dos cidadaos utilizou os servicos sem frustracoes."
            )
        elif csat_score_global >= 60:
            st.warning(
                f"O nivel de aprovacao esta em **Alerta ({csat_score_global:.1f}%)**. "
                "Ha um volume relevante de usuarios insatisfeitos ou neutros."
            )
        else:
            st.error(
                f"O nivel de aprovacao e **Critico ({csat_score_global:.1f}%)**. "
                "A experiencia atual exige intervencao imediata para reduzir desgaste do cidadao."
            )

        fig_gauge = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=csat_score_global,
                delta={"reference": 80, "increasing": {"color": "#22C55E"}, "decreasing": {"color": "#EF4444"}},
                title={"text": "CSAT (%)", "font": {"size": 16}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1},
                    "bar": {"color": "#2563EB"},
                    "steps": [
                        {"range": [0, 60], "color": "#FEE2E2"},
                        {"range": [60, 80], "color": "#FEF9C3"},
                        {"range": [80, 100], "color": "#DCFCE7"},
                    ],
                    "threshold": {
                        "line": {"color": "#1D4ED8", "width": 4},
                        "thickness": 0.75,
                        "value": 80,
                    },
                },
                number={"suffix": "%", "font": {"size": 28}},
            )
        )
        fig_gauge.update_layout(height=300, margin=dict(t=30, b=10, l=30, r=30))
        st.plotly_chart(fig_gauge, use_container_width=True)

        with st.expander("Entenda como calculamos a satisfacao dos cidadaos usando o CSAT"):
            st.markdown(
                """
                **O que e o CSAT?**
                O Indice de Satisfacao (CSAT) mede a avaliacao dos cidadaos em uma escala de 1 a 5 estrelas:
                * ⭐ **1 a 2:** Insatisfeito *(Exige melhorias urgentes)*
                * ⭐⭐⭐ **3:** Neutro *(Experiencia mediana)*
                * ⭐⭐⭐⭐ e ⭐⭐⭐⭐⭐ **4 a 5:** Satisfeito *(Atende ou supera as expectativas)*

                **Como chegamos a essa porcentagem?**
                Somamos **todas as estrelas recebidas** e dividimos pela **pontuacao maxima possivel**
                (o total de votos multiplicado por 5).

                **Exemplo rapido:**
                Se 100 pessoas avaliassem o servico, a nota maxima possivel seria 500 estrelas.
                Se a soma real das notas dadas por essas pessoas for 400 estrelas, a conta e:
                👉 `(400 / 500) x 100 = 80%`
                """
            )

        dist_df = pd.DataFrame(
            {
                "Classificacao": ["Satisfeito", "Neutro", "Insatisfeito"],
                "Votos": [satisfeitos, neutros, insatisfeitos],
            }
        )
        fig_dist = px.bar(
            dist_df,
            x="Classificacao",
            y="Votos",
            color="Classificacao",
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

    with col_ev:
        st.markdown("#### Evolucao da Satisfacao por Mes")
        df_ev = df.copy()
        df_ev["Mes"] = df_ev["data_voto"].dt.to_period("M").astype(str)

        df_group = df_ev.groupby(["Mes", "Classificacao"]).size().reset_index(name="Votos")

        fig_ev = px.bar(
            df_group,
            x="Mes",
            y="Votos",
            color="Classificacao",
            barmode="stack",
            color_discrete_map={
                "Satisfeito": "#22C55E",
                "Neutro": "#F59E0B",
                "Insatisfeito": "#EF4444",
            },
            labels={"Classificacao": "Classificacao"},
        )
        fig_ev.update_layout(
            height=300,
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis_title="",
            yaxis_title="Votos",
            legend_title_text="Classificacao",
        )
        st.plotly_chart(fig_ev, use_container_width=True)

        st.markdown("#### Nota Media por Mes")
        df_nota = df_ev.groupby("Mes")["avaliacao_voto_servico"].mean().reset_index()
        df_nota.columns = ["Mes", "Nota Media"]

        fig_nota = px.line(
            df_nota,
            x="Mes",
            y="Nota Media",
            markers=True,
            color_discrete_sequence=["#2563EB"],
        )
        fig_nota.update_layout(
            height=220,
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis_title="",
            yaxis=dict(range=[1, 5]),
            yaxis_title="Nota (1-5)",
        )
        fig_nota.add_hline(y=4, line_dash="dot", line_color="#22C55E", annotation_text="Meta >= 4")
        st.plotly_chart(fig_nota, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 🏛️ Satisfacao por Orgao")

    if "siglaorgao" in df.columns and "avaliacao_voto_servico" in df.columns:
        df_kpi = (
            df.groupby("siglaorgao")
            .agg(
                total=("Classificacao", "count"),
                satisfeitos=("Classificacao", lambda x: (x == "Satisfeito").sum()),
                insatisfeitos=("Classificacao", lambda x: (x == "Insatisfeito").sum()),
            )
            .reset_index()
        )

        if df_kpi.empty:
            st.info("Nao ha dados suficientes para montar o ranking por orgao.")
            return

        df_kpi["taxa_sat"] = df_kpi["satisfeitos"] / df_kpi["total"]
        df_kpi["taxa_insat"] = df_kpi["insatisfeitos"] / df_kpi["total"]

        df_stars = (
            df.groupby(["siglaorgao", "avaliacao_voto_servico"])
            .size()
            .reset_index(name="Votos")
        )

        star_map = {
            5: "⭐⭐⭐⭐⭐ (5)",
            4: "⭐⭐⭐⭐ (4)",
            3: "⭐⭐⭐ (3)",
            2: "⭐⭐ (2)",
            1: "⭐ (1)",
        }
        df_stars["Estrelas"] = df_stars["avaliacao_voto_servico"].map(star_map)
        df_stars = df_stars[df_stars["Estrelas"].notna()]

        if df_stars.empty:
            st.info("Nao ha distribuicao de estrelas suficiente para montar o grafico por orgao.")
            return

        df_stars = df_stars.merge(
            df_kpi[["siglaorgao", "total", "taxa_sat", "taxa_insat"]],
            on="siglaorgao",
            how="left",
        )

        ordem_orgaos = (
            df_kpi.sort_values(
                ["taxa_insat", "insatisfeitos", "total"],
                ascending=[True, True, True],
            )["siglaorgao"].tolist()
        )

        dynamic_height = max(400, len(ordem_orgaos) * 45)

        fig_stars = px.bar(
            df_stars,
            x="Votos",
            y="siglaorgao",
            color="Estrelas",
            orientation="h",
            barmode="stack",
            category_orders={
                "siglaorgao": ordem_orgaos,
                "Estrelas": [
                    "⭐⭐⭐⭐⭐ (5)",
                    "⭐⭐⭐⭐ (4)",
                    "⭐⭐⭐ (3)",
                    "⭐⭐ (2)",
                    "⭐ (1)",
                ],
            },
            color_discrete_map={
                "⭐⭐⭐⭐⭐ (5)": "#22C55E",
                "⭐⭐⭐⭐ (4)": "#86EFAC",
                "⭐⭐⭐ (3)": "#FCD34D",
                "⭐⭐ (2)": "#FCA5A5",
                "⭐ (1)": "#EF4444",
            },
            labels={"siglaorgao": "Orgao", "Votos": "Quantidade de Votos"},
            hover_data={
                "total": True,
                "taxa_sat": ":.1%",
                "taxa_insat": ":.1%",
            },
            template="plotly_white",
        )
        fig_stars.update_layout(
            height=dynamic_height,
            margin=dict(t=10, b=10, l=10, r=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            bargap=0.3,
            yaxis=dict(title="", autorange="reversed"),
        )

        with st.container(height=550):
            st.plotly_chart(fig_stars, use_container_width=True)

        st.caption(
            "Ranking ordenado pela taxa de insatisfacao. Os orgaos no topo concentram a maior prioridade de intervencao."
        )

        st.markdown("#### 📖 Leitura Estrategica")

        top_insat = df_kpi.sort_values(
            ["taxa_insat", "insatisfeitos", "total"],
            ascending=[False, False, False],
        ).iloc[0]
        top_sat = df_kpi.sort_values(
            ["taxa_sat", "satisfeitos", "total"],
            ascending=[False, False, False],
        ).iloc[0]

        st.warning(
            f"🚨 **Prioridade de intervencao:** O orgao **{top_insat['siglaorgao']}** apresenta a maior taxa proporcional "
            f"de insatisfacao ({top_insat['taxa_insat'] * 100:.1f}%, ou {int(top_insat['insatisfeitos'])} de "
            f"{int(top_insat['total'])} votos), indicando gargalos criticos na experiencia do cidadao."
        )
        st.success(
            f"🏆 **Referencia positiva:** O orgao **{top_sat['siglaorgao']}** apresenta a maior taxa de satisfacao "
            f"({top_sat['taxa_sat'] * 100:.1f}%, ou {int(top_sat['satisfeitos'])} de {int(top_sat['total'])} votos) "
            "e pode servir como benchmark de boas praticas."
        )
    else:
        st.info("Informacao de orgao ou avaliacao nao disponivel nos dados.")
