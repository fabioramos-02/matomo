import pandas as pd
import streamlit as st
import plotly.express as px


def render_ga_tab3_perfil(df_cities, df_os, df_device_types, df_time, ms_geojson, df_country_map=None):
    st.header("Perfil Técnico e Geográfico")
    st.markdown("""
    Esta visão revela **quem** é o cidadão digital e **de onde** ele interage. 
    A compreensão da infraestrutura tecnológica e da capilaridade geográfica permite otimizar a experiência do app para a realidade do usuário.
    """)

    # ── Mapa-mundo por país ───────────────────────────────────────────────────
    st.subheader("🌎 Alcance Global (Países)")
    if df_country_map is not None and not df_country_map.empty:
        col_map_world, col_tab_world = st.columns([2, 1])

        with col_map_world:
            import numpy as np
            df_plot = df_country_map.copy()
            # Escala Logarítmica para a cor (permite ver países com 1 acesso vs 80k)
            df_plot["Usuários (Log)"] = np.log10(df_plot["Usuários"] + 1)
            
            fig_world = px.choropleth(
                df_plot,
                locations="País",
                locationmode="country names",
                color="Usuários (Log)",
                hover_name="País",
                hover_data={"Usuários": True, "Usuários (Log)": False},
                color_continuous_scale="Viridis", 
                projection="natural earth",
            )
            fig_world.update_layout(
                margin=dict(t=0, b=0, l=0, r=0),
                coloraxis_showscale=False,
                geo=dict(showframe=False, showcoastlines=True, lakecolor="white"),
                height=400
            )
            st.plotly_chart(fig_world, use_container_width=True)

        with col_tab_world:
            df_pais = df_country_map.copy()
            df_pais.insert(0, "#", df_pais.index + 1)
            st.dataframe(df_pais[["#", "País", "Usuários"]], hide_index=True, use_container_width=True, height=400)
    else:
        st.info("Sem dados de país disponíveis.")

    st.markdown("---")

    # ── Mapa de cidades ──────────────────────────────────────────────────────
    st.subheader("🗺️ Distribuição Geográfica (Cidades)")
    st.markdown("""
    **Onde estão nossos usuários?** O mapa abaixo ilustra a densidade de acessos por localização. 
    Isso ajuda a identificar regiões com alta adoção e áreas que podem necessitar de ações de fomento à digitalização.
    """)
    
    if not df_cities.empty:
        col_map, col_tab = st.columns([2, 1])

        with col_map:
            # Filtro para evitar pontos inválidos (Verifica se colunas existem e têm dados)
            has_coords = "lat" in df_cities.columns and "lon" in df_cities.columns
            df_map = pd.DataFrame()
            
            if has_coords:
                # Converte para numerico por seguranca e remove nulos
                df_cities["lat"] = pd.to_numeric(df_cities["lat"], errors="coerce")
                df_cities["lon"] = pd.to_numeric(df_cities["lon"], errors="coerce")
                df_map = df_cities[df_cities["lat"].notna() & df_cities["lon"].notna()].copy()
            
            if not df_map.empty:
                fig_map = px.scatter_mapbox(
                    df_map,
                    lat="lat",
                    lon="lon",
                    size="Visitas",
                    color="Visitas",
                    hover_name="Cidade",
                    hover_data={"UF": True, "Visitas": True, "lat": False, "lon": False},
                    color_continuous_scale="Blues",
                    size_max=15,
                    zoom=3.5,
                    center={"lat": -15.7801, "lon": -47.9292}, # Centro do Brasil
                    mapbox_style="carto-positron",
                )
                fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=500)
                st.plotly_chart(fig_map, use_container_width=True)
            else:
                st.info("Coordenadas geográficas detalhadas não disponíveis no payload do GA4 para esta propriedade. O mapa de calor em tempo real requer que a coleta de latitude/longitude esteja ativa.")

        with col_tab:
            df_show = df_cities.copy()
            df_show.insert(0, "#", df_show.index + 1)
            cols = ["#", "Cidade", "UF", "Visitas"]
            st.dataframe(df_show[cols], hide_index=True, use_container_width=True, height=500)
    else:
        st.info("Sem dados geográficos detalhados.")

    st.markdown("---")

    # ── Horário de uso ────────────────────────────────────────────────────────
    st.subheader("⏰ Hábitos de Acesso (Horários)")
    st.markdown("Identifica os picos de uso durante o dia para planejar janelas de manutenção e atualizações com menor impacto.")
    if not df_time.empty:
        fig_time = px.bar(df_time, x="Hora", y="Visitas", color_discrete_sequence=["#0077b6"])
        fig_time.update_layout(margin=dict(t=10, b=10))
        st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.info("Sem dados de horário.")
