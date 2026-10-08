## Why

Trocar o provedor de LLM ativo hoje exige abrir o diálogo de configuração, selecionar o provedor, e salvar — o único gatilho é o botão "I.A." da sub-aba Documentos e o botão textual "Configuração" do chat. Não há como alternar rapidamente entre os provedores já validados, nem visibilidade de quais foram testados com sucesso. Além disso, a troca de modelo no meio da sessão não tem comportamento definido para o estado da conversa e o rótulo de contexto.

## What Changes

- Novo estado persistido `llm.chat.active`: lista dos provedores cuja conexão foi testada com sucesso **e** cujo teste corresponde à configuração salva (string de conexão `api_url`+`model`+`api_key`, `rpm` excluído). Uma vez ativo, o provedor permanece ativo.
- Combobox de seleção de modelo ativo (provedores em `active` + opção `None`), substituindo a troca por diálogo. Trocar no combobox grava `llm.chat.provider` imediatamente, preservando `providers` e `active`; `None` apenas desativa o provedor corrente.
- O botão textual "Configuração" do cabeçalho da aba "Chat AI" passa a ser um botão de ícone (`ai-properties.png`), posicionado logo após o combobox, reduzindo o espaço ocupado.
- O botão "I.A." das sub-abas "Documentos" e "Notícias" é **removido**; no mesmo lugar entram o combobox de modelo ativo e o botão de configuração com ícone.
- O modal de configuração passa a: ao selecionar um provedor, testá-lo com sucesso e salvar, ativá-lo e selecioná-lo automaticamente no combobox; ao salvar sem teste bem-sucedido dos valores salvos, manter a seleção anterior do combobox (grava apenas a entrada de `providers`).
- Migração: na primeira leitura, se `llm.chat.provider` não for `none` e não estiver em `active`, ele é semeado em `active` (apenas o provedor corrente), mantendo a UI coerente com o comportamento atual; os demais provedores exigem re-teste.
- O combobox e o botão de ícone ficam desabilitados durante processamento: no chat, enquanto houver envio em curso; em Documentos/Notícias, durante qualquer job em andamento.
- Comportamento definido na troca de modelo no meio da sessão: a sessão e a cota de navegação são herdadas (sem reset), o rótulo de tokens não é republicado na troca (evita misturar o prompt do modelo anterior com a janela do novo).

## Capabilities

### New Capabilities

<!-- Nenhuma: o comportamento é absorvido pelas capacidades existentes de configuração e GUI de LLM. -->

### Modified Capabilities

- `llm-config`: novo estado `llm.chat.active`, semântica de gravação que separa "entrada salva" de "provedor ativado", preservação de `active` no `None` e regra de migração/semeadura.
- `llm-gui`: o diálogo deixa de ser acionado pelo botão "I.A." da sub-aba Documentos e passa a ser acionado pelo botão de ícone; a promoção a ativo ocorre no salvamento condicionado a teste bem-sucedido dos valores salvos.
- `llm-chat-gui`: cabeçalho substitui o botão textual "Configuração" por combobox de modelo ativo + botão de ícone; desabilitação durante o envio.
- `llm-chat-tokens`: define que a troca de modelo não republica o rótulo (o percentual só é recalculado a partir da completion seguinte, com num e den do mesmo modelo).
- `documentos-ticker-panel`: o botão "I.A." da barra de documentos é substituído por seletor de modelo ativo + botão de configuração com ícone; ajustes de posição e das mensagens que citam o botão "I.A.".
- `noticias-panel`: a barra da sub-aba "Notícias" substitui o botão "I.A." por seletor de modelo ativo + botão de configuração com ícone.

## Impact

- **Configuração**: `~/.flowscope/config.json` ganha `llm.chat.active`; a gravação passa a aceitar a ativação condicional.
- **Apresentação**: novo widget compartilhado (combobox + botão de ícone) usado em `chat_panel.py`, `document_tree_panel.py` e `noticias_panel.py`; remoção do `_ia_btn`; ajustes em `app_tab_actions.py` (refresh coordenado dos combos) e `app_status.py` (bloqueio global inclui o combo).
- **Contrato da porta**: `LLMConfigPort`/`InfrastructureLLMConfig` ganham leitura de `active` e gravação com ativação condicional.
- **Testes**: `test_button_state.py::test_botao_ia_desabilitado_e_restaurado` deixa de referenciar `_ia_btn`; testes de config para `active`/migração/save condicional; testes de rótulo na troca de modelo.
- **Dependências**: nenhuma nova.
