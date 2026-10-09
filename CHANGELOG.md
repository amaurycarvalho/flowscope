# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### [diagnosis-panel](openspec/changes/diagnosis-panel) Painel "Diagnóstico" substitui o placeholder "Resumo Geral" com classificação qualitativa por eixos independentes e novos classificadores de liquidez e institucional

### [eficiencia-do-movimento](openspec/changes/eficiencia-do-movimento) Painel "Eficiência do Movimento" com gauge horizontal, card qualitativo e timeline de barras para os últimos 15 pregões

### [llm-chat-rag](openspec/changes/llm-chat-rag) Recuperação vetorial como evolução da `llm-chat`, com VectorStore SQLite, embeddings e indexação de documentos consultada pela aba "Chat AI"

#### Added

- VectorStore em SQLite puro, com busca top-k por cosine similarity e filtro opcional por ticker.
- Módulo de embeddings com dois provedores: `fastembed` (local, default) e liteLLM (API).
- Porta `DocumentoIndexavel`/`DocumentSource` e fontes concretas, com extração de texto (HTML e PDF).
- Pipeline de indexação (`IndexarDocumentosUseCase`) e consulta RAG (`ConsultarDocumentosUseCase`) consumindo a porta `LLMPort` da `llm-core`.
- Integração da consulta RAG à aba "Chat AI" como fonte adicional de contexto, pelo ponto de extensão da `llm-chat`.
- Chunker de texto em Python puro.
- Configuração de embedding persistida em `llm.embedding` e presets de provedores de embedding.
- Dependência opcional `fastembed` no grupo `[llm]`.
- CLI `--index <TICKER>` com `--data-inicio` e `--data-fim`.

### [participation-negociacoes](openspec/changes/participation-negociacoes) Painel "Participação nas Negociações" renomeado, com gauge de concentração, card informativo e timeline AFT

## [1.3.5] — 2026-10-09

### [chat-navegacao-granular](openspec/changes/archive/2026-10-09-chat-navegacao-granular) Granularidade por documento e foco de referência na árvore do Chat AI, com índices em `/documentos` e `/guidance`, playbook de intenção e manifesto com abas/sub-abas

#### Added

- `/documentos/<ticker>` passa a expor `/documentos/<ticker>/indice` (uma linha por documento, mais recente primeiro) e um nó interno por documento (`/documentos/<ticker>/<chave>`) com folhas `curto`, `longo` e `texto` do próprio documento, além de metadados estruturados e pesquisáveis (categoria, período, nome).
- `/guidance/<ticker>` passa a expor `/guidance/<ticker>/indice`, agregando os guidances por mês com o rótulo do Relatório Gerencial associado.
- O bloco de resultado da navegação passa a devolver um `foco` (último caminho obtido) para resolver referências como "nesse RG"/"esse último".
- O protocolo/manifesto ganham um playbook de intenção→ramo e a regra de preferir o `texto` integral do documento-alvo a resumos agregados quando a pergunta pede detalhe.

#### Changed

- O manifesto passa a anunciar `/flowscope/abas/<aba>` e a lista de sub-abas, e deixa de incluir metadados longos (teto por metadado).

### [chat-navegacao-robusta](openspec/changes/archive/2026-10-09-chat-navegacao-robusta) Ramos internos vazios omitidos da árvore do Chat AI, manifesto anunciando apenas ramos existentes e fallback para busca determinística por regex

#### Changed

- Ramos internos sem itens são omitidos da árvore de conhecimento em vez de existirem como folhas vazias: `/flowscope/abas`, `/flowscope/indicadores`, `/fundamentos/tickers`, `/fundamentos/campos` e `/fundamentos/valores`.
- O mapa canônico e a descrição do manifesto passam a anunciar **apenas os ramos existentes** na árvore corrente (deixa de citar caminhos inexistentes).
- O protocolo/manifesto e o prompt de sistema passam a orientar a LLM a usar a busca determinística `buscar(caminho, regex, em=[...])` sempre que `buscar_semantico` responder `indice_indisponivel`, e a preferir o nó `indice`/`buscar` a listar grupos grandes inteiros.

### [corrigir-assinatura-vinculo-noticias](openspec/changes/archive/2026-10-09-corrigir-assinatura-vinculo-noticias) Corrige o `TypeError` na resolução de documento vinculado de notícias, alinhando a chamada do painel à assinatura de `baixar_conteudo_vinculado`

#### Added

- Testes que exercitam a assinatura real do resolvedor usado em produção (`baixar_conteudo_vinculado`), impedindo que dublês com assinatura divergente escondam a regressão.

#### Fixed

- Alinhamento do contrato de chamada do resolvedor de documento vinculado injetado no `NoticiasPanel` com a assinatura de `baixar_conteudo_vinculado`, de modo que a senha opcional seja aceita sem `TypeError`.
- Uma falha do resolvedor (assinatura, rede ou formato) passa a degradar para o corpo original, sem propagar exceção para a pré-visualização nem para o lote.

### [documentos-arvore-ramos](openspec/changes/archive/2026-10-09-documentos-arvore-ramos) Árvore de documentos com ramos Guidance e Direitos e obrigações, navegação de guidance no chat e remontagem após o lote de resumos

#### Added

