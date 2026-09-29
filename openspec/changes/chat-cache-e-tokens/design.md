## Context

Ver `proposal.md` — Why. O estado atual relevante:

- `CascataDocumentos.preparar_resumo` gera resumo via LLM e `_preparar_texto_documento` extrai texto sob demanda (cache miss), ambos durante o chat.
- `FonteNoticias.__call__` ignora a pergunta e anexa o índice inteiro (até 32.000 ch) no sufixo volátil, reenviado em toda chamada.
- `ConsultarChatUseCase` resolve cada pergunta em até duas chamadas: prefixo estável (instruções + conhecimento + fundamentos + resumos) e sufixo (fontes + pergunta); a escalada acrescenta o texto integral e **reenvia** o índice de notícias.
- `LLMPort.complete(...) -> str`; o adaptador descarta `response.usage`.
- O `BackgroundManager` encerra por inatividade após 120 s; chamadas longas e a espera da confirmação (timeout de 300 s) disparam o watchdog e reativam o botão "Enviar".

## Goals / Non-Goals

**Goals:**

- Tornar o chat estritamente leitor de cache: nenhuma geração de resumo, embedding ou extração de texto durante a consulta.
- Minimizar o sufixo volátil, sobretudo o índice de notícias, com filtro determinístico e gate de confirmação.
- Expor o gasto de tokens do chat em rótulo persistente e restrito à aba.
- Impedir que chamadas longas sejam encerradas por inatividade.

**Non-Goals:**

- Não implementar busca semântica/embeddings (permanece no `llm-chat-rag`).
- Não alterar o pipeline de aquisição/resumo em lote (ação do usuário nas abas Documentos/Notícias).
- Não persistir o histórico nem o contador entre execuções.
- Não introduzir novo provedor ou dependência.

## Decisions

### 1. Cascata em 2 rodadas (bloco de resumos curto+longo e, depois, texto)

A primeira chamada leva os resumos cacheados (curto+longo) em um único prefixo estável; a segunda, sob pedido da LLM, o texto integral cacheado. Alternativa considerada: 3 rodadas literais (curto → longo → texto). Rejeitada porque as chamadas são stateless (a rodada do longo não "lembraria" do curto sem reenviá-lo), porque separar curto e longo cria **dois prefixos** distintos e enfraquece o cache de prompt recém-conquistado, e porque adiciona uma rodada de rede no caminho comum. A redação "curto+longo em bloco, depois texto" passa a ser a descrição da cascata.

### 2. Política cache-only e omissão silenciosa de pendentes

Remover de `CascataDocumentos` a chamada a `ResumirDocumentoUseCase` e a extração por `texto_preview`; ler apenas `_summary_store`/`_text_store`. Pendente = ausente do contexto, sem citação e sem aviso. Alternativas: (a) catálogo de chaves para tornar pendentes citáveis — rejeitada por exigir camada extra, rodada adicional e chaves curtas; (b) aviso determinístico na statusbar — rejeitada em favor da omissão silenciosa. A uniformização estende a mesma regra às notícias.

### 3. Índice de notícias filtrado, restrito a recuperáveis, com gate

`FonteNoticias` passa a: (i) listar apenas itens com resumo ou texto em cache; (ii) aplicar filtro determinístico por regex sobre a pergunta, extraindo tickers (padrão já existente em `structured_extractor`) e palavras-chave e casando com o título normalizado (`normalizar_texto`); (iii) se o subconjunto exceder um limite de envio automático, pedir confirmação pelo canal já existente do worker (`ctx.confirmar` → diálogo no Tk); (iv) sem casamento, omitir a seção. O filtro reusa a normalização e os padrões de `domain/noticias/classificacao.py`.

### 4. Segunda chamada sem o índice volátil

`ConsultarChatUseCase._montar_sufixo` deixa de reanexar as `fontes` na escalada; o sufixo da segunda chamada contém apenas o texto integral resolvido e a pergunta. Os resumos já estão no prefixo estável, então a rodada permanece coerente sem reenviar o índice.

### 5. Porta devolve texto + uso (`LLMResposta`/`LLMUsage`)

`LLMPort.complete` passa a devolver `LLMResposta(texto, LLMUsage(entrada, saida))`; o adaptador lê `response.usage` com tolerância a ausência. Alternativas: callbacks/atributo "último uso" (frágil, estado mutável compartilhado) e decorador medidor (não resolve a ausência do dado na porta). A mudança é **BREAKING** e atualiza os 4 consumidores (`consultar`, `resumo_documento`, `avaliar_guidance`, `config_dialog`).

### 6. Contador mede somente as completions do chat

Como o chat deixa de disparar resumos (decisão 2), não há chamadas ocultas: o total da sessão é a soma das completions do `ConsultarChatUseCase`. Isso dispensa instrumentar a fábrica de LLM. O acumulador vive no `ChatPanel`, zera em `limpar()`/`__init__`, e é atualizado a cada completion via callback (`ao_uso` → `Progresso` → handler na thread do Tk).

### 7. Rótulo persistente na barra de status, restrito à aba

Novo callback do painel para o rótulo (`tokens`), com o `StatusMixin` dono de um `tk.Label` na `_status_frame` (pack à direita). Visibilidade alternada em `_on_tab_changed` para a aba "Chat AI"; o texto formatado em `K` com 1 casa é independente do `_status_var`, então não é sobrescrito por outras operações e persiste após "Pronto.".

### 8. Watchdog não encerra chamadas longas

O worker publica um heartbeat periódico (`ctx.progress`) enquanto a completion e a espera da confirmação estiverem em andamento, mantendo `ultima_atividade` fresco. Alternativas: subir o `LIMITE_INATIVIDADE_S` global (atrasa a detecção de travas reais) e limite por job (não cobre a espera da confirmação sem mais plumbing). Complementarmente, `_enviar` marca o estado "enviando" antes de `_registrar`, fechando a janela de `_processando=False` entre registrar e submeter.

## Risks / Trade-offs

- [Perguntas amplas podem perder notícias] → o filtro inclui termos de evento além de tickers; a omissão é o comportamento acordado e o usuário pode reformular com termos presentes nos títulos.
- [Chaves de documento longas e frágeis] → mantém-se o bloco de resumos como primeira camada (a LLM já reproduz as chaves hoje); não se introduz catálogo, evitando expor mais chaves.
- [Mudança BREAKING da porta] → atualizar os 4 chamadores no mesmo commit; testes existentes da porta/adaptador ajustados.
- [Heartbeat e ciclo de vida da thread] → o heartbeat é um contexto curto que para ao fim da chamada; não deve manter o job ativo se o worker morrer.
- [Filtro determinístico com falso negativo] → trade-off aceito; sem casamento a seção é omitida, não se envia o índice completo.
- [Cache de prompt] → a segunda chamada mantém o mesmo prefixo estável; remover o índice do sufixo não altera o prefixo.

## Migration Plan

Não há migração de dados: os caches de resumo/texto e as configurações permanecem. A mudança é de comportamento em tempo de execução. Reversão: reverter o commit restaura a preparação sob demanda e o índice completo.

## Open Questions

- Valor exato do limite de envio automático do índice de notícias (ponto de partida ~600 tokens) e a unidade de medida (tokens estimados por caracteres).
- Formato final do rótulo (rótulos "entrada"/"saída", separador) e tratamento de valores abaixo de 1000.
