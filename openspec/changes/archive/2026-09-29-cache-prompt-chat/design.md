## Context

Ver `proposal.md - Why`. Em `consultar.py`, `_montar_prompt` (`:244`) concatena `INSTRUCAO_FORMATO`, conhecimento, fundamentos, resumos, texto integral opcional, fontes adicionais e a pergunta em uma única mensagem de usuário; `_completar` (`:234`) envia `[system_prompt, *historico, user]`. O `system_prompt` é apenas as instruções de `SYSTEM_PROMPT` (`:26`). O bloco de contexto é o maior volume e fica no fim. O cache de provedor é por prefixo.

O contexto estável é montado por `MontarContextoChat.montar` (`contexto.py:52`), combinando `conhecimento` (constante por versão), `montar_contexto_fundamentos` e `CascataDocumentos.montar_resumos`. As fontes adicionais (`fontes_adicionais`) dependem da pergunta e são voláteis. A change ativa `llm-chat-rag` adiciona a busca vetorial como mais uma fonte adicional, portanto também volátil.

## Goals / Non-Goals

**Goals:**
- Tornar o bloco estável um prefixo cacheável, idêntico byte-a-byte enquanto o contexto não mudar.
- Manter a composição das duas chamadas da cascata compartilhando prefixo e histórico.
- Preservar a informação enviada (mesmo conteúdo, outra posição).

**Non-Goals:**
- Alterar a porta `LLMPort` ou o adaptador (sem `cache_control`, sem telemetria de `usage`).
- Reduzir o volume do contexto (orçamento permanece em `documentos.py`).
- Reduzir o churn da poda do histórico (permanece 10 msgs / 8.000 chars).
- Aquecer o cache proativamente antes da primeira pergunta.

## Decisions

### Decisão 1: Prefixo estável no `system_prompt`

**Escolha**: o `system_prompt` enviado passa a ser `SYSTEM_PROMPT + INSTRUCAO_FORMATO + bloco_de_contexto_estável`, e o restante (histórico, sufixo) vai nas mensagens.

**Alternativas**: uma mensagem de contexto separada antes do histórico; manter o contexto na última mensagem.

**Razão**: mantém o contrato `complete(messages, system_prompt)`, evita múltiplas mensagens de sistema e cria um único prefixo contíguo estável. É exatamente o trecho que o provedor reaproveita.

### Decisão 2: Separar a montagem em prefixo e sufixo

**Escolha**: `_montar_prompt` é dividido em `_montar_prefixo(contexto)` (estável) e `_montar_sufixo(pergunta, fontes, texto_integral)` (volátil). O prefixo vai pelo `system_prompt`; o sufixo é a mensagem do turno atual.

**Alternativas**: manter a função única e apenas reordenar.

**Razão**: deixa explícita a fronteira cacheável e evita que conteúdo volátil entre no prefixo por descuido.

### Decisão 3: Revalidação por assinatura do contexto estável

**Escolha**: `MontarContextoChat` produz `(bloco_estavel, assinatura)`, onde a assinatura é derivada do conteúdo do bloco (conhecimento + fundamentos + resumos). O `ChatPanel` memoiza o último `(assinatura, bloco)` por conversa; a cada turno, se a assinatura casar, reusa o bloco byte-a-byte; caso contrário, reconstrói e aceita o miss.

**Alternativas**: congelar por snapshot de dados; congelar por sessão.

**Razão**: escolha do usuário — sempre fresco. O bloco já nasce estável no turno 1 porque `montar_resumos` gera os resumos sob demanda dentro do turno; o custo são misses pontuais quando fundamentos, watchlist ou resumos mudam. Memoizar pela assinatura garante byte-identidade e evita recomputo.

### Decisão 4: Fontes voláteis sempre no sufixo

**Escolha**: `fontes_adicionais` (RAG/notícias), o texto integral da escalada e a pergunta compõem o sufixo, após o histórico.

**Alternativas**: manter as fontes no bloco de contexto (como hoje).

**Razão**: elas dependem da pergunta; colocá-las no prefixo invalidaria o cache a cada turno. No sufixo, não afetam o prefixo estável.

### Decisão 5: Cascata compartilhando o prefixo

**Escolha**: ambas as chamadas de `consultar`/`_escalar` usam o mesmo `system_prompt` (prefixo) e o mesmo histórico; a segunda acrescenta o texto integral ao sufixo.

**Razão**: a segunda chamada reaproveita o cache da primeira; o item isolado que muda (texto integral) fica após o histórico.

### Decisão 6: Determinismo e conteúdo volátil fora do prefixo

**Escolha**: o bloco estável não pode conter timestamps, identificadores de sessão nem ordenação não determinística. A ordem de fundamentos segue a watchlist e a de resumos segue a do catálogo (já determinísticas). O conhecimento inclui versão/release, estáveis por versão do app.

**Razão**: qualquer variação espúria invalida o cache silenciosamente.

### Decisão 7: Testes headless do prompt

**Escolha**: verificar em `tests/test_application` (sem `DISPLAY`) que: o prefixo é idêntico entre turnos com contexto inalterado; conteúdo volátil fica no sufixo; a assinatura muda e reconstrói quando fundamentos/watchlist/resumos mudam; as duas chamadas compartilham o prefixo. O cache-hit real não é testável sem rede.

