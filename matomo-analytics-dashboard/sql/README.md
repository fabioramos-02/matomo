# SQL — Cartas de Serviço SETDIG / Portal ms.gov.br

Conjunto de scripts SQL para extração de cartas de serviço com **detecção
de duplicidade** (match exato por título + similaridade de descrição).
Motivação: apoiar a CGE-MS a reduzir o nº de cartas redundantes que o
cidadão encontra no portal `ms.gov.br`.

## Ordem de execução

| # | Arquivo | O que faz |
|---|---|---|
| 1 | `01_view_cartas_servico_descricao.sql` | Cria/atualiza `vw_cartas_servico_descricao` com `descricao`, `titulo_normalizado`, `url_servico` e `url_status`. |
| 2 | `02_duplicatas_exatas.sql` | Lista clusters e pares de cartas com **mesmo título normalizado**. Alta confiança. |
| 3 | `03_similaridade_descricao.sql` | Ranqueia pares por **similaridade de descrição** dentro do mesmo `tema_id`. Caminho A (pg_trgm) ou B (fallback). |

Rodar **em ordem**. Os scripts 2 e 3 dependem da view criada no 1.

## Requisitos

- PostgreSQL ≥ 12.
- VPN SETDIG ativa.
- Usuário `painel-sgd` com `SELECT` em `gerenciamento_servicos`,
  `gerenciamento_orgaos` e `gerenciamento_temas` (já concedido para as
  views LGPD existentes — ver `docs/views_postgresql.sql`).
- `CREATE` no schema corrente para o passo 1. **Sem isso**, use o "Plano B"
  comentado no fim do `01_*.sql` (transformar a view em CTE inline nas
  queries 2 e 3).
- `pg_trgm` é **opcional**. O script 3 detecta automaticamente; sem ele,
  descomentar o caminho B (fallback puro SQL com tokens).

## Caveat de schema

`docs/db_schema_report.txt` mostra colunas reais `id / titulo / created_at /
sigla / nome` em `gerenciamento_servicos` e `gerenciamento_orgaos`.
A view base do projeto (`vw_cartas_servico` em `docs/views_postgresql.sql`)
usa nomes `idservico / titulo_servico / data_criacao_servico / siglaorgao /
nome_orgao / idorgao`. Os scripts deste diretório **seguem a convenção da
view base** (fonte de verdade do time). Se o `CREATE OR REPLACE VIEW` do
passo 1 falhar com `column ... does not exist`, ajustar:

| usado aqui | provavelmente real |
|---|---|
| `s.idservico` | `s.id` |
| `s.titulo_servico` | `s.titulo` |
| `s.idorgao` | `s.setor_id` |
| `s.data_criacao_servico` | `s.created_at` |
| `s.data_atualizacao_servico` | `s.updated_at` |
| `o.siglaorgao` | `o.sigla` |
| `o.nome_orgao` | `o.nome` |

## Export para CSV

Cada arquivo SQL traz um bloco `\copy` comentado no final. Rodar **no psql
do cliente** (não no servidor — `\copy` é meta-comando do psql):

```bash
psql -h <host-vpn> -U painel-sgd -d <db> -f 01_view_cartas_servico_descricao.sql
psql -h <host-vpn> -U painel-sgd -d <db> -f 02_duplicatas_exatas.sql > duplicatas_exatas.txt
psql -h <host-vpn> -U painel-sgd -d <db> -c "\copy (SELECT ...) TO 'similaridade.csv' WITH (FORMAT csv, HEADER true, DELIMITER ';')"
```

Separador `;` por consistência com `exports/cartas_inventory.csv`.

## Leitura do score

- **`score_titulo`** — similaridade Jaccard de trigramas entre os títulos
  normalizados. `1.0` = match exato (também é o caso da query do passo 2).
- **`score_descricao`** — idem para o texto da descrição. Threshold padrão
  `0.6`. Heurística:

  | faixa | interpretação |
  |---|---|
  | `≥ 0.85` | Quase-cópia. Provável duplicata operacional. Unificar. |
  | `0.70 – 0.85` | Mesma intenção, redação diferente. Revisar. |
  | `0.60 – 0.70` | Tema próximo, conteúdo distinto. Avaliar caso a caso. |
  | `< 0.60` | Filtrado fora. Ruído. |

- **`tema`** = `mesmo` indica que ambas as cartas estão no mesmo `tema_id`
  do portal — peso adicional pra decisão de unificação.

## Quando ajustar threshold

- Saída do passo 3 com **muitos pares** (≥ 200) → subir pra `0.7`.
- Saída **vazia ou < 5 pares** → descer pra `0.5` e revisar manualmente.
- A coluna `score_descricao_tamanho` no passo 2 ajuda a triar pares com
  descrições de tamanho muito desigual (provável que uma seja stub).

## LGPD

Nenhum dado pessoal exposto. Views só leem campos descritivos do serviço,
em linha com `docs/views_postgresql.sql` e o plano técnico SETDIG.

## Próximos passos (não implementado aqui)

- **Embeddings semânticos**: trocar `pg_trgm` por `pgvector` +
  sentence-transformers pra captar paráfrases (ex.: "2ª via" vs "segunda
  via"). Útil quando o vocabulário entre cartas equivalentes diverge.
- **Job de revisão**: agendar export semanal e abrir tickets no fluxo da
