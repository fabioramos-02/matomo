-- =============================================================================
-- Views PostgreSQL — Bloco "Cartas de Serviço" | SETDIG / Portal ms.gov.br
-- Criadas para uso exclusivo pelo usuário somente-leitura "painel-sgd"
-- Todos os campos sensíveis (CPF, IP, comentários livres) foram excluídos
-- conforme LGPD e orientação do plano técnico.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 1. vw_cartas_servico
--    Inventário das cartas de serviço sem campos pessoais
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_cartas_servico AS
SELECT
    s.idservico,
    s.titulo_servico,
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
    s.data_criacao_servico,
    s.data_atualizacao_servico,
    s.data_revisao_servico
FROM servico s
LEFT JOIN orgao o ON s.idorgao = o.idorgao;


-- -----------------------------------------------------------------------------
-- 2. vw_cartas_erros
--    Erros reportados nas cartas — sem ip_erro e sem dados de pessoa
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_cartas_erros AS
SELECT
    e.iderroservico,
    e.idservico,
    o.siglaorgao,
    o.nome_orgao,
    e.conteudo,
    e.atendido,
    e.corrigido_erro,
    e.reportado_erro,
    e.resolucao_erro,
    e.data_criacao_erro,
    e.data_atualizacao_erro
    -- excluídos: ip_erro, idpessoa e qualquer dado identificável
FROM erroservico e
LEFT JOIN servico s ON e.idservico = s.idservico
LEFT JOIN orgao o ON s.idorgao = o.idorgao;


-- -----------------------------------------------------------------------------
-- 3. vw_cartas_votos
--    Votos de satisfação — sem comentario_voto (LGPD)
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_cartas_votos AS
SELECT
    v.id_voto,
    v.idservico,
    v.data_voto,
    v.avaliacao_voto_servico
    -- excluídos: comentario_voto, idpessoa e qualquer dado identificável
FROM votoservico v;


-- -----------------------------------------------------------------------------
-- 4. vw_cartas_avaliacao_info
--    Avaliações de qualidade da informação da carta
-- -----------------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_cartas_avaliacao_info AS
SELECT
    a.id_avaliacao,
    a.idservico,
    a.avaliacao_carta,
    a.data_avaliacao
    -- excluídos: idpessoa e qualquer dado identificável
FROM avaliacaoinformacao a;


-- -----------------------------------------------------------------------------
-- 5. Permissões para o usuário somente-leitura
-- -----------------------------------------------------------------------------
GRANT SELECT ON vw_cartas_servico        TO "painel-sgd";
GRANT SELECT ON vw_cartas_erros          TO "painel-sgd";
GRANT SELECT ON vw_cartas_votos          TO "painel-sgd";
GRANT SELECT ON vw_cartas_avaliacao_info TO "painel-sgd";


-- -----------------------------------------------------------------------------
-- Verificação rápida (rode para confirmar que as views estão funcionando)
-- -----------------------------------------------------------------------------
-- SELECT COUNT(*) FROM vw_cartas_servico;
-- SELECT COUNT(*) FROM vw_cartas_erros;
-- SELECT COUNT(*) FROM vw_cartas_votos;
-- SELECT COUNT(*) FROM vw_cartas_avaliacao_info;
