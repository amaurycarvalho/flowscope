## 1. Formatador compartilhado

- [ ] 1.1 Extrair `formatar_guidance(guidance: Guidance) -> str` em `application/fundamental/linhas.py`, preservando o formato `Guidance R$ X[/ a R$ Y]/cota (<período>, <mmm/aa>)`, e fazer `_itens_guidance` delegar a ele; verificar com `python -m pytest tests -k guidance` (ou teste novo do formatador) e conferir que a coluna `Informações adicionais` mantém o texto atual

## 2. Leitura (worker → pré-visualização)

- [ ] 2.1 Fazer `DocumentFlowMixin.avaliar_guidance` devolver `AvaliacaoGuidance | None` e `_trabalhar` capturar o retorno, incluindo-o em `ctx.resultado(valor=(resultado, precisa, resumo, avaliacao))`; verificar com o teste do painel de documentos existente
- [ ] 2.2 Ajustar `_aplicar_preview` para receber a avaliação e derivar o texto de guidance (via `formatar_guidance`) quando `avaliacao.guidance` existir; verificar que documentos não-`Relatorio` e avaliações de ausência não produzem item
- [ ] 2.3 Alterar `_mostrar_documento` para aceitar `guidance_texto` e compor `resumo` + linha em branco + `guidance` + linha em branco + `---` + linha em branco + texto, omitindo o guidance quando ausente e posicionando-o antes do `---` quando não houver resumo; verificar com teste de composição da pré-visualização

## 3. Lote de resumos

- [ ] 3.1 Atualizar o protocolo `_PainelDocumentos.avaliar_guidance` e `resumos_job._resumir` para publicar `ctx.resultado(valor=(resumo, avaliacao), dados=arquivo)`; verificar com os testes de `tests/test_presentation` do lote
- [ ] 3.2 Ajustar `app_resumos_actions._aplicar_resultado_resumo` para desempacotar `(resumo, avaliacao)` e repassá-la a `refletir_resumo`/`aplicar_resumo`, que propagam ao `_mostrar_documento`; verificar que a pré-visualização recomposta inclui o guidance

## 4. Verificação integrada

- [ ] 4.1 Executar `make test` (cobertura ≥ 85%) e `make lint` sem erros
- [ ] 4.2 Confirmar manualmente que um RG com guidance exibe o texto entre o resumo e o `---`, idêntico ao da coluna `Informações adicionais`, e que um RG sem guidance mantém a composição anterior
