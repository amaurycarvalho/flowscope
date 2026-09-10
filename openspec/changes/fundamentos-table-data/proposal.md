## Why

A sub-aba "Fundamentos" exibe Tipo/Sub-tipo derivados de uma taxonomia estática e deixa colunas vazias para ativos não elegíveis, enquanto o Fundamentus já entrega, por ticker, a classificação editorial (Papel/FII, setor, segmento, gestão) e os indicadores de mercado. Isso produz uma tabela incompleta e uma classificação que não reflete a fonte primária de dados.

## What Changes

- **BREAKING (classificação)**: as colunas "Tipo" e "Sub-tipo" passam a ser derivadas do Fundamentus, substituindo a taxonomia/sintaxe anteriores:
  - "Tipo" = `Papel` (rótulo `Papel`) ou `FII` (rótulo `FII`);
  - `Papel`: Sub-tipo = `Tipo; Setor; Subsetor` (concatenados por `"; "`);
  - `FII`: Sub-tipo = `Tijolo: Segmento; Gestão` quando `Qtd imóveis > 0`, senão `Papel: Segmento; Gestão`.
- O parser do Fundamentus extrai o discriminador do ticker (`Papel`/`FII`) e os campos `Tipo`, `Setor`, `Subsetor`, `Segmento`, `Gestão`; `Qtd imóveis` (já extraído) passa a ser o balizador Tijolo/Papel.
- Todas as colunas da tabela passam a ser preenchidas quando houver dado na fonte (Fundamentus primário, B3/CVM como fallback), inclusive P/VP, Dividend Yield e dividendo para ações.
- O gate de elegibilidade FFO é removido: FFO Yield, P/FFO e FFO Trend são preenchidos sempre que a fonte fornecer o dado, independentemente do tipo do ticker.
- Novas colunas ao final da tabela: número atual de cotistas, classificação por número de cotistas, tamanho patrimonial do fundo, classificação por tamanho patrimonial e data de referência dos dados.
- A classificação por cotistas e por patrimônio reutiliza as faixas determinísticas já existentes.
- Quando o Fundamentus não fornecer a classificação, a taxonomia/sintaxe atual (`classificar_ticker`) permanece como fallback.

## Capabilities

### New Capabilities
<!-- Nenhuma capability nova: os caminhos afetados já são definidos pelas changes em aberto
     fundamental-metrics-table e fundamentus-fundamental-provider. -->

### Modified Capabilities

- `fundamentus-fundamental-provider`: o parser/modelo passa a expor o discriminador do ticker e os campos `Tipo`, `Setor`, `Subsetor`, `Segmento` e `Gestão`; `Qtd imóveis` passa a balizar Tijolo/Papel.
- `fii-classification`: o tipo e o sub-tipo passam a ser derivados dos campos do Fundamentus (com prefixo `Tijolo:`/`Papel:`), com fallback para a classificação determinística atual.
- `fii-fundamental-metrics`: a elegibilidade deixa de restringir o cálculo; novas métricas de cotistas e patrimônio passam a ser expostas com suas classes e a data de referência.
- `gui-interface`: a tabela fundamentalista ganha novas colunas e passa a preencher todas as colunas aplicáveis por ticker.

## Impact

- **Código**: `infrastructure/fii/fundamentus/` (parser, adapter, modelo em `domain/fii/fundamentus.py`), `domain/fii/classification.py`, `application/fundamental_analysis.py`, `application/fundamental_ports.py`, `presentation/gui/charts/fundamental_table.py`.
- **Dados/fixtures**: as fixtures do Fundamentus precisam cobrir os novos rótulos (`Tipo`, `Setor`, `Subsetor`, `Segmento`, `Gestão`, `Qtd imóveis`) e o layout real.
- **Specs-base**: este change deve ser arquivado **depois** de `fundamental-metrics-table` e `fundamentus-fundamental-provider`, que materializam as specs `fii-classification`, `fii-fundamental-metrics` e `fundamentus-fundamental-provider` em `openspec/specs/`.
- **Compatibilidade**: mudança de comportamento observável nas colunas Tipo/Sub-tipo e no preenchimento das métricas FFO para ativos antes não elegíveis.
