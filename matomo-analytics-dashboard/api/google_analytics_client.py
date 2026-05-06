from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, Dimension, Metric, DateRange,
    FilterExpression, Filter, OrderBy,
)
from google.oauth2.credentials import Credentials


class GoogleAnalyticsAPI:
    def __init__(self, client_id: str, client_secret: str, refresh_token: str, property_id: str):
        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=["https://www.googleapis.com/auth/analytics.readonly"],
        )
        self.client = BetaAnalyticsDataClient(credentials=credentials)
        self.property = f"properties/{property_id}"

    def _run_report(self, dimensions: list, metrics: list, start_date: str, end_date: str):
        try:
            request = RunReportRequest(
                property=self.property,
                dimensions=[Dimension(name=d) for d in dimensions],
                metrics=[Metric(name=m) for m in metrics],
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                limit=500,
            )
            response = self.client.run_report(request)
            rows = []
            for row in response.rows:
                entry = {}
                for i, dim in enumerate(dimensions):
                    entry[dim] = row.dimension_values[i].value
                for i, met in enumerate(metrics):
                    entry[met] = row.metric_values[i].value
                rows.append(entry)
            return rows
        except Exception as e:
            print(f"Erro GA4 ({dimensions}/{metrics}): {e}")
            return []

    def get_screen_views(self, start_date: str, end_date: str):
        return self._run_report(["screenPageTitle", "pagePath"], ["screenPageViews"], start_date, end_date)

    def get_search_keywords(self, start_date: str, end_date: str):
        return self._run_report(["searchTerm"], ["eventCount"], start_date, end_date)

    def get_geography(self, start_date: str, end_date: str):
        """Tenta buscar dados geográficos em níveis decrescentes de complexidade."""
        # 1. Tentativa Completa (Mapa de Pontos)
        res = self._run_report(["city", "region", "country", "latitude", "longitude"], ["activeUsers"], start_date, end_date)
        if res: return res

        # 2. Fallback Regional (Tabela Cidade/UF)
        res = self._run_report(["city", "region", "country"], ["activeUsers"], start_date, end_date)
        if res: return res

        # 3. Fallback Global (Apenas País)
        return self._run_report(["country"], ["activeUsers"], start_date, end_date)

    def get_country_map(self, start_date: str, end_date: str):
        return self._run_report(["country"], ["activeUsers"], start_date, end_date)

    def get_devices(self, start_date: str, end_date: str):
        return self._run_report(["deviceCategory", "operatingSystem"], ["activeUsers"], start_date, end_date)

    def get_visit_time(self, start_date: str, end_date: str):
        return self._run_report(["hour"], ["activeUsers"], start_date, end_date)

    def get_top_events(self, start_date: str, end_date: str):
        return self._run_report(["eventName"], ["eventCount"], start_date, end_date)

    def get_overview(self, start_date: str, end_date: str):
        # userEngagementDuration = tempo total de engajamento (em segundos)
        return self._run_report(
            ["newVsReturning"], 
            ["activeUsers", "sessions", "screenPageViews", "userEngagementDuration"], 
            start_date, end_date
        )

    def get_platform(self, start_date: str, end_date: str):
        return self._run_report(["platform", "operatingSystem"], ["activeUsers", "sessions"], start_date, end_date)

    def get_funnel_events(self, start_date: str, end_date: str):
        """Todos os eventos (sem filtro) para visualização de funil."""
        return self._run_report(["eventName"], ["eventCount", "totalUsers"], start_date, end_date)

    # Dimensões candidatas para unified_screen_name (ordem de preferência baseada no payload GA4)
    _SCREEN_DIM_CANDIDATES = [
        "unifiedScreenName",
        "customEvent:unified_screen_name",
        "screenPageTitle",
        "screenName",
    ]
    _EXCLUIR_TELA = {"(not set)", "", "Educação", "Segurança", "Trânsito"}

    def _get_screen_dim(self, start_date: str, end_date: str) -> tuple[str, list]:
        """Retorna (dim_name, rows) para a primeira dim que tem dados de use_feature."""
        for dim in self._SCREEN_DIM_CANDIDATES:
            rows = self._run_report([dim, "eventName"], ["eventCount"], start_date, end_date)
            # Só aceita se tiver rows de use_feature com tela não-excluída
            for r in rows:
                if r.get("eventName") == "use_feature" and r.get(dim, "(not set)") not in self._EXCLUIR_TELA:
                    return dim, rows
        return "screenPageTitle", []

    def get_services(self, start_date: str, end_date: str):
        """Funcionalidades internas: use_feature × melhor dimensão de tela."""
        dim, rows = self._get_screen_dim(start_date, end_date)
        for r in rows:
            if dim != "screenPageTitle":
                r["screenPageTitle"] = r.pop(dim, "(not set)")
        return rows

    def get_services_trend(self, start_date: str, end_date: str):
        """Tendência temporal: use_feature por melhor dimensão + date."""
        dim, _ = self._get_screen_dim(start_date, end_date)
        rows = self._run_report([dim, "date", "eventName"], ["eventCount"], start_date, end_date)
        for r in rows:
            if dim != "screenPageTitle":
                r["screenPageTitle"] = r.pop(dim, "(not set)")
        return rows

    def get_external_links(self, start_date: str, end_date: str):
        """Links externos clicados: linkText + eventCount + activeUsers (evento click outbound)."""
        try:
            request = RunReportRequest(
                property=self.property,
                dimensions=[Dimension(name="linkText")],
                metrics=[Metric(name="eventCount"), Metric(name="activeUsers")],
                date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
                dimension_filter=FilterExpression(
                    filter=Filter(
                        field_name="eventName",
                        string_filter=Filter.StringFilter(
                            match_type=Filter.StringFilter.MatchType.EXACT,
                            value="click",
                        ),
                    )
                ),
                order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name="eventCount"), desc=True)],
                limit=50,
            )
            response = self.client.run_report(request)
            rows = []
            for row in response.rows:
                rows.append({
                    "linkText": row.dimension_values[0].value,
                    "eventCount": row.metric_values[0].value,
                    "activeUsers": row.metric_values[1].value,
                })
            return rows
        except Exception as e:
            print(f"Erro GA4 get_external_links: {e}")
            return []
