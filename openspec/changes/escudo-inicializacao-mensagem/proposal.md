## Why

O escudo de inicialização cobre a janela como um `tk.Frame` vazio, sem nenhuma indicação textual. O usuário vê uma tela cinza sem saber que a aplicação está inicializando e pode interpretar como travamento. Além disso, durante o bloqueio a barra superior com o rótulo "Data de referência" e seus controles pode permanecer acessível/visível em vez de ser coberta pelo escudo, quebrando a promessa de bloqueio total da entrada.

## What Changes

- O escudo de inicialização passa a exibir, dentro dele, uma mensagem de espera (ex.: "Aguarde a inicialização da aplicação…"), centralizada na janela.
- O escudo passa a cobrir de forma garantida toda a extensão do toplevel — incluindo a barra superior (rótulo "Data de referência", entrada de data, botões e comboboxes) —, sendo reerguido sobre os irmãos após a colocação, de modo que nenhum controle da barra superior escape ao bloqueio.
- Popups auxiliares associados à barra superior (tooltip da data e calendário do `DateEntry`) NÃO devem aparecer acima do escudo durante a inicialização.

## Capabilities

### New Capabilities
<!-- Nenhuma: o comportamento do escudo estende o bloqueio de entrada já existente. -->

### Modified Capabilities
- `loading-state-management`: o requisito "Bloqueio de entrada durante a inicialização" passa a exigir que o escudo apresente uma mensagem de espera e cubra toda a janela, inclusive a barra superior de data.

## Impact

- `src/flowscope/presentation/gui/startup_gate.py`: `colocar_escudo` passa a construir a mensagem e a garantir cobertura/empilhamento sobre a barra superior.
- `tests/test_presentation/test_startup_gate.py`: verificação da presença da mensagem e da cobertura da barra superior (dentro do orçamento de testes de UI).
- Delta em `openspec/specs/loading-state-management/spec.md`.
- Sem impacto em `domain`, `application` e `infrastructure`. Sem alteração no tempo de inicialização.
