## Context

Ver `proposal.md - Why`. O pipeline atual da sub-aba "Fundamentos":

- `FundamentalAnalysisUseCase._analisar_ticker` compõe `dados` via `CompositeFundamentalProvider` (Fundamentus → B3) e monta `AnaliseFundamental`.
- `fundamental_table.py` define `_COLUNAS`, monta as linhas (`_linha_analise`) e o CSV (`montar_csv`); as colunas são persistidas por id estável.
- O parser do Fundamentus já extrai `LPA`, `ROE`, `ROIC` (em `indicadores`), `Min/Max 52 sem` e `cap_rate`/`vacancia_media`/`qtd_imoveis` (em `imoveis`), mas o adapter só expõe um subconjunto.
- O HTML do Informe Mensal da B3 contém `CNPJ do Fundo/Classe`, `Nome do Administrador` e `CNPJ do Administrador`, mas `extrair_informe_mensal` não os extrai.
- O `INF_ANUAL` da CVM (`inf_anual_fii_geral_*` e `inf_anual_fii_complemento_*`) contém `Nome_Administrador`/`CNPJ_Administrador` e `Nome_Gestor`/`CNPJ_Gestor`, mas não é ingerido.
- O `INF_TRIMESTRAL/complemento` da CVM contém `Percentual_Indexador_Valor_Total_{IGPM,INPC,IPCA,INCC}`; o `CvmQuarterlyRepository` já baixa esse ZIP.
- Para Papel, o `CvmAcionistasSource` já resolve ticker→CNPJ via FCA (`fca_cia_aberta_valor_mobiliario`).

## Goals / Non-Goals

**Goals:**
- Preencher as colunas `Informações adicionais` e `Dados fiscais` com dados já disponíveis nas fontes, omitindo itens ausentes.
- Ingerir o `INF_ANUAL` da CVM para o gestor.
- Expor indicadores adicionais, Preço Típico e percentuais por indexador na análise.

**Non-Goals:**
- Não implementar CDI/SELIC (indisponível nas fontes).
- Não derivar mínima/máxima de 52 semanas dos dados diários da B3 (Preço Típico fica indisponível quando o Fundamentus não cobre o ticker).
- Não alterar colunas, ordem ou cálculo das métricas existentes.

## Decisions

### D1. Indicadores adicionais via novos campos compostos

Adicionar `CAMPO_LPA`, `CAMPO_ROE`, `CAMPO_ROIC`, `CAMPO_CAP_RATE` e `CAMPO_VACANCIA_MEDIA` a `fundamental_ports.py` e mapeá-los no adapter do Fundamentus (`campos_do_ativo`) a partir de `ativo.indicadores` e `ativo.imoveis`. Apenas o Fundamentus fornece esses campos; B3/CVM não os têm, então o composite os deixa ausentes quando a página não existe.

### D2. Identidade fiscal via provider B3 + novo provider CVM anual

Adicionar `CAMPO_CNPJ`, `CAMPO_ADMINISTRADOR`, `CAMPO_CNPJ_ADMINISTRADOR`, `CAMPO_GESTOR` e `CAMPO_CNPJ_GESTOR`. O `B3FundamentalDataProvider` passa a emitir CNPJ e administrador a partir do Informe Mensal; um novo provider CVM emite o gestor (e administrador como fallback) a partir do `INF_ANUAL`; para Papel, um provider resolve o CNPJ via FCA. A ordem do `CompositeFundamentalProvider` preserva a proveniência por campo.

### D3. Ingestão do INF_ANUAL com o downloader genérico

Criar `CvmAnnualRepository` sobre o `CvmDatasetDownloader` já existente (`base_url` do `FII/DOC/INF_ANUAL`, `dataset="FII-INF-ANUAL"`, `arquivo=lambda ano: f"inf_anual_fii_{ano}.zip"`), reaproveitando cache por ano, hash, metadados e revalidação. O repositório filtra por CNPJ e competência e normaliza gestor/administrador/prestadores. O CNPJ do ticker vem de `resolver_identidade` (FII) ou do FCA (Papel).

### D4. Percentuais por indexador em método dedicado do repositório trimestral

Adicionar `CvmQuarterlyRepository.get_indexadores(cnpj, reference_date)`, que lê apenas o `complemento` do ZIP já baixado e seleciona a competência mais recente. Mantém-se separado de `get_components` para não acoplar o cálculo de FFO ao complemento e evitar conflito com a leitura do layout largo do `resultado` (feita por `fundamentos-fallback-b3-cvm`).

### D5. Preço Típico como função pura de domínio

Implementar `preco_tipico(maxima, minima, cotacao)` e `percentual_preco_tipico(cotacao, preco_tipico)` em `domain/fii/metrics.py`, usando `Decimal`, retornando `None` quando faltar insumo ou o Preço Típico for zero. O caso de uso preenche `preco_tipico`/`pct_preco_tipico` em `AnaliseFundamental`.

### D6. Montagem das colunas na apresentação

Adicionar os ids `preco_tipico` e `p_pt` a `_COLUNAS` logo após `p` (P Cotação), alinhados à direita, e `informacoes_adicionais`/`dados_fiscais` ao final. O `Preço Típico` é formatado com separador de milhar e duas casas e o `P / PT` como percentual (`(Cotação − Preço Típico) / Preço Típico`), ambos `N/A` quando faltar insumo. Em `Informações adicionais`, os itens são concatenados com ` | ` e cada um é precedido de um label curto, sem o Preço Típico. Em `Dados fiscais`, os CNPJs são formatados como `99.999.999/9999-99` e administrador e gestor são exibidos como `<label> <nome> (<CNPJ>)`, omitindo as partes ausentes. A lógica de omissão (tipo do ativo, `qtd_imoveis` zero/desconhecido, itens ausentes) fica nesses helpers, e o CSV reutiliza as mesmas linhas.

### D7. Regras de omissão

- `Qtd imóveis` zero ou desconhecido → omitir `Qtd Imóveis`, `Cap Rate` e `Vacância Média`.
- Indexador com percentual ausente ou zero → omitir.
- Item de identidade fiscal ausente → omitir.
- Coluna sem nenhum item → `N/A`.

## Risks / Trade-offs

- **Download extra do `INF_ANUAL`** por ano e por consulta de gestor. → Mitigação: cache anual pelo `CvmDatasetDownloader` (ZIP + hash + revalidação), servido localmente.
- **Cobertura parcial da identidade fiscal** (fundo sem informe B3 e/ou sem INF_ANUAL). → Mitigação: omitir o item; a coluna degrada para os itens disponíveis.
- **Percentuais por indexador com defasagem trimestral**. → Aceito; é a única fonte disponível e o dado é estrutural.
- **Duplicação de parsing do informe B3** (CNPJ/administrador no informe e no provento). → Mitigação: reutilizar `_coletar_pares`/`_valor` e o padrão de `extrair_por_rotulo`.
- **Colunas largas** podem exigir rolagem horizontal. → Mitigação: largura persistida por id estável já existente.

## Migration Plan

- Sem migração de dados. Novas colunas ao final da tabela e novas chaves de cache anuais do `INF_ANUAL`.
- Rollback: reverter o commit; as colunas desaparecem e nenhuma métrica existente muda.
