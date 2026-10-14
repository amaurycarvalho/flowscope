## Why

A navegação da árvore de conhecimento (`listar`, `obter`, `contar`, `existe`, `buscar`, `buscar_semantico`) hoje só existe dentro do chat: o `ProtocoloNavegacao` valida, executa e serializa, mas não há uma superfície reutilizável para clientes externos (chats e modelos via MCP) nem para automações via CLI. Sem um núcleo único, cada superfície reimplementaria schemas, limites, paginação, erros e confinamento de leitura, abrindo espaço para divergências (RFC-016).

## What Changes

- **Novo núcleo de navegação compartilhado** (`NavegacaoCore`) que concentra as operações canônicas, os limites, a paginação, os erros estruturados e o confinamento de leitura ao cache local. O chat passa a consumi-lo por um adaptador local (`ProtocoloNavegacao` → `NavegacaoCore`), sem MCP e sem mudança de comportamento observável pelo usuário.
- **Servidor MCP embutido** iniciado por `flowscope --mcp`, com transporte **stdio** apenas e implementação JSON-RPC própria (sem dependência nova), alvo da revisão moderna **`2026-07-28`** (sem handshake `initialize`; `server/discover` obrigatório).
- **Tools MCP canônicas** `nav_listar`, `nav_obter`, `nav_contar`, `nav_existe`, `nav_buscar`, `nav_buscar_semantico` e `nav_manifesto`, em ordem alfabética determinística, com `title` e as anotações `readOnlyHint`, `destructiveHint`, `idempotentHint` e `openWorldHint`.
- **Comandos CLI** `flowscope nav <operacao> ...` reusando o mesmo núcleo, com saída JSON (e `--pretty` opcional para humanos).
- **Paginação padronizada (Opção B)**: as tools de listagem (`nav_listar`, `nav_buscar`, `nav_buscar_semantico`) devolvem `nextCursor` opaco (base64url de `{v, op, caminho, pos}`) apenas quando há mais resultados; `nav_obter` mantém `offset`/`limite` explícitos por caractere. A ordem passa a ser determinística por caminho.
- **Documentação**: atualização do `README.md` (novos parâmetros e link para o guia) e novo guia em `docs/misc/`.

**Fora de escopo (não faz parte desta mudança):**

- `nav_resetar` (o reset de navegação permanece uma preocupação do loop do chat, não do núcleo).
- `nav_batch` (execução em lote).
- Transporte Streamable HTTP e suporte dual-era (handshake `initialize` legado).
- Dependência de SDK MCP externo.
- RAG vetorial (a busca semântica continua com fallback `indice_indisponivel`; a indexação é a change `llm-chat-rag`).

## Capabilities

### New Capabilities

- `navegacao-core`: núcleo de navegação compartilhado — operações canônicas, validação, limites (50 resultados de busca, 200 caracteres por trecho, 12.000 caracteres por página de `obter`, timeout de regex, teto de manifesto), paginação com cursor opaco, erros estruturados recuperáveis, ordenação determinística e confinamento de leitura ao cache local.
- `mcp-server`: servidor MCP embutido (`flowscope --mcp`) — transporte stdio, revisão de protocolo `2026-07-28`, `server/discover`, catálogo de tools `nav_*` com schemas e anotações, `tools/call`, envelopes de paginação e erro, logs em `stderr`.

### Modified Capabilities

- `cli-interface`: novos subcomandos `flowscope nav listar|obter|contar|existe|buscar|buscar-semantico|manifesto` com saída JSON e `--pretty`, reusando o `NavegacaoCore`.

## Impact

- **Código**: `src/flowscope/application/chat/arvore.py` e `protocolo.py` (extração do núcleo e adaptador), novo módulo de núcleo de navegação e novo servidor MCP (camada de apresentação), `src/flowscope/presentation/cli.py` e `main.py` (subcomandos `nav` e flag `--mcp`), `README.md` e `docs/misc/mcp.md`.
- **Contratos**: `ProtocoloNavegacao` passa a delegar ao `NavegacaoCore`; a interface MCP e os subcomandos CLI são novos contratos externos.
- **Dependências**: nenhuma nova dependência de runtime (servidor JSON-RPC em stdlib). O `flowscope.spec` (PyInstaller) não requer novos hidden imports; conferir o ponto de entrada `--mcp` no empacotamento.
- **Compatibilidade**: sem quebra para o chat/GUI; os formatos legados de `obter` são preservados.
