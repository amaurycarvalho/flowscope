## Why

O mesmo conteúdo pode ser baixado e registrado mais de uma vez sob URLs, ids e datas diferentes — republicações de documentos (documentos relevantes, informe mensal, avisos de BDR) e notícias re-servidas em datas distintas. Hoje não há verificação por conteúdo: as raízes de documentos acumulam arquivos idênticos e o índice de notícias registra o mesmo artigo em chaves diferentes, poluindo as sub-abas "Documentos" e "Notícias". Falta um hash do conteúdo bruto e um housekeeping que mantenha apenas o registro mais antigo.

## What Changes

- Cálculo de **SHA-256 do conteúdo bruto** de cada documento/notícia baixado e verificação contra um **registro de hashes** antes de persistir.
- **Regra A (primeiro hash registrado vence)**: em colisão exata de conteúdo, o arquivo recém-baixado e o seu registro são descartados; o existente permanece. A comparação é feita pelo hash, sem reordenar por data.
- **Escopo do registro**: por ticker para documentos (compartilhado entre as três raízes — `bdr/`, `informe-mensal/`, `documentos-relevantes/`) e único global para notícias (escopo `NOTICIAS`), deduplicando inclusive entre seções.
- **Poda dos derivados** do item descartado: entrada de resumo, entrada de texto e, para notícias, a entrada do `index.json`.
- **Housekeeping no "Atualizar"**: varredura dos arquivos em cache **sem hash**, em ordem cronológica (mais antigo → mais recente), calculando o hash e aplicando a mesma regra para eliminar duplicatas legadas.
- **Hook de download em todas as vias**: documentos relevantes, informe mensal, avisos de BDR (fallback de dividendos, que deve continuar devolvendo os bytes para extração) e notícias.
- **Guarda de conteúdo**: corpos vazios, apenas espaços ou abaixo de um piso mínimo não entram no registro (evita descartar arquivos distintos por conteúdo genérico).
- **Validação do canônico**: se o arquivo canônico de um hash não existe mais, a entrada é descartada e o novo arquivo passa a ser registrado (evita bloqueio permanente após remoção manual).

## Capabilities

### New Capabilities

- `deduplicacao-conteudo`: hash SHA-256 do conteúdo bruto de documentos e notícias, registro de hashes por escopo, descarte de duplicata exata na aquisição, housekeeping por "Atualizar" e poda dos derivados.

### Modified Capabilities

- `documentos-ticker-panel`: o botão "Atualizar" da sub-aba "Documentos" passa a executar, além da aquisição, o housekeeping de deduplicação do ticker apresentado.
- `noticias-panel`: o botão "Atualizar" da sub-aba "Notícias" passa a executar, além da aquisição, o housekeeping de deduplicação global de notícias.

## Impact

- Código (novo): store de hashes em `infrastructure` (um por ticker para documentos, um global para notícias) com gravação atômica e lock; porta e política pura de deduplicação em `application`; caso de uso de housekeeping; helper de hash compartilhado.
- Código (alterado): `infrastructure/b3/documentos_relevantes.py`, `infrastructure/b3/informe_mensal_cache.py`, `infrastructure/b3/bdr/provider.py`, `infrastructure/b3/noticias_carga.py`; stores de texto/resumo (`document_texts.py`, `document_summaries.py`, `noticias_shards.py`) e índice (`noticias_index.py`) ganham operação de remoção; caches de arquivo (`DocumentosRelevantesCache`, `InformeMensalCache`, `PdfCache`, `NoticiasCache`) ganham remoção; wiring em `presentation/gui/app_actions.py` e `presentation/gui/noticias_actions.py`.
- Testes: novos testes de registro/hash, política de descarte, housekeeping e poda; ajuste em `test_documentos_aquisicao`, `test_noticias_aquisicao`, `test_bdr`, `test_app_actions` e `test_noticias_actions`.
- Sem novas dependências (`hashlib` da biblioteca padrão). Sem mudança no schema dos stores existentes.
- Limitação aceita: a deduplicação de notícias é por **bytes exatos**; o mesmo artigo re-servido com HTML diferente (chrome, timestamps) não é deduplicado.
