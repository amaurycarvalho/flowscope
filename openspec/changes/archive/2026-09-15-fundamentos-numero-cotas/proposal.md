## Why

A sub-aba "Fundamentos" exibe o "Nº de cotistas" mas não a quantidade de cotas/ações emitidas — dado que dimensiona o fundo/companhia e complementa patrimônio e cotistas. Esse número já é obtido da B3/CVM no `PatrimonioFii` (e descartado pela análise) e também é publicado pelo Fundamentus (`Nro. Cotas` para FII, `Nro. Ações` para Papel), então falta apenas expô-lo e dar-lhe uma política de prioridade por tipo.

## What Changes

- Adiciona a coluna `Nº de cotas` imediatamente antes de `Nº de cotistas`, alinhada à direita e formatada como inteiro com separador de milhar.
- Expõe no Fundamentus a quantidade de cotas/ações emitidas: `Nro. Cotas` (FII) e `Nro. Ações` (Papel), normalizados em `Decimal`.
- Resolve a quantidade por tipo de ativo: para **FII**, prioriza a B3 (Informe Mensal) e a CVM como fallback, usando o Fundamentus como fallback final; para **Papel**, usa o Fundamentus (única fonte disponível), exibindo `N/A` quando ausente.
- Propaga o valor resolvido por `AnaliseFundamental.cotas`, reutilizando o `PatrimonioFii` já buscado e memorizado (sem novo acesso à rede).
- Atualiza a lista/ordem de colunas, o alinhamento numérico e o quadro de orientações da sub-aba "Fundamentos".
- A contagem de colunas passa de 29 (2 fixas + 27 roláveis) para 30 (2 fixas + 28 roláveis).

## Capabilities

### New Capabilities

(nenhuma)

### Modified Capabilities

- `fundamentus-fundamental-provider`: expor `Nro. Cotas`/`Nro. Ações` como a quantidade de cotas/ações emitidas na composição de campos fundamentalistas.
- `fundamental-source-fallback`: definir a prioridade de fonte por tipo para a quantidade de cotas emitidas (FII: B3/CVM → Fundamentus; Papel: Fundamentus) e a exibição de `N/A` quando ausente.
- `gui-interface`: incluir a coluna `Nº de cotas` na ordem da tabela, no alinhamento à direita e no quadro de orientações.

## Impact

- **Código**: parser/adapter do Fundamentus (`parser.py`, `adapter.py`, `domain/fii/fundamentus.py`); porta de campos (`application/fundamental_ports.py`); resolução por tipo (`application/fundamental_providers.py`); domínio (`domain/fii/analysis.py`); caso de uso (`application/fundamental_analysis.py`); tabela (`presentation/gui/charts/fundamental_rows.py`, `fundamental_formatters.py`); orientação (`presentation/gui/app_tabs.py`); documentação (`panels.md`).
- **Colunas da tabela**: 29 -> 30 (2 fixas + 28 roláveis).
- **Dados/fixtures**: fixtures Fundamentus de ação e FII passam a conter `Nro. Ações`/`Nro. Cotas`; testes de tabela/CSV e contagens de colunas atualizados.
- **Dependências/APIs**: nenhuma nova; reutiliza B3 (Informe Mensal) e CVM (mensal) já acessados e memorizados.
- **Compatibilidade**: a coluna é aditiva; ativos sem o dado permanecem `N/A` e as demais colunas não mudam.
