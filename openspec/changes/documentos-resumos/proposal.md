## Why

Os documentos em cache (avisos de BDR, informes mensais e documentos relevantes) só podem ser lidos abrindo o arquivo ou lendo o texto extraído integral. O usuário não tem uma visão sintética do que cada agrupamento contém nem do que cada documento diz, o que torna a triagem lenta. Com a base de LLM da change `llm-core`, é possível gerar resumos curtos e longos dos documentos, exibi-los na própria sub-aba "Documentos" e permitir copiar trechos com facilidade.

## What Changes

- Novos campos `short_summary` (até 280 caracteres, nulo quando não gerado) e `long_summary` (até 1500 caracteres, nulo quando não gerado) no catálogo de documentos, com persistência em `~/.cache/flowscope/document-summaries/<TICKER>.json` (JSON por ticker, escrita atômica, chave = caminho relativo à raiz de cache).
- Ao selecionar um **agrupador** da árvore (ticker, ano, mês ou categoria), o campo de texto DEVE exibir uma lista Markdown de todos os documentos contidos no agrupamento, agrupada pelos sub-agrupamentos, com o `short_summary` de cada documento. Sem resumo, exibe a mensagem de indisponibilidade com a instrução condicional (clicar no documento ou configurar a LLM).
- Ao selecionar um **documento**, o campo de texto DEVE exibir `long_summary`, seguido de linha em branco, `---`, linha em branco e o texto integral do documento. Sem `long_summary`, o sistema gera os dois resumos via LLM (fórmula XYZ) e os persiste; se a LLM não estiver configurada/funcional, exibe a mensagem de indisponibilidade.
- O campo de texto permanece somente-leitura, mas passa a aceitar os atalhos de teclado (Ctrl+A, Shift+setas, Ctrl+C, navegação) e a exibir o cursor de foco, facilitando a cópia de trechos.
- Novo serviço especializado `ResumirDocumentoUseCase` que recebe um texto e produz os dois resumos, consumindo a porta `LLMPort` da change `llm-core`.

## Capabilities

### New Capabilities

- `documento-summary`: serviço que produz `short_summary` (até 280) e `long_summary` (até 1500) a partir de um texto, via `LLMPort` da `llm-core`, com fórmula XYZ e truncamento.

### Modified Capabilities

- `documentos-catalogo`: novos campos de resumo no catálogo e persistência dos resumos por ticker.
- `documentos-ticker-panel`: pré-visualização Markdown de agrupamentos, exibição de resumo longo + texto do documento, geração sob demanda de resumos e campo de texto somente-leitura com atalhos e cursor.

## Impact

- **Dependências**: consome a porta `LLMPort` da change `llm-core` (pré-requisito); nenhuma dependência nova além de `[llm]`.
- **Cache**: novo diretório `~/.cache/flowscope/document-summaries/` com um JSON por ticker.
- **GUI**: comportamento de seleção e pré-visualização da sub-aba "Documentos".
- **Custo/latência**: a primeira abertura de cada documento dispara uma chamada de LLM; resumos são persistidos e reutilizados.
