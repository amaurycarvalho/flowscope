## Context

Ver `proposal.md` — Why para a motivação. O estado atual que molda o desenho:

- Os PDFs dos Relatórios Gerenciais já ficam em `<cache>/documentos-relevantes/<TICKER>/<AAAA>/<MM>/relatorio/<id>.pdf`, com `<AAAA>/<MM>` derivado da `referenceDate` (`infrastructure/b3/documentos_relevantes.py:190`). A categoria exibida é `Relatorio` (`domain/structured/documentos_relevantes.py:13`); a pasta contém majoritariamente `Relatório Gerencial`, mas também `Outros Relatórios` e `Relatório Anual`.
- `pypdf>=4` já é dependência e há extração de texto pronta em `infrastructure/b3/bdr/text.py:14`.
- Há um padrão consolidado de persistência por ticker em `infrastructure/document_summaries.py` (JSON por ticker, escrita atômica, tolerância a corrupção) e a porta `LLMPort` com `create_llm_provider`/`load_llm_config` (`infrastructure/llm/factory.py`, `infrastructure/llm/config.py`).
- A leitura de um documento na sub-aba "Documentos" passa por `DocumentTreePanel._trabalhar` (`presentation/gui/charts/document_tree_panel.py:305`), que obtém o texto e aciona `DocumentSummaryService.gerar` (`presentation/gui/charts/document_summary.py:93`), executado em thread com polling na thread do Tk.
- O texto do documento passa a ser servido pelo **cache de texto do documento** introduzido pela change `cache-texto-documentos`, da qual esta depende. O cache registra o marcador de ausência quando não há texto extraível, e esse marcador suprime a avaliação de guidance.
- A coluna `Informações adicionais` é montada em `presentation/gui/charts/fundamental_rows.py:163` a partir de `AnaliseFundamental` (`domain/fii/analysis.py:70`).
- `FundamentalAnalysisUseCase` recebe portas por injeção (`application/fundamental_analysis.py:104`) e é montado em `presentation/gui/controller_fundamental.py:41` a partir do wiring em `presentation/gui/app_wiring.py:54`.
- Amostra real medida em 58 FIIs (relatório mais recente): 24 mencionam "guidance", 22 são guidance real, ~19 com valor extraível por regex, 3 só em gráfico, 2 falsos positivos.

## Goals / Non-Goals

**Goals:**
- Manter o guidance por FII em cache, com informação inicial vazia, sem calcular na carga de dados nem na exibição da tabela.
- Avaliar o guidance ao ler um Relatório Gerencial mais recente que o cache, preferindo a LLM (quando disponível e funcional) e caindo para extração determinística quando ela não estiver disponível/funcional.
- Exibir o guidance em `Informações adicionais` apenas para FIIs, lendo do cache.

**Non-Goals:**
- Sinônimos de guidance (`previsão`, `projeção`, `estimativa`) — cobertura futura.
- Extrair valores presos a gráficos/imagens sem texto (XPML11, XPLG11, TRXF11).
- Normalizar o período de validade em uma data final canônica; preserva-se o texto reconhecido.
- Baixar documentos novos: a avaliação opera apenas sobre o PDF que está sendo lido.
- Retroceder em relatórios anteriores: o cache guarda o guidance do relatório mais recente que o apontou.

## Decisions

### 1. Cache de guidance por FII e leitura preguiçosa

Persistir em `~/.cache/flowscope/guidance/<TICKER>.json` (modelo de `document_summaries.py`: escrita atômica, `schema_version`, tolerância a ausência/corrupção). O conteúdo é o último guidance conhecido do ticker — `valor_min`, `valor_max`, `periodo`, `data_relatorio` e `caminho_pdf` — ou vazio. `FundamentalAnalysisUseCase` apenas **lê** o store e preenche `AnaliseFundamental.guidance`; nunca dispara extração.

- **Por quê:** atende à regra de não calcular guidance na carga de dados nem na exibição, mantendo a tabela barata; a chave por ticker expressa "guidance por FII".
- **Alternativas:** cache por documento (versão anterior; rejeitado: a regra pede por FII e a comparação é contra o último guidance); calcular na análise (rejeitado: contraria 2.1).

### 2. Gatilho na leitura do Relatório Gerencial

A avaliação ocorre no fluxo de leitura do documento na sub-aba "Documentos", quando o arquivo pertence à categoria `Relatorio` e `(ano, mes)` do relatório é posterior à `data_relatorio` do guidance em cache (ou o cache está vazio). O texto avaliado é lido do **cache de texto do documento** (change `cache-texto-documentos`), sem reextrair o PDF; quando o cache indicar ausência de texto (`tem_texto` falso), a avaliação é suprimida. O trabalho roda na thread do painel, com o mesmo descarte de resultado obsoleto dos resumos.

- **Por quê:** é exatamente o ponto pedido ("ao ler um RG"), não onera a carga, aproveita a infraestrutura assíncrona da sub-aba e evita reprocessar texto inexistente.
- **Alternativas:** disparar na aquisição de documentos (rejeitado: não é leitura e viola 2.1); disparar na análise fundamentalista (rejeitado); reextrair o texto no gatilho (rejeitado: duplica a conversão que o cache de texto elimina).

### 3. Avaliação preferencial pela LLM

