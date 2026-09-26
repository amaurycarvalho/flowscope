# Referência do programa `clean-architecture-layering`

Documento de apoio para os increments filhos. Não altera specs; orienta como
mover código e testes sem quebrar o contrato `layer-boundaries`.

## Fluxo de dependências

```
presentation --> application --> domain
      |               ^
      v               |
infrastructure -------+   (infrastructure depende de application/domain)
```

Regras verificadas por `tests/architecture/test_layer_boundaries.py`:

| Camada | Não pode importar |
|---|---|
| `domain` | `application`, `infrastructure`, `presentation` |
| `application` | `infrastructure`, `presentation` |
| `infrastructure` | `presentation` |
| `presentation` | `infrastructure` (exceto composition root) |

## Composition root

`presentation/cli.py`, `presentation/main.py` e `presentation/gui/app_wiring.py`
são a única exceção estrutural a `presentation -> infrastructure`. Eles montam
as dependências e são a fronteira onde a infraestrutura encontra a UI. Nenhum
outro módulo de `presentation` deve importar `infrastructure`.

## Convenção de view-model

- `application` devolve **dados prontos** (dataclasses imutáveis ou estruturas
  simples) para os painéis: séries, linhas, contagens, resumos.
- `presentation` **apenas formata e desenha**: rótulos, cores, geometria,
  widgets e eventos. Não recalcula regressão de domínio.
- Regras de negócio (classificação, interpretação, agregação com significado)
  vivem em `domain` ou `application`.
- Entidades e objetos de valor vivem em `domain`, nunca em `infrastructure`.

## Allowlist de violações legadas

- Arquivo: `tests/architecture/allowlist.txt`.
- Formato: `<caminho relativo a src/flowscope> -> <camada importada>`.
- A lista é **dívida técnica decrescente**: violação nova reprova o teste e
  entrada sem violação correspondente também reprova.
- Cada incremento filho remove as entradas dos arquivos que refatorar.
- O incremento de fechamento (`enforce-clean-architecture-boundaries`) deixa a
  lista vazia.

## Como rodar

```bash
.venv/bin/python -m pytest tests/architecture -q
```

## Orçamento de testes

- Lógica pura: `tests/test_domain` ou `tests/test_application`, sem `DISPLAY`.
- UI: somente wiring, estado de widget/botão, empty-state e thread/queue.
- Comportamento observável (rótulos, números, ordem) deve permanecer idêntico
  após cada incremento.
