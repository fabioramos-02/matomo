-- =============================================================================
-- 02_duplicatas_exatas.sql
-- Cartas de Serviço — SETDIG / Portal ms.gov.br
--
-- Objetivo:
--   Identificar pares de cartas com TÍTULO IDÊNTICO após normalização
--   (lowercase + sem acentos + colapso de espaços + remoção de pontuação).
--   Saída pronta para revisão humana decidir unificação.
--
-- Estratégia:
--   1) Normaliza título via CTE (com fallback caso `unaccent` não esteja instalado).
--   2) Self-join com id_a < id_b para retornar pares únicos (sem A↔B + B↔A).
--   3) Inclui colunas-chave (URLs, órgãos, status) para o analista.
--
-- Requisitos:
--   - View vw_cartas_servico_descricao (script 01).
--   - Opcional: extensão `unaccent` (melhora a normalização). Sem ela,
--     usa translate() manual para acentos pt-BR comuns.
--
-- Última revisão: 2026-05-25
-- =============================================================================

-- Diagnóstico de extensões (apenas informa — não falha)
SELECT
    EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'unaccent') AS has_unaccent,
    EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm')  AS has_pg_trgm;

-- -----------------------------------------------------------------------------
-- Query principal — duplicatas exatas por título normalizado
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
        url_status,
        servico_ativo,
        -- Normalização: lowercase + remoção de acentos (translate manual pt-BR)
        --              + colapso de espaços + remoção de pontuação
        regexp_replace(
            regexp_replace(
                lower(
                    translate(
                        titulo_servico,
                        'áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ',
                        'aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC'
                    )
                ),
                '[[:punct:]]', ' ', 'g'
            ),
            '\s+', ' ', 'g'
        ) AS titulo_norm
    FROM vw_cartas_servico_descricao
),
grupos AS (
    SELECT
        titulo_norm,
        COUNT(*) AS qtd
    FROM base
    GROUP BY titulo_norm
    HAVING COUNT(*) > 1
)
SELECT
    a.idservico        AS idservico_a,
    b.idservico        AS idservico_b,
    a.titulo_norm,
    a.titulo_servico   AS titulo_a,
    b.titulo_servico   AS titulo_b,
    a.siglaorgao       AS siglaorgao_a,
    b.siglaorgao       AS siglaorgao_b,
    a.url_servico      AS url_a,
    b.url_servico      AS url_b,
    a.servico_ativo    AS ativo_a,
    b.servico_ativo    AS ativo_b,
    a.tema_id          AS tema_id_a,
    b.tema_id          AS tema_id_b,
    length(a.descricao) AS len_descricao_a,
    length(b.descricao) AS len_descricao_b,
    g.qtd              AS qtd_no_cluster
FROM base a
JOIN base b
  ON a.titulo_norm = b.titulo_norm
 AND a.idservico   < b.idservico
JOIN grupos g
  ON g.titulo_norm = a.titulo_norm
ORDER BY g.qtd DESC, a.titulo_norm ASC, a.idservico, b.idservico;

-- -----------------------------------------------------------------------------
-- Export para CSV
-- -----------------------------------------------------------------------------
-- \copy (
--   <colar a query acima inteira sem o ; final>
-- ) TO 'cartas_duplicatas_exatas.csv'
--   WITH (FORMAT csv, HEADER true, DELIMITER ';', ENCODING 'UTF8');
