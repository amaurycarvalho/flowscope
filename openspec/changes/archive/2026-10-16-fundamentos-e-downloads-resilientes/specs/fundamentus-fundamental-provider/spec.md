## ADDED Requirements

### Requirement: Host do Fundamentus coberto pelo certificado

O sistema DEVE consultar o Fundamentus pelo host cujo certificado TLS cobre o nome de destino (o domínio exibido no certificado), em todos os endpoints usados (`detalhes.php`, `proventos.php`, `fii_proventos.php` e `robots.txt`), de modo que a validação de certificado não falhe por incompatibilidade de nome. Uma falha de verificação TLS DEVE ser tratada como indisponibilidade da fonte, distinta de ticker ausente.

#### Scenario: Endpoints usados no host do certificado
- **WHEN** o sistema obtém dados, proventos de ações, rendimentos de FII e `robots.txt`
- **THEN** todas as requisições DEVEM usar o host coberto pelo certificado

#### Scenario: Falha de verificação TLS é indisponibilidade
- **WHEN** a conexão ao Fundamentus falha por incompatibilidade de nome no certificado
- **THEN** a fonte DEVE ser considerada indisponível e a análise DEVE prosseguir pelos fallbacks

### Requirement: Degradação controlada da fonte primária

Quando a fonte primária (Fundamentus) estiver indisponível, o sistema DEVE registrar a indisponibilidade no log por ticker e prosseguir com as fontes de fallback, sem interromper a análise dos demais tickers. A indisponibilidade da fonte primária NÃO DEVE ser silenciosa.

#### Scenario: Fonte primária indisponível é registrada
- **WHEN** o Fundamentus fica indisponível para um ticker
- **THEN** o log DEVE registrar a fonte indisponível e o ticker, e a análise DEVE continuar pelos fallbacks

#### Scenario: Demais tickers não são interrompidos
- **WHEN** o Fundamentus está indisponível para um ticker
- **THEN** a análise dos demais tickers DEVE continuar normalmente