- Ramo **Guidance** (somente FII, com base nos documentos `Relatorio`): sub-ramos ano e mês, com uma folha por guidance que possui valor em cache; clicar exibe o texto do guidance e o rótulo curado do RG, e duplo-clique salta para a folha do RG na ramificação Documentos.
- Ramo **Direitos e obrigações** com os sub-ramos "Direitos" (ativos) e "Obrigações" (passivos), vazios por enquanto, preenchidos por changes futuras.
- Ao entrar na sub-aba pela primeira vez na sessão (ou ao mudar o ticker), a árvore fica expandida apenas até o primeiro nível.
- A árvore de conhecimento da aba "Chat AI" ganha navegação para o guidance e para "Direitos e obrigações", com os caminhos canônicos refletidos no manifesto e na assinatura de estado.
- Após "Resumir pendentes", a árvore é remontada (sub-abas "Documentos" e "Notícias"), preservando o arquivo selecionado.

#### Changed

- A árvore da sub-aba "Documentos" passa a ter, sob o nome do ticker, três ramos: Guidance, Documentos e Direitos e obrigações.

### [documentos-conteudo-completo](openspec/changes/archive/2026-10-09-documentos-conteudo-completo) Resumos de documentos cortados em fronteira de frase/palavra, regeneração de resumos truncados e leitura paginada do texto integral

#### Added

- Resumos já em cache que terminam no meio da palavra passam a ser regenerados pelo lote "Resumir pendentes", sem exigir limpeza manual.
- A operação `obter` passa a aceitar `offset`/`limite` (leitura paginada) para o texto integral, e o manifesto/playbook orientam a leitura em partes quando o texto for longo.

#### Changed

- O resumo de documento passa a cortar em fronteira de frase/palavra (nunca no meio da palavra) e o prompt pede os resumos por frases/parágrafos, mantendo os tetos como salvaguarda.

### [guidance-preview-rg](openspec/changes/archive/2026-10-09-guidance-preview-rg) Guidance do próprio Relatório Gerencial exibido na pré-visualização de documentos e avaliação de RGs já resumidos pendentes de guidance no lote

#### Added

- A pré-visualização de um RG com guidance passa a exibir o texto do guidance entre o resumo e o separador `---`, com uma linha em branco antes e depois.
- O botão "Resumir pendentes" passa a ser habilitado, com a IA ativa, também quando houver Relatórios Gerenciais já resumidos cuja avaliação de guidance esteja pendente, mesmo sem documento sem `long_summary`.
- O lote passa a avaliar o guidance desses RGs pendentes, pulando a geração de resumo dos que já o possuem e reaproveitando resumos e texto em cache.

#### Changed

- O texto exibido é o guidance do RG específico (entrada do ledger daquele documento), formatado exatamente como na coluna `Informações adicionais` da sub-aba "Fundamentos".
- A formatação do item de guidance é extraída para uma função compartilhada, reusada pela coluna e pela pré-visualização.
- A verificação de pendências de guidance consulta o ledger fora da thread do Tk, no mesmo worker que lê o catálogo.

### [logging-falhas-comunicacao](openspec/changes/archive/2026-10-09-logging-falhas-comunicacao) Falhas de comunicação toleradas registradas em uma linha de `WARNING` sem traceback

#### Changed

- Convenção: em falha de comunicação tolerada, registrar uma linha de `WARNING` com o tipo e a mensagem da exceção, sem traceback; exceções não relacionadas a comunicação continuam com traceback.
- A convenção é implementada de forma central no formatter de logging da aplicação, cobrindo todos os pontos de aquisição sem alterar os 60+ call sites.
- Os registros em memória (`record.exc_info`) são preservados para testes e depuração; apenas a renderização passa a omitir o traceback de comunicação.
- O tratamento explícito já existente em `noticias_vinculo.py` é mantido.

### [testes-ui-headless](openspec/changes/archive/2026-10-09-testes-ui-headless) Costuras testáveis na apresentação e conversão de testes gated para headless, reduzindo o orçamento de testes de UI

#### Added

- Costuras testáveis na apresentação para verificar sem `DISPLAY` a lógica hoje presa ao widget: construção de `Figure`/`Axes` separada do invólucro Tk, decisões de mixins expostas como valores/funções puras e modelo de formulário separado dos `StringVar` no diálogo de configuração de LLM.

#### Changed

- As declarações gated correspondentes passam a rodar headless, preservando a asserção de comportamento observável (paridade de textos, números e ordem).
- A lógica pura hoje coberta sob gate de display migra para `tests/test_application`/`tests/test_presentation` headless.
- O baseline `tests/architecture/ui_test_budget.txt` é baixado após cada incremento (o ratchet exige atualização explícita).
- Fica sob teste de UI apenas o que só existe com Tk: layout/geometria, eventos de ponteiro, `Treeview`/notebooks reais, `ReadonlyText`/clipboard, overlay/modal e o binding fio-a-fio do estado aos widgets.

### [tooltip-robusto](openspec/changes/archive/2026-10-09-tooltip-robusto) Tooltips deixam de ficar presos na tela e cobertura de dicas estendida a todos os botões da aplicação

#### Added

- Dicas descritivas passam a cobrir todos os botões da aplicação que ainda não as possuíam (barra superior, barra de status, painéis de Notícias/Documentos, chat, diálogo de configuração de I.A. e aba Sobre), reutilizando a classe `ToolTip` endurecida.
- Testes unitários do ciclo de vida do `ToolTip` comprovam que uma segunda exibição sem `_leave` não deixa janela órfã.

#### Fixed

- `widgets/tooltip.py` passa a garantir que nunca haja mais de uma janela de tooltip viva por instância: cancela o `after` pendente no `_enter`, destrói a janela existente no `_show`, zera `_after_id` quando `_show` dispara e protege `after_cancel` contra `TclError`.

[Unreleased]: https://github.com/amaurycarvalho/flowscope/compare/v1.3.5...HEAD
[1.3.5]: https://github.com/amaurycarvalho/flowscope/releases/tag/v1.3.5

See [CHANGELOG Archive](CHANGELOG-ARCHIVE.md) for older releases.
