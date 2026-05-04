import streamlit as st
import plotly.express as px

def render_tab1_perfil(df_cities, df_browsers, df_device_types, df_time, ms_geojson):
    st.header("Perfil do Cidadão")
    st.markdown("Quem são, de onde vêm, com qual dispositivo e em qual horário acessam.")
    
    st.subheader("Distribuição Geográfica (Mato Grosso do Sul)")
    if not df_cities.empty:
        col_map, col_tab = st.columns([2, 1])
        with col_map:
            try:
                df_map = df_cities[df_cities['Cidade'] != 'Unknown'].copy()
                fig_cities = px.choropleth_mapbox(
                    df_map, geojson=ms_geojson, locations='Cidade', featureidkey='properties.name',
                    color='Visitas', color_continuous_scale='Greens', mapbox_style='carto-positron',
                    zoom=5, center={'lat': -20.44278, 'lon': -54.64639}, opacity=0.7, title="Acessos por Município"
                )
                fig_cities.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
                st.plotly_chart(fig_cities, use_container_width=True)
            except Exception as e:
                fig_cities = px.bar(df_cities.head(15), x='Cidade', y='Visitas', color='Visitas', color_continuous_scale='Greens', title="Top 15 Cidades")
                st.plotly_chart(fig_cities, use_container_width=True)
        with col_tab:
            st.dataframe(df_cities, height=400)
    else:
        st.info("Nenhum dado de cidade encontrado para o MS no período.")
        
    st.markdown("---")
    
    col_devices, col_time = st.columns(2)
    with col_devices:
        st.subheader("Dispositivos e Navegadores")
        col_b, col_t = st.columns(2)
        with col_b:
            if not df_browsers.empty:
                fig_b = px.pie(df_browsers, values='Visitas', names='Navegador', hole=0.4, title='Navegadores')
                fig_b.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_b, use_container_width=True)
        with col_t:
            if not df_device_types.empty:
                fig_d = px.pie(df_device_types, values='Visitas', names='Dispositivo', hole=0.4, title='Dispositivos')
                fig_d.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_d, use_container_width=True)
                
    with col_time:
        st.subheader("Picos de Acesso por Horário")
        if not df_time.empty:
            fig_time = px.bar(df_time, x='Hora', y='Visitas', color_discrete_sequence=['#ff7f0e'])
            st.plotly_chart(fig_time, use_container_width=True)
        else:
            st.info("Sem dados de horário disponíveis.")
