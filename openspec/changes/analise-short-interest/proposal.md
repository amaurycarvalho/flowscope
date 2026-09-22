## Why

A RFC-014 consolida a análise de *short interest* com dados oficiais (B3 e FINRA), mas o FlowScope ainda não traduz o estoque de empréstimos de ativos em métricas acionáveis. Dados brutos de ações alugadas, sem normalização por *free float* e por volume, não permitem comparar ativos nem hierarquizar o risco de fechamento (*short squeeze*). Esta change materializa a RFC-014 na sub-aba "Fundamentos", adicionando quatro colunas que respondem, respectivamente, a **Quanto?**, **Quão grave?**, **Quão difícil fechar?** e **Qual o nível de risco?**.

## What Changes

- Adiciona quatro colunas à tabela da sub-aba "Fundamentos", **entre** `Tendência do dividendo` e `FFO/Receita (12m)`, nesta ordem: `Shorts%`, `Volume de Shorts`, `Fechamento Shorts` e `Risco Fechamento`.
- **BREAKING (colunas)**: a ordem das colunas da tabela fundamentalista muda; o CSV copiado e a orientação da sub-aba passam a incluir as novas colunas.
- `Shorts%` = `(Ações Alugadas ÷ Free Float) × 100`, numérico em percentual com uma casa decimal.
- `Volume de Shorts` = classificação categórica do `Shorts%` em cinco rótulos (`Inexistente`, `Muito Baixo`, `Baixo`, `Alto`, `Muito Alto`).
- `Fechamento Shorts` (SIR) = `Ações Alugadas ÷ Volume Médio Diário de Negociação`, numérico (razão com uma casa decimal).
- `Risco Fechamento` = classificação categórica do SIR nos mesmos cinco rótulos.
- **Free float** obtido do CVM FRE (`Quantidade_Total_Acoes_Circulacao`), reutilizando o CSV `fre_cia_aberta_distribuicao_capital` já baixado e parseado pelo `CvmAcionistasSource`. **Fallback**: quando o free float não existir para o ticker, o denominador do `Shorts%` passa a ser o total emitido (`Nro. Ações`/cotas).
- **Ações alugadas** obtidas da B3, do arquivo público diário "Posições em Aberto de Empréstimo de Ativos". Um *spike* de aquisição fixa o mecanismo exato (formulário Lumis → `fileId` → `fileDownload.jsp`) antes do adapter.
- **Volume médio diário** calculado em memória a partir do `fin_instr_qty` dos dias já carregados (mesmo `daily_data` injetado no caso de uso), sem fonte nova; média dos dias disponíveis e `N/A` quando não houver nenhum.
- **Escopo por tipo**: `Papel` (ação) usa free float real; `FII` usa o total de cotas como denominador do `Shorts%`; `ETF`/`FIAGRO`/`BDR` exibem `N/A` quando não houver dado.
- **Não-objetivo**: integração FINRA para BDRs (exigiria mapear BDR→símbolo US, free float da empresa americana e licenciamento) fica citada como oportunidade futura, fora desta change.
- Insumo ausente resulta em `N/A` na coluna correspondente, sem impedir as demais.
- Bump da versão de schema do cache histórico de fundamentos para persistir os novos campos estruturados.

## Capabilities

### New Capabilities
- `short-interest`: métricas determinísticas de *short interest* (Shorts%, SIR), classificações de volume de shorts e risco de fechamento, tratamento de `N/A` e proveniência dos insumos (ações alugadas, free float e volume médio).

### Modified Capabilities
- `gui-interface`: a tabela fundamentalista passa a exibir as quatro novas colunas na posição definida, com alinhamento à direita para as numéricas, e o OrientationPanel da sub-aba "Fundamentos" descreve as novas colunas e como interpretá-las.

## Impact

- **Domínio**: novas funções puras e enums de classificação em `domain/fii/metrics.py` e `domain/fii/classification_faixas.py`; novos campos em `AnaliseFundamental` (`domain/fii/analysis.py`).
- **Aplicação**: novas portas (`ShortInterestProvider`, free float), resolução em `fundamental_analysis.py` e `fundamental_providers.py`; campos normalizados em `fundamental_ports.py`.
- **Infraestrutura**: extensão do `CvmAcionistasSource` para free float (CVM FRE) e novo adapter B3 de empréstimos; ajuste do codec do cache histórico (`fundamental_analysis_codec.py`, bump de `SCHEMA_VERSION_FUNDAMENTOS`).
- **Apresentação**: `charts/fundamental_rows.py` (colunas, alinhamento e linha), formatadores e rótulos, `app_tabs.py` (orientação) e `panels.md`.
- **Documentação**: `panels.md` e o texto de orientação da sub-aba.
- **Testes**: unitários das métricas/classificações, dos adapters (CVM FRE e B3 empréstimos) e da renderização/ordem das colunas.
