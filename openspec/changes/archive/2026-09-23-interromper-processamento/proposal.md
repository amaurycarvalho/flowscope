## Why

As operações longas executadas em background (análise fundamentalista, aquisição de documentos e resumo em lote) podem demorar minutos e hoje o usuário só recupera a interface quando elas terminam ou quando o watchdog de inatividade de 120s dispara. Não existe forma de o usuário interromper deliberadamente um processamento que já não deseja, o que prende a interface e desperdiça rede e chamadas de LLM.

## What Changes

- Adicionar um botão de interromper (ícone `process-stop.png`) na barra de status, posicionado imediatamente à esquerda da barra de progresso.
- O botão aparece apenas enquanto houver ao menos um job cancelável em background ativo e some, junto com a barra de progresso, ao fim do processamento ou após o usuário interromper.
- Um único clique no botão cancela **todos** os processamentos em background ativos (fundamentalista, documentos e resumos em lote).
- Cancelamento cooperativo real: um token compartilhado é observado no topo dos loops de trabalho; ao detectá-lo, o worker encerra pela via de uma exceção dedicada (`OperacaoCancelada`), sem ser confundido com falha recuperável.
- Ao cancelar, a interface finaliza imediatamente: barra e botão somem, controles e cursor são restaurados, os flashes de sucesso são suprimidos e a barra de status exibe "Processamento interrompido.".
- A carga principal síncrona (índice/Carregar) **não** é coberta por esta mudança; sua migração para thread será tratada em change própria. O botão não deve aparecer/agir durante esse fluxo.
- **BREAKING**: nenhuma.

## Capabilities

### New Capabilities
- `process-cancellation`: controle de interrupção de processamentos longos em background, incluindo a existência, visibilidade e ciclo de vida do botão de interromper, o cancelamento cooperativo de todos os jobs ativos e o desfecho na barra de status.

### Modified Capabilities
<!-- Nenhuma. As requirements existentes de loading-state-management continuam válidas; a restauração de controles/cursor após cancelamento já é coberta pelo estado ocupado existente. -->

## Impact

- **Presentation (GUI)**: `app_layout.py` (criação do botão), `app_status.py` (visibilidade do botão e mensagem de interrupção), `presenter.py` (token de cancelamento, contador de jobs canceláveis, desfecho), `controller_fundamental.py`, `app_actions.py`, `app_resumos_actions.py` (início/finalização e supressão de sucesso), `fundamental_job.py`, `documentos_job.py`, `resumos_job.py` (tratamento distinto de cancelamento).
- **Application**: novo módulo `cancellation.py` (exceção e token); `fundamental_analysis.py` (checagem no loop por ticker).
- **Infrastructure**: `b3/documentos_aquisicao.py` (checagem nos loops de aquisição).
- **Testes**: `tests/test_presentation/` (presenter, jobs, documentos, status) e `tests/test_application/` (casos de uso cancelados).
- Sem novas dependências externas; usa `threading.Event` da biblioteca padrão.
