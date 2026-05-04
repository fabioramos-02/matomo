# Matomo Analytics Dashboard

Aplicação em Python utilizando Streamlit para consumo da API do Matomo (webanalytics.ms.gov.br) e visualização focada na Jornada do Usuário no Portal de Serviços (idSite=298).

## Requisitos
* Python 3.9+
* Pip

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
* `app.py`: Interface principal do Dashboard construída com Streamlit.
* `api/matomo_client.py`: Cliente de comunicação com a API do Matomo via `requests`.
* `utils/data_processor.py`: Lógica de limpeza de dados e identificação do padrão de URL das "Cartas de Serviço".
* `docs/`: Pasta contendo a documentação do projeto e um levantamento de limitações técnicas para apresentação à gestão.

## Como Publicar na Nuvem (Deploy)

Como o Streamlit é um servidor Python em tempo real, plataformas *serverless* tradicionais voltadas para Javascript (como a **Vercel** ou Netlify) **não são recomendadas**. 

As 3 melhores opções gratuitas para colocar seu dashboard no ar são:

1. **Streamlit Community Cloud (Recomendado)**
   * **Como funciona:** É a plataforma oficial. Você sobe este código para o seu GitHub, acessa [share.streamlit.io](https://share.streamlit.io/), faz login com o GitHub e manda ele ler o repositório.
   * **Vantagem:** É 100% gratuito e feito sob medida para esse tipo de app.
   * **Atenção:** Como seu `MATOMO_TOKEN` não deve ficar público no GitHub, você deve acessar as *Settings* do seu app no painel do Streamlit Cloud e colar o token na área de **Secrets** lá.

2. **Render.com**
   * **Como funciona:** Você cria um "Web Service", conecta seu GitHub e ele roda como um servidor real. O comando de start será `streamlit run app.py --server.port $PORT`.

3. **Hugging Face Spaces**
   * **Como funciona:** Permite criar *Spaces* gratuitos rodando Streamlit. Ótimo para dashboards de dados.
