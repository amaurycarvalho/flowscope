## Context

Ver `proposal.md - Why`. Estado atual relevante:

- O catálogo de documentos é uma varredura de filesystem (`infrastructure/document_catalog.py`) sobre três raízes; não há índice de documentos.
- As notícias têm índice próprio (`infrastructure/b3/noticias_index.py`) e stores de resumo/texto particionados por ano/mês (`noticias_shards.py`).
- Os derivados por documento (resumo/texto) são JSON por ticker em `JsonDocumentSummaryStore`/`JsonDocumentTextStore`, que hoje não expõem remoção.
- Já existe convenção de hash de conteúdo no projeto (CVM): `hash_sha256` + `SHA256` sidecar + `metadata.json`, com preservação do `downloaded_at` quando o hash não muda.
- As vias de download de documentos/notícias são: `DocumentosRelevantesProvider.persistir`, `AquisicaoDocumentos._persistir_material_fact`, `InformeMensalArquivoProvider.persistir`, `BdrDividendProvider._obter_pdf` (fallback de dividendos, fora do botão "Atualizar") e `AquisicaoNoticias._persistir`.

## Goals / Non-Goals

**Goals:**

- Deduplicar conteúdo bruto por SHA-256, com registro por ticker (documentos) e global (notícias).
- Regra A: primeiro hash registrado vence, sem reordenação por data no download.
- Backfill de arquivos legados sem hash no "Atualizar", em ordem cronológica (mais antigo → mais recente).
- Poda dos derivados do item descartado (resumo, texto, índice de notícia).
- Cobrir todas as vias de download, inclusive o fallback de BDR.

**Non-Goals:**

- Deduplicação semântica/normalizada de HTML (apenas bytes exatos).
- Deduplicação entre tickers diferentes.
- Alterar o hash/cache das bases estruturadas da CVM (já têm hash e metadados próprios).
- Mudar o schema dos stores de resumo/texto existentes (apenas adicionar remoção).

## Decisions

### 1. Estrutura do registro: JSON por escopo, `hash -> caminho relativo`

Um arquivo por ticker para documentos (`document-hashes/<TICKER>.json`) e um global para notícias (`noticias/hashes.json`), no formato `{"schema_version": 1, "hashes": {"<sha256>": "<caminho relativo à raiz>"}}`.

- **Por quê**: a verificação "hash já existe?" é O(1) e o valor nomeia o canônico, necessário para validar existência e podar.
- **Alternativa descartada**: sidecar `SHA256` + `metadata.json` por arquivo (padrão CVM). Implica um arquivo extra por documento e não oferece uma lista global barata para o housekeeping.
- **Alternativa descartada**: mapa `caminho -> hash`. Determinaria "sem hash" por chave, mas a busca por hash seria O(N) por verificação.

### 2. Regra A (primeiro registrado vence) e ordenação do housekeeping

No download, se o hash existe (canônico válido), o novo arquivo não é gravado e seu registro é removido; senão, grava e registra. No housekeeping, os arquivos sem hash são processados do mais antigo para o mais recente, para que o sobrevivente das duplicatas legadas seja o mais antigo (intenção do requisito).

- **Por quê**: evita swap/evicção e mantém o registro como `set` de hashes com valor canônico.
- **Alternativa descartada (Regra B)**: manter sempre o mais antigo por data, inclusive no download — exigiria comparar datas e substituir o canônico já registrado (mais complexo e sem ganho pedido).
- **Custo aceito**: em ordem de download fora de ordem cronológica, vence o baixado primeiro, não o mais antigo.

### 3. Camadas

- **Domínio/aplicação (puro)**: política de decisão `avaliar_deduplicacao(hash, canonico_existe, caminho_atual) -> manter | descartar`, sem I/O; caso de uso de housekeeping que orquestra enumeração → hash → decisão via portas.
- **Aplicação (portas)**: `HashRegistryStore` (consultar/registrar/remover) e um enumerador de arquivos candidatos.
- **Infraestrutura**: `JsonHashStore` (gravação atômica + lock, padrão de `JsonDocumentSummaryStore`), `hash_sha256` compartilhado, remoção de arquivo por raiz e remoção de derivados nos stores.
- **Apresentação**: wiring no fluxo de "Atualizar" em background, antes de remontar.

