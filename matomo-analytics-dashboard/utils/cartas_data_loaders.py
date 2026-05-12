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
# DADOS MOCK — usados apenas quando o banco está inacessível                  #
# =========================================================================== #

_ORGAOS_MOCK = [
    ("SEJUSP", "Secretaria de Justiça e Segurança Pública"),
    ("SEFAZ", "Secretaria de Fazenda"),
    ("SAÚDE", "Secretaria de Saúde"),
    ("SED", "Secretaria de Educação"),
    ("SETDIG", "Secretaria de Tecnologia e Inovação"),
    ("DETRAN", "Departamento de Trânsito"),
    ("AGEHAB", "Agência de Habitação"),
    ("IMASUL", "Instituto de Meio Ambiente"),
    ("JUCEMS", "Junta Comercial"),
]
_SERVICOS_MOCK = [
    "Antecedentes Criminais", "Certidão de Nascimento", "Licenciamento de Veículo",
    "Matrícula Escolar", "Cadastro para Habitação", "Licença Ambiental",
    "Registro Empresarial", "Parcelamento de Débitos", "Cartão SUS",
    "Renovação de CNH", "Transferência de Veículo", "Bolsa de Estudos",
]

random.seed(42)


def _mock_inventory() -> pd.DataFrame:
    rows = []
    base = date(2020, 1, 1)
    for i, nome in enumerate(_SERVICOS_MOCK):
        sigla, orgao = _ORGAOS_MOCK[i % len(_ORGAOS_MOCK)]
        rows.append({
            "idservico": i + 1,
            "titulo_servico": nome,
            "slug_servico": nome.lower().replace(" ", "-"),
            "slug_categoria": "financas-e-impostos",
            "nome_popular": nome,
            "siglaorgao": sigla,
            "nome_orgao": orgao,
            "servico_ativo": i % 5 != 0,
            "digital": random.choice([True, True, False]),
            "online": random.choice([True, False]),
            "agendavel": random.choice([True, False, False]),
            "acesso_externo": random.choice([True, False]),
            "custo": random.choice(["Gratuito", "Pago", "Variável"]),
            "tempo": random.randint(1, 30),
            "tipo_tempo": random.choice(["dias úteis", "dias", "horas"]),
            "data_criacao_servico": base + timedelta(days=i * 45),
            "data_atualizacao_servico": base + timedelta(days=i * 45 + 60),
        })
    return pd.DataFrame(rows)


def _mock_errors() -> pd.DataFrame:
    tipos = ["Link quebrado", "Informação desatualizada", "Prazo incorreto", "Formulário inacessível"]
    base = date(2023, 1, 1)
    rows = []
    for i in range(40):
        sigla, orgao = _ORGAOS_MOCK[i % len(_ORGAOS_MOCK)]
        criacao = base + timedelta(days=random.randint(0, 400))
        rows.append({
            "iderroservico": i + 1,
            "idservico": random.randint(1, len(_SERVICOS_MOCK)),
            "titulo_servico": random.choice(_SERVICOS_MOCK),
            "slug_servico": "servico-mock",
            "slug_categoria": "financas-e-impostos",
            "siglaorgao": sigla,
            "nome_orgao": orgao,
            "conteudo": random.choice(tipos),
            "atendido": random.choice([True, True, False]),
            "corrigido_erro": random.choice([True, False]),
            "resolucao_erro": random.choice(["Corrigido", "Em análise", None]),
            "data_criacao_erro": criacao,
            "data_atualizacao_erro": criacao + timedelta(days=random.randint(0, 60)),
        })
    return pd.DataFrame(rows)


def _mock_votes() -> pd.DataFrame:
    base = date(2023, 1, 1)
    rows = []
    for i in range(200):
        sigla, orgao = _ORGAOS_MOCK[i % len(_ORGAOS_MOCK)]
        rows.append({
            "id_voto": i + 1,
            "idservico": random.randint(1, len(_SERVICOS_MOCK)),
            "titulo_servico": random.choice(_SERVICOS_MOCK),
            "siglaorgao": sigla,
            "nome_orgao": orgao,
            "data_voto": base + timedelta(days=random.randint(0, 500)),
            "avaliacao_voto_servico": random.choices([1, 2, 3, 4, 5], weights=[5, 10, 15, 35, 35])[0],
        })
    return pd.DataFrame(rows)


# =========================================================================== #
# LOADERS PÚBLICOS                                                             #
# =========================================================================== #

def _load_from_csv(filename: str, fallback_func):
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
            print(f"Erro ao carregar CSV de fallback ({path}): {e}")
    return fallback_func()


@st.cache_data(ttl=3600, show_spinner=False)
def load_service_cards_inventory() -> pd.DataFrame:
    """Inventário de cartas: gerenciamento_servicos × gerenciamento_orgaos."""
    if not is_db_available():
        return _load_from_csv("cartas_inventory.csv", _mock_inventory)
    df = run_query(_SQL_INVENTORY)
    return df if not df.empty else _load_from_csv("cartas_inventory.csv", _mock_inventory)


@st.cache_data(ttl=3600, show_spinner=False)
def load_service_cards_errors() -> pd.DataFrame:
    """Erros reportados: gerenciamento_servicoserros (sem IP e sem usuário)."""
    if not is_db_available():
        return _load_from_csv("cartas_errors.csv", _mock_errors)
    df = run_query(_SQL_ERRORS)
    return df if not df.empty else _load_from_csv("cartas_errors.csv", _mock_errors)


@st.cache_data(ttl=3600, show_spinner=False)
def load_service_cards_votes() -> pd.DataFrame:
    """Votos de satisfação: gerenciamento_votosservicos (sem comentário e sem IP)."""
    if not is_db_available():
        return _load_from_csv("cartas_votes.csv", _mock_votes)
    df = run_query(_SQL_VOTES)
    return df if not df.empty else _load_from_csv("cartas_votes.csv", _mock_votes)


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
