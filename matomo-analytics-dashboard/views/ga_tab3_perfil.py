import streamlit as st
import plotly.express as px


def render_ga_tab3_perfil(df_cities, df_os, df_device_types, df_time, df_platform, ms_geojson):
    st.header("Perfil Técnico dos Usuários")
    st.markdown("De onde acessam, qual dispositivo usam e em qual horário.")

    # Distribuição geográfica
    st.subheader("🗺️ Distribuição Geográfica (Mato Grosso do Sul)")
    if not df_cities.empty:
        col_map, col_tab = st.columns([2, 1])
        with col_map:
            try:
                df_map = df_cities[df_cities["Cidade"] != "Unknown"].copy()
                fig_map = px.choropleth_mapbox(
                    df_map, geojson=ms_geojson, locations="Cidade", featureidkey="properties.name",
                    color="Visitas", color_continuous_scale="Blues", mapbox_style="carto-positron",
                    zoom=5, center={"lat": -20.44278, "lon": -54.64639}, opacity=0.7,
                    title="Usuários por Município",
                )
                fig_map.update_layout(margin={"r": 0, "t": 40, "l": 0, "b": 0})
                st.plotly_chart(fig_map, use_container_width=True)
            except Exception:
                fig_bar = px.bar(df_cities.head(15), x="Cidade", y="Visitas",
                                 color="Visitas", color_continuous_scale="Blues", title="Top 15 Cidades")
                st.plotly_chart(fig_bar, use_container_width=True)
        with col_tab:
            st.dataframe(df_cities, height=400, hide_index=True)
    else:
        st.info("Sem dados de cidade disponíveis.")

    st.markdown("---")

    # Horário de uso
    st.subheader("⏰ Horários de Maior Uso")
    if not df_time.empty:
        fig_time = px.bar(df_time, x="Hora", y="Visitas", color_discrete_sequence=["#0077b6"])
        st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.info("Sem dados de horário.")

    st.markdown("---")

    # OS e Device Type
    st.subheader("📱 Sistema Operacional e Tipo de Dispositivo")
    col_os, col_dev = st.columns(2)

    with col_os:
        if not df_os.empty:
            st.markdown("**Sistema Operacional**")
            fig_os = px.pie(
                df_os, values="Visitas", names="Navegador", hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig_os.update_traces(textposition="inside", textinfo="percent+label")
            fig_os.update_layout(showlegend=False, margin=dict(t=20, b=20))
            st.plotly_chart(fig_os, use_container_width=True)

    with col_dev:
        if not df_device_types.empty:
            st.markdown("**Categoria de Dispositivo**")
            fig_dev = px.pie(
                df_device_types, values="Visitas", names="Dispositivo", hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            fig_dev.update_traces(textposition="inside", textinfo="percent+label")
            fig_dev.update_layout(showlegend=False, margin=dict(t=20, b=20))
            st.plotly_chart(fig_dev, use_container_width=True)

    # Detalhamento de plataforma (iOS vs Android vs Web)
    if not df_platform.empty:
        st.markdown("---")
        st.subheader("🔍 Detalhe por Plataforma × Sistema")
        df_detail = df_platform[["Plataforma", "Sistema", "Usuários", "Sessões"]].copy()
        st.dataframe(df_detail, hide_index=True, use_container_width=True)
