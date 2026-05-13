"""
Aba 2 — Análise por Órgão
Ranking de órgãos, serviços por tipo, % do total, maturidade digital.
"""
import streamlit as st
import pandas as pd
import plotly.express as px


def render_tab2_por_orgao(df: pd.DataFrame):
    """
    df: resultado de load_service_cards_inventory()
    """
    st.subheader("🏛️ Análise por Órgão")

    if df.empty:
        st.info("Nenhum dado disponível.")
        return

    for col in ["servico_ativo", "digital", "online", "agendavel"]:
        if col in df.columns:
            df[col] = df[col].astype(bool)

    # Filtra apenas ativos
    df = df[df["servico_ativo"]].copy()

    # ------------------------------------------------------------------ #
    # Filtro de Órgão                                                      #
    # ------------------------------------------------------------------ #
    orgaos = ["Todos"] + sorted(df["siglaorgao"].dropna().unique().tolist())
    selected = st.selectbox("Filtrar por Órgão", orgaos, key="cartas_orgao_filter")

    df_filter = df if selected == "Todos" else df[df["siglaorgao"] == selected]

    # ------------------------------------------------------------------ #
    # Métricas rápidas do filtro                                          #
    # ------------------------------------------------------------------ #
    total_filter = len(df_filter)
    ativos_filter = df_filter["servico_ativo"].sum()
    digitais_filter = df_filter[df_filter["digital"] | df_filter["online"]].shape[0]
    pct_d = (digitais_filter / total_filter * 100) if total_filter > 0 else 0
    pct_p = (100 - pct_d) if total_filter > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Serviços Ativos", f"{int(total_filter)}")
    c2.metric("Digitais / Online", f"{int(digitais_filter)}")
    c3.metric("% Digital", f"{pct_d:.1f}%")
    c4.metric("% Presencial", f"{pct_p:.1f}%")

    st.markdown("---")

    # ------------------------------------------------------------------ #
    # Ranking geral de órgãos (só mostra quando "Todos" está selecionado) #
    # ------------------------------------------------------------------ #
    if selected == "Todos":
        st.markdown("#### Ranking de Órgãos por Quantidade de Serviços")

        df_rank = (
            df.groupby(["siglaorgao", "nome_orgao"])
            .agg(
                Total=("idservico", "count"),
                Ativos=("servico_ativo", "sum"),
                Digitais=("digital", "sum"),
            )
            .reset_index()
            .sort_values("Total", ascending=False)
        )
        df_rank["% Total"] = (df_rank["Total"] / len(df) * 100).round(1)
        df_rank["% Digital"] = (df_rank["Digitais"] / df_rank["Total"].replace(0, 1) * 100).round(1)
        df_rank["% Presencial"] = (100 - df_rank["% Digital"]).round(1)

        col_bar, col_table = st.columns([3, 2])

        with col_bar:
            df_top10 = df_rank.head(10).copy()
            # Inverte para o Plotly h-bar mostrar o 1º no topo
            df_top10 = df_top10.sort_values("Total", ascending=True)

            fig = px.bar(
                df_top10,
                x="Total",
                y="siglaorgao",
                orientation="h",
                color="% Digital",
                color_continuous_scale="Blues",
                text="Total",
                labels={"siglaorgao": "Órgão", "Total": "Qtd Serviços", "% Digital": "% Digital"},
                template="plotly_white"
            )
            
            fig.update_traces(
                textposition="inside",
                marker_line_width=0,
                marker_line_color='white'
            )
            
            fig.update_layout(
                height=500, # Aumentado para dar "volume" às barras
                margin=dict(t=30, b=30, l=10, r=20),
                coloraxis_colorbar=dict(
                    title="% Digital",
                    thickness=15,
                    len=0.8,
                    yanchor="middle",
                    y=0.5
                ),
                bargap=0.3,
                yaxis=dict(
                    title="",
                    tickfont=dict(size=12, color="#4B5563"),
                    autorange="reversed"
                ),
                xaxis=dict(
                    title="Volume Total de Serviços (Ativos)",
                    gridcolor="#F3F4F6"
                ),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Exibindo os 10 órgãos com maior portfólio de serviços.")

        with col_table:
            st.dataframe(
                df_rank[["siglaorgao", "nome_orgao", "Ativos", "Digitais", "% Presencial", "% Digital"]]
                .rename(columns={"siglaorgao": "Sigla", "nome_orgao": "Órgão"}),
                use_container_width=True,
                hide_index=True,
            )

    # ------------------------------------------------------------------ #
    # Detalhamento do órgão selecionado                                   #
    # ------------------------------------------------------------------ #
    else:
        nome_orgao = df_filter["nome_orgao"].iloc[0] if "nome_orgao" in df_filter.columns else selected
        st.markdown(f"#### Serviços do órgão: **{nome_orgao}**")

        canal_labels = []
        for _, row in df_filter.iterrows():
            is_digital = row.get("digital", False) or row.get("online", False)
            if is_digital and row.get("agendavel", False):
                canal_labels.append("Híbrido")
            elif is_digital:
                canal_labels.append("Digital")
            else:
                canal_labels.append("Presencial")

        df_filter = df_filter.copy()
        df_filter["Canal"] = canal_labels
        
        # Garante que as colunas de slug existem para evitar KeyError
        if "slug_categoria" in df_filter.columns and "slug_servico" in df_filter.columns:
            df_filter["Link"] = (
                "https://www.ms.gov.br/" + 
                df_filter["slug_categoria"].fillna("servicos") + "/" + 
                df_filter["slug_servico"]
            )
        else:
            df_filter["Link"] = ""

        col_pie, col_list = st.columns([1, 2])

        with col_pie:
            canal_count = df_filter["Canal"].value_counts().reset_index()
            canal_count.columns = ["Canal", "Qtd"]
            fig_pie = px.pie(
                canal_count,
                names="Canal",
                values="Qtd",
                color_discrete_sequence=["#2563EB", "#64748B", "#F59E0B"],
                hole=0.4,
            )
            fig_pie.update_layout(height=280, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_list:
            cols_show = [c for c in ["titulo_servico", "Link", "Canal", "custo", "tempo", "tipo_tempo"]
                         if c in df_filter.columns]
            st.dataframe(
                df_filter[cols_show].rename(
                    columns={
                        "titulo_servico": "Serviço",
                        "Link": "Acessar Serviço",
                        "custo": "Custo",
                        "tempo": "Prazo",
                        "tipo_tempo": "Unidade",
                    }
                ),
                column_config={
                    "Acessar Serviço": st.column_config.LinkColumn(
                        "Acessar Serviço",
                        help="Clique para abrir a carta de serviço oficial",
                        validate=r"^https://",
                        display_text="🔗 Abrir Serviço"
                    )
                },
                use_container_width=True,
                hide_index=True,
            )
