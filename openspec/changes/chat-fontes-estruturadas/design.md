# Design

## Context

Ver `proposal.md` — Why. Os pontos do estado atual que moldam a solução:

- `ChatMessage.sources` já existe, mas está tipado como `list[dict]` e recebe `list[str]` em runtime (`domain/chat/models.py:26`, `chat_panel.py:491`).
- `RespostaChat.fontes` é `list[str]` e a UI concatena `"Fontes: ..."` ao bloco exibido (`consultar.py:99-106`, `chat_panel.py:495-498`).
- `_fontes()` (`consultar.py:386-395`) só enxerga `dados` quando é lista: captura itens de `listar`, mas perde `obter` (caminho no resultado) e `buscar`/`buscar_semantico` (`dados` é dict com `resultados`).
- O protocolo tolerante (`protocolo.py:100-108`) devolve `RespostaProtocolo` sem fontes; o prefixo envia persona/formato em `consultar.SYSTEM_PROMPT` + `INSTRUCAO_FORMATO` e novamente em `manifesto.PERSONA` + `PROTOCOLO`.
- O transcrito é append-only; `conteudo_sessao()` lê o widget e alimenta "Copiar chat"/CSV (`app_csv.py:109`).

## Goals / Non-Goals

**Goals:**

- Ancorar a identidade da fonte no caminho real da árvore; rótulo é apenas apresentação.
- Fazer o checkbox ser puramente de visualização: alternar não toca sessão, histórico, navegação nem tokens.
- Manter "Copiar chat"/CSV coerentes com a tela sem duplicar lógica de renderização.
- Preservar compatibilidade com respostas em texto puro e com o resumo forçado por limite de iterações.

**Non-Goals:**

- Persistir a preferência do checkbox entre sessões ou em configuração.
- Extrair citações inline escritas por modelos que desobedeçam ao prompt (não há remoção confiável de texto livre).
- Consolidar/refatorar a duplicação de persona e formato entre `consultar.py` e `manifesto.py` nesta change.
- Exportar a conversa como JSON estruturado; a cópia permanece textual.

## Decisions

### 1. Fonte estruturada no domínio

Criar `FonteChat` (dataclass frozen) em `domain/chat/models.py` com `caminho: str` e `rotulo: str | None = None`. `ChatMessage.sources` e `RespostaChat.fontes` passam a `list[FonteChat]`.

Alternativa descartada: manter `list[dict]`/`list[str]`. Além da divergência atual de tipo, a renderização e o merge precisariam normalizar formatos em cada ponto.

### 2. Parse tolerante do campo `fontes`

`RespostaProtocolo` ganha `fontes: list[FonteChat]`. `_fontes_declaradas(itens)` aceita item como string (caminho, sem rótulo) ou dicionário com `caminho` textual e `rotulo` textual opcional; itens inválidos são descartados. `extrair_json` continua exigindo a chave `resposta`, então modelos em texto puro seguem no caminho atual.

O campo só é considerado no turno final; `_resposta_final` recebe `interpretada.fontes`. `_resumo_final`, que não interpreta JSON, usa o conjunto declarado vazio.

### 3. Derivação por operação, não por formato de `dados`

Reescrever a extração para olhar o resultado de cada operação, independente do formato adaptado por `_para_chat`:

- `obter`: usar o `caminho` do próprio resultado, quando não houver `erro`.
- `listar`: itens em `dados` (lista) com `caminho`.
- `buscar`/`buscar_semantico`: itens em `dados["resultados"]`.
- `contar`, `existe`, `resetar_navegacao` e resultados com `erro`: nenhuma fonte.

Dedup com `dict.fromkeys` preservando a primeira ocorrência, mantendo a ordem determinística dos ciclos.

Alternativa descartada: inferir pelo tipo de `dados`. Foi exatamente essa heurística que deixou `obter` e buscas de fora.

### 4. Merge declarado × derivado com validação na árvore

Em `_resposta_final`, normalizar cada caminho declarado com `normalizar_caminho` e validar contra a árvore (novo método fino `ProtocoloNavegacao.existe(caminho)`). Regras:

