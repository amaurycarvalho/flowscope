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

## 1. Início do servidor (`flowscope mcp`)

O servidor é iniciado explicitamente pelo subcomando `flowscope mcp` e fala
**stdio**: o cliente lança o processo, as mensagens JSON-RPC 2.0 são delimitadas
por newline em `stdin` e `stdout`, e o servidor encerra ao receber **EOF**.
Nenhuma porta de rede é aberta. Sem os parâmetros de preparação,
a árvore é lida do cache local padrão do FlowScopeBR.

O subcomando aceita os parâmetros opcionais `--watchlist <arquivo>` e
`--data <AAAA-MM-DD>`, tratados pela **preparação na inicialização** (seção 7):
com eles, as mesmas etapas de `flowscope carregar watchlist` e
`flowscope atualizar fundamentos --data` são executadas **antes** de o servidor
começar a atender, sob o lock global de ação, com progresso em `stderr` e sem
escrever em `stdout`. Uma falha na preparação aborta a inicialização com código
diferente de zero, sem subir o servidor.

```bash
flowscope mcp
flowscope mcp --watchlist carteira.txt --data 2026-10-14
```

Regras do canal:

- `stdout` recebe **apenas** mensagens JSON-RPC válidas;
- logs, diagnósticos e o progresso da preparação vão para `stderr`;
- o servidor suporta `notifications/cancelled` sem corromper o canal.

### Exemplo de configuração de cliente MCP

```json
{
  "mcpServers": {
    "flowscope": {
      "command": "flowscope",
      "args": ["mcp"]
    }
  }
}
```

Ao instalar a partir do código-fonte, use `python3 -m flowscope mcp` ou o
caminho do executável gerado (`dist/flowscope mcp`).

---

## 2. Revisão de protocolo

O servidor implementa a revisão moderna **`2026-07-28`**: cada requisição
declara a versão em `_meta` (`{"_meta": {"protocolVersion": "2026-07-28"}}`) e
não há handshake `initialize`. A RPC obrigatória é `server/discover`, que devolve
as versões suportadas, as capacidades e a identidade do servidor:

```json
{
  "protocolVersions": ["2026-07-28"],
  "capabilities": { "tools": { "listChanged": false } },
  "serverInfo": { "name": "flowscope", "version": "<versão>" }
}
```

Quando a versão solicitada não é suportada, o servidor responde com
`UnsupportedProtocolVersionError` listando as versões suportadas. Ao receber um
`initialize` legado, responde com erro que nomeia `2026-07-28`.

---

## 3. Catálogo de tools `nav_*`

`tools/list` devolve as oito tools em **ordem alfabética determinística**, cada
uma com `title`, descrição, `inputSchema` e as anotações `readOnlyHint`,
`destructiveHint`, `idempotentHint` e `openWorldHint` (todas somente-leitura:
`true`, `false`, `true`, `false`).

| Tool                   | Operação           | Argumentos obrigatórios | Opcionais             |
| ---------------------- | ------------------ | ----------------------- | --------------------- |
| `nav_listar`           | `listar`           | `caminho`               | `cursor`              |
| `nav_obter`            | `obter`            | `caminho`               | `offset`, `limite`    |
| `nav_contar`           | `contar`           | `caminho`               | —                     |
| `nav_existe`           | `existe`           | `caminho`               | —                     |
| `nav_buscar`           | `buscar`           | `caminho`, `regex`      | `em`, `max`, `cursor` |
| `nav_buscar_semantico` | `buscar_semantico` | `caminho`, `consulta`   | `max`, `cursor`       |
| `nav_data_referencia`  | `data_referencia`  | —                       | —                     |
| `nav_manifesto`        | `manifesto`        | —                       | —                     |

