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
