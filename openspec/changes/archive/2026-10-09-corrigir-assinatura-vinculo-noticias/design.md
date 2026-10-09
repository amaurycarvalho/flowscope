## Context

Ver `proposal.md` — Why. O painel de notícias injeta um resolvedor de documento vinculado (`baixar_vinculo`) cujo tipo declarado é `Callable[[str, str | None], ExtracaoTexto | None]` (`src/flowscope/presentation/gui/charts/noticias_panel.py:82`) e o invoca posicionalmente (`noticias_panel.py:361`). O resolvedor de produção é `baixar_conteudo_vinculado` (`src/flowscope/infrastructure/b3/noticias_vinculo.py:62`), que declara `senha` como keyword-only (`*, senha`). Os dublês dos testes usam `lambda texto, senha=None`, aceitando a senha posicional, por isso a divergência passou despercebida.

## Goals / Non-Goals

**Goals:**
- Restabelecer o contrato posicional do resolvedor injetado, alinhando-o ao tipo declarado e ao call site.
- Impedir que falhas do resolvedor (incluindo assinatura) escapem do painel/lote, caindo no corpo original.
- Cobertura de teste que use a assinatura de produção, não apenas dublês.

**Non-Goals:**
- Redesenhar o fluxo de senha interativa ou o cache de texto.
- Alterar as assinaturas públicas de `extrair_pdf` ou `extrair_arquivo`.

## Decisions

### Decisão 1: Tornar `senha` posicional-or-keyword em `baixar_conteudo_vinculado`

Assinatura nova:

```python
def baixar_conteudo_vinculado(
    texto: str,
    senha: str | None = None,
    *,
    sessao: requests.Session | None = None,
    timeout: int = TIMEOUT,
) -> ExtracaoTexto | None: ...
```

**Por quê:** o tipo do parâmetro injetado (`Callable[[str, str | None], ...]`), o call site e todos os dublês já tratam a senha como posicional. Ajustar o call site para keyword exigiria renomear o parâmetro em todos os dublês e não é expressável no tipo `Callable`.

**Alternativas:** (a) mudar o call site para `senha=senha` e atualizar dublês/tipo — mais atrito e não reflete o tipo; (b) aceitar apenas keyword no painel via `functools.partial` — complexidade desnecessária.

### Decisão 2: Isolar a chamada do resolvedor em `_texto_do_arquivo`

Envolver `self._baixar_vinculo(resultado.texto, senha)` em `try/except Exception`, registrar `logger.warning(..., exc_info=True)` e devolver `resultado` (corpo original). Reforça o contrato "sem erro" já vigente e cobre resolvedores alternativos que levantem em vez de devolver `None`.

**Trade-off:** uma degradação silenciosa (com log) em vez de propagar; aceitável, pois o corpo original permanece visível e o item continua pendente.

## Risks / Trade-offs

- [Regressão de contrato futura] → teste que instancia o painel com o resolvedor real de produção e verifica que a resolução não levanta, além de teste explícito de chamada posicional da senha em `test_noticias_vinculo`.
- [Exceção ampla ocultar bug] → `except Exception` acompanhado de `logger.warning(..., exc_info=True)`, mantendo rastreabilidade.
