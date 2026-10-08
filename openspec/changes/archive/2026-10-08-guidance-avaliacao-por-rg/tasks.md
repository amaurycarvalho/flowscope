## 1. Domínio e porta

- [x] 1.1 Adicionar a entidade imutável `AvaliacaoGuidance` em `domain/fii` (metodo `ia`/`deterministico`, `data_relatorio`, `caminho_pdf`, `guidance: Guidance | None`) e exportá-la; verificar com testes em `tests/test_domain/test_fii/test_guidance.py` cobrindo presença e ausência de guidance
- [x] 1.2 Estender a porta `GuidanceStore` (`application/guidance_port.py`) com leitura/gravação de entradas por chave e ajustar `obter(ticker)` para devolver o guidance corrente derivado; verificar com `tests/test_application/test_guidance_port.py`

## 2. Persistência do ledger

- [x] 2.1 Reescrever `JsonGuidanceStore` (`infrastructure/guidance_store.py`) para o schema v2 `{schema_version, avaliacoes: {chave: entrada}}`, com `obter`, `obter_entrada`, `salvar_entrada` e derivação do guidance corrente; verificar com `tests/test_infrastructure/test_guidance_store.py`
- [x] 2.2 Implementar a migração do schema v1 (guidance único → entrada `deterministico` de chave `legacy`) e a regravação em v2; verificar com teste de leitura de arquivo v1 seguido de gravação
- [x] 2.3 Adicionar `threading.Lock` protegendo leitura-modificação-gravação preservando a escrita atômica; verificar com teste de duas gravações concorrentes que preserva ambas as entradas
- [x] 2.4 Garantir tolerância a ausência/corrupção/JSON inválido como ledger vazio; verificar com teste de arquivo corrompido

## 3. Identidade por hash

- [x] 3.1 Resolver o hash do documento a partir do registro de deduplicação (inversão de `{hash: caminho_relativo}` do ticker) com fallback para o caminho relativo; verificar com teste que um documento com hash registrado usa o hash e um sem hash usa o caminho
- [x] 3.2 Expor a identidade resolvida ao serviço de guidance sem re-hashear o PDF; verificar com teste que a avaliação não lê os bytes do arquivo para obter identidade

## 4. Caso de uso de avaliação

- [x] 4.1 Reescrever `AvaliarGuidanceUseCase` (`application/avaliar_guidance.py`) para consultar a entrada do RG e aplicar o controle uma vez por método (ia prevalece; determinístico reavaliado só com IA); verificar com `tests/test_application/test_avaliar_guidance.py`
- [x] 4.2 Implementar a cascata resumo curto → resumo longo → texto, parando na primeira fonte com guidance, para a IA e para o determinístico; verificar com testes de cada estágio e do caso "nenhuma fonte"
- [x] 4.3 Tratar falha na interação com a IA como não-gravação de `ia`, recorrendo ao determinístico e mantendo o RG elegível; verificar com teste de falha de `LLMPort`
- [x] 4.4 Garantir que uma avaliação de IA bem-sucedida que não encontra guidance registra ausência `ia` sem apagar o guidance de outros RGs; verificar com teste de ledger com múltiplas entradas

## 5. Disponibilidade da IA e remoção do flag

- [x] 5.1 Remover `load_guidance_llm_enabled`, `save_guidance_llm_enabled`, `guidance_llm_disponivel` e `DEFAULT_GUIDANCE_ENABLED` de `infrastructure/llm/config.py`; verificar com `tests/test_infrastructure/test_llm_config*` ajustados
- [x] 5.2 Ignorar silenciosamente um bloco legado `llm.guidance` e não repersisti-lo; verificar com teste de config com o bloco presente antes/depois da gravação
- [x] 5.3 Trocar o portão da avaliação pela condição "provedor de chat configurado" (`llm_configurada`/fábrica injetada); verificar com teste de IA indisponível que usa determinístico

## 6. Gatilhos de avaliação

- [x] 6.1 Mover a avaliação do lote (`presentation/gui/resumos_job.py`) da fase 1 para depois de `gerar_resumo_do_lote`, passando os resumos gerados; verificar com `tests/test_presentation/test_resumos_job.py` cobrindo ordem resumo→avaliação
- [x] 6.2 Avaliar na leitura (`presentation/gui/charts/document_flow_mixin.py`) após `_summary.gerar`, passando resumos do resultado ou do catálogo; verificar com `tests/test_presentation/test_document_flow.py` e `tests/test_presentation/test_document_guidance_flow.py`
- [x] 6.3 Atualizar `GuidanceService` (`application/documentos/document_guidance.py`) para o novo portão (sem data; com fontes) e mantê-lo tolerante a falhas; verificar com `tests/test_application/test_document_guidance.py`

## 7. Wiring e exibição

- [x] 7.1 Atualizar `presentation/gui/app_wiring.py` para remover o flag e injetar a fábrica de chat/disponibilidade na avaliação de guidance; verificar que a aplicação monta sem `guidance_llm_disponivel`
- [x] 7.2 Confirmar que `AnaliseFundamental.guidance` continua sendo preenchido pelo guidance corrente derivado, sem cálculo na carga/renderização; verificar com `tests/test_application/test_fundamental_guidance.py` e `tests/test_presentation/test_guidance_display.py`

## 8. Quality gate

- [x] 8.1 Rodar `make lint` e `make test` com sucesso; verificar que a cobertura permanece ≥ 85%
- [x] 8.2 Rodar `openspec validate guidance-avaliacao-por-rg` sem erros
