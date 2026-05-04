import streamlit as st
import plotly.express as px
from utils.data_processor import identify_service_cards

def render_tab3_servicos(df_pages):
    st.header("Serviços Consumidos")
    st.markdown("Identificadas pelo padrão de URL `/categoria/servico`.")
    
    df_services = identify_service_cards(df_pages)
    
    if not df_services.empty:
        df_cat = df_services.groupby('Categoria', as_index=False)['Visitas'].sum().sort_values(by='Visitas', ascending=False)
        
        col_cat, col_serv = st.columns(2)
        with col_cat:
            st.subheader("Top Categorias de Serviço (Geral)")
            st.markdown("Clique em uma barra para filtrar os serviços ao lado:")
            fig_cat = px.bar(df_cat.head(10), x='Visitas', y='Categoria', orientation='h', color='Visitas', color_continuous_scale='Oranges')
            fig_cat.update_layout(yaxis={'categoryorder':'total ascending'}, clickmode='event+select')
            
            # Interactive Selection
            event = st.plotly_chart(fig_cat, use_container_width=True, on_select="rerun", selection_mode="points")
            
            selected_category = "Todas as Categorias"
            try:
                points = None
                if hasattr(event, "selection") and isinstance(event.selection, dict):
                    points = event.selection.get("points")
                elif isinstance(event, dict) and "selection" in event:
                    points = event["selection"].get("points")
                    
                if points and len(points) > 0:
                    selected_category = points[0].get("y", "Todas as Categorias")
            except Exception as e:
                print("Erro lendo seleção do plotly:", e)

        lista_categorias = ["Todas as Categorias"] + sorted(df_services['Categoria'].unique().tolist())
        
        idx = 0
        if selected_category in lista_categorias:
            idx = lista_categorias.index(selected_category)
            
        categoria_selecionada = st.selectbox("🎯 Ou filtre Cartas por Categoria manualmente:", lista_categorias, index=idx)
        
        if categoria_selecionada != "Todas as Categorias":
            df_filtered = df_services[df_services['Categoria'] == categoria_selecionada]
        else:
            df_filtered = df_services
            
        with col_serv:
            st.subheader(f"Top 10 Cartas ({categoria_selecionada})")
            fig_serv = px.bar(df_filtered.head(10), x='Visitas', y='Nome do Serviço', orientation='h', color='Visitas', color_continuous_scale='Blues')
            fig_serv.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_serv, use_container_width=True)

        st.subheader("Explorar Cartas (Links Diretos)")
        
        # Adiciona a coluna de ranking/classificação (#)
        df_table = df_filtered[['Nome do Serviço', 'Categoria', 'Visitas', 'Link']].copy()
        df_table.reset_index(drop=True, inplace=True)
        df_table.insert(0, '#', df_table.index + 1)
        
        st.dataframe(
            df_table,
            column_config={
                "#": st.column_config.NumberColumn("#", width="small"),
                "Link": st.column_config.LinkColumn("Acessar no Portal", display_text="🔗 Abrir Serviço")
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.warning("Não foi possível identificar Cartas de Serviço no padrão de URLs para este período.")
