## Context

O RFC-004 descreve 7 fontes de dados regulatórios e de mercado da B3, mas em formato monolítico sem adaptação à Clean Architecture do FlowScope. As changes `structured-earnings`, `informe-mensal` e `documentos-relevantes` já estabeleceram o padrão arquitetural: entidades em `domain/structured/`, protocolos de repository, use cases, `to_text()` para VectorStore, e `DocumentSource` ABC para `llm-chat`.

A API `GetMaterialFacts` do RFC-004 é a única fonte de dados regulatórios que funciona para qualquer empresa listada na B3 (não apenas FIIs). As outras 3 fontes de documentos são exclusivas de fundos. Sem esta change, o `llm-chat` não conseguiria responder perguntas sobre fatos relevantes de empresas como PETR4, VALE3 ou ITUB4.

O projeto já possui `B3FundosClient` com padrão de token Base64 e `CacheManager`, além de `structured_parser.py` com funções de parsing HTML via BeautifulSoup. A change `llm-chat` define o ABC `DocumentSource` com 3 implementações planejadas — esta change adiciona mais 2, totalizando 5 fontes.

## Goals / Non-Goals

**Goals:**
- Criar entidades de domínio para todos os 7 tipos de dados regulatórios com `to_text()` para VectorStore
- Implementar resolução `ticker → codeCVM` análoga à resolução `ticker → idFNET` existente
- Pipeline completo para `GetMaterialFacts` (fatos relevantes, assembleias, avisos) com paginação e cache
- Pipeline para notícias do Plantão B3 com filtros de data e palavra-chave
- Extração de Censuras Públicas e Condições Excepcionais via parsing HTML
- Duas novas `DocumentSource` para o VectorStore: `MaterialFactsSource` (universal) e `NoticiasSource` (universal)
- Ticker-agnóstico: qualquer ticker pode ser consultado; fontes retornam vazio quando não há dados
- CLI: `--fatos-relevantes`, `--noticias`, `--regulacao`

**Non-Goals:**
- OCR em PDFs referenciados pelo `GetMaterialFacts` (apenas metadados e `to_text()`)
- GUI para dados regulatórios nesta change
- Paralelismo/async
- Programas de Aquisição (seção 3.3 do RFC-004) — análise de HTML pendente; escopo futuro
- Download de PDFs dos documentos CVM (URLs são expostas, mas download é delegado ao usuário)
- Persistência em banco de dados

## Decisions

### 1. Extensão de `B3FundosClient` para `listedCompaniesProxy`

**Decisão:** Adicionar métodos para `listedCompaniesProxy` ao `B3FundosClient` existente, sem criar uma nova classe cliente.

**Alternativa considerada:** Novo `B3ListedClient` dedicado ao domínio `listedCompaniesProxy`.
**Rejeitada porque:** `B3FundosClient` já possui injeção de `CacheManager`, construção de token Base64 (mesmo padrão), e opera no mesmo domínio base `sistemaswebb3-listados.b3.com.br`. Uma terceira classe cliente adicionaria indireção sem benefício. O nome `B3FundosClient` pode ser renomeado no futuro se necessário, mas a separação de responsabilidades é mantida pela organização dos métodos.

**Consequências:** `B3FundosClient` ganha os métodos `resolver_code_cvm()`, `listar_fatos_relevantes()` e `listar_noticias()`. Nenhuma nova classe no módulo `infrastructure/b3/`.

### 2. Resolução `ticker → codeCVM` com cache

**Decisão:** Implementar `resolver_code_cvm(ticker)` no `B3FundosClient` que consulta a API `listedCompaniesProxy` para mapear ticker para código CVM. Cache TTL de 30 dias, armazenando inclusive `None` para tickers sem código CVM.

**Alternativa considerada:** Hardcode de mapeamento ticker→codeCVM para tickers comuns.
**Rejeitada porque:** A B3 lista centenas de empresas; hardcode seria frágil e teria alta manutenção. A API `listedCompaniesProxy` deve expor um endpoint de listagem de empresas que permite a resolução dinâmica.

**Consequências:** Similar à resolução `ticker → idFNET` — uma chamada de API com cache. Cache compartilhado via `CacheManager` com chave `codecvm_{ticker}`.

**Open question:** O endpoint exato de listagem de empresas precisa ser confirmado durante a implementação. Se não existir endpoint direto, fallback: download do cadastro de empresas listadas em CSV da B3 e construção de índice local.

