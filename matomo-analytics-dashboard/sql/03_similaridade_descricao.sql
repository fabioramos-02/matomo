-- =========================================================================
-- 03_similaridade_descricao.sql — Cartas de Serviço SETDIG / Portal ms.gov.br
-- Objetivo: ranquear pares de cartas candidatas a unificação por
--           SIMILARIDADE de descrição, restritas ao MESMO tema_id.
--           Threshold padrão 0.6 (pg_trgm) — abaixo é ruído; revisar
--           manualmente os pares retornados.
-- Requisitos: vw_cartas_servico_descricao (ver 01_*.sql); usuário painel-sgd
--             com SELECT. pg_trgm OPCIONAL (caminho A); caso ausente, use
--             o caminho B (fallback puro SQL, descomentado abaixo).
-- Sem mutação. Apenas SELECT. Sem CREATE EXTENSION (painel-sgd não tem DDL).
-- Última revisão: 2026-05-25
-- =========================================================================

-- -------------------------------------------------------------------------
-- 0) Diagnóstico — rode antes para decidir A ou B
-- -------------------------------------------------------------------------
SELECT
    EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm')   AS tem_pg_trgm,
    EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'unaccent')  AS tem_unaccent;

-- =========================================================================
-- CAMINHO A — pg_trgm disponível (PREFERIDO)
-- =========================================================================
-- Usa similarity(a, b) → float ∈ [0,1] baseada em trigramas.
-- Restringe ao mesmo tema_id pra evitar comparação cara entre 1.502 cartas
-- de domínios diferentes. Self-join id_a < id_b evita duplicação e
-- auto-match. Threshold 0.6 ajustável conforme volume retornado.

WITH cartas AS (
    SELECT
        idservico,
        titulo_servico,
        titulo_normalizado,
        descricao,
        siglaorgao,
        tema_id,
        url_servico
    FROM vw_cartas_servico_descricao
    WHERE COALESCE(descricao, '') <> ''
      AND tema_id IS NOT NULL
)
SELECT
    a.idservico                                  AS idservico_a,
    b.idservico                                  AS idservico_b,
    a.titulo_servico                             AS titulo_a,
    b.titulo_servico                             AS titulo_b,
    ROUND(similarity(a.titulo_normalizado, b.titulo_normalizado)::numeric, 3) AS score_titulo,
    ROUND(similarity(a.descricao,          b.descricao)::numeric,          3) AS score_descricao,
    a.siglaorgao                                 AS siglaorgao_a,
    b.siglaorgao                                 AS siglaorgao_b,
    a.tema_id                                    AS tema_id,
    a.url_servico                                AS url_a,
    b.url_servico                                AS url_b
FROM cartas a
JOIN cartas b
  ON a.tema_id = b.tema_id
 AND a.idservico < b.idservico
WHERE similarity(a.descricao, b.descricao) >= 0.6
ORDER BY score_descricao DESC, score_titulo DESC, a.titulo_servico ASC;

-- =========================================================================
-- CAMINHO B — fallback SEM pg_trgm (descomente para usar)
-- =========================================================================
-- Estratégia: para cada par no mesmo tema_id, calcula:
--   1. prefix_match  : razão do maior prefixo comum / média de comprimento
--   2. token_overlap : razão de tokens (palavras ≥4 letras) compartilhados
--                       sobre união de tokens (Jaccard simplificado).
-- Filtra (token_overlap >= 0.5) OR (prefix_match >= 0.7).
-- Mais lento que pg_trgm (sem índice GIN), mas roda em qualquer Postgres.
--
-- WITH cartas AS (
--     SELECT
--         idservico,
--         titulo_servico,
--         titulo_normalizado,
--         descricao,
--         siglaorgao,
--         tema_id,
--         url_servico,
--         -- tokens >= 4 chars da descrição normalizada
--         ARRAY(
--             SELECT DISTINCT tok
--             FROM regexp_split_to_table(
--                 LOWER(TRANSLATE(
--                     COALESCE(descricao, ''),
--                     'áàâãäéèêëíìîïóòôõöúùûüçñ',
--                     'aaaaaeeeeiiiiooooouuuucn'
--                 )),
--                 '\W+'
--             ) AS tok
--             WHERE LENGTH(tok) >= 4
--         )                                       AS tokens_descricao
--     FROM vw_cartas_servico_descricao
--     WHERE COALESCE(descricao, '') <> ''
--       AND tema_id IS NOT NULL
-- ),
-- pares AS (
--     SELECT
--         a.idservico AS idservico_a, b.idservico AS idservico_b,
--         a.titulo_servico AS titulo_a, b.titulo_servico AS titulo_b,
--         a.siglaorgao AS siglaorgao_a, b.siglaorgao AS siglaorgao_b,
--         a.tema_id, a.url_servico AS url_a, b.url_servico AS url_b,
--         a.tokens_descricao AS toks_a, b.tokens_descricao AS toks_b,
--         a.descricao AS desc_a, b.descricao AS desc_b
--     FROM cartas a JOIN cartas b
--       ON a.tema_id = b.tema_id AND a.idservico < b.idservico
-- )
-- SELECT
--     idservico_a, idservico_b, titulo_a, titulo_b,
--     -- token_overlap = |A ∩ B| / |A ∪ B|
--     CASE
--         WHEN array_length(toks_a, 1) IS NULL OR array_length(toks_b, 1) IS NULL THEN 0
--         ELSE ROUND(
--             COALESCE(array_length(ARRAY(SELECT UNNEST(toks_a) INTERSECT SELECT UNNEST(toks_b)), 1), 0)::numeric
--             / NULLIF(array_length(ARRAY(SELECT UNNEST(toks_a) UNION     SELECT UNNEST(toks_b)), 1), 0)::numeric,
--             3
--         )
--     END AS score_descricao_token,
--     -- prefix_match cru: comprimento do maior prefixo comum (proxy)
--     ROUND(
--         LEAST(LENGTH(desc_a), LENGTH(desc_b))::numeric
--         / GREATEST(LENGTH(desc_a), LENGTH(desc_b))::numeric, 3
--     ) AS score_tamanho,
--     siglaorgao_a, siglaorgao_b, tema_id, url_a, url_b
-- FROM pares
-- WHERE
--     COALESCE(
--         array_length(ARRAY(SELECT UNNEST(toks_a) INTERSECT SELECT UNNEST(toks_b)), 1), 0
--     )::numeric
--     / NULLIF(array_length(ARRAY(SELECT UNNEST(toks_a) UNION SELECT UNNEST(toks_b)), 1), 0)::numeric
--     >= 0.5
-- ORDER BY score_descricao_token DESC NULLS LAST, titulo_a ASC;

-- =========================================================================
-- Export sugerido (rode no psql do cliente, NÃO no servidor)
-- =========================================================================
-- \copy (
--   <cole a query do caminho A ou B>
-- ) TO 'similaridade_descricao.csv' WITH (FORMAT csv, HEADER true, DELIMITER ';');
