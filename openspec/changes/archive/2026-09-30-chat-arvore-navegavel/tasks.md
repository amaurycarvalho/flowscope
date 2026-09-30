## 1. Árvore de conhecimento e manifesto

- [x] 1.1 Criar `application/chat/arvore.py` com índice de caminhos em memória e resolução de nós (folha → conteúdo, interno → filhos), sem tocar rede/disco na listagem; verificar com testes de resolução por caminho e omissão de nós pendentes
- [x] 1.2 Expor os ramos `/flowscope/*` e `/fundamentos/*` como provedores de nós a partir do conhecimento e dos fundamentos; verificar que os caminhos canônicos resolvem e que tickers/campos aparecem nas listas
- [x] 1.3 Criar `application/chat/manifesto.py` renderizando o manifesto determinístico (persona, descrição, metadados curtos, protocolo, listas de chaves) com assinatura por hash de arquivos + mtime + watchlist; verificar determinismo byte-a-byte e reconstrução por mudança de assinatura
- [x] 1.4 Implementar a degradação para "só chaves" e o teto de 4.000 tokens, com teste de regressão em watchlist canônica; verificar que o teste falha se o teto for excedido
- [x] 1.5 Incluir o mapa dos caminhos canônicos no manifesto e omitir metadados redundantes (iguais ao nome); verificar que o mapa aparece e que o manifesto cabe no teto
- [x] 1.6 Criar nós internos por chave nos ramos grandes (`/documentos/<ticker>` com `curto`/`longo`/`texto`) e listar `/documentos/tickers` só com tickers que têm conteúdo; verificar por testes de árvore

## 2. Protocolo de navegação

- [x] 2.1 Criar `application/chat/protocolo.py` com parser tolerante (reuso do `_extrair_json`), validação das operações `listar`, `obter`, `contar`, `existe` e agregação determinística de resultados; verificar com LLM fake e testes de formato reconhecido/não reconhecido
- [x] 2.2 Implementar a resolução de operações da árvore e o bloco `[RESULTADO_NAVEGACAO]` sem timestamps; verificar ordem estável e ausência de campos voláteis
- [x] 2.3 Validar caminho inválido e operação desconhecida como erro estruturado que conta iteração sem encerrar o loop; verificar por teste do loop com resposta inválida
- [x] 2.4 Devolver erro de navegação com dica de recuperação (`nao_interno`→`obter`, `nao_folha`→`listar`, `caminho_invalido`→`existe`); verificar por testes de protocolo
- [x] 2.5 Registrar em log (`warning`) todo erro de navegação com operação, caminho, motivo e detalhe; verificar no cenário de `listar` numa folha
- [x] 2.6 Validar tipo/curinga dos campos (`tipo_invalido`, `caminho_com_curinga`), separar `regex_invalida` de `regex_bloqueada`, converter falhas inesperadas em `erro_interno` e dar dica em `buscar_semantico` sem índice; verificar por testes de protocolo
- [x] 2.7 Acionáveis adicionais: `curinga_invalido` (`contar` fora de `prefixo/*`), `campo_inexistente` em `em` com campos disponíveis, dica de busca vazia, `caminho_invalido` citando o pai concreto e `buscar_semantico` validando o caminho; verificar por testes de árvore/protocolo
- [x] 2.8 Acionáveis em notícias/documentos: `caminho_invalido` cita o ancestral existente mais próximo (chaves de notícia erradas) e `buscar` com campo carregado sob demanda (`texto`) não acusa `campo_inexistente`, orientando `obter`; verificar por testes de árvore

## 3. Loop de navegação

- [x] 3.1 Reescrever `application/chat/consultar.py` como loop de até 10 ciclos sobre `LLMPort`, mantendo prefixo/manifesto e histórico compartilhados; verificar resposta no primeiro ciclo e resposta após navegação
- [x] 3.2 Selecionar o histórico de diálogo (10 mensagens/8.000 caracteres) e os pares de navegação acumulados em cotas separadas, sem assistant órfão; verificar por testes de montagem do payload
- [x] 3.3 Garantir que o prefixo estável (manifesto) é idêntico entre turnos e ciclos; verificar com teste headless de prompt que compara byte-a-byte

## 4. Gates e negativa estruturada

