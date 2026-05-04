# Limitações e Desafios Técnicos

Este documento tem como objetivo apresentar para a gestão as limitações técnicas e desafios encontrados na integração com a API do Matomo e no mapeamento da jornada do usuário do Portal de Serviços (www.ms.gov.br).

## 1. Mapeamento Visual da Jornada Completa (Árvore de Navegação)
**O que foi solicitado:** Entender a jornada completa do usuário (Sankey, fluxo de navegação de ponta a ponta).
**A Limitação:** O Matomo não fornece um método na API que retorne a árvore completa de navegação de todos os usuários agregada. 
* A API `Transitions.getTransitionsForPageUrl` permite visualizar o passo anterior e o próximo de **uma única página** por vez.
* Para montar a jornada completa (ex: Home -> Busca -> Serviço -> Saída), seria necessário extrair os logs de visitas brutas (`Live.getLastVisitsDetails`) e processar gigabytes de dados localmente. Isso não é viável para uma aplicação leve sem banco de dados, podendo causar travamentos e lentidão severa.

## 2. Identificação das "Cartas de Serviço"
**O que foi solicitado:** Quais são as cartas de serviço mais acessadas.
**A Limitação:** Atualmente, as cartas de serviço **não possuem uma padronização na URL** (como um prefixo `/servicos/nome-do-servico`). Elas estão misturadas na raiz do site com nomes descritivos (ex: `agendar-atendimento-presencial153`).
* Para contornar isso, a aplicação utiliza **padrões de texto (Expressões Regulares)** para tentar filtrar e capturar o que parece ser um serviço (URLs com hifens, verbos de ação e sem extensões genéricas). 
* **O Risco:** Esse filtro não é 100% preciso. Páginas de notícias ou campanhas com formato semelhante podem ser contadas como "serviços" acidentalmente, ou serviços com nomes muito diferentes podem ficar de fora da contagem.

## 3. Performance em Longos Períodos
**O que foi solicitado:** Extrair dados por ano e outros períodos amplos.
**A Limitação:** Requisições para a API do Matomo pedindo dados consolidados de um **ano inteiro** podem demorar consideravelmente ou até falhar (timeout) dependendo da carga no servidor do portal de analytics.
* Como a solução não utiliza banco de dados próprio (SQLite), toda vez que o dashboard é carregado, ele faz a requisição em tempo real para a API do governo.
* Aplicamos *cache* em memória para amenizar o problema: se um usuário pesquisar "Ano de 2026", o sistema guarda o resultado na memória temporária para navegações subsequentes.

## Métodos da API Analisados
Foram mapeados métodos que **não temos na solução atual mas o Matomo oferece**, caso seja decidido expandir a ferramenta e utilizar um banco de dados:
* `Actions.getEntryPageUrls` / `Actions.getExitPageUrls`: Taxa de rejeição e abandono de serviços.
* `DevicesDetection.getOs` / `Resolution.getResolution`: Identificação se as quedas de jornada ocorrem mais no celular ou no computador.
