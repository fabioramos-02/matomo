"""
Conector PostgreSQL para o bloco Cartas de Serviço.
Usa SQLAlchemy + psycopg2 com SSL e st.cache_resource para reutilizar a conexão.
Fallback automático para modo mock se o banco não estiver disponível.
"""
import streamlit as st
import pandas as pd
import os

# --------------------------------------------------------------------------- #
# Detecção de disponibilidade das libs                                         #
# --------------------------------------------------------------------------- #
try:
    from sqlalchemy import create_engine, text
    _SQLALCHEMY_OK = True
except ImportError:
    _SQLALCHEMY_OK = False


def _get_db_secret(key: str, default=None):
    """
    Lê um segredo do st.secrets com fallback para variáveis de ambiente.
    """
    # 1. Tenta st.secrets (Streamlit)
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    
    # 2. Tenta variáveis de ambiente (SO/Docker)
    return os.getenv(key, default)


def _build_connection_url() -> str:
    host = _get_db_secret("HOST", "localhost")
    port = _get_db_secret("PORT", 5432)
    user = _get_db_secret("USER", "")
    password = _get_db_secret("PASSWORD", "")
    # secrets.toml usa BANCO; aceita DATABASE como fallback
    database = _get_db_secret("BANCO") or _get_db_secret("DATABASE", "postgres")
    
    if not user or not password:
        # Se não houver usuário/senha, não tenta montar URL de produção
        return None
        
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"


@st.cache_resource(show_spinner=False)
def get_pg_engine():
    """
    Retorna um engine SQLAlchemy com SSL.
    Retorna None se a conexão falhar ou as dependências não estiverem instaladas.
    """
    if not _SQLALCHEMY_OK:
        return None

    url = _build_connection_url()
    try:
        engine = create_engine(
            url,
            connect_args={"sslmode": "prefer"},  # servidor interno sem SSL
            pool_pre_ping=True,
            pool_size=2,
            max_overflow=3,
        )
        # Testa a conexão
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        import logging
        logging.warning(f"Conexão com o banco falhou: {e}")
        return None


def run_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    """
    Executa uma query e retorna um DataFrame.
    Retorna DataFrame vazio em caso de erro.
    """
    engine = get_pg_engine()
    if engine is None:
        return pd.DataFrame()
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(sql), conn, params=params)
    except Exception as e:
        st.error(f"Erro na consulta ao banco: {e}")
        return pd.DataFrame()


def is_db_available() -> bool:
    """Verifica se o banco está acessível."""
    return get_pg_engine() is not None


@st.cache_resource(show_spinner=False)
def get_pg_engine_controlador():
    """
    Retorna um engine SQLAlchemy com SSL para o banco controlador_prd.
    """
    if not _SQLALCHEMY_OK:
        return None

    host = _get_db_secret("HOST", "localhost")
    port = _get_db_secret("PORT", 5432)
    user = _get_db_secret("USER", "")
    password = _get_db_secret("PASSWORD", "")
    database = _get_db_secret("BANCO_CONTROLADOR", "controlador_prd")
    
    if not user or not password:
        return None
        
    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
    try:
        engine = create_engine(
            url,
            connect_args={"sslmode": "prefer"},
            pool_pre_ping=True,
            pool_size=2,
            max_overflow=3,
        )
        # Testa a conexão
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        import logging
        logging.warning(f"Conexão com o banco controlador_prd falhou: {e}")
        return None


def run_query_controlador(sql: str, params: dict | None = None) -> pd.DataFrame:
    """
    Executa uma query no banco controlador_prd e retorna um DataFrame.
    """
    engine = get_pg_engine_controlador()
    if engine is None:
        return pd.DataFrame()
    try:
        with engine.connect() as conn:
            return pd.read_sql(text(sql), conn, params=params)
    except Exception as e:
        st.error(f"Erro na consulta ao banco controlador_prd: {e}")
        return pd.DataFrame()


def is_db_controlador_available() -> bool:
    """Verifica se o banco controlador_prd está acessível."""
    return get_pg_engine_controlador() is not None

