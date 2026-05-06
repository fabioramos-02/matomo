# Plano de Correção: KeyError 'lat' no Dashboard

## Problema
O arquivo `views/ms_digital/tab3_perfil.py` tenta acessar as colunas `lat` e `lon` de um DataFrame que pode não contê-las (caso de fallback do GA4 para nível Regional ou Global).

## Arquivos Envolvidos
- `utils/ga_data_processor.py`: Onde as colunas são (ou não) criadas.
- `views/ms_digital/tab3_perfil.py`: Onde o erro acontece.

## Passos para Implementação

1.  **Reforçar `utils/ga_data_processor.py`:**
    - Garantir que `lat` e `lon` existam no DataFrame retornado por `process_ga_cities`, mesmo que preenchidas com `NaN`. Isso evita quebras em qualquer componente que consuma este DataFrame.

2.  **Corrigir `views/ms_digital/tab3_perfil.py`:**
    - Adicionar verificação explícita de `lat` e `lon` antes de tentar filtrar o DataFrame para o mapa.
    - Se as colunas não existirem ou estiverem vazias, exibir a mensagem de "Coordenadas não disponíveis" graciosamente.

## Verificação
- Simular um DataFrame sem `lat`/`lon` e garantir que a página carrega sem erro.
- Testar com dados completos para garantir que o mapa continua funcionando.
