<!-- Ordem de implementação: a seção 5 (porte do transporte do chat) DEVE ser
     implementada antes das seções 1–4 (core do prompt), pois ambas reescrevem
     `_enviar`/`_executar` em `chat/envio.py` e o estado de `ChatPanel`.
     Ver design.md, "Decisão 8 (herdada)". -->

## 1. Prefixo estável e sufixo volátil

- [ ] 1.1 Dividir `_montar_prompt` em `_montar_prefixo(contexto)` e `_montar_sufixo(pergunta, fontes, texto_integral)` em `consultar.py`, e verificar com teste headless que o prefixo contém `SYSTEM_PROMPT`, `INSTRUCAO_FORMATO` e o contexto estável, e o sufixo contém fontes, texto integral e pergunta
- [ ] 1.2 Compor o `system_prompt` de `_completar` como `SYSTEM_PROMPT + INSTRUCAO_FORMATO + contexto_estavel` e verificar que as mensagens enviadas têm o prefixo no sistema, o histórico no meio e o sufixo no turno atual
- [ ] 1.3 Garantir que as duas chamadas da cascata usam o mesmo prefixo e histórico, diferindo só no sufixo, com teste headless das mensagens da segunda chamada

## 2. Memoização por assinatura

- [ ] 2.1 Fazer `MontarContextoChat` devolver `(bloco_estavel, assinatura)` derivada do conteúdo (conhecimento + fundamentos + resumos), com teste headless de determinismo (mesma entrada, mesmos bytes)
- [ ] 2.2 Memoizar o último `(assinatura, bloco)` por conversa no `ChatPanel` e reusar quando a assinatura casar, com teste headless de reuso sem recomputo
- [ ] 2.3 Reconstruir o bloco quando fundamentos, watchlist ou resumos mudarem, verificando com teste que a assinatura muda e o prefixo é reconstruído

## 3. Composição com fontes voláteis

- [ ] 3.1 Garantir que `fontes_adicionais` (busca vetorial/notícias) não integram o bloco estável nem a assinatura e ficam no sufixo, com teste headless, mas nao implementar `llm-chat-rag` (apenas preparação para implementaçao futura)
- [ ] 3.2 Verificar que a fonte vetorial do `llm-chat-rag` (quando presente) permanece no sufixo e não invalida o prefixo, mas nao implementar `llm-chat-rag` (apenas preparação para implementaçao futura)

## 4. Testes headless e verificação

- [ ] 4.1 Cobrir a forma do prompt em `tests/test_application` (sem `DISPLAY`): prefixo idêntico entre turnos, voláteis no sufixo, invalidação por assinatura e prefixo compartilhado entre as chamadas
- [ ] 4.2 Confirmar que nenhum teste novo usa `@needs_display` e que a contagem do guardrail de testes de UI não aumentou
- [ ] 4.3 Adicionar os deltas de `llm-chat-llm` e `llm-chat-context`, validar o change e rodar a suíte de aplicação, testes de complexidade e a checagem de fronteiras

## 5. Porte do envio do chat para o manager (herdado de `background-job-manager`)

<!-- Herdado da task 5.5 de `background-job-manager`: o envio do chat foi a única
     thread inline que ficou de fora daquela change (preview/resumo avulso,
     teste de config LLM e verificação de versão já foram portados). Aplicar
     esta seção fecha a 5.5, sem alterar o comportamento observável do chat.
     ESTA SEÇÃO VEM ANTES DAS SEÇÕES 1–4 (ver topo do arquivo).
     O gerenciador DEVE ser local ao painel (ou sem listeners de ciclo de vida),
     nunca o global de `app_wiring`, para não acionar o estado ocupado global.
     Sem delta de spec próprio: conclui a capability `background-jobs`; o único
     requisito novo é o handshake de confirmação, a incorporar ao spec de
     `background-jobs` quando `background-job-manager` for arquivado. -->

- [ ] 5.1 Estender `JobCallbacks`/`BackgroundManager` com um callback genérico de evento (`ao_evento`) e um evento `Confirmacao` (com `Event` e caixa de resposta) para o handshake worker→Tk, com teste headless do despacho na thread do Tk
- [ ] 5.2 Portar `chat/envio.py` para um manager **local do painel** no grupo `"chat"` com política `latest_wins` e token por job (nunca o manager global, para não alterar cursor/botões da janela), eliminando `_fila`, `_poll`, `_geracao` e a thread inline, preservando o cancelamento cooperativo e o descarte do desfecho tardio das duas chamadas da cascata
- [ ] 5.3 Derivar `_processando` e os controles (`_atualizar_controles`) do ciclo de vida do manager em `chat_panel.py` e adaptar `_atender_confirmacao` ao evento `Confirmacao`
- [ ] 5.4 Adaptar os testes de chat que tocam `_fila`/`_trabalhadores`/`_geracao` (mantendo paridade de mensagens, estados de botão e histórico) e confirmar que a contagem de `@needs_display` não aumentou
- [ ] 5.5 Rodar a suíte de apresentação, `ruff`, complexidade e a checagem de fronteiras, e confirmar ausência de novas violações
