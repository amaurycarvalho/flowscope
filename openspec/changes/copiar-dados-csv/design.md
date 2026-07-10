## Context

O botão "Copiar Dados" (`_copy_data_btn`) atualmente copia `Ticker;VWAP;MoneyFlowVolume` — dados agregados dos indicadores. O usuário precisa exportar os dados brutos do CSV original da B3 para verificar manualmente os cálculos em planilha externa.

A arquitetura existente:
- `_current_data: dict` armazena o resultado do `AnalyzeTickersUseCase.execute()`
- Cada ticker tem `daily_data: list[dict]` com registros diários do `TradeDay`
- O `daily_data` atual contém `date, avg_price, min_price, max_price, last_price, fin_vol, fin_instr_qty` mas **não** propaga `segment` (SgmtNm) nem `trades_qty` (TradQty) do `TradeDay`
- O botão é desabilitado/habilitado via `OperationGuard` + `_disable_all_buttons`/`_restore_all_buttons`
- O clipboard é acessado via `pyxclip` (primário) com fallback `tk.clipboard_append`

## Goals / Non-Goals

**Goals:**
- Substituir o conteúdo copiado pelo botão "Copiar Dados" para o CSV bruto com os campos especificados
- Comportamento sensível à aba ativa (Análise do Ticker → 1 ticker, Análise Geral → N tickers)
- Propagar `segment` e `trades_qty` do `TradeDay` até o `daily_data` no use case
- Respeitar o período selecionado (já refletido em `_current_data`)
- Manter o OperationGuard e o atalho `Ctrl+Shift+C`
- Formato brasileiro: separador de campo `;`, separador decimal `,`

**Non-Goals:**
- Não criar novo botão — é substituição da lógica existente
- Não alterar o comportamento do botão "Copiar Gráfico" (imagem PNG)
- Não alterar o `ExportVWAPUseCase` (CLI)
- Não adicionar novas dependências
- Não modificar o protocolo `GUIView` nem o `FlowScopePresenter`

## Decisions

### Decisão 1: Reaproveitar o botão existente em vez de criar novo
**Alternativa considerada**: Criar botão separado "Copiar dados CSV" ao lado do existente.
**Decisão**: Substituir a lógica do botão atual. O botão "Copiar Dados" existente já tem tooltip "Copiar dados CSV para a área de transferência" — está alinhado com o novo comportamento. Manter um único botão evita poluição visual na toolbar.

### Decisão 2: Modificar o use case para propagar campos faltantes
**Alternativa considerada**: Reconstruir os campos a partir do cache de CSV brutos.
**Decisão**: Adicionar `segment` e `trades_qty` ao `daily_data` em `AnalyzeTickersUseCase.execute()`. É a abordagem mais simples (2 linhas), sem impacto em outras partes do sistema (o campo novo é ignorado por consumidores existentes).

### Decisão 3: Formatar Decimais com vírgula via string replacement
**Alternativa considerada**: Usar `locale.setlocale(locale.LC_NUMERIC, 'pt_BR.UTF-8')`.
**Decisão**: `str(value).replace('.', ',')` — mais previsível, não depende de locale instalado no sistema, mesmo resultado em qualquer ambiente.

### Decisão 4: Extrair geração do CSV para método auxiliar
`_build_raw_csv()` retorna a string CSV. `_copy_data` e `_fallback_clipboard_text` chamam esse método, eliminando duplicação de lógica.

### Decisão 5: CSV itera sobre sampling_dates, não daily_data
O CSV deve conter todas as datas de amostragem, mesmo que o ticker não tenha negociado em alguma delas. Para isso, `_sampling_dates` é propagado do use case → GUI via chave `_sampling_dates` no dict resultado. Em `set_current_data()`, chaves `_` são extraídas para `self._sampling_dates` e removidas de `self._current_data`. Em `_build_raw_csv()`, itera sobre `_sampling_dates` e preenche com `;;;;;;;` linhas vazias para datas sem trade do ticker.

```python
sampling_dates = self._sampling_dates or sorted({day["date"] ...})
for ticker in tickers:
    by_date = {day["date"]: day for day in daily}
    for sd in sampling_dates:
        day = by_date.get(sd)
        if day: ...  # dados reais
        else: f"{sd};{ticker};;;;;;;"  # linha vazia
```

**Alternativa considerada:** iterar apenas sobre `daily_data` (datas com trades). Rejeitado porque o usuário precisa visualizar explicitamente as datas sem trade para auditoria.

### Decisão 6: Propagação de sampling_dates pelo pipeline
O use case retorna `_sampling_dates` no mesmo dict do resultado. O presenter (`on_result`) passa o dict completo para `set_current_data()`. A GUI extrai `_sampling_dates` e armazena separadamente, mantendo `_current_data` limpo (apenas dados de ticker).

## Risks / Trade-offs

- **[Baixo] Campo `segment` sempre "CASH"** — O parser B3 já filtra `SgmtNm=CASH`, então o campo será sempre "CASH". É informação redundante, mas mantida por completude do CSV bruto e consistência com a fonte original.
- **[Baixo] Performance em muitos tickers** — Para 100+ tickers com 30+ dias cada, o CSV pode ter milhares de linhas. O pyxclip lida bem com isso, e o Tkinter clipboard tem limite de ~1MB em alguns sistemas. Cenário improvável para o uso atual.
- **[Baixo] Ordenação dos registros** — Segue a ordem do `daily_data`, que reflete a ordem de chegada do parser B3 (tipicamente cronológica). Não é garantida mas é consistente com o comportamento atual.
