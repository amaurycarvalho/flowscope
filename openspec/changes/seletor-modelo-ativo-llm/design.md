## Context

Ver `proposal.md` — Why. A configuração de completion já vive em `llm.chat` (`config.py`), com `provider` (seleção ativa) e o mapa `providers` (credenciais por provedor). O diálogo (`config_dialog.py`) grava o bloco via `save_llm_config`, que hoje sempre promove o provedor do formulário. A janela de contexto é resolvida por `resolve_context_window` (preset + liteLLM) e consumida por `EnvioMixin._janela_contexto` e por `ChatPanel`. O botão de configuração é textual no chat e "I.A." em Documentos/Notícias (`document_tree_panel.py`, `noticias_panel.py`), acionando `_abrir_config_llm`.

## Goals / Non-Goals

**Goals:**
- Persistir `llm.chat.active` e derivar dele o combobox de modelo ativo (ativos + `None`).
- Separar "gravar entrada de provedor" de "ativar provedor", condicionando a ativação a um teste bem-sucedido dos valores salvos.
- Widget único de seleção/configuração reutilizado nas três telas.
- Preparar o rótulo de tokens para troca de modelo no meio da sessão sem cálculo cruzado.

**Non-Goals:**
- Alterar a resolução da janela de contexto (`resolve_context_window`) ou os presets.
- Recalcular/limitar o percentual quando o contexto herdado excede a janela do novo modelo.
- Persistir histórico de conversa entre sessões.
- Indexação/RAG (change `llm-chat-rag`, independente).

## Decisions

### 1. `active` como lista em `llm.chat`

Alternativa: booleano por entrada (`providers.<p>.tested`). Descartada porque a normalização de credenciais (`_CHAT_FIELDS`) reescreve a entrada a cada gravação e porque o teste não deve virar campo de credencial. A lista separada expressa "quais provedores estão ativos" e é preservada no read-modify-write.

### 2. Identidade de conexão = `api_url` + `model` + `api_key`

A promoção a ativo exige que o teste bem-sucedido corresponda aos valores salvos. A assinatura é normalizada (trim; URL sem barra final; `rpm` excluído) e mantida **apenas em memória** na sessão do diálogo — a chave nunca é usada como critério persistido. Alternativa: comparar o config inteiro, incluindo `rpm`; descartada porque `rpm` não afeta a conexão e mudaria o resultado sem motivo.

### 3. Promoção monotônica

Uma vez ativo, o provedor permanece ativo mesmo que a credencial seja editada depois sem novo teste ("testado com sucesso **pelo menos uma vez**"). Isso mantém a coerência com a regra de que salvar sem teste preserva a seleção anterior e evita rebaixamentos surpresa.

### 4. Semeadura efetiva do provedor corrente

Na leitura, o provedor corrente (`provider != none`) é tratado como membro efetivo do conjunto de ativos, sem ser persistido em `active` e sem afirmar que foi testado. Alternativa: semear persistindo em `active`; descartada por violar a semântica de "testado". Alternativa: nascer totalmente vazio; descartada porque a UI (combobox em `None`) divergiria do comportamento (chat usando o provedor corrente).

### 5. Widget compartilhado `SeletorModelo`

Um widget em `presentation/gui/llm/` compõe combobox + `ttk.Button` com `ai-properties.png` e delega: `on_trocar(provider)` (persistir e reavaliar) e `on_configurar()` (abrir o diálogo), além de `definir_ativo(provider)`/`recarregar()`. Alternativa: duplicar nos três painéis; descartada por espalhar a lógica de refresh e a lista efetiva.

### 6. Coordenação de refresh

`app_tab_actions._abrir_config_llm` passa a ser o ponto que, ao salvar e ao trocar no combobox, recarrega os três seletores, reavalia o chat (`_reavaliar_chat_llm`) e os botões `Resumir pendentes` dos painéis. A troca direta no combobox persiste via porta e chama o mesmo caminho.

### 7. Bloqueio durante processamento

No chat, o combobox entra em `_atualizar_controles` junto de `_config_btn`/`_send_btn`. Em Documentos/Notícias, o combobox e o botão integram `all_buttons()`, entrando no mecanismo global `_disable_all_buttons`/`_restore_all_buttons` que já cobre qualquer job.

### 8. Troca de modelo não recalcula o rótulo

`avaliar_estado`/`_reavaliar_chat_llm` não publicam tokens; a decisão é **não** adicionar republicação na troca, para não combinar o prompt do modelo anterior com a janela do novo. A sessão e a `_navegacao` permanecem (já é o comportamento atual; a navegação só zera por mudança de assinatura da árvore).

## Risks / Trade-offs

- **[Risco] Divergência se `active` não for preservado na gravação** → `save_llm_config` deve ler, mesclar e regravar `active` explicitamente; teste dedicado.
- **[Risco] Assinatura de teste frágil a normalização de URL** → normalizar (trim e barra final) antes de comparar; teste com URLs equivalentes.
- **[Risco] Percentual > 100% ao herdar contexto em modelo de janela menor** → aceito e exibido sem saturação; a navegação (32K tokens) e o diálogo (10 msgs/8K chars) limitam o prompt herdado.
- **[Trade-off] `active` monotônica pode manter ativo um provedor cuja credencial piorou** → intencional ("pelo menos uma vez"); o teste manual continua disponível.
- **[Trade-off] `ttk.Button` com imagem não mostra texto** → mitigado por tooltip, como já se faz com botões de ícone existentes.

## Migration Plan

1. Adicionar `active` (default vazio) à leitura/gravação, preservando chaves existentes; semeadura efetiva do provedor corrente.
2. Estender `LLMConfigPort`/`InfrastructureLLMConfig`: listar ativos efetivos, ativar/desativar provedor e gravar com ativação condicional.
3. Criar o widget `SeletorModelo` e integrá-lo ao chat, Documentos e Notícias, removendo o botão "I.A.".
4. Ajustar o diálogo para registrar a assinatura do teste bem-sucedido e decidir a promoção no salvamento.
5. Rollback: remover `active` e reverter a UI; mudanças são aditivas e o sistema volta ao comportamento anterior ignorando a chave.

## Open Questions

- O rótulo do item do combobox deve exibir só o nome do provedor ou `provedor / modelo`? Puramente cosmético; resolvível na implementação sem alterar as specs.
