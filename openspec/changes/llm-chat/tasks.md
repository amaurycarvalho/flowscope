## 1. Pré-requisitos e Setup

- [x] 1.1 Verificar que a `llm-core` está implementada (`LLMPort`, `create_llm_provider`, `load_llm_config`, `check_llm_deps`, `LLMConfigDialog`, exceções tipadas) e registrar o resultado
- [x] 1.2 Verificar que os caches `document-texts/` e `document-summaries/` são legíveis via `DocumentCatalog`/`JsonDocument*Store`
- [x] 1.3 Criar a estrutura de diretórios de domínio/contexto/LLM/GUI do chat
- [x] 1.4 Atualizar README.md com a seção "Chat com IA" (sem novas dependências)

## 2. Domínio — Chat Models

- [x] 2.1 `ChatMessage` e `ChatSession` em `domain/chat/models.py` e verificar testes unitários
- [x] 2.2 Atualizar `domain/chat/__init__.py` com os novos modelos e verificar importação

## 3. Contexto — Conhecimento do FlowScope

- [x] 3.1 Coletor que monta o bloco de conhecimento de `TAB_CONTENT` + constantes da aba Sobre, e verificar teste com fixture
- [x] 3.2 Bloco enviado como system prompt estável nos dois chats, e verificar presença nos dois escopos

## 4. Contexto — Fundamentos

- [x] 4.1 Serializador compacto da tabela de fundamentos (`_fundamental_data`), e verificar saída por ticker
- [x] 4.2 Seleção do escopo: watchlist completa no Chat Geral e ticker foco no Chat Ticker, e verificar cenários
- [x] 4.3 Estado sem dados carregados exibe orientação de carregamento, e verificar mensagem

## 5. Contexto — Cascata de Documentos

- [x] 5.1 Leitor dos resumos curtos/longos por escopo via `DocumentCatalog`, e verificar com store temporário
- [x] 5.2 Leitor do texto integral dos alvos via `JsonDocumentTextStore`, e verificar com cache temporário
- [x] 5.3 Preparação sob demanda de texto/resumo reutilizando `preparar_texto`/`ResumirDocumentoUseCase`, e verificar cache frio
- [x] 5.4 Gates de confirmação por quantidade (0–3, 4–7, ≥8) expostos como callback, e verificar cada faixa
- [x] 5.5 Orçamento de contexto (teto por documento e global) com truncamento e aviso, e verificar limite excedido

## 6. LLM — Orquestração da Cascata

- [x] 6.1 `ConsultarChatUseCase` consumindo `LLMPort`/`create_llm_provider` da `llm-core`, e verificar com mock
- [x] 6.2 Primeira chamada com resumos curtos + longos e interrupção antecipada, e verificar 1 chamada quando há resposta
- [x] 6.3 Segunda chamada com o texto integral dos alvos e verificar 2 chamadas quando necessário
- [x] 6.4 Contrato de resposta estruturada com parser tolerante e fallback, e verificar formato inválido
- [x] 6.5 Prompt de sistema (responder só pelo contexto, citar fontes, admitir ausência) e verificar conteúdo
- [x] 6.6 Mapear `LLMUnavailableError` da `llm-core` para o estado "Chat desabilitado", e verificar propagação

## 7. Testes de Domínio e Caso de Uso

- [x] 7.1 Testar `ChatMessage`/`ChatSession`
- [x] 7.2 Testar o caso de uso completo com mocks (resposta nos resumos, escalada, sem documentos, LLM indisponível)

## 8. GUI — ChatPanel

- [x] 8.1 `ChatPanel(tkinter.Frame)` parametrizado por ticker (mensagens, scroll, entrada, enviar), e verificar construção
- [x] 8.2 Área de respostas com `ReadonlyText` (cursor, seleção, Ctrl+A/C), e verificar bloqueio de edição
- [x] 8.3 Estado não configurado com entrada desabilitada, orientação e botão "Configurar", e verificar cenário
- [x] 8.4 Botão "Copiar chat" copiando o conteúdo da sessão, e verificar clipboard
- [x] 8.5 Cabeçalho com o ticker foco no Chat Ticker, e verificar atualização ao trocar de ticker
- [x] 8.6 Diálogo de confirmação por quantidade de documentos-alvo, e verificar as três faixas

## 9. GUI — Integração

- [x] 9.1 Sub-aba "Chat Geral" no notebook da Análise Geral, sempre visível, e verificar `ChatPanel(ticker=None)`
- [x] 9.2 Sub-aba "Chat Ticker" no notebook da Análise do Ticker, e verificar filtro pelo ticker
- [x] 9.3 "Configurar" abre `LLMConfigDialog` via `_abrir_config_llm` e reavalia o estado ao salvar, e verificar
- [x] 9.4 `_texto_para_copiar` inclui o chat quando a sub-aba está ativa, e verificar cópia
- [x] 9.5 Erros da LLM na statusbar (via `mensagem_erro_llm`) e no log, e verificar falha simulada

## 10. Testes GUI

- [x] 10.1 Estados do ChatPanel, cópia do chat, cabeçalho do ticker e integração com o diálogo
- [x] 10.2 Cópia de dados CSV com a sub-aba de chat ativa

## 11. Quality Gate

- [x] 11.1 `make lint` e `make complexity` limpos
- [x] 11.2 `pytest -m "not llm"` passa
- [x] 11.3 Testes existentes sem regressão
- [x] 11.4 Executar `openspec validate llm-chat` e garantir que a change permanece válida

## 12. Documentação

- [x] 12.1 Atualize README.md, indicators.md e panels.md com o que foi implementado nessa change.

## 13. Revisão de UX — Aba única "Chat AI"