Segue o padrão existente (portas em `application`, adaptadores JSON em `infrastructure`, políticas puras como `documentos/lote.py`).

### 4. Hooks de download

A decisão fica centralizada na política pura; cada provider faz: obter bytes → calcular hash → consultar registro → decidir.

- `DocumentosRelevantesProvider.persistir` e `AquisicaoDocumentos._persistir_material_fact`: gravar apenas se não for duplicata.
- `InformeMensalArquivoProvider.persistir`: idem.
- `BdrDividendProvider._obter_pdf`: se duplicata, **não gravar**, mas **retornar os bytes baixados** para a extração do dividendo continuar.
- `AquisicaoNoticias._persistir`: se duplicata, não gravar e não devolver `(caminho, meta)` para o índice.
- **Por quê**: o item de índice de notícia nasce do retorno de `_persistir`; suprimi-lo evita registrar a duplicata sem precisar reverter.

### 5. Remoção e poda

- `JsonDocumentSummaryStore` e `JsonDocumentTextStore` ganham `remover(ticker, chave)`; as subclasses de notícias traduzem o escopo para o shard.
- `NoticiasIndexStore` ganha `remover(relativo)`.
- Caches de arquivo (`DocumentosRelevantesCache`, `InformeMensalCache`, `PdfCache`, `NoticiasCache`) ganham remoção; ou a infraestrutura de housekeeping faz `unlink` direto, mantendo os caches como simples resolvedores de caminho.
- **Por quê**: sem poda, os stores acumulam órfãos e o chat (que lê o índice de notícias) mostraria itens removidos.

### 6. Guarda de conteúdo

Ignorar hash quando o conteúdo é vazio, só espaços (após decodificação para HTML/texto) ou menor que um piso (default sugerido: 1 KB), parametrizável.

- **Por quê**: evita que páginas genéricas curtas (`<html></html>`, placeholders) casem entre itens distintos e causem descarte indevido. O piso é conservador: documentos e artigos reais excedem 1 KB.

### 7. Validação do canônico

Antes de tratar como duplicata, verificar se o arquivo canônico existe; se não, remover o hash e prosseguir com o registro do novo.

- **Por quê**: sem isso, uma remoção manual do canônico bloquearia permanentemente o conteúdo.

### 8. Chave de "mais antigo"

- Documentos: `(ano, mes)` do caminho; desempate por `id` numérico quando aplicável e, por fim, caminho.
- Notícias: `data_publicacao` do índice; fallback `(ano, mes)` do caminho.
- **Por quê**: é a única data persistida para documentos (não há catálogo com data de referência); para notícias o índice já carrega a data.

## Risks / Trade-offs

- **Registro dessincronizado** (arquivo removido fora do app) → validação do canônico no momento da consulta.
- **Falsos positivos em conteúdo genérico pequeno** → guarda de conteúdo (piso mínimo).
- **Notícias com HTML volátil não deduplicam** → limitação aceita e documentada; só bytes exatos.
- **Custo do housekeeping de notícias** (até um ano de arquivos) → só arquivos sem hash são processados; a varredura é dirigida pelo índice.
- **Concorrência** (lote de resumos/preview lendo um arquivo que o housekeeping remove) → falhas toleradas por item; gravação do registro com lock e escrita atômica.
- **Duplicata removida enquanto ainda referenciada no índice** → a poda remove a entrada do índice na mesma operação.

## Migration Plan

- Não há migração de schema: o registro nasce vazio e os arquivos legados são hasheados no primeiro "Atualizar".
- Deploy: adicionar o registro e os hooks; sem necessidade de rebaixar cache existente.
- Rollback: desligar os hooks e apagar os arquivos de registro; os dados originais não são corrompidos (apenas duplicatas exatas podem ter sido removidas).

## Open Questions

- Valor definitivo do piso mínimo da guarda de conteúdo (1 KB sugerido) — ajustável sem impacto nos specs.
