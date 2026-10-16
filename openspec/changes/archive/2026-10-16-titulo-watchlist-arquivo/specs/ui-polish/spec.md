## MODIFIED Requirements

### Requirement: Título dinâmico da janela

A janela DEVE exibir no título o nome do arquivo de watchlist atualmente aberto, no formato `FlowScopeBR v{versão} — <arquivo>[*]`, onde `<arquivo>` é o nome-base (sem path) do arquivo carregado ou salvo e `[*]` é um asterisco exibido quando o conteúdo do watchlist foi editado e ainda não foi salvo. Quando não houver arquivo associado, o sistema DEVE exibir `Nova lista.txt` no lugar de `<arquivo>`. Ao carregar ou salvar um arquivo, o título DEVE refletir o nome-base sem asterisco. Ao editar o conteúdo do watchlist (adicionar ou remover tickers), o asterisco DEVE ser exibido; mudanças de seleção ou de filtro NÃO DEVEM exibir o asterisco. Ao preencher a lista por um botão de índice (IBOV/IDIV/IFIX), o sistema DEVE exibir `<ÍNDICE>.txt` sem asterisco. Ao iniciar com um arquivo de watchlist guardado, o título DEVE exibir o nome-base correspondente.

#### Scenario: Título após carregamento

- **WHEN** o usuário carrega a watchlist do arquivo `/home/user/dados/petr4.txt`
- **THEN** o título DEVE ser `FlowScopeBR v{versão} — petr4.txt`, sem asterisco

#### Scenario: Título após salvar arquivo

- **WHEN** o usuário salva a watchlist no arquivo `carteira.txt`
- **THEN** o título DEVE passar a `FlowScopeBR v{versão} — carteira.txt`, sem asterisco

#### Scenario: Asterisco após editar o conteúdo

- **WHEN** o usuário adiciona ou remove tickers do conteúdo do watchlist
- **THEN** o título DEVE exibir o asterisco ao lado do nome do arquivo

#### Scenario: Seleção não marca alteração

- **WHEN** o usuário apenas marca ou desmarca tickers na listbox (filtro)
- **THEN** o título NÃO DEVE exibir o asterisco

#### Scenario: Título após botão de índice

- **WHEN** o usuário clica no botão "IBOV"
- **THEN** o título DEVE ser `FlowScopeBR v{versão} — IBOV.txt`, sem asterisco

#### Scenario: Título sem arquivo

- **WHEN** a aplicação inicia e não há arquivo de watchlist guardado
- **THEN** o título DEVE exibir `Nova lista.txt` no lugar do nome do arquivo

#### Scenario: Título restaurado ao iniciar

- **WHEN** a aplicação inicia e há o arquivo `/home/user/dados/petr4.txt` guardado
- **THEN** o título DEVE exibir `FlowScopeBR v{versão} — petr4.txt`
