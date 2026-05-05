import { BetaAnalyticsDataClient } from "@google-analytics/data";

const client = new BetaAnalyticsDataClient({
  keyFilename: "matomo-analytics-dashboard/.streamlit/ms-digital-495412-e73bea41b2e6.json",
});

const [response] = await client.runReport({
  property: "properties/424604232",
  dateRanges: [{ startDate: "7daysAgo", endDate: "today" }],
  metrics: [{ name: "activeUsers" }],
});

console.log(response);
