import streamlit as st
import pandas as pd
from utils.data_processor import identify_service_cards
from utils.data_loaders import load_transitions_data

def render_tab4_jornada(df_pages, api, period, date, selected_site_id):
    st.header("Fluxo de Navegação (Jornada)")
    
    df_services = identify_service_cards(df_pages)
    if not df_services.empty:
        # Pega a carta principal do período selecionado
        top_service_url = df_services.iloc[0]['URL_Original']
        top_service_name = df_services.iloc[0]['Nome do Serviço']
        
        st.markdown(f"Analisando o funil do serviço mais acessado do período: **{top_service_name}**")
        
        # Load transitions dynamically based on the top service
        transitions = load_transitions_data(api, period, date, top_service_url, selected_site_id)
        
        col_origem, col_destino = st.columns(2)
        with col_origem:
            st.write("⬅️ **De onde vieram (Páginas Anteriores)**")
            if transitions.get('origens'):
                st.table(pd.DataFrame(transitions['origens']))
            else:
                st.info("Sem dados suficientes.")
                
        with col_destino:
            st.write("➡️ **Para onde foram (Próximas Páginas)**")
            if transitions.get('destinos'):
                st.table(pd.DataFrame(transitions['destinos']))
            else:
                st.info("Sem dados suficientes.")
    else:
        st.warning("Não há dados de serviço para analisar a jornada.")
