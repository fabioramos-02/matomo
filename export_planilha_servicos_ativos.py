"""Gera planilha XLSX de cartas de serviço ATIVAS para entrega à chefia.

Cruza:
  - ../cruzamento-carta/planilha_cartas.csv  (descrição limpa, sem HTML)
  - matomo-analytics-dashboard/exports/cartas_inventory.csv  (nome_orgao + flags canal)

Saída: matomo-analytics-dashboard/exports/planilha_servicos_ativos.xlsx
Colunas: titulo_carta, nome_orgao, sigla_orgao, descricao_servico, canal, url_servico
Canal:
  digital=True                                      -> Digital
  digital=False AND (online OR agendavel)           -> Híbrido
  caso contrário                                    -> Presencial
"""

from pathlib import Path

import pandas as pd

CRUZAMENTO_CSV = Path("../cruzamento-carta/planilha_cartas.csv")
INVENTORY_CSV = Path("matomo-analytics-dashboard/exports/cartas_inventory.csv")
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


def derivar_canal(row: pd.Series) -> str:
    if row["digital"] is True:
        return "Digital"
    if row["digital"] is False and (row["online"] is True or row["agendavel"] is True):
        return "Híbrido"
    return "Presencial"


def main() -> None:
    for p in (CRUZAMENTO_CSV, INVENTORY_CSV):
        if not p.exists():
            raise SystemExit(f"CSV não encontrado: {p}")

    desc = read_csv_smart(CRUZAMENTO_CSV)
    desc.columns = [c.strip().lstrip("﻿") for c in desc.columns]
    desc = desc[["siglaorgao", "titulo_servico", "o_que_e_servico"]].copy()

    inv = read_csv_smart(INVENTORY_CSV)
    inv.columns = [c.strip().lstrip("﻿") for c in inv.columns]
    inv = inv[inv["servico_ativo"] == True].copy()

    for col in ("digital", "online", "agendavel"):
        inv[col] = inv[col].astype(bool)

    inv["canal"] = inv.apply(derivar_canal, axis=1)
    inv["url_servico"] = (
        "https://www.ms.gov.br/"
        + inv["slug_categoria"].fillna("_sem-categoria_").astype(str)
        + "/"
        + inv["slug_servico"].fillna("_sem-slug_").astype(str)
    )

    inv = inv[
        ["siglaorgao", "titulo_servico", "nome_orgao", "canal", "url_servico"]
    ].drop_duplicates(subset=["siglaorgao", "titulo_servico"])

    merged = inv.merge(desc, on=["siglaorgao", "titulo_servico"], how="left")

    merged["o_que_e_servico"] = merged["o_que_e_servico"].fillna("").astype(str).str.strip()

    result = pd.DataFrame(
        {
            "titulo_carta": merged["titulo_servico"],
            "nome_orgao": merged["nome_orgao"],
            "sigla_orgao": merged["siglaorgao"],
            "descricao_servico": merged["o_que_e_servico"],
            "canal": merged["canal"],
            "url_servico": merged["url_servico"],
        }
    ).sort_values(["nome_orgao", "titulo_carta"]).reset_index(drop=True)

    distrib = result["canal"].value_counts().rename_axis("canal").reset_index(name="qtd")
    distrib["pct"] = (distrib["qtd"] / distrib["qtd"].sum() * 100).round(2)

    sem_descricao = int((result["descricao_servico"] == "").sum())

    XLSX_OUT.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(XLSX_OUT, engine="openpyxl") as writer:
        result.to_excel(writer, sheet_name="Servicos Ativos", index=False)
        distrib.to_excel(writer, sheet_name="Distribuicao Canal", index=False)

        ws = writer.sheets["Servicos Ativos"]
        widths = {"A": 60, "B": 50, "C": 14, "D": 80, "E": 14, "F": 70}
        for col, w in widths.items():
            ws.column_dimensions[col].width = w
        ws.freeze_panes = "A2"

    print(f"OK -> {XLSX_OUT}")
    print(f"Total servicos ativos: {len(result)}")
    print(f"Sem descricao (nao casaram com cruzamento-carta): {sem_descricao}")
    print(distrib.to_string(index=False))


if __name__ == "__main__":
    main()
