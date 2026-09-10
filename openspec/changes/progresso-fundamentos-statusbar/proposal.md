## Why

Durante a análise fundamentalista em background, a barra de status usa o glifo `ℹ`, que não renderiza de forma consistente em todas as plataformas (aparece como um "i" solto), e não há barra de progresso — enquanto o primeiro ticker é processado, o usuário vê uma pausa sem feedback. Além disso, o cursor de espera (`watch`) definido na janela é sobrescrito pelos cursores próprios de botões e da lista de tickers, então o hourglass não aparece quando o ponteiro está sobre eles.

## What Changes

- **Barra de progresso na fase de Fundamentos**: exibir a barra de progresso durante a análise fundamentalista, avançando por ticker (`current`/`total`) e com um estado inicial `0/N`, mantendo-a visível até a conclusão da fase.
- **Glifo de status consistente**: substituir o `ℹ` por um marcador que renderize de forma confiável (ex.: `•`), alinhado aos demais glifos que já aparecem corretamente (ex.: `✓`).
- **Cursor de espera em todos os widgets**: propagar o cursor `watch` para os widgets interativos, inclusive os que definem cursor próprio (botões, lista de tickers, comboboxes e data entry), restaurando cada cursor ao final da operação.
- **Controles desabilitados durante a fundamental**: manter botões, comboboxes, data entry e a lista de tickers desabilitados durante toda a análise fundamentalista em background, restaurando-os somente ao final, como ocorre na carga histórica.
- **Ajuste de apresentação**: a mensagem de progresso por ticker deixa de usar `set_status` com `ℹ` e passa a atualizar a barra de progresso com o marcador consistente. A mensagem publicada pelo job passa a carregar `current`/`total`.

## Capabilities

### New Capabilities
<!-- Nenhuma capability nova: são extensões de comportamento da interface existente. -->

### Modified Capabilities
- `gui-interface`: barra de progresso da análise fundamentalista e glifos consistentes na barra de status.
- `loading-state-management`: cursor de espera aplicado também aos widgets que definem cursor próprio.

## Impact

- **Código**: `presentation/gui/fundamental_job.py` (mensagem com `current`/`total`), `presentation/gui/controller.py` (consumo e estado inicial `0/N`), `presentation/gui/presenter.py` (progresso na barra e marcador), `presentation/gui/app_status.py` (cursor em todos os widgets e limpeza condicional da barra).
- **Testes**: `tests/test_presentation/test_fundamental_job.py`, `test_controller.py`, `test_presenter.py`, `test_button_state.py` e testes de status/cursor.
- **Compatibilidade**: o consumo de mensagens tolera o formato antigo sem `current`/`total`; nenhum contrato de domínio ou de aplicação muda.
- **Não escopo**: o tempo de renderização síncrona dos gráficos em `on_result` (não faz parte dos três pontos).
