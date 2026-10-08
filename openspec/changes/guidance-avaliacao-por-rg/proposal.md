## Why

A avaliação de guidance hoje é por FII, com um único valor "mais recente" e um portão de data: só reavalia quando o RG lido é posterior à data do guidance em cache. Isso impede que a análise de IA (mais capaz que o regex) cubra RGs já avaliados deterministicamente, e não distingue a origem nem registra os RGs que não têm guidance. O resultado é um cache que pode ficar preso a uma extração determinística antiga e que não acompanha a melhoria do provedor de chat.

## What Changes

- **BREAKING**: o cache de guidance por FII passa a ser um **ledger por RG**, com uma entrada por hash SHA-256 do PDF do Relatório Gerencial, registrando o **método** (`ia`/`deterministico`) e o **resultado** (guidance ou ausência avaliada).
- A avaliação deixa de ter portão de data: todo RG processado (ao ser lido ou ao ser resumido) é avaliado **uma vez por método**, **com exceção de falha na interação com a IA** (que não grava `ia` e mantém o RG elegível a nova tentativa).
- **IA prevalece sobre o determinístico** por RG; um resultado de IA sobrescreve a entrada determinística do mesmo RG.
- A avaliação segue a **cascata**: resumo curto → resumo longo → texto extraído, parando na primeira fonte que contém guidance; nenhuma delas contendo, o resultado é registrado como ausência para aquele RG.
- A **disponibilidade da IA** passa a ser "provedor de chat configurado". O flag `llm.guidance.enabled` é **removido** (descontinuado), eliminando a análise de guidance via LLM como recurso com controle próprio.
- O campo `Informações adicionais` continua lendo o cache, passando a exibir o guidance da entrada com **maior `data_relatorio`** entre as avaliadas com resultado (derivação do "guidance corrente", sem mudar o formato exibido).
- Migração do cache v1 (guidance único, sem origem): passa a ser lido como uma entrada `deterministico`.

## Capabilities

### New Capabilities

<!-- Nenhuma capability nova: a mudança é comportamental sobre capacidades existentes. -->

### Modified Capabilities

- `relatorio-gerencial-guidance`: ledger por RG (chave = hash), origem/proveniência, cascata de avaliação, fim do portão de data, avaliação por método, IA prevalecente com ressalva de falha, derivação do guidance corrente e migração do cache.
- `llm-config`: remoção do bloco/flag `llm.guidance.enabled`, que deixa de existir no arquivo de configuração.

## Impact

- Código (alterado): `application/avaliar_guidance.py`, `application/documentos/document_guidance.py`, `application/guidance_port.py`, `application/fundamental_analysis.py`, `infrastructure/guidance_store.py` (schema do ledger), `infrastructure/fii/guidance_extraction.py` (cascata/injeção), `infrastructure/content_hashes.py` (resolução do hash do documento), `presentation/gui/charts/document_flow_mixin.py` e `presentation/gui/resumos_job.py` (gatilho pós-resumo), `presentation/gui/app_wiring.py` (sem flag de guidance).
- Código (removido): flag `llm.guidance.enabled` e a exposição `guidance_llm_disponivel`; `Guidance` ganha origem (ou o resultado passa a carregar o método).
- Código (novo): resolução da identidade por hash do documento no catálogo; derivação do "guidance mais recente" a partir do ledger.
- Dependência: change `deduplicacao-por-hash` (registro `document-hashes/<TICKER>.json`) para a identidade por conteúdo.
- Sem novas dependências externas. Testes: reescrita/ajuste dos testes de avaliação, store, lote, leitura e renderização.
