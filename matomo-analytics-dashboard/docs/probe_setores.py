"""Valida a tabela gerenciamento_setor e o JOIN completo servico→setor→orgao."""
import psycopg2

conn = psycopg2.connect(
    host="s0845.ms", port=5432,
    user="painel-sgd", password="AxL#P7My!b7630Y2B3x2",
    dbname="admin_prd", sslmode="prefer"
)
cur = conn.cursor()

print("=== SETOR (colunas) ===")
cur.execute("""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'gerenciamento_setor'
    ORDER BY ordinal_position;
""")
for r in cur.fetchall():
    print(" ", r)

cur.execute("SELECT COUNT(*) FROM public.gerenciamento_setor;")
print("  registros:", cur.fetchone()[0])

cur.execute("SELECT id, nome, orgao_id FROM public.gerenciamento_setor LIMIT 5;")
print("  sample:", [r for r in cur.fetchall()])

print("\n=== JOIN servico x setor x orgao ===")
cur.execute("""
    SELECT
        s.id, s.titulo, s.ativo, s.digital, s.online,
        o.sigla, o.nome
    FROM public.gerenciamento_servicos s
    INNER JOIN public.gerenciamento_setor st ON st.id = s.setor_id
    INNER JOIN public.gerenciamento_orgaos o ON o.id = st.orgao_id
    LIMIT 5;
""")
for r in cur.fetchall():
    print(" ", r)

cur.execute("""
    SELECT COUNT(*)
    FROM public.gerenciamento_servicos s
    INNER JOIN public.gerenciamento_setor st ON st.id = s.setor_id
    INNER JOIN public.gerenciamento_orgaos o ON o.id = st.orgao_id;
""")
print("\n  Total com JOIN:", cur.fetchone()[0])

conn.close()
print("OK")
