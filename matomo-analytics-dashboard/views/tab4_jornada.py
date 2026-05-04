import streamlit as st
import pandas as pd
import plotly.express as px
import urllib.parse
from utils.data_processor import identify_service_cards
from utils.data_loaders import load_transitions_data, load_outlinks_data, load_last_visits_data

def render_tab4_jornada(df_pages, api, period, date, selected_site_id):
    st.header("Fluxo de Navegação (Jornada)")
    st.markdown("O portal do governo atua muitas vezes como um **Hub**: o cidadão entra, pesquisa e é direcionado para o serviço real em outro sistema (Detran, Sefaz, etc).")
    
    st.markdown("---")
    
    col_out, col_live = st.columns([1, 1.2])
    
    # 1. OUTLINKS (Destino Final)
    with col_out:
        st.subheader("1. Fuga do Hub (Links Externos)")
        st.markdown("Para onde os cidadãos vão ao sair do portal?")
        with st.spinner("Analisando destinos..."):
            outlinks = load_outlinks_data(api, period, date, selected_site_id)
            if outlinks:
                df_out = pd.DataFrame(outlinks)
                if 'label' in df_out.columns and 'nb_visits' in df_out.columns:
                    df_out = df_out[['label', 'nb_visits']].rename(columns={'label': 'Domínio de Destino', 'nb_visits': 'Visitas'})
                    df_out = df_out[~df_out['Domínio de Destino'].str.contains('ms.gov.br/login')] # Ignora login
                    fig_out = px.bar(df_out.head(10), x='Visitas', y='Domínio de Destino', orientation='h', color='Visitas', color_continuous_scale='Reds')
                    fig_out.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_out, use_container_width=True)
            else:
                st.info("Não há registros de links externos suficientes no período.")

    # 2. LIVE VISITS (Linha do Tempo Real)
    with col_live:
        st.subheader("2. Jornadas Reais (Amostragem)")
        st.markdown("Exemplos das últimas visitas reais que **começaram** pela página principal.")
        with st.spinner("Extraindo jornadas..."):
            # O segmento usa URL codificada: pageUrl==http%3A%2F%2Fms.gov.br%2F
            # Mas o site pode ser www.ms.gov.br ou ms.gov.br. Vamos usar entryPageUrl=@ms.gov.br
            segment = urllib.parse.quote("entryPageUrl=@ms.gov.br")
            visits = load_last_visits_data(api, period, date, selected_site_id, segment)
            
            if visits and isinstance(visits, list):
                count = 0
                for v in visits:
                    if count >= 5: break
                    actions = v.get('actionDetails', [])
                    if len(actions) > 1: # Só mostra visitas com mais de 1 clique para ter "jornada"
                        origem = v.get('referrerName', 'Acesso Direto')
                        if not origem: origem = 'Acesso Direto'
                        
                        path = [f"🌐 {origem}"]
                        for a in actions:
                            url = a.get('url', '')
                            # Simplifica a URL para mostrar só o caminho
                            clean_url = url.split('.br')[-1] if '.br' in url else url
                            if len(clean_url) > 30: clean_url = clean_url[:30] + "..."
                            if clean_url == "/" or clean_url == "": clean_url = "/ (Home)"
                            path.append(f"📄 {clean_url}")
                            
                        st.markdown(f"**Visitante {count+1}** (Tempo: {v.get('visitDuration', 0)}s)")
                        st.caption(" ➡️ ".join(path))
                        st.markdown("---")
                        count += 1
                if count == 0:
                    st.info("Não encontramos jornadas com mais de 1 clique nas amostras recentes.")
            else:
                st.info("API não retornou visitas recentes detalhadas para este segmento.")

    st.markdown("---")

    # 3. TRANSITIONS (Micro-Funil Específico)
    st.subheader("3. Análise Focada (Micro-Funil)")
    st.markdown("Selecione uma Carta de Serviço específica para entender a origem e o destino imediato dela.")
    
    df_services = identify_service_cards(df_pages)
    if not df_services.empty:
        opcoes = df_services['Nome do Serviço'].tolist()
        servico_selecionado = st.selectbox("Selecione o Serviço para analisar:", opcoes)
        
        row = df_services[df_services['Nome do Serviço'] == servico_selecionado].iloc[0]
        url_alvo = row['URL_Original']
        
        with st.spinner("Calculando transições..."):
            transitions = load_transitions_data(api, period, date, url_alvo, selected_site_id)
            
            col_origem, col_destino = st.columns(2)
            with col_origem:
                st.write("⬅️ **De onde vieram (Páginas Anteriores)**")
                if transitions and transitions.get('origens') and len(transitions['origens']) > 0:
                    st.table(pd.DataFrame(transitions['origens']))
                else:
                    st.warning("Sem dados suficientes de origem no período.")
                    
            with col_destino:
                st.write("➡️ **Para onde foram (Próximas Páginas)**")
                if transitions and transitions.get('destinos') and len(transitions['destinos']) > 0:
                    st.table(pd.DataFrame(transitions['destinos']))
                else:
                    st.warning("Sem dados suficientes de destino no período. (Provavelmente saíram do site)")
    else:
        st.warning("Não há dados de serviço para analisar o micro-funil.")
