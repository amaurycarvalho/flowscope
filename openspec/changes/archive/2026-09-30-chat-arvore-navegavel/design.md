## Context

Ver `proposal.md` — Why. O chat hoje vive sobre o contrato `prefixo estável + sufixo volátil` da `cache-prompt-chat` (arquivada) e sobre a cascata de `llm-chat-llm`/`llm-chat-context` (arquivadas). A porta de domínio `LLMPort` (`domain/llm/ports.py`) e o `_extrair_json` tolerante (`application/chat/consultar.py`) já existem e são os pontos de reuso. A `llm-chat-rag` está planejada (0/39) e depende da `cache-prompt-chat`; sua implementação permanece postergável.

## Goals / Non-Goals

**Goals:**
- Expor o estado local como árvore navegável por caminho, cache-only, sem resumir/extrair durante o chat.
- Prefixo estável pequeno (manifesto) para cache-hit máximo; granularidade fina no sufixo.
- Protocolo JSON determinístico, provedor-agnóstico, testável offline com LLM fake.
- Controle de custo explícito: cotas de diálogo e navegação, gates de tokens e iterações.
- Ponto de extensão para a recuperação semântica futura sem alterar o protocolo.

**Non-Goals:**
- Implementar embeddings/índice vetorial (fica na `llm-chat-rag`, opcional).
- Persistir histórico entre sessões (sessão em memória por design).
- Suporte homogêneo a function calling nativo.
- Pré-processamento de documentos/notícias pendentes (o chat continua sem efeitos colaterais).

## Decisions

### 1. Árvore cache-only com índice em memória e conteúdo em arquivo

A árvore mantém um **índice de caminhos em memória** (`listar`/`contar`/`existe`/`obter` de metadados) e lê o **conteúdo pesado** (resumos, textos, notícias) do cache de arquivos sob demanda. A assinatura do estado é o hash do conjunto de arquivos + mtime + watchlist; quando muda, o manifesto é recomputado e a navegação acumulada é descartada.

*Alternativas consideradas:* carregar todo o conteúdo em memória (descartado: memória e custo de leitura em watchlists grandes); ler tudo do disco a cada operação (descartado: lento para `listar`/`contar`).

### 2. Protocolo JSON em texto, não function calling

A LLM emite `{"resposta", "solicitacoes":[{op,...}]}` e recebe `[RESULTADO_NAVEGACAO]`. Reutiliza o `_extrair_json` tolerante já existente.

*Alternativas consideradas:* function calling nativo (descartado: suporte heterogêneo entre presets, mais surface de segurança, ainda exige loop); RAG pré-fetch por turno (descartado como mecanismo geral: tira a seleção da LLM).

### 3. `buscar_semantico` é contrato da árvore; backend é opcional

A op existe no protocolo, mas a árvore **não** importa `EmbeddingPort` nem o VectorStore. Sem índice, retorna resultado estruturado vazio com `motivo: "indice_indisponivel"`. A `llm-chat-rag` fornece o backend depois, sem alterar o protocolo nem o manifesto.

*Alternativas consideradas:* a fonte RAG compor o sufixo volátil (descartado: conflita com a árvore e com o prefixo estável, era o desenho da `cache-prompt-chat`); adicionar a op só quando o RAG existir (descartado: obrigaria um segundo delta de protocolo e re-teste do loop).

### 4. Gates como contrato de comportamento, não de implementação

Orçamento por pergunta: manifesto ≤ 4K tokens; tokens de navegação por turno ≤ 64K (pede autorização); cota acumulada de navegação ≤ 32K (descarta os pares mais antigos); ≤ 10 iterações (pede autorização; ao esgotar, resumo final obrigatório); ≤ 8 operações por turno; `buscar` com timeout de 100 ms, ≤ 50 resultados, varredura ≤ 500 ms/200 arquivos; janela total alerta a 80%. A negativa volta à LLM de forma estruturada (`{negado, motivo, tokens_solicitados}`) e o worker recusa repetir o mesmo pedido negado.

