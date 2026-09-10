## Context

A tabela da sub-aba "Fundamentos" é montada por `FundamentalAnalysisUseCase` a partir de `AnaliseFundamental` (`domain/fii/analysis.py`) e renderizada por `montar_linhas` (`presentation/gui/charts/fundamental_table.py`). A classificação atual vem de `classificar_ticker` (`domain/fii/classification.py`) e as métricas FFO só são calculadas para FIIs elegíveis (`SubTipoFii.TIJOLO`/`HIBRIDO`). O provider do Fundamentus (`infrastructure/fii/fundamentus/`) já expõe `raw`, `indicadores`, `balanco`, `demonstrativos_*` e `imoveis`, mas o modelo `AtivoFundamental` não guarda o discriminador `Papel`/`FII` nem `Tipo`, `Setor`, `Subsetor`, `Segmento` e `Gestão`. Ver `proposal.md - Why` para a motivação.

## Goals / Non-Goals

**Goals:**
- Tornar Tipo/Sub-tipo derivados dos campos do Fundamentus, com fallback determinístico.
- Expor cotistas, patrimônio, suas classificações e a data de referência na linha da tabela.
- Preencher as métricas existentes sempre que a fonte fornecer o dado.

**Non-Goals:**
- Alterar a persistência de layout ou o tratamento de cache (change `fundamentos-table-ux`).
- Alterar a regra de tendência de dividendo (change `fundamental-dividend-consolidation`).
- Introduzir novo provedor de dados; reutiliza Fundamentus/B3/CVM existentes.

## Decisions

### 1. Campos de classificação no modelo do Fundamentus

Estender `AtivoFundamental` com `discriminador` (`papel`/`fii`), `especie`, `setor`, `subsetor`, `segmento` e `gestao`, extraídos dos rótulos reais (`Papel`/`FII`, `Tipo`, `Setor`, `Subsetor`, `Segmento`, `Gestão`). O parser reutiliza `coletar_raw`, que já mapeia rótulo→valor. `Qtd imóveis` já é extraído em `imoveis` e passa a ser o balizador Tijolo/Papel.

**Alternativa considerada:** parsear a série JS da "Composição dos Ativos" — rejeitada por ser frágil e desnecessária, já que `Qtd imóveis` separa corretamente os casos reais (tijolo > 0; papel = 0).

### 2. Classificação de exibição no domínio, com fallback

Uma função pura compõe o rótulo de exibição: `Papel` → `Tipo; Setor; Subsetor`; `FII` → `Tijolo: `/`Papel: ` + `Segmento; Gestão`. Quando os campos do Fundamentus estão ausentes, cai em `classificar_ticker` (taxonomia/sintaxe). O resultado é materializado em `AnaliseFundamental` para a apresentação não conhecer Fundamentus.

**Alternativa considerada:** manter `ClassificacaoAtivo` e trocar apenas o rótulo na GUI — rejeitada porque a apresentação passaria a depender de campos brutos do provider.

### 3. Novos dados da linha e métricas

`AnaliseFundamental` passa a carregar o número de cotistas, o patrimônio líquido, suas classes (`classificar_cotistas`/`classificar_patrimonio`, já existentes) e a data de referência (`data_ultima_cotacao`). O `PatrimonioFii` continua sendo a fonte de cotistas/patrimônio; o Fundamentus (`Patrim Líquido`, `Nro. Cotas`) entra como fonte primária quando disponível, com CVM como fallback via `CompositeFundamentalProvider`.

**Alternativa considerada:** recalcular tudo no domínio a partir de `MetricasFii` — rejeitada por espalhar responsabilidade; a composição de fontes fica na camada de aplicação.

### 4. Remoção do gate de elegibilidade FFO

`_metricas_dos_dados` passa a ser tentado sempre; `_analisar_ffo` e `_metricas_parciais` não dependem mais de `elegivel_ffo()`. O `N/A` passa a refletir ausência de dado, não tipo do ativo. `elegivel_ffo` deixa de ser usado para preencher a tabela.

**Alternativa considerada:** manter o gate e apenas documentar — rejeitada pelo requisito de preencher FFO quando o dado existir.

### 5. Colunas na apresentação

`_COLUNAS` ganha as cinco novas colunas; `montar_linhas`/`montar_csv` incluem os novos valores formatados (cotistas com separador de milhar, patrimônio em `R$` legível, classes textuais, data em `DD/MM/AAAA`).

## Risks / Trade-offs

- **[Risco] Fixtures sintéticas não cobrem os novos rótulos** → Atualizar `tests/fixtures/fundamentus/` com `Tipo`/`Setor`/`Subsetor`/`Segmento`/`Gestão`/`Qtd imóveis` e ajustar os testes de contrato.
- **[Risco] `Qtd imóveis` ausente classifica FII de tijolo como papel** → Usar `classificar_ticker` como fallback quando o campo vier ausente; registrar aviso.
- **[Trade-off] Dependência de ordem de arquivamento** → As specs-base (`fii-classification`, `fii-fundamental-metrics`, `fundamentus-fundamental-provider`, `gui-interface`) são materializadas por changes anteriores; arquivar aquelas antes desta.
