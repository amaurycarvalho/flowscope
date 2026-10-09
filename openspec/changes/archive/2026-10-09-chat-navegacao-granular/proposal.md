## Why

Perguntas encadeadas sobre um mesmo ativo e documento (evolução do guidance, "o RG mais recente", "o que mais há nesse RG?", "qual o período desse último RG?") não são respondidas por navegação confiável: `/documentos/<ticker>` colapsa todos os documentos em três folhas agregadas (`curto`/`longo`/`texto`), o `texto` é um blob do ticker truncado por orçamento (o documento-alvo pode ficar de fora) e período/categoria não existem como dados navegáveis. Sem índice por item, sem foco entre turnos e sem orientação de intenção, a LLM não identifica o alvo, não abre o texto integral do documento e não resolve anáforas.

## What Changes

- `/documentos/<ticker>` passa a expor `/documentos/<ticker>/indice` (uma linha por documento, mais recente primeiro) e um nó interno por documento (`/documentos/<ticker>/<chave>`) com folhas `curto`, `longo` e `texto` do próprio documento, além de metadados estruturados e pesquisáveis (categoria, período, nome).
- `/guidance/<ticker>` passa a expor `/guidance/<ticker>/indice`, agregando os guidances por mês com o rótulo do Relatório Gerencial associado.
- O bloco de resultado da navegação passa a devolver um `foco` (último caminho obtido) para resolver referências como "nesse RG"/"esse último".
- O manifesto passa a anunciar `/flowscope/abas/<aba>` e a lista de sub-abas, e deixa de incluir metadados longos (teto por metadado).
- O protocolo/manifesto ganham um playbook de intenção→ramo e a regra de preferir o `texto` integral do documento-alvo a resumos agregados quando a pergunta pede detalhe.

## Capabilities

### New Capabilities
<!-- Nenhuma capability nova. -->

### Modified Capabilities
- `llm-chat-tree`: granularidade por documento e índice em `/documentos`; índice em `/guidance`; foco de referência entre turnos; playbook de navegação por intenção; manifesto com abas/sub-abas e teto de metadados.
- `llm-chat-context`: o conhecimento do próprio FlowScope passa a expor o nó de aba (`/flowscope/abas/<aba>`) e as sub-abas de forma descobrível por navegação, sem conteúdo pesado no manifesto.

## Impact

- **Aplicação**: `application/chat/documentos.py` (índice e nó por documento), `application/chat/guidance.py` (índice), `application/chat/arvore.py` e `application/chat/protocolo.py` (foco), `application/chat/consultar.py` (playbook), `application/chat/manifesto.py` (abas/sub-abas, teto de metadados, playbook).
- **Testes**: `tests/test_application/test_chat_documentos.py`, `test_chat_guidance.py`, `test_chat_arvore.py`, `test_chat_protocolo.py`, `test_chat_consulta.py`, `test_chat_manifesto.py`.
- Sem mudança de formato de cache, dependências ou persistência. Convive com as changes pendentes `chat-navegacao-robusta` e `documentos-arvore-ramos` (mesmas capabilities); as deltas desta change pressupõem aquelas já refletidas nos specs principais, então devem ser arquivadas antes.
