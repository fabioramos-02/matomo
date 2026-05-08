import streamlit as st
import plotly.express as px
from utils.data_processor import identify_service_cards

def render_tab3_servicos(df_pages, fonte="Portal (Matomo)", df_services=None, df_services_trend=None, trend_granularity='day'):
    is_ga = fonte == "MS Digital (GA4)"

    if is_ga:
        st.header("Telas mais Acessadas")
        st.markdown("Telas do app MS Digital ordenadas por visualizações.")

        if not df_pages.empty:
            df_show = df_pages.head(20).copy()
            df_show.insert(0, '#', df_show.index + 1)
            fig = px.bar(df_pages.head(15), x='Visitas', y='URL', orientation='h',
                         color='Visitas', color_continuous_scale='Blues')
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, width="stretch")
            st.dataframe(df_show[['#', 'URL', 'Visitas']], hide_index=True, width="stretch")
        else:
            st.warning("Sem dados de telas para este período.")
        return

    st.header("Serviços Consumidos")
    st.markdown("Identificadas pelo padrão de URL `/categoria/servico`.")

    if df_services is None:
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
            event = st.plotly_chart(fig_cat, width="stretch", on_select="rerun", selection_mode="points")
            
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
            st.plotly_chart(fig_serv, width="stretch")

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
            width="stretch"
        )
    else:
        st.warning("Não foi possível identificar Cartas de Serviço no padrão de URLs para este período.")

    # ── Evolução Temporal — Top 5 Serviços ───────────────────────────────────
    st.markdown("---")
    st.subheader("📈 Evolução Temporal — Top 5 Serviços")
    _labels = {"day": "diários", "month": "mensais", "week": "semanais"}
    granularity_label = _labels.get(trend_granularity, "diários")
    st.caption(f"Acessos {granularity_label} dos 5 serviços mais utilizados no período.")

    st.markdown(
        "Acompanhe a variação dos serviços mais acessados ao longo do tempo.\n\n"
        "- **Picos**: aumento de demanda — campanha, evento ou data comemorativa\n"
        "- **Quedas**: possível indisponibilidade ou perda de interesse\n"
        "- **Curvas similares**: serviços com comportamento relacionado\n\n"
        "_Use este gráfico para identificar oportunidades de comunicação e possíveis problemas operacionais._"
    )

    if df_services_trend is not None and not df_services_trend.empty and df_services_trend['Data'].nunique() > 1:
        fig_trend = px.line(
            df_services_trend,
            x="Data",
            y="Visitas",
            color="Serviço",
            markers=True,
            color_discrete_sequence=px.colors.qualitative.Plotly,
            labels={"Visitas": f"Acessos / {granularity_label[:-1]}", "Data": ""},
        )
        fig_trend.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5),
            margin=dict(t=10, b=80),
            hovermode="x unified",
        )
        fig_trend.update_traces(line=dict(width=2))
        st.plotly_chart(fig_trend, width="stretch")
    else:
        st.info("Selecione um período maior que 1 dia para visualizar a evolução temporal. Use **Semana**, **Mês**, **Ano** ou **Intervalo de datas**.")
