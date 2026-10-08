## Context

Ver `proposal.md` — Why. Estado atual relevante:

- `JsonGuidanceStore` (`infrastructure/guidance_store.py`) persiste um único `guidance` por ticker (schema v1), sem origem nem histórico.
- `AvaliarGuidanceUseCase` (`application/avaliar_guidance.py`) decide por data (`deve_avaliar`) e prefere a LLM se `llm.guidance.enabled` estiver ligado, caindo para o extrator determinístico.
- `GuidanceService` (`application/documentos/document_guidance.py`) é o portão de categoria/texto usado pela leitura (`document_flow_mixin._trabalhar`) e pelo lote (`resumos_job._preparar_textos`, fase 1).
- O gatilho de leitura/lote roda **antes** do resumo, então os resumos recém-gerados não estão disponíveis.
- `create_llm_provider`/`llm_configurada` já dizem se há provedor de chat; o flag vive em `infrastructure/llm/config.py` (`load_guidance_llm_enabled`, `save_guidance_llm_enabled`, `guidance_llm_disponivel`).
- O change `deduplicacao-por-hash` mantém `document-hashes/<TICKER>.json` no formato `{hash: caminho_relativo}` e `hash_sha256` em `infrastructure/content_hashes.py`.
- `DocumentoArquivo` (`domain/documents/entities.py`) não expõe hash; o catálogo (`infrastructure/document_catalog.py`) varre o filesystem e enriquece resumos.
- `AnaliseFundamental.guidance` é `Guidance | None`, lido sem cálculo em `application/fundamental_analysis.py`.

## Goals / Non-Goals

**Goals:**
- Trocar o cache único por um ledger por RG, com origem e resultado, sem tocar na carga nem na renderização da análise.
- Avaliar cada RG uma vez por método, com a IA prevalecendo sobre o determinístico, e a cascata resumo curto → resumo longo → texto.
- Remover o flag `llm.guidance.enabled`, passando a disponibilidade da IA a ser "provedor de chat configurado".
- Preservar o contrato de exibição: `AnaliseFundamental.guidance` continua sendo o guidance corrente, derivado do ledger.

**Non-Goals:**
- Reduzir o número de chamadas de IA na cascata (até 3 por RG) — otimização futura.
- Extrair valores presos a gráficos/imagens.
- Normalizar o período de validade em data canônica.
- Deduplicar RGs por conteúdo além do hash bruto já fornecido pelo change `deduplicacao-por-hash`.

## Decisions

### 1. Ledger por RG, com chave de hash e schema v2

Substituir o schema v1 por:

```json
{
  "schema_version": 2,
  "avaliacoes": {
    "<sha256-ou-caminho-relativo>": {
      "metodo": "ia" | "deterministico",
      "data_relatorio": "2026-08-01",
      "caminho_pdf": "...",
      "guidance": {
        "valor_min": "...", "valor_max": "...", "periodo": "..."
      }
    }
  }
}
```

`guidance` ausente/`null` representa ausência avaliada. A chave é o hash do PDF; sem hash, o caminho relativo.

- **Por quê**: a chave por conteúdo torna a entrada estável a re-baixamentos e é a base do controle "já avaliado".
- **Alternativas**: segunda estrutura de índice por RG separada do guidance (rejeitada: dois arquivos para sincronizar); manter por ticker sem chave (rejeitada: não distingue RGs).

### 2. Entidade de domínio `AvaliacaoGuidance`

Adicionar em `domain/fii` uma entidade imutável com `metodo`, `data_relatorio`, `caminho_pdf` e `guidance: Guidance | None`. `Guidance` permanece como está (valor + proveniência do relatório). A porta `GuidanceStore` ganha leitura/gravação de entradas; `obter(ticker)` passa a devolver o **guidance corrente derivado** (maior `data_relatorio` entre as entradas com `guidance`), preservando os consumidores atuais.

- **Por quê**: separa "resultado por RG" (domínio) de "guidance corrente" (derivado); evita espalhar a regra de maior-data.
- **Alternativas**: pôr `metodo` dentro de `Guidance` (rejeitada: mistura proveniência da extração com o resultado exibido) e derivar no store (rejeitada: regra de negócio em infraestrutura).

### 3. Identidade por hash com fallback para caminho

Resolver o hash do documento a partir do registro de `deduplicacao-por-hash`: inverter o mapa `{hash: caminho_relativo}` do ticker para `{caminho_relativo: hash}` e consultá-lo pelo caminho do arquivo. Sem hash registrado (legado ainda não backfillado), usar o caminho relativo como chave.

- **Por quê**: o registro já existe e é por ticker; evita re-hashear o PDF na avaliação.
- **Alternativas**: calcular `hash_sha256` do PDF a cada avaliação (rejeitada: relê o arquivo inteiro); sidecar por arquivo (rejeitada: diverge da convenção vigente).

### 4. Cascata de fontes

A avaliação percorre `short_summary` → `long_summary` → texto extraído, parando na primeira fonte com guidance. Na IA, "não encontrar" numa fonte é resposta negativa estruturada; no determinístico, ausência de match. Nenhuma fonte com guidance → registra ausência.

