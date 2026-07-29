## 1. Dependências e Estrutura

- [ ] 1.1 Adicionar `beautifulsoup4` ao `pyproject.toml` em `dependencies`
- [ ] 1.2 Criar estrutura de diretórios: `domain/structured/`, testes correspondentes
- [ ] 1.3 Rodar `make install` para instalar nova dependência

## 2. Domínio — Value Objects

- [ ] 2.1 Implementar `CNPJ` em `domain/structured/value_objects.py` com validação de formato `XX.XXX.XXX/XXXX-XX`
- [ ] 2.2 Implementar `ISIN` com validação de 12 caracteres e prefixo BR
- [ ] 2.3 Implementar `ValorProvento` aceitando string monetária brasileira e `Decimal`
- [ ] 2.4 Criar `domain/structured/__init__.py` exportando todos os value objects

## 3. Domínio — Entidades

- [ ] 3.1 Implementar `Entidade` dataclass com `nome`, `cnpj` (CNPJ), `nome_administrador`, `cnpj_administrador` (CNPJ), `responsavel`, `telefone`
- [ ] 3.2 Implementar `Provento` dataclass com `codigo_isin` (ISIN), `codigo_negociacao`, `tipo`, `data_base`, `valor_por_unidade` (ValorProvento), `data_pagamento`, `periodo_referencia`, `isento_ir`, `nota_isencao`
- [ ] 3.3 Implementar `DocumentoProvento` agregando `ticker`, `id_fnet`, `id_documento`, `url_documento`, `data_extracao`, `entidade` (Entidade), `provento` (Provento), com `to_dict()` e `to_text()`
- [ ] 3.4 Atualizar `domain/structured/__init__.py`

## 4. Testes do Domínio

- [ ] 4.1 Testes para `CNPJ`, `ISIN`, `ValorProvento`
- [ ] 4.2 Testes para `Entidade`, `Provento`, `DocumentoProvento`
- [ ] 4.3 Teste para `to_text()` — output contém campos esperados

## 5. Aplicação — Ports e Use Cases

- [ ] 5.1 Definir `ProventosRepository` protocol em `application/structured_ports.py`
- [ ] 5.2 Implementar `ExtrairProventosUseCase` — aceita `ProventosRepository`, `progress_callback`, retorna `list[DocumentoProvento]`
- [ ] 5.3 Tratamento: ticker sem resolução retorna lista vazia; erro em doc individual loga warning e continua

## 6. Testes da Aplicação

- [ ] 6.1 Mock `ProventosRepository` fixture
- [ ] 6.2 Testar use case — sucesso, lista vazia, erro em documento, progress callback

## 7. Infraestrutura — B3FundosClient

- [ ] 7.1 Implementar `B3FundosClient` em `infrastructure/b3/funds_client.py`
- [ ] 7.2 `_build_token(payload)` — serializa JSON, Base64
- [ ] 7.3 `resolver_ticker(ticker) -> str | None` — retorna `None` para tickers sem dados na API
- [ ] 7.4 Cache para `resolver_ticker` com TTL 30 dias (inclusive `None`)
- [ ] 7.5 `listar_documentos(id_fnet, data_inicio, data_fim, tipo)` com paginação
- [ ] 7.6 Cache para `listar_documentos` com TTL 1 dia
- [ ] 7.7 `buscar_html_documento(id_documento)` — GET + encoding

## 8. Infraestrutura — Parsing HTML

- [ ] 8.1 `extrair_por_rotulo()` em `infrastructure/b3/structured_parser.py`
- [ ] 8.2 `extrair_tabelas()` — cabeçalhos, linhas, contexto
- [ ] 8.3 `identificar_tipo_provento()` — verifica colunas X
- [ ] 8.4 `limpar_valor_monetario()`, `converter_data_br_para_iso()`
- [ ] 8.5 `extrair_documento_provento()` — função principal

## 9. Infraestrutura — FundosRepository

- [ ] 9.1 `FundosRepository` implementando `ProventosRepository`
- [ ] 9.2 Delegar para `B3FundosClient`

## 10. Testes Infraestrutura

- [ ] 10.1 Fixtures de HTML real
- [ ] 10.2 Testes de parsing, client mock, repository mock

## 11. CLI

- [ ] 11.1 Adicionar `--structured-earnings`, `--data-inicio`, `--data-fim`, `--output`
- [ ] 11.2 Implementar `run_structured_earnings(args)`
- [ ] 11.3 Dispatch em `main()`

## 12. Testes CLI

- [ ] 12.1 Testar argumentos e saída

## 13. Quality Gate

- [ ] 13.1 `make lint` limpo
- [ ] 13.2 `make test` todos passam
