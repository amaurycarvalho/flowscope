## Context

Ver `proposal.md` para a motivação. Estado atual relevante:

- `src/flowscope/application/chat/arvore.py` — estrutura `ArvoreConhecimento` com índice de caminhos em memória, `listar`, `obter` (paginação por `offset`/`limite` via `_paginar`), `contar`, `existe`, `buscar`, `buscar_semantico`. Mantém `MAX_RESULTADOS = 50`, `TAMANHO_TRECHO = 200` e `LIMITE_PAGINA_PADRAO = 12000`.
- `src/flowscope/application/chat/protocolo.py` — `ProtocoloNavegacao` valida (`OPERACOES`, `CAMPOS_OBRIGATORIOS`, `MAX_OPERACOES = 8`), despacha e serializa; é instanciado dentro de `ConsultarChatUseCase` (`consultar.py`) e não é uma porta abstrata.
- `src/flowscope/application/chat/manifesto.py` — `montar_manifesto` determinístico com teto `TETO_TOKENS = 4000`.
- `src/flowscope/presentation/cli.py` e `main.py` — `argparse` plano (sem subcomandos), dispatch das flags atuais.
- Sem dependência `mcp` no `pyproject.toml`; `flowscope.spec` (PyInstaller) coleta hidden imports do litellm/tiktoken.
- Restrições do projeto: specs em português com "DEVE"; specs `layer-boundaries` e `engineering-standards`; quality gate com cobertura e complexidade.

Revisão MCP confirmada como atual em `2026-07-28` (sem handshake `initialize`; `server/discover` obrigatório; metadados por requisição em `_meta`).

## Goals / Non-Goals

**Goals:**

- Um único executor de navegação reusado por chat, CLI e MCP.
- Servidor MCP stdio embutido, sem dependência nova, alvo `2026-07-28`.
- Subcomandos `flowscope nav ...` com saída JSON.
- Paginação Opção B: cursor opaco nas listagens, `offset`/`limite` em `obter`.

**Non-Goals:**

- Reset de navegação e execução em lote no núcleo/superfícies externas.
- Streamable HTTP, suporte dual-era (`initialize` legado) e SDK MCP.
- RAG vetorial (tratada em `llm-chat-rag`).
- MCP `resources`/`prompts` (apenas `tools` em v1).

## Decisions

### 1. Extrair `NavegacaoCore` na camada de aplicação e manter `ProtocoloNavegacao` como adaptador

Criar um núcleo de aplicação (`src/flowscope/application/navegacao/core.py`) que encapsula validação, despacho e erros sobre a `ArvoreConhecimento`. `ProtocoloNavegacao` passa a ser um adaptador fino que delega ao núcleo e mantém a serialização do bloco do chat. A CLI e o servidor MCP dependem diretamente do núcleo.

- **Por quê**: evita duplicação e mantém o chat sem MCP.
- **Alternativas**: (a) manter navegação interna e criar wrappers por superfície — rejeitada por duplicar schemas/limites; (b) chat consumindo MCP externo — rejeitada por custo operacional (RFC-016, opção C).
- **Localização**: núcleo em `application/` (regra `layer-boundaries`); servidor MCP em `presentation/`.

### 2. Ordenação determinística por caminho

Listagens passam a ordenar por caminho canônico antes de paginar. Hoje `listar` devolve a ordem de inserção dos filhos (`no.filhos`).

- **Por quê**: cursor pressupõe ordem estável.
- **Impacto/assunção**: a ordem de `listar` do chat passa a ser ordenada (antes, inserção). Nenhum requisito atual fixa a ordem de filhos; a mudança é considerada aditiva/benéfica, coberta por teste. Não se cria delta em `llm-chat-tree`.

### 3. Cursor opaco autocontido (Opção B)

Cursor = `base64url(json({"v": 1, "op": <tool>, "caminho": <caminho>, "pos": <int>}))`. Sem estado de sessão; versionado; vinculado a operação e caminho. `nextCursor` só quando há mais; `obter` permanece com `offset`/`limite`.

- **Por quê**: funciona em stdio e sem sessão; resiste a reuso indevido entre tools/caminhos.
- **Alternativas**: A (cursor também em `obter`) quebraria o contrato atual e a leitura sequencial por caractere; C (sem cursor) deixa clientes MCP sem continuação de listagem.
- **Erros**: cursor malformado/versão desconhecida/operação-caminho divergente → `cursor_invalido` (recuperável).
- **Limites**: `listar` página 100; `buscar` 50; `buscar_semantico` 20.

