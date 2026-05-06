# Graph Report - .  (2026-05-05)

## Corpus Check
- Corpus is ~8,461 words - fits in a single context window. You may not need a graph.

## Summary
- 155 nodes · 220 edges · 7 communities detected
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 36 edges (avg confidence: 0.82)
- Token cost: 67,202 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Matomo Views and Loaders|Matomo Views and Loaders]]
- [[_COMMUNITY_GA4 Data Loaders|GA4 Data Loaders]]
- [[_COMMUNITY_Core Architecture and Docs|Core Architecture and Docs]]
- [[_COMMUNITY_GA4 API Methods|GA4 API Methods]]
- [[_COMMUNITY_Matomo API Methods|Matomo API Methods]]
- [[_COMMUNITY_GA4 User Journey View|GA4 User Journey View]]
- [[_COMMUNITY_Project Documentation|Project Documentation]]

## God Nodes (most connected - your core abstractions)
1. `GoogleAnalyticsAPI` - 18 edges
2. `MatomoAPI` - 17 edges
3. `app.py - Dashboard Entry Point` - 16 edges
4. `MatomoAPI - Matomo Client` - 8 edges
5. `data_processor.py - Matomo Data Processor` - 8 edges
6. `data_loaders.py - Matomo Cached Loaders` - 7 edges
7. `render_tab4_jornada()` - 6 edges
8. `ga_data_loaders.py - GA4 Cached Loaders` - 5 edges
9. `Portal Tab4 - Fluxo de Navegacao` - 5 edges
10. `load_transitions_data()` - 3 edges

## Surprising Connections (you probably didn't know these)
- `No-Database Design: Real-time API + st.cache_data` --rationale_for--> `app.py - Dashboard Entry Point`  [INFERRED]
  docs/plano_implementacao.md → app.py
- `Regex-based Service Card Detection` --rationale_for--> `data_processor.py - Matomo Data Processor`  [INFERRED]
  docs/limitacoes.md → utils/data_processor.py
- `get_api()` --calls--> `MatomoAPI`  [INFERRED]
  app.py → api/matomo_client.py
- `get_ga_api()` --calls--> `GoogleAnalyticsAPI`  [INFERRED]
  app.py → api/google_analytics_client.py
- `Limitacoes e Desafios Tecnicos` --references--> `MatomoAPI - Matomo Client`  [EXTRACTED]
  docs/limitacoes.md → api/matomo_client.py

## Hyperedges (group relationships)
- **Matomo Data Pipeline: Client to Loaders to Processor to View** — api_matomo_client, utils_data_loaders, utils_data_processor, views_portal_tab1_perfil, views_portal_tab2_busca, views_portal_tab3_servicos, views_portal_tab4_jornada [EXTRACTED 1.00]
- **GA4 Data Pipeline: Client to Loaders to Processor to View** — api_google_analytics_client, utils_ga_data_loaders, utils_ga_data_processor, views_ms_digital_tab1_overview, views_ms_digital_tab2_funcionalidades, views_ms_digital_tab3_perfil, views_ms_digital_tab4_jornada [EXTRACTED 1.00]
- **Config Injection: config.py provides secrets to all API clients** — config_config, api_matomo_client, api_google_analytics_client, app_app [EXTRACTED 1.00]

## Communities (15 total, 3 thin omitted)

### Community 0 - "Matomo Views and Loaders"
Cohesion: 0.07
Nodes (28): render_tab3_servicos(), _range_is_long(), _render_tab4_ga4(), render_tab4_jornada(), load_devices_data(), load_entry_pages_data(), load_geography_data(), load_outlinks_data() (+20 more)

### Community 1 - "GA4 Data Loaders"
Cohesion: 0.08
Nodes (32): load_ga_country_map(), load_ga_devices(), load_ga_events(), load_ga_external_links(), load_ga_funnel(), load_ga_geography(), load_ga_overview(), load_ga_platform() (+24 more)

### Community 2 - "Core Architecture and Docs"
Cohesion: 0.14
Nodes (25): GoogleAnalyticsAPI - GA4 Client, MatomoAPI - Matomo Client, app.py - Dashboard Entry Point, config.py - Configuration and Secrets, Documentacao Funcional da Aplicacao, Limitacoes e Desafios Tecnicos, Plano de Implementacao, get_api() (+17 more)

### Community 3 - "GA4 API Methods"
Cohesion: 0.13
Nodes (7): GoogleAnalyticsAPI, Funcionalidades internas: use_feature × melhor dimensão de tela., Tendência temporal: use_feature por melhor dimensão + date., Links externos clicados: linkText + eventCount + activeUsers (evento click outbo, Tenta buscar dados geográficos em níveis decrescentes de complexidade., Todos os eventos (sem filtro) para visualização de funil., Retorna (dim_name, rows) para a primeira dim que tem dados de use_feature.

## Knowledge Gaps
- **24 isolated node(s):** `Tenta buscar dados geográficos em níveis decrescentes de complexidade.`, `Todos os eventos (sem filtro) para visualização de funil.`, `Retorna (dim_name, rows) para a primeira dim que tem dados de use_feature.`, `Funcionalidades internas: use_feature × melhor dimensão de tela.`, `Tendência temporal: use_feature por melhor dimensão + date.` (+19 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ga_data_processor.py - GA4 Data Processor` connect `Core Architecture and Docs` to `GA4 Data Loaders`?**
  _High betweenness centrality (0.297) - this node is a cross-community bridge._
- **Why does `data_processor.py - Matomo Data Processor` connect `Core Architecture and Docs` to `Matomo Views and Loaders`?**
  _High betweenness centrality (0.291) - this node is a cross-community bridge._
- **Why does `GoogleAnalyticsAPI` connect `GA4 API Methods` to `Core Architecture and Docs`?**
  _High betweenness centrality (0.235) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `app.py - Dashboard Entry Point` (e.g. with `No-Database Design: Real-time API + st.cache_data` and `Dual Data Source Architecture (Matomo + GA4)`) actually correct?**
  _`app.py - Dashboard Entry Point` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `data_processor.py - Matomo Data Processor` (e.g. with `Regex-based Service Card Detection` and `ga_data_processor.py - GA4 Data Processor`) actually correct?**
  _`data_processor.py - Matomo Data Processor` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Tenta buscar dados geográficos em níveis decrescentes de complexidade.`, `Todos os eventos (sem filtro) para visualização de funil.`, `Retorna (dim_name, rows) para a primeira dim que tem dados de use_feature.` to the rest of the system?**
  _24 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Matomo Views and Loaders` be split into smaller, more focused modules?**
  _Cohesion score 0.07 - nodes in this community are weakly interconnected._