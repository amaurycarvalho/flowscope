## Context

O RFC-001 descreve a extração de rendimentos e amortizações via API `fundsListedProxy` da B3. O projeto FlowScope segue Clean Architecture com 4 camadas e protocolos para desacoplamento. Esta change adapta o RFC-001 a essa arquitetura de forma ticker-agnóstica: qualquer ticker pode ser consultado, com a fonte retornando dados apenas quando disponíveis (fundos listados na B3).

O projeto já possui um `B3Client` que interage com o mesmo domínio `sistemaswebb3-listados.b3.com.br`. Os módulos de extração de dados estruturados compartilham a etapa de resolução de ticker.

## Goals / Non-Goals

**Goals:**
- Criar entidades de domínio (`Entidade`, `Provento`, `DocumentoProvento`) e value objects (`CNPJ`, `ISIN`, `ValorProvento`) desacoplados da API B3
- Usar `Ticker` existente (genérico) — sem validação de sufixo FII
- Definir protocolo `ProventosRepository` na camada de aplicação
- Extender o `B3Client` com `B3FundosClient` reaproveitando padrões
- Implementar parsing flexível de HTML tabular
- Resolução de ticker que retorna `None` para tickers sem dados na API de fundos
- Expor via CLI com `--structured-earnings`
- `DocumentoProvento.to_text()` como precursor para VectorStore no `llm-chat`

**Non-Goals:**
- Selenium/Playwright para HTML dinâmico
- Persistência em banco de dados
- Paralelismo/async
- GUI nesta change

## Decisions

### 1. Módulo `domain/structured/` com entidades e value objects

Entidades em `domain/structured/entities.py`, value objects em `domain/structured/value_objects.py`. Uso do `Ticker` existente (genérico, sem sufixo obrigatório).

### 2. Protocolo `ProventosRepository` na camada de aplicação

```python
class ProventosRepository(Protocol):
    def resolver_ticker(self, ticker: str) -> str | None: ...
    def listar_documentos(self, id_fnet: str, data_inicio: date, data_fim: date, tipo: int) -> list[dict]: ...
    def extrair_detalhes(self, id_documento: str) -> DocumentoProvento: ...
```

### 3. `B3FundosClient` — composição com `CacheManager`

Classe independente que recebe `CacheManager` por injeção, seguindo o padrão de construção de token Base64 do `B3Client`.

### 4. `FundosRepository` implementando `ProventosRepository`

Repository separado do `B3DataRepository`, mesmo padrão de injeção de dependência.

### 5. BeautifulSoup para parsing HTML

Adicionado ao `pyproject.toml`. HTML da B3 é complexo; BeautifulSoup é canônico e leve (~300KB).

### 6. Resolução de ticker tolerante

`resolver_ticker()` retorna `None` (não lança exceção) para tickers sem dados na API de fundos. Cache também armazena `None` para evitar requisições repetidas.

### 7. `DocumentoProvento.to_text()` para VectorStore

Método que produz representação textual densa do documento, adequada para chunking e embedding no `llm-chat`.

### 8. Estrutura de diretórios

```
src/flowscope/
├── domain/
│   └── structured/
│       ├── __init__.py
│       ├── entities.py          # Entidade, Provento, DocumentoProvento
│       └── value_objects.py     # CNPJ, ISIN, ValorProvento
├── application/
│   ├── structured_ports.py      # ProventosRepository protocol
│   └── structured_use_cases.py  # ExtrairProventosUseCase
├── infrastructure/b3/
│   ├── funds_client.py          # B3FundosClient
│   ├── structured_parser.py     # HTML parsing
│   └── structured_repository.py # FundosRepository
└── presentation/cli.py
```

## Risks / Trade-offs

- **[Risco] Mudança na estrutura HTML da B3** → Estratégias encadeadas mitigam; campos não encontrados ficam `None`
- **[Trade-off] Sem GUI** → Escopo gerenciável; GUI é extensão futura
