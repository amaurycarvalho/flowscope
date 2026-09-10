## Why

A sub-aba "Fundamentos" precisa de uma fonte primária de dados fundamentalistas. O `FundamentusProvider` atual extrai apenas o FFO 12m/3m, enquanto a RFC-011 especifica um provider completo (identidade, cotação, indicadores, balanço, demonstrativos e dados de FII) que já entrega `P/VP`, `FFO Yield`, `Div. Yield`, `FFO/Cota` e `VP/Cota`. Esta change implementa esse provider como **fonte primária** da tabela e adiciona uma camada de composição que usa B3 (RFC-008), CVM (RFC-009) e o motor de FFO (RFC-010) como **fallback por campo**, quando a conexão/scraping do Fundamentus falhar ou um dado específico não for encontrado.

## What Changes

- Implementação do provider do Fundamentus conforme RFC-011 (`detalhes.php?papel={TICKER}`): fetch, parsing tolerante a mudanças de layout, normalização para `Decimal`/`date` e modelo tipado para ações e FIIs.
- Novo modelo de domínio normalizado com proveniência por campo, usado para compor a análise fundamentalista.
- Camada de composição de provedores com prioridade por campo: Fundamentus primeiro; B3/CVM/motor-FFO como fallback; o resultado registra de qual fonte veio cada valor.
- Integração do provider composto ao `FundamentalAnalysisUseCase` como caminho primário; as fontes das changes anteriores deixam de ser o caminho principal e passam a ser substitutas.
- Reuso das dependências existentes (`requests` + `beautifulsoup4`), sem `httpx`/`lxml`/`pydantic`; rate-limit de 1 req/s e respeito a `robots.txt`.
- Pacote `infrastructure/fii/fundamentus/` (fetch, parser, modelo), mantendo `obter_ffo` como adaptador fino para compatibilidade.

## Capabilities

### New Capabilities

- `fundamentus-fundamental-provider`: Extração e normalização determinística dos dados fundamentalistas de ações e FIIs a partir do portal Fundamentus, com modelo tipado, tratamento de erros (ticker inexistente, layout alterado, falha de rede), rate-limit e fixtures de contrato.
- `fundamental-source-fallback`: Composição de fontes fundamentalistas com prioridade por campo (Fundamentus primário; B3, CVM e motor de FFO como fallback) e proveniência da origem de cada valor.

### Modified Capabilities

<!-- Nenhuma: a exibição continua coberta pela requirement genérica da sub-aba. -->

## Impact

- **Código afetado**: novo pacote `infrastructure/fii/fundamentus/`, novo modelo em `domain/fii/`, `application/fundamental_analysis.py` (provider composto), `infrastructure/fii/ffo_provider.py` (adaptador de compatibilidade), wiring da GUI (change `b3-fii-identity-and-dividends`).
- **APIs**: `https://www.fundamentus.com.br/detalhes.php` (público, sem credenciais); B3/CVM apenas como fallback.
- **Dependências**: nenhuma nova; mantém `requests` + `beautifulsoup4`.
- **Escopo faseado**: o modelo completo da RFC-011 é implementado; a integração inicial cobre os campos da tabela (`nome`, `P/VP`, `Dividend Yield`, `FFO Yield`, `P/FFO`, `FFO Trend`), com os demais campos disponíveis para uso futuro.
