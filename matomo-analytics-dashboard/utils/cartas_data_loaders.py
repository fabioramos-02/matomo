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

from utils.pg_connector import run_query, is_db_available, run_query_controlador, is_db_controlador_available


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
    s.slug                      AS slug_servico,
    t_cat.slug                  AS slug_categoria,
    o.sigla                     AS siglaorgao,
    o.nome                      AS nome_orgao,
    v.created_at                AS data_voto,
    v.avaliacao                 AS avaliacao_voto_servico
    -- excluídos: v.comentario (LGPD), v.ip, v.user_id
FROM public.gerenciamento_votosservicos v
INNER JOIN public.gerenciamento_servicos s ON s.id = v.servicos_id
INNER JOIN public.gerenciamento_setor st ON st.id = s.setor_id
INNER JOIN public.gerenciamento_orgaos o ON o.id = st.orgao_id
LEFT JOIN public.gerenciamento_temas t_cat ON t_cat.id = s.tema_id
ORDER BY v.created_at DESC;
"""



# =========================================================================== #
# LOADERS PÚBLICOS                                                             #
# =========================================================================== #

def _load_from_csv(filename: str) -> pd.DataFrame:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "exports", filename)
    if os.path.exists(path):
        try:
            # Removido engine='python' pois pode causar AssertionError em alguns arquivos com campos multi-linha
            df = pd.read_csv(
                path, 
                sep=';', 
                on_bad_lines='skip',
                encoding='utf-8-sig',
                low_memory=False
            )
            
            if df.empty:
                return df

            # Tenta converter colunas de data
            for col in df.columns:
                if any(x in col for x in ["data_", "created_at", "updated_at"]):
                    df[col] = pd.to_datetime(df[col], errors='coerce', utc=True)
            
            return df
        except Exception as e:
            import logging
            logging.error(f"⚠️ Erro ao ler CSV de fallback ({path}): {str(e) or repr(e)}")
            return pd.DataFrame()
    else:
        import logging
        logging.warning(f"⚠️ Sem conexão com o banco e arquivo '{path}' não encontrado.")
        return pd.DataFrame()


@st.cache_data(ttl=3600, show_spinner=False)
def load_service_cards_inventory() -> pd.DataFrame:
    """Inventário de cartas: gerenciamento_servicos × gerenciamento_orgaos."""
    if not is_db_available():
        return _load_from_csv("cartas_inventory.csv")
    df = run_query(_SQL_INVENTORY)
    return df if not df.empty else _load_from_csv("cartas_inventory.csv")


def _enrich_with_slugs(df: pd.DataFrame) -> pd.DataFrame:
    """Helper para adicionar slug_servico e slug_categoria se faltarem (ex: fallback CSV antigo)."""
    if df.empty or ("slug_servico" in df.columns and "slug_categoria" in df.columns):
        return df
    
    # Se não tem slug, tenta pegar do inventário
    df_inv = load_service_cards_inventory()
    if not df_inv.empty:
        # Pega apenas colunas necessárias para o join
        inv_subset = df_inv[['idservico', 'slug_servico', 'slug_categoria']].drop_duplicates()
        # Garante tipos iguais para o join
        df['idservico'] = df['idservico'].astype(str)
        inv_subset['idservico'] = inv_subset['idservico'].astype(str)
        
        # Remove colunas se existirem mas forem nulas (raro mas possível)
        cols_to_drop = [c for c in ['slug_servico', 'slug_categoria'] if c in df.columns]
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)
            
        df = df.merge(inv_subset, on='idservico', how='left')
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def load_service_cards_errors() -> pd.DataFrame:
    """Erros reportados: gerenciamento_servicoserros (sem IP e sem usuário)."""
    if not is_db_available():
        return _load_from_csv("cartas_errors.csv")
    df = run_query(_SQL_ERRORS)
    df = df if not df.empty else _load_from_csv("cartas_errors.csv")
    return _enrich_with_slugs(df)


@st.cache_data(ttl=3600, show_spinner=False)
def load_service_cards_votes() -> pd.DataFrame:
    """Votos de satisfação: gerenciamento_votosservicos (sem comentário e sem IP)."""
    if not is_db_available():
        return _load_from_csv("cartas_votes.csv")
    df = run_query(_SQL_VOTES)
    df = df if not df.empty else _load_from_csv("cartas_votes.csv")
    return _enrich_with_slugs(df)


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


@st.cache_data(ttl=600, show_spinner=False)
def load_portal_users_consolidated(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Retorna o total de usuários únicos cadastrados e os usuários únicos que
    acessaram no período dinâmico selecionado (app_id=36).
    Usa o banco controlador_prd.
    """
    _sql = """
    SELECT
        total.app_id                                                        AS id_app,
        total.Qtde_Total_Usuarios_Portal,
        period.Qtde_Acessos_Periodo,
        ROUND(
            (period.Qtde_Acessos_Periodo::NUMERIC
                / NULLIF(total.Qtde_Total_Usuarios_Portal, 0)) * 100,
            2
        )                                                                   AS Percentual_Acesso_Periodo
    FROM
        (
            SELECT
                ac.app_id,
                COUNT(DISTINCT ac.user_id) AS Qtde_Total_Usuarios_Portal
            FROM public.authentication_historicologin as ac
            WHERE ac.app_id = 36
            GROUP BY 1
        ) AS total
    LEFT JOIN
        (
            SELECT
                ac.app_id,
                COUNT(DISTINCT ac.user_id) AS Qtde_Acessos_Periodo
            FROM public.authentication_historicologin as ac
            WHERE
                ac.app_id = 36
                AND ac.created_at >= CAST(:start_date AS DATE)
                AND ac.created_at < CAST(:end_date AS DATE) + INTERVAL '1 day'
            GROUP BY 1
        ) AS period
    ON total.app_id = period.app_id;
    """
    if not is_db_controlador_available():
        return pd.DataFrame()
    return run_query_controlador(_sql, params={"start_date": start_date, "end_date": end_date})


@st.cache_data(ttl=600, show_spinner=False)
def load_portal_users_trend(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Retorna a evolução temporal diária de acessos de usuários únicos
    no período selecionado (app_id=36).
    Usa o banco controlador_prd.
    """
    _sql = """
    SELECT
        created_at::date AS data_acesso,
        COUNT(DISTINCT user_id) AS qtde_usuarios
    FROM public.authentication_historicologin
    WHERE
        app_id = 36
        AND created_at >= CAST(:start_date AS DATE)
        AND created_at < CAST(:end_date AS DATE) + INTERVAL '1 day'
    GROUP BY 1
    ORDER BY 1;
    """
    if not is_db_controlador_available():
        return pd.DataFrame()
    df = run_query_controlador(_sql, params={"start_date": start_date, "end_date": end_date})
    if not df.empty:
        df['data_acesso'] = pd.to_datetime(df['data_acesso'])
    return df

