# RFC-016: Navegação FlowScope como Tools MCP para integração externa e CLI

**Status:** Draft
**Escopo:** `ConsultarChatUseCase`, `ProtocoloNavegacao`, `NavegacaoCore`, servidor MCP `flowscope --mcp`, CLI `flowscope nav ...`
**Relacionados:** `src/flowscope/application/chat/consultar.py`, `protocolo.py`, `manifesto.py`; especificação MCP (2026-07-28).

---

## Problem

O mecanismo de navegação da aba Chat (`listar`, `obter`, `contar`, `existe`, `buscar`, `buscar_semantico`, `resetar_navegacao`) é interno ao `ConsultarChatUseCase` e ao `ProtocoloNavegacao`. Ele não é exposto como serviço reutilizável para:

- chats e modelos externos via MCP;
- automações via CLI;
- testes de contrato independentes do chat interno;
- outros consumidores internos do FlowScope.

Se cada superfície criar wrappers próprios, teremos duplicação de schemas, limites, erros, confinamento de leitura e orçamentos. O chat interno deve continuar acessando o protocolo diretamente, sem MCP. O servidor MCP deve apenas compartilhar os mesmos serviços de navegação para uso externo explícito, seguindo o padrão canônico MCP para que qualquer cliente consiga navegar sem fricção.

---

## Root cause

A causa raiz é a ausência de uma **superfície canônica de navegação** com um núcleo único.

Hoje:

1. `ProtocoloNavegacao` é uma porta interna usada apenas pelo chat.
2. O servidor MCP não expõe as operações de navegação como tools de primeira classe.
3. O chat não deve consumir MCP; ele continua chamando o protocolo diretamente.
4. Limites como 8 operações/turno, 12.000 caracteres por página, 50 resultados de busca, timeout de regex e confinamento de leitura ficam dispersos.
5. Erros estruturados (`caminho_invalido`, `indice_indisponivel`, `limite_operacoes`) não são compartilhados entre chat, MCP e CLI.

Sem um núcleo comum e uma exposição MCP padronizada, qualquer integração externa vira uma segunda implementação.

---

## Options

### A. Manter navegação interna e criar apenas wrappers CLI

- **Prós:** menor esforço inicial.
- **Contras:** duplica schemas e limites; MCP continua sem navegação; chat e CLI divergem.

### B. Expor navegação via MCP apenas para clientes externos

- **Prós:** chat não muda; clientes externos ganham acesso.
- **Contras:** duas implementações (interna e MCP); bugs de paridade; confinamento de leitura pode não ser aplicado ao chat.

### C. Fazer o chat consumir obrigatoriamente um servidor MCP externo

- **Prós:** superfície única; paridade real.
- **Contras:** adiciona processo, lifecycle, latência, tratamento de EOF e complexidade operacional para um caso que roda in-process.
- **Decisão:** rejeitada. O chat interno continua direto no protocolo, sem MCP.

### D. Núcleo dispatcher comum + tools MCP canônicas + CLI

- **Prós:** uma única implementação das operações; chat usa adapter local direto; MCP expõe `nav_*` como tools canônicas; CLI usa o mesmo núcleo; testes de contrato únicos.
- **Contras:** exige refatoração inicial do `ProtocoloNavegacao` e criação do catálogo de tools.
- **Recomendada.**

---

## Better solution

Adotar a opção D: criar um **núcleo de navegação** (`NavegacaoCore`) com dispatcher único, expô-lo como **tools MCP canônicas** e como comandos CLI, e manter o chat interno consumindo o `ProtocoloNavegacao` diretamente por um adaptador local. O MCP não participa do chat interno.

### 1. Núcleo compartilhado

Criar `NavegacaoCore`, que implementa as operações canônicas e aplica:

- confinamento de leitura ao cache local padrão do FlowScope;
- paginação com cursor opaco para listagens e conteúdo pesado;
- 50 resultados e 200 caracteres por trecho em `buscar`;
- timeout de regex de 100 ms;
- `buscar_semantico` com fallback `indice_indisponivel`;
- máximo de 8 operações por lote/turno;
- caminhos canônicos e rejeição de traversal;
- manifesto determinístico com teto de 4.000 tokens.

