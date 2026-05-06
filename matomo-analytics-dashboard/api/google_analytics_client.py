from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, Dimension, Metric, DateRange,
    FilterExpression, Filter, OrderBy,
)
from google.oauth2.credentials import Credentials
import re


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
            err_msg = str(e)
            print(f"Erro GA4 ({dimensions}/{metrics}): {err_msg}")
            
            # Fallback Dinâmico baseado na mensagem de erro
            new_dimensions = list(dimensions)
            new_metrics = list(metrics)
            changed = False

            # Mapa de substituições comuns para dimensões de tela/página
            replacements = {
                "screenPageTitle": "pageTitle",
                "unifiedScreenName": "pageTitle",
                "screenName": "pageTitle",
                "unifiedPageScreenName": "pageTitle",
                "averageEngagementTime": "userEngagementDuration",
            }

            # Identifica o campo problemático na mensagem de erro
            match = re.search(r"Field ([\w:]+) is not a valid (dimension|metric)", err_msg)
            if match:
                field = match.group(1)
                ftype = match.group(2)
                
                if ftype == "dimension" and field in new_dimensions:
                    idx = new_dimensions.index(field)
                    if field in replacements:
                        replacement = replacements[field]
                        if replacement in new_dimensions:
                            new_dimensions.pop(idx)
                        else:
                            new_dimensions[idx] = replacement
                        changed = True
                    elif field in ["latitude", "longitude"]:
                        new_dimensions.pop(idx)
                        changed = True
                elif ftype == "metric" and field in new_metrics:
                    idx = new_metrics.index(field)
                    if field in replacements:
                        replacement = replacements[field]
                        if replacement in new_metrics:
                            new_metrics.pop(idx)
                        else:
                            new_metrics[idx] = replacement
                        changed = True
                    else:
                        new_metrics.pop(idx)
                        changed = True

            if changed and (new_dimensions or new_metrics):
                print(f"Tentando fallback GA4: {new_dimensions} / {new_metrics}")
                return self._run_report(new_dimensions, new_metrics, start_date, end_date)
            
            return []

    def get_screen_views(self, start_date: str, end_date: str):
        return self._run_report(["pageTitle", "pagePath"], ["screenPageViews"], start_date, end_date)

    def get_search_keywords(self, start_date: str, end_date: str):
        return self._run_report(["searchTerm"], ["eventCount"], start_date, end_date)

    def get_geography(self, start_date: str, end_date: str):
        return self._run_report(["city", "region", "country"], ["activeUsers"], start_date, end_date)

    def get_country_map(self, start_date: str, end_date: str):
        return self._run_report(["country"], ["activeUsers"], start_date, end_date)

    def get_devices(self, start_date: str, end_date: str):
        return self._run_report(["deviceCategory", "operatingSystem"], ["activeUsers"], start_date, end_date)

    def get_visit_time(self, start_date: str, end_date: str):
        return self._run_report(["hour"], ["activeUsers"], start_date, end_date)

    def get_top_events(self, start_date: str, end_date: str):
        return self._run_report(["eventName"], ["eventCount"], start_date, end_date)

    def get_overview(self, start_date: str, end_date: str):
        return self._run_report(
            ["newVsReturning"], 
            ["activeUsers", "sessions", "screenPageViews", "userEngagementDuration"], 
            start_date, end_date
        )

    def get_platform(self, start_date: str, end_date: str):
        return self._run_report(["platform", "operatingSystem"], ["activeUsers", "sessions"], start_date, end_date)

    def get_funnel_events(self, start_date: str, end_date: str):
        return self._run_report(["eventName"], ["eventCount", "totalUsers"], start_date, end_date)

    def get_services(self, start_date: str, end_date: str):
        # unifiedPageScreenName é o mapeamento técnico para 'Título da página e nome da tela'
        return self._run_report(["unifiedPageScreenName", "eventName"], ["eventCount"], start_date, end_date)

    def get_services_trend(self, start_date: str, end_date: str):
        return self._run_report(["pageTitle", "date", "eventName"], ["eventCount"], start_date, end_date)

    def get_external_links(self, start_date: str, end_date: str):
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
