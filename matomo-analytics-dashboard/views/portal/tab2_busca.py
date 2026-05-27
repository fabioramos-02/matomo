import streamlit as st
import plotly.express as px
from utils.charts_formatter import create_top_bar_chart

def render_tab2_busca(df_search):
    st.header("Intenção de Busca no Portal")
    st.markdown("O que o cidadão buscou na **lupa** do site — capturado via SiteSearch e URLs `/buscar/q=*`.")
    if not df_search.empty:
        col1, col2 = st.columns([2, 1])
        with col1:
            # Correção do ValueError: a coluna correta é 'Buscas' e não 'Pesquisas'
            fig_search = create_top_bar_chart(df_search.head(15), 'Buscas', 'Palavra-chave', 'Purples')
            fig_search.update_layout(title="Top 15 Termos Buscados")
            st.plotly_chart(fig_search, width="stretch")
        with col2:
            st.dataframe(df_search, height=400)
    else:
        st.info("Nenhuma pesquisa interna registrada no período.")
