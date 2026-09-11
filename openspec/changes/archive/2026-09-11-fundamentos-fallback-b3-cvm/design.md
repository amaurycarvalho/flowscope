## Context

Ver `proposal.md - Why`. Hoje `FundamentalAnalysisUseCase._analisar_ticker` compõe `dados` via `CompositeFundamentalProvider` (Fundamentus → B3) e usa:

- `cotacao`, `vp_cota` e `data_referencia` somente de campos do Fundamentus;
- classificação de exibição via `classificar_exibicao(discriminador/segmento/gestao/qtd_imoveis)` do Fundamentus, com fallback na classificação determinística (`classificar_ticker`), que é FII-only por taxonomia;
- preço de fechamento por `MarketPricePort` (`B3MarketPriceFromResult`, criado por carga) em `_metricas_parciais`/`_analisar_ffo`;
- FFO de `_metricas_dos_dados` (Fundamentus) ou de `CompositeFfoProvider` (Fundamentus → `FFOEngineProvider`).

O `CompositeFundamentalProvider` é criado uma única vez em `app.py`; o `MarketPricePort` é criado por execução em `controller_fundamental.py`. O `B3FundamentalRepository.obter_patrimonio` já devolve `PatrimonioFii` com `vp_cota` e `reference_date`, mas a análise descarta esses valores.

O `CvmQuarterlyRepository` lê apenas o layout longo (`Descricao`/`Valor`); o ZIP real (`inf_trimestral_fii_2026.zip`) só tem layout largo, então `validar_aliases` levanta `CvmSchemaError` e o `FFOEngineProvider` devolve `None` sempre.

Esta change é aplicada **depois** de `fundamentos-informacoes-adicionais-fiscais`, que já terá: acrescentado campos fiscais ao `B3InformeMensal`/provider B3, criado `CvmQuarterlyRepository.get_indexadores` (leitura do `complemento`), adicionado campos compostos em `fundamental_ports.py`, ampliado `AnaliseFundamental` e adicionado as colunas `Informações adicionais`/`Dados fiscais`. Os pontos de contato são os mesmos arquivos, mas os acréscimos são aditivos; esta change não pode sobrescrevê-los nem duplicar o parsing do ZIP da CVM.

## Goals / Non-Goals

**Goals:**
- Preencher `P (Cotação)`, `VP (VP/Cota)`, `P/L`, `Tipo`, `Sub-tipo` e `Data de referência` para tickers sem Fundamentus, usando B3/CVM.
- Manter a proveniência por campo para os campos resolvidos por provider.
- Tornar o motor determinístico de FFO operacional contra o layout real da CVM, restrito a FII de tijolo/híbrido.

**Non-Goals:**
- Não alterar o comportamento do Fundamentus como fonte primária.
- Não sintetizar FFO para FII de papel (permanece `N/A`).
- Não criar novas colunas nem mudar ordem/formatação da tabela.
- Não implementar reconciliação DFIN nem versionamento novo de schema além do reconhecimento do layout largo.

## Decisions

### D1. Cotação e data de referência preenchidas no caso de uso

`cotacao` e `data_referencia` passam a ser preenchidos em `_analisar_ticker` a partir de `self._mercado.preco_fechamento(ticker, reference_date)` quando `_decimal_campo(dados, CAMPO_COTACAO)` / `_data_campo(dados, CAMPO_DATA_REFERENCIA)` forem `None`. Reaproveita-se o mesmo `PrecoObservacao` já buscado pelas métricas (evita busca duplicada).

**Por que não no composite**: o `CompositeFundamentalProvider` é construído uma vez em `app.py`, enquanto o `MarketPricePort` depende dos dados diários da carga corrente. Injetar preço no composite exigiria reconstruí-lo a cada carga.

### D2. VP/Cota e classificação resolvidos por provider B3 (proveniência preservada)

