import streamlit as st
import plotly.express as px

def render_ga_tab2_funcionalidades(df_services, df_services_trend, df_events):
    st.header("Serviços Mais Acessados — MS Digital App")
    st.markdown("Quais funcionalidades os cidadãos mais utilizam. Baseado em acessos de tela (`screen_view`).")

    # ── KPIs ─────────────────────────────────────────────────────────────────
    if not df_services.empty:
        total_acessos = int(df_services["Acessos"].sum())
        servico_top = df_services.iloc[0]["Serviço"]
        acessos_top = int(df_services.iloc[0]["Acessos"])
        pct_top3 = round(df_services.head(3)["Acessos"].sum() / total_acessos * 100, 1) if total_acessos > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("📊 Total de Acessos a Serviços", f"{total_acessos:,}".replace(",", "."))
        col2.metric("🏆 Serviço #1", servico_top, f"{acessos_top:,} acessos".replace(",", "."))
        col3.metric("📈 Concentração Top 3", f"{pct_top3}%", "dos acessos totais")

    st.markdown("---")

    # ── Ranking de Serviços ───────────────────────────────────────────────────
    st.subheader("📱 Ranking de Serviços")

    if not df_services.empty:
        col_chart, col_table = st.columns([1.4, 1])

        with col_chart:
            df_top = df_services.head(15).copy()
            fig = px.bar(
                df_top,
                x="Acessos",
                y="Serviço",
                orientation="h",
                color="Acessos",
                color_continuous_scale="Blues",
                text=df_top["%"].apply(lambda v: f"{v}%"),
            )
            fig.update_traces(textposition="outside")
            fig.update_layout(
                yaxis={"categoryorder": "total ascending"},
                coloraxis_showscale=False,
                margin=dict(t=10, b=10, r=80),
            )
            fig.update_yaxes(tickfont=dict(size=11))
            st.plotly_chart(fig, use_container_width=True)

        with col_table:
            st.markdown("**Tabela completa**")
            df_show = df_services.copy()
            df_show.insert(0, "#", df_show.index + 1)
            df_show["% do Total"] = df_show["%"].apply(lambda v: f"{v}%")
            st.dataframe(
                df_show[["#", "Serviço", "Acessos", "% do Total"]],
                hide_index=True,
                use_container_width=True,
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
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Evolução temporal não disponível para o período selecionado (necessário mais de 1 dia).")

    st.markdown("---")

    # ── Eventos Customizados ──────────────────────────────────────────────────
    st.subheader("⚡ Eventos Customizados")
    st.caption("Ações disparadas pela interação do usuário (além de acessos de tela).")

    if not df_events.empty:
        col_ev_chart, col_ev_table = st.columns([1.3, 1])

        with col_ev_chart:
            fig_ev = px.bar(
                df_events.head(15),
                x="Acessos",
                y="Evento",
                orientation="h",
                color="Acessos",
                color_continuous_scale="Oranges",
            )
            fig_ev.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
            fig_ev.update_yaxes(tickfont=dict(size=11))
            st.plotly_chart(fig_ev, use_container_width=True)

        with col_ev_table:
            df_ev_show = df_events.head(20).copy()
            df_ev_show.insert(0, "#", df_ev_show.index + 1)
            st.dataframe(df_ev_show[["#", "Evento", "Acessos"]], hide_index=True, use_container_width=True)
    else:
        st.info("Sem eventos customizados para o período.")
