import pandas as pd


def process_ga_screens(data: list) -> pd.DataFrame:
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df = df.rename(columns={"pagePath": "URL", "screenPageViews": "Visitas"})
    df["Visitas"] = pd.to_numeric(df["Visitas"], errors="coerce").fillna(0).astype(int)
    return df[["URL", "Visitas"]].sort_values("Visitas", ascending=False).reset_index(drop=True)


def process_ga_search(data: list) -> pd.DataFrame:
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df = df.rename(columns={"searchTerm": "Palavra-chave", "eventCount": "Buscas"})
    df["Buscas"] = pd.to_numeric(df["Buscas"], errors="coerce").fillna(0).astype(int)
    df = df[df["Palavra-chave"].notna() & (df["Palavra-chave"] != "(not set)")]
    return df[["Palavra-chave", "Buscas"]].sort_values("Buscas", ascending=False).head(20).reset_index(drop=True)


_REGION_TO_UF = {
    # PT com acento
    "Acre": "AC", "Alagoas": "AL", "Amapá": "AP", "Amazonas": "AM",
    "Bahia": "BA", "Ceará": "CE", "Distrito Federal": "DF",
    "Espírito Santo": "ES", "Goiás": "GO", "Maranhão": "MA",
    "Mato Grosso": "MT", "Mato Grosso do Sul": "MS", "Minas Gerais": "MG",
    "Pará": "PA", "Paraíba": "PB", "Paraná": "PR", "Pernambuco": "PE",
    "Piauí": "PI", "Rio de Janeiro": "RJ", "Rio Grande do Norte": "RN",
    "Rio Grande do Sul": "RS", "Rondônia": "RO", "Roraima": "RR",
    "Santa Catarina": "SC", "São Paulo": "SP", "Sergipe": "SE", "Tocantins": "TO",
    # EN / sem acento (como GA4 retorna)
    "Amapa": "AP", "Ceara": "CE", "Espirito Santo": "ES", "Goias": "GO",
    "Maranhao": "MA", "Para": "PA", "Paraiba": "PB", "Parana": "PR",
    "Piaui": "PI", "Rondonia": "RO", "Sao Paulo": "SP",
    "State of Acre": "AC", "State of Alagoas": "AL", "State of Amapá": "AP",
    "State of Amazonas": "AM", "State of Bahia": "BA", "State of Ceará": "CE",
    "State of Espírito Santo": "ES", "State of Goiás": "GO",
    "State of Maranhão": "MA", "State of Mato Grosso": "MT",
    "State of Mato Grosso do Sul": "MS", "State of Minas Gerais": "MG",
    "State of Pará": "PA", "State of Paraíba": "PB", "State of Paraná": "PR",
    "State of Pernambuco": "PE", "State of Piauí": "PI",
    "State of Rio de Janeiro": "RJ", "State of Rio Grande do Norte": "RN",
    "State of Rio Grande do Sul": "RS", "State of Rondônia": "RO",
    "State of Roraima": "RR", "State of Santa Catarina": "SC",
    "State of São Paulo": "SP", "State of Sergipe": "SE",
    "State of Tocantins": "TO", "Federal District": "DF",
}


from utils.geo_constants import CITY_COORDS

