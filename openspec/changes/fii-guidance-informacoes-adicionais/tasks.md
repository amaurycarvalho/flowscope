## 1. Domínio

- [ ] 1.1 Criar o value object `Guidance` em `src/flowscope/domain/fii/` com `valor_min`, `valor_max`, `periodo`, `data_relatorio` e `caminho_pdf`; verificar com teste unitário que valor único tem `valor_min == valor_max`
- [ ] 1.2 Adicionar o campo `guidance: Guidance | None = None` a `AnaliseFundamental` (`src/flowscope/domain/fii/analysis.py`) e exportá-lo em `domain/fii/__init__.py`; verificar que os testes existentes de análise continuam passando

## 2. Cache de guidance por FII (infraestrutura)

- [ ] 2.1 Implementar o store de guidance por FII em `~/.cache/flowscope/guidance/<TICKER>.json`, com informação inicial vazia, escrita atômica e tolerância a ausência/corrupção (modelo de `infrastructure/document_summaries.py`); verificar com testes de leitura vazia, gravação/recuperação e JSON corrompido

## 3. Extração determinística (fallback)

- [ ] 3.1 Implementar normalização de texto (colapso de espaços e heurística para caracteres espaçados) e reutilizar/estender a extração de texto PDF; verificar com testes sobre amostras reais, incluindo um caso com letras espaçadas
- [ ] 3.2 Implementar a extração de valor (único, faixa, banda, múltiplo) com o padrão de alta confiança `Guidance <período>: R$ X` e a janela ranqueada por proximidade; verificar com testes dos formatos listados em design.md (Pátria, faixa, banda, inglês)
- [ ] 3.3 Implementar a extração do período de validade (`2S26`, `3T26`, `próximos N meses`, `restante do ano`, `até o fim do ano`, `jul/26 a dez/26`, `next N months`, `segundo semestre de YYYY`); verificar com testes por padrão
- [ ] 3.4 Implementar os filtros de falso positivo (glossário e `forward guidance`); verificar com testes de não-detecção
- [ ] 3.5 Implementar a tolerância a falha de leitura de PDF (preserva o cache); verificar com teste de PDF inválido

## 4. Avaliação do Relatório Gerencial

> Dependência: implementar após a change `cache-texto-documentos`, cujo cache de texto do documento é a fonte do texto avaliado pelo gatilho.

- [ ] 4.1 Implementar o `AvaliarGuidanceUseCase` em `src/flowscope/application/` com prompt específico via `LLMPort` para determinar se o relatório contém guidance e devolver `Guidance` ou ausência; verificar com teste de LLM que encontra e que não encontra guidance
- [ ] 4.2 Implementar a seleção do caminho: LLM quando disponível e funcional (chamada sem `LLMError`), extração determinística quando indisponível/não funcional; gravar no cache somente quando houver guidance e deixá-lo intacto em ausência/falha; verificar com testes de LLM funcional, LLM indisponível, falha da LLM e ausência de extração
- [ ] 4.3 Implementar o gatilho ao ler um Relatório Gerencial na sub-aba "Documentos": apenas categoria `Relatorio`, apenas quando `(ano, mês)` for posterior à data do guidance em cache (ou cache vazio) e apenas quando houver texto extraível, lendo o texto do cache de texto do documento (change `cache-texto-documentos`) sem reextrair; verificar com testes de relatório mais recente, cache vazio, relatório não mais recente, outra categoria e documento sem texto extraível

## 5. Aplicação

- [ ] 5.1 Definir a porta do store de guidance em `src/flowscope/application/` com o contrato de leitura por ticker; verificar que o tipo é consumível sem importar infraestrutura
- [ ] 5.2 Consumir a porta em `FundamentalAnalysisUseCase` apenas para `TIPO_EXIBICAO_FII`, lendo o cache sem calcular, e preencher `AnaliseFundamental.guidance`; verificar com teste de integração que FII com cache recebe guidance, cache vazio não dispara extração e Papel não consulta

## 6. Apresentação

- [ ] 6.1 Adicionar `_itens_guidance` em `src/flowscope/presentation/gui/charts/fundamental_rows.py`, no ramo FII, lendo `analise.guidance`, no formato `Guidance R$ X[/ a R$ Y]/cota (<período>, <mmm/aa>)`; verificar com testes de linha e de exportação CSV
- [ ] 6.2 Integrar o gatilho de avaliação ao fluxo de leitura do documento (`charts/document_summary.py` / `charts/document_tree_panel.py`), lendo o texto do cache de texto do documento e ignorando documento sem texto extraível, fora da thread do Tk e com descarte de resultado obsoleto; verificar com testes do gatilho e de seleção trocada
- [ ] 6.3 Injetar o store e o serviço de avaliação no wiring (`app_wiring.py`) e no `controller_fundamental.py`; verificar que a composição da análise fundamentalista monta sem erro
- [ ] 6.4 Atualizar o texto explicativo do OrientationPanel, se mencionar os itens de `Informações adicionais` de FIIs, para incluir o guidance; verificar com o teste existente de conteúdo do painel

## 7. Verificação final

- [ ] 7.1 Rodar `make lint` e corrigir avisos introduzidos
- [ ] 7.2 Rodar `make test` e garantir cobertura mínima de 85%
- [ ] 7.3 Validar a change com `openspec validate "fii-guidance-informacoes-adicionais"`