- caminho derivado + declarado → mantém a posição derivada e associa o rótulo;
- caminho declarado válido não derivado → acrescenta ao final (rede de segurança para a extração);
- caminho declarado inexistente ou inválido → descarta e registra em log (`logger.warning`);
- declarações repetidas → uma única entrada.

Sem declaradas, a lista final é exatamente a derivada, sem rótulos. Adotar um teto defensivo de entradas declaradas (ex.: 50) para evitar respostas com `fontes` desproporcional.

Alternativa descartada: deixar a LLM escolher o subconjunto exibido. O conjunto continua sendo o que foi efetivamente navegado; a LLM só rotula, como acordado.

### 5. Prompt: contrato único em dois pontos

Atualizar `SYSTEM_PROMPT`/`INSTRUCAO_FORMATO` (`consultar.py`) e `PERSONA`/`PROTOCOLO` (`manifesto.py`) para remover "Cite as fontes..." e exigir: não citar fontes no corpo de `resposta`; declará-las em `fontes` com `caminho` da árvore e `rotulo` curto opcional.

Como os textos são complementares (não idênticos) e o escopo é conter a change, não consolidar agora; adicionar teste de contrato que verifica a orientação nos dois pontos, prevenindo drift.

### 6. Renderização dirigida pela sessão

Extrair um único renderizador `_bloco(mensagem)`: `"<rótulo>: <content>"` e, se for `assistant`, o checkbox estiver marcado e houver fontes, acrescenta um bloco separado:

```
-- Fontes consultadas --
- <rotulo> (<caminho>)
- <caminho>
```

`_registrar` adiciona à sessão e chama `_renderizar_conversa()`, que limpa o `ReadonlyText` e reconstrói todas as mensagens. O toggle apenas chama o mesmo renderizador. Consequências:

- consistência entre append e toggle;
- `conteudo_sessao()` continua lendo o widget, então "Copiar chat"/CSV seguem o checkbox sem mudança em `app_csv.py`;
- custo O(n²) no total de appends, irrelevante para o teto de conversa em memória.

Alternativa descartada: append incremental + re-render só no toggle. Duplica a lógica de formatação e abre espaço para divergência entre o que foi anexado e o que o toggle desenha.

### 7. Checkbox no cabeçalho

`tk.BooleanVar(value=False)` + `ttk.Checkbutton` no cabeçalho, com texto "Exibir fontes". Permanece habilitado durante o envio (é só visualização) e não entra no bloqueio de cabeçalho. Alternar não altera sessão, tokens nem navegação. O scroll vai para o fim após redesenhar.

## Risks / Trade-offs

- **Modelo cita fontes inline mesmo instruído** → não há remoção confiável de texto livre; mitigação é o prompt explícito + teste de contrato, com risco residual documentado.
- **Lista derivada ruidosa** (ex.: `listar` de ramo grande gera muitos caminhos) → os rótulos ajudam a leitura; o comportamento fica fiel a "consultadas". Se necessário, a curadoria por subconjunto pode ser reavaliada depois.
- **Acoplamento ao formato de `dados`** → a extração passa a chavear por `op`, e os testes cobrem cada operação para evitar regressão silenciosa.
- **Re-render apaga seleção/scroll** → redesenhar e reposicionar no fim é aceitável para o tamanho da conversa; preservar `yview` fica fora do escopo.
- **Custo de saída do campo `fontes`** → entradas curtas e teto defensivo limitam o impacto; fontes não são reenviadas no histórico (só `content`).
- **`_tem_conteudo()` depende do texto renderizado** → mensagem com resposta vazia e apenas fontes ocultas contaria como vazia; não ocorre no fluxo normal, mas o teste de renderização deve cobrir respostas sem fontes.

## Migration Plan

- Sem dados persistidos, configuração ou migração. A mudança vale em runtime a partir do próximo envio.
- Rollback: reverter o código; respostas antigas não existem entre execuções (sessão em memória).

## Open Questions

Nenhuma que altere specs, abordagem ou tarefas. A persistência da preferência do checkbox e a consolidação dos prompts ficam explicitamente fora do escopo.
