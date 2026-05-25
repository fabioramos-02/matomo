-- =============================================================================
-- 01_view_cartas_servico_descricao.sql
-- Cartas de Serviço — SETDIG / Portal ms.gov.br
--
-- Objetivo:
--   Estender vw_cartas_servico (docs/views_postgresql.sql) com:
--     - descricao (text)               vinda de gerenciamento_servicos
--     - url_servico (text)             montada como
--                                      https://www.ms.gov.br/{slug_categoria}/{slug_servico}
--     - url_status (text)              'ok' | 'incompleta' (slug_categoria NULL/vazio)
--
-- Motivação:
--   Permitir análise de duplicidade de cartas (mesmo título e descrição similar)
--   para reduzir o nº de cartas que CGE-MS aprova e que o cidadão pesquisa.
--
-- Requisitos:
--   - PostgreSQL >= 12
--   - Executor com SELECT em gerenciamento_servicos, gerenciamento_orgaos,
--     gerenciamento_temas
--   - Privilégio para CREATE OR REPLACE VIEW (DBA / dono do schema)
--
-- LGPD: nenhum dado pessoal exposto (mantém padrão das views existentes).
-- Última revisão: 2026-05-25
-- =============================================================================

CREATE OR REPLACE VIEW vw_cartas_servico_descricao AS
SELECT
    s.idservico,
    s.titulo_servico,
    s.slug                                                AS slug_servico,
    t.slug                                                AS slug_categoria,
    s.nome_popular,
    o.siglaorgao,
    o.nome_orgao,
    s.servico_ativo,
    s.digital,
    s.online,
    s.agendavel,
    s.acesso_externo,
    s.custo,
    s.tempo,
    s.tipo_tempo,
    s.descricao,
    s.tema_id,
    -- URL pública do portal — preenche placeholder quando categoria ausente
    'https://www.ms.gov.br/'
        || COALESCE(NULLIF(t.slug, ''), '_sem-categoria_')
        || '/'
        || COALESCE(NULLIF(s.slug, ''), '_sem-slug_')        AS url_servico,
    CASE
        WHEN t.slug IS NULL OR t.slug = '' THEN 'incompleta'
        WHEN s.slug IS NULL OR s.slug = '' THEN 'incompleta'
        ELSE 'ok'
    END                                                   AS url_status,
    s.data_criacao_servico,
    s.data_atualizacao_servico
FROM gerenciamento_servicos s
LEFT JOIN gerenciamento_orgaos o ON s.idorgao = o.idorgao
LEFT JOIN gerenciamento_temas  t ON t.id      = s.tema_id;

-- Permissão somente leitura para o painel
GRANT SELECT ON vw_cartas_servico_descricao TO "painel-sgd";

-- -----------------------------------------------------------------------------
-- Verificação rápida
-- -----------------------------------------------------------------------------
-- SELECT COUNT(*) FROM vw_cartas_servico_descricao;
-- SELECT COUNT(*) FILTER (WHERE url_status = 'incompleta') AS sem_url
--   FROM vw_cartas_servico_descricao;
-- SELECT titulo_servico, url_servico, siglaorgao
--   FROM vw_cartas_servico_descricao
--   ORDER BY titulo_servico
--   LIMIT 20;

-- -----------------------------------------------------------------------------
-- Export para CSV via psql (rode na máquina remota, com VPN ativa)
-- -----------------------------------------------------------------------------
-- \copy (SELECT * FROM vw_cartas_servico_descricao)
--   TO 'cartas_servico_descricao.csv'
--   WITH (FORMAT csv, HEADER true, DELIMITER ';', ENCODING 'UTF8');
