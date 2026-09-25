## 1. Pré-requisitos e Spike

- [x] 1.1 Verificar que a `llm-chat` expõe o ponto de extensão de contexto da aba "Chat AI" e registrar o resultado
- [x] 1.2 Spike: confirmar que a URL da notícia retorna HTML server-rendered com o corpo extraível, e registrar a conclusão
- [x] 1.3 Criar a estrutura de diretórios da aquisição e do painel de notícias

## 2. Aquisição e Cache

- [x] 2.1 Listagem das notícias do período via `RegulacaoRepository`, e verificar com mock
- [x] 2.2 Chave surrogate estável (`sha1` de URL ou de data|agência|título), e verificar os dois casos
- [x] 2.3 Download do corpo do artigo com `baixar` injetável e cache `noticias/<AAAA>/<MM>/<hash>.html`, e verificar gravação
- [x] 2.4 Tolerância por item (sem URL, sem conteúdo, erro de rede) e deduplicação no cache, e verificar reexecução
- [x] 2.5 Progresso e cancelamento (padrão de `AquisicaoDocumentos`), e verificar callback e token

## 3. Extração e Resumos

- [x] 3.1 Extração do texto do HTML do artigo para os stores existentes, e verificar com fixture
- [x] 3.2 Reuso do serviço de resumo para resumo curto/longo por notícia, e verificar persistência
- [x] 3.3 Falha da LLM no lote não interrompe os demais, e verificar item que falha
- [x] 3.4 Estado sem LLM configurada orienta a configuração, e verificar mensagem

## 4. Painel — Sub-aba "Notícias"

- [x] 4.1 `NoticiasPanel` em `tkinter` (árvore + preview via `ReadonlyText`), e verificar construção
- [x] 4.2 Botões "Atualizar", "Abrir", "I.A." e "Resumir pendentes" com barra de progresso, e verificar ações
- [x] 4.3 Abertura do artigo no navegador e estado vazio/sem texto, e verificar cenários
- [x] 4.4 Registro da sub-aba "Notícias" no notebook da Análise Geral, e verificar presença

## 5. Integração com o Chat

- [x] 5.1 Registro das notícias como fonte adicional no contexto da aba "Chat AI", e verificar presença
- [x] 5.2 Relevância por ticker inferida pela LLM a partir da pergunta, e verificar cenário
- [x] 5.3 Cache frio de notícias não quebra a montagem do contexto, e verificar cenário

## 6. Testes

- [x] 6.1 Aquisição/cache com `responses` e caches temporários
- [x] 6.2 Painel: estados, preview, abertura e resumos com LLM mockada
- [x] 6.3 Integração com o contexto de chat (fonte adicional, cache frio e ticker inferido)

## 7. Quality Gate

- [x] 7.1 `make lint` e `make complexity` limpos
- [x] 7.2 `pytest -m "not llm"` passa
- [x] 7.3 Testes existentes sem regressão
- [x] 7.4 Executar `openspec validate noticias-b3` e garantir que a change permanece válida

## 8. Documentação

- [x] 8.1 Atualize README.md, indicators.md e panels.md com o que foi implementado nessa change.

## 10. Categorias regulatórias na sub-aba (RFC-004)

- [x] 10.1 Entidade `ProgramaAquisicao` e exports do domínio
- [x] 10.2 Corrigir parser de censuras (`li.accordion-navigation`) e de condições (cabeçalho); parser de programas
- [x] 10.3 `listar_programas_aquisicao` no cliente com retry e na porta `RegulacaoRepository`
- [x] 10.4 Item unificado (`ItemNoticia`), chave estável e conteúdo próprio quando não há URL
- [x] 10.5 Catálogo em seções ("Geral", "Censuras Públicas", "Condições Excepcionais", "Programas de Aquisição")
- [x] 10.6 Árvore com raiz e seções e pré-visualização por seção
- [x] 10.7 Contexto do chat cobrindo as quatro categorias
- [x] 10.8 Testes das novas fontes, parsers, catálogo, painel e chat
- [x] 10.9 `make lint`/`make complexity` limpos e `pytest -m "not llm"` passa
- [x] 10.10 Atualizar README.md e panels.md com as novas categorias

## 11. Ordem das categorias

- [x] 11.1 Posicionar a categoria "Geral" por último na árvore e na ordem de processamento
- [x] 11.2 Atualizar specs, design e testes da ordem
- [x] 11.3 `make lint` e `pytest -m "not llm"` passam

## 9. Ajustes de carga

- [x] 9.1 Limitar a leitura das notícias aos últimos 6 meses, em janelas mensais (limite de 30 dias por consulta da API)
- [x] 9.2 (superado por 9.4) Excluir da carga os títulos administrativos pré-definidos, com correspondência tolerante a caixa e acentos
- [x] 9.3 `make lint`/`make complexity` limpos e `pytest -m "not llm"` passa
- [x] 9.4 Substituir o filtro por inclusão (whitelist) de eventos excepcionais de mercado, com fronteira de palavra
- [x] 9.5 Refazer a análise dos tipos remanescentes e registrar o volume resultante
- [x] 9.6 Aumentar a janela de leitura para 12 meses
- [x] 9.7 Retirar os anúncios de distribuição da whitelist
- [x] 9.8 Revisar falso-positivos (boletins diários) e falso-negativos (modificação de oferta, cancelamento de registro, liquidação etc.) e implementar a lista aprovada

## 12. Carga inicial somente do cache local

