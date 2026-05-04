import streamlit as st
import pandas as pd
import plotly.express as px
from utils.data_processor import identify_service_cards
from utils.data_loaders import load_transitions_data, load_outlinks_data

def render_tab4_jornada(df_pages, api, period, date, selected_site_id):
    st.header("Fluxo de Navegação (Jornada)")
    st.markdown("O portal do governo atua muitas vezes como um **Hub**: o cidadão entra, pesquisa e é direcionado para o serviço real em outro sistema (Detran, Sefaz, etc).")
    
    st.markdown("---")
    
    # 1. OUTLINKS (Destino Final)
    st.subheader("1. Fuga do Hub (Links Externos)")
    st.markdown("Para onde os cidadãos vão ao sair do portal?")
    with st.spinner("Analisando destinos..."):
        outlinks = load_outlinks_data(api, period, date, selected_site_id)
        if outlinks:
            df_out = pd.DataFrame(outlinks)
            if 'label' in df_out.columns and 'nb_visits' in df_out.columns:
                df_out = df_out[['label', 'nb_visits']].rename(columns={'label': 'Domínio de Destino', 'nb_visits': 'Visitas'})
                df_out = df_out[~df_out['Domínio de Destino'].str.contains('ms.gov.br/login')] # Ignora login
                
                # Exibe o gráfico de outlinks
                fig_out = px.bar(df_out.head(15), x='Visitas', y='Domínio de Destino', orientation='h', color='Visitas', color_continuous_scale='Reds')
                fig_out.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_out, use_container_width=True)
        else:
            st.info("Não há registros de links externos suficientes no período.")

    st.markdown("---")

    # 2. TRANSITIONS (Micro-Funil Específico)
    st.subheader("2. Análise Focada (Micro-Funil)")
    st.markdown("Selecione uma Carta de Serviço específica para entender a origem e o destino imediato dela.")
    
    df_services = identify_service_cards(df_pages)
    if not df_services.empty:
        opcoes = df_services['Nome do Serviço'].tolist()
        servico_selecionado = st.selectbox("Selecione o Serviço para analisar:", opcoes)
        
        row = df_services[df_services['Nome do Serviço'] == servico_selecionado].iloc[0]
        url_alvo = row['URL_Original']
        
        # Correção da URL: A API Transitions do Matomo precisa da URL absoluta (ou exata)
        # Se a label vier apenas como /categoria/servico, injetamos o domínio padrão.
        if url_alvo.startswith('/'):
            url_alvo = "https://www.ms.gov.br" + url_alvo
        
        with st.spinner("Calculando transições... (O primeiro carregamento é direto da API e pode demorar um pouco, mas depois fica em cache)"):
            transitions = load_transitions_data(api, period, date, url_alvo, selected_site_id)
            
            col_origem, col_destino = st.columns(2)
            with col_origem:
                st.write("⬅️ **De onde vieram (Páginas Anteriores)**")
                if transitions and transitions.get('origens') and len(transitions['origens']) > 0:
                    st.table(pd.DataFrame(transitions['origens']))
                else:
                    st.warning("Sem dados suficientes de origem. Ninguém acessou essa página vindo de outro link interno neste período.")
                    
            with col_destino:
                st.write("➡️ **Para onde foram (Próximas Páginas)**")
                if transitions and transitions.get('destinos') and len(transitions['destinos']) > 0:
                    st.table(pd.DataFrame(transitions['destinos']))
                else:
                    st.warning("Sem dados suficientes de destino. Isso geralmente significa que o cidadão saiu do site (Outlink) a partir daqui.")
    else:
        st.warning("Não há dados de serviço para analisar o micro-funil.")
