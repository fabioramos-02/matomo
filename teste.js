import { google } from "googleapis";

// 1. Você precisa criar essas credenciais no Google Cloud Console (APIs & Services > Credentials)
// Selecione "OAuth client ID" do tipo "Web application" ou "Desktop app"
const CLIENT_ID =
  "474569765246-p86ghkaf2svdu7s2vdkj1e5e105gmuqh.apps.googleusercontent.com";
const CLIENT_SECRET = process.env.GOOGLE_CLIENT_SECRET || "YOUR_CLIENT_SECRET_HERE";
const REDIRECT_URI = "http://localhost:8501/callback";

const oauth2Client = new google.auth.OAuth2(
  CLIENT_ID,
  CLIENT_SECRET,
  REDIRECT_URI,
);

// 2. TOKEN DE ACESSO:
// Para pegar o token pela primeira vez, descomente a linha abaixo e rode o script:
// console.log("Abra esta URL no navegador para autorizar:", oauth2Client.generateAuthUrl({ access_type: 'offline', scope: ['https://www.googleapis.com/auth/analytics.readonly'] }));

// Assim que tiver o ACCESS_TOKEN (via Playground ou URL acima), cole aqui:
oauth2Client.setCredentials({
  access_token: "tes",
});

const analyticsData = google.analyticsdata({
  version: "v1beta",
  auth: oauth2Client,
});

async function runReport() {
  try {
    const res = await analyticsData.properties.runReport({
      property: "properties/424604232",
      requestBody: {
        dateRanges: [{ startDate: "7daysAgo", endDate: "today" }],
        metrics: [{ name: "activeUsers" }],
      },
    });

    console.log("Dados do GA4:", JSON.stringify(res.data, null, 2));
  } catch (err) {
    console.error("Erro na requisição:", err.message);
  }
}

runReport();