- [x] 12.1 Criar `NoticiasIndexStore` (`noticias/index.json`) com gravação atômica e leitura tolerante a ausência/corrupção
- [x] 12.2 Fazer a aquisição registrar os metadados de cada item com corpo, inclusive quando já cacheado (reparo do índice) e no cancelamento
- [x] 12.3 Reescrever `NoticiasCatalog` para ler somente o índice e o cache local, removendo a dependência do repositório da B3
- [x] 12.4 Garantir que o painel e a `FonteNoticias` não consultem a B3 na exibição/contexto; "Atualizar" permanece o único caminho de rede
- [x] 12.5 Atualizar os testes do índice, catálogo, painel, contexto do chat e aquisição
- [x] 12.6 Atualizar specs, design, README.md e panels.md
- [x] 12.7 `make lint`, `make complexity` e `pytest -m "not llm"` limpos; `openspec validate noticias-b3`

## 13. Status por categoria, carga parcial e corpo do artigo

- [x] 13.1 Consumir `fontes_noticias` na aquisição, anunciando cada categoria antes da listagem e reportando o progresso por item com o nome da categoria
- [x] 13.2 Indexar os metadados a cada item processado, de modo que a interrupção preserve e exiba a carga parcial
- [x] 13.3 Extrair o corpo do artigo da "Geral" por `#conteudoDetalhe` na pré-visualização e no resumo, com fallback para a página inteira
- [x] 13.4 Limpar o cache da sub-aba "Notícias" (`noticias/`, `NOTICIAS.json` de textos e resumos e caches de listagem da B3)
- [x] 13.5 Atualizar os testes de aquisição, painel e extração
- [x] 13.6 Atualizar README.md, indicators.md e panels.md
- [x] 13.7 `make lint`, `make complexity` e `pytest -m "not llm"` limpos; `openspec validate noticias-b3`

## 14. Documento vinculado sob demanda

- [x] 14.1 Criar `noticias_vinculo` com extração da URL suportada e resolução do documento (GET do visualizador + POST `ExibirPDF` + base64→PDF, reusando `pypdf`), tolerando captcha e falhas
- [x] 14.2 Resolver o documento vinculado na pré-visualização (seleção) e no lote de "Resumir pendentes", anexando o texto ao corpo e persistindo no cache de textos
- [x] 14.3 Cobrir com testes de infraestrutura (payload, captcha, erro, sem URL) e do painel (anexa/ignora por seção)
- [x] 14.4 Atualizar README.md, indicators.md, panels.md e os artefatos da change
- [x] 14.5 `make lint`, `make complexity` e `pytest -m "not llm"` limpos; `openspec validate noticias-b3`

## 15. Agrupamento da "Geral" por tipo de notícia

- [x] 15.1 Definir `TIPOS_NOTICIA` cobrindo a whitelist e `classificar_tipo` (título → tipo, com "Outros" de fallback)
- [x] 15.2 Usar o tipo como `categoria` da "Geral" em `item_de_noticia`, substituindo a agência no 3º nível da árvore (ano → mês → tipo → item)
- [x] 15.3 Atualizar o teste de cobertura da whitelist e os testes de catálogo/painel/chat, cobrindo títulos típicos e "Outros"
- [x] 15.4 Limpar o cache da "Geral" (HTML, índice, textos/resumos e listagem do Plantão B3), preservando as seções regulatórias
- [x] 15.5 Atualizar README.md, indicators.md, panels.md e os artefatos da change
- [x] 15.6 `make lint`, `make complexity` e `pytest -m "not llm"` limpos; `openspec validate noticias-b3`

## 16. Árvore recolhida e carga incremental da "Geral"

- [x] 16.1 Exibir a árvore de notícias expandida só até o primeiro nível (raiz aberta, categorias recolhidas), ajustando `DocumentTreeView`/`NoticiasTreeView`
- [x] 16.2 Carregar a "Geral" em lotes de até 30 dias cobrindo um ano, do mais recente ao antigo
- [x] 16.3 Persistir a data processada da "Geral" no índice (`geral_processada_ate`) e pular os lotes já concluídos, sempre recarregando o primeiro lote
- [x] 16.4 Permitir lote menor que 30 dias para completar o período/ano
- [x] 16.5 Atualizar os testes de janelas, marcador, aquisição incremental e estado da árvore
- [x] 16.6 Atualizar README.md, indicators.md, panels.md e os artefatos da change
- [x] 16.7 `make lint`, `make complexity` e `pytest -m "not llm"` limpos; `openspec validate noticias-b3`

## 17. Verificação do cache das fontes regulatórias

- [x] 17.1 Verificar que a listagem de "Censuras Públicas", "Condições Excepcionais" e "Programas de Aquisição de Ações" é servida pelo cache HTTP (validade própria) sem rede
- [x] 17.2 Verificar que o corpo dos itens regulatórios não é reescrito quando já existe em cache, com teste de regressão
- [x] 17.3 Documentar a garantia na spec `noticias-acquisition`
- [x] 17.4 `make lint`/`pytest -m "not llm"` limpos; `openspec validate noticias-b3`

## 18. Carga diária da "Geral" e escritas do índice agrupadas

- [x] 18.1 Alterar a "Geral" para carregar dia a dia (`DIAS_LOTE = 1`), pulando os dias já processados via marcadores
- [x] 18.2 Agrupar as escritas do índice das fontes regulatórias (lotes de 25 itens + final)
- [x] 18.3 Agrupar as escritas do índice da "Geral" (lotes de 25 dias + final), preservando parcial em cancelamento
- [x] 18.4 Extrair `AquisicaoNoticias` para `noticias_carga.py` para manter o gate de complexidade
- [x] 18.5 Atualizar os testes (janelas diárias, agrupamento de escritas, cargas) e os docs/artefatos
- [x] 18.6 `make lint`, `make complexity` e `pytest -m "not llm"` limpos; `openspec validate noticias-b3`
