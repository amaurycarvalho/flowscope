## 1. Estrutura e Dependências

- [ ] 1.1 Verificar que `beautifulsoup4` está disponível (já adicionado por `structured-earnings`)
- [ ] 1.2 Criar diretórios de teste: `tests/test_infrastructure/test_regulacao/`, `tests/test_domain/test_structured/`

## 2. Domínio — Value Objects

- [ ] 2.1 Implementar `CodeCVM` em `domain/structured/value_objects.py` como string validada (campo numérico da B3)
- [ ] 2.2 Implementar `CategoriaMaterialFact` enum em `domain/structured/value_objects.py` com membros: ASSEMBLEIAS="1", AVISO_ACIONISTAS="3", FATOS_RELEVANTES="4", AVISO_DEBENTURISTAS="48", RELATORIO_PROVENTOS="107"
- [ ] 2.3 Atualizar `domain/structured/__init__.py` exportando novos value objects

## 3. Domínio — Entidades Regulatórias

- [ ] 3.1 Implementar `CensuraPublica` dataclass com `titulo`, `ticker` (str | None), `data`, `conteudo` e `to_text()`
- [ ] 3.2 Implementar `CondicaoExcepcional` dataclass com `companhia`, `segmento` (str | None), `condicao`, `data_concessao` (str | None), `prazo` (str | None) e `to_text()`
- [ ] 3.3 Implementar `NoticiaB3` dataclass com `titulo`, `data_publicacao`, `url` (str | None), `agencia` e `to_text()`
- [ ] 3.4 Implementar `DocumentoMaterialFact` dataclass base com campos comuns do `GetMaterialFacts`: `code_cvm`, `empresa`, `ticker`, `data_referencia`, `data_entrega`, `categoria`, `tipo`, `especie`, `status`, `assunto`, `url_documento`, `url_download`
- [ ] 3.5 Implementar `FatoRelevante(DocumentoMaterialFact)` com `to_text()` contextualizado para fatos relevantes
- [ ] 3.6 Implementar `Assembleia(DocumentoMaterialFact)` com campos adicionais `tipo_assembleia`, `especie_documento` e `to_text()`
- [ ] 3.7 Implementar `AvisoAcionista(DocumentoMaterialFact)` e `AvisoDebenturista(DocumentoMaterialFact)` com `to_text()`
- [ ] 3.8 Atualizar `domain/structured/__init__.py` exportando todas as novas entidades

## 4. Testes do Domínio

- [ ] 4.1 Testes para `CodeCVM` — validação, str(), igualdade
- [ ] 4.2 Testes para `CategoriaMaterialFact` — 5 membros, iteração, validação de código inválido
- [ ] 4.3 Testes para `CensuraPublica` — instanciação, campos obrigatórios, `to_text()` contém ticker e conteúdo
- [ ] 4.4 Testes para `CondicaoExcepcional` — instanciação, campos opcionais como None
- [ ] 4.5 Testes para `NoticiaB3` — instanciação, `to_text()` contém título e data
- [ ] 4.6 Testes para `DocumentoMaterialFact` e subclasses — hierarquia, `to_text()` específico por subclasse

## 5. Infraestrutura — Resolução codeCVM

- [ ] 5.1 Adicionar método `resolver_code_cvm(ticker: str) -> str | None` ao `B3FundosClient`
- [ ] 5.2 Implementar consulta à API `listedCompaniesProxy` para obter código CVM a partir do ticker
- [ ] 5.3 Cache via `CacheManager` com chave `codecvm_{ticker}`, TTL 30 dias, armazenando inclusive `None`
- [ ] 5.4 Fallback: se API direta não existir, baixar cadastro de empresas listadas (CSV) e construir índice ticker→codeCVM

## 6. Testes da Resolução codeCVM

- [ ] 6.1 Mock da API `listedCompaniesProxy` — retorna codeCVM para PETR4, None para ticker inválido
- [ ] 6.2 Testar cache: segunda chamada não gera requisição HTTP
- [ ] 6.3 Testar cache de None: ticker sem codeCVM não é reconsultado