Um `AvaliarGuidanceUseCase` recebe o texto do relatório e, via `LLMPort`, faz uma pergunta específica (se o relatório contém guidance de distribuição, com valor/faixa e período) e interpreta a resposta de forma estruturada/tolerante. "Disponível e funcional" = `create_llm_provider` não lança `LLMUnavailableError`/`LLMConfigurationError` e a chamada conclui sem `LLMError`. Se a LLM responde que **há** guidance, o resultado substitui o cache; se responde que **não há**, o cache permanece intacto.

- **Por quê:** a LLM cobre casos que a regex não extrai (redação variada, faixas, gráficos com texto), sem custo na carga; a chamada bem-sucedida é o teste de funcionalidade.
- **Alternativas:** usar a LLM apenas para confirmar candidatos da regex (rejeitado: perde cobertura); validar funcionalidade com chamada de teste separada (rejeitado: dobra o custo).

### 4. Extração determinística como fallback

Quando a LLM está indisponível ou não funcional (provedor `none`, dependência `litellm` ausente, configuração inválida ou `LLMError` na chamada), aplicar a extração determinística por `pypdf` + expressões regulares:

1. Normalizar o texto (colapsar espaços; heurística para texto com caracteres espaçados, caso HSML11).
2. Localizar menções a `guidance` (case-insensitive).
3. Descartar falsos positivos: glossário (`Guidance: Projeção ...`) e `forward guidance`.
4. Priorizar o padrão de alta confiança `Guidance <período>[:|]? R$ X` (muito regular nos fundos Pátria).
5. Caso contrário, varrer uma janela ao redor da menção por valores monetários, exigindo proximidade de "cota"/"unit" ou de um token de período, e ranquear por distância.
6. Extrair o período por regex (`2S26`, `3T26`, `próximos N meses`, `restante do ano`, `até o fim do ano`, `jul/26 a dez/26`, `next N months`, `segundo semestre de YYYY`).

Se extrair guidance, gravar no cache; se não, deixar o cache intacto.

- **Por quê:** garante o funcionamento sem LLM e mantém a resiliência do projeto; a ausência de extração não pode apagar um guidance anterior válido.
- **Alternativas:** um único regex amplo (rejeitado: falsos valores medidos em GARE11/HSML11/HGRE11); limpar o cache quando não extrair (rejeitado: perde informação válida).

### 5. Modelo de resultado com proveniência

`Guidance(valor_min, valor_max, periodo, data_relatorio, caminho_pdf)`. Valor único → `valor_min == valor_max`. Faixas e bandas → min/max. Ausência de guidance é ausência do item no cache (distinta de falha de leitura, que também preserva o cache mas é logada).

- **Por quê:** min/max cobre valor único, faixa, banda superior/inferior e listas de valores; a proveniência alimenta o "(período, mês/ano)" exibido.

### 6. Renderização em `Informações adicionais` a partir do cache

Adicionar `_itens_guidance` em `fundamental_rows.py`, no ramo `TIPO_EXIBICAO_FII`, produzindo `Guidance R$ X[/ a R$ Y]/cota (<período>, <mmm/aa>)` quando `analise.guidance` estiver preenchido; caso contrário, omitir o item.

- **Por quê:** segue o formato de itens concatenados por ` | ` já existente e não faz IO nem cálculo na renderização.

## Risks / Trade-offs

- **[Guidance só aparece após a leitura do RG]** → a coluna fica vazia até o usuário abrir um Relatório Gerencial; é o comportamento pedido.
- **[Guidance só em gráfico]** → 3 de 22 FIIs não têm valor em texto; resultado é ausência do item, sem quebra.
- **[LLM com falso negativo]** → uma resposta "não há guidance" mantém o cache anterior; mitigação: prompt específico e formato estruturado.
- **[Pasta `relatorio` inclui outros tipos]** → `Outros Relatórios`/`Relatório Anual` também disparam a avaliação; se não contiverem guidance, o cache permanece intacto.
- **[Custo/latência da LLM na leitura]** → roda fora da thread do Tk, com estado de carregamento e descarte de resultado obsoleto, como os resumos.
- **[Texto com caracteres espaçados]** → HSML11 extrai com espaços entre letras; mitigação: heurística de normalização; se falhar, cai para ausência.
- **[Dependência de `cache-texto-documentos`]** → o gatilho pressupõe o cache de texto implementado; implementar esta change depois daquela e ler o texto do cache, nunca reextraindo.

## Migration Plan

- Mudança aditiva: novo campo em `AnaliseFundamental` com default `None`; sem migração de dados existentes.
- Novo diretório de cache criado sob demanda; cache ausente/corrompido é tolerado (tratado como vazio).
- Requer a change `cache-texto-documentos` implementada antes: o gatilho lê o texto do cache de texto do documento.
- Rollback: remover o gatilho de leitura, o store do wiring e o item da coluna; os campos default não afetam o comportamento anterior.

## Open Questions

- Limitar a extração às primeiras N páginas do PDF (otimização) pode ser decidido na implementação sem alterar specs ou abordagem.
- Detectar `Relatório Gerencial` pelo título do PDF (e não só pela categoria `Relatorio`) pode ser adicionado como reforço, se a avaliação de "Outros Relatórios" se mostrar custosa.
