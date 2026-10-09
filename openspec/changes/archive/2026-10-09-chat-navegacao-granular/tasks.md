## 1. Documentos — índice e nó por item

- [x] 1.1 Refatorar `FonteDocumentos._construir_ticker` (`application/chat/documentos.py`) para montar `/documentos/<ticker>/indice` (linha por documento, mais recente primeiro, com categoria/período/nome e sinalização de resumo/texto, teto de chars) e um nó interno `/documentos/<ticker>/<chave>` por documento recuperável, com folhas `curto`/`longo`/`texto` próprias; remover as folhas agregadas do ticker. Verificar com teste de árvore
- [x] 1.2 Derivar a chave curta e estável do documento (hash do caminho relativo) e preencher `metadado` (`<categoria> — <mmm/aa> — <nome>`) e `campos={"categoria","periodo","nome"}` no nó do documento e no índice; omitir folha de resumo sem dado. Verificar com teste
- [x] 1.3 Garantir que o `texto` de cada documento é lido do `text_store` uma única vez por ticker e truncado por `TETO_DOCUMENTO`, sem concatenar documentos. Verificar com teste de documento alvo presente no `texto`
- [x] 1.4 Verificar por teste que `obter(/documentos/<ticker>/indice)` começa pelo documento mais recente e que o `texto` do nó escolhido contém o integral daquele documento

## 2. Guidance — índice por ticker

- [x] 2.1 Adicionar `/guidance/<ticker>/indice` em `FonteGuidance` (`application/chat/guidance.py`), agregando as entradas em ordem decrescente com `<mmm/aa>: <guidance> — <rótulo do RG>`, reutilizando `agrupar_entradas`/`rotulo_relatorio_gerencial`. Verificar com teste
- [x] 2.2 Adicionar `campos` pesquisáveis (`periodo`, `guidance`, `relatorio`) às folhas de guidance. Verificar com teste de busca por período

## 3. Foco de referência entre turnos

- [x] 3.1 Registrar o caminho do último `obter` bem-sucedido como `foco` no `_Estado` (`application/chat/consultar.py`) e incluí-lo no bloco serializado do turno via `ProtocoloNavegacao.serializar` (`application/chat/protocolo.py`). Verificar com teste de resposta contendo `foco`
- [x] 3.2 Descartar o `foco` junto da navegação acumulada em `resetar_navegacao`, mudança de assinatura e "Limpar". Verificar com teste

## 4. Playbook, abas/sub-abas e teto de metadado no manifesto

- [x] 4.1 Adicionar ao manifesto (`application/chat/manifesto.py`) o playbook de intenção→ramo (guidance via índice; documento mais recente via `/documentos/<ticker>/indice`; resumo via `curto`/`longo`; detalhe profundo via `.../<chave>/texto`; app via `/flowscope/abas`/`meta`) e reforçar a cascata resumo→detalhe no `SYSTEM_PROMPT` (`application/chat/consultar.py`). Verificar com teste do texto do manifesto/prompt
- [x] 4.2 Anunciar `/flowscope/abas/<aba>` em `_caminhos_flowscope` e nomear as sub-abas por aba nas listas de chaves. Verificar com teste do manifesto
- [x] 4.3 Aplicar teto curto a `_metadados` para não integrar metadados longos e preservar os curtos; verificar com teste de manifesto sem o texto integral de sub-aba
- [x] 4.4 Verificar que o manifesto continua determinístico e dentro de 4.000 tokens com os novos ramos, mantendo o teste de regressão de teto
- [x] 4.5 Rotular as folhas `curto`/`longo`/`texto` com metadado legível, excluir esses metadados de documento da seção de metadados do manifesto e orientar a cascata de resumos no playbook/prompt (resumo -> `curto`/`longo`; detalhe profundo -> `texto`). Verificar com testes
- [x] 4.6 Corrigir a orientação após feedback: comentar/analisar um documento deve abrir o `texto` integral do alvo (não parar em `curto`/`longo`), resumo/lista de vários usa `longo`/`curto`, e o Relatório Gerencial mensal é identificado pelo `/guidance/<ticker>/indice` (a categoria de cache não distingue RG de cartas). Verificar com testes do manifesto/prompt
- [x] 4.7 Tornar o índice autoexplicativo: trecho curto do resumo (corte em fim de frase/palavra), tipo `RG mensal`/`documento` derivado do ledger de guidance (resolvedor `rg_chaves` injetado em `FonteDocumentos` a partir do `chat_panel`) e sinalização `posição/total` para repetidos no mês. Verificar com testes de índice
- [x] 4.8 Orientar no manifesto/prompt a não prometer navegação (emitir `solicitacoes` com `resposta` nulo quando faltam dados) e a reusar o `foco`. Verificar com testes
- [x] 4.9 Rotular a prévia do índice e orientar explicitamente o resumo curto (`/curto`) e o longo (`/longo`) no playbook/prompt, para a LLM não confundir a prévia com o resumo nem pular o `/curto`. Verificar com testes

## 5. Verificação integrada

- [x] 5.1 Executar `make lint` e `make complexity` sem erros
- [x] 5.2 Executar `make test` (cobertura ≥ 85%) sem erros
- [x] 5.3 Confirmar manualmente no Chat AI o encadeamento do exemplo: evolução do guidance do ALZR11 (`/guidance/ALZR11/indice`), RG mais recente (`/documentos/ALZR11/indice` → `/documentos/ALZR11/<chave>/texto`), "o que mais há nesse RG" pelo `foco`, período do último RG pelos metadados, e as perguntas sobre o FlowScope pelas abas/sub-abas