Estender `B3FundamentalDataProvider` para emitir, além de `CAMPO_NOME`:
- `CAMPO_VP_COTA` (do `PatrimonioFii.vp_cota`; se ausente, derivar `net_asset_value / shares_outstanding`);
- `CAMPO_DISCRIMINADOR = fii`, `CAMPO_SEGMENTO`, `CAMPO_GESTAO` e um novo `CAMPO_CLASSIFICACAO_FII` (Papel/Tijolo/Híbrido) a partir da classificação autorregulação do informe.

O prefixo `Tijolo:`/`Papel:` do sub-tipo é derivado de `CAMPO_CLASSIFICACAO_FII`; o `CAMPO_QTD_IMOVEIS` não é emitido pela B3 (o informe não traz quantidade de imóveis) e continua vindo apenas do Fundamentus.

Assim o `CompositeFundamentalProvider` registra `CampoFundamental.fonte` normalmente. Alternativa (preencher tudo no caso de uso) foi descartada por perder a proveniência por campo e duplicar a lógica de composição.

### D3. Classificação autorregulação vem do Informe Mensal da B3

`extrair_informe_mensal` passa a extrair o rótulo `Classificação autorregulação` (Classificação, Subclassificação, Gestão, Segmento de Atuação) e `B3InformeMensal` ganha esses campos. O informe já é baixado para patrimônio, então não há novo acesso. O CVM `geral` (`Segmento_Atuacao`, `Tipo_Gestao`) não distingue Papel/Tijolo/Híbrido, por isso não é a fonte primária da classificação.

### D4. Elegibilidade do motor FFO pela classe efetiva do FII

O motor determinístico só é acionado quando a classe efetiva do FII é Tijolo ou Híbrido. A classe efetiva é derivada dos campos compostos: `CAMPO_CLASSIFICACAO_FII` (B3) ou, na sua ausência, `CAMPO_QTD_IMOVEIS` do Fundamentus. Papel → motor não é chamado e `FFO Yield`/`P/FFO`/`FFO Trend` ficam `N/A`. O FFO reportado pelo Fundamentus (`_metricas_dos_dados`) não é afetado.

### D5. CvmQuarterlyRepository reconhece o layout largo

`_ler_registros` passa a detectar o layout largo (presença de `CNPJ_Fundo_Classe` + `Data_Referencia` + colunas de resultado, ausência de `Descricao`/`Valor`) e, por linha, converter cada coluna monetária aplicável em um `_Registro`:
- `codigo` = nome original da coluna;
- `descricao` = nome da coluna com `_` → espaço e sufixo `_Contabil`/`_Financeiro` preservado, para casar com as regras de `classificar_componente` (ex.: `Receita_Aluguel_Investimento_Contabil` → contém "aluguel" → `RECURRING`);
- `valor` = `parse_decimal` da célula; valores vazios/zero são ignorados.

Colunas que não casam com nenhuma regra permanecem `UNKNOWN` e fora do FFO, de forma conservadora. O caminho de layout longo é mantido para compatibilidade.

### D6. Reuso dos módulos compartilhados já ampliados

Como `fundamentos-informacoes-adicionais-fiscais` é aplicada antes, esta change DEVE:
- reaproveitar o padrão de leitura/extração de CSV do `CvmQuarterlyRepository` (incluindo o método de indexadores do `complemento`) e não duplicar o carregamento do ZIP nem a seleção de competência;
- reaproveitar a extração por rótulo do `extrair_informe_mensal` (já usada para CNPJ/administrador) para somar a classificação autorregulação, mantendo `_coletar_pares`/`_valor`;
- adicionar seus campos (`CAMPO_CLASSIFICACAO_FII`, `CAMPO_VP_COTA` no provider, `vp_cota`/`data_referencia` no caso de uso) sem remover nem renomear os campos fiscais e adicionais introduzidos pela change anterior;
- manter as colunas `Informações adicionais`/`Dados fiscais` e o restante da tabela inalterados.

### D7. Preço Típico a partir da janela B3 já carregada

