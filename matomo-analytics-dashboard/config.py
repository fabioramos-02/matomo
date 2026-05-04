import os

# Configurações da API do Matomo
MATOMO_URL = os.getenv("MATOMO_URL", "https://webanalytics.ms.gov.br/")
MATOMO_SITE_ID = os.getenv("MATOMO_SITE_ID", "298")
MATOMO_TOKEN = os.getenv("MATOMO_TOKEN", "ae94bc07624d7657a95d51a53a025d5f")

# Parâmetros padrão
DEFAULT_PERIOD = "month"
DEFAULT_DATE = "today"
