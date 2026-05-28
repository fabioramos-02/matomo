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


_SVG_PATHS = {
    1: "M10 0C8.68678 0 7.38642 0.258658 6.17317 0.761205C4.95991 1.26375 3.85752 2.00035 2.92893 2.92893C1.05357 4.8043 0 7.34784 0 10C0 12.6522 1.05357 15.1957 2.92893 17.0711C3.85752 17.9997 4.95991 18.7362 6.17317 19.2388C7.38642 19.7413 8.68678 20 10 20C12.6522 20 15.1957 18.9464 17.0711 17.0711C18.9464 15.1957 20 12.6522 20 10C20 8.68678 19.7413 7.38642 19.2388 6.17317C18.7362 4.95991 17.9997 3.85752 17.0711 2.92893C16.1425 2.00035 15.0401 1.26375 13.8268 0.761205C12.6136 0.258658 11.3132 0 10 0ZM5 7.5V6L8 7.5C8 8.3 7.3 9 6.5 9C5.7 9 5 8.3 5 7.5ZM12.77 15.23C12.32 14.5 11.25 14 10 14C8.75 14 7.68 14.5 7.23 15.23L5.81 13.81C6.71 12.72 8.25 12 10 12C11.75 12 13.29 12.72 14.19 13.81L12.77 15.23ZM15 7.5C15 8.3 14.3 9 13.5 9C12.7 9 12 7.5L15 6V7.5Z",
    2: "M10 0C8.68678 0 7.38642 0.258658 6.17317 0.761205C4.95991 1.26375 3.85752 2.00035 2.92893 2.92893C1.05357 4.8043 0 7.34784 0 10C0 12.6522 1.05357 15.1957 2.92893 17.0711C3.85752 17.9997 4.95991 18.7362 6.17317 19.2388C7.38642 19.7413 8.68678 20 10 20C12.6522 20 15.1957 18.9464 17.0711 17.0711C18.9464 15.1957 20 12.6522 20 10C20 8.68678 19.7413 7.38642 19.2388 6.17317C18.7362 4.95991 17.9997 3.85752 17.0711 2.92893C16.1425 2.00035 15.0401 1.26375 13.8268 0.761205C12.6136 0.258658 11.3132 0 10 0ZM5 7.5C5 6.7 5.7 6 6.5 6C7.3 6 8 6.7 8 7.5C8 8.3 7.3 9 6.5 9C5.7 9 5 8.3 5 7.5ZM12.77 15.23C12.32 14.5 11.25 14 10 14C8.75 14 7.68 14.5 7.23 15.23L5.81 13.81C6.71 12.72 8.25 12 10 12C11.75 12 13.29 12.72 14.19 13.81L12.77 15.23ZM13.5 9C12.7 9 12 8.3 12 7.5C12 6.7 12.7 6 13.5 6C14.3 6 15 6.7 15 7.5C15 8.3 14.3 9 13.5 9Z",
    3: "M10 0C8.68678 0 7.38642 0.258658 6.17317 0.761205C4.95991 1.26375 3.85752 2.00035 2.92893 2.92893C1.05357 4.8043 0 7.34784 0 10C0 12.6522 1.05357 15.1957 2.92893 17.0711C3.85752 17.9997 4.95991 18.7362 6.17317 19.2388C7.38642 19.7413 8.68678 20 10 20C12.6522 20 15.1957 18.9464 17.0711 17.0711C18.9464 15.1957 20 12.6522 20 10C20 8.68678 19.7413 7.38642 19.2388 6.17317C18.7362 4.95991 17.9997 3.85752 17.0711 2.92893C16.1425 2.00035 15.0401 1.26375 13.8268 0.761205C12.6136 0.258658 11.3132 0 10 0M5 7.5C5 7.10218 5.15804 6.72064 5.43934 6.43934C5.72064 6.15804 6.10218 6 6.5 6C6.89782 6 7.27936 6.15804 7.56066 6.43934C7.84196 6.72064 8 7.10218 8 7.5C8 7.89782 7.84196 8.27936 7.56066 8.56066C7.27936 8.84196 6.89782 9 6.5 9C6.10218 9 5.72064 8.84196 5.43934 8.56066C5.15804 8.27936 5 7.89782 5 7.5ZM14 14H6V12H14V14ZM13.5 9C13.1022 9 12.7206 8.84196 12.4393 8.56066C12.158 8.27936 12 7.89782 12 7.5C12 7.10218 12.158 6.72064 12.4393 6.43934C12.7206 6.15804 13.1022 6 13.5 6C13.8978 6 14.2794 6.15804 14.5607 6.43934C14.842 6.72064 15 7.10218 15 7.5C15 7.89782 14.842 8.27936 14.5607 8.56066C14.2794 8.84196 13.8978 9 13.5 9V9Z",
    4: "M10 0C8.68678 0 7.38642 0.258658 6.17317 0.761205C4.95991 1.26375 3.85752 2.00035 2.92893 2.92893C1.05357 4.8043 0 7.34784 0 10C0 12.6522 1.05357 15.1957 2.92893 17.0711C3.85752 17.9997 4.95991 18.7362 6.17317 19.2388C7.38642 19.7413 8.68678 20 10 20C12.6522 20 15.1957 18.9464 17.0711 17.0711C18.9464 15.1957 20 12.6522 20 10C20 8.68678 19.7413 7.38642 19.2388 6.17317C18.7362 4.95991 17.9997 3.85752 17.0711 2.92893C16.1425 2.00035 15.0401 1.26375 13.8268 0.761205C12.6136 0.258658 11.3132 0 10 0ZM5 7.5C5 6.7 5.7 6 6.5 6C7.3 6 8 6.7 8 7.5C8 8.3 7.3 9 6.5 9C5.7 9 5 8.3 5 7.5ZM10 15.23C8.25 15.23 6.71 14.5 5.81 13.42L7.23 12C7.68 12.72 8.75 13.23 10 13.23C11.25 13.23 12.32 12.72 12.77 12L14.19 13.42C13.29 14.5 11.75 15.23 10 15.23ZM13.5 9C12.7 9 12 8.3 12 7.5C12 6.7 12.7 6 13.5 6C14.3 6 15 6.7 15 7.5C15 8.3 14.3 9 13.5 9Z",
    5: "M10 0C4.47 0 0 4.47 0 10C0 15.53 4.47 20 10 20C12.6522 20 15.1957 18.9464 17.0711 17.0711C18.9464 15.1957 20 12.6522 20 10C20 4.47 15.5 0 10 0ZM6.88 5.82L9 7.94L7.94 9L6.88 7.94L5.82 9L4.76 7.94L6.88 5.82ZM10 15.5C7.67 15.5 5.69 14.04 4.89 12H15.11C14.31 14.04 12.33 15.5 10 15.5ZM14.18 9L13.12 7.94L12.06 9L11 7.94L13.12 5.82L15.24 7.94L14.18 9Z",
}

