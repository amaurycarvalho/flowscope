## Why

O Informe Mensal Estruturado (type=40) da B3 é um documento **HTML** (`exibirDocumento?id=`) já consumido pelas entidades de leitura existentes (`B3InformeMensal`, `informe_mensal_parser`, `B3ReportsRepository`), que alimentam a sub-aba Fundamentos. Esses dados ficam apenas no cache JSON interno (`fund_doc_html_*`), sem um arquivo acessível por ticker/ano/mês para inspeção e visualização. Esta change re-escopa o informe mensal para persistir o HTML bruto do documento em uma árvore de arquivos, servindo de fonte para a sub-aba de documentos.

## What Changes

- Persistir o HTML do informe mensal em `~/.cache/flowscope/informe-mensal/<TICKER>/<AAAA>/<MM>/<id>.html`, com ano/mês derivados da data de referência do documento.
- Expor a leitura dessa árvore (existência, caminho e conteúdo) para o catálogo de documentos.
- Reutilizar a listagem type=40 e o download HTML já existentes no `B3FundosClient`, **sem alterar** as entidades de leitura (`B3InformeMensal`, parser e repositório).
- Remover do escopo: domínio rico (`Carteira`, `Resultados`, `Indicadores`, `InformeMensal`), value object `Percentual`, `InformeMensalRepository`/`ExtrairInformeMensalUseCase`, parser multi-tabela, CLI `--informe-mensal` e `to_text()`/preparação de VectorStore (transferida para `llm-chat`).

## Capabilities

### New Capabilities

- `informe-mensal-cache`: persistência em arquivo do HTML do informe mensal, organizada por ticker/ano/mês, e sua leitura pelo catálogo de documentos.

### Modified Capabilities

_Nenhuma. As entidades de leitura existentes não têm requisitos alterados._

## Impact

- **Dependência**: reutiliza `B3FundosClient` (listagem type=40 e `buscar_html_documento`) e `B3ReportsRepository` já implementados.
- **Código**: `infrastructure/b3/` (novo cache de arquivo do informe mensal); consumo indireto pela sub-aba de documentos via catálogo.
- **Cache**: nova raiz `~/.cache/flowscope/informe-mensal/`; o cache JSON `fund_doc_html_*` existente permanece.
- **Transferência**: partes de indexação (`to_text`, fonte de documentos) passam para a change `llm-chat`.