def process_ga_cities(data: list) -> pd.DataFrame:
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)

    # Renomeação dinâmica (só renomeia o que existe)
    rename_map = {
        "city": "Cidade",
        "region": "Região",
        "country": "País",
        "latitude": "lat",
        "longitude": "lon",
        "activeUsers": "Visitas"
    }
    # Filtra o map para colunas presentes
    actual_rename = {k: v for k, v in rename_map.items() if k in df.columns}
    df = df.rename(columns=actual_rename)

    df["Visitas"] = pd.to_numeric(df["Visitas"], errors="coerce").fillna(0).astype(int)

    # Processa coordenadas se existirem
    if "lat" in df.columns:
        df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    if "lon" in df.columns:
        df["lon"] = pd.to_numeric(df["lon"], errors="coerce")

    # Fallback de Geocodificação Estática para Cidades de MS (quando GA4 não envia coordenadas)
    def apply_geo_fallback(row):
        # Se lat/lon já existem e são válidos, mantém
        if pd.notna(row.get("lat")) and pd.notna(row.get("lon")):
            return row["lat"], row["lon"]

        # Tenta buscar no dicionário estático
        cidade = row.get("Cidade")
        if cidade in CITY_COORDS:
            return CITY_COORDS[cidade]["lat"], CITY_COORDS[cidade]["lon"]

        return row.get("lat"), row.get("lon")

    # Garante que lat/lon existam antes de aplicar fallback
    for col in ["lat", "lon"]:
        if col not in df.columns:
            df[col] = pd.NA

    df[["lat", "lon"]] = df.apply(lambda r: pd.Series(apply_geo_fallback(r)), axis=1)

    # Garantia de colunas mínimas para evitar quebra no agrupamento/UI
    if "Cidade" not in df.columns:
        df["Cidade"] = "Global (País)"
    if "UF" not in df.columns:
        df["UF"] = df.get("País", "Desconhecido")    
    # Limpeza e Normalização
    df["Cidade"] = df["Cidade"].replace({"(not set)": "Desconhecido", "": "Desconhecido"}).fillna("Desconhecido")
    
    # Mapeamento de UF (Apenas para Brasil)
    def map_uf(row):
        pais = row.get("País", "Brazil")
        regiao = row.get("Região", "")
        if pais != "Brazil" and pais != "Desconhecido":
            return pais
        return _REGION_TO_UF.get(regiao, "Outros/Desconhecido")
    
    if "Região" in df.columns or "País" in df.columns:
        df["UF"] = df.apply(map_uf, axis=1)
    
    # Agrupamento dinâmico
    agg_dict = {"Visitas": "sum"}
    if "lat" in df.columns: 
        agg_dict["lat"] = "mean"
    if "lon" in df.columns: 
        agg_dict["lon"] = "mean"
    
    group_cols = ["Cidade", "UF"]
    df = df.groupby(group_cols, as_index=False).agg(agg_dict)
    
    # Garante colunas mínimas para a UI não quebrar
    for col in ["lat", "lon"]:
        if col not in df.columns:
            df[col] = pd.NA
    
    return df.sort_values("Visitas", ascending=False).reset_index(drop=True)


def process_ga_country_map(data: list) -> pd.DataFrame:
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df = df.rename(columns={"country": "País", "activeUsers": "Usuários"})
    df["Usuários"] = pd.to_numeric(df["Usuários"], errors="coerce").fillna(0).astype(int)
    df = df[df["País"].notna() & (df["País"] != "(not set)")]
    # Agrupa por país caso venham duplicatas por alguma razão
    df = df.groupby("País", as_index=False)["Usuários"].sum()
    return df.sort_values("Usuários", ascending=False).reset_index(drop=True)


def process_ga_devices(data: list) -> pd.DataFrame:
    """Retorna dois DataFrames: (df_os como 'browsers', df_category como 'device_types')."""
    if not data:
        return pd.DataFrame(), pd.DataFrame()
    df = pd.DataFrame(data)
    df["activeUsers"] = pd.to_numeric(df["activeUsers"], errors="coerce").fillna(0).astype(int)

    # df_os → substitui browsers (Sistema Operacional)
    df_os = df.groupby("operatingSystem", as_index=False)["activeUsers"].sum()
    df_os = df_os.rename(columns={"operatingSystem": "Navegador", "activeUsers": "Visitas"})
    df_os = df_os[df_os["Navegador"] != "(not set)"].sort_values("Visitas", ascending=False)
    if len(df_os) > 5:
        top = df_os.head(4)
        outros = pd.DataFrame([{"Navegador": "Outros", "Visitas": df_os.iloc[4:]["Visitas"].sum()}])
        df_os = pd.concat([top, outros], ignore_index=True)

    # df_category → device types
    df_cat = df.groupby("deviceCategory", as_index=False)["activeUsers"].sum()
    df_cat = df_cat.rename(columns={"deviceCategory": "Dispositivo", "activeUsers": "Visitas"})
    df_cat = df_cat[df_cat["Dispositivo"] != "(not set)"].sort_values("Visitas", ascending=False)

    return df_os.reset_index(drop=True), df_cat.reset_index(drop=True)


