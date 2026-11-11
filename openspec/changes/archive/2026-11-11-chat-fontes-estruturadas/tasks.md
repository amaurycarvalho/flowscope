# Tasks

## 1. Domínio e protocolo

- [x] 1.1 Criar `FonteChat` (caminho obrigatório, rótulo opcional) em `domain/chat/models.py` e trocar `ChatMessage.sources` para `list[FonteChat]`; verificar com os testes de `tests/test_domain/test_chat/test_models.py`.
- [x] 1.2 Trocar `RespostaChat.fontes` para `list[FonteChat]` e adicionar `fontes` a `RespostaProtocolo`, com parse tolerante em `protocolo.py` (string ou objeto, `rotulo` opcional, itens inválidos descartados, turno intermediário ignorado); verificar com testes em `tests/test_application/test_chat_protocolo.py`.
- [x] 1.3 Atualizar os testes existentes de domínio e protocolo para a fonte estruturada e o novo campo; executar `pytest tests/test_domain/test_chat tests/test_application/test_chat_protocolo.py` e confirmar que passam.

## 2. Derivação e merge das fontes

- [x] 2.1 Reescrever a extração de fontes em `consultar.py` por operação (`obter` pelo caminho do resultado, `listar` pelos itens, `buscar`/`buscar_semantico` pelos `resultados`), deduplicando com ordem estável e excluindo resultados com erro; verificar com testes em `tests/test_application/test_chat_consulta.py` cobrindo cada operação.
- [x] 2.2 Adicionar `ProtocoloNavegacao.existe(caminho)` e o merge em `_resposta_final`: normalizar e validar cada caminho declarado, rotular os derivados, incluir declarados válidos não derivados, descartar e logar inexistentes, deduplicar e aplicar teto defensivo de entradas; verificar com testes de merge em `tests/test_application/test_chat_consulta.py`.
- [x] 2.3 Garantir fallback sem declaradas (resposta final sem `fontes`, texto puro e `_resumo_final`) e sem fontes derivadas; verificar com testes de fallback em `tests/test_application/test_chat_consulta.py`.

## 3. Prompt e contrato entre agentes

- [x] 3.1 Atualizar `SYSTEM_PROMPT` e `INSTRUCAO_FORMATO` em `consultar.py`: remover a orientação de citar fontes no corpo e exigir a declaração em `fontes`; verificar com testes de `tests/test_application/test_chat_consulta.py` (classe `TestPromptSistema`).
- [x] 3.2 Atualizar `PERSONA` e `PROTOCOLO` em `manifesto.py` com a mesma orientação e o esquema de resposta com `fontes`; verificar com testes de `tests/test_application/test_chat_manifesto.py`.
- [x] 3.3 Adicionar teste de contrato que assegura, nos dois pontos do prompt, a proibição de citação no corpo e a presença do campo `fontes`; executar `pytest tests/test_application/test_chat_consulta.py tests/test_application/test_chat_manifesto.py`.

## 4. Interface do chat

- [x] 4.1 Adicionar `BooleanVar` e `ttk.Checkbutton` "Exibir fontes" no cabeçalho, desmarcado por padrão e disponível durante o envio; verificar com teste em `tests/test_presentation/test_chat_panel.py`.
- [x] 4.2 Extrair o renderizador de bloco e a reconstrução da área de mensagens a partir da sessão, exibindo as fontes em bloco separado quando o checkbox estiver marcado; verificar com testes de `tests/test_presentation/test_chat_panel.py` (estado inicial, marcar/desmarcar todas as respostas, separação, resposta sem fontes).
- [x] 4.3 Garantir que "Copiar chat" e a cópia de CSV usam o conteúdo renderizado e seguem o checkbox; verificar com testes em `tests/test_presentation/test_chat_panel.py` e, se necessário, `tests/test_presentation/test_chat_integration.py`.
- [x] 4.4 Ajustar os stubs de host/orquestração ao novo formato de fontes; verificar com `pytest tests/test_presentation/test_chat_orquestracao.py tests/test_presentation/test_chat_envio.py`.

## 5. Documentação e orientação da aba

- [x] 5.1 Atualizar `docs/misc/panels.md` (contrato `fontes`, checkbox "Exibir fontes", comportamento da cópia) e conferir por leitura que a seção do Chat AI reflete o novo comportamento.
- [x] 5.2 Atualizar a orientação do Chat AI em `TAB_CONTENT` (`presentation/gui/app_tabs.py`) descrevendo a declaração estruturada das fontes e o checkbox; verificar por leitura e com o teste de conhecimento que consome o `TAB_CONTENT`, se existir.

## 6. Verificação integrada

- [x] 6.1 Executar `make lint` e confirmar que não há erros.
- [x] 6.2 Executar `make complexity` e confirmar que os limites são respeitados.
- [x] 6.3 Executar os testes impactados (`pytest tests/test_domain/test_chat tests/test_application/test_chat_consulta.py tests/test_application/test_chat_protocolo.py tests/test_application/test_chat_manifesto.py tests/test_presentation/test_chat_panel.py tests/test_presentation/test_chat_orquestracao.py tests/test_presentation/test_chat_envio.py`) e confirmar que passam.

## 7. Marcações em negrito e cópia em Markdown

- [x] 7.1 Trocar o cabeçalho do bloco de fontes para `\n\nFontes consultadas:\n` e atualizar os testes de renderização.
- [x] 7.2 Renderizar `Você:`, `Assistente:` e `Fontes consultadas:` em negrito via tag Tk e cobrir com testes.
- [x] 7.3 Copiar chat convertendo as marcações em negrito para Markdown, mantendo o CSV em texto simples; cobrir com testes.
- [x] 7.4 Atualizar `docs/misc/panels.md` e a orientação do `TAB_CONTENT`; executar `make lint`, `make complexity` e os testes impactados.
- [x] 7.5 Inserir uma linha em branco antes de `Fontes consultadas:` e atualizar testes, design, proposta e spec.

## 8. Uso não criptográfico de SHA1

- [x] 8.1 Aplicar `usedforsecurity=False` nos sete usos de SHA1 de chaves e identificadores determinísticos, sem alterar os valores gerados.
- [x] 8.2 Executar os testes impactados de notícias, documentos, guidance e renda fixa.
- [x] 8.3 Executar `make lint`, `make complexity` e `make security` e confirmar o resultado.

## Workflow follow-up

- Arquivar a change após a revisão do projeto.
- Executar a suíte completa (`make test`) e o quality gate (`make quality-gate`) apenas se o usuário autorizar explicitamente; por precaução, ficam como passo manual do usuário.
