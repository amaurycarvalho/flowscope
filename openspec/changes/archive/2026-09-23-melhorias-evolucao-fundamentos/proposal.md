## Why

A change `analise-short-interest` adicionou a métrica `Shorts%` à tabela de Fundamentos, mas a sub-aba "Evolução dos Fundamentos" ainda não mostra a sua série temporal. Além disso, os rótulos de data dos gráficos exibem apenas mês e ano (`09/26`), o que impede distinguir observações próximas, e os painéis não oferecem inspeção dos pontos individuais, forçando a leitura apenas pelo traço da linha.

## What Changes

- Adicionar um oitavo painel `Shorts%` aos small multiples da sub-aba "Evolução dos Fundamentos", representando a evolução de `AnaliseFundamental.short.shorts_pct`, formatado em percentual com uma casa decimal (igual à coluna `Shorts%` da tabela de Fundamentos).
- Corrigir o rótulo de data dos eixos dos gráficos de `MM/AA` (`%m/%y`) para `DD/MM/AA` (`%d/%m/%y`).
- Acrescentar tooltip de hover em todos os painéis da sub-aba, exibindo a data e o valor correspondente do ponto sob o cursor.
- Atualizar o texto do OrientationPanel da sub-aba e a documentação (`panels.md`, `TAB_CONTENT`/`TAB_CONFIGS`) para refletir os oito painéis e o novo indicador.
- Sem alteração de domínio, de fontes de dados ou do schema do cache histórico: o dado `short.shorts_pct` já é calculado e persistido pela `analise-short-interest`.

## Capabilities

### New Capabilities
<!-- Nenhuma nova capability. -->

### Modified Capabilities
- `fundamental-evolution-panel`: passa a representar oito campos (incluindo `Shorts%`, com uma casa decimal), a rotular as datas com dia/mês/ano e a oferecer tooltip de data e valor em todos os painéis.
- `gui-interface`: o conteúdo do OrientationPanel da sub-aba "Evolução dos Fundamentos" passa a descrever oito mini-gráficos e o indicador `Shorts%`.

## Impact

- **Apresentação**: `presentation/gui/charts/fundamental_evolution_data.py` (novo `CampoEvolucao` e extrator), `fundamental_evolution_panel.py` (contagem de eixos, formato de data e handlers de hover/tooltip); `app_tabs.py` (`TAB_CONFIGS` e `TAB_CONTENT`).
- **Documentação**: `panels.md` (campos, layout e interação).
- **Testes**: `test_fundamental_evolution_data.py`, `test_fundamental_evolution_panel.py` e `test_fundamental_evolution_integration.py` (contagem de séries, tipos, rótulo de data e tooltip).
- **Sem impacto** em domínio, aplicação, infraestrutura, cache histórico ou API pública.