Fluxo de dependências:

```text
Chat interno ──> ProtocoloNavegacao ──> NavegacaoCore
CLI nav ─────────────────────────────> NavegacaoCore
Servidor MCP ────────────────────────> NavegacaoCore
Chats/modelos externos ──> MCP ──────> NavegacaoCore
```

O chat interno **não** inicia, não consulta e não depende do servidor MCP.

### 2. Chat interno continua direto

O `ConsultarChatUseCase` permanece com o loop de até 10 ciclos, histórico, navegação acumulada e bloco `[RESULTADO_NAVEGACAO]`. A dependência continua sendo:

```text
ConsultarChatUseCase(protocolo: ProtocoloNavegacao)
```

A implementação padrão passa a ser um adapter local sobre `NavegacaoCore`:

```text
ProtocoloNavegacaoLocal -> NavegacaoCore
```

Não haverá configuração `chat.navegacao.transporte = mcp`. O chat sempre usa o protocolo diretamente.

O chat continua responsável por:

- montar o prefixo estável com persona + formato + manifesto;
- limitar 10 ciclos, 8 operações/turno, 64.000 tokens/turno e 32.000 tokens acumulados;
- decidir quando a resposta é final;
- aplicar `resetar_navegacao` no estado do diálogo.

O `NavegacaoCore` apenas executa operações e devolve resultados determinísticos.

### 3. Tools MCP canônicas

O servidor MCP expõe cada operação como uma **tool independente**, descoberta via `tools/list` e invocada via `tools/call`, seguindo o padrão de mercado:

- **Nomes:** `snake_case` com padrão `<ação>_<recurso>`, sem prefixo de produto. O agente distingue tools pelo nome do servidor MCP.
- **Ordem determinística:** `tools/list` retorna as tools em ordem alfabética estável para permitir cache do cliente e cache de prompt do LLM.
- **Anotações:** cada tool carrega `title`, `readOnlyHint`, `destructiveHint`, `idempotentHint` e `openWorldHint`.

| Operação interna    | Tool MCP               | `readOnlyHint` | `destructiveHint` | `idempotentHint` | `openWorldHint` |
| ------------------- | ---------------------- | -------------- | ----------------- | ---------------- | --------------- |
| `listar`            | `nav_listar`           | true           | false             | true             | false           |
| `obter`             | `nav_obter`            | true           | false             | true             | false           |
| `contar`            | `nav_contar`           | true           | false             | true             | false           |
| `existe`            | `nav_existe`           | true           | false             | true             | false           |
| `buscar`            | `nav_buscar`           | true           | false             | true             | false           |
| `buscar_semantico`  | `nav_buscar_semantico` | true           | false             | true             | false           |
| `resetar_navegacao` | `nav_resetar`          | false          | true              | true             | false           |
| manifesto           | `nav_manifesto`        | true           | false             | true             | false           |
| batch               | `nav_batch`            | false          | false             | false            | false           |

**Observações sobre anotações:**

- `nav_resetar` descarta o foco/navegação de sessão. Não modifica dados persistentes, mas altera estado. `destructiveHint: true` sinaliza que a operação descarta estado; `idempotentHint: true` indica que repetir tem o mesmo efeito.
- `nav_batch` não é idempotente em geral, pois pode conter operações que alteram sessão (como `nav_resetar`), e `readOnlyHint: false` porque pode executar operações não-leitura.

### 4. Schemas de entrada

**`nav_listar`**

```json
{
  "type": "object",
  "properties": {
    "caminho": { "type": "string", "description": "Caminho canônico do nó." }
  },
  "required": ["caminho"]
}
```

**`nav_obter`** — com paginação explícita:

```json
{
  "type": "object",
  "properties": {
    "caminho": { "type": "string" },
    "offset": { "type": "integer", "minimum": 0, "default": 0 },
    "limite": {
      "type": "integer",
      "minimum": 1,
      "maximum": 12000,
      "default": 12000
    }
  },
  "required": ["caminho"]
}
```

