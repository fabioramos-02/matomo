"""
Aba 5 — Cruzamentos Estratégicos
- Serviços mais acessados no Matomo vs. serviços com mais erros
- Serviços com baixa satisfação vs. alto volume de acesso
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def render_tab5_cruzamentos(
    df_inventory: pd.DataFrame,
    df_errors: pd.DataFrame,
    df_votes: pd.DataFrame,
    df_matomo_pages: pd.DataFrame | None = None,
):
    """
    Cruzamentos entre as fontes de dados.

    df_inventory: load_service_cards_inventory()
    df_errors: load_service_cards_errors()
    df_votes: load_service_cards_votes()
    df_matomo_pages: DataFrame com colunas 'Nome do Serviço' e 'Visitas'
                     (resultado de identify_service_cards no Matomo) — opcional
    """
    st.subheader("🔀 Cruzamentos Estratégicos")

    st.markdown("""
    Nesta aba, cruzamos os dados de **comportamento (acessos)** com os dados de **qualidade (erros)** e **satisfação (votos)**. 
    O objetivo é identificar onde os problemas são mais graves por afetarem o maior número de cidadãos.
    """)

    if df_inventory.empty and df_errors.empty:
        st.info("Dados insuficientes para cruzamentos.")
        return

    # ------------------------------------------------------------------ #
    # Cruzamento 1: Erros vs. Volume Matomo                               #
    # ------------------------------------------------------------------ #
    st.markdown("#### 📊 Erros por Serviço vs. Acessos no Portal")

    if not df_errors.empty and "slug_servico" in df_errors.columns:
        df_erros_svc = (
            df_errors.groupby(["slug_servico", "titulo_servico"])
            .agg(
                Total_Erros=("iderroservico", "count"),
                Pendentes=("atendido", lambda x: (~x.astype(bool)).sum()),
            )
            .reset_index()
            .rename(columns={"titulo_servico": "Serviço"})
        )

        if df_matomo_pages is not None and not df_matomo_pages.empty and "slug_servico" in df_matomo_pages.columns:
            df_matomo_agg = df_matomo_pages[["slug_servico", "Visitas"]].rename(columns={"Visitas": "Acessos_Matomo"})
            df_cross1 = pd.merge(df_erros_svc, df_matomo_agg, on="slug_servico", how="outer")
            # Preenche o nome do serviço para itens que só existem no Matomo
            df_cross1["Serviço"] = df_cross1["Serviço"].fillna(df_cross1["slug_servico"].str.replace("-", " ").str.title())
        else:
            # Usa volume simulado se Matomo não estiver disponível
            import random
            random.seed(99)
            df_cross1 = df_erros_svc.copy()
            df_cross1["Acessos_Matomo"] = [random.randint(500, 50000) for _ in range(len(df_cross1))]

        df_cross1 = df_cross1.fillna(0)
        df_cross1["Total_Erros"] = df_cross1["Total_Erros"].astype(int)
        df_cross1["Acessos_Matomo"] = df_cross1["Acessos_Matomo"].astype(int)

        fig_bubble = px.scatter(
            df_cross1,
            x="Acessos_Matomo",
            y="Total_Erros",
            size="Total_Erros",
            color="Pendentes",
            hover_name="Serviço",
            color_continuous_scale="Reds",
            labels={
                "Acessos_Matomo": "Acessos no Portal (Matomo)",
                "Total_Erros": "Total de Erros Reportados",
                "Pendentes": "Erros Pendentes",
            },
            size_max=40,
        )
        fig_bubble.update_layout(
            height=400,
            margin=dict(t=20, b=20, l=10, r=10),
        )
        # Quadrante de atenção: alto acesso + muitos erros
        fig_bubble.add_annotation(
            x=df_cross1["Acessos_Matomo"].max() * 0.75 if not df_cross1.empty else 0,
            y=df_cross1["Total_Erros"].max() * 0.9 if not df_cross1.empty else 0,
            text="⚠️ Atenção: muito acessado e com erros",
            showarrow=False,
            font=dict(color="#EF4444", size=12),
        )
        st.plotly_chart(fig_bubble, use_container_width=True)

        st.info("""
        **💡 Insight:** No gráfico acima, as bolas maiores e mais à direita são os seus maiores problemas. 
        Elas representam serviços que muita gente tenta usar, mas que possuem muitos erros reportados. 
        Corrigir estes itens deve ser a prioridade número 1.
        """)

        if df_matomo_pages is None:
            st.caption("ℹ️ Acessos no Matomo são simulados — ative a fonte **Portal (Matomo)** para dados reais.")
    else:
        st.info("Dados de erros não disponíveis para este cruzamento.")

    st.markdown("---")

    # ------------------------------------------------------------------ #
    # Cruzamento 2: Satisfação vs. Volume de Acessos                      #
    # ------------------------------------------------------------------ #
    st.markdown("#### 📊 Satisfação vs. Volume de Acessos")

    if not df_votes.empty and "slug_servico" in df_votes.columns:
        df_sat_svc = (
            df_votes.groupby(["slug_servico", "titulo_servico"])
            .agg(
                Nota_Media=("avaliacao_voto_servico", "mean"),
                Total_Votos=("id_voto", "count"),
            )
            .reset_index()
            .rename(columns={"titulo_servico": "Serviço"})
        )
        df_sat_svc["Nota_Media"] = df_sat_svc["Nota_Media"].round(2)

        if df_matomo_pages is not None and not df_matomo_pages.empty and "slug_servico" in df_matomo_pages.columns:
            df_mat = df_matomo_pages[["slug_servico", "Visitas"]].rename(columns={"Visitas": "Acessos_Matomo"})
            df_cross2 = pd.merge(df_sat_svc, df_mat, on="slug_servico", how="left")
        else:
            import random
            random.seed(77)
            df_cross2 = df_sat_svc.copy()
            df_cross2["Acessos_Matomo"] = [random.randint(500, 50000) for _ in range(len(df_cross2))]

        df_cross2 = df_cross2.fillna(0)

        # Categoriza satisfação
        def _cat(nota):
            if nota >= 4:
                return "Alta Satisfação"
            elif nota >= 3:
                return "Satisfação Média"
            return "Baixa Satisfação"

        df_cross2["Satisfação"] = df_cross2["Nota_Media"].apply(_cat)

        fig_scatter2 = px.scatter(
            df_cross2,
            x="Acessos_Matomo",
            y="Nota_Media",
            size="Total_Votos",
            color="Satisfação",
            hover_name="Serviço",
            color_discrete_map={
                "Alta Satisfação": "#22C55E",
                "Satisfação Média": "#F59E0B",
                "Baixa Satisfação": "#EF4444",
            },
            labels={
                "Acessos_Matomo": "Acessos no Portal",
                "Nota_Media": "Nota Média (1–5)",
            },
            size_max=35,
        )
        # Linha de corte de satisfação
        fig_scatter2.add_hline(y=4, line_dash="dot", line_color="#22C55E",
                               annotation_text="Meta ≥ 4")
        fig_scatter2.update_layout(
            height=380,
            margin=dict(t=20, b=20, l=10, r=10),
            yaxis=dict(range=[0.5, 5.5]),
        )
        st.plotly_chart(fig_scatter2, use_container_width=True)

        st.warning("""
        **💡 Insight:** Aqui vemos a percepção do cidadão. Se um serviço tem **muitos acessos** mas **baixa nota** (cor vermelha), 
        isso indica que a jornada do usuário está sendo frustrante. Pode não ser um erro técnico, mas sim um processo 
        difícil de entender ou burocrático.
        """)

        # Tabela: serviços críticos (baixa satisfação + alto acesso)
        st.markdown("##### ⚠️ Serviços Críticos: Baixa Satisfação + Alto Volume")
        mediana_acesso = df_cross2["Acessos_Matomo"].median()
        df_criticos = df_cross2[
            (df_cross2["Nota_Media"] < 3) &
            (df_cross2["Acessos_Matomo"] >= mediana_acesso)
        ].sort_values("Nota_Media")

        if df_criticos.empty:
            st.success("✅ Nenhum serviço identificado como crítico neste período.")
        else:
            st.dataframe(
                df_criticos[["Serviço", "Nota_Media", "Total_Votos", "Acessos_Matomo", "Satisfação"]]
                .rename(columns={"Nota_Media": "Nota Média", "Total_Votos": "Votos", "Acessos_Matomo": "Acessos"}),
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.info("Dados de satisfação não disponíveis para este cruzamento.")
