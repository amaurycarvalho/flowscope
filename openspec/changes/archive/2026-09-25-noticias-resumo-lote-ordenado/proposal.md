## Why

O lote "Resumir pendentes" da sub-aba "Notícias" processa os itens na ordem de inserção da árvore. No nível folha essa ordem é pelo `sha1` do arquivo (`noticias_aquisicao.py:189`), praticamente aleatória, então a regra "das mais recentes para as mais antigas" dentro de cada grupo não é garantida. Além disso, a gravação diferida na thread do Tk faz uma interrupção descartar resumos já gerados.

## What Changes

- Ordem explícita do lote por **grupo**: "Censuras Públicas" → "Condições Excepcionais" → "Programas de Aquisição de Ações" → "Geral" (a `SECOES_ORDEM` já usada na árvore), e dentro de cada grupo da **notícia mais recente para a mais antiga**, pela data de publicação.
- A ordenação deixa de ser efeito colateral da inserção na árvore e passa a ser uma regra explícita, com desempate determinista para datas ausentes ou empatadas.
- Cada resumo é **gravado imediatamente após a geração**, no worker, reutilizando o seam introduzido por `documentos-resumo-lote-persistente`.
- Interrupção (cancelar, fechar, crash) preserva os resumos já gerados; perde-se no máximo o item em processamento.

## Capabilities

### New Capabilities

<!-- nenhuma -->

### Modified Capabilities

- `noticias-panel`: o resumo em lote passa a seguir uma ordem explícita (por grupo e da notícia mais recente para a mais antiga) e a persistir cada resumo imediatamente após a geração.

## Impact

- **Código afetado**: `presentation/gui/charts/noticias_panel.py` (ordenação dos pendentes e gancho de persistência), `presentation/gui/app_resumos_actions.py` (consumo da ordem), `presentation/gui/resumos_job.py` (reuso do seam).
- **Dados**: usa `data_publicacao` e `secao` de `NoticiaArquivo`, já existentes; nenhum campo novo.
- **Testes afetados**: `tests/test_presentation/test_noticias_panel.py` (ordem do lote e persistência por item).
- **Depende de**: `documentos-resumo-lote-persistente` (seam de persistência no worker). Deve ser implementada depois dela por tocar os mesmos arquivos.
