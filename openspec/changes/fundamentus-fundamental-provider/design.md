## Context

O `FundamentusProvider` existente (`infrastructure/fii/ffo_provider.py`) cobre apenas o FFO 12m/3m e retorna `FfoObservacao`; a RFC-011 especifica um provider completo. As changes `b3-fii-identity-and-dividends` (B3), `cvm-monthly-fund-data` (CVM) e `deterministic-ffo-engine` (motor de FFO) fornecem fontes alternativas, que agora passam a ser fallback. Ver `proposal.md` para motivação.

O projeto usa `requests` + `beautifulsoup4` e convenções de domínio com `decimal.Decimal`, dataclasses e portas (Protocol) para desacoplar infraestrutura. O wiring da GUI (change B3) já prevê execução em background com progresso.

## Goals / Non-Goals

**Goals:**
- Implementar o provider do Fundamentus conforme RFC-011, normalizado ao domínio do projeto.
- Tornar o Fundamentus a fonte primária da análise fundamentalista.
- Compor fontes com prioridade por campo e proveniência.
- Detectar quebras de layout com testes de contrato.

**Non-Goals:**
- Persistência em banco ou cache distribuído.
- Dados intraday/séries históricas.
- Novas dependências (`httpx`/`lxml`/`pydantic`).
- Substituir o motor de métricas ou o motor de FFO; eles permanecem como fallback.

## Decisions

### 1. Estrutura fetch/parse/model em pacote próprio

`infrastructure/fii/fundamentus/` com `client.py` (fetch + rate-limit + robots), `parser.py` (rótulos → valores) e `model.py`/domínio. `ffo_provider.py` permanece como adaptador fino que usa o provider e expõe `obter_ffo` para compatibilidade.

**Alternativa:** manter tudo em um arquivo — rejeitada por dificultar testes e evolução independente (RFC-011 §13).

### 2. Modelo normalizado em `Decimal` com mapa bruto

O modelo (`AtivoFundamental`) usa `Decimal`/`date` e campos opcionais, guardando também o mapa bruto rótulo→valor. **Alternativa:** usar `float` como no código de referência — rejeitada por contrariar a convenção do domínio (`metrics.py`).

### 3. Dependências existentes e rate-limit

Usar `requests` + `BeautifulSoup(..., "html.parser")`, com rate-limit de 1 req/s e checagem de `robots.txt`, em vez de `httpx`/`lxml`/`pydantic`. **Alternativa:** adotar a stack da RFC-011 — rejeitada para não introduzir dependências sem ganho comprovado.

### 4. Composição por campo com proveniência

Nova porta `FundamentalDataProvider` que retorna um conjunto normalizado de campos com origem; `CompositeFundamentalProvider` consulta o Fundamentus e, por campo ausente, os fallbacks (B3/CVM/motor de FFO). O isolamento por ticker é preservado.

**Alternativa:** fallback "tudo ou nada" por provedor — rejeitada porque o usuário quer cobrir também "informação não encontrada".

### 5. Integração sem duplicar cálculo

O caso de uso consome o provider composto; quando o valor é reportado pelo Fundamentus, usa-o diretamente com proveniência; quando vem do fallback por componentes, reaproveita `analisar_snapshot`/motor de FFO. **Alternativa:** forçar sempre o cálculo a partir de `FiiSnapshot` — rejeitada por divergir dos valores reportados e exigir derivar cotas/NAV.

### 6. Erros tipados e layout

`FundamentusError` com subtipos `TickerNotFound`, `LayoutChanged`, `NetworkError`; `LayoutChanged` quando nome e cotação ausentes. O composite trata essas falhas como "campo indisponível" e segue para o fallback.

## Risks / Trade-offs

- **[Risco] Parsing frágil por rótulo textual** → Fixtures de contrato e detecção explícita de `LayoutChanged`.
- **[Risco] Rate-limit/instabilidade do Fundamentus** → 1 req/s, backoff e fallback automático para B3/CVM/FFO.
- **[Risco] Disponibilidade incerta de campos para FIIs** → Campos opcionais com `N/A` e proveniência; fallback cobre ausências.
- **[Trade-off] Dois caminhos de montagem de métricas** (reportado vs. calculado) → Documentar a precedência e registrar a origem por campo.
- **[Trade-off] Escopo amplo da RFC-011** → Modelo completo, integração inicial limitada aos campos da tabela.

## Migration Plan

1. Criar o pacote `fundamentus/` e o modelo, com testes de normalizadores e fixtures.
2. Implementar fetch/parse e os testes de contrato (ação e FII).
3. Introduzir a porta `FundamentalDataProvider` e o `CompositeFundamentalProvider`.
4. Integrar ao `FundamentalAnalysisUseCase` como primário; manter o caminho B3/CVM/FFO como fallback.
5. Manter `obter_ffo` como adaptador; ajustar o wiring em background.
6. Rollback: desativar o primário e voltar ao provider de fallback sem alterar a tabela.