`nav_data_referencia` devolve a data de referência resolvida da última carga de
fundamentos (marcador `last_fundamentals`, com fallback para `last_date`); sem
data registrada, devolve `{"data": null}` **sem `isError`**. É somente-leitura:
não consulta a B3/CVM, não baixa, não extrai e não escreve estado.

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
  "content": [
    { "type": "text", "text": "{\"itens\": [...], \"nextCursor\": \"...\"}" }
  ],
  "structuredContent": { "itens": ["..."], "nextCursor": "..." }
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
flowscope nav data-referencia
flowscope nav manifesto --pretty
```

---

## 6. Escopo restrito de leitura

O servidor e a CLI **apenas leem o cache local** por meio do núcleo de navegação.
Nenhuma tool ou subcomando de navegação permite consultar a B3/CVM, baixar,
extrair, resumir ou escrever estado. Nós sem dado em cache são omitidos em
silêncio.

As **ações de atualização são exclusivas da CLI** (`flowscope carregar`,
`atualizar` e `resumir`) e **não** são expostas como tools MCP. A preparação
opcional na inicialização do `flowscope mcp` (seção 7) ocorre antes do servidor,
reusa os mesmos núcleos e **não** é acessível pelo protocolo.

---

## 7. Preparação na inicialização do `flowscope mcp`

Com `--watchlist <arquivo>`, o sistema executa antes de servir a mesma etapa de
`flowscope carregar watchlist <arquivo>`. Com `--data <AAAA-MM-DD>`, executa a
mesma etapa de `flowscope atualizar fundamentos --data <AAAA-MM-DD>`, usando a
watchlist resultante; sem `--data`, a árvore usa a data de referência resolvida.
A preparação reusa os núcleos das ações, ocorre sob o lock global de ação
(liberado antes de o servidor atender) e monta a árvore refletindo a data de
referência. Falha na preparação aborta a inicialização com código de saída
diferente de zero. O default de **data de hoje** vale para os subcomandos
`atualizar`; `flowscope mcp` sem `--data` continua **sem atualizar** e apenas
serve a árvore a partir do cache.

Em um dia não útil, uma atualização sem `--data` grava a data de hoje no
marcador de última carga; a navegação recua para a observação mais recente
disponível. Use `--data` (ou `FLOWSCOPE_REFERENCE_DATE`) quando precisar de uma
data específica.

---

## 8. Servidor MCP em container Docker

Esta seção mostra como empacotar o servidor MCP em uma imagem Docker para
executá-lo sem instalar Python, dependências ou a interface gráfica na máquina
cliente. O container fala **stdio**: o cliente MCP inicia `docker run -i` e
conversa com o processo pelo `stdin`/`stdout`, sem publicar portas.

O exemplo abaixo inclui uma preparação **opcional** na inicialização. Por
padrão (`FLOWSCOPE_INIT_UPDATES=none`) o container apenas carrega a watchlist,
se o arquivo existir, e sobe o servidor MCP. Quando habilitada, a preparação
executa, antes de servir, as ações de atualização da CLI — sempre com a **data
de hoje** no fuso do container, salvo se `FLOWSCOPE_REFERENCE_DATE` for
informado como override opcional:

| Etapa                | Comando executado                                  |
| -------------------- | -------------------------------------------------- |
| `fundamentos`        | `flowscope atualizar fundamentos [--data <data>]`  |
| `documentos`         | `flowscope atualizar documentos [--data <data>]`   |
| `noticias`           | `flowscope atualizar noticias [--data <data>]`     |
| `resumir-documentos` | `flowscope resumir documentos`                     |
| `resumir-noticias`   | `flowscope resumir noticias`                       |

Use `FLOWSCOPE_INIT_UPDATES=all` para todas as etapas ou uma lista separada por
vírgulas para escolher etapas individuais, por exemplo
`FLOWSCOPE_INIT_UPDATES=fundamentos,noticias`. Como `all` inclui as etapas
`resumir-*`, ele exige a LLM configurada e pode atrasar o handshake do MCP
enquanto resume toda a watchlist. As mesmas ações também podem ser executadas
isoladamente, sem iniciar o servidor (veja a seção 8.5).

A imagem pode ser montada de duas formas: a partir do **código-fonte** (seção
8.1) ou usando o **binário `flowscope-linux` já compilado pelo PyInstaller** e
baixado da página de releases (seção 8.2). As duas variantes reutilizam o mesmo
`entrypoint.sh` e compartilham a configuração das seções seguintes.

### 8.1. Arquivos de exemplo (a partir do código-fonte)

Na **raiz do repositório**, crie o `Dockerfile` e o `entrypoint.sh` com o
conteúdo abaixo (o build usa `pyproject.toml` e `src/` como contexto):

```dockerfile
# Dockerfile
# A variante completa (não -slim) inclui o módulo _tkinter usado pela
# composição da árvore de conhecimento do FlowScope.
FROM python:3.12

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=America/Sao_Paulo

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
RUN pip install ".[llm]"

