import json
import os
import unicodedata

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import date as dt_date


_MESES_PT = {
    1: "JAN", 2: "FEV", 3: "MAR", 4: "ABR", 5: "MAI", 6: "JUN",
    7: "JUL", 8: "AGO", 9: "SET", 10: "OUT", 11: "NOV", 12: "DEZ",
}


def _months_in_range(start_date: str | None, end_date: str | None) -> float:
    if not start_date or not end_date:
        return 1.0
    try:
        s = dt_date.fromisoformat(start_date)
        e = dt_date.fromisoformat(end_date)
    except (TypeError, ValueError):
        return 1.0
    days = max((e - s).days + 1, 1)
    return max(days / 30.44, 1.0)


def _period_badge(start_date: str | None, end_date: str | None) -> str:
    try:
        s = dt_date.fromisoformat(start_date)
        e = dt_date.fromisoformat(end_date)
    except (TypeError, ValueError):
        return "PERÍODO SELECIONADO"
    if s.year == e.year and s.month == e.month:
        return f"{_MESES_PT[s.month]}/{s.year}"
    return f"{_MESES_PT[s.month]}/{s.year} → {_MESES_PT[e.month]}/{e.year}"


def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)).lower().strip()


@st.cache_data(ttl=86400)
def _load_ms_city_coords() -> dict:
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    mun_path = os.path.join(base, "data", "municipios.json")
    est_path = os.path.join(base, "data", "estados.json")
    try:
        with open(mun_path, "rb") as f:
            raw = f.read()
            if raw.startswith(b"\xef\xbb\xbf"):
                raw = raw[3:]
            municipios = json.loads(raw.decode("utf-8"))
        with open(est_path, "rb") as f:
            raw = f.read()
            if raw.startswith(b"\xef\xbb\xbf"):
                raw = raw[3:]
            estados = json.loads(raw.decode("utf-8"))
    except Exception:
        return {}
    ms_codes = {e["codigo_uf"] for e in estados if e.get("uf") == "MS"}
    return {
        _strip_accents(m["nome"]): (m["latitude"], m["longitude"])
        for m in municipios
        if m.get("codigo_uf") in ms_codes
    }


