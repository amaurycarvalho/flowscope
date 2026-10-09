## MODIFIED Requirements

### Requirement: Manifesto estável como prefixo cacheável

O sistema DEVE compor um manifesto único enviado como prefixo de sistema, contendo: persona e regras, descrição da árvore, **o mapa dos caminhos canônicos de cada ramo**, metadados curtos de abas/sub-abas/indicadores/campos/grupos, o protocolo de navegação e as listas de chaves (tickers, campos, abas, indicadores, grupos), sem valores pesados. Metadados iguais ao nome do nó DEVEM ser omitidos por redundantes. O manifesto DEVE ser byte-a-byte idêntico entre turnos enquanto a assinatura do estado não mudar. O manifesto DEVE respeitar um teto de 4.000 tokens; ao estourar, o ramo mais volumoso DEVE degradar para "só chaves". A assinatura do estado DEVE ser derivada do conjunto de arquivos de cache (hash + mtime) — incluindo o ledger de guidance — e da watchlist.

#### Scenario: Mapa da árvore no manifesto
- **WHEN** o manifesto é montado
- **THEN** ele DEVE descrever os caminhos canônicos de cada ramo (ex.: `/documentos/<ticker>/curto`, `/guidance/<ticker>/<ano>/<mes>/<guidance>`, `/direitos-obrigacoes/direitos`, `/noticias/<grupo>/indice`), para a LLM navegar sem adivinhar

#### Scenario: Metadado redundante é omitido
- **WHEN** o metadado de um nó é igual ao seu nome
- **THEN** a linha correspondente NÃO DEVE integrar a seção de metadados do manifesto

#### Scenario: Manifesto idêntico entre turnos
- **WHEN** duas perguntas consecutivas são feitas sem mudança de estado
- **THEN** o manifesto DEVE ser byte-a-byte idêntico entre os turnos

#### Scenario: Reconstrução por mudança de estado
- **WHEN** fundamentos são recarregados, um resumo é cacheado, uma avaliação de guidance é registrada ou a watchlist muda
- **THEN** a assinatura DEVE mudar, o manifesto DEVE ser recomputado e a navegação acumulada DEVE ser descartada

#### Scenario: Teto do manifesto
- **WHEN** o manifesto excede 4.000 tokens para a watchlist canônica
- **THEN** o ramo mais volumoso DEVE degradar para "só chaves" e um teste de regressão DEVE falhar se o teto for excedido

#### Scenario: Metadado ausente degrada
- **WHEN** não há metadado curado para uma chave
- **THEN** o manifesto DEVE exibir apenas a chave, sem erro

## ADDED Requirements

### Requirement: Ramo /guidance da árvore de conhecimento

A árvore de conhecimento DEVE expor um ramo `/guidance` com o guidance avaliado em cache, agrupado por ticker, ano e mês da data do relatório, com uma folha por entrada de guidance que possua valor. Cada folha DEVE ter como conteúdo o texto formatado do guidance e o rótulo curado do Relatório Gerencial associado. O ramo DEVE ser montado apenas a partir do ledger em cache, sem avaliar, alterar ou reextrair nada, e DEVEM ser omitidos os tickers sem entrada de guidance com valor.

#### Scenario: Navegação do guidance
- **WHEN** a LLM lista `/guidance/<ticker>` e obtém uma folha de guidance
- **THEN** o sistema DEVE devolver os anos e meses como nós internos e, na folha, o texto formatado do guidance com o rótulo curado do Relatório Gerencial associado

#### Scenario: Ticker sem guidance com valor é omitido
- **WHEN** um ticker não possui nenhuma entrada de guidance com valor em cache
- **THEN** o nó `/guidance/<ticker>` NÃO DEVE existir na árvore

#### Scenario: Sem efeitos colaterais
- **WHEN** o chat navega o ramo `/guidance`
- **THEN** o ledger DEVE permanecer inalterado e nenhum PDF DEVE ser relido ou reextraído
