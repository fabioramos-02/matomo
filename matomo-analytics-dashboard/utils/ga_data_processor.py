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


def process_ga_cities(data: list) -> pd.DataFrame:
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df = df.rename(columns={"city": "Cidade", "activeUsers": "Visitas"})
    df["Visitas"] = pd.to_numeric(df["Visitas"], errors="coerce").fillna(0).astype(int)
    df = df[df["Cidade"].notna() & (df["Cidade"] != "(not set)")]
    df = df.groupby("Cidade", as_index=False)["Visitas"].sum()
    return df.sort_values("Visitas", ascending=False).reset_index(drop=True)


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
        return {"total_users": 0, "total_sessions": 0, "total_views": 0, "retention_df": pd.DataFrame()}
    df = pd.DataFrame(data)
    for col in ["activeUsers", "sessions", "screenPageViews"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    df = df.rename(columns={
        "newVsReturning": "Tipo",
        "activeUsers": "Usuários",
        "sessions": "Sessões",
        "screenPageViews": "Visualizações",
    })
    label_map = {"new": "Novos", "returning": "Recorrentes"}
    df["Tipo"] = df["Tipo"].map(label_map).fillna(df["Tipo"])
    return {
        "total_users": int(df["Usuários"].sum()),
        "total_sessions": int(df["Sessões"].sum()),
        "total_views": int(df["Visualizações"].sum()),
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
