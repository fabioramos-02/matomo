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

    st.markdown("---")
    # Filtro de Órgão a nível da Aba
    if "siglaorgao" in df.columns:
        orgaos_disp = ["Geral (Todos)"] + sorted(df["siglaorgao"].dropna().unique().tolist())
        orgao_sel = st.selectbox("Analisar Aba de Satisfação por Órgão", orgaos_disp)
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

        # Cálculo CSAT oficial (Soma das notas / Máximo possível)
        if "avaliacao_voto_servico" in df.columns and total_votos > 0:
            soma_notas = df["avaliacao_voto_servico"].sum()
            max_possivel = total_votos * 5
            csat_score = (soma_notas / max_possivel) * 100
        else:
            csat_score = 0

        # Storytelling do Índice
        st.markdown("##### 📖 O que significa este índice?")
        if total_votos == 0:
            st.info("Não há avaliações suficientes para calcular o índice neste recorte.")
        elif csat_score >= 80:
            st.success(f"O nível de aprovação é **Excelente (CSAT: {csat_score:.1f}%)**! A grande maioria dos cidadãos utilizou os serviços sem frustrações. O alvo governamental é manter este ponteiro na zona verde (>80%).")
        elif csat_score >= 60:
            st.warning(f"O nível de aprovação está em **Alerta (CSAT: {csat_score:.1f}%)**. Há um volume considerável de usuários insatisfeitos ou neutros. Ajustes na clareza ou na usabilidade podem elevar o serviço de volta à zona de excelência.")
        else:
            st.error(f"O nível de aprovação é **Crítico (CSAT: {csat_score:.1f}%)**. A maioria rejeita a experiência atual, apontando para gargalos graves ou falhas de processo que exigem intervenção imediata para reduzir o desgaste do cidadão.")

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=csat_score,
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
        ))
        fig_gauge.update_layout(height=300, margin=dict(t=30, b=10, l=30, r=30))
        st.plotly_chart(fig_gauge, use_container_width=True)

        with st.expander("Entenda como calculamos a satisfação dos cidadãos usando o CSAT"):
            st.markdown("""
            **O que é o CSAT?**
            O Índice de Satisfação (CSAT) mede a avaliação dos cidadãos em uma escala de 1 a 5 estrelas:
            * ⭐ **1 a 2:** Insatisfeito *(Exige melhorias urgentes)*
            * ⭐⭐⭐ **3:** Neutro *(Experiência mediana)*
            * ⭐⭐⭐⭐⭐ **4 a 5:** Satisfeito *(Atende ou supera as expectativas)*

            **Como chegamos a essa porcentagem?**
            Somamos **todas as estrelas recebidas** e dividimos pela **pontuação máxima possível** (o total de votos multiplicado por 5).

            **Exemplo rápido:**
            Se 100 pessoas avaliassem o serviço, a nota máxima possível seria 500 estrelas. 
            Se a soma real das notas dadas por essas pessoas for 400 estrelas, a conta é simples:
            👉 `(400 / 500) x 100 = 80%`

            Isso significa que o serviço atingiu **80% do seu potencial máximo de excelência**. Quanto maior o número, melhor a experiência entregue ao cidadão!
            """)

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
    
    if "siglaorgao" in df.columns and "avaliacao_voto_servico" in df.columns:
        # 1. Agrupar dados por Órgão e Nota (1 a 5)
        df_stars = (
            df.groupby(["siglaorgao", "avaliacao_voto_servico"])
            .size()
            .reset_index(name="Votos")
        )
        
        # 2. Mapear as notas para Emojis de Estrela
        star_map = {
            5: "⭐⭐⭐⭐⭐ (5)",
            4: "⭐⭐⭐⭐ (4)",
            3: "⭐⭐⭐ (3)",
            2: "⭐⭐ (2)",
            1: "⭐ (1)",
        }
        df_stars["Estrelas"] = df_stars["avaliacao_voto_servico"].map(star_map)
        
        # Ordenar os órgãos pelo total de votos para que as barras fiquem bonitas
        orgao_totals = df.groupby("siglaorgao").size().reset_index(name="TotalVotos")
        orgao_totals = orgao_totals.sort_values("TotalVotos", ascending=True)
        ordem_orgaos = orgao_totals["siglaorgao"].tolist()
        
        # 3. Criar Gráfico de Barras Empilhadas
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
                ]
            },
            color_discrete_map={
                "⭐⭐⭐⭐⭐ (5)": "#22C55E", # Verde Forte
                "⭐⭐⭐⭐ (4)": "#86EFAC", # Verde Claro
                "⭐⭐⭐ (3)": "#FCD34D", # Amarelo (Neutro)
                "⭐⭐ (2)": "#FCA5A5", # Vermelho Claro
                "⭐ (1)": "#EF4444",   # Vermelho Forte
            },
            labels={"siglaorgao": "Órgão", "Votos": "Quantidade de Votos"}
        )
        fig_stars.update_layout(
            height=500,
            margin=dict(t=10, b=10, l=10, r=10),
            legend_title_text="Avaliação",
            yaxis=dict(title="")
        )
        st.plotly_chart(fig_stars, use_container_width=True)

        # 4. Storytelling de Dados Simples e Objetivo
        st.markdown("#### 📖 O que os dados nos dizem?")
        
        df_5 = df_stars[df_stars["avaliacao_voto_servico"] == 5]
        top_5_orgao = df_5.loc[df_5["Votos"].idxmax(), "siglaorgao"] if not df_5.empty else "Nenhum"
        top_5_votos = df_5["Votos"].max() if not df_5.empty else 0
            
        df_1 = df_stars[df_stars["avaliacao_voto_servico"] == 1]
        top_1_orgao = df_1.loc[df_1["Votos"].idxmax(), "siglaorgao"] if not df_1.empty else "Nenhum"
        top_1_votos = df_1["Votos"].max() if not df_1.empty else 0
        
        total_5_estrelas = df_5["Votos"].sum() if not df_5.empty else 0
        total_1_estrela = df_1["Votos"].sum() if not df_1.empty else 0

        st.info(
            f"🎯 **Destaque Positivo:** O órgão **{top_5_orgao}** lidera as avaliações de excelência absoluta, concentrando o maior número de notas máximas ({top_5_votos} votos de 5 estrelas). No panorama geral, temos {total_5_estrelas} votos totais de excelência no estado.\n\n"
            f"🚨 **Ponto de Atenção:** Por outro lado, o órgão **{top_1_orgao}** possui o maior volume de insatisfações críticas ({top_1_votos} votos de 1 estrela de um total de {total_1_estrela} no estado), "
            "o que sugere que os serviços digitais atrelados a este órgão devem ser priorizados para revisões de usabilidade e processos."
        )

    else:
        st.info("Informação de órgão ou avaliação não disponível nos dados.")
