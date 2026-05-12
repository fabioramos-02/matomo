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
    process_ga_platform,
    process_ga_funnel,
    process_ga_external_links,
    process_ga_search
)
from utils.data_processor import (
    process_cities_ms,
    process_matomo_summary,
    process_page_urls,
    identify_service_cards,
    process_search_keywords,
    process_services_trend,
)
from utils.cartas_data_loaders import (
    load_service_cards_inventory,
    load_service_cards_errors,
    load_service_cards_votes,
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
        
        # Funil de Eventos (Jornada)
        raw_funnel = ga_api.get_funnel_events(start_date, end_date)
        data_to_export["ga_funnel"] = process_ga_funnel(raw_funnel)
        
        # Links Externos
        raw_links = ga_api.get_external_links(start_date, end_date)
        data_to_export["ga_links"] = process_ga_external_links(raw_links)

        # Buscas Internas
        raw_ga_search = ga_api.get_search_keywords(start_date, end_date)
        data_to_export["ga_search"] = process_ga_search(raw_ga_search)
        
    except Exception as e:
        print(f"❌ Erro ao processar GA4: {e}")

    # 4. Buscar e Processar Dados — Portal (Matomo)
    print("📉 Buscando dados do Matomo...")
    try:
        # Overview
        raw_matomo_overview = matomo_api.get_visits_summary("range", f"{start_date},{end_date}")
        data_to_export["matomo_overview"] = process_matomo_summary(raw_matomo_overview)

        # Cidades MS
        raw_matomo_cities = matomo_api.get_city("range", f"{start_date},{end_date}")
        data_to_export["matomo_cities"] = process_cities_ms(raw_matomo_cities)
        
        # Serviços (Cartas de Serviço) — agregado do período
        raw_page_urls = matomo_api.get_page_urls("range", f"{start_date},{end_date}", limit=500)
        df_pages = process_page_urls(raw_page_urls)
        df_services = identify_service_cards(df_pages)
        data_to_export["matomo_services"] = df_services

        # Evolução Temporal — Top 5 Serviços (diário, ≤60 dias)
        top5_names = df_services['Nome do Serviço'].head(5).tolist() if not df_services.empty else []
        if top5_names:
            raw_trend = matomo_api.get_page_urls_trend(start_date, end_date, granularity='day')
            if raw_trend and isinstance(raw_trend, dict):
                data_to_export["matomo_services_trend"] = process_services_trend(raw_trend, top5_names)

        # Buscas Internas
        raw_matomo_search = matomo_api.get_site_search_keywords("range", f"{start_date},{end_date}")
        data_to_export["matomo_search"] = process_search_keywords(raw_matomo_search)

    except Exception as e:
        print(f"❌ Erro ao processar Matomo: {e}")

    # 5. Buscar e Processar Dados — Cartas de Serviço (PostgreSQL)
    print("🗄️ Buscando dados do PostgreSQL (Cartas de Serviço)...")
    try:
        data_to_export["cartas_inventory"] = load_service_cards_inventory()
        data_to_export["cartas_errors"] = load_service_cards_errors()
        data_to_export["cartas_votes"] = load_service_cards_votes()
    except Exception as e:
        print(f"❌ Erro ao processar PostgreSQL: {e}")

    # 6. Exportar tudo
    export_to_qlik(data_to_export, output_dir="exports")
    print("✅ Exportação concluída com sucesso!")

if __name__ == "__main__":
    run()