## 7. Infraestrutura — GetMaterialFacts

- [ ] 7.1 Adicionar método `listar_fatos_relevantes(code_cvm, categoria, data_inicio, data_fim)` ao `B3FundosClient`
- [ ] 7.2 Construção de token Base64 com payload: `linguagem`, `codeCVM`, `year`, `dataInicial`, `dataFinal`, `categoria`, `pageNumber`, `pageSize`
- [ ] 7.3 Paginação automática: detectar `totalPages` na resposta e iterar páginas 2..N
- [ ] 7.4 Conversão dos resultados JSON para entidades de domínio (`FatoRelevante`, `Assembleia`, `AvisoAcionista`, `AvisoDebenturista`) conforme `category` do resultado
- [ ] 7.5 Cache via `CacheManager` com chave `matfacts_{codeCVM}_{cat}_{ini}_{fim}`, TTL 1 dia
- [ ] 7.6 Tratamento de erro: API indisponível loga warning e retorna lista vazia

## 8. Infraestrutura — Notícias (Plantão B3)

- [ ] 8.1 Adicionar método `listar_noticias(agencia, data_inicio, data_fim, palavra)` ao `B3FundosClient`
- [ ] 8.2 Requisição GET a `PlantaoNoticias/Noticias/ListarTitulosNoticias` com query params
- [ ] 8.3 Suporte a paginação (se endpoint retornar `totalPages`)
- [ ] 8.4 Conversão dos resultados JSON para entidades `NoticiaB3`
- [ ] 8.5 Cache via `CacheManager` com chave `noticias_{agencia}_{ini}_{fim}_{palavra}`, TTL 1 hora

## 9. Infraestrutura — Parsing HTML Regulatório

- [ ] 9.1 Adicionar `extrair_censuras(html: str) -> list[CensuraPublica]` em `infrastructure/b3/structured_parser.py`
- [ ] 9.2 Extração de ticker via regex `\(([A-Z0-9]+)\)` no título
- [ ] 9.3 Extração de data via regex `\((\d{2}/\d{2}/\d{4})\)`
- [ ] 9.4 Fallback: campos não encontrados ficam `None`, parsing continua
- [ ] 9.5 Adicionar `extrair_condicoes_excepcionais(html: str) -> list[CondicaoExcepcional]` em `structured_parser.py`
- [ ] 9.6 Parsing de tabela HTML com 5 colunas (Companhia, Segmento, Condição, Data Concessão, Prazo)
- [ ] 9.7 Adicionar `listar_censuras()` e `listar_condicoes_excepcionais()` ao `B3FundosClient` (fetch HTML + parse + cache)
- [ ] 9.8 Cache com TTL 7 dias para ambos

## 10. Testes de Infraestrutura — Parsing HTML

- [ ] 10.1 Fixture com HTML real de censuras públicas (exemplo do RFC-004)
- [ ] 10.2 Testar `extrair_censuras()` — ticker extraído, data extraída, conteúdo presente
- [ ] 10.3 Testar `extrair_censuras()` com título sem ticker — retorna `ticker=None`
- [ ] 10.4 Testar `extrair_censuras()` com HTML vazio — retorna `[]`
- [ ] 10.5 Fixture com HTML real de condições excepcionais (exemplo do RFC-004)
- [ ] 10.6 Testar `extrair_condicoes_excepcionais()` — 5 colunas mapeadas corretamente
- [ ] 10.7 Testar `extrair_condicoes_excepcionais()` com linha de menos colunas — linha pulada, warning logado

## 11. Testes de Infraestrutura — APIs

- [ ] 11.1 Mock do endpoint `GetMaterialFacts` — resposta com 1 página, 3 documentos
- [ ] 11.2 Mock do endpoint `GetMaterialFacts` — resposta com 3 páginas (testar paginação)
- [ ] 11.3 Testar `listar_fatos_relevantes()` — cache, TTL, paginação
- [ ] 11.4 Mock do endpoint `ListarTitulosNoticias`
- [ ] 11.5 Testar `listar_noticias()` — cache, TTL 1 hora, filtro de palavra

