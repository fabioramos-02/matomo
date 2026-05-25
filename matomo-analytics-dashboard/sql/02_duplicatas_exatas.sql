<<<<<<< HEAD
-- =========================================================================
-- 02_duplicatas_exatas.sql — Cartas de Serviço SETDIG / Portal ms.gov.br
-- Objetivo: listar pares de cartas com MESMO título após normalização.
--           São candidatas de alta confiança a unificação pela CGE-MS.
-- Requisitos: vw_cartas_servico_descricao (ver 01_*.sql); usuário painel-sgd
--             com SELECT. Sem mutação. Apenas SELECT.
-- Última revisão: 2026-05-25
-- =========================================================================

-- -------------------------------------------------------------------------
-- A) Lista clusters de duplicatas (1 linha por título normalizado repetido)
--    Útil para visão geral antes de abrir os pares.
-- -------------------------------------------------------------------------
SELECT
    titulo_normalizado,
    COUNT(*)                                      AS qtd_cartas,
    STRING_AGG(DISTINCT siglaorgao, ', ' ORDER BY siglaorgao) AS orgaos,
    ARRAY_AGG(idservico ORDER BY idservico)       AS idservicos,
    ARRAY_AGG(titulo_servico ORDER BY idservico)  AS titulos_originais
FROM vw_cartas_servico_descricao
WHERE titulo_normalizado <> ''
GROUP BY titulo_normalizado
HAVING COUNT(*) > 1
ORDER BY qtd_cartas DESC, titulo_normalizado ASC;

-- -------------------------------------------------------------------------
-- B) Pares de duplicatas (formato compatível com query de similaridade)
--    Self-join com id_a < id_b evita duplicar par (A,B)=(B,A) e auto-match.
--    score_titulo = 1.0 porque match é exato após normalização.
--    score_descricao calculado por sobreposição simples (caracteres iguais
--    sobre média de comprimento) para dar pista de quão alinhadas estão
--    as descrições — sem depender de pg_trgm.
-- -------------------------------------------------------------------------
WITH pares AS (
    SELECT
        a.idservico                          AS idservico_a,
        b.idservico                          AS idservico_b,
        a.titulo_servico                     AS titulo_a,
        b.titulo_servico                     AS titulo_b,
        1.0::numeric                         AS score_titulo,
        a.descricao                          AS descricao_a,
        b.descricao                          AS descricao_b,
        a.siglaorgao                         AS siglaorgao_a,
        b.siglaorgao                         AS siglaorgao_b,
        a.tema_id                            AS tema_id_a,
        b.tema_id                            AS tema_id_b,
        a.url_servico                        AS url_a,
        b.url_servico                        AS url_b
    FROM vw_cartas_servico_descricao a
    JOIN vw_cartas_servico_descricao b
      ON a.titulo_normalizado = b.titulo_normalizado
     AND a.idservico < b.idservico
    WHERE a.titulo_normalizado <> ''
)
SELECT
    idservico_a,
    idservico_b,
    titulo_a,
    titulo_b,
    score_titulo,
    -- Heurística leve: razão entre comprimentos das descrições (proxy
    -- barato para "estão na mesma ordem de grandeza"). 1.0 = idênticas
    -- em tamanho; perto de 0 = uma muito maior que a outra.
    CASE
        WHEN GREATEST(LENGTH(descricao_a), LENGTH(descricao_b)) = 0 THEN NULL
        ELSE ROUND(
            LEAST(LENGTH(descricao_a), LENGTH(descricao_b))::numeric
            / GREATEST(LENGTH(descricao_a), LENGTH(descricao_b))::numeric,
            3
        )
    END                                       AS score_descricao_tamanho,
    siglaorgao_a,
    siglaorgao_b,
    CASE WHEN tema_id_a = tema_id_b THEN 'mesmo' ELSE 'diferente' END AS tema,
    url_a,
    url_b
FROM pares
ORDER BY siglaorgao_a, siglaorgao_b, titulo_a;

-- -------------------------------------------------------------------------
-- C) Export sugerido (rode no psql do cliente, NÃO no servidor)
-- -------------------------------------------------------------------------
-- \copy (
--   <cole a query B inteira aqui>
-- ) TO 'duplicatas_exatas.csv' WITH (FORMAT csv, HEADER true, DELIMITER ';');
=======
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
>>>>>>> 36dc56c595dae2f391fe62bf8b8ce63ac7a50d5e
