"""
db_discovery.py — Script de diagnóstico do banco PostgreSQL
Executa como script standalone (não precisa do Streamlit rodando).

Uso:
    py matomo-analytics-dashboard/db_discovery.py

O que faz:
    1. Testa a conexão com o banco
    2. Lista todos os schemas disponíveis
    3. Lista todas as tabelas e views do schema público
    4. Para cada tabela relevante (servico, orgao, erro...), mostra as colunas
    5. Salva o relatório em docs/db_schema_report.txt
"""

import os
import sys

# ── Força UTF-8 no terminal Windows ─────────────────────────────────────────
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ── Leitura dos segredos sem depender do Streamlit ─────────────────────────
def _load_secrets() -> dict:
    """Lê o secrets.toml sem precisar do Streamlit."""
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        try:
            import tomli as tomllib  # fallback
        except ImportError:
            # Parsing manual simples para TOML flat
            secrets = {}
            toml_path = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")
            with open(toml_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, _, v = line.partition("=")
                        secrets[k.strip()] = v.strip().strip('"')
            return secrets

    toml_path = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")
    with open(toml_path, "rb") as f:
        return tomllib.load(f)


secrets = _load_secrets()

HOST     = secrets.get("HOST", "localhost")
PORT     = int(secrets.get("PORT", 5432))
USER     = secrets.get("USER", "")
PASSWORD = secrets.get("PASSWORD", "")
DATABASE = secrets.get("BANCO", secrets.get("DATABASE", "postgres"))

# ── Conexão ─────────────────────────────────────────────────────────────────
try:
    import psycopg2
except ImportError:
    print("❌ psycopg2 não instalado. Execute: py -m pip install psycopg2-binary")
    sys.exit(1)

print(f"\n🔌 Conectando em {HOST}:{PORT} / banco={DATABASE} / user={USER}...")

try:
    conn = psycopg2.connect(
        host=HOST, port=PORT, user=USER, password=PASSWORD,
        dbname=DATABASE, sslmode="prefer", connect_timeout=10,
    )
    print("✅ Conexão bem-sucedida!\n")
except Exception as e:
    print(f"❌ Falha na conexão: {e}")
    sys.exit(1)

cur = conn.cursor()
report_lines = [f"=== Relatório de Schema: {DATABASE} ===\n"]

# ── 1. Schemas disponíveis ───────────────────────────────────────────────────
cur.execute("SELECT schema_name FROM information_schema.schemata ORDER BY schema_name;")
schemas = [r[0] for r in cur.fetchall()]
report_lines.append(f"Schemas: {schemas}\n")
print(f"📂 Schemas encontrados: {schemas}")

# ── 2. Tabelas e Views ───────────────────────────────────────────────────────
cur.execute("""
    SELECT table_schema, table_name, table_type
    FROM information_schema.tables
    WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
    ORDER BY table_schema, table_type, table_name;
""")
objects = cur.fetchall()

print(f"\n📋 Objetos encontrados ({len(objects)} total):")
report_lines.append(f"\n{'='*60}\nTabelas e Views ({len(objects)} total):\n{'='*60}")
for schema, name, obj_type in objects:
    tipo = "TABLE" if obj_type == "BASE TABLE" else "VIEW"
    line = f"  [{tipo}] {schema}.{name}"
    print(line)
    report_lines.append(line)

# ── 3. Colunas das tabelas relevantes ────────────────────────────────────────
KEYWORDS = ["servic", "orgao", "erro", "voto", "avali", "pessoa", "atend", "carta", "portal"]

relevant = [
    (schema, name) for schema, name, _ in objects
    if any(kw in name.lower() for kw in KEYWORDS)
]

print(f"\n🔍 Detalhando {len(relevant)} tabelas/views relevantes...")
report_lines.append(f"\n{'='*60}\nColunas das tabelas relevantes:\n{'='*60}")

for schema, table in relevant:
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position;
    """, (schema, table))
    cols = cur.fetchall()

    block = f"\n[{schema}.{table}]\n"
    for col_name, data_type, nullable in cols:
        block += f"  - {col_name} ({data_type}) {'NULL' if nullable=='YES' else 'NOT NULL'}\n"

    print(block)
    report_lines.append(block)

    # Contagem de registros
    try:
        cur.execute(f'SELECT COUNT(*) FROM "{schema}"."{table}";')
        count = cur.fetchone()[0]
        line = f"  → {count:,} registros\n"
        print(line)
        report_lines.append(line)
    except Exception:
        pass

# ── 4. Salva relatório ───────────────────────────────────────────────────────
report_path = os.path.join(os.path.dirname(__file__), "docs", "db_schema_report.txt")
os.makedirs(os.path.dirname(report_path), exist_ok=True)
with open(report_path, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))

print(f"\n✅ Relatório salvo em: {report_path}")
cur.close()
conn.close()