Quando o Fundamentus não fornecer `Min 52 sem`/`Max 52 sem`, `_analisar_ticker` preenche os extremos com o menor `min_price` e o maior `max_price` da janela diária da B3 já carregada para a análise (`daily_data`), restrita a `reference_date − 52 semanas`. A janela é a mesma do `MarketPricePort` (D1), sem novo acesso. Para expor os extremos, a porta de mercado ganha `extremos_preco(ticker, reference_date, janela)` (implementada por `B3MarketPriceFromResult`/`B3MarketPricePort` sobre os dados em memória); `preco_tipico`/`P / PT` são então calculados como hoje. Sem dias válidos na janela, ambos permanecem `N/A`.

**Por que não no composite**: mesma razão de D1 — a janela depende da carga corrente; o composite é construído uma vez em `app.py`.

**Semântica**: como a janela carregada (30/60/90 dias por configuração, em datas amostradas) costuma ser menor que 52 semanas, o `Preço Típico` de fallback representa os extremos do período disponível, não necessariamente de 52 semanas; o rótulo da coluna não muda.

## Cobertura de fallback e cache

Esta seção registra, para cada coluna da sub-aba "Fundamentos", se existe fallback B3/CVM quando o Fundamentus não fornece o dado, e o estado de cache de cada origem.

### Matriz de cobertura por coluna

| Coluna | Fonte primária | Fallback B3/CVM | Coberto |
| --- | --- | --- | --- |
| Ticker | watchlist | — | n/a |
| Nome | Fundamentus | B3 identidade (`obter_nome`) | sim |
| Tipo / Sub-tipo | Fundamentus | B3 informe (classificação autorregulação) + taxonomia | sim (D3) |
| P (Cotação) | Fundamentus | preço B3 (`MarketPricePort`) | sim (D1) |
| Preço Típico | Fundamentus (`Max 52 sem`/`Min 52 sem`) | extremos da janela B3 em cache (≤ 52 semanas) | sim (D7; janela pode ser < 52 semanas) |
| P / PT | derivado do Preço Típico | derivado (herda o fallback do PT) | sim (D7) |
| VP (VP/Cota) | Fundamentus | B3 informe / CVM patrimônio | sim (D2) |
| P/VP | Fundamentus | derivado (preço B3 × cotas ÷ PL B3/CVM) | sim |
| P/L | Fundamentus (Papel) | FII: derivado (`cotação ÷ (dividendo × 12)`) | FII sim / Papel não |
| Dividend Yield | Fundamentus | derivado (dividendos 12m ÷ preço B3) | FII sim / Papel não |
| Última data-com / Último dividendo / Dividendo anterior | B3 proventos + Fundamentus | — | FII sim / Papel não |
| Tendência do dividendo | derivado | — | derivado |
| FFO Yield / P/FFO / FFO Trend | Fundamentus | motor CVM (layout largo) | sim (D5) |
| Dividend Payout | derivado (DY ÷ FFOY) | — | derivado |
| Nº de cotistas / Classe de cotistas | B3 informe / CVM mensal | CVM acionistas (Papel) | sim |
| Patrimônio / Classe de patrimônio | Fundamentus | B3 informe / CVM mensal | sim |
| Data de referência | Fundamentus | data do fechamento B3 | sim (D1) |
| Informações adicionais — Papel: `LPA`/`ROE`/`ROIC` | Fundamentus | **nenhum** | **não** |
| Informações adicionais — FII: `Qtd Imóveis`/`Cap Rate`/`Vacância Média` | Fundamentus | **nenhum** | **não** |
| Informações adicionais — FII: indexadores | CVM trimestral (`complemento`) | — | sim |
| Dados fiscais (CNPJ / Administrador / Gestor) | B3 informe + CVM anual/FCA | — | sim |

Campos sem fallback possível, que DEVEM permanecer `N/A` quando o Fundamentus não os fornece:

