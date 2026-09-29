## Why

Alguns provedores impõem limites ao volume de tokens de entrada permitidos (ex.: quotas por minuto do Gemini free tier), e o prefixo do chat carrega sempre os dados iniciais — conhecimento do FlowScope, fundamentos da watchlist e resumos de documentos. Esse volume inicial é reenviado a cada completion e pode estourar a cota antes mesmo de o usuário obter resposta. Falta uma forma de o usuário declarar que o modelo tem janela de entrada limitada e fazer esse contexto ser carregado sob demanda.

## What Changes

- Novo parâmetro booleano `input_limitado` por provedor/modelo na configuração da LLM (`llm.chat.providers[<provider>]`), com default `false`.
- Checkbox correspondente no diálogo de configuração, persistido e restaurado ao trocar de provedor.
- Com o flag ativo, o prefixo estável do chat NÃO DEVE carregar conhecimento, fundamentos e resumos; em vez disso, DEVE informar a existência desses recursos e como solicitá-los.
- Os recursos iniciais (conhecimento, fundamentos e resumos) passam a ser servidos sob demanda pela mesma cascata de requisição de conteúdo já usada para documentos.
- Com o flag ativo, o orçamento da cascata sobe de duas para **até três chamadas** para acomodar a requisição de recursos e a escalada para documentos na mesma pergunta.
- Recursos iniciais solicitados sob demanda DEVEM passar por um gate de confirmação com **texto próprio**, distinto do gate de texto integral de documentos.

## Capabilities

### New Capabilities

<!-- Nenhuma: a mudança estende configuração e composição de contexto já existentes. -->

### Modified Capabilities

- `llm-config`: o bloco `llm.chat.providers[<provider>]` passa a guardar `input_limitado`, com default `false`, preservado na memória por provedor.
- `llm-gui`: o diálogo de configuração ganha o checkbox de janela de entrada limitada, carregado/salvo junto dos demais campos.
- `llm-chat-context`: com o flag ativo, o bloco estável omite conhecimento, fundamentos e resumos, apresenta um manifesto de recursos disponíveis e serve esses recursos sob demanda com gate próprio.
- `llm-chat-llm`: a cascata passa a admitir até três chamadas quando o flag está ativo, servindo os recursos iniciais e mantendo o prefixo estável compartilhado.

## Impact

- **Código**: `infrastructure/llm/config.py` (`_CHAT_FIELDS`, `_normalizar_provedor`, `save_llm_config`), `application/llm_config_port.py`/`infrastructure/llm/config_adapter.py` (contrato do flag), `presentation/gui/llm/config_dialog.py` (checkbox), `application/chat/contexto.py` (`_renderizar_bloco`, manifesto, gate) e `application/chat/consultar.py` (orçamento 2→3 e serviço de recursos).
- **Config persistida**: novo campo booleano em `llm.chat.providers`; leitura com default `false` garante compatibilidade com arquivos existentes (sem migração).
- **Comportamento**: sem o flag, o comportamento atual é preservado integralmente.
- **Interação**: com o flag ativo, o prefixo estável fica menor, reduzindo o peso na janela de contexto e a pressão de cache acompanhada pela change `llm-chat-contabilidade-tokens`.
