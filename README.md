# Matomo Analytics Dashboard

🌐 **Ambiente de Produção (Online):** [https://setdig-dados.streamlit.app/](https://setdig-dados.streamlit.app/)
📚 **Documentação da API do Matomo:** [Matomo Reporting API](https://developer.matomo.org/api-reference/reporting-api)

Aplicação em Python utilizando Streamlit para consumo da API do Matomo (webanalytics.ms.gov.br) e visualização focada na Jornada do Usuário no Portal de Serviços (idSite=298).

## Requisitos

- Python 3.9+
- Pip

## Como Rodar Localmente

1. Clone o repositório ou navegue até a pasta:

```bash
cd matomo-analytics-dashboard
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. (Opcional) Configure as variáveis de ambiente se o token for alterado:

```bash
# Windows (PowerShell)
$env:MATOMO_TOKEN="seu_token_aqui"
```

4. Execute o dashboard:

```bash
streamlit run app.py
```

5. Acesse `http://localhost:8501` no seu navegador.

## Estrutura do Projeto

- `app.py`: Interface principal do Dashboard construída com Streamlit.
- `api/matomo_client.py`: Cliente de comunicação com a API do Matomo via `requests`.
- `utils/`: Módulos utilitários para processamento de dados, carregamento (`data_loaders`) e padronização visual (`charts_formatter`).
- `exports/`: Pasta de armazenamento de dados CSV exportados pela automação (ETL) para consumo em fallback offline.
- `docs/`: Pasta contendo a documentação do projeto e um levantamento de limitações técnicas para apresentação à gestão.

## 🤖 Automação e Exportação de Dados (Serverless ETL)

O projeto utiliza uma abordagem **Serverless ETL** para manter os custos zero e manutenção mínima, integrando os dados (Matomo, GA4 e Banco de Dados) ao Qlik Sense e fornecendo um *fallback* robusto para o Streamlit.

1. **Extração e Transformação (`run_export.py`)**: Script em Python que consome APIs e Banco de Dados, limpa as informações (como geolocalização e engajamento) e salva tudo na pasta `exports/`.
2. **Carga e Fallback**: Os dados são salvos como CSVs. O Qlik Sense pode ler diretamente as URLs "Raw" do GitHub, e o dashboard Streamlit utiliza estes arquivos como *fallback* caso as APIs ou o Banco de Dados fiquem offline.
3. **Automação (Robozinho)**: O workflow `.github/workflows/data_sync.yml` executa automaticamente a extração todos os dias às **03:00 AM** ou de forma manual (workflow_dispatch).

### Como forçar a exportação manualmente:
Se precisar atualizar os CSVs na sua máquina local:
1. Certifique-se de que os segredos de API e Banco estão configurados em `.streamlit/secrets.toml`.
2. Execute o script de ETL:
```bash
python matomo-analytics-dashboard/run_export.py
```
3. A pasta `exports/` será atualizada com os dados mais recentes.
