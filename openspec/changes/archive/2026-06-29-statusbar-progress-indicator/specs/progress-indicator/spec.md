## ADDED Requirements

### Requirement: Barra de progresso determinate na statusbar

O sistema SHALL exibir uma barra de progresso determinate (`ttk.Progressbar`) na statusbar durante o carregamento de dados externos, acompanhada de um rótulo textual descrevendo a etapa atual.

#### Scenario: Barra visível durante carregamento
- **WHEN** o usuário clica em "Carregar" ou seleciona um índice (IBOV/IDIV/IFIX)
- **THEN** a statusbar SHALL exibir uma `ttk.Progressbar` no modo determinate
- **AND** a statusbar SHALL exibir um rótulo textual lado a lado com a barra
- **AND** a barra SHALL refletir o progresso real da operação

#### Scenario: Carregamento concluído
- **WHEN** o carregamento termina com sucesso
- **THEN** a barra SHALL atingir 100%
- **AND** o rótulo SHALL exibir "Pronto." ou mensagem de sucesso similar
- **AND** após 2.5s a statusbar SHALL retornar ao estado ocioso (apenas texto)

### Requirement: Fases de progresso

O progresso SHALL ser dividido em fases ponderadas por peso relativo, refletindo as etapas reais do pipeline de carregamento.

#### Scenario: Múltiplas fases são reportadas
- **WHEN** o carregamento inclui portfólio, download de datas e processamento de indicadores
- **THEN** o progresso SHALL refletir cada fase sequencialmente
- **AND** o rótulo SHALL atualizar o nome da fase atual

#### Scenario: Pesos relativos entre fases
- **WHEN** uma fase tem peso maior que outra
- **THEN** a barra SHALL avançar proporcionalmente mais durante aquela fase

### Requirement: Cache refletido no progresso

Quando os dados da data já estão em cache, o progresso SHALL avançar imediatamente sem pausa.

#### Scenario: Todas as datas em cache
- **WHEN** todas as datas estão em cache
- **THEN** o progresso SHALL avançar rapidamente de 0% a 100%
- **AND** a barra SHALL atingir 100% sem travamentos ou saltos abruptos

#### Scenario: Cache parcial
- **WHEN** algumas datas estão em cache e outras não
- **THEN** as datas em cache SHALL ser processadas sem delay perceptível
- **AND** as datas não cacheadas SHALL mostrar progresso normal por data

### Requirement: Falhas refletidas no progresso

Quando o download ou parsing de uma data falha, o progresso SHALL contabilizar a falha e continuar.

#### Scenario: Data falha durante carregamento
- **WHEN** uma data específica falha ao ser baixada ou processada
- **THEN** o progresso SHALL avançar mesmo na falha (a data é contada como processada)
- **AND** o rótulo SHALL incluir o número de falhas (ex: "Baixando 3/7 (1 falhou)")
- **AND** o carregamento SHALL continuar com as demais datas

#### Scenario: Múltiplas falhas
- **WHEN** múltiplas datas falham consecutivamente
- **THEN** o progresso SHALL continuar avançando
- **AND** ao final, o rótulo SHALL indicar o total de falhas

### Requirement: Portfolio loading como etapa textual

O carregamento de portfólio (IBOV/IDIV/IFIX) SHALL ser reportado como uma etapa textual na progressão.

#### Scenario: Portfolio carregado via botão de índice
- **WHEN** o usuário clica em IBOV, IDIV ou IFIX
- **THEN** a statusbar SHALL exibir "Baixando portfólio IBOV..."
- **AND** a barra de progresso SHALL ser exibida (mesmo sendo etapa única)
- **AND** ao concluir, SHALL mostrar "Carteira IBOV carregada com N ativos."

#### Scenario: Portfolio carregado automaticamente
- **WHEN** o sistema carrega IDIV automaticamente via `_ensure_tickers()`
- **THEN** o progresso SHALL incluir esta etapa como parte do pipeline
- **AND** o rótulo SHALL indicar "Baixando portfólio IDIV..."
