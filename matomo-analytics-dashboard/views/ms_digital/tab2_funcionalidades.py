from datetime import date as dt_date

import streamlit as st
import plotly.express as px
from utils.charts_formatter import create_top_bar_chart


def _months_in_range(start_date, end_date):
    if not start_date or not end_date:
        return 1.0
    try:
        s = dt_date.fromisoformat(start_date)
        e = dt_date.fromisoformat(end_date)
    except (TypeError, ValueError):
        return 1.0
    return max(((e - s).days + 1) / 30.44, 1.0)


def render_ga_tab2_funcionalidades(df_services, df_services_trend, df_external_links=None, start_date=None, end_date=None):
    st.header("Serviços Mais Acessados — MS Digital App")
    st.markdown("Quais funcionalidades os cidadãos mais utilizam. Baseado em acessos de tela (`screen_view`).")

    n_meses = _months_in_range(start_date, end_date)

    # ── KPIs ─────────────────────────────────────────────────────────────────
    if not df_services.empty:
        total_acessos = int(df_services["Acessos"].sum())
        servico_top = df_services.iloc[0]["Serviço"]
        acessos_top = int(df_services.iloc[0]["Acessos"])
        pct_top3 = round(df_services.head(3)["Acessos"].sum() / total_acessos * 100, 1) if total_acessos > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("📊 Total de Acessos a Serviços", f"{total_acessos:,}".replace(",", "."))
        col1.caption(f"Média mensal: **{int(total_acessos / n_meses):,}".replace(",", ".") + "**")
        col2.metric("🏆 Serviço #1", servico_top, f"{acessos_top:,} acessos".replace(",", "."))
        col2.caption(f"Média mensal do #1: **{int(acessos_top / n_meses):,}".replace(",", ".") + "**")
        col3.metric("📈 Concentração Top 3", f"{pct_top3}%", "dos acessos totais")
        col3.caption(f"Período: {start_date} → {end_date} (~{n_meses:.1f} meses)")

    st.markdown("---")

    # ── Ranking de Serviços ───────────────────────────────────────────────────
    st.subheader("📱 Ranking de Serviços")

    if not df_services.empty:
        col_chart, col_table = st.columns([1.4, 1])

        with col_chart:
            df_top = df_services.head(15).copy()
            df_top["Média Mensal"] = (df_top["Acessos"] / n_meses).round(0).astype(int)
            fig = create_top_bar_chart(df_top, "Acessos", "Serviço", "Blues")

            n = len(df_top)
            text_labels = [f"<b>{int(v):,}</b>".replace(",", ".") for v in df_top["Acessos"]]
            text_colors = ["#FFFFFF"] + ["#000000"] * (n - 1)
            text_sizes = [13] + [12] * (n - 1)

            fig.update_layout(
                coloraxis_showscale=False,
                margin=dict(t=10, b=10, r=80),
                font=dict(color="#000000"),
            )
            fig.update_xaxes(
                tickfont=dict(color="#000000", size=11),
                title_font=dict(color="#000000"),
            )
            fig.update_yaxes(
                tickfont=dict(color="#000000", size=11),
                title_font=dict(color="#000000"),
            )
            fig.update_traces(
                text=text_labels,
                texttemplate="%{text}",
                textfont=dict(color=text_colors, size=text_sizes, family="Arial Black"),
                customdata=df_top[["Média Mensal"]].values,
                hovertemplate="<b>%{y}</b><br>Acessos: %{x:,.0f}<br>Média mensal: %{customdata[0]:,.0f}<extra></extra>",
            )
            st.plotly_chart(fig, width="stretch")

        with col_table:
            st.markdown("**Tabela completa**")
            df_show = df_services.copy()
            df_show.insert(0, "#", df_show.index + 1)
            df_show["% do Total"] = df_show["%"].apply(lambda v: f"{v}%")
            df_show["Média Mensal"] = (df_show["Acessos"] / n_meses).round(0).astype(int)
            st.dataframe(
                df_show[["#", "Serviço", "Acessos", "Média Mensal", "% do Total"]],
                column_config={
                    "Acessos": st.column_config.NumberColumn("Acessos", format="%d"),
                    "Média Mensal": st.column_config.NumberColumn("Média/mês", format="%d"),
                },
                hide_index=True,
                width="stretch",
                height=500,
            )
    else:
        st.info("Sem dados de serviços para o período.")

    st.markdown("---")

    # ── Evolução Temporal ─────────────────────────────────────────────────────
    st.subheader("📈 Evolução Temporal — Top 5 Serviços")
    st.caption("Acessos diários dos 5 serviços mais utilizados no período.")

    if df_services_trend is not None and not df_services_trend.empty:
        fig_trend = px.line(
            df_services_trend,
            x="Data",
            y="Acessos",
            color="Serviço",
            markers=True,
            color_discrete_sequence=px.colors.qualitative.Plotly,
        )
        fig_trend.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5),
            margin=dict(t=10, b=80),
        )
        st.plotly_chart(fig_trend, width="stretch")
    else:
        st.info("Evolução temporal não disponível para o período selecionado (necessário mais de 1 dia).")

    st.markdown("---")

    # ── Links Externos (Redirecionamentos) ────────────────────────────────────
    st.subheader("🔗 Links Externos — Para onde o usuário é redirecionado")
    st.caption("Destinos clicados dentro do app (eventos `click` outbound).")

    if df_external_links is not None and not df_external_links.empty:
        col_ext_chart, col_ext_table = st.columns([1.3, 1])

        with col_ext_chart:
            fig_ext = create_top_bar_chart(df_external_links.head(15), "Cliques", "Destino", "Greens")
            fig_ext.update_layout(coloraxis_showscale=False)
            fig_ext.update_yaxes(tickfont=dict(size=11))
            st.plotly_chart(fig_ext, width="stretch")

        with col_ext_table:
            df_ext_show = df_external_links.head(20).copy()
            df_ext_show.insert(0, "#", df_ext_show.index + 1)
            st.dataframe(df_ext_show[["#", "Destino", "Cliques", "Usuários"]], hide_index=True, width="stretch")
    else:
        st.info("Sem dados de links externos para o período.")

