## ADDED Requirements

### Requirement: Subcomandos de navegação via CLI

O sistema DEVE aceitar o subcomando `flowscope nav <operacao> ...` para executar as operações de navegação diretamente pelo terminal, reusando o mesmo núcleo de navegação do chat e do servidor MCP. As operações DEVEM incluir `listar`, `obter`, `contar`, `existe`, `buscar`, `buscar-semantico` e `manifesto`. A saída padrão DEVE ser JSON estruturado em `stdout`; a flag opcional `--pretty` DEVE formatar a saída para leitura humana. `flowscope nav obter <caminho>` DEVE aceitar `--offset` e `--limite`, `flowscope nav buscar <caminho>` DEVE aceitar `--regex`, `--em` e `--max`, e `flowscope nav buscar-semantico <caminho>` DEVE aceitar `--consulta` e `--max`. As operações de listagem DEVEM aceitar `--cursor` para continuar a paginação. Erros de navegação DEVEM ser impressos como JSON estruturado em `stdout`; mensagens de diagnóstico DEVEM ir para `stderr`.

#### Scenario: Listagem por CLI

- **WHEN** o usuário executa `flowscope nav listar /noticias/grupos`
- **THEN** o sistema DEVE imprimir o JSON com os filhos imediatos e, quando houver continuação, o `nextCursor`

#### Scenario: Continuação por cursor

- **WHEN** o usuário executa `flowscope nav listar <caminho> --cursor <token>`
- **THEN** o sistema DEVE imprimir a página seguinte do resultado

#### Scenario: Leitura de conteúdo pesado

- **WHEN** o usuário executa `flowscope nav obter /documentos/PETR4/<chave>/texto --offset 0 --limite 12000`
- **THEN** o sistema DEVE imprimir o trecho correspondente com total, offset, limite e indicador de continuação

#### Scenario: Busca determinística por CLI

- **WHEN** o usuário executa `flowscope nav buscar /documentos/PETR4 --regex "..." --em titulo,texto --max 50`
- **THEN** o sistema DEVE imprimir os nós que casam, respeitando o limite de resultados

#### Scenario: Saída legível opcional

- **WHEN** o usuário adiciona `--pretty` a um subcomando `nav`
- **THEN** o sistema DEVE formatar o JSON para leitura humana

#### Scenario: Erro de navegação na CLI

- **WHEN** uma operação `nav` falha de forma recuperável
- **THEN** o sistema DEVE imprimir o erro estruturado com motivo, detalhe e dica, e o diagnóstico DEVE ir para `stderr`
