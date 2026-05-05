import os
import streamlit as st

# Função segura para pegar configurações
def get_config(key, default_value=None):
    # 1. Tenta pegar do gerenciador de segredos do Streamlit Cloud (ou local .streamlit/secrets.toml)
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    
    # 2. Tenta pegar de variáveis de ambiente do SO (Docker, etc)
    return os.getenv(key, default_value)

# Configurações da API do Matomo
MATOMO_URL = get_config("MATOMO_URL", "https://webanalytics.ms.gov.br/")
MATOMO_SITE_ID = get_config("MATOMO_SITE_ID", "298")
MATOMO_TOKEN = get_config("MATOMO_TOKEN", "")  # Protegido!

# Parâmetros padrão
DEFAULT_PERIOD = "month"
DEFAULT_DATE = "today"

# Google Analytics (MS Digital App) — OAuth2 com conta pessoal
GOOGLE_CLIENT_ID = get_config("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = get_config("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REFRESH_TOKEN = get_config("GOOGLE_REFRESH_TOKEN", "")
GOOGLE_PROPERTY_ID = get_config("GOOGLE_PROPERTY_ID", "")
