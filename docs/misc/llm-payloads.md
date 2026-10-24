# Payloads de interação com o modelo (LLM)

Este documento descreve os formatos de payload trocados com o provedor de LLM nos recursos de I.A. do FlowScopeBR:

- **Resumo de documentos** (sub-aba "Documentos");
- **Resumo de notícias** (sub-aba "Notícias");
- **Chat AI** (aba de topo "Chat AI").

Todos os consumidores falam com o provedor pela porta `LLMPort.complete(messages, system_prompt)`, implementada pelo `LiteLLMChatAdapter` sobre `litellm.completion`. As mensagens seguem o formato `{"role": "user" | "assistant" | "system", "content": str}`. Quando `system_prompt` é informado, o adaptador o insere como **primeira** mensagem `system`. Enquanto o provedor configurado for `none`, nenhuma chamada de rede é realizada.

---

## 1. Resumo de documentos e notícias ("Documentos" e "Notícias")

As duas sub-abas reutilizam o mesmo caso de uso: `ResumirDocumentoUseCase.resumir(texto)` (`src/flowscope/application/resumo_documento.py`). Cada documento gera **exatamente uma** completion, com as instruções estáveis em um prefixo de sistema (`SYSTEM_PROMPT`) e **uma única mensagem de usuário** contendo apenas o texto do documento.

### 1.1 Payload enviado

```
{
  "model": "<modelo configurado>",
  "messages": [
    {
      "role": "system",
      "content": "Resuma o documento a seguir em português do Brasil, aplicando a fórmula XYZ (X: o que o texto diz; Y: por que isso importa; Z: o que se conclui) tanto no resumo curto quanto no longo.\nResponda em uma única mensagem, no formato exato:\nCURTO: <resumo em 1 a 2 frases, de até 400 caracteres>\nLONGO: <resumo em parágrafos, de até 1800 caracteres>\nPlaneje X, Y e Z para caberem no orçamento de cada resumo e nunca omita a conclusão (Z) para caber. Não use markdown, listas, títulos ou comentários. Não escreva nada antes de CURTO: nem depois do resumo longo. Baseie-se exclusivamente no documento fornecido."
    },
    {
      "role": "user",
      "content": "<texto do documento>"
    }
  ]
}
```

- **Prefixo estável:** o `system_prompt` é constante e idêntico entre documentos e entre as sub-abas "Documentos" e "Notícias", permitindo reaproveitar o cache de prompt quando o provedor suportar.
- **Fórmula XYZ:** `X` = o que o texto diz; `Y` = por que isso importa; `Z` = o que se conclui.
- **Orçamento de entrada:** o texto do documento é truncado a **12.000 caracteres** (`ORCAMENTO_ENTRADA`) antes de ser enviado como mensagem `user`.
- **Texto vazio:** `resumir("")` não chama a LLM e devolve resumos vazios.

### 1.2 Formato de resposta esperado

```
CURTO: <resumo em 1 a 2 frases>
LONGO: <resumo em parágrafos>
```

O parser é tolerante:

- Interpreta os delimitadores `CURTO:` e `LONGO:` (regex `DOTALL`, insensível a caixa).
- Sem os delimitadores, usa **a resposta inteira** como resumo longo e os primeiros caracteres como resumo curto (corte em fronteira de frase/palavra).

### 1.3 Tetos e truncamento

O prompt declara um orçamento de **400 caracteres** para o resumo curto (`ORCAMENTO_CURTO`) e **1.800** para o longo (`ORCAMENTO_LONGO`), dimensionado para acomodar a fórmula XYZ. Os tetos de truncamento ficam logo acima, como salvaguarda:

| Campo | Orçamento no prompt | Teto (salvaguarda) | Constante |
| --- | --- | --- | --- |
| `short_summary` | 400 caracteres | 450 caracteres | `LIMITE_CURTO` |
| `long_summary` | 1.800 caracteres | 2.000 caracteres | `LIMITE_LONGO` |

