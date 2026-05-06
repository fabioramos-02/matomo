import pandas as pd
import streamlit as st
import plotly.express as px

_EVENTOS_SISTEMA = {
    "first_open":      ("Novos Usuários",      "Abriram o app pela 1ª vez no período"),
    "session_start":   ("Sessões Iniciadas",   "Cada vez que o app foi aberto"),
    "screen_view":     ("Visualizações de Tela","Navegações entre telas do app"),
    "user_engagement": ("Interações",           "Toques e ações dentro do app (dispara ~a cada 10s de uso)"),
}


def _fmt(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}k"
    return str(n)


def render_ga_tab4_jornada(df_funnel):
    st.header("Jornada do Usuário — MS Digital App")

    if df_funnel is None or df_funnel.empty:
        st.warning("Sem dados de eventos para o período selecionado.")
        return

    sistema_mask = df_funnel["Evento"].isin(_EVENTOS_SISTEMA.keys())
    df_sistema = df_funnel[sistema_mask].copy()
    df_custom = df_funnel[~sistema_mask].copy()

    # ── KPIs de volume ────────────────────────────────────────────────────────
    st.subheader("📊 Resumo de Atividade no Período")

    kpi_map = {k: {"label": v[0], "desc": v[1]} for k, v in _EVENTOS_SISTEMA.items()}
    row = df_sistema.set_index("Evento")

    col1, col2, col3, col4 = st.columns(4)
    cols = [col1, col2, col3, col4]
    for i, (evt, info) in enumerate(kpi_map.items()):
        val = int(row.loc[evt, "Usuários"]) if evt in row.index and "Usuários" in row.columns else 0
        evt_count = int(row.loc[evt, "Ocorrências"]) if evt in row.index else 0
        with cols[i]:
            st.metric(label=info["label"], value=_fmt(val if val > 0 else evt_count))
            st.caption(info["desc"])

    st.markdown("---")

    # ── Contexto para a gestora ───────────────────────────────────────────────
    first_open_val = int(row.loc["first_open", "Usuários"]) if "first_open" in row.index and "Usuários" in row.columns else int(row.loc["first_open", "Ocorrências"]) if "first_open" in row.index else 0
    session_val = int(row.loc["session_start", "Ocorrências"]) if "session_start" in row.index else 0
    engagement_val = int(row.loc["user_engagement", "Ocorrências"]) if "user_engagement" in row.index else 0

    if first_open_val > 0 and session_val > 0:
        sessoes_por_novo = round(session_val / first_open_val, 1)
        st.info(
            f"**Leitura:** No período, **{_fmt(first_open_val)} novos usuários** abriram o MS Digital pela primeira vez. "
            f"No total foram **{_fmt(session_val)} sessões** abertas — média de **{sessoes_por_novo} sessões por novo usuário**, "
            f"indicando que usuários retornam ao app após o primeiro acesso. "
            f"As **{_fmt(engagement_val)} interações** refletem o uso ativo dentro de cada sessão "
            f"(esse contador dispara automaticamente a cada ~10 segundos de uso contínuo)."
        )

    st.markdown("---")

    # ── Funil de Engajamento — Storytelling ──────────────────────────────────
    st.subheader("📊 Funil de Engajamento")
    st.markdown("""
    Este funil responde: **"O cidadão que abre o app, realmente o utiliza?"**. 
    Diferente de contagem de cliques, aqui olhamos para **Usuários Únicos** para entender a retenção.
    """)

    if not df_sistema.empty and "Usuários" in df_sistema.columns:
        # Ordem lógica sugerida pela gestão:
        # 1. Novos Downloads (Primeira abertura)
        # 2. Entrada (Sessão iniciada)
        # 3. Navegação (Visualização de telas)
        # 4. Engajamento (Interação ativa)
        ordem_funil = ["first_open", "session_start", "screen_view", "user_engagement"]
        
        df_funnel_plot = (
            df_sistema[df_sistema["Evento"].isin(ordem_funil)]
            .set_index("Evento")
            .reindex(ordem_funil)
            .dropna()
            .reset_index()
        )
        
        label_funil = {
            "first_open":      "1. Aquisição (Downloads)",
            "session_start":   "2. Ativação (Sessão)",
            "screen_view":     "3. Navegação (Telas)",
            "user_engagement": "4. Retenção (Engajamento)"
        }
        
        df_funnel_plot["Etapa"] = df_funnel_plot["Evento"].map(label_funil)
        df_funnel_plot["Usuários"] = pd.to_numeric(df_funnel_plot["Usuários"], errors="coerce").fillna(0).astype(int)

        fig_funnel = px.funnel(
            df_funnel_plot,
            x="Usuários",
            y="Etapa",
            color_discrete_sequence=["#1f77b4"]
        )
        fig_funnel.update_layout(margin=dict(t=20, b=20, l=100, r=20), showlegend=False)
        st.plotly_chart(fig_funnel, width="stretch")

        # ── O Storytelling (Para a chefe) ─────────────────────────────────────
        with st.expander("💡 Como explicar estes dados para a gestão?", expanded=True):
            st.markdown(f"""
            *   **Aquisição (Downloads):** Temos **{_fmt(df_funnel_plot.iloc[0]['Usuários'])}** novos usuários que baixaram e abriram o app pela primeira vez. 
            *   **Ativação (Sessão):** Total de **{_fmt(df_funnel_plot.iloc[1]['Usuários'])}** usuários únicos geraram sessões no período (inclui novos e antigos).
            *   **Navegação (Telas):** Dos que ativaram, **{df_funnel_plot.iloc[2]['Usuários'] / df_funnel_plot.iloc[1]['Usuários']:.1%}** progrediram para ver ao menos uma funcionalidade.
            *   **Retenção (Engajamento):** Representa o público fiel. Temos **{_fmt(df_funnel_plot.iloc[3]['Usuários'])}** usuários que interagiram de forma contínua com o app.
            """)

        # ── Funil de Abandono (Churn) ──────────────────────────────────────────
        st.markdown("---")
        st.subheader("📉 Funil de Abandono (Churn)")
        st.markdown("Identifica em qual etapa os usuários estão deixando o aplicativo.")
        
        abandon_data = []
        for i in range(len(df_funnel_plot) - 1):
            atual = df_funnel_plot.iloc[i]
            proximo = df_funnel_plot.iloc[i+1]
            perda = atual["Usuários"] - proximo["Usuários"]
            taxa_abandono = (perda / atual["Usuários"] * 100) if atual["Usuários"] > 0 else 0
            abandon_data.append({
                "Etapa": f"{atual['Etapa']} → {proximo['Etapa']}",
                "Abandono (%)": round(taxa_abandono, 1),
                "Usuários Perdidos": perda
            })
        
        df_abandon = pd.DataFrame(abandon_data)
        fig_abandon = px.bar(
            df_abandon, x="Etapa", y="Abandono (%)", 
            text="Abandono (%)", color="Abandono (%)",
            color_continuous_scale="Reds"
        )
        fig_abandon.update_traces(texttemplate='%{text}%', textposition='outside')
        fig_abandon.update_layout(yaxis_ticksuffix="%", coloraxis_showscale=False)
        st.plotly_chart(fig_abandon, width="stretch")

        # ── Storytelling do Churn (Para a chefe) ──────────────────────────────
        with st.expander("💡 Onde estamos perdendo mais usuários?", expanded=True):
            # Identifica o maior gargalo
            maior_perda = df_abandon.sort_values("Abandono (%)", ascending=False).iloc[0]
            
            st.markdown(f"""
            O ponto crítico de abandono hoje é na transição **{maior_perda['Etapa']}**, onde perdemos **{maior_perda['Abandono (%)']}%** dos usuários (**{_fmt(maior_perda['Usuários Perdidos'])} pessoas**).
            
            *   **Interpretando o número:** 
                *   Se a maior perda é em **Aquisição → Ativação**: Indica que as pessoas baixam o app mas não chegam a abrir ou logar (possível problema técnico no login ou tamanho do app).
                *   Se a maior perda é em **Ativação → Navegação**: O usuário abre o app mas não encontra o que precisa ou acha a interface confusa.
                *   Se a maior perda é em **Navegação → Engajamento**: O usuário usa o app pontualmente mas não cria o hábito de retorno.
            """)
    else:
        st.info("Dados de usuários únicos não disponíveis para gerar o funil.")

    st.markdown("---")

    # ── Eventos customizados (ações reais do usuário) ─────────────────────────
    st.subheader("⚡ Ações Realizadas pelos Usuários")
    st.caption(
        "Eventos disparados pelo próprio usuário ao interagir com funcionalidades do app. "
        "Diferente dos eventos automáticos acima — estes refletem intenção real."
    )

    if not df_custom.empty:
        col_chart, col_table = st.columns([1.3, 1])

        with col_chart:
            fig_ev = px.bar(
                df_custom.head(10),
                x="Ocorrências", y="Evento", orientation="h",
                color="Ocorrências", color_continuous_scale="Purples",
            )
            fig_ev.update_layout(
                yaxis={"categoryorder": "total ascending"},
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig_ev, width="stretch")

        with col_table:
            df_show = df_custom.head(15).copy()
            df_show.insert(0, "#", df_show.index + 1)
            cols_show = ["#", "Evento", "Ocorrências"]
            if "Usuários" in df_show.columns:
                cols_show.append("Usuários")
            st.dataframe(df_show[cols_show], hide_index=True, width="stretch")
    else:
        st.info("Sem eventos customizados no período.")
