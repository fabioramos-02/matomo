<<<<<<< HEAD
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
=======
-- =============================================================================
-- 03_similaridade_descricao.sql
-- Cartas de Serviço — SETDIG / Portal ms.gov.br
--
-- Objetivo:
--   Ranquear pares de cartas candidatas a UNIFICAÇÃO com base em:
--     - similaridade de TÍTULO normalizado
--     - similaridade de DESCRIÇÃO
--   Restrito ao mesmo tema_id para evitar matches espúrios entre áreas
--   distintas (ex.: "Inscrição" em Educação x Saúde).
--
-- Caminhos:
--   (A) pg_trgm instalado  -> usa similarity() (Jaccard de trigramas).
--   (B) pg_trgm AUSENTE    -> usa heurística: prefixo + tamanho relativo
--                             + match exato de 1ª frase (fallback).
--
-- Threshold default:
--   score_titulo     >= 0.70   (títulos quase iguais)
--   score_descricao  >= 0.60   (descrições semanticamente próximas)
--   Ajuste conforme volume de candidatas retornadas.
--
-- Requisitos:
--   - View vw_cartas_servico_descricao (script 01).
--   - Recomendado: CREATE EXTENSION pg_trgm; (DBA, uma única vez)
--
-- Última revisão: 2026-05-25
-- =============================================================================

-- Diagnóstico
SELECT
    EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm')  AS has_pg_trgm,
    EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'unaccent') AS has_unaccent;


-- =============================================================================
-- CAMINHO (A) — com pg_trgm  [RECOMENDADO]
-- =============================================================================
-- Rode UMA VEZ no banco (precisa de DBA):
--   CREATE EXTENSION IF NOT EXISTS pg_trgm;
--
-- (Opcional, para acelerar em produção)
--   CREATE INDEX IF NOT EXISTS idx_servicos_titulo_trgm
--     ON gerenciamento_servicos USING gin (titulo_servico gin_trgm_ops);
--   CREATE INDEX IF NOT EXISTS idx_servicos_descricao_trgm
--     ON gerenciamento_servicos USING gin (descricao      gin_trgm_ops);
-- -----------------------------------------------------------------------------

WITH base AS (
    SELECT
        idservico,
        titulo_servico,
        descricao,
        siglaorgao,
        nome_orgao,
        tema_id,
        url_servico,
        servico_ativo,
        lower(
            regexp_replace(
                translate(
                    titulo_servico,
                    'áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ',
                    'aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC'
                ),
                '[[:punct:]]+', ' ', 'g'
            )
        ) AS titulo_norm,
        lower(
            translate(
                descricao,
                'áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ',
                'aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC'
            )
        ) AS descricao_norm
    FROM vw_cartas_servico_descricao
)
SELECT
    a.idservico         AS idservico_a,
    b.idservico         AS idservico_b,
    a.titulo_servico    AS titulo_a,
    b.titulo_servico    AS titulo_b,
    ROUND(similarity(a.titulo_norm,    b.titulo_norm)::numeric,    3) AS score_titulo,
    ROUND(similarity(a.descricao_norm, b.descricao_norm)::numeric, 3) AS score_descricao,
    a.siglaorgao        AS siglaorgao_a,
    b.siglaorgao        AS siglaorgao_b,
    a.nome_orgao        AS nome_orgao_a,
    b.nome_orgao        AS nome_orgao_b,
    a.url_servico       AS url_a,
    b.url_servico       AS url_b,
    a.servico_ativo     AS ativo_a,
    b.servico_ativo     AS ativo_b,
    a.tema_id
FROM base a
JOIN base b
  ON a.tema_id    = b.tema_id          -- só dentro do mesmo tema
 AND a.idservico  < b.idservico         -- pares únicos
WHERE similarity(a.titulo_norm,    b.titulo_norm)    >= 0.70
   OR similarity(a.descricao_norm, b.descricao_norm) >= 0.60
ORDER BY
    GREATEST(
        similarity(a.titulo_norm,    b.titulo_norm),
        similarity(a.descricao_norm, b.descricao_norm)
    ) DESC,
    a.tema_id, a.idservico, b.idservico;


-- =============================================================================
-- CAMINHO (B) — FALLBACK sem pg_trgm
-- =============================================================================
-- Use SE o diagnóstico acima retornou has_pg_trgm = false E não há DBA
-- disponível para instalar a extensão.
--
-- Heurística:
--   - Mesmo tema_id
--   - Mesmas N primeiras palavras do título (após normalização)
--   - Tamanho da descrição em janela de ±30%
--   - Match exato da 1ª frase da descrição (até o primeiro ".")
-- -----------------------------------------------------------------------------
/*
WITH base AS (
    SELECT
        idservico,
        titulo_servico,
        descricao,
        siglaorgao,
        nome_orgao,
        tema_id,
        url_servico,
        servico_ativo,
        lower(
            regexp_replace(
                translate(titulo_servico,
                    'áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ',
                    'aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC'),
                '[[:punct:]]+', ' ', 'g')
        ) AS titulo_norm,
        lower(split_part(descricao, '.', 1)) AS primeira_frase,
        length(descricao)                    AS len_desc
    FROM vw_cartas_servico_descricao
),
primeiras_palavras AS (
    SELECT
        idservico,
        titulo_servico,
        descricao,
        siglaorgao,
        nome_orgao,
        tema_id,
        url_servico,
        servico_ativo,
        titulo_norm,
        primeira_frase,
        len_desc,
        array_to_string(
            (string_to_array(trim(titulo_norm), ' '))[1:4],
            ' '
        ) AS prefixo_titulo
    FROM base
)
SELECT
    a.idservico       AS idservico_a,
    b.idservico       AS idservico_b,
    a.titulo_servico  AS titulo_a,
    b.titulo_servico  AS titulo_b,
    a.prefixo_titulo,
    a.primeira_frase  AS primeira_frase_a,
    b.primeira_frase  AS primeira_frase_b,
    (a.primeira_frase = b.primeira_frase)                            AS match_primeira_frase,
    abs(a.len_desc - b.len_desc)::float / GREATEST(a.len_desc, b.len_desc, 1)
                                                                     AS dif_tamanho_rel,
    a.siglaorgao      AS siglaorgao_a,
    b.siglaorgao      AS siglaorgao_b,
    a.url_servico     AS url_a,
    b.url_servico     AS url_b,
    a.tema_id
FROM primeiras_palavras a
JOIN primeiras_palavras b
  ON a.tema_id        = b.tema_id
 AND a.prefixo_titulo = b.prefixo_titulo
 AND a.idservico      < b.idservico
WHERE abs(a.len_desc - b.len_desc)::float / GREATEST(a.len_desc, b.len_desc, 1) <= 0.30
   OR a.primeira_frase = b.primeira_frase
ORDER BY a.tema_id, a.prefixo_titulo, a.idservico, b.idservico;
*/

-- -----------------------------------------------------------------------------
-- Export (caminho A)
-- -----------------------------------------------------------------------------
-- \copy (
--   <colar a query do CAMINHO (A) sem o ; final>
-- ) TO 'cartas_similaridade_descricao.csv'
--   WITH (FORMAT csv, HEADER true, DELIMITER ';', ENCODING 'UTF8');
>>>>>>> 36dc56c595dae2f391fe62bf8b8ce63ac7a50d5e