### 4. Servidor MCP em JSON-RPC próprio sobre stdio, alvo `2026-07-28`

Implementar um servidor mínimo em `presentation/` que fala JSON-RPC 2.0 newline-delimited em `stdin`/`stdout`, implementa `server/discover`, `tools/list`, `tools/call` e `ping`, trata `notifications/cancelled`, valida a versão de protocolo por `_meta` e responde `UnsupportedProtocolVersionError` quando necessário.

- **Por quê**: sem dependência nova; binários offline preservados; superfície pequena e testável.
- **Alternativas**: SDK `mcp` (dependência nova, impacto em `pyproject.toml` e `flowscope.spec`) — adiada; Streamable HTTP — adiado.
- **Integridade do canal**: `stdout` só com JSON-RPC; logs em `stderr`. Teste dedicado garante que nenhuma linha não-JSON-RPC vaze para `stdout`.

### 5. Tools `nav_*` e `nav_manifesto` como tool em v1

Nomes `snake_case` com prefixo de domínio `nav_`, ordem alfabética determinística e anotações completas. O manifesto é exposto como tool `nav_manifesto` (não como MCP resource/prompt) em v1.

- **Por quê**: um único primitivo (`tools`) simplifica o servidor; `resources`/`prompts` não são necessários para o caso de uso.

### 6. Rejeição de traversal em `normalizar_caminho`

`normalizar_caminho` (em `arvore.py`) passa a recusar segmentos `.` e `..`, devolvendo `caminho_invalido`.

- **Por quê**: os caminhos são lógicos, não de filesystem, mas a RFC pede confinamento explícito; barato e defensivo.

### 7. CLI por subparsers e flag `--mcp`

Adicionar subcomandos `nav` via `argparse` subparsers, preservando as flags atuais como comportamento padrão. Adicionar a flag `--mcp` como ponto de entrada alternativo do servidor.

- **Por quê**: subcomandos evitam ambiguidade com as flags existentes; `--mcp` é um modo de execução distinto.

### 8. Documentação

Atualizar `README.md` (parâmetros `--mcp` e `flowscope nav ...` nas duas seções "Como Usar" e link em "Saiba Mais") e criar `docs/misc/mcp.md` no padrão dos guias existentes (`docs/misc/*.md`).

## Risks / Trade-offs

- **Ordem de `listar` do chat muda** → teste de regressão e nota no design; nenhum requisito fixa a ordem atual.
- **Deriva de cursor sob mutação do cache** → documentado como melhor esforço; cliente refaz a operação para nova visão.
- **`stdout` poluído quebra o cliente MCP** → logging estritamente em `stderr` e teste de canal.
- **Churn da revisão MCP** → isolar o servidor em módulo próprio e pinar `2026-07-28` nos testes; mudanças futuras ficam contidas.
- **Duplicação de contrato entre `navegacao-core` e `llm-chat-tree`** → `llm-chat-tree` mantém o foco no protocolo voltado à LLM; o núcleo cobre a superfície compartilhada.
- **Revisão de complexidade/cobertura do quality gate** → núcleo e servidor com testes de contrato; complexidade mantida por despacho tabular.

## Migration Plan

1. Extrair o núcleo e adaptar `ProtocoloNavegacao`, mantendo a suíte do chat verde.
2. Introduzir ordenação determinística e cursor no núcleo, com testes de contrato.
3. Adicionar subcomandos `nav` na CLI reusando o núcleo.
4. Adicionar o servidor MCP stdio (`--mcp`) e testes de protocolo (discover, tools/list, tools/call, erros).
5. Atualizar `README.md` e criar `docs/misc/mcp.md`.
6. Rollback: reverter os módulos novos e o adaptador; a árvore permanece utilizável pelo chat.

## Open Questions

- Suporte MCP dual-era (`initialize`) para clientes legados — pode ser adicionado depois sem alterar specs.
- Expor o manifesto como MCP `resource`/`prompt` em vez de tool — decisão futura.
- Transporte Streamable HTTP — fora de escopo, reavaliar sob demanda.
