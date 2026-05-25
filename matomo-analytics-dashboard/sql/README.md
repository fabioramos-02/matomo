<<<<<<< HEAD
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
  CGE-MS pra pares com `score_descricao ≥ 0.85` e órgãos diferentes.
=======
# SQL — Extração e Análise de Duplicidade de Cartas de Serviço

Scripts PostgreSQL para identificar **cartas de serviço duplicadas ou muito similares** no Portal `ms.gov.br`, com o objetivo de reduzir o nº de cartas que a **CGE-MS** precisa aprovar e que o **cidadão** precisa pesquisar.

---

## Pré-requisitos

- VPN SETDIG ativa (banco de dados não é acessível pela internet aberta).
- `psql` instalado na máquina remota.
- Usuário com `SELECT` em `gerenciamento_servicos`, `gerenciamento_orgaos`, `gerenciamento_temas` (ex.: `painel-sgd`).
- Para criar a view (script 01): privilégio de `CREATE VIEW` no schema (DBA / dono).
- **Recomendado:** extensão `pg_trgm` instalada (DBA — uma única vez).

```sql
-- Rode UMA VEZ no banco como superusuário:
CREATE EXTENSION IF NOT EXISTS pg_trgm;
-- (opcional, mas melhora muito a normalização pt-BR)
CREATE EXTENSION IF NOT EXISTS unaccent;
```

---

## Ordem de execução

| # | Arquivo | O que faz | Quem executa |
|---|---|---|---|
| 1 | `01_view_cartas_servico_descricao.sql` | Cria `vw_cartas_servico_descricao` (view com `descricao` e `url_servico` montada) | DBA / dono do schema |
| 2 | `02_duplicatas_exatas.sql` | Lista pares de cartas com **título idêntico** após normalização | Analista (`painel-sgd`) |
| 3 | `03_similaridade_descricao.sql` | Ranqueia pares por similaridade de **título + descrição** dentro do mesmo `tema_id` | Analista (`painel-sgd`) |

Rodar do diretório `sql/` na máquina remota:

```bash
psql "$DATABASE_URL" -f 01_view_cartas_servico_descricao.sql
psql "$DATABASE_URL" -f 02_duplicatas_exatas.sql           > duplicatas_exatas.txt
psql "$DATABASE_URL" -f 03_similaridade_descricao.sql      > similaridade.txt
```

> Substitua `$DATABASE_URL` pela string de conexão real.

---

## Exportar resultado para CSV

Cada script inclui um bloco `\copy` comentado no final. Para usar:

1. Abrir `psql` em modo interativo: `psql "$DATABASE_URL"`.
2. Colar a query da seção principal envolvida em `\copy (...) TO 'arquivo.csv' ...`.
3. CSV gerado fica no diretório de onde o `psql` foi aberto.

Padrão de saída: `FORMAT csv, HEADER true, DELIMITER ';', ENCODING 'UTF8'` (compatível com `exports/cartas_inventory.csv`).

---

## Como interpretar o resultado

### `02_duplicatas_exatas.sql`

Cada linha = **par de cartas com mesmo título normalizado**.

Colunas-chave:
- `titulo_norm` — título após lowercase + sem acentos + sem pontuação. Igual entre A e B.
- `siglaorgao_a` vs `siglaorgao_b` — se diferentes → **forte candidata a carta única servida por múltiplos órgãos**.
- `ativo_a` / `ativo_b` — preferir manter a ativa; arquivar a inativa.
- `qtd_no_cluster` — quantas cartas no total compartilham este título normalizado (>2 = revisar todas juntas).

### `03_similaridade_descricao.sql`

Cada linha = **par dentro do mesmo `tema_id`** com `score_titulo ≥ 0.70` ou `score_descricao ≥ 0.60`.

Faixas de leitura (pg_trgm, escala 0–1):

| Score | Interpretação |
|---|---|
| 1.00 | Idêntico |
| 0.85–0.99 | Quase idêntico — provável duplicata real |
| 0.70–0.84 | Forte similaridade — revisar texto |
| 0.60–0.69 | Similaridade moderada — pode ser variante ou serviço aparentado |
| < 0.60 | Filtrado fora |

**Decisão sugerida ao revisor:**
1. Ler `titulo_a` / `titulo_b` lado a lado.
2. Se órgãos diferentes (`siglaorgao_a ≠ siglaorgao_b`) **e** ambas ativas → candidata a **carta genérica** que múltiplos órgãos compartilham.
3. Se mesmo órgão → candidata a **fusão** ou **uma é versão antiga**.
4. Validar com a área dona antes de propor à CGE-MS.

---

## Caminhos com e sem `pg_trgm`

`03_similaridade_descricao.sql` traz dois caminhos:

- **Caminho (A) — com pg_trgm** (recomendado): usa `similarity()` em título e descrição.
- **Caminho (B) — fallback**: comentado em bloco `/* ... */`. Usa prefixo das 4 primeiras palavras do título + match exato da 1ª frase da descrição + janela de ±30% de tamanho.

Se o diagnóstico (`SELECT EXISTS(... 'pg_trgm') ...`) retornar `false`, descomente o bloco do Caminho (B) ou peça à DBA para instalar a extensão.

---

## Próximos passos sugeridos

- [ ] Cruzar o output com `exports/cartas_votes.csv` (qual carta do par tem mais votos positivos = manter).
- [ ] Cruzar com `exports/cartas_errors.csv` (qual carta tem mais erros reportados = priorizar correção/unificação).
- [ ] Construir aba no `matomo-analytics-dashboard` exibindo top 50 candidatas de unificação.
- [ ] Levar lista priorizada para reunião com CGE-MS e órgãos donos.
- [ ] Após unificação aprovada, registrar decisão via `/decisao` no Diário de Decisões do projeto.

---

## Observações LGPD

Nenhuma das views ou queries expõe dado pessoal (CPF, e-mail, IP, comentários livres). Padrão herdado de `docs/views_postgresql.sql`.
>>>>>>> 36dc56c595dae2f391fe62bf8b8ce63ac7a50d5e