O truncamento corta no último fim de frase (`.`, `;`, `!`, `?`), depois no último espaço e, só em último caso, no teto.

### 1.4 Persistência e regeneração

- **Documentos:** `~/.cache/flowscope/document-summaries/{TICKER}.json` (um JSON por ticker, `schema_version = 1`, chave = caminho relativo do documento à raiz de cache, escrita atômica).
- **Notícias:** shards `~/.cache/flowscope/document-summaries/NOTICIAS-<ANO>-<MES>.json` (escopo `NOTICIAS`, a partir da data do item; o formato anterior `NOTICIAS.json` é migrado automaticamente).
- Um resumo persistido que **não termina em pontuação final** é considerado truncado e é regerado pelo lote ("Resumir pendentes"); resumos íntegros não são refeitos.

### 1.5 Payload adicional — avaliação de guidance ("Documentos")

Os Relatórios Gerenciais (categoria `Relatorio`) passam por uma avaliação separada, `AvaliarGuidanceUseCase` (`src/flowscope/application/avaliar_guidance.py`), que envia as instruções estáveis em um prefixo de sistema (`SYSTEM_PROMPT`) e **uma única mensagem de usuário** contendo apenas o trecho avaliado:

```
{
  "model": "<modelo configurado>",
  "messages": [
    {
      "role": "system",
      "content": "Você recebe um trecho de um Relatório Gerencial de um fundo imobiliário (FII). Determine se ele contém guidance de distribuição de rendimentos: uma projeção, orientação ou faixa de valor por cota para um período futuro.\nIgnore definições de glossário e referências macroeconômicas (forward guidance).\nResponda no formato exato, em quatro linhas:\nGUIDANCE: SIM ou NAO\nVALOR_MIN: <valor numérico por cota, ou vazio>\nVALOR_MAX: <valor numérico por cota, ou vazio>\nPERIODO: <período de validade, ou vazio>\nCom GUIDANCE: NAO, deixe VALOR_MIN, VALOR_MAX e PERIODO vazios. Um valor único preenche VALOR_MIN e VALOR_MAX com o mesmo número. Use o ponto como separador decimal e não inclua símbolo de moeda. Na dúvida, responda NAO."
    },
    {
      "role": "user",
      "content": "<texto>"
    }
  ]
}
```

- **Prefixo estável:** o `system_prompt` é constante e idêntico entre fontes e entre Relatórios Gerenciais, permitindo reaproveitar o cache de prompt quando o provedor suportar.
- A avaliação percorre em cascata as fontes do RG — resumo curto, resumo longo e texto extraído — e **prefere a IA**; se a IA falha, recorre à extração determinística.
- Cada RG é avaliado no máximo uma vez por método e o resultado é persistido no ledger de guidance (`/guidance` na árvore do chat e ramo "Guidance" da sub-aba "Documentos").

---

## 2. Chat AI

Origem: `ConsultarChatUseCase.consultar(...)` (`src/flowscope/application/chat/consultar.py`) e o protocolo `ProtocoloNavegacao` (`src/flowscope/application/chat/protocolo.py`). O chat resolve a pergunta por um **loop de navegação** sobre a árvore de conhecimento, com até 10 ciclos.

### 2.1 Prefixo de sistema (estável e cacheável)

O `system_prompt` enviado a cada completion é o **prefixo estável**:

```
<SYSTEM_PROMPT do ConsultarChatUseCase>

<INSTRUCAO_FORMATO>

<manifesto da árvore>
```