- **Por quê**: atende ao pedido e evita submeter o texto integral quando o resumo já basta.
- **Alternativas**: concatenar as três fontes numa única chamada (rejeitada: o pedido é explícito na ordem; concatenar encarece e dilui); avaliar só o texto (rejeitada: ignora a cascata pedida).

### 5. Controle de avaliação uma vez por método

O caso de uso consulta a entrada antes de avaliar: `ia` → não faz nada; `deterministico` + IA disponível → avalia por IA e substitui; `deterministico` + IA indisponível → não faz nada; sem entrada → IA se disponível, senão determinístico. Falha na interação com a IA não grava `ia` (cai no determinístico, se aplicável) e mantém o RG elegível.

- **Por quê**: evita repetição e implementa a precedência pedida.
- **Alternativas**: portão de data anterior (rejeitado: opção (a) escolhida); gravar `ia` mesmo em falha (rejeitado: travaria o RG sem resultado válido).

### 6. Disponibilidade da IA = provedor de chat configurado

Remover `load_guidance_llm_enabled`/`save_guidance_llm_enabled`/`guidance_llm_disponivel`/`DEFAULT_GUIDANCE_ENABLED`. A avaliação usa a `llm_factory` já injetada (a mesma dos resumos) e `llm_configurada()`; um bloco legado `llm.guidance` no `config.json` é ignorado e não é repersistido.

- **Por quê**: simplifica o desenho e remove um controle que deixou de existir.
- **Alternativas**: manter o flag como força-desligada (rejeitada: o pedido é descontinuá-lo).

### 7. Gatilho após a geração do resumo

Mover a avaliação do lote da fase 1 (`_preparar_textos`) para a fase 2, logo após `gerar_resumo_do_lote`, passando os resumos recém-gerados ao serviço de guidance. Na leitura (`document_flow_mixin._trabalhar`), avaliar após `_summary.gerar`, passando `short_summary`/`long_summary` do resultado (ou do catálogo, quando já houver). A chamada continua fora da thread do Tk e tolerante a falhas.

- **Por quê**: a cascata exige os resumos; a fase 2 já os tem em mãos.
- **Alternativas**: manter na fase 1 e reextrair/gerar resumos no gatilho (rejeitada: duplica e não cobre o resumo recém-criado).

### 8. Concorrência e escrita atômica

`JsonGuidanceStore` ganha `threading.Lock` (padrão de `JsonHashStore`) protegendo leitura-modificação-gravação, além da escrita atômica existente, porque leitura e lote podem avaliar RGs do mesmo ticker em threads distintas.

- **Por quê**: sem lock, duas avaliações concorrentes podem perder entradas no read-modify-write.
- **Alternativas**: confiar só na escrita atômica (rejeitada: não evita perda de entrada).

### 9. Migração do v1

`_carregar` reconhece `schema_version == 1` e constrói uma entrada `deterministico` de chave `legacy` com o `guidance` existente, mantendo o guidance corrente exposto. Na próxima gravação, o arquivo assume o schema v2.

- **Por quê**: preserva a informação já coletada sem exigir reavaliação.
- **Alternativas**: descartar o v1 (rejeitada: perde guidance válido).

## Risks / Trade-offs

- **[IA "não há guidance" apaga o determinístico do mesmo RG]** → comportamento pedido; mitigado por só sobrescrever em avaliação de IA **bem-sucedida** e por não afetar outros RGs.
- **[Custo: até 3 chamadas de IA por RG, em todo RG lido/resumido]** → a cascata para na primeira fonte; avaliar cada RG uma vez por método limita repetição. Otimização futura (ex.: reusar a chamada do resumo).
- **[Resumo gerado por IA alimentando a avaliação por IA]** → risco de circularidade/falso positivo; mitigado pelo prompt específico e pelo registro de proveniência `ia`.
- **[Sem hash para legado]** → chave de fallback por caminho pode duplicar entrada se o arquivo for rebaixado; mitigado pelo backfill de `deduplicacao-por-hash`.
- **[Remoção do flag é breaking]** → usuários que dependiam de desligar a avaliação por LLM perdem o controle; documentado na migration do `llm-config`.
- **[Duas avaliações concorrentes do mesmo RG]** → lock no store; última gravação consistente com o ledger completo.

## Migration Plan

- Mudança aditiva no domínio: `AvaliacaoGuidance` nova; `AnaliseFundamental.guidance` inalterado.
- O store lê v1 como entrada `deterministico` e regrava em v2 na primeira avaliação.
- Remover o flag e suas funções; wiring passa a usar `llm_configurada()` e a mesma fábrica de chat dos resumos.
- Rollback: restaurar o store v1 e o flag; como o ledger v2 não é lido pela versão anterior, o rollback exige limpar/degradar o arquivo para v1.

## Open Questions

- Reduzir chamadas da cascata (por exemplo, aproveitar a chamada de resumo para já responder ao guidance) sem alterar specs nem a abordagem — decidível na implementação.
