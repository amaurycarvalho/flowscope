## Why

O conteúdo que o chat obtém dos documentos chega incompleto: os resumos são cortados no meio da palavra (`short_summary` em 280 e `long_summary` em 1500 caracteres, com `curto[:280]`/`longo[:1500]` em `resumo_documento.py`) e o texto integral é truncado em 12.000 caracteres (`TETO_DOCUMENTO`). Num RG de ~37.000 caracteres o modelo só acessa cerca de um terço, então respostas sobre "o que mais há de relevante" ou sobre os resumos curto/longo saem truncadas e pouco assertivas.

## What Changes

- O resumo de documento passa a cortar em **fronteira de frase/palavra** (nunca no meio da palavra) e o prompt pede os resumos por **frases/parágrafos**, mantendo os tetos como salvaguarda.
- Os resumos já em cache que terminam no meio da palavra DEVEM poder ser **regenerados** pelo lote "Resumir pendentes", sem exigir limpeza manual.
- A operação `obter` passa a aceitar `offset`/`limite` (leitura **paginada**) para o texto integral, e o manifesto/playbook orientam a leitura em partes quando o texto for longo.

## Capabilities

### New Capabilities
<!-- Nenhuma capability nova. -->

### Modified Capabilities
- `documento-summary`: o truncamento passa a ser em fronteira de frase/palavra e o prompt solicita os resumos por frases/parágrafos; resumos armazenados truncados são regeneráveis.
- `llm-chat-tree`: a operação `obter` aceita `offset`/`limite` para leitura paginada do texto integral, com o manifesto/protocolo orientando a paginação.

## Impact

- **Aplicação**: `application/resumo_documento.py` (truncamento em fronteira e prompt), `application/chat/documentos.py` (texto paginado por página), `application/chat/protocolo.py` (`obter` com `offset`/`limite`), `application/chat/manifesto.py` e `application/chat/consultar.py` (orientação de paginação).
- **Apresentação**: `presentation/gui/*` do lote de resumos, para regerar os resumos truncados.
- **Testes**: `tests/test_application/test_resumo_documento.py` (ou equivalente), `test_chat_documentos.py`, `test_chat_protocolo.py`, `test_chat_manifesto.py`.
- Sem dependências novas. Convive com `chat-navegacao-granular` (mesma capability `llm-chat-tree`); convém arquivá-la antes.
