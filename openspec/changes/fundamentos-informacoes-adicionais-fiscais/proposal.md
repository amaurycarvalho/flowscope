## Why

A sub-aba "Fundamentos" concentra apenas métricas de valuation/dividendos e não reúne, por ativo, os dados qualitativos e fiscais que já existem nas fontes: indicadores adicionais (LPA/ROE/ROIC, Cap Rate, Vacância Média), o preço típico de 52 semanas, o percentual de patrimônio por indexador e a identidade fiscal (CNPJ, administrador e gestor). Hoje esses dados ficam dispersos ou nem são ingeridos, obrigando a consulta manual em outros sistemas.

## What Changes

- Adicionar as colunas **Preço Típico** e **P / PT** logo após **P (Cotação)**, alinhadas à direita.
- Adicionar duas colunas ao final da tabela de Fundamentos: **Informações adicionais** e **Dados fiscais**, com concatenação de itens separados por ` | ` e precedidos de labels curtos.
- **Informações adicionais — Papel**: `LPA`, `ROE` e `ROIC`.
- **Informações adicionais — FII**: `Qtd Imóveis`, `Cap Rate`, `Vacância Média` e o percentual por indexador (`IPCA`, `IGP-M`, `INPC`, `INCC`). Quando `Qtd imóveis` for zero ou desconhecido, omitir `Qtd Imóveis`, `Cap Rate` e `Vacância Média`.
- `Preço Típico = (Max 52 sem + Min 52 sem + Cotação) / 3` e `P / PT = (Cotação − Preço Típico) / Preço Típico`, por funções puras de domínio; exibidos em colunas próprias e `N/A` quando faltar qualquer insumo.
- **Dados fiscais — FII**: `CNPJ`, `Administrador <nome> (<CNPJ>)` e `Gestor <nome> (<CNPJ>)`. **Dados fiscais — Papel**: apenas `CNPJ`.
- Ingerir o Informe Anual da CVM (`INF_ANUAL`) como fonte do gestor (nome e CNPJ) e complementar administrador/custodiante/auditor, por CNPJ, com cache e hash.
- Extrair do Informe Mensal Estruturado da B3 o CNPJ do fundo e o administrador (nome e CNPJ), reutilizando o HTML já baixado para patrimônio.
- Ler os percentuais por indexador do `complemento` do Informe Trimestral da CVM (já baixado para o motor de FFO).
- CDI/SELIC fica **fora de escopo**: não existe em nenhum dos datasets consumidos (B3 ou CVM); apenas os quatro indexadores de inflação estão disponíveis.
- Itens sem dado em nenhuma fonte são omitidos; se a coluna inteira ficar sem itens, exibir `N/A`.

## Capabilities

### New Capabilities
- `cvm-annual-fund-data`: aquisição e normalização do Informe Anual da CVM (INF_ANUAL) por CNPJ, expondo gestor, administrador, custodiante e auditor independente com proveniência.

### Modified Capabilities
- `fundamentus-fundamental-provider`: expor os indicadores `LPA`, `ROE`, `ROIC` e os campos de imóveis `Cap Rate` e `Vacância Média` na composição de campos fundamentalistas.
- `b3-fii-extraction`: o Informe Mensal Estruturado passa a expor o CNPJ do fundo e o administrador (nome e CNPJ).
- `fundamental-source-fallback`: resolver a identidade fiscal (`cnpj`, `administrador`, `gestor`) por prioridade de fontes com proveniência, omitindo itens ausentes; Papel resolve apenas o CNPJ.
- `cvm-quarterly-fund-data`: expor os percentuais por indexador (`IGPM`, `INPC`, `IPCA`, `INCC`) do arquivo `complemento`.
- `fii-fundamental-metrics`: adicionar `Preço Típico` e `P / PT` como funções puras e expor os percentuais por indexador na análise.
- `gui-interface`: novas colunas `Preço Típico` e `P / PT` após `P (Cotação)`, além de `Informações adicionais` e `Dados fiscais` no fim da tabela, com regras de conteúdo, labels e exportação CSV consistentes.

## Impact

- **Código**: `presentation/gui/charts/fundamental_table.py`; `application/fundamental_analysis.py`, `application/fundamental_ports.py`, `application/fundamental_fallback.py`; `domain/fii/analysis.py`, `domain/fii/metrics.py`; `infrastructure/fii/fundamentus/adapter.py`; `infrastructure/fii/b3_fundamental_provider.py` e `b3_fundamental_repository.py`; `infrastructure/b3/informe_mensal_parser.py`; `infrastructure/cvm/quarterly.py` e novo fluxo anual (`infrastructure/cvm/annual.py` ou equivalente) reutilizando `CvmDatasetDownloader`.
- **APIs**: novo diretório de dados abertos da CVM `FII/DOC/INF_ANUAL/DADOS`; sem credenciais. O `INF_TRIMESTRAL` já é baixado.
- **Cache**: nova chave anual para o `INF_ANUAL` (ZIP bruto + hash + metadados) pelo downloader genérico da CVM.
- **Dados/fixtures**: fixture do informe anual (gestor/administrador) e amostra do `complemento` trimestral com os percentuais por indexador.
- **Coordenacao**: esta change deve ser aplicada **antes** de `fundamentos-fallback-b3-cvm`, que toca os mesmos módulos (`cvm/quarterly.py`, `b3/informe_mensal_parser.py`, `application/fundamental_ports.py`, `domain/fii/analysis.py`, provider B3). Aquela change será ajustada para construir sobre estes acréscimos.
- **Compatibilidade**: quatro colunas novas (duas após `P (Cotação)` e duas no fim da tabela); CSV ganha as mesmas quatro colunas; nenhum contrato de porta é removido.