def process_ga_visit_time(data: list) -> pd.DataFrame:
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df = df.rename(columns={"hour": "Hora", "activeUsers": "Visitas"})
    df["Visitas"] = pd.to_numeric(df["Visitas"], errors="coerce").fillna(0).astype(int)
    df["Hora"] = df["Hora"].apply(lambda h: f"{int(h)}h")
    return df[["Hora", "Visitas"]].sort_values("Hora").reset_index(drop=True)


def process_ga_overview(data: list) -> dict:
    """Retorna dict com KPIs totais e DataFrame new vs returning."""
    if not data:
        return {
            "total_users": 0, "total_sessions": 0, "total_views": 0, 
            "avg_engagement": "0s", "retention_df": pd.DataFrame()
        }
    df = pd.DataFrame(data)
    
    # Lista base de colunas esperadas
    metrics = ["activeUsers", "sessions", "screenPageViews", "userEngagementDuration", "averageSessionDuration"]
    available_metrics = [m for m in metrics if m in df.columns]
    
    for col in available_metrics:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(float)
    
    df = df.rename(columns={
        "newVsReturning": "Tipo",
        "activeUsers": "Usuários",
        "sessions": "Sessões",
        "screenPageViews": "Visualizações",
    })
    
    total_users = int(df["Usuários"].sum())
    
    # Cálculo do Tempo de Engajamento
    # Se userEngagementDuration (segundos totais) existe e é > 0, usamos ele
    # Caso contrário, tentamos usar averageSessionDuration (que já vem como média do GA4)
    if "userEngagementDuration" in df.columns and df["userEngagementDuration"].sum() > 0:
        total_engagement_sec = df["userEngagementDuration"].sum()
        avg_sec = total_engagement_sec / total_users if total_users > 0 else 0
    elif "averageSessionDuration" in df.columns:
        avg_sec = df["averageSessionDuration"].mean()
    else:
        avg_sec = 0
    
    m, s = divmod(int(avg_sec), 60)
    avg_engagement_str = f"{m} min {s} s" if m > 0 else f"{s} s"

    label_map = {"new": "Novos", "returning": "Recorrentes"}
    df["Tipo"] = df["Tipo"].map(label_map).fillna(df["Tipo"])
    
    return {
        "total_users": total_users,
        "total_sessions": int(df["Sessões"].sum()),
        "total_views": int(df["Visualizações"].sum()),
        "avg_engagement": avg_engagement_str,
        "retention_df": df[["Tipo", "Usuários", "Sessões"]].reset_index(drop=True),
    }


def process_ga_platform(data: list) -> pd.DataFrame:
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df["activeUsers"] = pd.to_numeric(df["activeUsers"], errors="coerce").fillna(0).astype(int)
    df["sessions"] = pd.to_numeric(df["sessions"], errors="coerce").fillna(0).astype(int)
    df = df.rename(columns={"platform": "Plataforma", "operatingSystem": "Sistema", "activeUsers": "Usuários", "sessions": "Sessões"})
    df = df[df["Plataforma"] != "(not set)"]
    return df.sort_values("Usuários", ascending=False).reset_index(drop=True)