_RATING_META = [
    (1, "MUITO INSATISFEITO", "#EF4444"),
    (2, "INSATISFEITO",       "#F97316"),
    (3, "REGULAR",            "#F59E0B"),
    (4, "SATISFEITO",         "#4ADE80"),
    (5, "MUITO SATISFEITO",   "#22C55E"),
]


def _render_satisfaction_icons(df: pd.DataFrame, total_votos: int) -> None:
    counts = df["avaliacao_voto_servico"].value_counts()

    items_html = ""
    for nota, label, cor in _RATING_META:
        n = int(counts.get(nota, 0))
        pct = (n / total_votos * 100) if total_votos else 0
        svg_path = _SVG_PATHS[nota]
        items_html += f"""
        <div style="text-align:center; min-width:100px; flex:1;">
          <div style="width:64px; height:64px; border-radius:50%; background:{cor};
                      display:flex; align-items:center; justify-content:center; margin:0 auto;">
            <svg focusable="false" viewBox="0 0 20 20" aria-hidden="true" fill="none"
                 style="width:32px; height:32px;">
              <path d="{svg_path}" fill="white"/>
            </svg>
          </div>
          <p style="font-size:11px; font-weight:700; letter-spacing:.4px;
                    margin:8px 0 2px; color:#374151; line-height:1.3;">{label}</p>
          <p style="font-size:20px; font-weight:800; margin:0; color:#111827;">{n}</p>
          <p style="font-size:13px; color:#6B7280; margin:2px 0 0;">{pct:.1f}%</p>
        </div>"""

    st.markdown(
        f"""
        <div style="display:flex; justify-content:center; align-items:flex-start;
                    gap:12px; flex-wrap:wrap; padding:20px 8px 8px; margin-bottom:4px;">
          {items_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


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

    c1, c2, c3 = st.columns(3)
    c1.metric("🗳️ Total de Votos", f"{int(total_votos)}")
    c2.metric("📊 Indice CSAT", f"{csat_score_global:.1f}%")
    c3.metric("⭐ Nota Media", f"{nota_media:.2f}/5" if not pd.isna(nota_media) else "N/A")

    _render_satisfaction_icons(df, total_votos)

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
                O Customer Satisfaction Score (CSAT) mede a satisfacao dos cidadaos com base em avaliacoes
                de 1 a 5, conforme a metodologia oficial do Portal ms.gov.br:

                * ⭐ **1 — Muito Insatisfeito:** Experiencia muito abaixo das expectativas.
                * ⭐⭐ **2 — Insatisfeito:** Experiencia nao atendeu as expectativas.
                * ⭐⭐⭐ **3 — Regular:** Experiencia adequada, mas nao excepcional.
                * ⭐⭐⭐⭐ **4 — Satisfeito:** Experiencia atendeu as expectativas.
                * ⭐⭐⭐⭐⭐ **5 — Muito Satisfeito:** Experiencia superou as expectativas.

                **Formula:**
                👉 `CSAT = (soma de todas as notas / total de votos × 5) × 100`

                **Exemplo:** 100 avaliacoes com soma de notas igual a 400:
                `(400 / 500) × 100 = 80%`
                """
            )

        _label_map = {1: "Muito Insatisfeito", 2: "Insatisfeito", 3: "Regular", 4: "Satisfeito", 5: "Muito Satisfeito"}
        _color_map_dist = {
            "Muito Insatisfeito": "#EF4444",
            "Insatisfeito": "#F97316",
            "Regular": "#F59E0B",
            "Satisfeito": "#4ADE80",
            "Muito Satisfeito": "#22C55E",
        }
        _label_order = list(_label_map.values())
        counts_dist = df["avaliacao_voto_servico"].value_counts().reindex([1, 2, 3, 4, 5], fill_value=0)
        dist_df = pd.DataFrame({
            "Avaliacao": [_label_map[i] for i in [1, 2, 3, 4, 5]],
            "Votos": counts_dist.values,
        })
        fig_dist = px.bar(
            dist_df,
            x="Avaliacao",
            y="Votos",
            color="Avaliacao",
            color_discrete_map=_color_map_dist,
            category_orders={"Avaliacao": _label_order},
            text="Votos",
        )
        fig_dist.update_traces(textposition="outside")
        fig_dist.update_layout(
            height=260,
            margin=dict(t=10, b=10, l=10, r=10),
            showlegend=False,
            xaxis_title="",
        )
        st.plotly_chart(fig_dist, use_container_width=True)

    with col_ev:
        st.markdown("#### Evolucao da Satisfacao por Mes")
        _ev_label_map = {1: "Muito Insatisfeito", 2: "Insatisfeito", 3: "Regular", 4: "Satisfeito", 5: "Muito Satisfeito"}
        _ev_color_map = {
            "Muito Insatisfeito": "#EF4444",
            "Insatisfeito": "#F97316",
            "Regular": "#F59E0B",
            "Satisfeito": "#4ADE80",
            "Muito Satisfeito": "#22C55E",
        }
        df_ev = df.copy()
        df_ev["Mes"] = df_ev["data_voto"].dt.to_period("M").astype(str)
        df_ev["Avaliacao"] = df_ev["avaliacao_voto_servico"].map(_ev_label_map)

        df_group = df_ev.groupby(["Mes", "Avaliacao"]).size().reset_index(name="Votos")

        fig_ev = px.bar(
            df_group,
            x="Mes",
            y="Votos",
            color="Avaliacao",
            barmode="stack",
            color_discrete_map=_ev_color_map,
            category_orders={"Avaliacao": list(_ev_label_map.values())},
            labels={"Avaliacao": "Avaliacao"},
        )
        fig_ev.update_layout(
            height=300,
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis_title="",
            yaxis_title="Votos",
            legend_title_text="Avaliacao",
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
