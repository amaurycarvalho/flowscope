## 1. Aplicação — linhas e formatação

- [x] 1.1 Criar `application/fundamental/formatters.py` com os formatadores de exibição (`formatar_*`, `rotulo_*`, `NA`) movidos de `presentation/gui/charts/fundamental_formatters.py`; verificar com testes puros de formatação
- [x] 1.2 Criar `application/fundamental/linhas.py` com o layout de colunas e `montar_linhas`/`montar_csv` movidos de `presentation/gui/charts/fundamental_rows.py`; verificar com testes puros de montagem de linhas e CSV
- [x] 1.3 Atualizar `fundamental_table.py` para reexportar/consumir a API de `application` e `app_csv.py` para importar `montar_csv` de `application`; verificar `make test` verde sem mudança de comportamento

## 2. Aplicação — evolução

- [x] 2.1 Mover `fundamental_evolution_data.py` para `application/fundamental/evolucao.py` (Fibonacci e `montar_series`), mantendo os tipos de campo; verificar com testes puros de amostragem e séries
- [x] 2.2 Atualizar `fundamental_evolution_panel.py` para consumir `application`; verificar o painel com fakes e paridade de séries

## 3. Apresentação e composition root

- [x] 3.1 Injetar o adaptador de mercado no `FundamentalMixin` pelo composition root, removendo o import de `infrastructure`; verificar que `controller_fundamental` não consta mais na allowlist
- [x] 3.2 Atualizar `app_wiring.py` para montar a fábrica do adaptador de mercado; verificar `make test` verde com o job/controlador

## 4. Testes e allowlist

- [x] 4.1 Migrar os testes puros de linhas/CSV/formatação e de evolução para `tests/test_application`; deixar no painel apenas wiring, estado, congelamento/rolagem e seleção; verificar ausência de `DISPLAY` nos testes puros
- [x] 4.2 Remover a entrada `controller_fundamental` da allowlist; verificar `tests/architecture` verde sem entradas obsoletas
- [x] 4.3 Rodar `make test` e `make quality-gate` e confirmar tudo verde com paridade de comportamento