- [x] 13.1 Mover o chat para uma aba de topo "Chat AI" entre "Análise do Ticker" e "Sobre" e remover as sub-abas "Chat Geral"/"Chat Ticker"
- [x] 13.2 Ajustar `_current_tabs`/`_restore_tabs`, `_resolve_chart` e a restauração de preferências à aba de topo
- [x] 13.3 Adaptar `_texto_para_copiar`, `_sync_copy_button_for_tab` e `_reavaliar_chat_llm` à aba única
- [x] 13.4 Usar o contexto da watchlist completa e fazer a LLM inferir o ticker pela pergunta (prompt e remoção do escopo foco do `ChatPanel`)
- [x] 13.5 Adicionar o botão "Configuração" após "Copiar chat", sempre visível, abrindo o mesmo diálogo da sub-aba Documentos
- [x] 13.6 Atualizar testes de chat, integração, wiring e do estado não configurado
- [x] 13.7 Atualizar panels.md, README.md e indicators.md para a aba única e o botão permanente
- [x] 13.8 `make lint`, `make complexity` e `pytest -m "not llm"` limpos; `openspec validate llm-chat`
- [x] 13.9 Expor ponto de extensão de contexto (`ContextoChat` com fontes adicionais por pergunta) para `noticias-b3` e `llm-chat-rag`, e verificar com fonte de teste e fonte que falha

## 14. Botão "Limpar" do chat

- [x] 14.1 Adicionar o botão "Limpar" antes de "Copiar chat" no cabeçalho do `ChatPanel`, com confirmação (Sim/Não) e reinício da sessão
- [x] 14.2 Atualizar os testes do `ChatPanel` (botão, confirmação e cancelamento)
- [x] 14.3 Atualizar panels.md com o botão "Limpar"
- [x] 14.4 `make lint`, `make complexity` e `pytest -m "not llm"` limpos; `openspec validate llm-chat`

## 15. Botão "Cancelar o envio" do chat

- [x] 15.1 Adicionar ao lado de "Enviar" um botão de cancelamento com o ícone `process-stop.png`, habilitado somente durante o processamento, e verificar com testes de estado
- [x] 15.2 Estender `ConsultarChatUseCase.consultar` com `CancellationToken` opcional e verificar a interrupção antes das chamadas de completion
- [x] 15.3 Implementar o cancelamento cooperativo no `ChatPanel` (token, contador de geração e descarte do desfecho tardio), com restauração imediata dos botões, e verificar com testes
- [x] 15.4 Atualizar panels.md e README.md com o botão de cancelar o envio
- [x] 15.5 `make lint`, `make complexity` e `pytest -m "not llm"` limpos; `openspec validate llm-chat`

## 16. Histórico textual da conversa

- [x] 16.1 Adicionar `enviar_ao_modelo` (bool, padrão `True`) ao `ChatMessage` e cobrir com teste de domínio
- [x] 16.2 Estender `ConsultarChatUseCase.consultar` com `historico: Sequence[ChatMessage]` e enviar os turnos anteriores antes da pergunta atual, com o mesmo histórico nas duas chamadas da cascata
- [x] 16.3 Aplicar o teto de 10 mensagens e 8.000 caracteres ao histórico, descartando os turnos mais antigos
- [x] 16.4 Marcar erros e avisos da LLM com `enviar_ao_modelo=False` e filtrá-los do histórico
- [x] 16.5 Capturar o snapshot da sessão no `ChatPanel`/`EnvioMixin` antes de registrar a pergunta e passá-lo ao caso de uso
- [x] 16.6 Atualizar os testes do caso de uso e do painel (histórico presente/ordenado, ambas as chamadas, teto, erros excluídos, Limpar)
- [x] 16.7 Atualizar panels.md e README.md com o contexto multi-turno
- [x] 16.8 `make lint`, `make complexity` e `pytest -m "not llm"` limpos; `openspec validate llm-chat`

## 17. Estados dos botões e orientação da aba "Chat AI"

- [x] 17.1 Condicionar o botão "Enviar" à existência de fundamentos carregados (`_tem_fundamentos`) e reavaliar o painel no `on_tab_changed` disparado ao final da carga de fundamentos, e verificar com testes de estado
- [x] 17.2 Desabilitar "Limpar", "Copiar chat" e "Configuração" durante o envio e restaurá-los ao término (resposta, erro ou cancelamento), e verificar com testes
- [x] 17.3 Habilitar "Limpar" e "Copiar chat" apenas com conteúdo textual na conversa, desabilitando após "Limpar", e verificar com testes
- [x] 17.4 Adicionar a orientação da aba "Chat AI" em `TAB_CONTENT` e aplicá-la ao quadro textual em `_on_tab_changed`, e verificar no teste de integração
- [x] 17.5 Verificar o acesso da LLM aos caches da sub-aba "Notícias" via `FonteNoticias` (`noticias-b3`), confirmando o registro em `fontes_adicionais` e a leitura dos caches; adicionar teste de wiring
- [x] 17.6 Atualizar panels.md e README.md com os estados dos botões e a orientação da aba
- [x] 17.7 `make lint`, `make complexity` e `pytest -m "not llm"` limpos; `openspec validate llm-chat`

## 18. Orientação da aba "Sobre"

- [x] 18.1 Adicionar a orientação da aba "Sobre" em `TAB_CONTENT` (chave `(ABOUT_TAB, ABOUT_TAB)`)
- [x] 18.2 Aplicar a orientação ao quadro textual em `_on_tab_changed` quando a aba "Sobre" está ativa, e verificar com testes
- [x] 18.3 Atualizar panels.md e README.md
- [x] 18.4 `make lint`, `make complexity` e `pytest -m "not llm"` limpos; `openspec validate llm-chat`
