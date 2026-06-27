## Context

O FlowScope carrega dados consolidados de negociação da B3 (TradeInformationConsolidated) para uma janela temporal de Fibonacci. Atualmente:

- O sistema carrega **todos** os tickers disponíveis quando o filtro está vazio, usando `select_top_tickers()` para pegar os de maior volume — o que pode incluir centenas de ativos, muitos irrelevantes para análise de dividendos
- O parser aceita **todas** as linhas do CSV, incluindo segmentos não-CASH (BMF, FUTURE, etc.) que poluem os dados
- Não há cache de portfólio de índices — cada execução precisaria buscar a carteira do zero

Este design cobre a busca da carteira do IDIV como filtro padrão e a filtragem por segmento CASH.

## Goals / Non-Goals

**Goals:**
- Buscar a carteira do IDIV via endpoint próprio da B3
- Cachear o portfólio com TTL (7 dias) para evitar requisições desnecessárias
- Filtrar linhas do CSV para manter apenas `SgmtNm == "CASH"`
- Quando o filtro de tickers estiver vazio, preencher automaticamente com os tickers do IDIV
- Permitir que o usuário edite manualmente a lista após o preenchimento automático

**Non-Goals:**
- Não criar uma UI separada para seleção de índices (IDIV é o único índice suportado)
- Não modificar o fluxo de Fibonacci ou datas de download
- Não alterar os indicadores calculados (VWAP, CVD)
- Não adicionar dependências externas

## Decisions

### 1. Local do fetch IDIV: novo método em B3Client

Criar `B3Client.fetch_idiv_portfolio() -> list[str]` que faz GET no endpoint:
```
https://sistemaswebb3-listados.b3.com.br/indexProxy/indexCall/GetDownloadPortfolioDay/<token>
```
O token é base64 de `{"index":"IDIV","language":"pt-br"}` — mantido como constante codificada.

**Alternativa considerada:** Um `IndexPortfolioClient` separado. Rejeitado porque a responsabilidade é similar (cliente HTTP para API da B3) e o B3Client já gerencia cache.

### 2. Cache do portfólio: CacheManager com TTL

Reutilizar `CacheManager` existente, mas com suporte a TTL. O cache de CSV é permanente (nunca expira), mas o portfólio IDIV deve expirar após 7 dias (rebalanceamento quadrimestral, mas 7 dias é conservador).

O cache armazena: `{ "tickers": ["ABCB4", "ALOS3", ...], "cached_at": "2026-06-27T10:00:00" }`. Ao ler, verifica se `cached_at` + 7 dias > now. Se expirado, busca novamente e atualiza.

**Alternativa considerada:** Cache sem TTL, forçando refresh manual. Rejeitado porque o IDIV rebalanceia e o usuário pode não saber que precisa limpar o cache.

### 3. Filtro CASH no parser

Adicionar parâmetro `segment_filter: str | None = "CASH"` em `parse_csv()`. Linhas cujo `SgmtNm` não corresponder são ignoradas. Default `"CASH"` para manter compatibilidade com o fluxo existente.

**Alternativa considerada:** Filtrar no repositório (pós-parse). Rejeitado porque filtrar cedo reduz memória e acelera o parse. Se no futuro precisar de outros segmentos, basta passar `segment_filter=None`.

### 4. Auto-preenchimento na GUI

Em `_on_load_data()` e `_on_ticker_edit()`, antes de executar o caso de uso:

```
se tickers vazio:
    tickers = buscar IDIV
    preencher campo de texto
```

Isolation: o `TickerList` ganha um método `load_idiv()` que preenche o campo e aplica o filtro. A busca do IDIV é via repositório.

### 5. Parse do CSV do IDIV

O CSV retornado tem formato:
```
IDIV - Carteira do Dia 29/06/26
Código;Ação;Tipo;Qtde. Teórica;Part. (%)
ABCB4;ABC BRASIL;PN N2;94.194.244;0,443;
...
```
Parser específico para extrair a coluna `Código` (ticker). As demais colunas são ignoradas. Linhas de cabeçalho e rodapé (totalizadores) são descartadas.

## Risks / Trade-offs

| Risco | Mitigação |
|---|---|
| Endpoint do IDIV muda de formato ou URL | Tratamento de exceção no parser; fallback silencioso para comportamento atual (sem filtro) |
| API do IDIV fica fora do ar | Cache de 7 dias garante funcionamento mesmo sem acesso temporário |
| Usuário quer analisar ativos fora do IDIV | Basta limpar o campo e digitar manualmente; o IDIV só preenche quando vazio |
| Usuário quer segmento não-CASH (ex: BMF) | Se necessário no futuro, adicionar seletor de segmento; por enquanto CASH é o único usado |
| TTL de 7 dias pode servir dados desatualizados em período de rebalanceamento | TTL conservador (7d) vs rebalanceamento quadrimestral; risco baixo |
