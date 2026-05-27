import streamlit as st
import plotly.express as px
from utils.data_processor import identify_service_cards

def _create_top_bar_chart(df, x_col, y_col, color_scale, margin_r=110):
    n_items = len(df)
    labels, textpositions, textcolors, textsizes = [], [], [], []
    if n_items > 0:
        for i, v in enumerate(df[x_col]):
            formatted = f"{v:,}".replace(",", ".")
            if i == 0:
                labels.append(f"<b>{formatted}</b>")
            else:
                labels.append(formatted)
        textpositions = ['inside'] + ['outside'] * (n_items - 1)
        textcolors = ['#FFFFFF'] + ['#E0E0E0'] * (n_items - 1)
        textsizes = [13] + [11] * (n_items - 1)
        
    fig = px.bar(df, x=x_col, y=y_col, orientation='h', color=x_col, color_continuous_scale=color_scale, text=labels)
    fig.update_traces(
        texttemplate='%{text}',
        textposition=textpositions,
        textfont=dict(color=textcolors, size=textsizes),
        insidetextanchor='end'
    )
    fig.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(r=margin_r, t=20, b=20, l=20))
    return fig

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
            fig.update_traces(texttemplate='%{x:,.0f}', textposition='outside')
            fig.update_layout(
                yaxis={'categoryorder': 'total ascending'},
                separators=',.',
                margin=dict(r=110)
            )
            st.plotly_chart(fig, width="stretch")
            st.dataframe(df_show[['#', 'URL', 'Visitas']], hide_index=True, width="stretch")
        else:
            st.warning("Sem dados de telas para este período.")
        return

    st.header("Serviços Consumidos")
    st.markdown("Identificados cruzando as URLs acessadas com o **Inventário Oficial de Cartas de Serviços (Apenas Serviços Ativos)**.")

    if df_services is None:
        df_services = identify_service_cards(df_pages)
    
    if not df_services.empty:
        total_visitas = df_services['Visitas'].sum()
        total_servicos = df_services['Nome do Serviço'].nunique()
        
        orgao_top = "N/A"
        perc_digital = 0.0
        
        if 'Órgão' in df_services.columns:
            orgao_top = df_services.groupby('Órgão')['Visitas'].sum().idxmax()
            
        if 'Modalidade' in df_services.columns:
            visitas_digitais = df_services[df_services['Modalidade'] == 'Digital']['Visitas'].sum()
            if total_visitas > 0:
                perc_digital = (visitas_digitais / total_visitas) * 100
                
        st.info(f"💡 **Perfil de Consumo:** Neste período, os cidadãos acessaram **{total_servicos}** serviços ativos, somando **{total_visitas:,.0f}** visualizações. O órgão com maior volume de acessos foi **{orgao_top}**. Além disso, **{perc_digital:.1f}%** das visualizações foram direcionadas a serviços puramente **Digitais**.")
        st.markdown("---")
        
        if 'Modalidade' in df_services.columns and 'Órgão' in df_services.columns:
            col_mod, col_org = st.columns(2)
            with col_mod:
                st.subheader("Distribuição por Modalidade")
                df_mod = df_services.groupby('Modalidade', as_index=False)['Visitas'].sum()
                fig_mod = px.pie(df_mod, values='Visitas', names='Modalidade', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_mod.update_traces(textposition='inside', textinfo='percent+label')
                fig_mod.update_layout(margin=dict(t=20, b=20, l=20, r=20))
                st.plotly_chart(fig_mod, width='stretch')
                
            with col_org:
                st.subheader("Top Órgãos Mais Demandados")
                df_org = df_services.groupby('Órgão', as_index=False)['Visitas'].sum().sort_values(by='Visitas', ascending=False).head(10)
                fig_org = _create_top_bar_chart(df_org, 'Visitas', 'Órgão', 'Teal')
                st.plotly_chart(fig_org, width='stretch')
            
            st.markdown("---")

        df_cat = df_services.groupby('Categoria', as_index=False)['Visitas'].sum().sort_values(by='Visitas', ascending=False)
        
        col_cat, col_serv = st.columns(2)
        with col_cat:
            st.subheader("Top Categorias de Serviço (Geral)")
            st.markdown("Clique em uma barra para filtrar os serviços ao lado:")
            
            top_cat = df_cat.head(10)
            fig_cat = _create_top_bar_chart(top_cat, 'Visitas', 'Categoria', 'Oranges')
            fig_cat.update_layout(clickmode='event+select')
            
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
            
        col_filtros1, col_filtros2 = st.columns(2)
        with col_filtros1:
            categoria_selecionada = st.selectbox("🎯 Filtre Cartas por Categoria:", lista_categorias, index=idx)
            
        with col_filtros2:
            orgaos_selecionados = []
            if 'Órgão' in df_services.columns and 'Nome do Órgão' in df_services.columns:
                orgao_map = df_services.drop_duplicates('Órgão').set_index('Órgão')['Nome do Órgão'].to_dict()
                lista_orgaos = sorted(df_services['Órgão'].dropna().unique().tolist())
                
                def formata_orgao(sigla):
                    nome = orgao_map.get(sigla, "")
                    if sigla == "Não Identificado" or not nome or nome == "Não Identificado":
                        return sigla
                    return f"{nome} - {sigla}"

                orgaos_selecionados = st.multiselect(
                    "🏢 Filtre Cartas por Órgão:", 
                    options=lista_orgaos, 
                    default=[],
                    format_func=formata_orgao
                )
        
        df_filtered = df_services
        if categoria_selecionada != "Todas as Categorias":
            df_filtered = df_filtered[df_filtered['Categoria'] == categoria_selecionada]
        if orgaos_selecionados:
            df_filtered = df_filtered[df_filtered['Órgão'].isin(orgaos_selecionados)]
            
        with col_serv:
            st.subheader(f"Top 10 Cartas ({categoria_selecionada})")
            
            top_10 = df_filtered.head(10)
            fig_serv = _create_top_bar_chart(top_10, 'Visitas', 'Nome do Serviço', 'Blues')
            st.plotly_chart(fig_serv, width="stretch")

        st.subheader("Explorar Cartas (Links Diretos)")
        
        # Adiciona a coluna de ranking/classificação (#)
        cols_to_show = ['Nome do Serviço', 'Órgão', 'Categoria', 'Modalidade', 'Visitas', 'Link']
        cols_to_show = [c for c in cols_to_show if c in df_filtered.columns]
        
        df_table = df_filtered[cols_to_show].copy()
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
