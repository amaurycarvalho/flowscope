## Why

Ativos sem página de detalhes no Fundamentus (ex.: `CYCR11`, cujo HTML é um redirect para `cotacoes.php`) chegam à tabela da sub-aba "Fundamentos" com `Tipo=Desconhecido`, `Sub-tipo=N/A`, `P (Cotação)=N/A`, `VP (VP/Cota)=N/A`, `P/L=N/A` e `Data de referência=N/A`, mesmo quando a B3 e a CVM já possuem esses dados. Em paralelo, o `CvmQuarterlyRepository` não lê o layout real do Informe Trimestral da CVM (arquivos largos, sem `Descricao;Valor`), então o motor determinístico de FFO nunca é acionado como fallback.

## What Changes

- Preencher `P (Cotação)` e `Data de referência` a partir do último fechamento da B3 (`MarketPricePort`) quando o Fundamentus não fornecer, mantendo a semântica de `Data últ cot`.
- Preencher `VP (VP/Cota)` a partir do Informe Mensal da B3 (e da CVM como fallback), derivando `patrimônio líquido / cotas` quando o VP/Cota não vier reportado.
- Derivar `P/L` automaticamente quando `P` e a classificação FII estiverem disponíveis (comportamento já definido para FII).
- Classificar `Tipo`/`Sub-tipo` a partir da "Classificação autorregulação" do Informe Mensal da B3 (Classificação/Subclassificação/Gestão/Segmento de Atuação) quando o Fundamentus não fornecer, produzindo rótulos como `FII` / `Papel: Outros, Ativa`.
- Corrigir o `CvmQuarterlyRepository` para reconhecer e ler o layout largo real (`inf_trimestral_fii_resultado_contabil_financeiro_*.csv`), convertendo as colunas monetárias em componentes do FFO com código e proveniência preservados; o layout longo legado continua aceito.
- **BREAKING (comportamento do motor)**: restringir o motor determinístico de FFO a FIIs de tijolo/híbrido; para FII de papel, as métricas derivadas do motor permanecem `N/A`. Valores de FFO reportados pelo Fundamentus continuam sendo exibidos.
- **Coordenação de ordem**: esta change é aplicada **depois** de `fundamentos-informacoes-adicionais-fiscais` e DEVE construir sobre os acréscimos daquela change nos módulos compartilhados, sem duplicar parsing nem sobrescrever campos.

## Capabilities

### New Capabilities
<!-- Nenhuma capability nova: todas as mudanças estendem capacidades existentes. -->

### Modified Capabilities
- `fundamental-source-fallback`: novos campos de fallback (VP/Cota e classificação) e preenchimento de cotação/data de referência pelo preço B3 quando o Fundamentus não fornece.
- `b3-fii-extraction`: o Informe Mensal Estruturado passa a expor a classificação autorregulação (Classificação, Subclassificação, Gestão, Segmento de Atuação).
- `fii-classification`: a classificação Tipo/Sub-tipo passa a usar o Informe Mensal da B3 como fallback quando o Fundamentus não fornece os campos.
- `fii-fundamental-metrics`: a data de referência passa a aceitar a data do último fechamento da B3 como fallback.
- `cvm-quarterly-fund-data`: leitura do layout largo do resultado contábil-financeiro e mapeamento das colunas em componentes de FFO.
- `deterministic-ffo-engine`: o motor determinístico passa a ser restrito a FIIs de tijolo/híbrido; papel mantém `N/A` nas métricas derivadas do motor.

## Impact

- **Código**: `application/fundamental_analysis.py`, `application/fundamental_ports.py`, `application/fundamental_fallback.py`; `domain/fii/analysis.py`, `domain/fii/classification.py`, `domain/ffo/`; `infrastructure/fii/b3_fundamental_provider.py`, `infrastructure/fii/b3_fundamental_repository.py`; `infrastructure/b3/informe_mensal_parser.py`; `infrastructure/cvm/quarterly.py`, `infrastructure/cvm/schema.py`.
- **APIs**: nenhuma credencial nova; B3 FundosNet (`type=40`) já é acessado, CVM dados abertos `FII/DOC/INF_TRIMESTRAL` já é baixado.
- **Cache**: reutiliza as chaves existentes do informe B3 e do Informe Trimestral CVM; sem novas chaves obrigatórias.
- **Dados/fixtures**: fixture do Informe Mensal B3 de `CYCR11` (rótulos de classificação) e amostra real do `resultado_contabil_financeiro` da CVM.
- **Dependência**: requer `fundamentos-informacoes-adicionais-fiscais` aplicada antes. Os módulos compartilhados (`infrastructure/cvm/quarterly.py`, `infrastructure/b3/informe_mensal_parser.py`, `application/fundamental_ports.py`, `domain/fii/analysis.py`, provider B3) já terão os acréscimos daquela change; esta change apenas soma os campos de classificação/fallback e a leitura do layout largo.
- **Compatibilidade**: linhas sintéticas e dados ausentes permanecem `N/A`; nenhum contrato de porta é removido; FFO reportado pelo Fundamentus não muda; as colunas `Informações adicionais` e `Dados fiscais` permanecem inalteradas.
