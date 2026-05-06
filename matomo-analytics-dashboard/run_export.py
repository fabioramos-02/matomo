import os
import pandas as pd
from datetime import datetime, timedelta

# Importar configurações e APIs
import config
from api.matomo_client import MatomoAPI
from api.google_analytics_client import GoogleAnalyticsAPI

# Importar Processadores
from utils.ga_data_processor import (
    process_ga_overview,
    process_ga_cities,
    process_ga_services,
    process_ga_platform
)
from utils.data_processor import (
    process_cities_ms
)

# Importar Exportador
from utils.qlik_exporter import export_to_qlik

def run():
    print("🚀 Iniciando processo de exportação para Qlik...")
    
    # 1. Configuração de Datas (Últimos 30 dias por padrão)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    print(f"📅 Período: {start_date} até {end_date}")

    # 2. Inicializar APIs
    # Matomo
    matomo_api = MatomoAPI(
        base_url=config.MATOMO_URL, 
        token=config.MATOMO_TOKEN, 
        site_id=config.MATOMO_SITE_ID
    )
    
    # GA4
    ga_api = GoogleAnalyticsAPI(
        client_id=config.GOOGLE_CLIENT_ID,
        client_secret=config.GOOGLE_CLIENT_SECRET,
        refresh_token=config.GOOGLE_REFRESH_TOKEN,
        property_id=config.GOOGLE_PROPERTY_ID
    )

    data_to_export = {}

    # 3. Buscar e Processar Dados — MS Digital (GA4)
    print("📊 Buscando dados do GA4...")
    try:
        # Overview e Engajamento
        raw_overview = ga_api.get_overview(start_date, end_date)
        ga_ov_dict = process_ga_overview(raw_overview)
        data_to_export["ga_overview"] = ga_ov_dict["retention_df"]
        
        # Cidades
        raw_cities = ga_api.get_geography(start_date, end_date)
        data_to_export["ga_cities"] = process_ga_cities(raw_cities)
        
        # Serviços/Funcionalidades
        raw_services = ga_api.get_services(start_date, end_date)
        data_to_export["ga_services"] = process_ga_services(raw_services)
        
        # Plataformas
        raw_platform = ga_api.get_platform(start_date, end_date)
        data_to_export["ga_platform"] = process_ga_platform(raw_platform)
        
    except Exception as e:
        print(f"❌ Erro ao processar GA4: {e}")

    # 4. Buscar e Processar Dados — Portal (Matomo)
    print("📉 Buscando dados do Matomo...")
    try:
        # Cidades MS
        raw_matomo_cities = matomo_api.get_city("range", f"{start_date},{end_date}", site_id=config.MATOMO_SITE_ID)
        data_to_export["matomo_cities"] = process_cities_ms(raw_matomo_cities)
        
        # Podemos adicionar mais métricas do Matomo conforme a necessidade
    except Exception as e:
        print(f"❌ Erro ao processar Matomo: {e}")

    # 5. Exportar tudo
    export_to_qlik(data_to_export, output_dir="exports")
    print("✅ Exportação concluída com sucesso!")

if __name__ == "__main__":
    run()
