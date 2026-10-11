## Why

Quando o provedor de IA responde com erro de cota/limite (HTTP 429 `RESOURCE_EXHAUSTED`), o lote de resumo de Notícias — configurado como contínuo — segue tentando cada item pendente, falhando em todos e emitindo um stack trace por item. Além de martelar a API sem chance de sucesso, isso polui o log e torna o desfecho ilegível, sem que o usuário entenda que precisa aguardar a renovação da cota ou trocar de provedor.

## What Changes

- **Interrupção do lote em cota esgotada**: ao encontrar `LLMRateLimitError` (limite/cota do provedor) durante a geração de resumo em lote, o lote para imediatamente — inclusive o lote contínuo de Notícias — preservando os resumos já gravados. Os demais itens permanecem pendentes para uma nova tentativa posterior.
- **Desfecho único e honesto**: a falha de cota é reportada uma única vez na barra de status, distinguindo-a de falhas isoladas por item; a mensagem orienta aguardar a renovação ou reconfigurar o provedor.
- **Registro conciso**: a cota esgotada é registrada uma única vez em nível de aviso, sem traceback por item; as demais falhas transitórias mantêm o comportamento atual.

## Capabilities

### New Capabilities
- `resiliencia-cota-llm`: interrupção do lote de resumo ao esgotar a cota/limite do provedor de IA, com desfecho único e registro conciso.

### Modified Capabilities
- `noticias-panel`: o lote contínuo de Notícias deixa de continuar item a item quando a falha é de cota/limite, passando a interromper o lote e reportar o desfecho uma vez.

## Impact

- Código: `presentation/gui/resumos_job.py` (propagar a interrupção do lote por cota), `presentation/gui/app_resumos_actions.py` (desfecho e registro conciso), `presentation/gui/llm/mensagens.py` (mensagem de cota), e possivelmente `application/documentos/lote.py` (política de continuidade).
- Sem quebra de contrato de dados; resumos já gravados são preservados e os itens não processados permanecem pendentes.
- Sem novas dependências.
