## Context

Atualmente o sistema baixa a carteira do IDIV através de `B3Client.fetch_idiv_portfolio()`, que usa uma URL hardcoded com token base64 fixo para `{"index":"IDIV","language":"pt-br"}`. O parser `parse_idiv_csv()` também é específico para IDIV. A GUI expõe apenas o autopreenchimento silencioso com IDIV — sem botões visíveis para outros índices.

O endpoint `GetDownloadPortfolioDay` da B3 é genérico: qualquer código de índice pode ser passado no payload JSON, codificado em base64 na URL. O CSV retornado segue sempre o mesmo formato (colunas: `Codigo;Acao;Tipo;Qtde Teorica;Part.(%)`), variando apenas o prefixo na primeira linha descritiva (`"IBOV - ..."`, `"IDIV - ..."`, etc.).

## Goals / Non-Goals

**Goals:**
- Generalizar o download para qualquer índice B3 via parâmetro `index`
- Generalizar o parser para ignorar qualquer linha de cabeçalho/rodapé, independente do nome do índice
- Substituir `fetch_idiv_portfolio()` e `parse_idiv_csv()` por versões genéricas
- Adicionar botões "IBOV", "IDIV", "IFIX" na interface
- Extrair lógica de autopreenchimento para `_fill_with_index("IDIV")`
- Atualizar cache para usar chave por `(índice, data)` em vez de fixa

**Non-Goals:**
- Não incluir download da carteira como parte do fluxo do use case — continua sendo chamado diretamente da GUI (infraestrutura pura)
- Não adicionar seletor de índice genérico (dropdown) — apenas os 3 botões fixos
- Não modificar o fluxo de download de trades (TradeInformationConsolidated)
- Não afetar o cache de CSVs diários

## Decisions

### 1. Generalização do B3Client

**Decisão:** Criar `fetch_portfolio(index: str, language: str = "pt-br") -> list[str]` que constrói a URL dinamicamente via base64 do payload JSON. Manter `fetch_idiv_portfolio()` como wrapper para compatibilidade durante a migração, depois remover.

```python
def _build_portfolio_url(self, index: str, language: str = "pt-br") -> str:
    payload = json.dumps({"index": index, "language": language}, separators=(",", ":"))
    b64 = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
    return f"{self._BASE_PORTFOLIO_URL}{b64}"

def fetch_portfolio(self, index: str, language: str = "pt-br") -> list[str]:
    url = self._build_portfolio_url(index, language)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    raw = resp.text.strip()
    decoded = base64.b64decode(raw).decode("latin-1") if _is_base64(raw) else raw
    return parse_index_csv(decoded, index)
```

**Alternativa considerada:** Manter URLs hardcoded para IBOV, IDIV, IFIX. Rejeitada porque o endpoint é totalmente genérico — não faz sentido duplicar.

### 2. Generalização do parser

**Decisão:** Renomear `parse_idiv_csv()` → `parse_index_csv()` e remover a verificação `startswith("IDIV -")`. Em vez disso, pular qualquer linha que comece com palavras-chave de rodapé (`Quantidade`, `Redutor`) ou linhas vazias. Detectar cabeçalho pelo valor exato `"Código"`.

```python
def parse_index_csv(content: str) -> list[str]:
    tickers = []
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(";")
        ticker = parts[0].strip()
        if not ticker or ticker in ("Código", "Código"):
            continue
        if ticker.startswith("Quantidade") or ticker.startswith("Redutor"):
            continue
        # Pula primeira linha descritiva (ex: "IBOV - Composição...")
        if not ticker.isupper() or not ticker.isascii():
            continue
        tickers.append(ticker)
    return tickers
```

**Alternativa considerada:** Receber `index` como parâmetro e verificar `startswith(f"{index} -")`. Rejeitada porque a verificação por uppercase+ascii cobre todos os casos sem precisar passar o nome do índice.

### 3. Cache por índice

**Decisão:** Mudar chave de cache de `"idiv_portfolio_v2"` para `f"portfolio_{index}"`. O TTL de 7 dias permanece. Cada índice tem seu próprio cache independente.

```python
def fetch_portfolio(self, index: str) -> list[str]:
    def _fetch():
        ...
        return {"tickers": tickers, "index": index}
    data = self._cache.get_or_fetch(f"portfolio_{index}", ttl_days=7, fetch_fn=_fetch)
    return data["tickers"]
```

### 4. Botões na interface

**Decisão:** Adicionar os 3 botões em uma nova fileira (`btn_frame2`) abaixo dos botões existentes no `TickerList`. Cada botão recebe um callback específico via parâmetro.

```python
# Novo parâmetro: on_index_click: dict[str, callable] | None
# Ex: {"IBOV": self._on_ibov, "IDIV": self._on_idiv, "IFIX": self._on_ifix}
```

A lógica geral é extraída para `_fill_with_index(index)` em `FlowScopeGUI`:

```python
def _fill_with_index(self, index: str) -> None:
    tickers = self._repo.get_index_tickers(index)
    if tickers:
        self._ticker_list.set_tickers(tickers)
        self._flash_status(f"Carteira {index} carregada com {len(tickers)} ativos.")
    else:
        self._flash_status(f"Não foi possível carregar a carteira {index}.", "⚠")
```

`_ensure_tickers()` e `_on_ticker_edit()` passam a chamar `_fill_with_index("IDIV")`.

### 5. Camada Repository

**Decisão:** Substituir `get_idiv_tickers()` por `get_index_tickers(index: str) -> list[str]` que chama `self._client.fetch_portfolio(index)`.

## Risks / Trade-offs

- **Risco:** O parser genérico baseado em `isupper() + isascii()` pode falhar se a B3 mudar o formato do CSV. **Mitigação:** Testes com CSVs reais de IBOV, IDIV e IFIX.
- **Risco:** Cache independente por índice pode crescer (muitos índices consultados). **Mitigação:** TTL de 7 dias + apenas 3 índices expostos na UI.
- **Trade-off:** Manter cache na `B3Client` em vez de migrar para `B3DataRepository` preserva a simplicidade atual, mas mantém a lógica de cache fora da camada de aplicação. Aceitável porque portfolio fetching é infraestrutura pura.