def process_ga_funnel(data: list) -> pd.DataFrame:
    """Todos os eventos ordenados por volume para visualização de funil."""
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df = df.rename(columns={"eventName": "Evento", "eventCount": "Ocorrências", "totalUsers": "Usuários"})
    df["Ocorrências"] = pd.to_numeric(df["Ocorrências"], errors="coerce").fillna(0).astype(int)
    df["Usuários"] = pd.to_numeric(df["Usuários"], errors="coerce").fillna(0).astype(int)
    # Ordena: eventos de sistema no topo (contexto de funil), depois customizados
    ordem_sistema = ["first_open", "session_start", "screen_view", "user_engagement"]
    sistema = df[df["Evento"].isin(ordem_sistema)].set_index("Evento").reindex(ordem_sistema).dropna().reset_index()
    customizados = df[~df["Evento"].isin(ordem_sistema)].sort_values("Ocorrências", ascending=False)
    return pd.concat([sistema, customizados], ignore_index=True)


_SERVICOS_EXCLUIR = {"(not set)", "", "Educação", "Segurança", "Trânsito"}
_EVENTO_SERVICO = "use_feature"


def process_ga_services(data: list) -> pd.DataFrame:
    """Segmento 'Funcionalidade' do GA4: use_feature por unifiedScreenName.
    Exclusoes do payload: (not set), Educacao, Seguranca, Transito."""
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df = df.rename(columns={"screenPageTitle": "Serviço", "eventCount": "Acessos"})
    df["Acessos"] = pd.to_numeric(df["Acessos"], errors="coerce").fillna(0).astype(int)
    if "eventName" in df.columns:
        df = df[df["eventName"] == _EVENTO_SERVICO]
    df = df[df["Serviço"].notna() & ~df["Serviço"].isin(_SERVICOS_EXCLUIR)]
    df = df.groupby("Serviço", as_index=False)["Acessos"].sum()
    df = df.sort_values("Acessos", ascending=False).reset_index(drop=True)
    total = df["Acessos"].sum()
    df["%"] = (df["Acessos"] / total * 100).round(1) if total > 0 else 0.0
    return df


def process_ga_services_trend(data: list, top_services: list) -> pd.DataFrame:
    """Tendência temporal dos top serviços. Filtra por use_feature e exclusoes do segmento."""
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df = df.rename(columns={"screenPageTitle": "Serviço", "date": "Data", "eventCount": "Acessos"})
    df["Acessos"] = pd.to_numeric(df["Acessos"], errors="coerce").fillna(0).astype(int)
    if "eventName" in df.columns:
        df = df[df["eventName"] == _EVENTO_SERVICO]
    df = df[df["Serviço"].isin(top_services)]
    df["Data"] = pd.to_datetime(df["Data"], format="%Y%m%d", errors="coerce")
    df = df.dropna(subset=["Data"]).sort_values("Data")
    return df


_LINKS_EXCLUIR = {"(not set)", "", "unknown"}


def process_ga_external_links(data: list) -> pd.DataFrame:
    """Links externos: click event por linkText. Exclui unknown/(not set)/empty (payload GA4)."""
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df = df.rename(columns={"linkText": "Destino", "eventCount": "Cliques", "activeUsers": "Usuários"})
    df["Cliques"] = pd.to_numeric(df["Cliques"], errors="coerce").fillna(0).astype(int)
    df["Usuários"] = pd.to_numeric(df["Usuários"], errors="coerce").fillna(0).astype(int)
    df = df[df["Destino"].notna() & ~df["Destino"].isin(_LINKS_EXCLUIR)]
    return df.sort_values("Cliques", ascending=False).reset_index(drop=True)


def process_ga_events(data: list) -> pd.DataFrame:
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df = df.rename(columns={"eventName": "Evento", "eventCount": "Acessos"})
    df["Acessos"] = pd.to_numeric(df["Acessos"], errors="coerce").fillna(0).astype(int)
    # Filtra eventos automáticos irrelevantes para análise de jornada
    eventos_ruido = {"session_start", "first_visit", "first_open", "user_engagement", "app_remove"}
    df = df[~df["Evento"].isin(eventos_ruido)]
    return df.sort_values("Acessos", ascending=False).reset_index(drop=True)
