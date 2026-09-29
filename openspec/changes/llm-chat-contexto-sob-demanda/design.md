## Context

Ver `proposal.md` — Why. Hoje `MontarContextoChat._renderizar_bloco` (`application/chat/contexto.py:125`) concatena conhecimento, fundamentos e resumos no bloco estável, e `ConsultarChatUseCase` (`application/chat/consultar.py`) resolve a pergunta em até duas chamadas, escalando para o texto integral via `documentos_solicitados`. A configuração por provedor guarda `api_url`, `model`, `api_key` e `rpm` (`_CHAT_FIELDS`, `infrastructure/llm/config.py:30`), com memória por provedor no diálogo. O bloco de conhecimento sozinho soma ~5,6k tokens, reenviado a cada completion.

## Goals / Non-Goals

**Goals:**

- Permitir declarar, por provedor/modelo, que a janela de entrada é limitada.
- Com o flag ativo, não enviar conhecimento, fundamentos e resumos no prefixo; carregá-los apenas sob solicitação explícita da LLM, com gate de confirmação próprio.
- Preservar intacto o comportamento atual quando o flag está desligado.

**Non-Goals:**

- Não alterar a cascata de documentos existente (texto integral) para o caso sem flag.
- Não introduzir indexação vetorial nem novas fontes de contexto.
- Não detectar automaticamente a limitação de janela (é declaração do usuário).

## Decisions

### D1: Flag `input_limitado` por provedor

Adicionar `input_limitado: bool` (default `False`) à entrada de cada provedor em `llm.chat.providers`. `_CHAT_FIELDS` passa a incluí-lo (com coerção booleana em `_normalizar_provedor`), e `save_llm_config`/`load_provider_configs` o preservam por provedor. O diálogo ganha um `Checkbutton` e o carrega/salva no fluxo existente (`_coletar_campos_provedor`, `_carregar_provedor`).

**Alternativas:** flag global (o problema é por modelo); inferir pela cota do provedor (não confiável e específico de conta).

### D2: Bloco estável enxuto + manifesto de recursos

Com o flag ativo, `_renderizar_bloco` omite as seções `## Conhecimento do FlowScope`, `## Fundamentos carregados` e `## Resumos de documentos` e inclui uma seção de manifesto listando os recursos disponíveis (`conhecimento`, `fundamentos`, `resumos`) e a instrução de como solicitá-los. O prefixo resultante continua estável e cacheável; a assinatura passa a refletir o manifesto.

**Alternativas:** remover as seções por completo (a LLM não saberia que existem); manter só o conhecimento (não resolve a cota).

### D3: Recursos servidos pela mesma cascata

Estender `ContextoChat`/`ContextoDocumental` com os recursos iniciais como alvos resolvíveis (chave → texto de exibição + conteúdo). A lista `documentos` da resposta estruturada passa a aceitar tanto chaves de recursos quanto chaves de documentos; a resolução prioriza recursos e depois documentos. As chaves de recurso são reservadas e documentadas no manifesto e na instrução de formato.

**Alternativas:** um terceiro campo JSON (`recursos`) separado (mais rígido e mais uma peça no contrato tolerante); um segundo caso de uso (duplicaria a orquestração).

### D4: Orçamento de até três chamadas com o flag ativo

```
flag OFF (hoje, 2 chamadas)          flag ON (até 3 chamadas)
1) prefixo estável + pergunta        1) prefixo (manifesto) + pergunta
   -> resposta OU pede docs             -> resposta OU pede {recursos/docs}
2) texto integral dos docs           2) recursos pedidos
                                        -> resposta OU pede docs
                                     3) texto integral dos docs
```

Sem o flag, o comportamento atual é preservado. Com o flag, a chamada 1 não tem os resumos; a chamada 2 carrega os recursos pedidos; a chamada 3 lê o texto integral dos documentos. O prefixo estável e o histórico são compartilhados por todas as chamadas.

**Alternativas:** manter 2 chamadas (a LLM não conseguiria pedir recursos e depois documentos na mesma pergunta).

### D5: Gate de confirmação próprio para recursos

O gate atual monta a mensagem de "texto integral de N documentos". Recursos iniciais usam uma mensagem própria (ex.: carregar os dados iniciais do FlowScope). A confirmação passa a carregar um motivo/tipo que a apresentação usa para escolher o texto, mantendo o callback único. O gate de documentos permanece inalterado.

**Alternativas:** reaproveitar o texto de documentos (enganoso); não confirmar recursos (o usuário pediu gate explícito).

## Risks / Trade-offs

- [A LLM pode não pedir os recursos e responder pior] → manifesto e prompt de sistema explícitos sobre a existência e as chaves; fallback tolerante já existente trata JSON não reconhecido.
- [Mais uma chamada aumenta latência e tokens de saída] → só com o flag ativo; a economia de entrada compensa em modelos com cota apertada.
- [Colisão entre chave de recurso e chave de documento] → chaves de recurso reservadas e documentadas; resolução prioriza recursos.
- [Diálogos de confirmação extras incomodam] → texto conciso e específico; o gate de documentos não muda.
- [Duas mudanças tocam `llm-config`] → campos distintos (`input_limitado` aqui, `context_window` na change A); reconciliar ao arquivar, se ambas estiverem ativas.

## Migration Plan

1. Estender a config (`_CHAT_FIELDS`, normalização, save/load) com default `false`.
2. Adicionar o checkbox no diálogo e o fluxo de memória por provedor.
3. Tornar o bloco estável condicional ao flag e montar o manifesto.
4. Estender `ContextoChat`/`ContextoDocumental` com recursos e o gate próprio.
5. Elevar o orçamento da cascata para 3 com o flag e ajustar o wiring.
6. Atualizar specs e testes; sem migração de `config.json`.

## Open Questions

- Nenhuma bloqueante. Os nomes literais das chaves de recurso e do texto de confirmação ficam a critério da implementação.
