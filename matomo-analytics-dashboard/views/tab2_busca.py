import streamlit as st
import plotly.express as px

def render_tab2_busca(df_search):
    st.header("Intenção de Busca no Portal")
    st.markdown("O que o cidadão digitou na **lupa** do site.")
    if not df_search.empty:
        col1, col2 = st.columns([2, 1])
        with col1:
            # Correção do ValueError: a coluna correta é 'Buscas' e não 'Pesquisas'
            fig_search = px.bar(df_search.head(15), x='Buscas', y='Palavra-chave', orientation='h', color='Buscas', color_continuous_scale='Purples', title="Top 15 Termos Buscados")
            fig_search.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_search, use_container_width=True)
        with col2:
            st.dataframe(df_search, height=400)
    else:
        st.info("Nenhuma pesquisa interna registrada no período.")
