## Context

Ver `proposal.md - Why`. Hoje a quantidade de cotas emitidas já é obtida, mas descartada:

- `PatrimonioFii.shares_outstanding` (`domain/fii/analysis.py`) carrega as cotas emitidas; `B3FundamentalRepository._buscar_patrimonio` já resolve B3 (Informe Mensal) → CVM (mensal) e é memorizado por `(ticker, reference_date)`.
- `FundamentalDataMixin._resolver_cotistas` (`application/fundamental_providers.py`) devolve apenas `(patrimonio, cotistas)`, descartando `shares_outstanding`.
- `AnaliseFundamental` não possui campo de cotas.
- O `CompositeFundamentalProvider` (`application/fundamental_fallback.py`) resolve cada campo pela **primeira** fonte em ordem fixa; em `app.py` a ordem é `FundamentusFundamentalDataProvider` → `B3FundamentalDataProvider` → CVM. Ou seja, o Fundamentus sempre precede a B3.
- A página real do Fundamentus expõe `Nro. Cotas` (FII) e `Nro. Ações` (Papel); o parser atual não extrai nenhum dos dois (`AtivoFundamental` não tem o campo, embora `coletar_raw` já traga o par rótulo→valor).

A apresentação monta as linhas em `presentation/gui/charts/fundamental_rows.py` a partir de `_COLUNAS`, `_linha_analise` e `_COLUNAS_DIREITA`; a contagem atual é 29 colunas (2 fixas + 27 roláveis).

## Goals / Non-Goals

**Goals:**
- Expor `Nº de cotas` na tabela, imediatamente antes de `Nº de cotistas`, formatado como inteiro com separador de milhar.
- Extrair `Nro. Cotas`/`Nro. Ações` do Fundamentus.
- Resolver a quantidade por tipo: FII prioriza B3/CVM (via `PatrimonioFii`) com Fundamentus como fallback final; Papel usa o Fundamentus.
- Reutilizar o `PatrimonioFii` já buscado, sem novo acesso de rede.

**Non-Goals:**
- Não buscar quantidade de ações de Papel na CVM/B3: não há campo equivalente nos datasets consumidos hoje (o FRE traz número de acionistas, não de papéis). Papel fica restrito ao Fundamentus.
- Não alterar a prioridade das demais colunas (o Fundamentus continua primário para `patrimônio`/`VP/Cota`).
- Não criar classificação/faixa para a quantidade de cotas (a coluna é informativa, sem análogo a `Classe de cotistas`).

## Decisions

### D1. Novo campo `cotas_emitidas` no Fundamentus

O parser ganha `_ROTULOS_COTAS = ["Nro. Cotas", "Nro. Ações"]`, extraídos por `_primeiro(raw, _ROTULOS_COTAS)` e normalizados por `para_decimal` (já trata milhar pt-BR: `144.355.726` → `Decimal("144355726")`). `AtivoFundamental` ganha `cotas_emitidas: Decimal | None`, e o adapter do Fundamentus emite `CAMPO_COTAS_EMITIDAS` via `_adicionar`.

**Por que `para_decimal` e não `para_int`**: preserva o tipo `Decimal` do restante da análise e evita conversão prematura; o arredondamento/truncamento para inteiro acontece só na formatação.

### D2. Resolução por tipo no caso de uso, não no composite

A prioridade pedida (FII: B3/CVM → Fundamentus; Papel: Fundamentus) **não pode** ser expressa pelo `CompositeFundamentalProvider`, que tem ordem fixa Fundamentus-primeiro. Emitir `CAMPO_COTAS_EMITIDAS` também pelo provider B3 seria inútil: o valor do Fundamentus o sombrearia no composite.

Assim, adiciona-se `_resolver_cotas(dados, classificacao, patrimonio_repo)` em `FundamentalDataMixin`, análogo a `_resolver_cotistas`:

- `cotas_fundamentus = _decimal_campo(dados, CAMPO_COTAS_EMITIDAS)`
- `cotas_repo = patrimonio_repo.shares_outstanding` (B3→CVM já resolvido)
- `FII` → `cotas_repo` se disponível, senão `cotas_fundamentus`
- `Papel` → `cotas_fundamentus`

O `patrimonio_repo` é o mesmo objeto já buscado em `_analisar_ticker` e passado a `_resolver_cotistas`; a memorização do repositório evita dupla consulta. A proveniência por campo não é persistida em `AnaliseFundamental` (mesmo comportamento de `patrimonio`/`cotistas`), mas o valor de `PatrimonioFii.fonte` já registra a origem B3/CVM quando aplicável.

**Alternativas descartadas**: (a) emitir por provider B3 e confiar no composite — não expressa a prioridade por tipo; (b) criar prioridade por campo no composite — mudança transversal e desproporcional.

### D3. Armazenamento e formatação

`AnaliseFundamental` ganha `cotas: Decimal | None`. A apresentação adiciona `("cotas", "Nº de cotas")` em `_COLUNAS` imediatamente antes de `("cotistas", "Nº de cotistas")`, inclui `"cotas"` em `_COLUNAS_DIREITA` e emite `formatar_quantidade(analise.cotas)` antes de `formatar_inteiro(analise.cotistas)`.

`formatar_quantidade(valor: Decimal | None)` (novo, em `fundamental_formatters.py`) trunca para inteiro e agrupa milhares com `.` (ex.: `144.355.726`), retornando `N/A` quando ausente — consistente com `formatar_inteiro`.

### D4. Contagens, orientação e documentação

A contagem passa de 29 para 30 colunas (2 fixas + 28 roláveis); `_linha_sintetica` já se ajusta sozinho via `len(_COLUNAS) - 4`. Atualiza-se o quadro de orientações (`app_tabs.py`) com a quantidade de cotas e `panels.md` (texto "demais 27 colunas" → 28). Testes de tabela/CSV e contagens de colunas são ajustados.

## Risks / Trade-offs

- **Papel sem fallback CVM/B3** → aceito; o Fundamentus é a única fonte de `Nro. Ações`. Se indisponível, `N/A`.
- **Divergência de valor entre Fundamentus e B3/CVM para FII** (defasagem do Fundamentus) → mitigado pela prioridade B3/CVM para FII, que é a fonte mais precisa; o Fundamentus só entra quando B3 e CVM faltam.
- **Rótulo "Nº de cotas" para Papel** → semanticamente "ações"; aceito para manter a coluna única e a paridade com "Nº de cotistas", que já usa o termo para ações.
- **`Nro. Ações`/`Nro. Cotas` pode variar de layout** → o parser já é orientado por rótulo e tolerante; fixture de ação e de FII serão atualizadas para cobrir os dois rótulos.

## Migration Plan

- Sem migração de dados: mudança aditiva de exibição.
- Cache do Fundamentus é versionado por parser; a nova extração exige bump da versão do parser para invalidar snapshots sem o campo (a definir na implementação).
- Rollback: reverter o commit; nenhum schema de cache além da versão do parser é invalidado.
