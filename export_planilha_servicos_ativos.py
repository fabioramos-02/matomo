"""Converte planilha_servicos_ativos.csv (gerado via \\copy do psql)
em XLSX formatado para entrega à chefia.

Pré-requisito:
  psql -h <host> -U painel-sgd -d <db> \
       -f matomo-analytics-dashboard/sql/04_planilha_servicos_ativos.sql
  (ou rodar o bloco \\copy do mesmo arquivo no psql interativo)

CSV esperado: matomo-analytics-dashboard/exports/planilha_servicos_ativos.csv
Saída XLSX:   matomo-analytics-dashboard/exports/planilha_servicos_ativos.xlsx
"""

from pathlib import Path

import pandas as pd

CSV_IN = Path("matomo-analytics-dashboard/exports/planilha_servicos_ativos.csv")
XLSX_OUT = Path("matomo-analytics-dashboard/exports/planilha_servicos_ativos.xlsx")


def read_csv_smart(path: Path, sep: str = ";") -> pd.DataFrame:
    with open(path, "rb") as f:
        raw = f.read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    for enc in ["utf-8", "cp1252", "latin1"]:
        try:
            (raw[3:] if bom else raw).decode(enc)
            return pd.read_csv(
                path,
                sep=sep,
                encoding="utf-8-sig" if (enc == "utf-8" and bom) else enc,
            )
        except (UnicodeDecodeError, ValueError):
            continue
    return pd.read_csv(path, sep=sep, encoding="latin1")


def main() -> None:
    if not CSV_IN.exists():
        raise SystemExit(
            f"CSV não encontrado: {CSV_IN}\n"
            "Rode antes o \\copy do sql/04_planilha_servicos_ativos.sql via psql."
        )

    df = read_csv_smart(CSV_IN)
    df.columns = [c.lstrip("﻿") for c in df.columns]

    expected = [
        "titulo_carta",
        "nome_orgao",
        "sigla_orgao",
        "descricao_servico",
        "canal",
        "url_servico",
    ]
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise SystemExit(f"Colunas ausentes no CSV: {missing}")

    df = df[expected].copy()
    df["descricao_servico"] = df["descricao_servico"].fillna("").astype(str).str.strip()
    df["canal"] = df["canal"].fillna("Presencial")

    distrib = df["canal"].value_counts().rename_axis("canal").reset_index(name="qtd")
    distrib["pct"] = (distrib["qtd"] / distrib["qtd"].sum() * 100).round(2)

    XLSX_OUT.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(XLSX_OUT, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Servicos Ativos", index=False)
        distrib.to_excel(writer, sheet_name="Distribuicao Canal", index=False)

        ws = writer.sheets["Servicos Ativos"]
        widths = {"A": 60, "B": 50, "C": 14, "D": 80, "E": 14, "F": 70}
        for col, w in widths.items():
            ws.column_dimensions[col].width = w
        ws.freeze_panes = "A2"

    print(f"OK -> {XLSX_OUT}")
    print(f"Total servicos ativos: {len(df)}")
    print(distrib.to_string(index=False))


if __name__ == "__main__":
    main()
