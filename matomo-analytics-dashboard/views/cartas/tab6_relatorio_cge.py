"""
Aba 6 — Relatório CGE
Consolida métricas de erros (Seção 2) e satisfação (Seção 3) com export XLSX e PDF.
"""
from __future__ import annotations

import io
from datetime import date

import pandas as pd
import streamlit as st


# ------------------------------------------------------------------ #
# SVG / metadados reutilizados de tab4_satisfacao                     #
# ------------------------------------------------------------------ #
_SVG_PATHS = {
    1: "M10 0C8.68678 0 7.38642 0.258658 6.17317 0.761205C4.95991 1.26375 3.85752 2.00035 2.92893 2.92893C1.05357 4.8043 0 7.34784 0 10C0 12.6522 1.05357 15.1957 2.92893 17.0711C3.85752 17.9997 4.95991 18.7362 6.17317 19.2388C7.38642 19.7413 8.68678 20 10 20C12.6522 20 15.1957 18.9464 17.0711 17.0711C18.9464 15.1957 20 12.6522 20 10C20 8.68678 19.7413 7.38642 19.2388 6.17317C18.7362 4.95991 17.9997 3.85752 17.0711 2.92893C16.1425 2.00035 15.0401 1.26375 13.8268 0.761205C12.6136 0.258658 11.3132 0 10 0ZM5 7.5V6L8 7.5C8 8.3 7.3 9 6.5 9C5.7 9 5 8.3 5 7.5ZM12.77 15.23C12.32 14.5 11.25 14 10 14C8.75 14 7.68 14.5 7.23 15.23L5.81 13.81C6.71 12.72 8.25 12 10 12C11.75 12 13.29 12.72 14.19 13.81L12.77 15.23ZM15 7.5C15 8.3 14.3 9 13.5 9C12.7 9 12 7.5L15 6V7.5Z",
    2: "M10 0C8.68678 0 7.38642 0.258658 6.17317 0.761205C4.95991 1.26375 3.85752 2.00035 2.92893 2.92893C1.05357 4.8043 0 7.34784 0 10C0 12.6522 1.05357 15.1957 2.92893 17.0711C3.85752 17.9997 4.95991 18.7362 6.17317 19.2388C7.38642 19.7413 8.68678 20 10 20C12.6522 20 15.1957 18.9464 17.0711 17.0711C18.9464 15.1957 20 12.6522 20 10C20 8.68678 19.7413 7.38642 19.2388 6.17317C18.7362 4.95991 17.9997 3.85752 17.0711 2.92893C16.1425 2.00035 15.0401 1.26375 13.8268 0.761205C12.6136 0.258658 11.3132 0 10 0ZM5 7.5C5 6.7 5.7 6 6.5 6C7.3 6 8 6.7 8 7.5C8 8.3 7.3 9 6.5 9C5.7 9 5 8.3 5 7.5ZM12.77 15.23C12.32 14.5 11.25 14 10 14C8.75 14 7.68 14.5 7.23 15.23L5.81 13.81C6.71 12.72 8.25 12 10 12C11.75 12 13.29 12.72 14.19 13.81L12.77 15.23ZM13.5 9C12.7 9 12 8.3 12 7.5C12 6.7 12.7 6 13.5 6C14.3 6 15 6.7 15 7.5C15 8.3 14.3 9 13.5 9Z",
    3: "M10 0C8.68678 0 7.38642 0.258658 6.17317 0.761205C4.95991 1.26375 3.85752 2.00035 2.92893 2.92893C1.05357 4.8043 0 7.34784 0 10C0 12.6522 1.05357 15.1957 2.92893 17.0711C3.85752 17.9997 4.95991 18.7362 6.17317 19.2388C7.38642 19.7413 8.68678 20 10 20C12.6522 20 15.1957 18.9464 17.0711 17.0711C18.9464 15.1957 20 12.6522 20 10C20 8.68678 19.7413 7.38642 19.2388 6.17317C18.7362 4.95991 17.9997 3.85752 17.0711 2.92893C16.1425 2.00035 15.0401 1.26375 13.8268 0.761205C12.6136 0.258658 11.3132 0 10 0M5 7.5C5 7.10218 5.15804 6.72064 5.43934 6.43934C5.72064 6.15804 6.10218 6 6.5 6C6.89782 6 7.27936 6.15804 7.56066 6.43934C7.84196 6.72064 8 7.10218 8 7.5C8 7.89782 7.84196 8.27936 7.56066 8.56066C7.27936 8.84196 6.89782 9 6.5 9C6.10218 9 5.72064 8.84196 5.43934 8.56066C5.15804 8.27936 5 7.89782 5 7.5ZM14 14H6V12H14V14ZM13.5 9C13.1022 9 12.7206 8.84196 12.4393 8.56066C12.158 8.27936 12 7.89782 12 7.5C12 7.10218 12.158 6.72064 12.4393 6.43934C12.7206 6.15804 13.1022 6 13.5 6C13.8978 6 14.2794 6.15804 14.5607 6.43934C14.842 6.72064 15 7.10218 15 7.5C15 7.89782 14.842 8.27936 14.5607 8.56066C14.2794 8.84196 13.8978 9 13.5 9V9Z",
    4: "M10 0C8.68678 0 7.38642 0.258658 6.17317 0.761205C4.95991 1.26375 3.85752 2.00035 2.92893 2.92893C1.05357 4.8043 0 7.34784 0 10C0 12.6522 1.05357 15.1957 2.92893 17.0711C3.85752 17.9997 4.95991 18.7362 6.17317 19.2388C7.38642 19.7413 8.68678 20 10 20C12.6522 20 15.1957 18.9464 17.0711 17.0711C18.9464 15.1957 20 12.6522 20 10C20 8.68678 19.7413 7.38642 19.2388 6.17317C18.7362 4.95991 17.9997 3.85752 17.0711 2.92893C16.1425 2.00035 15.0401 1.26375 13.8268 0.761205C12.6136 0.258658 11.3132 0 10 0ZM5 7.5C5 6.7 5.7 6 6.5 6C7.3 6 8 6.7 8 7.5C8 8.3 7.3 9 6.5 9C5.7 9 5 8.3 5 7.5ZM10 15.23C8.25 15.23 6.71 14.5 5.81 13.42L7.23 12C7.68 12.72 8.75 13.23 10 13.23C11.25 13.23 12.32 12.72 12.77 12L14.19 13.42C13.29 14.5 11.75 15.23 10 15.23ZM13.5 9C12.7 9 12 8.3 12 7.5C12 6.7 12.7 6 13.5 6C14.3 6 15 6.7 15 7.5C15 8.3 14.3 9 13.5 9Z",
    5: "M10 0C4.47 0 0 4.47 0 10C0 15.53 4.47 20 10 20C12.6522 20 15.1957 18.9464 17.0711 17.0711C18.9464 15.1957 20 12.6522 20 10C20 4.47 15.5 0 10 0ZM6.88 5.82L9 7.94L7.94 9L6.88 7.94L5.82 9L4.76 7.94L6.88 5.82ZM10 15.5C7.67 15.5 5.69 14.04 4.89 12H15.11C14.31 14.04 12.33 15.5 10 15.5ZM14.18 9L13.12 7.94L12.06 9L11 7.94L13.12 5.82L15.24 7.94L14.18 9Z",
}

