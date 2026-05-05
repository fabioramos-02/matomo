import streamlit as st
import plotly.express as px


def render_ga_tab2_funcionalidades(df_screens, df_events):
    st.header("Funcionalidades Mais Usadas")
    st.markdown("Quais telas e ações os cidadãos mais utilizam no MS Digital.")

    col_telas, col_eventos = st.columns(2)

    with col_telas:
        st.subheader("📱 Telas Mais Visitadas")
        if not df_screens.empty:
            df_top = df_screens.head(15)
            fig = px.bar(
                df_top, x="Visitas", y="URL", orientation="h",
                color="Visitas", color_continuous_scale="Blues",
            )
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
            fig.update_yaxes(tickfont=dict(size=11))
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Ranking de Telas")
            df_show = df_screens.head(20).copy()
            df_show.insert(0, "#", df_show.index + 1)
            st.dataframe(df_show[["#", "URL", "Visitas"]], hide_index=True, use_container_width=True)
        else:
            st.info("Sem dados de telas para o período.")

    with col_eventos:
        st.subheader("⚡ Eventos Mais Disparados")
        st.caption("Ações realizadas pelos usuários dentro do app.")
        if not df_events.empty:
            df_top_ev = df_events.head(15)
            fig_ev = px.bar(
                df_top_ev, x="Acessos", y="Evento", orientation="h",
                color="Acessos", color_continuous_scale="Oranges",
            )
            fig_ev.update_layout(yaxis={"categoryorder": "total ascending"}, coloraxis_showscale=False)
            fig_ev.update_yaxes(tickfont=dict(size=11))
            st.plotly_chart(fig_ev, use_container_width=True)

            st.subheader("Ranking de Eventos")
            df_ev_show = df_events.head(20).copy()
            df_ev_show.insert(0, "#", df_ev_show.index + 1)
            st.dataframe(df_ev_show[["#", "Evento", "Acessos"]], hide_index=True, use_container_width=True)
        else:
            st.info("Sem dados de eventos para o período.")
