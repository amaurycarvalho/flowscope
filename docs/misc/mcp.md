# Servidor MCP e navegação por CLI

O FlowScopeBR expõe a sua árvore de conhecimento — o mesmo estado local navegável
usado pela aba "Chat AI" — como **tools MCP canônicas** e como **subcomandos
`nav`** de linha de comando. As duas superfícies reusam o mesmo núcleo de
navegação (`NavegacaoCore`), então a mesma operação produz o mesmo resultado
estruturado, com os mesmos limites, a mesma paginação e os mesmos erros.

> **MCP é opcional.** O chat interno **não** inicia, não consulta e não depende
> do servidor MCP: ele continua consumindo o protocolo JSON diretamente, por um
> adaptador local. O servidor destina-se a chats e modelos externos e a
> automações.

---

## 1. Início do servidor (`flowscope --mcp`)

O servidor é iniciado explicitamente e fala **stdio**: o cliente lança o
processo, as mensagens JSON-RPC 2.0 são delimitadas por newline em `stdin` e
`stdout`, e o servidor encerra ao receber **EOF**. Nenhuma porta de rede é
aberta e o comando **não** aceita parâmetros de raiz ou de compactação: a árvore
é sempre lida do cache local padrão do FlowScopeBR.

```bash
flowscope --mcp
```

Regras do canal:

- `stdout` recebe **apenas** mensagens JSON-RPC válidas;
- logs e diagnósticos vão para `stderr`;
- o servidor suporta `notifications/cancelled` sem corromper o canal.

### Exemplo de configuração de cliente MCP

```json
{
  "mcpServers": {
    "flowscope": {
      "command": "flowscope",
      "args": ["--mcp"]
    }
  }
}
```

Ao instalar a partir do código-fonte, use `python3 -m flowscope --mcp` ou o
caminho do executável gerado (`dist/flowscope --mcp`).

---

## 2. Revisão de protocolo

O servidor implementa a revisão moderna **`2026-07-28`**: cada requisição
declara a versão em `_meta` (`{"_meta": {"protocolVersion": "2026-07-28"}}`) e
não há handshake `initialize`. A RPC obrigatória é `server/discover`, que devolve
as versões suportadas, as capacidades e a identidade do servidor:

```json
{
  "protocolVersions": ["2026-07-28"],
  "capabilities": {"tools": {"listChanged": false}},
  "serverInfo": {"name": "flowscope", "version": "<versão>"}
}
```

Quando a versão solicitada não é suportada, o servidor responde com
`UnsupportedProtocolVersionError` listando as versões suportadas. Ao receber um
`initialize` legado, responde com erro que nomeia `2026-07-28`.

---

## 3. Catálogo de tools `nav_*`

`tools/list` devolve as sete tools em **ordem alfabética determinística**, cada
uma com `title`, descrição, `inputSchema` e as anotações `readOnlyHint`,
`destructiveHint`, `idempotentHint` e `openWorldHint` (todas somente-leitura:
`true`, `false`, `true`, `false`).

| Tool                   | Operação            | Argumentos obrigatórios | Opcionais                          |
| ---------------------- | ------------------- | ----------------------- | ---------------------------------- |
| `nav_listar`           | `listar`            | `caminho`               | `cursor`                           |
| `nav_obter`            | `obter`             | `caminho`               | `offset`, `limite`                 |
| `nav_contar`           | `contar`            | `caminho`               | —                                  |
| `nav_existe`           | `existe`            | `caminho`               | —                                  |
| `nav_buscar`           | `buscar`            | `caminho`, `regex`      | `em`, `max`, `cursor`              |
| `nav_buscar_semantico` | `buscar_semantico`  | `caminho`, `consulta`   | `max`, `cursor`                    |
| `nav_manifesto`        | `manifesto`         | —                       | —                                  |

Limites dos schemas: `nav_obter.limite` entre 1 e 12.000 (padrão 12.000);
`nav_buscar.max` entre 1 e 50 (padrão 50); `nav_buscar_semantico.max` entre 1 e
20 (padrão 10). Argumentos que violem o schema são recusados com erro
estruturado de validação, sem executar a operação.

---

## 4. Paginação por cursor

As tools de listagem (`nav_listar`, `nav_buscar`, `nav_buscar_semantico`) aceitam
um argumento `cursor` opcional e devolvem `nextCursor` **apenas quando há mais
resultados**. O cursor é um token **opaco** (base64url de `{v, op, caminho,
pos}`): o cliente não o interpreta, apenas o devolve na chamada seguinte. A
ausência de `nextCursor` significa fim dos resultados.

- `nav_listar` pagina de **100 em 100** itens;
- `nav_buscar` mantém o limite de **50** resultados por página;
- `nav_buscar_semantico` mantém o limite de **20** resultados por página.

Um cursor malformado, de versão desconhecida ou originado de outra operação ou
caminho é recusado com erro recuperável `cursor_invalido`.

A paginação é sensível à mudança de estado: se o cache mudar entre duas páginas,
os itens podem deslocar. Nesse caso, refaça a operação sem cursor para obter uma
nova visão.

### Envelopes de resultado e erro

`tools/call` devolve o resultado em `content` (texto JSON) e
`structuredContent`:

```json
{
  "content": [{"type": "text", "text": "{\"itens\": [...], \"nextCursor\": \"...\"}"}],
  "structuredContent": {"itens": ["..."], "nextCursor": "..."}
}
```

Erros de domínio recuperáveis (`caminho_invalido`, `cursor_invalido`,
`indice_indisponivel`, `regex_bloqueada`, `timeout_regex`, …) são devolvidos como
conteúdo estruturado com `motivo`, `detalhe` e `dica`, **sem `isError`**:

```json
{
  "structuredContent": {
    "erro": {
      "motivo": "caminho_invalido",
      "detalhe": "/nao/existe",
      "dica": "caminho não existe; use existe(caminho) ou listar(/ancestral)"
    }
  }
}
```

Falhas internas não tratadas são marcadas com `isError: true`, e o servidor
continua atendendo novas chamadas. Uma tool desconhecida devolve erro JSON-RPC de
tool não encontrada, também sem encerrar o servidor.

---

## 5. Subcomandos `flowscope nav ...`

A CLI usa o mesmo `NavegacaoCore`. A saída padrão é JSON em `stdout`; a flag
`--pretty` formata a saída para leitura humana. Erros de navegação são impressos
como JSON estruturado em `stdout`, com o diagnóstico em `stderr`.

```bash
flowscope nav listar /noticias/grupos
flowscope nav listar /noticias/grupos --cursor <token>
flowscope nav obter /documentos/PETR4/<chave>/texto --offset 0 --limite 12000
flowscope nav contar "/documentos/PETR4/*"
flowscope nav existe /guidance/PETR4
flowscope nav buscar /documentos/PETR4 --regex "..." --em titulo,texto --max 50
flowscope nav buscar-semantico /documentos/PETR4 --consulta "..." --max 10
flowscope nav manifesto --pretty
```

---

## 6. Escopo restrito de leitura

O servidor e a CLI **apenas leem o cache local** por meio do núcleo de navegação.
Nenhuma tool ou subcomando permite consultar a B3/CVM, baixar, extrair, resumir
ou escrever estado. Nós sem dado em cache são omitidos em silêncio.
