# Plano de Implementação: Matomo Analytics Dashboard

## Objetivo
Criar uma aplicação simples em Python para extrair dados analíticos do portal de serviços (https://www.ms.gov.br/, idSite=298) através da API do Matomo e exibi-los em um dashboard interativo focado na jornada do usuário. A aplicação não utilizará banco de dados; ela processará os dados da API sob demanda e os exibirá.

## Visão Geral da Arquitetura
A aplicação será construída utilizando **Streamlit**, que permite criar dashboards interativos rapidamente em Python sem necessidade de escrever frontend (HTML/JS/CSS). 

**Fluxo de Dados (Pipeline):**
1. O usuário seleciona o período (dia, semana, mês, ano) no Dashboard.
2. A aplicação Python faz requisições HTTP (usando `requests`) para a API do Matomo buscando respostas em JSON.
3. Os dados são limpos e filtrados usando `pandas` (ex: aplicando expressões regulares para encontrar as Cartas de Serviço).
4. Os dados são renderizados na interface usando gráficos do Streamlit/Plotly (ex: barras, tabelas e possivelmente fluxos).

## Estrutura do Repositório (Proposta)
```text
matomo-analytics-dashboard/
├── app.py                 # Interface principal (Dashboard Streamlit)
├── config.py              # Configurações de API, Tokens e IDs
├── api/
│   └── matomo_client.py   # Funções que chamam a API do Matomo
├── utils/
│   └── data_processor.py  # Tratamento de dados e identificação de Cartas de Serviço
├── docs/
│   ├── limitacoes.md      # Limitações técnicas e de negócio (Chefe)
│   └── documentacao.md    # Documentação funcional da aplicação
├── requirements.txt       # Dependências (streamlit, pandas, requests, plotly)
└── README.md
```

## Identificação das "Cartas de Serviço"
Analisando a estrutura retornada pela API (`Actions.getPageUrls`), os serviços não possuem um prefixo único como `/servicos/`. Eles aparecem como slugs descritivos, muitas vezes com um número no final ou o sufixo `/imprimir` (Ex: `agendar-atendimento-presencial153`, `requerer-a-reducao-da-contribuicao-previdenciaria195`).
**Padrão Proposto:** Utilizar uma expressão regular que filtre páginas cujo "label" (URL) não seja genérico (como `/index`, `/busca`), possua palavras-chave de ação ("requerer", "agendar", "solicitar", "pagar", etc.) e hífen.

## Documentos Solicitados

### 1. Funcionalidades da Aplicação (O que ela faz)
* **Extração Dinâmica:** Coleta dados em JSON para períodos flexíveis (day, week, month, year, date range).
* **Top Páginas:** Exibe as URLs gerais mais acessadas.
* **Top Palavras Buscadas:** Consome o método `Actions.getSiteSearchKeywords` para ver o que os cidadãos buscam na pesquisa do site.
* **Filtro de Cartas de Serviço:** Isola e ranqueia os serviços específicos mais buscados, validando o padrão das URLs.
* **Jornada de Navegação Básica:** Utiliza transições de página (de onde o usuário veio e para onde foi) focando em uma carta de serviço específica.

### 2. Limitações e Faltas (Para a Chefia)
* **Falta de Padronização de URL:** Como as Cartas de Serviço não estão debaixo de um diretório exclusivo (ex: `ms.gov.br/servico/nome`), a captura depende de padrões de texto (regex) que podem falhar ou incluir páginas incorretas se o portal criar uma notícia com formato similar.
* **Mapeamento Visual da Jornada Completa (Sankey):** O Matomo não fornece um endpoint simples que retorne a "Árvore de Navegação" de todos os usuários ao mesmo tempo (ex: Home -> Busca -> Serviço -> Saída). A API `Transitions.getTransitionsForPageUrl` permite ver o passo anterior e o próximo de *uma única página*, mas montar o gráfico de fluxo completo do site requer extração massiva dos logs brutos (`Live.getLastVisitsDetails`), o que não é performático para períodos longos (como 'year') sem um banco de dados.
* **Performance da API:** Extrair dados com `period=year` pode levar vários segundos ou causar timeout no servidor do Matomo dependendo do volume. Como não usaremos banco de dados local (SQLite), o dashboard pode ter lentidão ao ser recarregado se não aplicarmos cache em memória (ex: `@st.cache_data` do Streamlit).

## Métodos Úteis do Matomo (Para Jornada e Acesso)
Além de `Actions.getPageUrls` e `Actions.getSiteSearchKeywords`, listei outros métodos valiosos na API:
1. **`Transitions.getTransitionsForPageUrl`**: Essencial para a jornada. Mostra páginas anteriores, páginas seguintes e saídas a partir de uma URL específica.
2. **`Live.getLastVisitsDetails`**: Retorna os detalhes linha-a-linha de visitas individuais. É excelente para entender jornadas específicas, mas os dados são pesados. Pode ser segmentado (ex: só visitas que entraram em uma carta de serviço).
3. **`Actions.getEntryPageUrls` / `Actions.getExitPageUrls`**: Quais páginas os usuários veem primeiro e de onde eles abandonam o site.
4. **`DevicesDetection.getOs` / `Resolution.getResolution`**: Entender se a jornada falha em mobile.
