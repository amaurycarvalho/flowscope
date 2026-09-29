## Why

O cache de prompt dos provedores é por **prefixo**: reutiliza o maior trecho inicial byte-a-byte idêntico a uma chamada anterior. Hoje o `ConsultarChatUseCase` coloca todo o contexto (conhecimento, fundamentos e resumos) dentro da **última mensagem do usuário**, depois do histórico — ou seja, no fim do prompt, fora de qualquer prefixo cacheável. Esse bloco pode chegar a ~10k tokens (teto global de 40.000 caracteres) e é reenviado a preço cheio em todo turno; na escalada, a segunda chamada reenvia o mesmo contexto inteiro. Reordenar o prompt para tornar o trecho estável um prefixo cacheável reduz o custo de tokens ao longo do chat.

## What Changes

- Reordena o prompt do chat em **prefixo estável + sufixo volátil**: o prompt de sistema passa a conter as instruções e o contexto estável (conhecimento + fundamentos + resumos); o histórico segue depois; e o sufixo (fontes adicionais por pergunta, texto integral da escalada e a pergunta) fica no fim.
- **Memoiza** o bloco de contexto estável com **revalidação por assinatura**: reusa o texto renderizado byte-a-byte enquanto a assinatura (conhecimento + fundamentos + resumos) não muda; reconstrói e aceita o miss quando muda.
- Mantém as fontes voláteis (busca vetorial/notícias do `llm-chat-rag`) e a pergunta sempre no sufixo, sem invalidar o prefixo.
- As duas chamadas da cascata compartilham o prefixo estável + histórico.
- Não altera a porta `LLMPort` nem o adaptador: a melhoria é provider-agnóstica (OpenAI/Gemini/DeepSeek aproveitam automaticamente).
- Conclui o porte do envio do chat para o `BackgroundManager` (única pendência da task 5.5 de `background-job-manager`): o `ChatPanel` deixa de manter thread/fila/poll/generation próprios e passa a derivar o estado dos controles do ciclo de vida dos jobs.

## Capabilities

### New Capabilities
<!-- Nenhuma: estende o prompt e o contexto já definidos. -->

### Modified Capabilities
- `llm-chat-llm`: o prompt passa a ter um prefixo estável (instruções + contexto) cacheável, com histórico e conteúdo volátil no sufixo, e o prefixo é compartilhado pelas duas chamadas da cascata.
- `llm-chat-context`: o bloco de contexto estável é renderizado de forma determinística e revalidado por assinatura, sendo reusado enquanto o conteúdo não muda.

## Impact

- `src/flowscope/application/chat/consultar.py`: separar `_montar_prompt` em prefixo estável e sufixo volátil; `_completar` envia o prefixo pelo `system_prompt` e o sufixo na mensagem do turno atual.
- `src/flowscope/application/chat/contexto.py`: expor o bloco estável e a assinatura para memoização; separar fontes voláteis.
- `src/flowscope/application/chat/documentos.py`: leitura dos resumos como parte do bloco estável (a geração sob demanda continua).
- `src/flowscope/presentation/gui/chat/{chat_panel,envio}.py`: manter a memoização do bloco estável por conversa e concluir o porte do envio para o `BackgroundManager` (seção 5 de `tasks.md`).
- Deltas em `openspec/specs/llm-chat-llm/spec.md` e `openspec/specs/llm-chat-context/spec.md`.
- **Dependências**: `background-job-manager` (envio do chat gerenciado e preparação do contexto — esta change conclui o porte deixado pendente pela task 5.5 daquela), `carga-principal-background` e `leituras-catalogo-background` (definem quando fundamentos e resumos mudam, gatilho da assinatura), `reduzir-testes-ui` (testes headless do prompt).
- **Coordenação**: `llm-chat-rag` (fonte adicional por pergunta, que deve permanecer no sufixo).
- Sem impacto em `domain` e `infrastructure`.
