# Plano: Cartas de Serviço no Streamlit

## Resumo

Adicionar ao dashboard Streamlit o bloco 5. Cartas de Serviço, usando os dados já existentes no modelo Qlik como referência de campos. O  
 app não deve ler QVD diretamente no Streamlit Cloud; a SETDIG deve disponibilizar views PostgreSQL somente leitura com esses mesmos dados  
 já tratados e sem dados pessoais.

## Fonte De Dados

Usar as tabelas do Qlik como base conceitual:

- Orgao: cadastro dos órgãos.
- Serviço: inventário das cartas de serviço.
- ErroServico: erros reportados nas cartas.
- VotoServico: votos e satisfação dos usuários.
- AvaliacaoInformacao: avaliação da informação da carta.
- Atendimento: dados operacionais vinculados a serviços, se necessário para análises futuras.

Não usar no dashboard público/gerencial:

- Pessoa
- AdministradorControl
- LogAcesso com CPF/IP
- campos como cpf, ip_erro, ip_login, comentario_voto, salvo se houver anonimização e autorização LGPD.

## Views PostgreSQL Recomendadas

Criar views read-only no banco para o Streamlit:

- vw_cartas_servico
  - idservico
  - titulo_servico
  - nome_popular
  - siglaorgao
  - nome_orgao
  - servico_ativo
  - digital
  - online
  - agendavel
  - acesso_externo
  - custo
  - tempo
  - tipo_tempo
  - data_criacao_servico
  - data_atualizacao_servico
  - data_revisao_servico
- vw_cartas_erros
  - iderroservico
  - idservico
  - siglaorgao
  - nome_orgao
  - conteudo
  - atendido
  - corrigido_erro
  - reportado_erro
  - resolucao_erro
  - data_criacao_erro
  - data_atualizacao_erro
  - excluir ip_erro
- vw_cartas_votos
  - id_voto
  - idservico
  - data_voto
  - avaliacao_voto_servico
  - excluir ou anonimizar comentario_voto
- vw_cartas_avaliacao_info
  - id_avaliacao
  - idservico
  - avaliacao_carta
  - data_avaliacao

## Implementação No Streamlit

- Adicionar uma nova aba principal: 5. Cartas de Serviço.
- Criar loaders próprios com cache:
  - load_service_cards_inventory
  - load_service_cards_errors
  - load_service_cards_votes
  - load_service_cards_info_reviews
- Criar visualizações:
  - Visão Geral: total de serviços, ativos/inativos, digitais, presenciais, híbridos e percentual digital.
  - Por Órgão: ranking de órgãos, quantidade de serviços e percentual do total.
  - Qualidade: total de erros, atendidos, corrigidos, pendentes, erros por órgão, erros por serviço e evolução temporal.
  - Detalhamento de Erros: tabela operacional com órgão, serviço, descrição, atendido, corrigido, resolução e datas.
  - Satisfação: total de votos, satisfação, insatisfação e evolução por período.
  - Cruzamentos Estratégicos: serviços mais acessados no Matomo versus serviços com mais erros.

## Segurança E Custo

- Manter tudo com ferramentas gratuitas/open source: Streamlit, pandas, plotly, SQLAlchemy e psycopg.
- Guardar credenciais apenas em st.secrets.
- Usar usuário PostgreSQL somente leitura.
- Exigir SSL na conexão.
- Não expor CPF, IP, nome de pessoa, comentário livre ou qualquer campo identificável.
- Preferir views já agregadas ou sanitizadas no banco.
- Usar st.cache_data(ttl=3600) para reduzir carga no banco.

## Métricas

- Total de serviços cadastrados: contagem de idservico.
- Serviços ativos/inativos: por servico_ativo.
- Serviços digitais: por digital ou online.
- Serviços presenciais: digital = false e online = false.
- Híbridos: combinação de canal digital com atendimento/agendamento presencial, usando online, agendavel e acesso_externo.
- Percentual digital: serviços digitais / total de serviços ativos.
- Erros pendentes: erros não corrigidos ou não atendidos.
- Tempo médio de resolução: data_atualizacao_erro - data_criacao_erro, quando houver resolução/correção.
- Satisfação: cálculo sobre avaliacao_voto_servico, conforme valores reais encontrados no banco.

## Testes

- Validar conexão PostgreSQL no Streamlit Cloud.
- Confirmar que o usuário read-only não consegue executar INSERT, UPDATE ou acessar tabelas brutas.
- Testar views vazias, serviços sem órgão, erros sem resolução e votos sem avaliação.
- Conferir totais contra o Qlik para garantir paridade.
- Validar que nenhum campo sensível aparece na interface ou nos logs.

## Assumptions

- O dashboard usará apenas dados administrativos e agregados.
- Comentários de voto, CPF e IP ficam fora do v1 por segurança e LGPD.
