## Context

Ver `proposal.md - Why`. O Informe Mensal Estruturado (type=40) já é adquirido e lido: `B3FundosClient.listar_documentos(..., type=40)` lista as referências e `B3FundosClient.buscar_html_documento(id)` baixa o HTML, que `B3ReportsRepository.extrair_informe` transforma em `B3InformeMensal` via `informe_mensal_parser`. O HTML fica no cache JSON do `CacheManager` (`fund_doc_html_*`), chaveado apenas pelo id do documento, sem ticker/ano/mês.

Esta change adiciona uma persistência em arquivo do HTML bruto, organizada por ticker/ano/mês, para consumo da sub-aba de documentos. As entidades de leitura existentes não são alteradas.

## Goals / Non-Goals

**Goals:**
- Persistir o HTML do informe mensal em `<cache>/informe-mensal/<TICKER>/<AAAA>/<MM>/<id>.html`.
- Reutilizar listagem type=40 e download existentes, sem novo cliente.
- Expor leitura da árvore (documentos de um ticker, ordenados do mais recente ao mais antigo).

**Non-Goals:**
- Alterar `B3InformeMensal`, `informe_mensal_parser` ou `B3ReportsRepository`.
- Domínio rico (`Carteira`, `Resultados`, `Indicadores`), `Percentual`, use case próprio.
- Indexação/VectorStore (`to_text`, `DocumentSource`) — pertence a `llm-chat`.
- CLI `--informe-mensal`.
- OCR ou conversão do HTML para PDF.

## Decisions

### 1. Raiz de cache própria, análoga ao cache de PDFs de BDR

**Decisão**: gravar em `<cache>/informe-mensal/<TICKER>/<AAAA>/<MM>/<id>.html`, sem TTL. Mesmo padrão de árvore do `PdfCache` de BDR, mas em raiz própria.

**Alternativas**: (a) reusar o cache JSON `fund_doc_html_*` — não comporta ticker/ano/mês e é compartilhado com proventos (type=41); (b) reusar a árvore `bdr/` — semanticamente errada. A raiz própria mantém o cache BDR intacto e permite a varredura por fonte escolhida para o catálogo.

### 2. Não alterar as entidades de leitura

**Decisão**: o novo cache apenas grava/lê arquivos; a extração de `B3InformeMensal` continua a cargo do parser existente.

**Racional**: as entidades já estão implementadas e em uso na sub-aba Fundamentos; a change deve apenas tornar o documento acessível.

### 3. Ano/mês derivados da data de referência

**Decisão**: usar `reference_date` do documento; fallback para a data de entrega e, por fim, a data corrente. Mantém a árvore navegável mesmo quando a B3 não informa a referência.

## Risks / Trade-offs

- **[Risco] Duplicação de bytes** entre o cache JSON (parsing) e o arquivo HTML (visualização) → Aceitável: o JSON serve ao parsing e o arquivo à inspeção; o volume é pequeno (HTML).
- **[Trade-off] Sem PDF** → O informe mensal é HTML; a sub-aba abre HTML no navegador padrão, não no leitor de PDF. Decisão confirmada.
- **[Risco] Layout de URL mudar** → Reutiliza o mesmo `exibirDocumento?id=` já usado pelo parser, sem novo contrato.

## Migration Plan

1. Adicionar o cache de arquivo do informe mensal em `infrastructure/b3/`.
2. Integrar a gravação ao fluxo de aquisição do informe (após o download do HTML).
3. Consumir a árvore pela sub-aba de documentos (change `visualizacao-documentos`).
4. Rollback: as mudanças são aditivas; remover o cache de arquivo restaura o comportamento atual.
