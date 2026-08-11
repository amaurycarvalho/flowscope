## ADDED Requirements

### Requirement: Testes matam mutantes sobreviventes em clipboard_image

A suíte de testes DEVE matar os 62 mutantes sobreviventes no módulo `flowscope.infrastructure.clipboard_image`, fortalecendo as assertions sobre argumentos passados a `subprocess.run` e `figure.savefig`.

#### Scenario: Mutação de check=True para check=None é detectada
- **WHEN** `_copy_linux` é chamada com um path válido
- **THEN** o teste DEVE verificar que `subprocess.run` foi chamado com `check=True`

#### Scenario: Mutação de string em argumento de subprocess é detectada
- **WHEN** `_copy_linux` é chamada com um path válido
- **THEN** o teste DEVE verificar que os argumentos incluem `"xclip"`, `"-selection"`, `"clipboard"`, `"-t"`, `"image/png"`

### Requirement: Testes matam mutantes sobreviventes em cache

A suíte de testes DEVE matar os 38 mutantes sobreviventes no módulo `flowscope.infrastructure.cache`, adicionando testes para métodos não cobertos e fortalecendo asserts sobre conteúdo escrito.

#### Scenario: find_nearest com cache disponível retorna a data correta
- **WHEN** existe um arquivo de cache para uma data próxima dentro do max_deviation
- **THEN** `find_nearest` DEVE retornar a data do cache mais próximo

#### Scenario: find_nearest sem cache retorna None
- **WHEN** não existe nenhum arquivo de cache dentro do max_deviation
- **THEN** `find_nearest` DEVE retornar None

#### Scenario: Mutação de encoding é detectada
- **WHEN** `put` ou `get_or_fetch` escreve um arquivo
- **THEN** o teste DEVE verificar que `write_text` foi chamado com `encoding="utf-8"`

### Requirement: Testes matam mutantes sobreviventes em generators

A suíte de testes DEVE matar os 31 mutantes sobreviventes no módulo `flowscope.infrastructure.b3.generators`, cobrindo todos os branches condicionais e validando saídas exatas.

#### Scenario: fibonacci_double_dates com period_days <= 30 usa offsets fixos
- **WHEN** `_fibonacci_double_dates` é chamada com `period_days=30`
- **THEN** DEVE retornar datas baseadas nos offsets `[1, 2, 3, 13, 19, 20, 21]`

#### Scenario: fibonacci_double_dates com period_days > 30 usa offsets dinâmicos
- **WHEN** `_fibonacci_double_dates` é chamada com `period_days=90`
- **THEN** DEVE retornar datas baseadas nos offsets dinâmicos da sequência de Fibonacci

#### Scenario: _fibs_up_to filtra offsets pelo limite
- **WHEN** `_fibs_up_to` é chamada com `limit=30`
- **THEN** DEVE retornar apenas offsets <= limit

### Requirement: Testes matam mutantes sobreviventes em calendar

A suíte de testes DEVE matar os 20 mutantes sobreviventes no módulo `flowscope.infrastructure.b3.calendar`, cobrindo combinações de `has_data=None` e `has_data=Callable`.

#### Scenario: resolve_dates com has_data=None usa dias úteis diretos
- **WHEN** `resolve_dates` é chamada com `has_data=None`
- **THEN** DEVE retornar apenas dias úteis, sem busca de dados

#### Scenario: _find_nearest_with_data com has_data sempre True retorna primeiro candidato
- **WHEN** `_find_nearest_with_data` é chamada com `has_data=lambda d: True`
- **THEN** DEVE retornar o candidate para delta=0 (a própria data)

### Requirement: Testes matam mutantes sobreviventes em repository

A suíte de testes DEVE matar os 49 mutantes sobreviventes no módulo `flowscope.infrastructure.b3.repository`, cobrindo `_has_data`, `fetch_trades` com diferentes flags e callbacks.

#### Scenario: _has_data retorna False para conteúdo vazio
- **WHEN** `_has_data` é chamada com uma data cujo cache contém apenas header
- **THEN** DEVE retornar False

#### Scenario: fetch_trades com cache_only=True não chama fetch_file com download
- **WHEN** `fetch_trades` é chamada com `cache_only=True`
- **THEN** DEVE passar `cache_only=True` para `fetch_file`

### Requirement: Testes matam mutantes sobreviventes em domain strategies

A suíte de testes DEVE matar os 135+ mutantes sobreviventes nos módulos de estratégia do domínio (`volume`, `flow`, `dominance`, `conviction`, `indicators`, `density`, `money_flow`), adicionando testes para edge cases e branches não cobertos.

#### Scenario: Cálculos de indicadores com valores zero não quebram
- **WHEN** um indicador recebe valores de entrada zero ou None
- **THEN** DEVE retornar resultado definido (None, 0, ou outro valor documentado)

#### Scenario: Mutações em operadores lógicos são detectadas
- **WHEN** um classificador recebe valores que caem exatamente no boundary
- **THEN** o teste DEVE verificar a saída esperada para ambas as direções da condição

### Requirement: Testes matam mutantes sobreviventes em módulos de prioridade média

A suíte de testes DEVE matar os mutantes sobreviventes nos módulos `b3.parser` (112), `b3.client` (99) e `application.use_cases` (144), fortalecendo asserts sobre parsing de CSV e chamadas HTTP.

#### Scenario: Mutação em campo de CSV é detectada
- **WHEN** `parse_csv` processa uma linha com um campo específico
- **THEN** o teste DEVE verificar o valor exato do campo no objeto resultante

#### Scenario: Mutação em parâmetro de requests.get é detectada
- **WHEN** `_request_token` ou `_download_csv` realiza uma chamada HTTP
- **THEN** o teste DEVE verificar que `requests.get` foi chamado com `params`, `timeout` e `url` corretos

### Requirement: Testes matam mutantes sobreviventes em módulos de prioridade baixa

A suíte de testes DEVE matar os mutantes sobreviventes nos módulos de apresentação (`cli`, `shortcuts`, `main`) e infraestrutura restante (`logging`), dentro do possível para código de interface.

#### Scenario: Funções CLI retornam valores esperados para argumentos válidos
- **WHEN** uma função CLI é chamada com argumentos simulados
- **THEN** DEVE retornar o código de saída ou resultado esperado

### Requirement: Mutantes impossíveis são excluídos via configuração

O `pyproject.toml` DEVE incluir padrões no `do_not_mutate_patterns` para mutações que não podem ser mortas com teste unitário, evitando falsos survivors.

#### Scenario: Padrão de log não gera mutante
- **WHEN** mutmut encontra `logger.info(...)`, `logger.warning(...)`, `logger.error(...)`
- **THEN** NÃO DEVE gerar mutantes para essas linhas

#### Scenario: Padrão de raise não gera mutante
- **WHEN** mutmut encontra `raise SomeError(...)`
- **THEN** NÃO DEVE gerar mutantes para essas linhas
