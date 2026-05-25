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