- `LPA`, `ROE`, `ROIC` (Papel): só o Fundamentus os expõe; não há indicador equivalente nos datasets B3/CVM consumidos.
- `Qtd Imóveis`, `Cap Rate`, `Vacância Média` (FII): só o Fundamentus os expõe. O Informe Mensal da B3 traz a classificação autorregulação, mas não quantidade de imóveis nem cap rate/vacância (verificado nos fixtures `CYCR11`/`ALZR11`).
- Papel: `P/L`, `Dividend Yield` e as colunas de dividendo dependem do Fundamentus, pois a série de proventos da B3 (`type=41`) é restrita a FIIs.

**Inconsistência resolvida**: o `CAMPO_QTD_IMOVEIS` **não** é emitido a partir do informe B3, pois nem o delta de `b3-fii-extraction` nem o parser expõem a quantidade de imóveis. O prefixo `Tijolo:`/`Papel:` passou a ser derivado de `CAMPO_CLASSIFICACAO_FII` (`classificar_exibicao`), e `Qtd Imóveis` permanece sem fallback (`N/A`), conforme a matriz acima.

### Cache por origem

| Origem | Mecanismo | Estado |
| --- | --- | --- |
| Fundamentus snapshot | cache condicional (`Data últ cot` + HTTP), versionado | ok |
| Fundamentus proventos | TTL 1 dia | ok |
| B3 identidade / HTML de documento / lista de documentos | 30 / 30 / 1 dias, versionado | ok |
| B3 negociações diárias | cache por data (`CacheManager`) | ok |
| Preço B3 (`MarketPricePort`) | derivado da memória, sem novo acesso | ok |
| Janela de preços B3 (extremos para o PT) | derivada de `daily_data` em memória, sem novo acesso | ok |
| CVM INF_MENSAL / INF_ANUAL / INF_TRIMESTRAL / FRE+FCA | cache condicional (arquivo + hash + metadados) | ok |
| CVM acionistas (normalizado) | cache por hash + `parser_version` | ok |
| CVM trimestral normalizado (componentes/indexadores) | re-parseia o ZIP a cada chamada | gap |
| CVM anual normalizado (gestor/administrador) | re-parseia o ZIP a cada chamada | gap |
| B3 `obter_patrimonio` | não memoizado (só `obter_informe`) | previsto na task 2.2 |

Todas as origens consumidas têm cache de arquivo bruto. Os dois gaps são de memoização do parse normalizado na CVM; o `CvmAcionistasSource` já adota esse cache, servindo de referência. Para esta change, o cache de arquivo bruto é suficiente: o re-parse do ZIP não altera valores nem proveniência e o custo é aceitável para a janela de anos consultada; a memoização do normalizado fica como otimização futura (fora do escopo).

## Risks / Trade-offs

- **Acesso extra ao informe B3 por ticker**: o provider B3 é consultado mesmo quando o Fundamentus cobre o ticker. → Mitigação: o `B3FundamentalRepository` já memoriza identidade e o HTML do documento é cacheado; memoizar `obter_patrimonio` na mesma instância evita repetição entre o provider e `_resolver_cotistas`.
- **Dupla busca de patrimônio** entre `B3FundamentalDataProvider` e `_resolver_cotistas`. → Mitigação: cache por `(ticker, reference_date)` no repositório.
- **Mapeamento do layout largo pode classificar componentes indevidamente**. → Mitigação: regras conservadoras (UNKNOWN fora do FFO) e teste com amostra real; papel nem chega ao motor (D4).
- **Mudança de semântica da `Data de referência`** para tickers sem Fundamentus (passa de `N/A` para a data do fechamento B3). → Aceito; é o valor mais próximo de `Data últ cot`.
- **`vp_cota` derivado de `NAV/cotas`** difere do valor reportado por arredondamento. → Mitigação: preferir o `vp_cota` reportado e só derivar como fallback.

## Migration Plan

- Sem migração de dados: mudança de comportamento de exibição/cálculo.
- Rollback: reverter o commit; nenhum schema de cache é invalidado (chaves existentes reutilizadas).
