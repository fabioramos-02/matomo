from datetime import date as dt_date

import streamlit as st
import plotly.express as px


def _months_in_range(start_date, end_date):
    if not start_date or not end_date:
        return 1.0
    try:
        s = dt_date.fromisoformat(start_date)
        e = dt_date.fromisoformat(end_date)
    except (TypeError, ValueError):
        return 1.0
    return max(((e - s).days + 1) / 30.44, 1.0)


def _fmt_int(n):
    return f"{int(n):,}".replace(",", ".")


def render_ga_tab1_overview(overview: dict, df_platform, df_funnel, start_date=None, end_date=None, downloads_lifetime=None, downloads_last12m=None):
    st.header("Visão Geral — MS Digital App")
    st.markdown("Métricas consolidadas de uso do aplicativo no período selecionado.")

    n_meses = _months_in_range(start_date, end_date)

    # Extrai Novos Downloads (first_open) do df_funnel
    novos_downloads = 0
    if not df_funnel.empty:
        df_fo = df_funnel[df_funnel["Evento"] == "first_open"]
        if not df_fo.empty:
            novos_downloads = int(df_fo.iloc[0]["Usuários"])

    # ── Downloads acumulados (vigência + últimos 12 meses) ─────────────
    if downloads_lifetime or downloads_last12m:
        st.markdown("#### 📥 Downloads Acumulados")
        col_life, col_12m = st.columns(2)
        if downloads_lifetime:
            life_users = downloads_lifetime.get("users", 0)
            life_start = downloads_lifetime.get("start", "—")
            life_end = downloads_lifetime.get("end", "—")
            life_months = _months_in_range(life_start, life_end)
            col_life.metric("🗓️ Downloads Totais (Vigência)", _fmt_int(life_users))
            col_life.caption(
                f"Desde **{life_start}** até **{life_end}** · "
                f"Média mensal: **{_fmt_int(life_users / life_months)}**"
            )
        if downloads_last12m:
            m12_users = downloads_last12m.get("users", 0)
            col_12m.metric("📆 Downloads — Últimos 12 meses", _fmt_int(m12_users))
            col_12m.caption(f"Média mensal: **{_fmt_int(m12_users / 12)}**")
        st.markdown("---")

    st.markdown("#### 📊 Métricas do Período Selecionado")
    # KPIs período
    col0, col1, col2, col3, col4 = st.columns(5)

    col0.metric("📥 Novos Downloads", _fmt_int(novos_downloads))
    col0.caption(f"Média mensal: **{_fmt_int(novos_downloads / n_meses)}**")

    col1.metric("👤 Usuários Ativos", _fmt_int(overview['total_users']))
    col1.caption(f"Média mensal: **{_fmt_int(overview['total_users'] / n_meses)}**")

    col2.metric("📱 Sessões", _fmt_int(overview['total_sessions']))
    col2.caption(f"Média mensal: **{_fmt_int(overview['total_sessions'] / n_meses)}**")

    col3.metric("🖥️ Visualizações de Tela", _fmt_int(overview['total_views']))
    col3.caption(f"Média mensal: **{_fmt_int(overview['total_views'] / n_meses)}**")

    col4.metric("⏱️ Engajamento Médio", overview.get("avg_engagement", "0s"))
    col4.caption("Tempo médio por usuário ativo")

    if overview["total_sessions"] > 0:
        telas_por_sessao = round(overview["total_views"] / overview["total_sessions"], 1)
        st.caption(f"📌 **Telas por sessão:** {telas_por_sessao} · Período: {start_date} → {end_date} (~{n_meses:.1f} meses)")

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
            fig.update_traces(
                textposition="inside",
                texttemplate="<b>%{label}<br>%{percent:.1%}</b>",
                insidetextfont=dict(size=16)
            )
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
            fig_plat.update_traces(
                textposition="inside",
                texttemplate="<b>%{label}<br>%{percent:.1%}</b>",
                insidetextfont=dict(size=16)
            )
            fig_plat.update_layout(showlegend=False, margin=dict(t=20, b=20))
            st.plotly_chart(fig_plat, width="stretch")

            # Detalhamento por OS
            df_os = df_platform.groupby("Sistema", as_index=False)["Usuários"].sum()
            df_os = df_os[df_os["Sistema"] != "(not set)"].sort_values("Usuários", ascending=False)
        else:
            st.info("Sem dados de plataforma para o período.")