def _render_ranking_card(df_top: pd.DataFrame, badge: str):
    st.markdown(
        """
        <style>
        .geo-card { background:#fff; border:1px solid #E5E9F0; border-radius:12px; padding:18px 18px 8px; box-shadow:0 2px 6px rgba(15,23,42,0.06); }
        .geo-card h3 { margin:0; color:#0F3057; font-size:18px; letter-spacing:0.4px; font-weight:800; }
        .geo-card .geo-sub { color:#5B6B84; font-size:13px; margin-bottom:10px; }
        .geo-badge { display:inline-block; background:#DCE7F5; color:#0F3057; font-weight:700; padding:4px 14px; border-radius:6px; font-size:12.5px; letter-spacing:0.6px; margin-bottom:12px; }
        .geo-table { width:100%; border-collapse:collapse; font-size:13px; }
        .geo-table thead th { background:#0F3057; color:#fff; text-align:left; padding:8px 10px; font-weight:700; font-size:11.5px; letter-spacing:0.5px; }
        .geo-table td { padding:6px 10px; border-bottom:1px solid #F0F2F6; color:#111827; }
        .geo-table tr:last-child td { border-bottom:none; }
        .geo-table tr:nth-child(even) td { background:#F7FAFF; }
        .geo-pos { display:inline-flex; align-items:center; justify-content:center; width:22px; height:22px; border-radius:50%; background:#1E5BA8; color:#fff; font-size:11px; font-weight:700; }
        .geo-vol { color:#0A2540; font-weight:800; text-align:right; font-variant-numeric:tabular-nums; font-size:13.5px; }
        .geo-foot { color:#9AA5B8; font-size:10.5px; margin-top:8px; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    rows_html = "".join(
        f"<tr><td><span class='geo-pos'>{i+1}</span></td>"
        f"<td>{row['Cidade']}</td>"
        f"<td class='geo-vol'>{int(row['Visitas']):,}</td></tr>".replace(",", ".")
        for i, row in df_top.reset_index(drop=True).iterrows()
    )
    st.markdown(
        f"""
        <div class="geo-card">
          <h3>🗺️ DISTRIBUIÇÃO GEOGRÁFICA</h3>
          <div class="geo-sub">Volume de Acessos</div>
          <div class="geo-badge">{badge}</div>
          <table class="geo-table">
            <thead><tr><th>POS.</th><th>CIDADE</th><th style="text-align:right;">VOLUME DE ACESSOS</th></tr></thead>
            <tbody>{rows_html}</tbody>
          </table>
          <div class="geo-foot">* Dados referentes ao volume total de acessos.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_pin_map(df_top: pd.DataFrame, ms_geojson):
    coords = _load_ms_city_coords()
    df = df_top.copy()
    df["_key"] = df["Cidade"].astype(str).map(_strip_accents)
    df["lat"] = df["_key"].map(lambda k: coords.get(k, (None, None))[0])
    df["lon"] = df["_key"].map(lambda k: coords.get(k, (None, None))[1])
    df = df.dropna(subset=["lat", "lon"])
    if df.empty:
        st.info("Coordenadas indisponíveis para as cidades no período.")
        return
    df["cidade_label"] = df["Cidade"]
    df["valor_label"] = df["Visitas"].astype(int).map(lambda v: f"{v:,}".replace(",", "."))

    fig = go.Figure()
    if ms_geojson:
        feats = [f for f in ms_geojson.get("features", []) if f.get("properties", {}).get("name")]
        fig.add_trace(
            go.Choroplethmapbox(
                geojson=ms_geojson,
                locations=[f["properties"]["name"] for f in feats],
                z=[1] * len(feats),
                featureidkey="properties.name",
                colorscale=[[0, "#EEF3FB"], [1, "#DCE7F5"]],
                showscale=False,
                marker_line_color="#7B9BC6",
                marker_line_width=0.9,
                hoverinfo="skip",
            )
        )

    fig.add_trace(
        go.Scattermapbox(
            lat=df["lat"],
            lon=df["lon"],
            mode="markers",
            marker=dict(size=13, color="#0A2540"),
            hoverinfo="text",
            hovertext=df.apply(
                lambda r: f"<b>{r['Cidade']}</b><br>Visitas: {int(r['Visitas']):,}".replace(",", "."), axis=1
            ),
            name="Cidades",
        )
    )
    fig.add_trace(
        go.Scattermapbox(
            lat=df["lat"],
            lon=df["lon"],
            mode="text",
            text=df["cidade_label"],
            textposition="top center",
            textfont=dict(size=11, color="#0A2540", family="Arial Black"),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scattermapbox(
            lat=df["lat"],
            lon=df["lon"],
            mode="text",
            text=df["valor_label"],
            textposition="bottom center",
            textfont=dict(size=13, color="#08111F", family="Arial Black"),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            center=dict(lat=-20.5, lon=-54.6),
            zoom=5.25,
        ),
        margin=dict(l=0, r=0, t=32, b=0),
        showlegend=False,
        height=560,
        paper_bgcolor="#FFFFFF",
        title=dict(text="<b>VOLUME DE ACESSOS</b>", x=0.5, xanchor="center", font=dict(color="#0F3057", size=14)),
    )
    st.plotly_chart(fig, width="stretch")


def render_tab1_perfil(df_cities, df_browsers, df_device_types, df_time, ms_geojson, visits_summary=None, fonte="Portal (Matomo)", start_date=None, end_date=None):
    st.header("Perfil do Cidadão")
    st.markdown("Quem são, de onde vêm, com qual dispositivo e em qual horário acessam.")

    if visits_summary:
        nb_visits = visits_summary.get("nb_visits", 0)
        col_metric = st.columns(3)[0]
        col_metric.metric("Total de Acessos", f"{nb_visits:,}".replace(",", "."))
        st.caption("ℹ️ Valor total de acessos globais (independente de região ou estado).")

    n_meses = _months_in_range(start_date, end_date)
    badge = _period_badge(start_date, end_date)

    if not df_cities.empty:
        df_cities_view = df_cities[df_cities['Cidade'] != 'Unknown'].copy()
        if 'Visitas' in df_cities_view.columns:
            df_cities_view['Média Mensal'] = (df_cities_view['Visitas'] / n_meses).round(1)

        df_top20 = df_cities_view.head(20).reset_index(drop=True)

        col_card, col_map = st.columns([0.42, 0.58], gap="small")
        with col_card:
            _render_ranking_card(df_top20, badge)
        with col_map:
            _render_pin_map(df_top20, ms_geojson)

        st.caption(
            f"📅 Período: **{start_date or '—'} → {end_date or '—'}** "
            f"(~**{n_meses:.1f} meses**) · Média mensal = Visitas ÷ meses do período. "
            f"Para recortar por ano (ex.: 2025), use **Período = Ano** ou **Intervalo de datas** na barra lateral."
        )

        with st.expander("📋 Tabela completa (todas as cidades + média mensal)"):
            st.dataframe(
                df_cities_view,
                column_config={
                    "Visitas": st.column_config.NumberColumn("Visitas", format="%d"),
                    "Média Mensal": st.column_config.NumberColumn("Média Mensal", format="%.1f"),
                },
                hide_index=True,
                width="stretch",
            )
    else:
        st.info("Nenhum dado de cidade encontrado para o MS no período.")
        
    st.markdown("---")
    
    st.subheader("⏰ Picos de Acesso por Horário")
    if not df_time.empty:
        fig_time = px.bar(df_time, x='Hora', y='Visitas', color_discrete_sequence=['#ff7f0e'])
        fig_time.update_xaxes(dtick=1) # Força a exibição de todos os ticks de hora
        st.plotly_chart(fig_time, width="stretch")
    else:
        st.info("Sem dados de horário disponíveis.")
        
    st.markdown("---")
    
    st.subheader("💻 Dispositivos e Navegadores")
    col_b, col_t = st.columns(2)
    
    with col_b:
        if not df_browsers.empty:
            label_browsers = "Sistema Operacional" if fonte == "MS Digital (GA4)" else "Navegadores Mais Utilizados"
            st.markdown(f"**{label_browsers}**")
            # Usa paleta qualitativa vibrante (melhor para categorias independentes)
            fig_b = px.pie(df_browsers, values='Visitas', names='Navegador', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_b.update_traces(textposition='inside', textinfo='percent')
            fig_b.update_layout(
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
                margin=dict(t=20, b=40, l=20, r=20)
            )
            st.plotly_chart(fig_b, width="stretch")
            
    with col_t:
        if not df_device_types.empty:
            st.markdown("**Tipos de Dispositivo**")
            # Usa paleta qualitativa vibrante 
            fig_d = px.pie(df_device_types, values='Visitas', names='Dispositivo', hole=0.5, color_discrete_sequence=px.colors.qualitative.Set2)
            fig_d.update_traces(textposition='inside', textinfo='percent')
            fig_d.update_layout(
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
                margin=dict(t=20, b=40, l=20, r=20)
            )
            st.plotly_chart(fig_d, width="stretch")
