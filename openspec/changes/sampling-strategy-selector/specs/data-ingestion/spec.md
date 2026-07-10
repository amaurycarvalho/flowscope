## MODIFIED Requirements

### Requirement: Janela temporal com offsets de Fibonacci

O sistema DEVE calcular as datas de download usando offsets de Fibonacci a partir da data de referência, **parametrizável por período e método de amostragem configurados pelo usuário**. A configuração padrão (período=30, método=Fibonacci) mantém o comportamento atual: d-1, d-2, d-3, d-5, d-8, d-13, d-21. Outras combinações de período e método produzem diferentes conjuntos de datas conforme definido no capability `sampling-strategy`.

#### Scenario: Cálculo da janela a partir de uma data de referência (configuração padrão)

- **WHEN** a data de referência é `2026-06-26` (sexta-feira), período=30 e amostragem=Fibonacci
- **THEN** as datas calculadas DEVEM ser: 2026-06-25, 2026-06-24, 2026-06-23, 2026-06-22, 2026-06-18, 2026-06-15, 2026-06-05 (considerando apenas dias úteis)

#### Scenario: Cálculo com período=60 e Fibonacci

- **WHEN** a data de referência é `2026-06-26`, período=60 e amostragem=Fibonacci
- **THEN** as datas DEVEM incluir também d-34 e d-55 em relação à data de referência (além dos 7 offsets padrão)

### Requirement: Cache-only para períodos acima de 30 dias

O sistema DEVE, quando o período selecionado for maior que 30 dias, utilizar apenas dados do cache local para todas as datas, sem realizar requisições HTTP à B3.

#### Scenario: Período 60 dias sem cache não baixa dados

- **WHEN** período=60 e o cache não contém dados para as datas calculadas
- **THEN** o sistema DEVE pular as datas sem cache e retornar apenas os dados disponíveis, sem fazer download

## ADDED Requirements

### Requirement: Ajuste de data para cache disponível

O sistema DEVE, para cada data calculada em modo cache-only (período > 30), buscar no cache a data mais próxima dentro de uma margem de ±7 dias corridos. Se uma data alternativa for encontrada, deve substituir a data original. Se nenhuma data for encontrada dentro da margem, a data DEVE ser pulada.

#### Scenario: Data exata encontrada no cache

- **WHEN** a data calculada ref_date - 55 está presente no cache
- **THEN** o sistema DEVE usar ref_date - 55 sem ajustes

#### Scenario: Data aproximada encontrada no cache

- **WHEN** ref_date - 55 não está no cache, mas ref_date - 52 está (dentro de ±7 dias)
- **THEN** o sistema DEVE usar ref_date - 52 como substituta

#### Scenario: Nenhuma data próxima no cache

- **WHEN** ref_date - 55 não está no cache e nenhuma data dentro de ±7 dias está disponível
- **THEN** o sistema DEVE pular esta data e continuar com as demais

### Requirement: Deduplicação da lista final de datas

O sistema DEVE remover datas duplicadas do conjunto final, mantendo apenas uma ocorrência de cada data na lista ordenada.

#### Scenario: Datas duplicadas removidas

- **WHEN** o ajuste ao próximo dia útil faz duas datas diferentes colapsarem para a mesma data (ex: sábado e domingo ajustam para segunda)
- **THEN** a data DEVE aparecer apenas uma vez na lista final de datas a serem consultadas

### Requirement: Substituição de datas sem trades (pós-resolução ticker-aware)

Após o download dos trades, cada data de amostragem DEVE ser verificada contra os dados reais dos tickers analisados. Se nenhum ticker analisado tiver negociado em uma data de amostragem, a data DEVE ser substituída pela data mais próxima (d±1..d±7, dias úteis não repetidos) onde pelo menos um ticker tenha negociado.

A substituição DEVE ocorrer antes da execução do motor de indicadores, para que gráficos (ex: Evolução da Dominância) exibam todas as datas de amostragem com indicadores computados.

#### Scenario: Data de amostragem sem trades substituída

- **WHEN** uma data de amostragem d não possui trades de nenhum ticker analisado
- **AND** d+1 possui trades de pelo menos um ticker analisado
- **THEN** o sistema DEVE substituir d por d+1 na lista de datas de amostragem
- **AND** o motor de indicadores DEVE computar indicadores para d+1

#### Scenario: Data sem trades mantida se não houver substituta

- **WHEN** uma data de amostragem d não possui trades de nenhum ticker analisado
- **AND** nenhuma data em d±1..d±7 possui trades de nenhum ticker analisado
- **THEN** o sistema DEVE manter d na lista (como fallback, resultando em linha vazia no CSV)