- [x] 4.1 Implementar o gate de tokens de navegação por turno (64K) e a cota acumulada (32K, descarte em pares), parametrizáveis; verificar por testes de limiar
- [x] 4.2 Implementar o gate de iterações (10) com resumo final obrigatório e o limite de 8 operações por turno; verificar por teste de loop que atinge o teto
- [x] 4.3 Implementar a negativa estruturada (`{negado, motivo, tokens_solicitados}`) e a recusa de repetição do pedido negado; verificar por testes de motivos canônicos
- [x] 4.4 Implementar o gate de janela total a 80% com destaque no display; verificar atualização do rótulo durante o processamento

## 5. Busca com regex e segurança

- [x] 5.1 Adicionar `regex` ao grupo opcional `[llm]` e criar `application/chat/seguranca_regex.py` com timeout de 100 ms, bloqueio heurístico e fallback para `re` da stdlib com teto de padrão; verificar por testes de timeout e padrão catastrófico
- [x] 5.2 Implementar a operação `buscar` com limite de 50 resultados (`truncado: true`) e teto de varredura em disco (500 ms / 200 arquivos); verificar por testes de truncamento e varredura
- [x] 5.3 Adicionar índice invertido em memória para campos quentes (tickers e títulos); verificar que a busca comum não toca disco

## 6. Reuso, invalidação e notícias

- [x] 6.1 Reusar a navegação entre perguntas e descartá-la na mudança de assinatura, no "Limpar" e em `resetar_navegacao`; verificar por testes de reuso e invalidação
- [x] 6.2 Converter `application/chat/noticias.py` (e o índice/filtro de `noticias/fonte_chat.py`) em provedor do ramo `/noticias` com grupos, índice e nós de título/resumo/texto, sem filtro por pergunta nem confirmação de envio; verificar caminhos e omissão de pendentes
- [x] 6.3 Converter a cascata de documentos (`application/chat/documentos.py`) nos ramos `/documentos/<ticker>/{curto,longo,texto}`, cache-only; verificar que pendentes são omitidos

## 7. Remoção de `input_limitado` e deltas

- [x] 7.1 Remover `input_limitado` de `infrastructure/llm/config.py`, `presets.py` e `presentation/gui/llm/config_dialog.py`, ignorando a chave antiga na leitura; verificar por teste de config com chave legada
- [x] 7.2 Remover a caixa de seleção e o diálogo de confirmação de recursos iniciais da GUI; verificar abertura/salvamento do diálogo
- [x] 7.3 Remover `MANIFESTO_RECURSOS`, `_instrucao_limitada`, `_escalar` e `_escalar_sob_demanda` de `consultar.py`/`contexto.py`; verificar que dependências residuais não são mais referenciadas
- [x] 7.4 Atualizar o contador de tokens (`presentation/gui/chat/tokens.py`) para cotas separadas de diálogo e navegação e o rótulo `nav: W/32K`; verificar o formato do rótulo
- [x] 7.5 Ajustar o wiring da aba (`app_tab_layout.py`, `app_wiring.py`) para injetar a árvore e o protocolo; verificar a montagem ponta a ponta com LLM fake

## 8. Busca semântica (contrato)

- [x] 8.1 Expor a operação `buscar_semantico` no protocolo com backend opcional, retornando `indice_indisponivel` quando não houver índice; verificar que o manifesto e a assinatura não mudam com/sem backend
- [x] 8.2 Adicionar o ponto de injeção do backend vetorial sem introduzir dependência obrigatória; verificar que a árvore não importa `EmbeddingPort` nem o VectorStore

## 9. `llm-chat-rag` e RFC

- [x] 9.1 Atualizar `openspec/changes/llm-chat-rag/`: substituir o requisito "Fonte vetorial volátil no sufixo do prompt" pelo backend de `buscar_semantico`, ajustar design (Decisão 7 + risco) e re-apontar a dependência para `chat-arvore-navegavel`; verificar com `openspec validate llm-chat-rag`
- [x] 9.2 Corrigir o cabeçalho da RFC-015 para marcá-la como destino (não "funcionamento atual") e referenciar `chat-arvore-navegavel`; verificar leitura do documento

## 10. Verificação final

- [x] 10.1 Rodar `make lint` e `make test` (cobertura ≥ 85%) e corrigir regressões
- [x] 10.2 Rodar `openspec validate chat-arvore-navegavel --strict` e confirmar ausência de erros
