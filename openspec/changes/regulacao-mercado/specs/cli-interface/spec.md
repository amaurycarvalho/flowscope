## ADDED Requirements

### Requirement: Argumentos CLI para dados regulatórios
O sistema DEVE aceitar novos argumentos de linha de comando para extração de dados regulatórios e de mercado:

- `--fatos-relevantes <TICKER>`: Extrai fatos relevantes, assembleias e avisos do ticker especificado via `GetMaterialFacts`
- `--noticias`: Lista notícias do Plantão B3
- `--regulacao`: Extrai Censuras Públicas e Condições Excepcionais da B3
- `--categoria <CODIGO>`: Filtra categoria de documento para `--fatos-relevantes` (1=Assembleias, 3=Aviso Acionistas, 4=Fatos Relevantes, 48=Aviso Debenturistas, 107=Relatório Proventos)
- `--palavra <TERMO>`: Filtra notícias por palavra-chave (usado com `--noticias`)

#### Scenario: Extração de fatos relevantes de um ticker
- **WHEN** o usuário executa `flowscope --fatos-relevantes PETR4 --data-inicio 2026-01-01 --data-fim 2026-06-30`
- **THEN** o sistema DEVE resolver o codeCVM de PETR4, consultar `GetMaterialFacts` para todas as categorias e exibir os resultados em JSON no stdout

#### Scenario: Extração de fatos relevantes com categoria específica
- **WHEN** o usuário executa `flowscope --fatos-relevantes PETR4 --categoria 4`
- **THEN** o sistema DEVE consultar apenas a categoria Fatos Relevantes (4)

#### Scenario: Listagem de notícias com filtro de data
- **WHEN** o usuário executa `flowscope --noticias --data-inicio 2026-07-01 --data-fim 2026-07-29`
- **THEN** o sistema DEVE listar notícias do Plantão B3 no período e exibir em JSON no stdout

#### Scenario: Listagem de notícias com palavra-chave
- **WHEN** o usuário executa `flowscope --noticias --palavra PETROBRAS --data-inicio 2026-01-01 --data-fim 2026-12-31`
- **THEN** o sistema DEVE filtrar notícias que contenham "PETROBRAS" no título

#### Scenario: Extração de dados regulatórios da B3
- **WHEN** o usuário executa `flowscope --regulacao`
- **THEN** o sistema DEVE extrair Censuras Públicas e Condições Excepcionais e exibir em JSON no stdout

#### Scenario: Reutilização de argumentos de data existentes
- **WHEN** `--data-inicio` e `--data-fim` são usados com `--fatos-relevantes` ou `--noticias`
- **THEN** os argumentos DEVEM filtrar o período de consulta, mesmo comportamento já definido para `--structured-earnings`