- **Persona e regras** (`SYSTEM_PROMPT`): assistente do FlowScopeBR, responde apenas com base no contexto navegado, cita as fontes, identifica o ticker referido, usa `contar`/`existe` antes de listar ramos grandes, lê o texto integral de alvos por `obter` (paginando com `offset`/`limite`), abre resumos (`/curto`, `/longo`) para listar/resumir vários documentos e nunca responde prometendo navegar.
- **Contrato de resposta** (`INSTRUCAO_FORMATO`): exige um objeto JSON `{"resposta": "<texto ou null>", "solicitacoes": [...]}`, vazio quando a resposta já for conclusiva.
- **Manifesto** (`montar_manifesto`, `src/flowscope/application/chat/manifesto.py`): renderizado de forma determinística e **byte-a-byte estável** enquanto a assinatura do estado não muda (aproveitando cache de prompt quando o provedor suporta). Contém as seções:
  - `# Árvore de conhecimento do FlowScopeBR` + persona;
  - `## Descrição` (ramos de topo presentes);
  - `## Mapa da árvore` (caminhos canônicos apenas dos ramos presentes);
  - `### Playbook por intenção` (intenção → ramo);
  - `## Listas de chaves` (tickers, campos, abas, sub-abas, indicadores, grupos de notícias);
  - `## Metadados` (metadados curtos, sem conteúdo pesado);
  - `## Protocolo de navegação` (operações, formato de resposta e limites).

  O manifesto tem teto de **4.000 tokens**; ao exceder, degrada para "só chaves" e, no limite, trunca.

### 2.2 Payload de mensagens

A cada ciclo, as mensagens são montadas na ordem: **histórico de diálogo** → **navegação acumulada** (pares assistant/resultado de perguntas anteriores) → **pergunta atual** → **navegação corrente** (pares gerados neste turno).

```
{
  "model": "<modelo configurado>",
  "messages": [
    { "role": "system", "content": "<prefixo estável: persona + formato + manifesto>" },

    { "role": "user",      "content": "<pergunta anterior>" },
    { "role": "assistant", "content": "<resposta final anterior>" },

    { "role": "assistant", "content": "{\"resposta\": null, \"solicitacoes\": [{\"op\": \"listar\", \"caminho\": \"/noticias/grupos\"}]}" },
    { "role": "user",      "content": "[RESULTADO_NAVEGACAO] {\"resultados\": [{\"op\": \"listar\", \"caminho\": \"/noticias/grupos\", \"dados\": [...]}], \"foco\": null}" },

    { "role": "user", "content": "<pergunta atual>" }
  ]
}
```

- O **histórico** inclui apenas turnos marcados para envio (erros e avisos ficam de fora), com teto de **10 mensagens** e **8.000 caracteres**, descartando os turnos mais antigos.
- A **navegação acumulada** é reusada entre perguntas, respeitando uma cota de **32.000 tokens**; é descartada quando a assinatura do estado muda.

### 2.3 Formato de resposta exigido (JSON estrito)

```
{"resposta": "<texto ou null>", "solicitacoes": [{"op": "contar", "caminho": "/documentos/PETR4/*"}]}
```

