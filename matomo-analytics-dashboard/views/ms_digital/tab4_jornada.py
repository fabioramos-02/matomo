import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


# Eventos de sistema que marcam pontos fixos da jornada
_EVENTOS_SISTEMA = {
    "first_open": "1. Primeira Abertura",
    "session_start": "2. Início de Sessão",
    "screen_view": "3. Visualização de Tela",
    "user_engagement": "4. Engajamento",
}


def render_ga_tab4_jornada(df_funnel):
    st.header("Jornada do Usuário — MS Digital App")
    st.markdown(
        "Análise do comportamento sequencial no app. "
        "O funil mostra o volume de cada etapa — a queda entre eventos revela onde os usuários abandonam a ação."
    )

    if df_funnel is None or df_funnel.empty:
        st.warning("Sem dados de eventos para construir a jornada no período selecionado.")
        return

    # Separar eventos de sistema (contexto) dos customizados (ações reais)
    sistema_mask = df_funnel["Evento"].isin(_EVENTOS_SISTEMA.keys())
    df_sistema = df_funnel[sistema_mask].copy()
    df_custom = df_funnel[~sistema_mask].copy()

    # ── Funil de sistema ──────────────────────────────────────────────────
    st.subheader("📊 Funil de Engajamento")
    st.caption("Mostra quantos usuários chegam em cada etapa fundamental do app.")

    if not df_sistema.empty:
        df_sistema["Etapa"] = df_sistema["Evento"].map(_EVENTOS_SISTEMA).fillna(df_sistema["Evento"])
        df_sistema = df_sistema.sort_values("Ocorrências", ascending=False)

        fig_funil = go.Figure(go.Funnel(
            y=df_sistema["Etapa"],
            x=df_sistema["Ocorrências"],
            textinfo="value+percent initial",
            marker={"color": ["#0077b6", "#00b4d8", "#90e0ef", "#caf0f8"][:len(df_sistema)]},
        ))
        fig_funil.update_layout(margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_funil, use_container_width=True)
    else:
        st.info("Eventos de sistema (first_open, session_start) não encontrados nos dados.")

    st.markdown("---")

    # ── Ações mais realizadas ─────────────────────────────────────────────
    st.subheader("⚡ Ações Mais Realizadas (Eventos Customizados)")
    st.caption("Eventos disparados pela interação do usuário com funcionalidades do app.")

    if not df_custom.empty:
        col_chart, col_table = st.columns([1.3, 1])

        with col_chart:
            fig_ev = px.bar(
                df_custom.head(15),
                x="Ocorrências", y="Evento", orientation="h",
                color="Ocorrências", color_continuous_scale="Purples",
            )
            fig_ev.update_layout(
                yaxis={"categoryorder": "total ascending"},
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig_ev, use_container_width=True)

        with col_table:
            df_show = df_custom.head(20).copy()
            df_show.insert(0, "#", df_show.index + 1)
            cols = ["#", "Evento", "Ocorrências"]
            if "Usuários" in df_show.columns:
                cols.append("Usuários")
            st.dataframe(df_show[cols], hide_index=True, use_container_width=True)
    else:
        st.info("Sem eventos customizados encontrados. Verifique se o app envia eventos personalizados ao GA4.")

    st.markdown("---")
    st.info(
        "💡 Para análise de funil personalizada (ex: tela A → tela B → conversão), "
        "acesse o GA4 diretamente em **Exploração → Análise de funil**."
    )