**Razão**: a forma do prompt é lógica de aplicação, alinhada ao `reduzir-testes-ui`.

### Decisão 8 (herdada): Porte do envio do chat para o manager

**Escolha**: esta change absorve a única pendência da task 5.5 de
`background-job-manager` — portar `chat/envio.py` para o `BackgroundManager`. O
detalhamento está na seção 5 de `tasks.md`.

**Esforço estimado**: ~4–6 h de implementação e ajuste de testes, mais ~1 h de
verificação. O trabalho concentra-se em:
- adicionar um callback genérico de evento (`ao_evento`) e o evento
  `Confirmacao` no manager (~30 linhas), preservando o handshake síncrono
  worker→Tk da confirmação de leitura;
- portar o envio para o grupo `"chat"` com política `latest_wins` e token por
  job, eliminando `_fila`/`_poll`/`_geracao` (~80 linhas);
- derivar `_processando` e os controles do ciclo de vida do manager e ajustar
  `_atender_confirmacao` (~30 linhas);
- adaptar ~8–12 testes de chat, sem aumentar o orçamento de `@needs_display`
  (ver `background-job-manager`).

**Riscos**: o handshake de confirmação é a parte mais delicada (exige o evento
genérico); o descarte de desfecho tardio passa a ser responsabilidade do
`latest_wins` do manager, coberto por teste dedicado.

**Razão**: o `cache-prompt-chat` já depende de `background-job-manager` para o
"envio do chat gerenciado e preparação do contexto" e toca o mesmo par de
arquivos (`chat/{chat_panel,envio}.py`), tornando-o o lugar natural para
concluir o porte sem abrir nova fatia.

**Restrições de implementação**:

- **Manager local ao painel**: o envio do chat DEVE usar um `BackgroundManager`
  próprio do `ChatPanel` (ou um manager sem listeners de ciclo de vida), nunca o
  manager global montado em `app_wiring`. O manager global publica
  `job_iniciado`/`job_terminado`, e o wiring os traduz em `presenter.enter/exit`
  e no botão de interromper; usar o global faria cada turno de chat alterar o
  cursor e os botões de toda a janela, quebrando a paridade observável e os
  testes de estado de botão. É a mesma escolha já feita para preview, config LLM
  e verificação de versão.
- **Ordem de implementação**: a seção 5 (porte do transporte) DEVE preceder as
  seções 1–4 (core do prompt). O core muda `_executar` para consumir
  `(bloco_estavel, assinatura)` de `MontarContextoChat`; o porte muda o mesmo
  `_enviar`/`_executar` para o manager. Fazer o core antes refaria essas funções
  duas vezes. Sequência: **seção 5 → seções 1–4**.

**Delta de spec**: a seção 5 não adiciona delta próprio. Políticas, token por
job, cancelamento, drenagem e ciclo de vida já são requisitos da capability
`background-jobs` introduzida por `background-job-manager`. O único
comportamento novo é o handshake de confirmação worker→Tk (`Confirmacao` +
callback genérico), ausente do spec original dessa capability. Como
`background-jobs` ainda não foi arquivada em `openspec/specs/`, registramos a
pendência aqui: o requisito do handshake DEVE ser incorporado ao spec de
`background-jobs` quando `background-job-manager` for arquivado — ou aceito como
delta `ADDED` desta change, caso ela seja aplicada depois daquela.

## Risks / Trade-offs

- **[Risco]** Reordenar o prompt alterar a qualidade das respostas → **Mitigação**: mesmo conteúdo, apenas posição; validar paridade observável com respostas equivalentes.
- **[Risco]** Mensagem de sistema grande (até ~10k tokens) → **Trade-off** aceito; o orçamento global já limita o volume e é o trecho cacheável.
- **[Risco]** Assinatura mudar com frequência (ex.: aquisição de documentos durante o chat) → **Trade-off** aceito; cada mudança custa um turno cheio e depois volta a cachear.
- **[Risco]** Cache do provedor expirar entre turnos espaçados → **Fora de escopo**; a reordenação não piora o caso atual.
- **[Risco]** `llm-chat-rag` colocar a fonte vetorial no bloco estável → **Mitigação**: spec exige fontes dependentes da pergunta no sufixo.

## Migration Plan

1. Portar o envio do chat para o `BackgroundManager` local do painel (seção 5 de
   `tasks.md`), fechando a task 5.5 de `background-job-manager`; validar a
   paridade observável do chat e rodar a suíte.
2. Dividir `_montar_prompt` em prefixo estável e sufixo volátil; compor o `system_prompt` com o contexto estável.
3. Expor `(bloco, assinatura)` em `MontarContextoChat` e memoizar por conversa no `ChatPanel`.
4. Posicionar fontes adicionais, texto integral e pergunta no sufixo.
5. Atualizar os deltas de `llm-chat-llm` e `llm-chat-context` e validar.
6. Cobrir com testes headless de forma do prompt (prefixo idêntico, voláteis no sufixo, invalidação) e rodar a suíte; rollback = reverter o commit.
