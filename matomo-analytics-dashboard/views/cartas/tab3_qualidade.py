"""
Aba 3 — Qualidade das Cartas (Erros)
KPIs: total, atendidos, corrigidos, pendentes.
Gráficos: erros por órgão, evolução temporal, tabela operacional.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import timedelta


def render_tab3_qualidade(df_errors: pd.DataFrame):
    """
    df_errors: resultado de load_service_cards_errors()
    Colunas esperadas: iderroservico, idservico, titulo_servico, siglaorgao,
                       nome_orgao, conteudo, atendido, corrigido_erro,
                       reportado_erro, resolucao_erro,
                       data_criacao_erro, data_atualizacao_erro
    """
    st.subheader("🐛 Qualidade das Cartas — Erros Reportados")

    if df_errors.empty:
        st.info("Nenhum erro reportado encontrado.")
        return

    for col in ["atendido", "corrigido_erro"]:
        if col in df_errors.columns:
            df_errors[col] = df_errors[col].astype(bool)

    for col in ["data_criacao_erro", "data_atualizacao_erro"]:
        if col in df_errors.columns:
            df_errors[col] = pd.to_datetime(df_errors[col], errors="coerce")

    total_erros = len(df_errors)
    atendidos = int(df_errors["atendido"].sum()) if "atendido" in df_errors.columns else 0
    corrigidos = int(df_errors["corrigido_erro"].sum()) if "corrigido_erro" in df_errors.columns else 0
    pendentes = total_erros - atendidos

    # Tempo médio de resolução
    if "data_criacao_erro" in df_errors.columns and "data_atualizacao_erro" in df_errors.columns and "corrigido_erro" in df_errors.columns:
        df_res = df_errors[df_errors["corrigido_erro"]].copy()
        df_res["dias_resolucao"] = (
            df_res["data_atualizacao_erro"] - df_res["data_criacao_erro"]
        ).dt.days
        tempo_medio = df_res["dias_resolucao"].mean()
        tempo_str = f"{tempo_medio:.1f} dias" if not pd.isna(tempo_medio) else "N/A"
    else:
        tempo_str = "N/A"

    # ------------------------------------------------------------------ #
    # KPIs                                                                 #
    # ------------------------------------------------------------------ #
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("📋 Total de Erros", f"{total_erros:,}")
    c2.metric("✅ Atendidos", f"{atendidos:,}")
    c3.metric("🔧 Corrigidos", f"{corrigidos:,}")
    c4.metric("⚠️ Pendentes", f"{pendentes:,}",
              delta=f"{pendentes/total_erros*100:.0f}% do total" if total_erros else None,
              delta_color="inverse")
    c5.metric("⏱️ Tempo Médio Resolução", tempo_str)

    st.markdown("---")
    col_left, col_right = st.columns(2)

    # ------------------------------------------------------------------ #
    # Erros por Órgão                                                      #
    # ------------------------------------------------------------------ #
    with col_left:
        st.markdown("#### Erros por Órgão")
        if "siglaorgao" in df_errors.columns:
            df_orgao = (
                df_errors.groupby("siglaorgao")
                .agg(
                    Total=("iderroservico", "count"),
                    Atendidos=("atendido", "sum"),
                    Corrigidos=("corrigido_erro", "sum"),
                )
                .reset_index()
                .sort_values("Total", ascending=True)
            )
            df_orgao["Pendentes"] = df_orgao["Total"] - df_orgao["Atendidos"]

            fig = px.bar(
                df_orgao,
                x=["Atendidos", "Pendentes"],
                y="siglaorgao",
                orientation="h",
                barmode="stack",
                color_discrete_map={"Atendidos": "#22C55E", "Pendentes": "#EF4444"},
                labels={"siglaorgao": "Órgão", "value": "Erros", "variable": "Status"},
            )
            fig.update_layout(
                height=380,
                margin=dict(t=10, b=10, l=10, r=10),
                legend_title_text="Status",
                yaxis=dict(autorange="reversed"),
            )
            st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------------------ #
    # Evolução Temporal de Erros                                           #
    # ------------------------------------------------------------------ #
    with col_right:
        st.markdown("#### Evolução Mensal de Erros")
        if "data_criacao_erro" in df_errors.columns:
            df_ev = df_errors.copy()
            df_ev["Mês"] = df_ev["data_criacao_erro"].dt.to_period("M").astype(str)
            df_ev_group = df_ev.groupby("Mês").size().reset_index(name="Erros")

            fig_line = px.line(
                df_ev_group,
                x="Mês",
                y="Erros",
                markers=True,
                color_discrete_sequence=["#EF4444"],
            )
            fig_line.update_layout(
                height=380,
                margin=dict(t=10, b=10, l=10, r=10),
                xaxis_title="",
                yaxis_title="Erros reportados",
            )
            st.plotly_chart(fig_line, use_container_width=True)

    # ------------------------------------------------------------------ #
    # Tabela Operacional                                                   #
    # ------------------------------------------------------------------ #
    st.markdown("---")
    st.markdown("#### 📄 Detalhamento de Erros")

    filtro_pendentes = st.checkbox("Mostrar apenas pendentes (não atendidos)", value=False,
                                   key="cartas_erros_pendentes")
    df_tabela = df_errors[~df_errors["atendido"]] if filtro_pendentes else df_errors.copy()

    # Link dinâmico
    if "slug_categoria" in df_tabela.columns and "slug_servico" in df_tabela.columns:
        df_tabela["Link"] = (
            "https://www.ms.gov.br/" + 
            df_tabela["slug_categoria"].fillna("servicos") + "/" + 
            df_tabela["slug_servico"]
        )
    else:
        df_tabela["Link"] = ""

    cols_tabela = [c for c in [
        "siglaorgao", "titulo_servico", "Link", "conteudo",
        "atendido", "corrigido_erro", "resolucao_erro",
        "reportado_erro", "data_criacao_erro", "data_atualizacao_erro"
    ] if c in df_tabela.columns]

    rename_map = {
        "siglaorgao": "Órgão",
        "titulo_servico": "Serviço",
        "Link": "Acessar Serviço",
        "conteudo": "Tipo de Erro",
        "atendido": "Atendido",
        "corrigido_erro": "Corrigido",
        "resolucao_erro": "Resolução",
        "reportado_erro": "Reportado em",
        "data_criacao_erro": "Data Abertura",
        "data_atualizacao_erro": "Última Atualização",
    }

    st.dataframe(
        df_tabela[cols_tabela].rename(columns=rename_map),
        column_config={
            "Acessar Serviço": st.column_config.LinkColumn(
                "Acessar Serviço",
                display_text="🔗 Abrir Serviço"
            )
        },
        use_container_width=True,
        hide_index=True,
    )