- `solicitacoes` vazio ⇒ `resposta` é final e o loop encerra.
- O parser é tolerante: aceita bloco cercado por ```json, o texto cru ou o trecho entre a primeira `{` e a última `}`. Sem JSON reconhecido, **todo o texto** é tratado como resposta final.

### 2.4 Operações de navegação

| `op` | Campos obrigatórios | Campos opcionais | Resultado |
| --- | --- | --- | --- |
| `listar` | `caminho` | — | Filhos imediatos (`nome`, `caminho`, `metadado`) |
| `obter` | `caminho` | `offset`, `limite` | Conteúdo do nó; nós pesados devolvem página |
| `contar` | `caminho` | — | Número de nós da subárvore |
| `existe` | `caminho` | — | Booleano |
| `buscar` | `caminho`, `regex` | `em` (lista), `max` | Nós cujos campos casam com o regex |
| `buscar_semantico` | `caminho`, `consulta` | `max` | Nós por similaridade (ou `indice_indisponivel`) |
| `resetar_navegacao` | — | — | Descarta a navegação acumulada e o foco |

- No máximo **8 operações por turno**; o excedente é respondido com `{"op": "limite_operacoes", "erro": {...}}`.
- O coringa `*` só é aceito em `contar`, e apenas como `prefixo/*`.
- Sem backend vetorial, `buscar_semantico` devolve `{"resultados": [], "motivo": "indice_indisponivel", ...}` e o chat segue na busca determinística por `buscar` (evolução futura `llm-chat-rag`).

### 2.5 Bloco de resultado da navegação

Os resultados das operações são serializados em um bloco determinístico, com o `foco` (último caminho obtido com sucesso) para resolver referências anafóricas ("esse documento"):

```
[RESULTADO_NAVEGACAO] {"resultados": [{"op": "obter", "caminho": "/documentos/PETR4/<chave>/texto", "dados": {"texto": "...", "total": 40000, "offset": 0, "limite": 12000, "continua": true}}], "foco": "/documentos/PETR4/<chave>/texto"}
```

Erros são devolvidos de forma estruturada, com dica de recuperação:

```
{"op": "obter", "caminho": "/nao/existe", "erro": {"motivo": "caminho_invalido", "detalhe": "...", "dica": "use existe(caminho) ou listar(...)"}}
```

Quando um turno excede o teto de tokens e o usuário **não** autoriza o custo, a LLM recebe uma negativa:

```
{"negado": true, "motivo": "custo", "tokens_solicitados": 70000}
```

### 2.6 Orçamentos, tokens e cache

| Limite | Valor |
| --- | --- |
| Manifesto | 4.000 tokens (degrada para "só chaves"; depois trunca) |
| Histórico de diálogo | 10 mensagens / 8.000 caracteres |
| Ciclos do loop | 10 |
| Operações por turno | 8 |
| Teto de navegação por turno | 64.000 tokens |
| Cota de navegação acumulada | 32.000 tokens |
| Página de conteúdo pesado (`obter`) | 12.000 caracteres |
| Trecho por resultado de `buscar` | 200 caracteres |
| Resultados de `buscar` | 50 |
| Timeout de regex | 100 ms |
| Alerta de janela | acima de 80% da janela do modelo |

- A contagem de tokens usa o contador real do fornecedor quando disponível; sem ele, estima por `caracteres / 4`.
- O prefixo estável é reenviado a cada ciclo; quando o provedor suporta cache de prompt, o FlowScopeBR estima o `cache_hit` do prefixo caso o provedor não o reporte.
- Na barra de status (aba ativa), o contador exibe entrada (descontando cache), saída, o contexto da completion mais recente com percentual da janela e a cota de navegação (`nav: X/32K`).

### 2.7 Árvore de conhecimento (ramos)

A árvore é montada apenas a partir do cache local e exposta por caminhos canônicos. Os ramos correntes:

| Ramo | Conteúdo |
| --- | --- |
| `/flowscope` | `meta/<chave>` (apresentação, licença, versão, release, repositório), `abas/<aba>`, `abas/<aba>/subabas/<sub>`, `indicadores/<indicador>` |
| `/fundamentos` | `tickers`, `campos`, `valores/<ticker>` |
| `/documentos` | `<ticker>/indice`, `<ticker>/<chave>/curto`, `<ticker>/<chave>/longo`, `<ticker>/<chave>/texto` |
| `/guidance` | `<ticker>/indice`, `<ticker>/<ano>/<mes>/<guidance>` |
| `/direitos-obrigacoes` | `data-referencia`, `obrigacoes`, `direitos` → `titulos/<tipo>/<id>/{geral,adicionais,ltv,documentos}`, `agregado/resumo`, `sem-fonte` |
| `/noticias` | `grupos`, `<grupo>/indice`, `<grupo>/<chave>/titulo`, `<grupo>/<chave>/resumo`, `<grupo>/<chave>/texto` |

A árvore **não resume, não extrai, não baixa e não consulta a B3/CVM**; nós sem dado (pendentes de resumo ou extração) são omitidos em silêncio. Os limites de tokens por nó e por operação substituem os antigos tetos em caracteres.
