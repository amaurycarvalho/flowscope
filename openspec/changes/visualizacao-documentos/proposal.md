## Why

Os documentos baixados pela aplicação ficam em caches por ticker/ano/mês — os PDFs de Avisos aos Acionistas de BDR (`bdr/`), os PDFs de documentos relevantes (`documentos-relevantes/`) e o HTML do Informe Mensal (`informe-mensal/`) — mas não há como navegá-los ou inspecioná-los pela interface. Esta change adiciona uma sub-aba de documentos na "Análise do Ticker" para navegar e visualizar esses arquivos em cache.

## What Changes

- Catálogo de documentos que varre as raízes de cache (`bdr/`, `informe-mensal/`, `documentos-relevantes/`) e normaliza os arquivos em uma hierarquia `ticker → ano → mês → categoria → arquivos`, com tipo (`pdf`/`html`) e caminho.
- Nova sub-aba **"Documentos"** na "Análise do Ticker" com uma árvore hierárquica, o nome do ticker no topo e as categorias derivadas da fonte/ pasta.
- Pré-visualização textual em caixa de texto somente-leitura ao selecionar um arquivo, com extração sob demanda (HTML→texto; PDF→`pypdf`) executada fora da thread da interface.
- Abertura do arquivo no aplicativo padrão do sistema operacional (PDF→leitor de PDF; HTML→navegador) por duplo-clique, tecla Enter ou botão "Abrir".
- Ordenação (ano/mês decrescentes, categorias alfabéticas, arquivos do mais recente ao mais antigo), estado vazio e atualização manual.

## Capabilities

### New Capabilities

- `documentos-catalogo`: varredura das raízes de cache, normalização hierárquica por ticker/ano/mês/categoria, classificação de tipo e ordenação.
- `documentos-ticker-panel`: sub-aba "Documentos" na "Análise do Ticker" com árvore, pré-visualização textual e abertura no aplicativo padrão.

### Modified Capabilities

_Nenhuma. A sub-aba é introduzida pela nova capability `documentos-ticker-panel`; a lista de sub-abas de `gui-interface` não é alterada por esta change._

## Impact

- **Código**: nova camada de catálogo (varredura de cache) e novo painel em `presentation/gui/`, registrado em `TAB_CONFIGS`/`_build_ticker_tabs` e no mapa `_TICKER`.
- **Cache**: somente leitura das raízes `~/.cache/flowscope/bdr/`, `informe-mensal/` e `documentos-relevantes/`.
- **Dependências**: `pypdf` (já presente) para extração de texto do preview.
- **Dependência de changes**: `informe-mensal` (cache HTML) e `documentos-relevantes` (cache PDF) definem as raízes consumidas; o cache `bdr/` já existe.
