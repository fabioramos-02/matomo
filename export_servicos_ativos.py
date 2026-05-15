import pandas as pd


def read_csv_smart(path, sep=";"):
    """Lê CSV detectando encoding (UTF-8 com BOM ou cp1252/latin1)."""
    with open(path, "rb") as f:
        raw = f.read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    content = raw[3:] if bom else raw
    for enc in ["utf-8", "cp1252", "latin1"]:
        try:
            content.decode(enc)
            return pd.read_csv(
                path,
                sep=sep,
                encoding="utf-8-sig" if (enc == "utf-8" and bom) else enc,
            )
        except (UnicodeDecodeError, ValueError):
            continue
    return pd.read_csv(path, sep=sep, encoding="latin1")


# Carrega arquivos
inventory = read_csv_smart(
    "matomo-analytics-dashboard/exports/cartas_inventory.csv"
)
matomo = read_csv_smart(
    "matomo-analytics-dashboard/exports/matomo_services.csv"
)

# Limpa BOM em nomes de colunas
inventory.columns = [c.lstrip("﻿") for c in inventory.columns]
matomo.columns = [c.lstrip("﻿") for c in matomo.columns]

# Monta mapeamento slug_categoria -> nome legível da categoria
matomo["slug_cat"] = matomo["URL_Original"].str.split("/").str[0]
cat_map = (
    matomo.dropna(subset=["Categoria", "slug_cat"])
    .drop_duplicates("slug_cat")
    .set_index("slug_cat")["Categoria"]
    .to_dict()
)

# Filtra apenas serviços ativos
ativos = inventory[inventory["servico_ativo"] == True][
    ["idservico", "titulo_servico", "siglaorgao", "nome_orgao", "slug_categoria", "slug_servico"]
].copy()

# Categoria legível e URL
ativos["categoria"] = ativos["slug_categoria"].map(cat_map).fillna(ativos["slug_categoria"])
ativos["url"] = (
    "https://www.ms.gov.br/" + ativos["slug_categoria"] + "/" + ativos["slug_servico"]
)

# Seleciona e ordena colunas finais
result = (
    ativos[["titulo_servico", "siglaorgao", "nome_orgao", "categoria", "url"]]
    .drop_duplicates()
    .sort_values("titulo_servico")
    .reset_index(drop=True)
)

output_path = "matomo-analytics-dashboard/exports/servicos_ativos.csv"
result.to_csv(output_path, sep=";", index=False, encoding="utf-8-sig")

print(f"Arquivo gerado: {output_path}")
print(f"Total de serviços ativos: {len(result)}")
print()
print(result.head(10).to_string(index=False))
