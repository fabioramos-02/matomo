-- =========================================================================
-- 04_planilha_servicos_ativos.sql
-- Objetivo: extrair planilha de cartas de serviço ATIVAS para chefia.
-- Colunas: titulo_carta, nome_orgao, sigla_orgao, descricao_servico, canal
--          (Digital | Híbrido | Presencial), url_servico.
-- Regra de canal:
--   digital = TRUE                                          -> 'Digital'
--   digital = FALSE AND (online = TRUE OR agendavel = TRUE) -> 'Híbrido'
--   demais                                                  -> 'Presencial'
-- Requisitos: vw_cartas_servico_descricao (01_*.sql) e usuário com SELECT.
-- Sem mutação. Idempotente.
-- =========================================================================

SELECT
    v.titulo_servico                                          AS titulo_carta,
    v.nome_orgao,
    v.siglaorgao                                              AS sigla_orgao,
    v.descricao                                               AS descricao_servico,
    CASE
        WHEN v.digital = TRUE                                  THEN 'Digital'
        WHEN v.digital = FALSE
             AND (v.online = TRUE OR v.agendavel = TRUE)       THEN 'Híbrido'
        ELSE 'Presencial'
    END                                                       AS canal,
    v.url_servico
FROM vw_cartas_servico_descricao v
WHERE v.servico_ativo = TRUE
ORDER BY v.nome_orgao, v.titulo_servico;

-- -------------------------------------------------------------------------
-- Export CSV — rodar no psql do cliente (com VPN ativa):
-- -------------------------------------------------------------------------
-- \copy (
--   SELECT
--       v.titulo_servico                                       AS titulo_carta,
--       v.nome_orgao,
--       v.siglaorgao                                           AS sigla_orgao,
--       v.descricao                                            AS descricao_servico,
--       CASE
--           WHEN v.digital = TRUE                              THEN 'Digital'
--           WHEN v.digital = FALSE
--                AND (v.online = TRUE OR v.agendavel = TRUE)   THEN 'Híbrido'
--           ELSE 'Presencial'
--       END                                                    AS canal,
--       v.url_servico
--   FROM vw_cartas_servico_descricao v
--   WHERE v.servico_ativo = TRUE
--   ORDER BY v.nome_orgao, v.titulo_servico
-- ) TO 'planilha_servicos_ativos.csv'
--   WITH (FORMAT csv, HEADER true, DELIMITER ';', ENCODING 'UTF8');

-- -------------------------------------------------------------------------
-- Resumo de canais (sanity check):
-- -------------------------------------------------------------------------
-- SELECT
--     CASE
--         WHEN digital = TRUE                              THEN 'Digital'
--         WHEN digital = FALSE
--              AND (online = TRUE OR agendavel = TRUE)     THEN 'Híbrido'
--         ELSE 'Presencial'
--     END AS canal,
--     COUNT(*) AS qtd
-- FROM vw_cartas_servico_descricao
-- WHERE servico_ativo = TRUE
-- GROUP BY 1
-- ORDER BY 2 DESC;