### 5. Segurança de regex

Usar a biblioteca `regex` (único caminho com `timeout=`), adicionada ao grupo opcional `[llm]`; heurística bloqueia lookarounds aninhados, `.*` ilimitado e backreferences. Quando `regex` não estiver disponível, `buscar` degrada para `re` da stdlib com teto de tamanho de padrão, sinalizando a limitação.

### 6. Camadas e contratos

Apresentação (`ChatPanel`, `EnvioMixin`) não importa `infrastructure`; aplicação (`ArvoreConhecimento`, `ManifestoArvore`, `ProtocoloNavegacao`, `ConsultarChatUseCase`) não importa liteLLM; domínio mantém `LLMPort`/`ChatSession`/`ChatMessage`. A única porta para o provedor continua `LLMPort`.

### 7. Erros de navegação acionáveis e logados

Cada erro de navegação devolvido à LLM carrega um `motivo` canônico, um `detalhe` e, quando existe alternativa, uma **`dica`** de recuperação. Motivos cobertos e dicas:

| `motivo` | Disparo | Dica |
| --- | --- | --- |
| `nao_interno` | `listar` numa folha | use `obter(caminho)` |
| `nao_folha` | `obter` num nó interno | use `listar(caminho)` |
| `caminho_invalido` | caminho inexistente | use `existe(caminho)` ou liste o **ancestral existente mais próximo** |
| _campo pesado_ (não erro) | `buscar em=["texto"]` sem casamento | `texto` é carregado sob demanda; use `obter(caminho)` |
| `caminho_com_curinga` | `*` fora de `contar` | curinga só é aceito em `contar` |
| `curinga_invalido` | `*` em formato não suportado em `contar` | use um único `*` no final (`prefixo/*`) |
| `tipo_invalido` | `em`/`max`/`caminho`/`regex`/`consulta` com tipo errado | informe o tipo esperado |
| `campo_inexistente` | `em` nomeia campos ausentes no ramo | liste os campos disponíveis |
| `campo_ausente` | campo obrigatório ausente | inclua o campo |
| `op_desconhecida` | operação fora do protocolo | liste as operações válidas |
| `regex_invalida` | regex com sintaxe inválida | corrija a sintaxe |
| `regex_bloqueada` / `timeout_regex` | padrão catastrófico / lento | simplifique o regex |
| `erro_interno` | falha inesperada de uma operação | tente outra abordagem |

Além dos erros, resultados sem casamento em `buscar` trazem dica para ampliar a consulta; `caminho_invalido` cita o `listar(<pai>)` concreto; e `buscar_semantico` valida o caminho antes de devolver `indice_indisponivel` (com dica de usar `buscar`/`listar`). A validação de tipo/curinga ocorre antes de executar, evitando `TypeError` não tratado que derrubaria o loop; uma captura ampla converte falhas inesperadas em `erro_interno`. Todo erro é registrado em log (`warning`, logger `flowscope`) com operação, caminho, motivo e detalhe.

*Rationale:* a LLM observada tratou `nao_interno` como "bloqueado/indisponível" e desistiu da pergunta; a dica torna o erro auto-corretivo no ciclo seguinte, e o log permite diagnosticar padrões. *Alternativas consideradas:* erro genérico (induz à desistência); corrigir apenas no `SYSTEM_PROMPT` (mais frágil que a dica no próprio resultado); deixar a validação de tipo apenas na árvore (deixa exceções vazarem do loop).

### 8. Notícias como ramo da árvore

`/noticias/<grupo>/indice` e `/noticias/<grupo>/<chave>/{titulo,resumo,texto}` substituem o índice filtrado por pergunta e a escalada em duas camadas. O filtro determinístico `filtrar_por_pergunta` deixa de existir; a LLM usa `buscar`/`listar`.

