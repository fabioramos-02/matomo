# 🚀 Feature: Dashboard de Inteligência Governamental (Matomo & GA4)

**Descrição:** Implementação de um dashboard analítico centralizado para monitoramento de tráfego, engajamento e satisfação dos serviços públicos do estado, integrando dados do Matomo, Google Analytics 4 e Base Operacional (PostgreSQL).
**Link de Acesso:** [https://setdig-dados.streamlit.app/](https://setdig-dados.streamlit.app/)

---

## 📋 PBI 1: Integração e Visualização Matomo (Portal MS)
**Objetivo:** Extrair e visualizar métricas de acessos e comportamento dos usuários no Portal do Estado via API Matomo.

*   **Tarefa 1:** Configurar loader de dados (`matomo_data_loaders.py`) para consumo via API/CSV.
*   **Tarefa 2:** Implementar processador de identificação de slugs e categorias (`data_processor.py`).
*   **Tarefa 3:** Criar visões de Dispositivos, Localização (Cidades) e Engajamento Temporal.
*   **Tarefa 4:** Desenvolver ranking de páginas mais acessadas com filtros de data.

---

## 📋 PBI 2: Integração e Visualização Google Analytics 4 (GA4)
**Objetivo:** Consolidar métricas de audiência global e comportamento de busca utilizando os dados do GA4.

*   **Tarefa 1:** Implementar extração programática via Python (`run_export.py`) com persistência em CSV.
*   **Tarefa 2:** Criar visualização de Funil de Conversão e Fluxo de Usuários.
*   **Tarefa 3:** Desenvolver análise de origem de tráfego (Orgânico, Direto, Social).
*   **Tarefa 4:** Implementar KPIs de usuários ativos, sessões e taxa de rejeição.

---

## 📋 PBI 3: Módulo Analítico de Cartas de Serviços
**Objetivo:** Cruzar dados de acesso (Matomo) com dados operacionais de satisfação e qualidade (PostgreSQL).

*   **Tarefa 1:** Criar pipeline de sincronização entre Inventário de Serviços e Logs de Acesso.
*   **Tarefa 2:** Implementar Aba de Qualidade com monitoramento de erros reportados por órgão.
*   **Tarefa 3:** Desenvolver Aba de Satisfação com cálculo de Índice CSAT (1-5 estrelas).
*   **Tarefa 4:** Criar Cruzamentos Estratégicos (Satisfação vs. Volume) para priorização de melhorias.
*   **Tarefa 5:** Refinar UX com gráficos de altura dinâmica e containers roláveis para grandes volumes de órgãos.