## 12. Aplicação — Protocolo e Use Case

- [ ] 12.1 Definir `RegulacaoRepository` protocol em `application/structured_ports.py` com métodos: `resolver_code_cvm`, `listar_fatos_relevantes`, `listar_noticias`, `listar_censuras`, `listar_condicoes_excepcionais`
- [ ] 12.2 Implementar `ExtrairDadosRegulatoriosUseCase` em `application/structured_use_cases.py` — orquestra extração conforme tipo solicitado (fatos, noticias, regulacao)
- [ ] 12.3 Tratamento: ticker sem codeCVM retorna lista vazia; erro em categoria individual loga warning e continua

## 13. Infraestrutura — DocumentSources para llm-chat

- [ ] 13.1 Criar `infrastructure/document_sources/material_facts_source.py` com `MaterialFactsSource(DocumentSource)`
- [ ] 13.2 `MaterialFactsSource.obter_documentos(ticker)` — resolve codeCVM, itera 5 categorias, coleta `to_text()`
- [ ] 13.3 Tolerância a falhas: se uma categoria falhar, continua para as próximas
- [ ] 13.4 Criar `infrastructure/document_sources/noticias_source.py` com `NoticiasSource(DocumentSource)`
- [ ] 13.5 `NoticiasSource.obter_documentos()` — ignora ticker, consulta Plantão B3 últimos 30 dias
- [ ] 13.6 Período padrão configurável no construtor (`dias: int = 30`)

## 14. Testes das DocumentSources

- [ ] 14.1 Testar `MaterialFactsSource.obter_documentos("PETR4")` — retorna documentos com `to_text()`
- [ ] 14.2 Testar `MaterialFactsSource.obter_documentos("TICKER_INVALIDO")` — retorna `[]`
- [ ] 14.3 Testar `MaterialFactsSource` com falha em uma categoria — continua e loga warning
- [ ] 14.4 Testar `NoticiasSource.obter_documentos()` — retorna notícias com `to_text()`

## 15. CLI — Argumentos e Integração

- [ ] 15.1 Adicionar `--fatos-relevantes` (str, ticker) ao parser em `presentation/cli.py`
- [ ] 15.2 Adicionar `--noticias` (flag) ao parser
- [ ] 15.3 Adicionar `--regulacao` (flag) ao parser
- [ ] 15.4 Adicionar `--categoria` (str) ao parser
- [ ] 15.5 Adicionar `--palavra` (str) ao parser
- [ ] 15.6 Reutilizar `--data-inicio` e `--data-fim` existentes para filtros de período
- [ ] 15.7 Implementar dispatch: quando `--fatos-relevantes` é usado, executa `ExtrairDadosRegulatoriosUseCase` com tipo fatos
- [ ] 15.8 Implementar dispatch: quando `--noticias` é usado, executa `ExtrairDadosRegulatoriosUseCase` com tipo noticias
- [ ] 15.9 Implementar dispatch: quando `--regulacao` é usado, executa `ExtrairDadosRegulatoriosUseCase` com tipo regulacao
- [ ] 15.10 Output JSON formatado em stdout para todos os comandos

## 16. Testes do CLI

- [ ] 16.1 Testar `--fatos-relevantes PETR4` — output JSON contém companyName e código CVM
- [ ] 16.2 Testar `--fatos-relevantes PETR4 --categoria 4` — apenas Fatos Relevantes
- [ ] 16.3 Testar `--noticias --data-inicio 2026-07-01 --data-fim 2026-07-29` — output JSON
- [ ] 16.4 Testar `--noticias --palavra PETROBRAS` — filtro aplicado
- [ ] 16.5 Testar `--regulacao` — output JSON com censuras e condições
- [ ] 16.6 Testar cenário sem dados — ticker sem codeCVM retorna JSON vazio, sem crash