COPY entrypoint.sh /usr/local/bin/flowscope-entrypoint
RUN chmod +x /usr/local/bin/flowscope-entrypoint \
    && useradd --create-home --uid 1000 flowscope \
    && mkdir -p /home/flowscope/.cache/flowscope /home/flowscope/.flowscope \
    && chown -R flowscope:flowscope /home/flowscope

USER flowscope
WORKDIR /home/flowscope

VOLUME ["/home/flowscope/.cache/flowscope", "/home/flowscope/.flowscope"]

ENTRYPOINT ["flowscope-entrypoint"]
CMD ["mcp"]
```

```sh
#!/bin/sh
# entrypoint.sh
set -eu

: "${FLOWSCOPE_WATCHLIST:=/data/watchlist.txt}"
: "${FLOWSCOPE_INIT_UPDATES:=none}"
: "${FLOWSCOPE_LOCK_WAIT:=60}"
: "${FLOWSCOPE_REFERENCE_DATE:=}"

if [ "$#" -eq 0 ]; then
  set -- mcp
fi

# Atualiza com a data de hoje, ou com FLOWSCOPE_REFERENCE_DATE quando definida.
atualizar() {
  if [ -n "$FLOWSCOPE_REFERENCE_DATE" ]; then
    flowscope "$@" --data "$FLOWSCOPE_REFERENCE_DATE" --esperar "$FLOWSCOPE_LOCK_WAIT" >/dev/null
  else
    flowscope "$@" --esperar "$FLOWSCOPE_LOCK_WAIT" >/dev/null
  fi
}

if [ -f "$FLOWSCOPE_WATCHLIST" ]; then
  flowscope carregar watchlist "$FLOWSCOPE_WATCHLIST" >/dev/null
fi

if [ "$1" = "mcp" ] && [ "$FLOWSCOPE_INIT_UPDATES" != "none" ]; then
  etapas=$(printf '%s' "$FLOWSCOPE_INIT_UPDATES" | tr -d '[:space:]')
  if [ "$etapas" = "all" ]; then
    etapas="fundamentos,documentos,noticias,resumir-documentos,resumir-noticias"
  fi

  old_ifs=$IFS
  IFS=,
  for etapa in $etapas; do
    case "$etapa" in
      fundamentos)
        atualizar atualizar fundamentos
        ;;
      documentos)
        atualizar atualizar documentos
        ;;
      noticias)
        atualizar atualizar noticias
        ;;
      resumir-documentos)
        flowscope resumir documentos --esperar "$FLOWSCOPE_LOCK_WAIT" >/dev/null
        ;;
      resumir-noticias)
        flowscope resumir noticias --esperar "$FLOWSCOPE_LOCK_WAIT" >/dev/null
        ;;
      *)
        echo "Etapa desconhecida em FLOWSCOPE_INIT_UPDATES: $etapa" >&2
        exit 1
        ;;
    esac
  done
  IFS=$old_ifs
fi

exec flowscope "$@"
```

Os resultados JSON das ações de preparação são descartados (`>/dev/null`), pois
o `stdout` do container precisa conter apenas mensagens JSON-RPC do MCP. O
progresso e os erros continuam em `stderr`. Qualquer falha em uma etapa aborta a
inicialização, como na preparação nativa de `flowscope mcp`.

### 8.2. Variante com binário do PyInstaller

Se você já baixou o binário `flowscope-linux` da
[página de releases](https://github.com/amaurycarvalho/flowscope/releases) e o
colocou na **mesma pasta do Dockerfile**, use esta variante. Ela não instala
Python nem as dependências do projeto: copia o executável e apenas as
bibliotecas de sistema necessárias para HTTPS, fuso horário e Tk.

> O binário publicado é gerado no runner `ubuntu-latest`, então a imagem usa
> `ubuntu:24.04` para manter a compatibilidade da glibc. O binário é `x86_64`;
> em outra arquitetura, compile a partir do código-fonte ou gere um binário
> compatível.

```dockerfile
# Dockerfile.binario
FROM ubuntu:24.04

