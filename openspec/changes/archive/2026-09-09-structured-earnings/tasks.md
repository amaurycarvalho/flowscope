## 1. Dependências e Estrutura

- [x] 1.1 Adicionar `beautifulsoup4` ao `pyproject.toml` em `dependencies`
- [x] 1.2 Criar estrutura de diretórios: `domain/structured/`, testes correspondentes
- [x] 1.3 Rodar `make install` para instalar nova dependência

## 2. Domínio — Value Objects

- [x] 2.1 Implementar `CNPJ` em `domain/structured/value_objects.py` com validação de formato `XX.XXX.XXX/XXXX-XX`
- [x] 2.2 Implementar `ISIN` com validação de 12 caracteres e prefixo BR
- [x] 2.3 Implementar `ValorProvento` aceitando string monetária brasileira e `Decimal`
- [x] 2.4 Criar `domain/structured/__init__.py` exportando todos os value objects

## 3. Domínio — Entidades

- [x] 3.1 Implementar `Entidade` dataclass com `nome`, `cnpj` (CNPJ), `nome_administrador`, `cnpj_administrador` (CNPJ), `responsavel`, `telefone`
- [x] 3.2 Implementar `Provento` dataclass com `codigo_isin` (ISIN), `codigo_negociacao`, `tipo`, `data_base`, `valor_por_unidade` (ValorProvento), `data_pagamento`, `periodo_referencia`, `isento_ir`, `nota_isencao`
- [x] 3.3 Implementar `DocumentoProvento` agregando `ticker`, `id_fnet`, `id_documento`, `url_documento`, `data_extracao`, `entidade` (Entidade), `provento` (Provento), com `to_dict()` e `to_text()`
- [x] 3.4 Atualizar `domain/structured/__init__.py`

## 4. Testes do Domínio

- [x] 4.1 Testes para `CNPJ`, `ISIN`, `ValorProvento`
- [x] 4.2 Testes para `Entidade`, `Provento`, `DocumentoProvento`
- [x] 4.3 Teste para `to_text()` — output contém campos esperados

## 5. Aplicação — Ports e Use Cases

- [x] 5.1 Definir `ProventosRepository` protocol em `application/structured_ports.py`
- [x] 5.2 Implementar `ExtrairProventosUseCase` — aceita `ProventosRepository`, `progress_callback`, retorna `list[DocumentoProvento]`
- [x] 5.3 Tratamento: ticker sem resolução retorna lista vazia; erro em doc individual loga warning e continua

## 6. Testes da Aplicação

- [x] 6.1 Mock `ProventosRepository` fixture
- [x] 6.2 Testar use case — sucesso, lista vazia, erro em documento, progress callback

## 7. Infraestrutura — B3FundosClient

- [x] 7.1 Implementar `B3FundosClient` em `infrastructure/b3/funds_client.py`
- [x] 7.2 `_build_token(payload)` — serializa JSON, Base64
- [x] 7.3 `resolver_ticker(ticker) -> str | None` — retorna `None` para tickers sem dados na API
- [x] 7.4 Cache para `resolver_ticker` com TTL 30 dias (inclusive `None`)
- [x] 7.5 `listar_documentos(id_fnet, data_inicio, data_fim, tipo)` com paginação
- [x] 7.6 Cache para `listar_documentos` com TTL 1 dia
- [x] 7.7 `buscar_html_documento(id_documento)` — GET + encoding

## 8. Infraestrutura — Parsing HTML

- [x] 8.1 `extrair_por_rotulo()` em `infrastructure/b3/structured_parser.py`
- [x] 8.2 `extrair_tabelas()` — cabeçalhos, linhas, contexto
- [x] 8.3 `identificar_tipo_provento()` — verifica colunas X
- [x] 8.4 `limpar_valor_monetario()`, `converter_data_br_para_iso()`
- [x] 8.5 `extrair_documento_provento()` — função principal

## 9. Infraestrutura — FundosRepository

- [x] 9.1 `FundosRepository` implementando `ProventosRepository`
- [x] 9.2 Delegar para `B3FundosClient`

## 10. Testes Infraestrutura

- [x] 10.1 Fixtures de HTML real
- [x] 10.2 Testes de parsing, client mock, repository mock

## 11. CLI

- [x] 11.1 Adicionar `--structured-earnings`, `--data-inicio`, `--data-fim`, `--output`
- [x] 11.2 Implementar `run_structured_earnings(args)`
- [x] 11.3 Dispatch em `main()`

## 12. Testes CLI

- [x] 12.1 Testar argumentos e saída

## 13. Quality Gate

- [x] 13.1 `make lint` limpo
- [x] 13.2 `make test` todos passam
