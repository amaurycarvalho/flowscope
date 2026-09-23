## Why

Os Relatórios Gerenciais de FIIs publicam um *guidance* de distribuição de rendimentos — o valor (ou faixa) projetado e o período de validade — que hoje fica enterrado em PDFs e não aparece na análise fundamentalista. Em vez de reprocessar PDFs a cada carga de dados, o guidance é avaliado quando o usuário lê um Relatório Gerencial na sub-aba "Documentos" e guardado em cache por FII; a coluna `Informações adicionais` apenas exibe o que já está em cache. Quando a LLM está configurada e funcional, ela faz a avaliação específica do relatório; caso contrário, usa-se a extração determinística por expressões regulares.

## What Changes

- Cache de guidance **por FII** (`~/.cache/flowscope/guidance/<TICKER>.json`), com informação inicial vazia, escrita atômica e tolerância a ausência/corrupção.
- A coluna `Informações adicionais` de FIIs lê o cache e exibe um item `Guidance ...` quando houver. **O guidance não é calculado na carga de dados nem na exibição da tabela**: cache vazio → item omitido.
- Gatilho ao **ler um Relatório Gerencial na sub-aba "Documentos"** (categoria `Relatorio`): se o relatório for mais recente que o guidance em cache (ou o cache estiver vazio), o sistema avalia o **texto do relatório obtido do cache de texto do documento** (change `cache-texto-documentos`), sem reextrair o PDF. Documento sem texto extraível não dispara avaliação.
- O botão **"Resumir pendentes"** da sub-aba "Documentos" também avalia o guidance dos documentos da categoria `Relatorio` que já processa (pendentes de resumo), reaproveitando o texto preparado pelo lote e as mesmas condições do gatilho de leitura, sem interromper o lote em caso de falha. O lote **não** varre Relatórios já resumidos: nesses casos o guidance continua a ser atualizado apenas ao ler o RG.
  - Se a análise de guidance via LLM estiver **habilitada** (flag na configuração da aplicação) e o recurso estiver disponível e funcional, a LLM faz uma avaliação específica se há guidance no relatório; havendo, a nova informação substitui a anterior no cache.
  - Se o flag estiver desabilitado, ou a LLM estiver indisponível ou não funcional, usa-se a extração determinística (`pypdf` + regex) já especificada; extraindo guidance, grava-se no cache; não extraindo, o cache permanece intacto.
- Flag de análise de guidance via LLM na configuração da aplicação (`llm.guidance.enabled` em `~/.flowscope/config.json`), **desabilitado por padrão**; desligado, o guidance roda apenas de forma determinística, independentemente do provedor de chat configurado.
- Extração determinística do **valor** (único, faixa ou múltiplos valores por cota), do **período de validade** (`2S26`, `3T26`, `próximos N meses`, `restante do ano`, `até o fim do ano`, `jul/26 a dez/26`, `next N months`) e da **data do relatório** de origem.
- Escopo restrito à palavra literal `guidance`; sinônimos (`previsão`, `projeção`, `estimativa`) ficam como não-objetivo.
- Aplicável apenas a ativos do tipo `FII`.

## Capabilities

### New Capabilities
- `relatorio-gerencial-guidance`: cache de guidance por FII, avaliação do Relatório Gerencial ao ser lido na sub-aba "Documentos" (LLM preferencial com fallback determinístico por regex) e exposição do resultado na análise fundamentalista.

### Modified Capabilities
- `gui-interface`: o requisito "Colunas Preço Típico, P / PT, Informações adicionais e Dados fiscais" passa a exibir, para FIIs, o item de guidance **lido do cache** em `Informações adicionais` (label, valor/faixa, período e mês/ano do relatório), sem calcular guidance na carga nem na renderização.

## Dependencies

- Depende de `cache-texto-documentos`: o texto avaliado pelo gatilho é lido do cache persistente de texto do documento (ou do marcador de ausência), sem reextrair o PDF. Esta change deve ser implementada **após** a implementação daquela, que é pré-requisito do gatilho.

## Impact

- **Domínio**: novo value object `Guidance` e novo campo em `AnaliseFundamental` (`domain/fii/analysis.py`).
- **Aplicação**: porta de cache de guidance, serviço de avaliação (`AvaliarGuidanceUseCase`) e leitura na análise fundamentalista (`application/fundamental_analysis.py`), aplicada somente a `TIPO_EXIBICAO_FII`.
- **Infraestrutura**: store de guidance por FII (modelo de `document_summaries.py`), extração determinística (`pypdf` + regex), avaliação via `LLMPort` e flag `llm.guidance.enabled` na configuração de LLM (padrão desabilitado).
- **Apresentação**: gatilho no fluxo de leitura do RG (`charts/document_summary.py` / `document_tree_panel.py`), lendo o texto do cache de texto do documento e ignorando documento sem texto extraível; avaliação adicional no processamento em lote dos pendentes (`resumos_job.py` / `app_resumos_actions.py`), restrita aos documentos já processados; e item de guidance em `_informacoes_adicionais` (`charts/fundamental_rows.py`).
- **Wiring**: `presentation/gui/app_wiring.py` e `controller_fundamental.py` injetam o store e o serviço.
- **Testes**: unitários da extração (regex/casos reais), do store com cache, da avaliação LLM/fallback e da renderização da coluna.