**`nav_contar`**

```json
{
  "type": "object",
  "properties": {
    "caminho": { "type": "string" }
  },
  "required": ["caminho"]
}
```

**`nav_existe`**

```json
{
  "type": "object",
  "properties": {
    "caminho": { "type": "string" }
  },
  "required": ["caminho"]
}
```

**`nav_buscar`**

```json
{
  "type": "object",
  "properties": {
    "caminho": { "type": "string" },
    "regex": { "type": "string" },
    "em": { "type": "array", "items": { "type": "string" } },
    "max": { "type": "integer", "minimum": 1, "maximum": 50, "default": 50 }
  },
  "required": ["caminho", "regex"]
}
```

**`nav_buscar_semantico`**

```json
{
  "type": "object",
  "properties": {
    "caminho": { "type": "string" },
    "consulta": { "type": "string" },
    "max": { "type": "integer", "minimum": 1, "maximum": 20, "default": 10 }
  },
  "required": ["caminho", "consulta"]
}
```

**`nav_resetar`**

```json
{
  "type": "object",
  "properties": {}
}
```

**`nav_manifesto`**

```json
{
  "type": "object",
  "properties": {}
}
```

**`nav_batch`**

```json
{
  "type": "object",
  "properties": {
    "steps": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "params": { "type": "object" }
        },
        "required": ["id"]
      }
    },
    "stop_on_error": { "type": "boolean", "default": true }
  },
  "required": ["steps"]
}
```

### 5. Paginação padronizada

Toda tool que retorna lista devolve o envelope MCP:

```json
{
  "items": [...],
  "nextCursor": "eyJwYWdlIjogM30="
}
```

O cursor é um **token opaco**: o cliente não interpreta, apenas o devolve na próxima chamada. A ausência de `nextCursor` significa fim dos resultados.

**Argumento de continuação:** as tools que suportam paginação (`nav_listar`, `nav_buscar`, `nav_buscar_semantico`) aceitam um argumento `cursor` (string opcional) para buscar a próxima página.

**`nav_obter`:** mantém `offset`/`limite` explícitos para o texto integral, porque o conteúdo pesado é paginado por caractere. O resultado inclui `total`, `offset`, `limite`, `continua` e, quando aplicável, `nextCursor` para o próximo bloco.

### 6. Resultados e erros

**Resultados de sucesso:** JSON estruturado no formato MCP, com o campo `result` contendo os dados.

**Erros de domínio recuperáveis** (`caminho_invalido`, `indice_indisponivel`, `limite_operacoes`): retornam JSON estruturado com `erro.motivo`, `erro.detalhe` e `erro.dica`, sem `isError: true`. Exemplo:

```json
{
  "erro": {
    "motivo": "caminho_invalido",
    "detalhe": "Caminho não encontrado na árvore.",
    "dica": "use existe(caminho) ou listar(...)"
  }
}
```

**Falhas internas e panics escapados:** retornam `isError: true` e o servidor continua servindo.

### 7. Transporte MCP

O servidor MCP usa o transporte padrão MCP, com suporte a **stdio** e **Streamable HTTP**.

**stdio:** o cliente lança o servidor como subprocesso. O servidor lê JSON-RPC de `stdin` e escreve em `stdout`, com mensagens delimitadas por newline. Logs vão para `stderr`. O servidor **não** escreve nada em `stdout` que não seja uma mensagem MCP válida.

**Streamable HTTP:** o servidor expõe um único endpoint que aceita POST. Cada mensagem JSON-RPC é um POST independente; a resposta pode ser um JSON único ou um stream SSE escopado à requisição.

**Startup:** o servidor é iniciado explicitamente com:

```text
flowscope --mcp
```

Sem `--root` e sem `--compact`. A árvore é lida sempre do cache local padrão do FlowScope. O servidor para em EOF no modo stdio.

### 8. Exposição via CLI

Além do servidor MCP, expor comandos diretos para uso humano:

