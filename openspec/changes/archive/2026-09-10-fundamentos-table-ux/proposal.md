## Why

O layout da tabela fundamentalista é redefinido a cada execução, a barra de status não distingue dados vindos do cache nem informa o desfecho da carga, e o cursor de espera é restaurado antes de a análise fundamentalista terminar. Isso gera retrabalho de ajuste de colunas e feedback impreciso ao usuário.

## What Changes

- As larguras das colunas da tabela fundamentalista são persistidas no `config.json` e restauradas na próxima execução.
- O texto de progresso da análise fundamentalista recebe o sufixo `" - cached"` quando o dado do ticker vem do cache (resultados `HIT` e `REVALIDATED`).
- Ao final da carga, a barra de status exibe:
  - `"Dados atualizados com sucesso."` quando não houve falha na captura;
  - `"Dados atualizados com mitigação de falhas."` quando houve falha recuperável;
  - `"Falha ao atualizar dados"` em falha catastrófica.
- O cursor de espera (`watch`) permanece visível durante toda a análise fundamentalista, inclusive quando os dados vêm do cache.

## Capabilities

### New Capabilities
<!-- Nenhuma capability nova. -->

### Modified Capabilities

- `gui-interface`: persistência das larguras das colunas e mensagens de status da análise fundamentalista (sufixo de cache e desfecho final).
- `loading-state-management`: o cursor de espera permanece durante a análise fundamentalista, mesmo com dados servidos do cache.

## Impact

- **Código**: `presentation/gui/app.py` (preferências e ciclo de vida), `presentation/gui/charts/fundamental_table.py` (larguras), `presentation/gui/app_status.py`/`presenter.py`/`controller.py` (status e cursor), `infrastructure/fii/fundamentus/adapter.py` (propagação do resultado de cache).
- **Configuração**: nova chave de preferências para as larguras das colunas.
- **Specs-base**: arquivar **depois** de `fundamental-metrics-table` e `conditional-cache-fundamentus-cvm` (materializam `gui-interface` e o resultado de cache).
- **Compatibilidade**: apenas comportamento de apresentação; nenhuma mudança de dados.
