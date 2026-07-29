## 1. Pré-requisito

- [ ] 1.1 `structured-earnings` implementada (B3FundosClient, CacheManager, ticker-resolution, HTML parsing base, value objects, Entidade)

## 2. Domínio — Value Objects e Entidades

- [ ] 2.1 Implementar `Percentual` em `domain/structured/value_objects.py`
- [ ] 2.2 Implementar `CarteiraAtivo`, `Carteira` em `domain/structured/entities.py`
- [ ] 2.3 Implementar `Resultados`, `Indicadores`, `OutrasInformacoes` em `domain/structured/entities.py`
- [ ] 2.4 Implementar `InformeMensal` com `to_dict()` e `to_text()`
- [ ] 2.5 Atualizar `domain/structured/__init__.py`

## 3. Testes do Domínio

- [ ] 3.1 Testar `Percentual`, `CarteiraAtivo`, `Carteira`
- [ ] 3.2 Testar `Resultados`, `Indicadores`, `InformeMensal.to_text()`

## 4. Aplicação

- [ ] 4.1 Definir `InformeMensalRepository` protocol em `application/structured_ports.py`
- [ ] 4.2 Implementar `ExtrairInformeMensalUseCase` em `application/structured_use_cases.py`

## 5. Testes da Aplicação

- [ ] 5.1 Mock `InformeMensalRepository`, testar use case — sucesso, vazio, erro

## 6. Infraestrutura — Parsing Multi-Tabela

- [ ] 6.1 `classificar_contexto_tabela()` em `infrastructure/b3/structured_parser.py`
- [ ] 6.2 `extrair_carteira()`, `extrair_resultados()`, `extrair_indicadores()`, `extrair_outras_informacoes()`
- [ ] 6.3 `validar_totais_carteira()`, `validar_resultado_liquido()`
- [ ] 6.4 `extrair_informe_mensal()` — função principal

## 7. Infraestrutura — Repository

- [ ] 7.1 `FundosInformeMensalRepository` implementando `InformeMensalRepository`

## 8. Testes Infraestrutura

- [ ] 8.1 Fixture HTML multi-tabela, testar classificação e extração
- [ ] 8.2 Testar validação cruzada, repository com mock

## 9. CLI

- [ ] 9.1 `--informe-mensal` no parser, `run_informe_mensal()`, dispatch

## 10. Testes CLI

- [ ] 10.1 Testar argumentos e saída

## 11. Quality Gate

- [ ] 11.1 `make lint` + `make test` passam
