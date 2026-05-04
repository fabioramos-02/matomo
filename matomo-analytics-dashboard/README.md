# Matomo Analytics Dashboard

🌐 **Ambiente de Produção (Online):** [https://setdig-dados.streamlit.app/](https://setdig-dados.streamlit.app/)

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
- `utils/data_processor.py`: Lógica de limpeza de dados e identificação do padrão de URL das "Cartas de Serviço".
- `docs/`: Pasta contendo a documentação do projeto e um levantamento de limitações técnicas para apresentação à gestão.
