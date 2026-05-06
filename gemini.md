# 🚀 Contexto do Projeto: Automação e Integração Qlik Sense

Este documento sumariza a arquitetura de dados e o fluxo de automação implementado para integrar os dados do **Matomo** e **Google Analytics 4 (GA4)** com o **Qlik Sense**.

## 🏗️ Arquitetura de Dados

O projeto utiliza uma abordagem **Serverless ETL** para manter os custos em zero e a manutenção mínima:

1.  **Extração (Python)**: Um script (`run_export.py`) consome as APIs do Matomo e GA4.
2.  **Transformação**: O Python limpa os dados, aplica geolocalização via dicionário JSON local e normaliza as métricas de engajamento e serviços.
3.  **Carga (GitHub)**: Os dados são salvos como arquivos CSV na pasta `matomo-analytics-dashboard/exports/`.
4.  **Automação (Robozinho)**: Um **GitHub Action** (`data_sync.yml`) roda automaticamente todos os dias às 03:00 AM (ou manualmente) para atualizar estes CSVs.
5.  **Consumo (Qlik)**: O Qlik Sense lê os arquivos diretamente do GitHub através das URLs "Raw".

---

## 🤖 O Robozinho (GitHub Actions)

O workflow está configurado em `.github/workflows/data_sync.yml`.

### Configurações Atuais:
- **Ambiente**: `qlik-env` (onde residem os segredos).
- **Permissões**: `contents: write` (necessário para o robô salvar os CSVs no seu repositório).
- **Trigger**: Agendado para as 03h da manhã e disponível para disparo manual (workflow_dispatch).

### Variáveis de Ambiente (Secrets):
As seguintes chaves já estão configuradas no ambiente `qlik-env` do seu GitHub:
- `MATOMO_URL`, `MATOMO_SITE_ID`, `MATOMO_TOKEN`
- `GOOGLE_PROPERTY_ID`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`

---

## 📊 Integração com Qlik Sense

Para conectar o Qlik aos dados, utilize o conector **Web File** com as URLs abaixo:

### URLs dos Dados (Versão Raw):
- **Serviços**: `https://raw.githubusercontent.com/fabioramos-02/matomo/main/matomo-analytics-dashboard/exports/ga_services.csv`
- **Cidades**: `https://raw.githubusercontent.com/fabioramos-02/matomo/main/matomo-analytics-dashboard/exports/ga_cities.csv`
- **Visão Geral**: `https://raw.githubusercontent.com/fabioramos-02/matomo/main/matomo-analytics-dashboard/exports/ga_overview.csv`

> [!IMPORTANT]
> Sempre que o robô rodar, o Qlik atualizará automaticamente ao recarregar o aplicativo, pois a URL é permanente.

---

## 🧠 Lógica de Inteligência (Python)

- **Geolocalização**: Não dependemos mais da API do Google para lat/lon (que falhava). Usamos um lookup nos arquivos `data/municipios.json` e `data/estados.json`.
- **Ranking de Serviços**: O sistema detecta automaticamente se a propriedade GA4 está usando `screenName`, `pageTitle` ou dimensões customizadas, garantindo que o ranking nunca fique vazio.
- **Storytelling**: O dashboard Streamlit (`nacional-streamlit-app`) já possui interpretações automáticas para Churn e Engajamento.

---

## 🛠️ Como rodar manualmente (Local)

Caso queira forçar uma exportação do seu computador:
1.  Certifique-se de que os segredos estão no arquivo `.streamlit/secrets.toml`.
2.  Execute: `python matomo-analytics-dashboard/run_export.py`.
3.  Os arquivos na pasta `exports/` serão atualizados.
