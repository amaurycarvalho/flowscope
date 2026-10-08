## 1. Configuração persistida

- [x] 1.1 Adicionar `active` (default vazio) à leitura e gravação do bloco `llm.chat` em `src/flowscope/infrastructure/llm/config.py`, preservando as demais chaves; verificar com testes de config que a chave ausente vira `[]` e que a gravação a mantém.
- [x] 1.2 Separar, na gravação, "entrada de provedor salva" de "provedor ativado": gravar `providers` sempre e alterar `provider`/`active` apenas quando a ativação for solicitada; preservar `active` quando a seleção passa a `none`; verificar com testes de save (ativa, preserva e mantém no `None`).
- [x] 1.3 Expor os ativos efetivos na leitura, semeando o provedor corrente (`provider != none`) sem persistí-lo em `active`; verificar com teste de migração (config com `provider` e `active` vazia → corrente incluído; demais `providers` fora).

## 2. Porta de configuração

- [x] 2.1 Estender `LLMConfigPort` (`src/flowscope/application/llm_config_port.py`) e `InfrastructureLLMConfig` (`config_adapter.py`) com: listar provedores ativos efetivos, ativar provedor e gravar com ativação condicional; verificar com testes do adaptador.
- [x] 2.2 Atualizar os dublês/fakes de `LLMConfigPort` usados nos testes de apresentação para as novas operações; verificar rodando os testes de configuração de LLM.

## 3. Diálogo de configuração

- [x] 3.1 Em `config_dialog.py`, registrar na sessão do diálogo a assinatura do teste bem-sucedido (`api_url`+`model`+`api_key` normalizados, sem `rpm`, apenas em memória); verificar com teste de unidade da normalização/comparação.
- [x] 3.2 No salvamento, promover o provedor (gravar entrada, incluí-lo em `active` e mudar `provider`) somente quando a assinatura salva casar com um teste bem-sucedido; senão gravar apenas a entrada e manter `provider`; verificar com testes de `llm-gui`.
- [x] 3.3 Garantir que, ao promover, o provedor fique selecionado no combobox; verificar com teste do fluxo testar→salvar.

## 4. Widget compartilhado

- [x] 4.1 Criar `SeletorModelo` em `src/flowscope/presentation/gui/llm/` compondo combobox readonly + `ttk.Button` com `ai-properties.png` e tooltip, com callbacks de troca e de configuração; verificar com teste headless do widget.
- [x] 4.2 Popular o combobox com ativos efetivos + `None`, refletir `provider`, e expor `recarregar()`/`definir_ativo(provider)`; verificar com testes de composição da lista (apenas ativos + corrente + `None`).

## 5. Integração na aba Chat AI

- [x] 5.1 Substituir o `_config_btn` textual do cabeçalho de `chat_panel.py` pelo `SeletorModelo` (combobox + botão de ícone), removendo o rótulo "Configuração"; verificar com teste de integração do chat.
- [x] 5.2 Tratar a troca no combobox persistindo o provedor ativo e reavaliando o estado da LLM; verificar com teste de troca (persiste `provider`, preserva `providers`/`active`, reavalia).
- [x] 5.3 Incluir o combobox no bloqueio de `_atualizar_controles` durante o envio e restaurá-lo ao término; verificar com teste de bloqueio.

## 6. Integração em Documentos e Notícias

- [x] 6.1 Substituir o `_ia_btn` de `document_tree_panel.py` e de `noticias_panel.py` pelo `SeletorModelo`, removendo `_on_ia` e a referência ao callback "I.A."; verificar com testes dos painéis.
- [x] 6.2 Incluir o combobox e o botão em `all_buttons()` dos dois painéis, para desabilitar/restaurar durante processamento; verificar com teste de bloqueio global.
- [x] 6.3 Atualizar a mensagem de indisponibilidade de resumo de Documentos para orientar o botão de configuração; verificar com teste da mensagem.
- [x] 6.4 Atualizar `tests/test_presentation/test_button_state.py` (referência a `_ia_btn`) e demais testes que citem "I.A."/"Configuração"; verificar com `make test`.

## 7. Coordenação e rótulo de tokens

- [x] 7.1 Em `app_tab_actions.py`, recarregar os três seletores e reavaliar chat + `refresh_resumir_button` dos painéis após salvar o diálogo e após a troca no combobox; verificar com teste de integração.
- [x] 7.2 Garantir que a troca de modelo não republica o rótulo de tokens nem reseta sessão/`_navegacao`; verificar com teste de tokens (`test_chat_envio.py`) cobrindo troca sem nova completion.

## 8. Qualidade

- [x] 8.1 Rodar `make lint` e corrigir os apontamentos de estilo e documentação.
- [x] 8.2 Rodar `make test` e garantir a cobertura mínima e a suíte verde.