### 3. Entidades unificadas em `domain/structured/`

**Decisão:** Todas as entidades regulatórias são adicionadas a `domain/structured/entities.py` e `domain/structured/value_objects.py`, seguindo o padrão das outras changes que colocalizam suas entidades nesses mesmos arquivos.

**Alternativa considerada:** Módulo separado `domain/regulatorio/`.
**Rejeitada porque:** A ADR-002 (decisão 1) estabeleceu `domain/structured/` como o namespace para todas as entidades de dados estruturados da B3. Criar um novo namespace fragmentaria o domínio sem ganho arquitetural.

**Consequências:** Extensão de `entities.py` com ~8 novas dataclasses e `value_objects.py` com ~4 novos value objects. Arquivo `entities.py` cresce mas mantém coesão de domínio.

### 4. Duas `DocumentSource`, não uma só

**Decisão:** Criar duas implementações separadas de `DocumentSource`:
- `MaterialFactsSource`: alimenta o VectorStore com documentos de `GetMaterialFacts` (fatos relevantes, assembleias, avisos). Universal — funciona para qualquer ticker com `codeCVM`.
- `NoticiasSource`: alimenta o VectorStore com notícias do Plantão B3. Universal — não depende de ticker.

**Alternativa considerada:** Uma única `RegulacaoSource` unificando todos os tipos.
**Rejeitada porque:** `MaterialFactsSource` e `NoticiasSource` têm origens de dados radicalmente diferentes (API paginada com token Base64 vs. API REST simples com query params), escopos distintos (ticker-específico vs. mercado geral) e granularidades de atualização diferentes (diário vs. horário). O ABC `DocumentSource` existe justamente para isolar fontes com comportamentos distintos.

**Consequências:** O `IndexarDocumentosUseCase` do `llm-chat` itera sobre 5 fontes no total. Cada fonte segue o contrato do ABC e é testável independentemente.

**Fora do escopo como DocumentSource:** Censuras Públicas e Condições Excepcionais. São dados de referência (não ticker-específicos para busca) que podem ser adicionados como `DocumentSource` futura se necessário.

### 5. Categorias de `GetMaterialFacts` como enum

**Decisão:** Mapear as 5 categorias documentadas no RFC-004 como um `Enum` `CategoriaMaterialFact` no módulo de domínio:

```python
class CategoriaMaterialFact(Enum):
    ASSEMBLEIAS = "1"
    AVISO_ACIONISTAS = "3"
    FATOS_RELEVANTES = "4"
    AVISO_DEBENTURISTAS = "48"
    RELATORIO_PROVENTOS = "107"
```

**Alternativa considerada:** Strings livres passadas como parâmetro.
**Rejeitada porque:** O enum documenta as categorias disponíveis, fornece autocomplete, e valida entradas. O RFC-004 recomenda "Mapear todas as categorias disponíveis" — o enum é extensível quando novas categorias forem descobertas.

**Consequências:** O CLI e o `MaterialFactsSource` usam o enum para validação e iteração sobre categorias.

### 6. Pipeline CLI unificado com subcomandos implícitos

**Decisão:** Expor 3 argumentos CLI mutuamente exclusivos na prática (mas tecnicamente compossíveis):
- `--fatos-relevantes <TICKER>`: extrai via `GetMaterialFacts`
- `--noticias`: lista notícias do Plantão B3
- `--regulacao`: extrai censuras e condições excepcionais

Cada argumento dispara uma parte diferente do `ExtrairDadosRegulatoriosUseCase`, com `--categoria`, `--palavra`, `--data-inicio`, `--data-fim` como filtros comuns.

**Alternativa considerada:** Subcomandos estilo git (`flowscope regulacao noticias`, `flowscope regulacao fatos`).
**Rejeitada porque:** O padrão CLI do projeto usa flags planas (`--structured-earnings`, `--informe-mensal`), não subcomandos. Manter consistência com o estilo existente.

**Consequências:** O `cli.py` ganha 3 blocos de dispatch condicional. Reutiliza `--data-inicio`, `--data-fim` já definidos por `structured-earnings`. Novo argumento `--categoria` para filtrar tipo de documento no `GetMaterialFacts`.

### 7. Parsing HTML com funções puras, não classes