ENV PYTHONUNBUFFERED=1 \
    TZ=America/Sao_Paulo

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates tzdata tk passwd \
    && rm -rf /var/lib/apt/lists/*

COPY flowscope-linux /usr/local/bin/flowscope
COPY entrypoint.sh /usr/local/bin/flowscope-entrypoint
RUN chmod +x /usr/local/bin/flowscope /usr/local/bin/flowscope-entrypoint \
    && useradd --create-home --uid 1000 flowscope \
    && mkdir -p /home/flowscope/.cache/flowscope /home/flowscope/.flowscope \
    && chown -R flowscope:flowscope /home/flowscope

USER flowscope
WORKDIR /home/flowscope

VOLUME ["/home/flowscope/.cache/flowscope", "/home/flowscope/.flowscope"]

ENTRYPOINT ["flowscope-entrypoint"]
CMD ["mcp"]
```

Com o `Dockerfile.binario`, o `entrypoint.sh` da seção 8.1 e o
`flowscope-linux` baixado na mesma pasta, execute:

```bash
docker build -f Dockerfile.binario -t flowscope-mcp:bin .
```

O `entrypoint.sh` é exatamente o mesmo da seção 8.1; as variáveis e os comandos
de atualização não mudam. A diferença é que o binário de release já inclui o
Python, as dependências do projeto e o liteLLM, o que dispensa `pip install` no
build e reduz o tempo de criação da imagem.

### 8.3. Build e execução

Para a imagem a partir do código-fonte, a partir da raiz do repositório, com os
dois arquivos criados, execute:

```bash
docker build -t flowscope-mcp .
```

Recomenda-se um `.dockerignore` com `.git`, `.venv`, `build`, `dist`, `mutants`,
`tests`, `docs` e `openspec` para reduzir o contexto de build. Para a variante
com o binário, use o comando da seção 8.2.

Execução manual, com a watchlist montada e os dados persistidos em volumes:

```bash
docker run --init -i --rm \
  -e TZ=America/Sao_Paulo \
  -e FLOWSCOPE_INIT_UPDATES=all \
  -v flowscope-cache:/home/flowscope/.cache/flowscope \
  -v flowscope-config:/home/flowscope/.flowscope \
  -v "$PWD/carteira.txt:/data/watchlist.txt:ro" \
  flowscope-mcp:latest
```

O comando acima sobe o servidor MCP e fica aguardando mensagens em `stdin`.
Normalmente ele é iniciado pelo cliente MCP, não manualmente.

### 8.4. Configuração de cliente MCP

Para um cliente que aceita servidores MCP via `command`/`args` (por exemplo,
`opencode`), use o Docker como comando e mantenha `-i` para o transporte stdio:

```json
{
  "mcpServers": {
    "flowscope": {
      "command": "docker",
      "args": [
        "run", "--init", "-i", "--rm",
        "-e", "TZ=America/Sao_Paulo",
        "-e", "FLOWSCOPE_INIT_UPDATES=all",
        "-e", "FLOWSCOPE_WATCHLIST=/data/watchlist.txt",
        "-v", "flowscope-cache:/home/flowscope/.cache/flowscope",
        "-v", "flowscope-config:/home/flowscope/.flowscope",
        "-v", "/caminho/para/carteira.txt:/data/watchlist.txt:ro",
        "flowscope-mcp:latest"
      ]
    }
  }
}
```

Para deixar o container somente-leitura em relação à preparação, use
`FLOWSCOPE_INIT_UPDATES=none` (padrão) ou omita a variável. Nesse caso o cache
precisa ter sido populado por execuções anteriores ou por outro comando.

### 8.5. Atualizações individuais

As etapas podem ser executadas isoladamente, sem subir o servidor. O entrypoint
carrega a watchlist automaticamente quando o arquivo está presente:

```bash
# Fundamentos com a data de hoje
docker run --rm \
  -v flowscope-cache:/home/flowscope/.cache/flowscope \
  -v flowscope-config:/home/flowscope/.flowscope \
  -v "$PWD/carteira.txt:/data/watchlist.txt:ro" \
  flowscope-mcp:latest atualizar fundamentos

# Documentos de toda a watchlist
docker run --rm \
  -v flowscope-cache:/home/flowscope/.cache/flowscope \
  -v flowscope-config:/home/flowscope/.flowscope \
  -v "$PWD/carteira.txt:/data/watchlist.txt:ro" \
  flowscope-mcp:latest atualizar documentos

# Notícias e resumos
docker run --rm \
  -v flowscope-cache:/home/flowscope/.cache/flowscope \
  -v flowscope-config:/home/flowscope/.flowscope \
  -v "$PWD/carteira.txt:/data/watchlist.txt:ro" \
  flowscope-mcp:latest atualizar noticias

docker run --rm \
  -v flowscope-cache:/home/flowscope/.cache/flowscope \
  -v flowscope-config:/home/flowscope/.flowscope \
  -v "$PWD/carteira.txt:/data/watchlist.txt:ro" \
  flowscope-mcp:latest resumir documentos

docker run --rm \
  -v flowscope-cache:/home/flowscope/.cache/flowscope \
  -v flowscope-config:/home/flowscope/.flowscope \
  flowscope-mcp:latest resumir noticias
```

Sem `--data`, as ações `atualizar` usam a **data de hoje** no fuso do container
(`TZ`). Para usar outra data, acrescente `--data AAAA-MM-DD` (ou defina
`FLOWSCOPE_REFERENCE_DATE` no container). `resumir documentos` sem ticker
processa toda a `last_tickers` carregada. Para os
resumos, a LLM precisa estar configurada no `config.json` persistido no volume
de configuração (ou montado a partir do host); sem provedor, `resumir` falha com
erro estruturado. Por isso, ao usar `FLOWSCOPE_INIT_UPDATES`, não inclua etapas
de resumo (`all` ou `resumir-*`) se a LLM não estiver configurada.

### 8.6. Variáveis de ambiente

| Variável                    | Padrão                | Descrição                                                                 |
| --------------------------- | --------------------- | ------------------------------------------------------------------------- |
| `TZ`                        | `America/Sao_Paulo`   | Fuso usado para resolver “hoje” e registrar datas.                        |
| `FLOWSCOPE_WATCHLIST`       | `/data/watchlist.txt` | Arquivo com um ticker por linha, carregado antes das atualizações.        |
| `FLOWSCOPE_INIT_UPDATES`    | `none`                | `none`, `all` ou lista separada por vírgulas das etapas da tabela acima.  |
| `FLOWSCOPE_REFERENCE_DATE`  | não definida           | Override opcional (`AAAA-MM-DD`); sem ela, `atualizar` usa a data de hoje. |
| `FLOWSCOPE_LOCK_WAIT`       | `60`                  | Segundos de espera pelo lock global antes de uma etapa falhar.            |

### 8.7. Dados persistentes e segurança

- Monte `/home/flowscope/.cache/flowscope` para preservar o cache de
  fundamentos, documentos e notícias entre execuções.
- Monte `/home/flowscope/.flowscope` para preservar `config.json` (watchlist,
  data de referência e configuração de LLM) e os logs.
- Se preferir compartilhar os dados com a instalação local, use bind mounts em
  vez de volumes nomeados:
  `-v "$HOME/.cache/flowscope:/home/flowscope/.cache/flowscope"` e
  `-v "$HOME/.flowscope:/home/flowscope/.flowscope"`. Nesse caso, garanta que o
  UID do processo tenha permissão de escrita nos diretórios do host (o exemplo
  usa UID 1000; ajuste com `--user "$(id -u):$(id -g)"` se necessário).
- O container não abre portas. A única entrada é o `stdin` do processo; mantenha
  o transporte stdio e não adicione `-t`, que pode interferir no canal.
- Chaves de API e demais segredos ficam em `config.json`; não os passe em
  variáveis de ambiente nem os inclua na imagem.
