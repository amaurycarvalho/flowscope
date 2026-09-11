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
- `CAMPO_DISCRIMINADOR = fii`, `CAMPO_SEGMENTO`, `CAMPO_GESTAO`, `CAMPO_QTD_IMOVEIS` e um novo `CAMPO_CLASSIFICACAO_FII` (Papel/Tijolo/Híbrido) a partir da classificação autorregulação do informe.

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

## Risks / Trade-offs

- **Acesso extra ao informe B3 por ticker**: o provider B3 é consultado mesmo quando o Fundamentus cobre o ticker. → Mitigação: o `B3FundamentalRepository` já memoriza identidade e o HTML do documento é cacheado; memoizar `obter_patrimonio` na mesma instância evita repetição entre o provider e `_resolver_cotistas`.
- **Dupla busca de patrimônio** entre `B3FundamentalDataProvider` e `_resolver_cotistas`. → Mitigação: cache por `(ticker, reference_date)` no repositório.
- **Mapeamento do layout largo pode classificar componentes indevidamente**. → Mitigação: regras conservadoras (UNKNOWN fora do FFO) e teste com amostra real; papel nem chega ao motor (D4).
- **Mudança de semântica da `Data de referência`** para tickers sem Fundamentus (passa de `N/A` para a data do fechamento B3). → Aceito; é o valor mais próximo de `Data últ cot`.
- **`vp_cota` derivado de `NAV/cotas`** difere do valor reportado por arredondamento. → Mitigação: preferir o `vp_cota` reportado e só derivar como fallback.

## Migration Plan

- Sem migração de dados: mudança de comportamento de exibição/cálculo.
- Rollback: reverter o commit; nenhum schema de cache é invalidado (chaves existentes reutilizadas).