**Decisão:** Funções puras em `infrastructure/b3/structured_parser.py` para extração de Censuras e Condições Excepcionais, seguindo o padrão de parsing encadeado da ADR-002 (decisão 6).

**Alternativa considerada:** Classes de parser com estado.
**Rejeitada porque:** O parsing é stateless (entrada HTML → saída lista de entidades). Funções puras são mais testáveis e alinhadas ao estilo do projeto.

**Consequências:** Novas funções: `extrair_censuras(html: str) -> list[CensuraPublica]`, `extrair_condicoes_excepcionais(html: str) -> list[CondicaoExcepcional]`. Fallback: campos não encontrados ficam `None`, sem interromper o pipeline.

### 8. Cache com TTLs diferenciados por fonte

**Decisão:** TTLs específicos por tipo de dado, armazenados via `CacheManager`:

| Fonte | Chave de cache | TTL | Justificativa |
|---|---|---|---|
| Resolução codeCVM | `codecvm_{ticker}` | 30 dias | Código CVM não muda |
| GetMaterialFacts | `matfacts_{codeCVM}_{cat}_{ini}_{fim}` | 1 dia | Documentos novos aparecem diariamente |
| Notícias | `noticias_{agencia}_{ini}_{fim}_{palavra}` | 1 hora | Notícias são atualizadas ao longo do dia |
| Censuras | `censuras_publicas` | 7 dias | Atualização esporádica |
| Condições Excepcionais | `condicoes_excepcionais` | 7 dias | Atualização esporádica |

**Alternativa considerada:** TTL único de 1 dia para todos.
**Rejeitada porque:** Notícias precisam de atualização mais frequente; censuras raramente mudam. TTLs diferenciados equilibram frescor dos dados com eficiência de rede.

**Consequências:** Cada método no repository aplica o TTL apropriado ao chamar `CacheManager.get_or_fetch()`.

### 9. `to_text()` focado em informação semanticamente densa

**Decisão:** Cada entidade expõe `to_text()` que produz texto adequado para chunking e embedding. O texto inclui ticker, datas, tipo de documento e conteúdo descritivo, mas omite metadados técnicos irrelevantes para busca semântica (URLs, IDs internos, versões).

**Exemplo para `FatoRelevante`:**
```
[Fato Relevante] PETROBRAS (PETR4) — 16/04/2026
Categoria: Assembleia | Tipo: AGO | Espécie: Ata
Assunto: Tomada de Contas-Votação do Relatório da Administração...
Status: Ativo
```

**Alternativa considerada:** JSON serializado como texto.
**Rejeitada porque:** Embeddings capturam melhor a semântica de texto natural. JSON serializado introduz ruído (chaves, aspas, estrutura) que reduz a qualidade da busca semântica.

**Consequências:** `DocumentoProvento.to_text()`, `InformeMensal.to_text()` (já definidos) e as novas entidades seguem o mesmo padrão de formatação.

## Risks / Trade-offs

- **[Risco] Mudança na estrutura HTML da B3 (censuras, condições)** → Mitigação: seletores CSS com fallback. Campos não encontrados ficam `None`. Log de warning quando a estrutura difere do esperado.
- **[Risco] `GetMaterialFacts` requer `codeCVM` e a resolução `ticker → codeCVM` pode não ter endpoint direto** → Mitigação: fallback para download do cadastro de empresas listadas em CSV da B3 (`ConsultarRendaVariavel`) e construção de índice local. Verificar durante implementação.
- **[Risco] Endpoint de Notícias pode ter paginação não documentada** → Mitigação: tratar resposta como paginada; se `totalPages` for 1, iterar não tem efeito colateral.
- **[Trade-off] Sem GUI para dados regulatórios** → Escopo gerenciável. CLI cobre extração. A GUI é indiretamente beneficiada via `llm-chat` (VectorStore populado com dados regulatórios). Extensão futura pode adicionar painéis de notícias/regulação.
- **[Trade-off] `B3FundosClient` acumula responsabilidades de múltiplos domínios de API** → O nome "Fundos" se torna parcialmente impreciso. Aceito como dívida técnica de naming; refatoração futura pode renomear para `B3APIClient` se necessário.
- **[Trade-off] Sem Programas de Aquisição** → RFC-004 admite que a seção requer análise adicional. Postergado para evitar bloqueio das outras 6 fontes.
