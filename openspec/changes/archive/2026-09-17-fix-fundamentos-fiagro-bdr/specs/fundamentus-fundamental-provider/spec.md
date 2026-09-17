## ADDED Requirements

### Requirement: Histórico de proventos de FII e FIAGRO

O sistema DEVE obter o histórico de proventos de FIIs e FIAGROs a partir da página de rendimentos de FII do Fundamentus (`fii_proventos.php?papel={TICKER}`), normalizando cada linha em um dividendo com data-base (coluna `Última Data Com`), valor por unidade (coluna `Valor`) e origem Fundamentus, tratando o tipo `Rendimento` como dividendo. Quando a página de ações (`proventos.php`) não retornar proventos, o sistema DEVE consultar a página de FII. A ausência de proventos DEVE resultar em lista vazia, distinta de falha de aquisição.

#### Scenario: Histórico extraído para FII
- **WHEN** a página `fii_proventos.php` de um FII contém linhas com `Última Data Com`, `Valor` e `Tipo` igual a `Rendimento`
- **THEN** o sistema DEVE retornar uma lista de dividendos com data-base e valor, preservando a origem Fundamentus

#### Scenario: Fallback acionado quando a página de ações está vazia
- **WHEN** `proventos.php` não retorna proventos para o ticker
- **THEN** o sistema DEVE consultar `fii_proventos.php` e usar o histórico encontrado

#### Scenario: Sem proventos em nenhuma página
- **WHEN** nem `proventos.php` nem `fii_proventos.php` retornam linhas válidas
- **THEN** o sistema DEVE retornar lista vazia sem erro

#### Scenario: Falha de rede
- **WHEN** a requisição à página de rendimentos de FII falha
- **THEN** o sistema DEVE sinalizar indisponibilidade, sem retornar dados parciais como se estivessem completos