```bash
flowscope nav listar /noticias/grupos
flowscope nav obter /documentos/PETR4/<chave>/texto --offset 0 --limite 12000
flowscope nav contar /documentos/PETR4/*
flowscope nav existe /guidance/PETR4
flowscope nav buscar /documentos/PETR4 --regex "..." --em titulo,texto --max 50
flowscope nav buscar-semantico /documentos/PETR4 --consulta "..." --max 10
flowscope nav resetar
flowscope nav manifesto
flowscope nav batch ops.json
```

A CLI usa o mesmo `NavegacaoCore`. Saída padrão em JSON; `--pretty` opcional para humano.

### 9. Segurança e observabilidade

- Confinamento de leitura ao cache local padrão do FlowScope.
- Nenhuma consulta à B3/CVM, download ou extração.
- Nós sem dado são omitidos em silêncio.
- Logs sempre em `stderr` no modo MCP.
- Status bar do chat mantém contadores de entrada/saída, cache, contexto e `nav: X/32K`.
- Métricas sugeridas: chamadas `nav_*`, latência, erros por motivo, uso de `buscar_semantico`, cache hit do prefixo.

### 10. Orçamentos e limites (inalterados)

| Limite                              | Valor                                                  |
| ----------------------------------- | ------------------------------------------------------ |
| Manifesto                           | 4.000 tokens (degrada para "só chaves"; depois trunca) |
| Histórico de diálogo                | 10 mensagens / 8.000 caracteres                        |
| Ciclos do loop                      | 10                                                     |
| Operações por turno                 | 8                                                      |
| Teto de navegação por turno         | 64.000 tokens                                          |
| Cota de navegação acumulada         | 32.000 tokens                                          |
| Página de conteúdo pesado (`obter`) | 12.000 caracteres                                      |
| Trecho por resultado de `buscar`    | 200 caracteres                                         |
| Resultados de `buscar`              | 50                                                     |
| Timeout de regex                    | 100 ms                                                 |

---

## Evaluate

**Prós**

- Uma única implementação para chat, MCP e CLI.
- Paridade de schemas, limites e erros.
- Chat interno permanece direto no protocolo, sem MCP.
- Chats e modelos externos ganham acesso padronizado via tools MCP canônicas.
- Confinamento de leitura e limites ficam centralizados.
- Testes de contrato podem rodar contra `NavegacaoCore`, CLI e MCP.
- Nomes de tools sem prefixo de produto seguem o padrão de mercado e evitam redundância.

**Contras e riscos**

- Refatoração inicial do `ProtocoloNavegacao` e criação do catálogo de tools.
- Necessidade de lifecycle cuidado para stdio (EOF, cancelamento) e Streamable HTTP (sessões, reconexão).
- Possível divergência de `isError` entre erro de domínio e falha interna; mitigado por contrato explícito.
- `nav_resetar` é estado de sessão; no MCP deve ser documentado como reset de foco/sessão, não de histórico.

**Critérios de aceite**

1. O chat interno continua usando `ProtocoloNavegacao` diretamente, sem iniciar MCP.
2. `tools/list` inclui `nav_*` com nomes `snake_case`, ordem determinística, schemas estritos e anotações completas.
3. `tools/call` executa cada operação com resultado determinístico.
4. `flowscope nav ...` produz o mesmo JSON do `NavegacaoCore`.
5. Paginação com cursor opaco funciona em `nav_listar`, `nav_buscar` e `nav_buscar_semantico`.
6. Confinamento de leitura, paginação de 12.000 caracteres, regex timeout e limite de 8 operações são testados.
7. Nenhuma regressão nos orçamentos de token, cache de prompt ou status bar.
8. Chats externos conseguem usar `tools/list` e `tools/call` para implementar seus próprios loops.

**Rollout sugerido**

1. Extrair `NavegacaoCore` e schemas canônicos.
2. Adaptar o chat para usar `ProtocoloNavegacaoLocal` sobre o núcleo.
3. Implementar as tools `nav_*` no servidor MCP com transporte stdio e Streamable HTTP.
4. Criar CLI `flowscope nav ...`.
5. Publicar testes de paridade entre núcleo, CLI e MCP.
6. Documentar que o MCP é opcional, explícito via CLI e destinado a integrações externas.
