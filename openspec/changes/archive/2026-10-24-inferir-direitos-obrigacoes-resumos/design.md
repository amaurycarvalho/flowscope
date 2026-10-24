## Context

Os resumos longos já são persistidos pelo lote de `executar_resumos` e ficam disponíveis no catálogo do ticker (`DocumentoArquivo.long_summary`). O ramo de direitos e obrigações é montado a partir de um cache oficial por ticker (`RepositorioTitulosJson`) e exposto tanto pela GUI quanto por `FonteDireitosObrigacoes` no Chat AI. A árvore é estritamente cache-only.

Ver `proposal.md` para motivação e os specs para requisitos. Este documento fixa as decisões técnicas.

## Goals / Non-Goals

**Goals:**

- Extrair itens estruturados dos resumos longos já existentes, com evidência e proveniência.
- Persistir em cache separado, idempotente e invalidável por documento/versão de prompt.
- Integrar a fase ao lote "Resumir pendentes" (GUI e CLI) sem alterar a extração de texto.
- Exibir itens inferidos na árvore sem competir com o dado oficial.

**Non-Goals:**

- Inferir a partir do PDF integral ou de documentos sem resumo.
- Substituir, completar ou corrigir silenciosamente dados oficiais.
- Executar inferência no carregamento da aba, na navegação do Chat AI ou no botão "Atualizar".
- Cobrir ações; o foco são FIIs com Relatório Gerencial e informe mensal.

## Decisions

### 1. Caso de uso próprio, separado do serviço de resumo

Criar `InferirDireitosObrigacoesUseCase` na camada de aplicação, com dependências explícitas:

- catálogo/resumos já persistidos;
- repositório oficial de títulos do ticker;
- porta `LLMPort`;
- repositório de inferências;
- flag de configuração e versão do prompt.

Alternativa descartada: acoplar ao `DocumentSummaryService`, que passaria a ter duas responsabilidades e misturaria invalidação de resumos com a de inferências.

### 2. Entrada limitada aos resumos elegíveis

A seleção considera apenas documentos cujo `long_summary` está persistido e cuja categoria/tipo representa Relatório Gerencial ou informe mensal do FII. O texto enviado é o resumo longo, truncado por orçamento, sem reabrir PDF. Documentos sem resumo ou com resumo truncado não entram na fase; permanecem elegíveis ao próximo lote.

Alternativa descartada: usar o texto integral em cache; aumentaria custo, latência e risco de exceder o contexto sem ganho proporcional.

### 3. Contrato de resposta e validação estrita

A LLM recebe um prompt de sistema estável (para cache de prompt) e uma entrada compacta com ticker, documento e resumo. A resposta DEVE ser JSON com uma lista de itens contendo:

```text
tipo, papel, descricao, documento, trecho, confianca
```

O adaptador valida tipos do enum de renda fixa e papéis conhecidos, descarta itens sem evidência/documento e limita a quantidade por chamada. Falha de parse é tratada como resposta inválida, não como erro fatal do lote.

Alternativa descartada: texto livre convertido por heurística; baixa previsibilidade e difícil auditoria.

### 4. Cache separado e idempotente

Arquivo `<cache>/direitos-obrigacoes/inferencias/<TICKER>.json`:

```json
{
  "ticker": "HGLG11",
  "parser_version": "direitos-obrigacoes-inferencia-v1",
  "atualizado_em": "...",
  "itens": [
    {
      "tipo": "CRI",
      "papel": "direito",
      "descricao": "...",
      "documento": "Relatorio Gerencial ...",
      "chave_documento": "...",
      "hash_resumo": "...",
      "trecho": "...",
      "confianca": 0.82,
      "data_referencia": "2026-09-30",
      "fonte": "LLM"
    }
  ]
}
```

- A chave de idempotência é `(chave_documento, hash_resumo, parser_version)`.
- Só documentos com hash/versão diferentes geram nova chamada.
- A escrita é atômica e preserva itens de documentos não reprocessados.
- O cache oficial não é alterado; a leitura combina os dois na apresentação.

### 5. Elegibilidade por cobertura oficial e flag

A fase só roda quando:

- `renda_fixa.inferir_no_resumo` é `true`;
- a LLM está configurada e funcional;
- existe ao menos um resumo elegível ainda não inferido;
- a cobertura oficial do ticker está vazia ou parcial (há `sem-fonte` ou nenhum título para um papel/tipo relevante).

A flag é lida por `feature_flag`, compartilhada por GUI e CLI, e desligada por padrão até a feature ser validada.

### 6. Precedência e apresentação

A leitura combinada usa o dado oficial primeiro. Um item inferido só é exibido se não houver item oficial equivalente por `(tipo, papel, identificação)`; em conflito, o oficial prevalece. Itens inferidos usam um rótulo/atributo próprio (`inferido`) e um nó com proveniência (documento, trecho, data, confiança). `AusenciaFonte` só permanece quando não há oficial nem inferência.

Alternativa descartada: mesclar campos do inferido no título oficial; criaria dados híbridos sem proveniência clara.

### 7. Integração ao lote

A fase é executada ao final de `executar_resumos`, depois da gravação dos resumos e antes da finalização. O `ResultadoResumos` ganha um desfecho de inferência (executada, itens, falhas, cancelada), sem alterar as contagens de resumo. GUI e CLI reusam o mesmo caso de uso; o progresso usa um rótulo próprio e o cancelamento é cooperativo.

O botão "Resumir pendentes" passa a consultar também `precisa_inferencia_direitos(ticker)` fora da thread do Tk, junto da leitura do catálogo, para habilitar quando não houver documentos pendentes mas existir inferência elegível.

### 8. Manifesto/árvore do Chat AI

Os caminhos de direitos e obrigações continuam cache-only. O manifesto anuncia apenas ramos existentes; itens inferidos entram nos mesmos caminhos canônicos, com metadado de proveniência. Nenhuma chamada à LLM ou à rede ocorre na navegação.

## Risks / Trade-offs

- **Alucinação da LLM** → validação de esquema, evidência obrigatória, confiança mínima, rótulo explícito e precedência oficial.
- **Custo e latência no lote** → só documentos elegíveis e sem cache válido; entrada limitada ao resumo; cache por hash/versão do prompt.
- **Falsos vínculos por nome** → exigir tipo conhecido e evidência textual; não criar vínculo por aproximação de nome de emissor.
- **Cache desatualizado** → invalidar por hash do resumo e versão do prompt; preservar itens não reprocessados.
- **Manifesto acima do teto de tokens** → anunciar apenas tipos/ramos presentes e manter a descrição compacta.
- **Falha da inferência contamina o lote** → desfecho separado; resumos e itens já gravados permanecem.

## Migration Plan

1. Adicionar o domínio, o repositório e o caso de uso com testes unitários, sem ligar ao lote.
2. Integrar a fase ao lote atrás da flag desligada por padrão.
3. Expor os itens inferidos na árvore e no manifesto, mantendo o oficial como precedente.
4. Habilitar a flag em ambientes de validação; rollback é desligar a flag ou remover o cache de inferências, sem migração.
