import streamlit as st
import plotly.express as px


def render_ga_tab1_overview(overview: dict, df_platform, df_funnel):
    st.header("Visão Geral — MS Digital App")
    st.markdown("Métricas consolidadas de uso do aplicativo no período selecionado.")

    # Extrai Novos Downloads (first_open) do df_funnel
    novos_downloads = 0
    if not df_funnel.empty:
        df_fo = df_funnel[df_funnel["Evento"] == "first_open"]
        if not df_fo.empty:
            novos_downloads = int(df_fo.iloc[0]["Usuários"])

    # KPIs
    col0, col1, col2, col3, col4 = st.columns(5)
    col0.metric("📥 Novos Downloads", f"{novos_downloads:,}".replace(",", "."))
    col1.metric("👤 Usuários Ativos", f"{overview['total_users']:,}".replace(",", "."))
    col2.metric("📱 Sessões", f"{overview['total_sessions']:,}".replace(",", "."))
    col3.metric("🖥️ Visualizações de Tela", f"{overview['total_views']:,}".replace(",", "."))
    col4.metric("⏱️ Engajamento Médio", overview.get("avg_engagement", "0s"))

    if overview["total_sessions"] > 0:
        telas_por_sessao = round(overview["total_views"] / overview["total_sessions"], 1)
        col1.caption(f"Telas por sessão: **{telas_por_sessao}**")
    
    col4.caption("Tempo médio por usuário ativo")

    st.markdown("---")

    col_ret, col_plat = st.columns(2)

    # Novos vs Recorrentes
    with col_ret:
        st.subheader("🔄 Novos vs Recorrentes")
        df_ret = overview["retention_df"]
        if not df_ret.empty:
            fig = px.pie(
                df_ret, values="Usuários", names="Tipo", hole=0.5,
                color_discrete_map={"Novos": "#00b4d8", "Recorrentes": "#0077b6"},
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            fig.update_layout(showlegend=False, margin=dict(t=20, b=20))
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Sem dados de retenção para o período.")

    # Plataforma
    with col_plat:
        st.subheader("📲 Plataforma")
        if not df_platform.empty:
            df_plat_group = df_platform.groupby("Plataforma", as_index=False)["Usuários"].sum()
            df_plat_group = df_plat_group[df_plat_group["Plataforma"] != "(not set)"]
            fig_plat = px.pie(
                df_plat_group, values="Usuários", names="Plataforma", hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_plat.update_traces(textposition="inside", textinfo="percent+label")
            fig_plat.update_layout(showlegend=False, margin=dict(t=20, b=20))
            st.plotly_chart(fig_plat, width="stretch")

            # Detalhamento por OS
            df_os = df_platform.groupby("Sistema", as_index=False)["Usuários"].sum()
            df_os = df_os[df_os["Sistema"] != "(not set)"].sort_values("Usuários", ascending=False)
        else:
            st.info("Sem dados de plataforma para o período.")
