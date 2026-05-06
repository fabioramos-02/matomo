import streamlit as st
import plotly.express as px

def render_tab1_perfil(df_cities, df_browsers, df_device_types, df_time, ms_geojson, visits_summary=None, fonte="Portal (Matomo)"):
    st.header("Perfil do Cidadão")
    st.markdown("Quem são, de onde vêm, com qual dispositivo e em qual horário acessam.")

    if visits_summary:
        nb_visits = visits_summary.get("nb_visits", 0)
        col_metric = st.columns(3)[0]
        col_metric.metric("Total de Acessos", f"{nb_visits:,}".replace(",", "."))
        st.caption("ℹ️ Valor total de acessos globais (independente de região ou estado).")

    st.subheader("🗺️ Distribuição Geográfica (Mato Grosso do Sul)")
    if not df_cities.empty:
        col_map, col_tab = st.columns([2, 1])
        with col_map:
            try:
                df_map = df_cities[df_cities['Cidade'] != 'Unknown'].copy()
                import numpy as np
                df_map["Visitas (Log)"] = np.log10(df_map["Visitas"] + 1)
                
                fig_cities = px.choropleth_mapbox(
                    df_map, geojson=ms_geojson, locations='Cidade', featureidkey='properties.name',
                    color='Visitas (Log)', color_continuous_scale='YlGn', mapbox_style='carto-positron',
                    zoom=5, center={'lat': -20.44278, 'lon': -54.64639}, opacity=0.7, 
                    title="Densidade de Acessos por Município (Escala Log)",
                    hover_data={"Visitas": True, "Visitas (Log)": False}
                )
                fig_cities.update_layout(margin={"r":0,"t":40,"l":0,"b":0}, coloraxis_showscale=False)
                st.plotly_chart(fig_cities, use_container_width=True)
            except Exception as e:
                fig_cities = px.bar(df_cities.head(15), x='Cidade', y='Visitas', color='Visitas', color_continuous_scale='Greens', title="Top 15 Cidades")
                st.plotly_chart(fig_cities, use_container_width=True)
        with col_tab:
            st.dataframe(df_cities, height=400)
    else:
        st.info("Nenhum dado de cidade encontrado para o MS no período.")
        
    st.markdown("---")
    
    st.subheader("⏰ Picos de Acesso por Horário")
    if not df_time.empty:
        fig_time = px.bar(df_time, x='Hora', y='Visitas', color_discrete_sequence=['#ff7f0e'])
        fig_time.update_xaxes(dtick=1) # Força a exibição de todos os ticks de hora
        st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.info("Sem dados de horário disponíveis.")
        
    st.markdown("---")
    
    st.subheader("💻 Dispositivos e Navegadores")
    col_b, col_t = st.columns(2)
    
    with col_b:
        if not df_browsers.empty:
            label_browsers = "Sistema Operacional" if fonte == "MS Digital (GA4)" else "Navegadores Mais Utilizados"
            st.markdown(f"**{label_browsers}**")
            # Usa paleta qualitativa vibrante (melhor para categorias independentes)
            fig_b = px.pie(df_browsers, values='Visitas', names='Navegador', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_b.update_traces(textposition='inside', textinfo='percent')
            fig_b.update_layout(
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
                margin=dict(t=20, b=40, l=20, r=20)
            )
            st.plotly_chart(fig_b, use_container_width=True)
            
    with col_t:
        if not df_device_types.empty:
            st.markdown("**Tipos de Dispositivo**")
            # Usa paleta qualitativa vibrante 
            fig_d = px.pie(df_device_types, values='Visitas', names='Dispositivo', hole=0.5, color_discrete_sequence=px.colors.qualitative.Set2)
            fig_d.update_traces(textposition='inside', textinfo='percent')
            fig_d.update_layout(
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
                margin=dict(t=20, b=40, l=20, r=20)
            )
            st.plotly_chart(fig_d, use_container_width=True)
