from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, Dimension, Metric, DateRange
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
        return self._run_report(["city", "region"], ["activeUsers"], start_date, end_date)

    def get_devices(self, start_date: str, end_date: str):
        return self._run_report(["deviceCategory", "operatingSystem"], ["activeUsers"], start_date, end_date)

    def get_visit_time(self, start_date: str, end_date: str):
        return self._run_report(["hour"], ["activeUsers"], start_date, end_date)

    def get_top_events(self, start_date: str, end_date: str):
        return self._run_report(["eventName"], ["eventCount"], start_date, end_date)

    def get_overview(self, start_date: str, end_date: str):
        return self._run_report(["newVsReturning"], ["activeUsers", "sessions", "screenPageViews"], start_date, end_date)

    def get_platform(self, start_date: str, end_date: str):
        return self._run_report(["platform", "operatingSystem"], ["activeUsers", "sessions"], start_date, end_date)

    def get_funnel_events(self, start_date: str, end_date: str):
        """Todos os eventos (sem filtro) para visualização de funil."""
        return self._run_report(["eventName"], ["eventCount", "totalUsers"], start_date, end_date)