_RATING_META = [
    (1, "MUITO INSATISFEITO", "#EF4444"),
    (2, "INSATISFEITO",       "#F97316"),
    (3, "REGULAR",            "#F59E0B"),
    (4, "SATISFEITO",         "#4ADE80"),
    (5, "MUITO SATISFEITO",   "#22C55E"),
]


# ------------------------------------------------------------------ #
# Helpers internos                                                     #
# ------------------------------------------------------------------ #

def _render_satisfaction_icons(df: pd.DataFrame, total_votos: int) -> None:
    counts = df["avaliacao_voto_servico"].value_counts()
    items_html = ""
    for nota, label, cor in _RATING_META:
        n = int(counts.get(nota, 0))
        pct = (n / total_votos * 100) if total_votos else 0
        svg_path = _SVG_PATHS[nota]
        items_html += f"""
        <div style="text-align:center; min-width:100px; flex:1;">
          <div style="width:64px; height:64px; border-radius:50%; background:{cor};
                      display:flex; align-items:center; justify-content:center; margin:0 auto;">
            <svg focusable="false" viewBox="0 0 20 20" aria-hidden="true" fill="none"
                 style="width:32px; height:32px;">
              <path d="{svg_path}" fill="white"/>
            </svg>
          </div>
          <p style="font-size:11px; font-weight:700; letter-spacing:.4px;
                    margin:8px 0 2px; color:#374151; line-height:1.3;">{label}</p>
          <p style="font-size:20px; font-weight:800; margin:0; color:#111827;">{n}</p>
          <p style="font-size:13px; color:#6B7280; margin:2px 0 0;">{pct:.1f}%</p>
        </div>"""
    st.markdown(
        f"""
        <div style="display:flex; justify-content:center; align-items:flex-start;
                    gap:12px; flex-wrap:wrap; padding:20px 8px 8px; margin-bottom:4px;">
          {items_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _build_df_sat_por_servico(df_votes: pd.DataFrame) -> pd.DataFrame:
    if df_votes.empty or "titulo_servico" not in df_votes.columns:
        return pd.DataFrame()
    grp = (
        df_votes.groupby("titulo_servico")
        .agg(
            total_votos=("avaliacao_voto_servico", "count"),
            nota_media=("avaliacao_voto_servico", "mean"),
            soma_notas=("avaliacao_voto_servico", "sum"),
        )
        .reset_index()
    )
    grp["csat_pct"] = (grp["soma_notas"] / (grp["total_votos"] * 5) * 100).round(1)
    grp["nota_media"] = grp["nota_media"].round(2)

    # Contagem por nota (1-5) para cada serviço
    pivot = (
        df_votes.groupby(["titulo_servico", "avaliacao_voto_servico"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=[1, 2, 3, 4, 5], fill_value=0)
        .reset_index()
    )
    pivot.columns = ["titulo_servico", "n1", "n2", "n3", "n4", "n5"]
    grp = grp.merge(pivot, on="titulo_servico", how="left")
    for c in ["n1", "n2", "n3", "n4", "n5"]:
        grp[c] = grp[c].fillna(0).astype(int)

    return grp.sort_values("csat_pct", ascending=False).reset_index(drop=True)


def _build_df_erros_por_orgao(df_errors: pd.DataFrame) -> pd.DataFrame:
    if df_errors.empty or "siglaorgao" not in df_errors.columns:
        return pd.DataFrame()
    for col in ["atendido", "corrigido_erro"]:
        if col in df_errors.columns:
            df_errors[col] = df_errors[col].astype(bool)
    grp = (
        df_errors.groupby("siglaorgao")
        .agg(
            Total=("iderroservico", "count"),
            Atendidos=("atendido", "sum"),
            Corrigidos=("corrigido_erro", "sum"),
        )
        .reset_index()
    )
    grp["Pendentes"] = grp["Total"] - grp["Atendidos"]
    return grp.sort_values("Total", ascending=False).reset_index(drop=True)


# ------------------------------------------------------------------ #
# Export XLSX                                                          #
# ------------------------------------------------------------------ #

def _export_xlsx(df_errors: pd.DataFrame, df_votes: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    # openpyxl não suporta datetime com timezone — remover tz antes de escrever
    df_errors = df_errors.copy()
    for col in df_errors.select_dtypes(include=["datetimetz"]).columns:
        df_errors[col] = df_errors[col].dt.tz_localize(None)

    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        # Aba Erros
        if not df_errors.empty:
            cols_erros = [c for c in [
                "siglaorgao", "titulo_servico", "conteudo",
                "atendido", "corrigido_erro", "resolucao_erro",
                "data_criacao_erro", "data_atualizacao_erro",
            ] if c in df_errors.columns]
            rename_erros = {
                "siglaorgao": "Órgão",
                "titulo_servico": "Serviço",
                "conteudo": "Tipo de Erro",
                "atendido": "Atendido",
                "corrigido_erro": "Corrigido",
                "resolucao_erro": "Resolução",
                "data_criacao_erro": "Data Abertura",
                "data_atualizacao_erro": "Última Atualização",
            }
            df_errors[cols_erros].rename(columns=rename_erros).to_excel(
                writer, sheet_name="Erros", index=False
            )
        # Aba Satisfação
        df_sat = _build_df_sat_por_servico(df_votes)
        if not df_sat.empty:
            df_sat.rename(columns={
                "titulo_servico": "Serviço",
                "total_votos": "Total Votos",
                "nota_media": "Nota Média",
                "soma_notas": "Soma Notas",
                "csat_pct": "CSAT (%)",
            }).drop(columns=["Soma Notas"], errors="ignore").to_excel(
                writer, sheet_name="Satisfação", index=False
            )
    return buf.getvalue()


# ------------------------------------------------------------------ #
# Export PDF                                                           #
# ------------------------------------------------------------------ #

def _p(text: str) -> str:
    """Converte string para Latin-1 seguro (fontes built-in do fpdf2 são Latin-1)."""
    import unicodedata
    # normaliza combinados (é → e + combining) depois codifica/decodifica com replace
    nfkd = unicodedata.normalize("NFKD", str(text))
    return nfkd.encode("latin-1", errors="replace").decode("latin-1")


def _export_pdf(
    df_errors: pd.DataFrame,
    df_votes: pd.DataFrame,
    total_erros: int,
    atendidos: int,
    pendentes: int,
    total_votos: int,
    csat: float,
    nota_media: float,
) -> bytes:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Cabeçalho
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, _p("Relatorio CGE - Cartas de Servico"), ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, _p(f"Gerado em: {date.today().strftime('%d/%m/%Y')}"), ln=True, align="C")
    pdf.ln(6)

    # Secao 2 — Erros
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_fill_color(36, 64, 97)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, _p("Secao 2 - Atualizacao das Cartas de Servicos"), ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(60, 7, _p(f"Total de Erros: {total_erros}"), border=1)
    pdf.cell(65, 7, _p(f"Atendidos: {atendidos} ({atendidos/total_erros*100:.0f}%)" if total_erros else "Atendidos: 0"), border=1)
    pdf.cell(65, 7, _p(f"Pendentes: {pendentes} ({pendentes/total_erros*100:.0f}%)" if total_erros else "Pendentes: 0"), border=1)
    pdf.ln(10)

    # Tabela de erros por orgao
    df_org = _build_df_erros_por_orgao(df_errors)
    if not df_org.empty:
        pdf.set_font("Helvetica", "B", 10)
        col_w = [40, 30, 30, 30, 30]
        headers = ["Orgao", "Total", "Atendidos", "Corrigidos", "Pendentes"]
        pdf.set_fill_color(220, 230, 241)
        for h, w in zip(headers, col_w):
            pdf.cell(w, 7, _p(h), border=1, fill=True)
        pdf.ln()
        pdf.set_font("Helvetica", "", 9)
        for _, row in df_org.iterrows():
            vals = [
                str(row.get("siglaorgao", "")),
                str(int(row.get("Total", 0))),
                str(int(row.get("Atendidos", 0))),
                str(int(row.get("Corrigidos", 0))),
                str(int(row.get("Pendentes", 0))),
            ]
            for v, w in zip(vals, col_w):
                pdf.cell(w, 6, _p(v), border=1)
            pdf.ln()

    # Evolucao mensal de erros
    if "data_criacao_erro" in df_errors.columns and not df_errors.empty:
        df_ev = df_errors.copy()
        df_ev["data_criacao_erro"] = pd.to_datetime(df_ev["data_criacao_erro"], errors="coerce", utc=True)
        df_ev["Mes"] = df_ev["data_criacao_erro"].dt.to_period("M").astype(str)
        df_ev_group = df_ev.groupby("Mes").size().reset_index(name="Erros")
        if not df_ev_group.empty:
            pdf.ln(4)
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, _p("Evolucao Mensal de Erros"), ln=True)
            pdf.set_font("Helvetica", "B", 10)
            col_wev = [80, 40]
            pdf.set_fill_color(220, 230, 241)
            for h, w in zip(["Mes", "Erros"], col_wev):
                pdf.cell(w, 7, _p(h), border=1, fill=True)
            pdf.ln()
            pdf.set_font("Helvetica", "", 9)
            for _, row in df_ev_group.iterrows():
                for v, w in zip([str(row["Mes"]), str(int(row["Erros"]))], col_wev):
                    pdf.cell(w, 6, _p(v), border=1)
                pdf.ln()

    pdf.ln(6)

    # Secao 3 — Satisfacao
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_fill_color(36, 64, 97)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, _p("Secao 3 - Indice de Satisfacao"), ln=True, fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(60, 7, _p(f"Total de Votos: {total_votos}"), border=1)
    pdf.cell(65, 7, _p(f"CSAT: {csat:.1f}%"), border=1)
    nm_str = f"{nota_media:.2f}/5" if not pd.isna(nota_media) else "N/A"
    pdf.cell(65, 7, _p(f"Nota Media: {nm_str}"), border=1)
    pdf.ln(10)

    # Tabela breakdown 5 categorias
    _rating_labels_pdf = {
        1: "Muito Insatisfeito",
        2: "Insatisfeito",
        3: "Regular",
        4: "Satisfeito",
        5: "Muito Satisfeito",
    }
    counts_v = df_votes["avaliacao_voto_servico"].value_counts() if not df_votes.empty else pd.Series(dtype=int)
    pdf.set_font("Helvetica", "B", 10)
    col_w3 = [80, 40, 40]
    pdf.set_fill_color(220, 230, 241)
    for h, w in zip(["Categoria", "Votos", "%"], col_w3):
        pdf.cell(w, 7, _p(h), border=1, fill=True)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for nota, label in _rating_labels_pdf.items():
        n = int(counts_v.get(nota, 0))
        pct = (n / total_votos * 100) if total_votos else 0
        for v, w in zip([label, str(n), f"{pct:.1f}%"], col_w3):
            pdf.cell(w, 6, _p(v), border=1)
        pdf.ln()
    pdf.ln(6)

    # Tabela satisfacao por servico (com contagem por nota)
    df_sat = _build_df_sat_por_servico(df_votes)
    if not df_sat.empty:
        pdf.set_font("Helvetica", "B", 8)
        col_w2 = [55, 16, 16, 16, 16, 16, 16, 22]
        headers2 = ["Servico", "Votos", "N1", "N2", "N3", "N4", "N5", "CSAT%"]
        pdf.set_fill_color(220, 230, 241)
        for h, w in zip(headers2, col_w2):
            pdf.cell(w, 7, _p(h), border=1, fill=True)
        pdf.ln()
        pdf.set_font("Helvetica", "", 7)
        for _, row in df_sat.head(30).iterrows():
            titulo = str(row.get("titulo_servico", ""))[:38]
            vals2 = [
                titulo,
                str(int(row.get("total_votos", 0))),
                str(int(row.get("n1", 0))),
                str(int(row.get("n2", 0))),
                str(int(row.get("n3", 0))),
                str(int(row.get("n4", 0))),
                str(int(row.get("n5", 0))),
                str(row.get("csat_pct", "")),
            ]
            for v, w in zip(vals2, col_w2):
                pdf.cell(w, 6, _p(v), border=1)
            pdf.ln()

    return pdf.output()


# ------------------------------------------------------------------ #
# Render principal                                                     #
# ------------------------------------------------------------------ #

def render_tab6_relatorio_cge(
    df_errors: pd.DataFrame,
    df_votes: pd.DataFrame,
    df_inventory: pd.DataFrame,
) -> None:
    st.subheader("📋 Relatório CGE — Cartas de Serviço")
    st.caption(
        "Relatório consolidado para a Controladoria-Geral do Estado. "
        "Reflete os filtros de órgão e período aplicados no painel."
    )

    # ---------------------------------------------------------- #
    # Seção 2 — Erros                                            #
    # ---------------------------------------------------------- #
    st.markdown("### Seção 2 — Atualização das Cartas de Serviços")

    for col in ["atendido", "corrigido_erro"]:
        if col in df_errors.columns:
            df_errors[col] = df_errors[col].astype(bool)
    for col in ["data_criacao_erro", "data_atualizacao_erro"]:
        if col in df_errors.columns:
            df_errors[col] = pd.to_datetime(df_errors[col], errors="coerce", utc=True)

    total_erros = len(df_errors)
    atendidos = int(df_errors["atendido"].sum()) if "atendido" in df_errors.columns else 0
    corrigidos = int(df_errors["corrigido_erro"].sum()) if "corrigido_erro" in df_errors.columns else 0
    pendentes = total_erros - atendidos

    c1, c2, c3 = st.columns(3)
    c1.metric("📋 Total de Erros", f"{total_erros}")
    c2.metric(
        "✅ Atendidos",
        f"{atendidos}",
        delta=f"{atendidos/total_erros*100:.0f}%" if total_erros else None,
    )
    c3.metric(
        "⚠️ Pendentes",
        f"{pendentes}",
        delta=f"{pendentes/total_erros*100:.0f}%" if total_erros else None,
        delta_color="inverse",
    )

    if not df_errors.empty:
        # Link dinâmico
        df_tab = df_errors.copy()
        if "slug_categoria" in df_tab.columns and "slug_servico" in df_tab.columns:
            df_tab["Link"] = (
                "https://www.ms.gov.br/"
                + df_tab["slug_categoria"].fillna("servicos")
                + "/"
                + df_tab["slug_servico"]
            )
        else:
            df_tab["Link"] = ""

        cols_show = [c for c in [
            "siglaorgao", "titulo_servico", "Link", "conteudo",
            "atendido", "corrigido_erro", "resolucao_erro",
            "data_criacao_erro",
        ] if c in df_tab.columns]

        rename_map = {
            "siglaorgao": "Órgão",
            "titulo_servico": "Serviço",
            "Link": "Acessar Serviço",
            "conteudo": "Tipo de Erro",
            "atendido": "Atendido",
            "corrigido_erro": "Corrigido",
            "resolucao_erro": "Resolução",
            "data_criacao_erro": "Data Abertura",
        }
        col_cfg: dict = {}
        if "Link" in cols_show:
            col_cfg["Acessar Serviço"] = st.column_config.LinkColumn(
                "Acessar Serviço", display_text="🔗 Abrir"
            )

        st.dataframe(
            df_tab[cols_show].rename(columns=rename_map),
            column_config=col_cfg,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Nenhum erro encontrado para o filtro atual.")

    st.markdown("---")

    # ---------------------------------------------------------- #
    # Seção 3 — Satisfação                                       #
    # ---------------------------------------------------------- #
    st.markdown("### Seção 3 — Índice de Satisfação")

    df_v = df_votes.copy()
    if not df_v.empty:
        df_v["data_voto"] = pd.to_datetime(df_v["data_voto"], errors="coerce", utc=True)

    total_votos = len(df_v)
    nota_media = df_v["avaliacao_voto_servico"].mean() if total_votos else float("nan")
    soma_notas = df_v["avaliacao_voto_servico"].sum() if total_votos else 0
    csat = (soma_notas / (total_votos * 5) * 100) if total_votos else 0.0

    cv1, cv2, cv3 = st.columns(3)
    cv1.metric("🗳️ Total de Votos", f"{total_votos}")
    cv2.metric("📊 CSAT", f"{csat:.1f}%")
    cv3.metric("⭐ Nota Média", f"{nota_media:.2f}/5" if not pd.isna(nota_media) else "N/A")

    if total_votos:
        _render_satisfaction_icons(df_v, total_votos)

    # Ranking por serviço
    df_sat = _build_df_sat_por_servico(df_v)
    if not df_sat.empty:
        st.dataframe(
            df_sat.rename(columns={
                "titulo_servico": "Serviço",
                "total_votos": "Total Votos",
                "nota_media": "Nota Média",
                "soma_notas": "Soma Notas",
                "csat_pct": "CSAT (%)",
                "n1": "😡 M.Insatisfeito",
                "n2": "😟 Insatisfeito",
                "n3": "😐 Regular",
                "n4": "🙂 Satisfeito",
                "n5": "😄 M.Satisfeito",
            }).drop(columns=["Soma Notas"], errors="ignore"),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Nenhum dado de satisfação encontrado para o filtro atual.")

    st.markdown("---")

    # ---------------------------------------------------------- #
    # Exportar                                                    #
    # ---------------------------------------------------------- #
    st.markdown("### Exportar Relatório")
    col_xl, col_pdf = st.columns(2)

    with col_xl:
        try:
            xlsx_bytes = _export_xlsx(df_errors, df_v)
            st.download_button(
                label="⬇️ Exportar XLSX",
                data=xlsx_bytes,
                file_name="relatorio_cge.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except ImportError:
            st.warning("openpyxl não instalado. Execute: pip install openpyxl")

    with col_pdf:
        try:
            pdf_bytes = _export_pdf(
                df_errors, df_v,
                total_erros, atendidos, pendentes,
                total_votos, csat, nota_media,
            )
            st.download_button(
                label="⬇️ Exportar PDF",
                data=bytes(pdf_bytes),
                file_name="relatorio_cge.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except ImportError:
            st.warning("fpdf2 não instalado. Execute: pip install fpdf2")
