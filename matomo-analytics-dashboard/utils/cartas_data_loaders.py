"""
Loaders de dados para o bloco Cartas de Serviço.

Pipeline de dados:
    banco PostgreSQL (admin_prd)
        └── gerenciamento_servicos        → inventário das cartas
        └── gerenciamento_orgaos          → cadastro de órgãos
        └── gerenciamento_servicoserros   → erros reportados nas cartas
        └── gerenciamento_votosservicos   → votos de satisfação

Princípio de Responsabilidade Única:
    - Cada função lê UMA fonte e retorna UM DataFrame normalizado.
    - Nenhum loader faz transformação de negócio — isso fica nas views.
    - Fallback automático para dados mock se o banco estiver indisponível.
"""

import os
import pandas as pd
import streamlit as st
import random
from datetime import date, timedelta

from utils.pg_connector import run_query, is_db_available


# =========================================================================== #
# QUERIES — nomes reais das tabelas do banco admin_prd                        #
# =========================================================================== #

_SQL_INVENTORY = """
SELECT
    s.id                        AS idservico,
    s.titulo                    AS titulo_servico,
    s.slug                      AS slug_servico,
    t.slug                      AS slug_categoria,
    s.nome_popular,
    o.sigla                     AS siglaorgao,
    o.nome                      AS nome_orgao,
    s.ativo                     AS servico_ativo,
    s.digital,
    s.online,
    s.agendavel,
    s.acesso_externo,
    s.custo,
    s.tempo,
    s.tipo_tempo,
    s.created_at                AS data_criacao_servico,
    s.updated_at                AS data_atualizacao_servico
FROM public.gerenciamento_servicos s
INNER JOIN public.gerenciamento_setor st ON st.id = s.setor_id
INNER JOIN public.gerenciamento_orgaos o ON o.id = st.orgao_id
LEFT JOIN public.gerenciamento_temas t ON t.id = s.tema_id
ORDER BY s.titulo;
"""

_SQL_ERRORS = """
SELECT
    e.id                        AS iderroservico,
    e.servico_id                AS idservico,
    s.titulo                    AS titulo_servico,
    s.slug                      AS slug_servico,
    t_cat.slug                  AS slug_categoria,
    o.sigla                     AS siglaorgao,
    o.nome                      AS nome_orgao,
    e.conteudo,
    e.atendido,
    e.resolucao                 AS resolucao_erro,
    CASE WHEN e.corrigido_por_id IS NOT NULL THEN TRUE ELSE FALSE END AS corrigido_erro,
    e.created_at                AS data_criacao_erro,
    e.updated_at                AS data_atualizacao_erro
FROM public.gerenciamento_servicoserros e
INNER JOIN public.gerenciamento_servicos s ON s.id = e.servico_id
INNER JOIN public.gerenciamento_setor st ON st.id = s.setor_id
INNER JOIN public.gerenciamento_orgaos o ON o.id = st.orgao_id
LEFT JOIN public.gerenciamento_temas t_cat ON t_cat.id = s.tema_id
ORDER BY e.created_at DESC;
"""

_SQL_VOTES = """
SELECT
    v.id                        AS id_voto,
    v.servicos_id               AS idservico,
    s.titulo                    AS titulo_servico,
    o.sigla                     AS siglaorgao,
    o.nome                      AS nome_orgao,
    v.created_at                AS data_voto,
    v.avaliacao                 AS avaliacao_voto_servico
    -- excluídos: v.comentario (LGPD), v.ip, v.user_id
FROM public.gerenciamento_votosservicos v
INNER JOIN public.gerenciamento_servicos s ON s.id = v.servicos_id
INNER JOIN public.gerenciamento_setor st ON st.id = s.setor_id
INNER JOIN public.gerenciamento_orgaos o ON o.id = st.orgao_id
ORDER BY v.created_at DESC;
"""



# =========================================================================== #
# LOADERS PÚBLICOS                                                             #
# =========================================================================== #

def _load_from_csv(filename: str) -> pd.DataFrame:
    path = os.path.join("exports", filename)
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            # Try to convert datetime columns if they exist
            for col in df.columns:
                if "data_" in col or "created_at" in col or "updated_at" in col:
                    df[col] = pd.to_datetime(df[col], errors='ignore')
            return df
        except Exception as e:
            st.error(f"⚠️ Erro ao ler CSV de fallback ({path}): {e}")
            return pd.DataFrame()
    else:
        st.warning(f"⚠️ Sem conexão com o banco e arquivo '{path}' não encontrado. Execute 'python run_export.py' para gerar os dados.")
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def load_service_cards_inventory() -> pd.DataFrame:
    """Inventário de cartas: gerenciamento_servicos × gerenciamento_orgaos."""
    if not is_db_available():
        return _load_from_csv("cartas_inventory.csv")
    df = run_query(_SQL_INVENTORY)
    return df if not df.empty else _load_from_csv("cartas_inventory.csv")


@st.cache_data(ttl=3600, show_spinner=False)
def load_service_cards_errors() -> pd.DataFrame:
    """Erros reportados: gerenciamento_servicoserros (sem IP e sem usuário)."""
    if not is_db_available():
        return _load_from_csv("cartas_errors.csv")
    df = run_query(_SQL_ERRORS)
    return df if not df.empty else _load_from_csv("cartas_errors.csv")


@st.cache_data(ttl=3600, show_spinner=False)
def load_service_cards_votes() -> pd.DataFrame:
    """Votos de satisfação: gerenciamento_votosservicos (sem comentário e sem IP)."""
    if not is_db_available():
        return _load_from_csv("cartas_votes.csv")
    df = run_query(_SQL_VOTES)
    return df if not df.empty else _load_from_csv("cartas_votes.csv")


@st.cache_data(ttl=3600, show_spinner=False)
def load_service_cards_info_reviews() -> pd.DataFrame:
    """
    Avaliações de informação (gerenciamento_avaliacaoinformacaoservicos).
    Retorna apenas avaliacao (boolean) e data — sem IP (LGPD).
    9.867 registros disponíveis no banco.
    """
    _sql = """
        SELECT
            a.id            AS id_avaliacao,
            a.servico_id    AS idservico,
            s.titulo        AS titulo_servico,
            a.avaliacao     AS avaliacao_carta,
            a.created_at    AS data_avaliacao
            -- excluídos: a.ip (LGPD)
        FROM public.gerenciamento_avaliacaoinformacaoservicos a
        INNER JOIN public.gerenciamento_servicos s ON s.id = a.servico_id
        ORDER BY a.created_at DESC;
    """
    if not is_db_available():
        return pd.DataFrame()
    df = run_query(_sql)
    return df
