<<<<<<< HEAD
-- =========================================================================
-- vw_cartas_servico_descricao — Cartas de Serviço SETDIG / Portal ms.gov.br
-- Objetivo: estende vw_cartas_servico com `descricao`, `url_servico` e
--           `url_status` para alimentar detecção de duplicidade e revisão
--           humana das cartas aprovadas pela CGE-MS.
-- Requisitos: usuário `painel-sgd` com SELECT em gerenciamento_servicos,
--             gerenciamento_orgaos e gerenciamento_temas; permissão de
--             CREATE no schema corrente (caso contrário usar bloco SELECT
--             ad-hoc da seção "Plano B" no final).
-- Sem DDL global. Sem mutação. Idempotente (CREATE OR REPLACE).
-- Última revisão: 2026-05-25
-- =========================================================================

-- -------------------------------------------------------------------------
-- 1) View estendida
--    Mantém todos os campos da view base vw_cartas_servico e acrescenta:
--      - descricao         : texto livre da carta (vem de gerenciamento_servicos)
--      - tema_id           : usado para limitar comparação de similaridade
--                            ao mesmo tema (evita falsos positivos entre
--                            domínios diferentes, ex.: saúde x trânsito)
--      - titulo_normalizado: lowercase + sem acentos + sem pontuação +
--                            espaços colapsados → chave de duplicata exata
--      - url_servico       : URL pública montada conforme padrão do portal
--      - url_status        : 'ok' quando todos os slugs presentes;
--                            'incompleta' quando slug_categoria ausente
-- -------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_cartas_servico_descricao AS
WITH base AS (
    SELECT
        s.idservico,
        s.titulo_servico,
        s.slug                                          AS slug_servico,
        t.slug                                          AS slug_categoria,
        s.tema_id,
        s.nome_popular,
        o.siglaorgao,
        o.nome_orgao,
        s.descricao,
        s.servico_ativo,
        s.digital,
        s.online,
        s.agendavel,
        s.acesso_externo,
        s.custo,
        s.tempo,
        s.tipo_tempo,
        s.data_criacao_servico,
        s.data_atualizacao_servico
    FROM gerenciamento_servicos s
    LEFT JOIN gerenciamento_orgaos o ON s.idorgao = o.idorgao
    LEFT JOIN gerenciamento_temas  t ON t.id      = s.tema_id
)
SELECT
    b.idservico,
    b.titulo_servico,
    b.slug_servico,
    b.slug_categoria,
    b.tema_id,
    b.nome_popular,
    b.siglaorgao,
    b.nome_orgao,
    b.descricao,
    b.servico_ativo,
    b.digital,
    b.online,
    b.agendavel,
    b.acesso_externo,
    b.custo,
    b.tempo,
    b.tipo_tempo,
    b.data_criacao_servico,
    b.data_atualizacao_servico,

    -- Normalização do título para match exato:
    --   1. lowercase
    --   2. translate() remove acentos pt-BR comuns (fallback caso unaccent ausente)
    --   3. regexp_replace tira pontuação e símbolos
    --   4. colapsa múltiplos espaços e faz trim
    TRIM(
        REGEXP_REPLACE(
            REGEXP_REPLACE(
                TRANSLATE(
                    LOWER(COALESCE(b.titulo_servico, '')),
                    'áàâãäéèêëíìîïóòôõöúùûüçñÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇÑ',
                    'aaaaaeeeeiiiiooooouuuucnaaaaaeeeeiiiiooooouuuucn'
                ),
                '[[:punct:]]+', ' ', 'g'
            ),
            '\s+', ' ', 'g'
        )
    )                                                   AS titulo_normalizado,

    -- URL pública: padrão https://www.ms.gov.br/{slug_categoria}/{slug_servico}
    -- Quando slug_categoria é NULL/vazio, usa placeholder _sem-categoria_
    -- e a coluna url_status sinaliza para revisão humana.
    'https://www.ms.gov.br/'
        || COALESCE(NULLIF(b.slug_categoria, ''), '_sem-categoria_')
        || '/'
        || COALESCE(NULLIF(b.slug_servico,   ''), '_sem-slug_')
                                                        AS url_servico,
    CASE
        WHEN COALESCE(NULLIF(b.slug_categoria, ''), '') = '' THEN 'incompleta'
        WHEN COALESCE(NULLIF(b.slug_servico,   ''), '') = '' THEN 'incompleta'
        ELSE 'ok'
    END                                                 AS url_status
FROM base b;

-- -------------------------------------------------------------------------
-- 2) Permissão (somente se o owner da view tiver poder de GRANT)
-- -------------------------------------------------------------------------
GRANT SELECT ON vw_cartas_servico_descricao TO "painel-sgd";

-- -------------------------------------------------------------------------
-- 3) Verificação rápida
-- -------------------------------------------------------------------------
-- SELECT COUNT(*) FROM vw_cartas_servico_descricao;
-- SELECT url_status, COUNT(*) FROM vw_cartas_servico_descricao GROUP BY 1;

-- -------------------------------------------------------------------------
-- 4) Plano B — sem CREATE VIEW
--    Caso painel-sgd não tenha CREATE no schema corrente, transforme o
--    bloco CREATE OR REPLACE VIEW ... AS acima em um WITH cte_cartas AS (...)
--    e cole no início das queries 02 e 03 substituindo as referências a
--    vw_cartas_servico_descricao por cte_cartas.
-- -------------------------------------------------------------------------
=======
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
>>>>>>> 36dc56c595dae2f391fe62bf8b8ce63ac7a50d5e
