## Why

O botão "Resumir pendentes" volta a ficar habilitado no meio do processamento em lote: a cada documento resumido, a aplicação do resultado reavalia o estado do botão apenas com "LLM configurada e há pendentes", sem considerar que um lote está em andamento. Isso contraria o requisito vigente ("... e nenhum resumo em lote estiver em andamento") e permite um novo acionamento concorrente enquanto o lote corre.

## What Changes

- Tornar o estado derivado do botão "Resumir pendentes" ciente do lote em andamento, consultando a fonte de verdade já existente no app-layer (o job de resumo ativo).
- Injetar no painel de documentos um predicado de "resumo em lote em andamento", no mesmo padrão de callbacks já usados (`resumir_callback`, `ia_callback`).
- Garantir que qualquer reavaliação disparada durante o lote (documento aplicado, resumo individual concorrente ou recarregamento do painel) mantenha o botão desabilitado, reabilitando-o somente ao término — conclusão ou interrupção — conforme a disponibilidade remanescente.
- Cobertura de testes para a permanência do estado desabilitado ao longo do lote e para a reabilitação ao término.

## Capabilities

### New Capabilities
<!-- Nenhuma nova capability. -->

### Modified Capabilities
- `documentos-ticker-panel`: novo requisito que fixa o comportamento do estado derivado do botão "Resumir pendentes" enquanto o lote está em andamento, incluindo a reavaliação apenas ao término.

## Impact

- `src/flowscope/presentation/gui/charts/document_flow_mixin.py`: estado derivado passa a considerar o lote em andamento.
- `src/flowscope/presentation/gui/charts/document_tree_panel.py`: novo parâmetro de callback de atividade do lote.
- `src/flowscope/presentation/gui/app_tab_layout.py`: injeção do callback ao construir o painel de documentos.
- `src/flowscope/presentation/gui/app_resumos_actions.py`: exposição do predicado de lote ativo a partir de `_resumos_job`.
- Testes de apresentação do painel e do estado de botões.
- Sem mudanças de formato de dados, dependências ou compatibilidade; correção aditiva de estado de interface.
