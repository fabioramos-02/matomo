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