*Trade-off:* perde-se a filtragem barata por pergunta; ganha-se uniformidade com o protocolo. Se o custo de navegação de notícias se mostrar alto, uma poda opcional pode voltar como otimização de apresentação, sem mudar o contrato dos nós.

### 9. Manifesto descreve o mapa da árvore e omite metadados redundantes

O manifesto inclui um **mapa dos caminhos canônicos** de cada ramo (`/fundamentos/valores/<ticker>`, `/documentos/<ticker>/{curto,longo,texto}`, `/noticias/<grupo>/indice`, ...), além das listas de chaves. Metadados iguais ao nome do nó são omitidos. Ramos grandes ganham **nó interno por chave** (`/documentos/<ticker>`) em vez de uma listagem plana.

*Rationale:* sem o mapa, a LLM não sabia que documentos/notícias vivem sob subcaminhos e passou a adivinhar (`/fundamentos/GGRC11`, `/flowscope/GGRC11`), concluindo que "não havia dados". O mapa orienta a navegação; a omissão de metadados redundantes (campos repetidos) evita inflar o teto de 4K; o nó interno por ticker torna `listar` útil. *Alternativas consideradas:* expor cada caminho como chave (inviável: milhares de notícias); injetar o conteúdo dos resumos no manifesto (contradiz o prefixo estável pequeno).

## Risks / Trade-offs

- **[Risco] Custo/latência maiores que a cascata em watchlists pequenas** (N idas-e-vindas vs 1 chamada) → gate de tokens, `contar`/`existe` antes de `listar`, `LATEST_WINS`; medir com LLM fake e reavaliar limiares.
- **[Risco] Cache-hit depende de o provedor cachear o prefixo crescente (inclui turnos de navegação)** → manter a ordem `manifesto → diálogo → navegação acumulada → turno corrente`; para provedores sem cache a RFC documenta que o ganho é menos tokens, não desconto.
- **[Risco] LLM não segue JSON estrito** → `_extrair_json` tolerante + fallback textual + retry único; erro de protocolo volta estruturado e conta iteração.
- **[Risco] ReDoS / `regex` indisponível** → `regex` com timeout + bloqueio heurístico + fallback stdlib com teto de padrão.
- **[Risco] Metadados curados do manifesto divergirem dos dados** → teto de 4K tokens, degradação para "só chaves", teste de regressão em watchlist canônica.
- **[Risco] Staleness por reuso de navegação** → invalidação por assinatura de estado + `resetar_navegacao` + "Limpar".
- **[Trade-off] `buscar_semantico` sem backend** → retorna vazio estruturado; sem regressão enquanto a `llm-chat-rag` não for implementada.

## Migration Plan

1. `llm-chat-tree`: árvore + manifesto + protocolo (`listar`/`obter`/`contar`/`existe`), sem `buscar`.
2. `llm-chat-llm`: loop de navegação substitui a cascata; contadores e cotas separados.
3. Gates de tokens/iterações + negativa estruturada.
4. `buscar` + `seguranca_regex`.
5. Reuso + invalidação por mudança de estado; notícias como ramo.
6. Remoção de `input_limitado`, do gate antigo e dos tetos em caracteres; deltas em `llm-config`/`llm-gui`/`llm-chat-tokens`/`llm-chat-context`.
7. `buscar_semantico` (contrato; backend vazio).
8. `llm-chat-rag`: ajuste de planejamento (integração → node backend; dependência → `chat-arvore-navegavel`); implementação postergável.
9. Rollback: manter a cascata atrás do flag de migração até o loop estabilizar; a remoção de `input_limitado` é tolerante à chave antiga.

## Open Questions

- Nome final da op de busca semântica (`buscar_semantico` é provisório) — não altera o contrato, só o vocabulário.
- `regex` no grupo `[llm]` vs dependência base — decisão de empacotamento, sem impacto de comportamento.
