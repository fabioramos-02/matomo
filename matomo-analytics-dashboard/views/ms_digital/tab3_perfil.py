import streamlit as st
import plotly.express as px


def render_ga_tab3_perfil(df_cities, df_os, df_device_types, df_time, ms_geojson, df_country_map=None):
    st.header("Perfil Técnico dos Usuários")
    st.markdown("De onde acessam, qual dispositivo usam e em qual horário.")

    # ── Mapa-mundo por país ───────────────────────────────────────────────────
    st.subheader("🌎 Usuários Ativos por País")
    if df_country_map is not None and not df_country_map.empty:
        col_map_world, col_tab_world = st.columns([2, 1])

        with col_map_world:
            fig_world = px.choropleth(
                df_country_map,
                locations="ISO",
                color="Usuários",
                hover_name="País",
                color_continuous_scale="Blues",
                projection="natural earth",
            )
            fig_world.update_layout(
                margin=dict(t=0, b=0, l=0, r=0),
                coloraxis_colorbar=dict(title="Usuários"),
                geo=dict(showframe=False, showcoastlines=True),
            )
            st.plotly_chart(fig_world, use_container_width=True)

        with col_tab_world:
            df_pais = df_country_map.copy()
            df_pais.insert(0, "#", df_pais.index + 1)
            st.dataframe(df_pais[["#", "País", "Usuários"]], hide_index=True, use_container_width=True, height=350)
    else:
        st.info("Sem dados de país disponíveis.")

    st.markdown("---")

    # ── Cidades por estado ────────────────────────────────────────────────────
    st.subheader("🗺️ Distribuição por Cidade")
    if not df_cities.empty:
        col_map, col_tab = st.columns([2, 1])

        with col_map:
            try:
                df_map = df_cities[df_cities["Cidade"] != "Unknown"].copy()
                fig_map = px.choropleth_mapbox(
                    df_map, geojson=ms_geojson, locations="Cidade", featureidkey="properties.name",
                    color="Visitas", color_continuous_scale="Blues", mapbox_style="carto-positron",
                    zoom=5, center={"lat": -20.44278, "lon": -54.64639}, opacity=0.7,
                )
                fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
                st.plotly_chart(fig_map, use_container_width=True)
            except Exception:
                fig_bar = px.bar(
                    df_cities.head(15), x="Cidade", y="Visitas",
                    color="Visitas", color_continuous_scale="Blues",
                )
                st.plotly_chart(fig_bar, use_container_width=True)

        with col_tab:
            df_show = df_cities.copy()
            df_show.insert(0, "#", df_show.index + 1)
            cols = ["#", "Cidade"]
            if "UF" in df_show.columns:
                cols.append("UF")
            cols.append("Visitas")
            st.dataframe(df_show[cols], hide_index=True, use_container_width=True, height=400)
    else:
        st.info("Sem dados de cidade disponíveis.")

    st.markdown("---")

    # ── Horário de uso ────────────────────────────────────────────────────────
    st.subheader("⏰ Horários de Maior Uso")
    if not df_time.empty:
        fig_time = px.bar(df_time, x="Hora", y="Visitas", color_discrete_sequence=["#0077b6"])
        fig_time.update_layout(margin=dict(t=10, b=10))
        st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.info("Sem dados de horário.")

    st.markdown("---")

    # ── SO e Dispositivo ─────────────────────────────────────────────────────
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
