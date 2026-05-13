import pandas as pd

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
