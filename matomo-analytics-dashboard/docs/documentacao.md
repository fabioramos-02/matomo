# Documentação do Dashboard Analítico do Matomo

🌐 **Ambiente de Produção:** [https://setdig-dados.streamlit.app/](https://setdig-dados.streamlit.app/)

## O que a aplicação faz?
Esta aplicação é um painel interativo (Dashboard) construído em **Python com Streamlit** que se conecta diretamente à API do Matomo (webanalytics.ms.gov.br) para o site do Portal de Serviços de MS (`idSite=298`).

O objetivo principal é oferecer uma visualização intuitiva sobre a **Jornada do Usuário**, sem a necessidade de manter uma infraestrutura de banco de dados complexa. Os dados são processados em tempo real (sob demanda).

## Funcionalidades Principais

### 1. Visão Geral de Acessos
A aplicação consome a API `Actions.getPageUrls` para extrair e exibir graficamente quais são as páginas gerais mais acessadas do portal de serviços, baseado no período selecionado (dia, semana, mês ou ano).

### 2. Análise de Buscas (O que o cidadão procura)
Através do método `Actions.getSiteSearchKeywords`, o dashboard extrai as palavras-chave mais buscadas na barra de pesquisa do portal, ajudando a identificar gargalos de navegação (quando o usuário não encontra algo no menu, ele busca).

### 3. Filtro e Ranking de "Cartas de Serviço"
Como o portal não possui as cartas de serviço separadas em um módulo de URL específico (ex: `/servico/nome`), a aplicação utiliza um **motor de processamento de texto (Regex)** que analisa a lista das páginas mais acessadas e filtra apenas aquelas que se parecem com um serviço (URL longa, contendo hifens, sem se tratar de diretórios raiz como `/index`).
Isso gera um ranking focado especificamente nos serviços oferecidos ao cidadão.

### 4. Transições de Navegação (Jornada)
Para a principal carta de serviço identificada no filtro, a aplicação realiza uma requisição na API `Transitions.getTransitionsForPageUrl`. O resultado exibe de onde os usuários vieram antes de acessar o serviço e para onde eles foram depois (ou se abandonaram o portal).

## Componentes do Sistema
* **Interface (app.py):** Interface gráfica responsiva usando Streamlit e gráficos interativos usando Plotly.
* **Cliente API (matomo_client.py):** Módulo dedicado para gerenciar autenticação, tokens e a construção das URLs de requisição ao Matomo.
* **Processador de Dados (data_processor.py):** O "cérebro" que filtra as URLs retornadas e identifica os padrões das Cartas de Serviço.
