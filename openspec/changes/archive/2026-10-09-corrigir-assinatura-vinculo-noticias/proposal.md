## Why

Notícias "Geral" cujo corpo é apenas um apontador para um documento vinculado (CVM RAD/FNET) não conseguem ser visualizadas, extraídas nem resumidas: o painel passa a senha de forma posicional ao resolvedor injetado, mas `baixar_conteudo_vinculado` a declara como keyword-only, causando `TypeError` em toda tentativa. O lote de "Resumir pendentes" falha em série para todas essas notícias.

## What Changes

- Alinhar o contrato de chamada do resolvedor de documento vinculado injetado no `NoticiasPanel` com a assinatura de `baixar_conteudo_vinculado`, de modo que a senha opcional seja aceita sem `TypeError`.
- Garantir que uma falha do resolvedor (assinatura, rede ou formato) degrade para o corpo original, sem propagar exceção para a pré-visualização nem para o lote.
- Adicionar testes que exercitem a assinatura real do resolvedor usado em produção (`baixar_conteudo_vinculado`), impedindo que dublês com assinatura divergente escondam a regressão.

## Capabilities

### New Capabilities
<!-- nenhuma -->

### Modified Capabilities
- `noticias-panel`: explicitar o contrato de injeção do resolvedor de documento vinculado (texto + senha opcional) e que a resolução nunca pode falhar por incompatibilidade de assinatura.

## Impact

- `src/flowscope/presentation/gui/charts/noticias_panel.py`
- `src/flowscope/infrastructure/b3/noticias_vinculo.py` (ou o call site, conforme a decisão de design)
- `tests/test_presentation/test_noticias_panel.py`
- `tests/test_infrastructure/test_regulacao/test_noticias_vinculo.py`
