# Fontes de Dados do FlowScopeBR

Este documento reúne todas as fontes de dados consumidas pelo FlowScopeBR:
URLs, parâmetros/payloads de entrada, formatos de saída, normalização aplicada,
cache local e regras de fallback.

As fontes externas são públicas e não exigem cadastro ou chave de API, com
exceção opcional dos provedores de LLM. Nas fontes públicas, a aplicação faz
apenas leituras; as únicas requisições `POST` são a consulta da tabela de
empréstimos da B3 e o download de PDFs do visualizador da CVM.

---

## 1. Visão geral

| Fonte | Uso no FlowScopeBR | Endpoint principal | Entrada | Saída |
| --- | --- | --- | --- | --- |
| B3 — Arquivos | Cotações diárias do pregão | `https://arquivos.b3.com.br/api/download/...` | query string | CSV |
| B3 — Índices | Carteira de IBOV, IDIV e IFIX | `https://sistemaswebb3-listados.b3.com.br/indexProxy/indexCall/...` | JSON em Base64 | CSV em Base64 |
| B3 — BDI | Ações alugadas (_short interest_) | `https://arquivos.b3.com.br/bdi/table/BTBLendingOpenPosition/...` | `POST` com JSON `{}` | JSON tabular |
| B3 — Fundos listados | Identidade de FIIs e relatórios | `https://sistemaswebb3-listados.b3.com.br/fundsListedProxy/Search/...` | JSON em Base64 | JSON |
| B3 — Empresas listadas | `codeCVM` e material facts | `https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/...` | JSON em Base64 | JSON |
| B3 — Programas | Programas de aquisição de ações | `https://sistemaswebb3-listados.b3.com.br/stockProgramProxy/...` | JSON em Base64 | JSON |
| B3 — Plantão de Notícias | Notícias e avisos aos acionistas | `https://sistemasweb.b3.com.br/PlantaoNoticias/Noticias/...` | query string | JSON / HTML |
| B3 — Regulatório | Censuras e condições excepcionais | `https://www.b3.com.br/pt_br/regulacao/...` | — | HTML |
| FNET | Documentos de fundos | `https://fnet.bmfbovespa.com.br/fnet/publico/...` | query string | HTML / PDF |
| CVM — Dados Abertos | Informes, DFIN, FRE e FCA | `https://dados.cvm.gov.br/dados/...` | `GET`/`HEAD` condicional | ZIP / CSV |
| CVM — RAD | PDFs de documentos regulatórios | `https://www.rad.cvm.gov.br/ENETWEB/...` | `POST` JSON | JSON com PDF em Base64 |
| Fundamentus | Fundamentos, FFO e proventos | `https://fundamentus.com.br/...` | query string | HTML |
| LLM | Resumos e Chat AI (opcional) | endpoints OpenAI-compatible | JSON | JSON |
| GitHub | Verificação de nova versão | `https://github.com/amaurycarvalho/flowscope/releases/latest` | — | redirecionamento/HTML |
| Locais | Watchlist, configuração e cache | sistema de arquivos | texto / JSON | texto / JSON |

### 1.1 Convenções dos endpoints B3 em Base64

Os proxies da B3 recebem o payload como JSON compacto codificado em Base64 no
próprio caminho da URL:

```python
import base64, json

payload = {"language": "pt-br", "typeFund": "FII", "pageNumber": 1, "pageSize": 20}
token = base64.b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode()
url = f"https://sistemaswebb3-listados.b3.com.br/fundsListedProxy/Search/GetListFunds/{token}"
```

O mesmo mecanismo é usado por `fundsListedProxy`, `listedCompaniesProxy`,
`stockProgramProxy` e pela carteira de índices. A decodificação das respostas
também pode vir em Base64 (carteiras de índice).

### 1.2 Tratamento de falhas e cache

- A maioria das fontes é tolerante a falha: indisponibilidade vira lista vazia
  ou campo `N/A`, sem interromper a análise dos demais tickers.
- Há retry com backoff para erros transitórios de rede/HTTP. O FNET trata
  `403` intermitente como repetível; a API de programas da B3 trata `404`
  intermitente como repetível.
- Cache em disco no diretório padrão do sistema:
  - Linux: `~/.cache/flowscope`
  - Windows: `%LOCALAPPDATA%\flowscope\cache`
  - macOS: `~/Library/Caches/flowscope`
- Arquivos CSV da CVM usam `latin1` e delimitador `;`. Os CSVs da B3 usam
  delimitador `;` e codificação detectada pela resposta HTTP.

---

## 2. B3 — dados de mercado

### 2.1 Cotações diárias (`TradeInformationConsolidated`)

**Módulos:** `infrastructure/b3/client.py`, `infrastructure/b3/parser.py`,
`infrastructure/b3/repository.py`

O download é feito em duas etapas:

```text
GET https://arquivos.b3.com.br/api/download/requestname
    ?fileName=TradeInformationConsolidated
    &date=2026-06-25

→ {"token": "<token>"}   (ou {"redirectUrl": "<url>"})

GET https://arquivos.b3.com.br/api/download/
    ?token=<token>

→ CSV
```

**Entrada**

| Parâmetro | Formato | Exemplo |
| --- | --- | --- |
| `fileName` | texto | `TradeInformationConsolidated` |
| `date` | `AAAA-MM-DD` | `2026-06-25` |

Dias não úteis (fim de semana/feriado) não são requisitados e retornam `None`.

**Saída bruta — CSV**

Cabeçalho esperado:

```text
RptDt;TckrSymb;SgmtNm;MinPric;MaxPric;TradAvrgPric;LastPric;TradQty;NtlFinVol;FinInstrmQty
2026-06-25;PETR4;CASH;28,50;29,10;28,80;28,90;15000;432000;15000
```

**Normalização**

Cada linha do segmento `CASH` vira um `TradeDay`:

| Campo | Origem |
| --- | --- |
| `date` | `RptDt` |
| `ticker` | `TckrSymb` |
| `segment` | `SgmtNm` |
| `min_price` | `MinPric` |
| `max_price` | `MaxPric` |
| `avg_price` | `TradAvrgPric` |
| `last_price` | `LastPric` |
| `trades_qty` | `TradQty` |
| `fin_vol` | `NtlFinVol` |
| `fin_instr_qty` | `FinInstrmQty` |

**Cache:** um arquivo por data, `<cache>/AAAA-MM-DD.csv`, sem expiração. Com
`cache_only`, os dias ausentes não são baixados.

### 2.2 Carteiras de índice (IBOV, IDIV, IFIX)

**Módulos:** `infrastructure/b3/client.py`, `infrastructure/b3/parser.py`

```text
GET https://sistemaswebb3-listados.b3.com.br/indexProxy/indexCall/
    GetDownloadPortfolioDay/{BASE64}
```

**Entrada — JSON antes do Base64**

```json
{"index": "IBOV", "language": "pt-br"}
```

Índices aceitos: `IBOV`, `IDIV` e `IFIX`.

**Saída bruta**

A resposta é um CSV em Base64, por exemplo:

```text
IBOV - Carteira do Dia 28/06/26
Código;Ação;Tipo;Qtde. Teórica;Part. (%)
VALE3;VALE;ON      NM;542.345.678;11,432;
PETR4;PETROBRAS;PN      N2;398.765.432;9,876;
Quantidade Teórica Total;;;1.427.530.863;100,000
Redutor;;;0,99999999;
```

**Saída normalizada:** `list[str]` com os tickers válidos da carteira.

**Cache:** chave `portfolio_<ÍNDICE>` em JSON, TTL de 7 dias. Resultados vazios
são invalidados para não congelar falhas transitórias.

### 2.3 Ações alugadas / _short interest_ (`BTBLendingOpenPosition`)

**Módulo:** `infrastructure/b3/emprestimos.py`

```text
POST https://arquivos.b3.com.br/bdi/table/BTBLendingOpenPosition/
     {AAAA-MM-DD}/{AAAA-MM-DD}/{página}/{take}
Content-Type: application/json

{}
```

- `take` máximo usado: `1000`.
- Headers: `Accept: application/json` e `User-Agent` de navegador.

**Saída bruta — JSON**

```json
{
  "table": {
    "name": "BTBLendingOpenPosition",
    "pageCount": 1,
    "columns": [
      {"name": "RptDt"}, {"name": "DtRef"}, {"name": "TckrSymb"},
      {"name": "ISIN"}, {"name": "Company"}, {"name": "Type"},
      {"name": "Market"}, {"name": "StockBalance"}, {"name": "AvgPric"},
      {"name": "Balance"}
    ],
    "values": [
      ["2026-09-22", "2026-09-22", "PETR4", "BRPETRACNPR6",
       "PETROLEO BRASILEIRO S.A. PETROBRAS", "PN N2",
       "Neg. Eletrônica D+1", 53184474, 30.0, 1595534220.0],
      ["2026-09-22", "2026-09-22", "PETR4", "BRPETRACNPR6",
       "PETROLEO BRASILEIRO S.A. PETROBRAS", "PN N2",
       "Total", 194503553, null, null]
    ]
  },
  "status": 5
}
```

**Normalização:** mapa `ticker → Decimal` com a soma de `StockBalance` das
linhas `Market = "Total"`; na ausência da linha `Total`, soma as demais linhas
do ticker.

**Cache:** por data (`b3_emprestimos_btb-v1_AAAA-MM-DD.json`). Como a B3
publica a posição do pregão anterior, a consulta recua até 7 dias. Cache vazio
é descartado para permitir nova tentativa após a publicação.

---

## 3. B3 — fundos, empresas e documentos

O cliente `B3FundosClient` organiza as consultas em mixins:
`fundos`, `documentos`, `documentos_relevantes`, `code_cvm`,
`material_facts`, `noticias` e `regulatorio`.

### 3.1 Identidade de fundos e resolução de ticker

**Módulos:** `infrastructure/b3/funds_client/fundos.py`,
`fundos_helpers.py`, `infrastructure/b3/fund_repository.py`

#### `GetListFunds`

```text
GET https://sistemaswebb3-listados.b3.com.br/fundsListedProxy/Search/
    GetListFunds/{BASE64}
```

**Entrada**

```json
{
  "language": "pt-br",
  "typeFund": "FII",
  "pageNumber": 1,
  "pageSize": 20
}
```

`typeFund` é tentado em `FII`, `FIAGRO`, `FIP` e `FIDC`.

**Saída**

```json
{
  "page": {"pageNumber": 1, "pageSize": 20, "totalRecords": 2, "totalPages": 1},
  "results": [
    {"id": "870", "idMain": null, "acronym": "ALZR",
     "fundName": "ALIANZA TRUST RENDA IMOBILIÁRIA - FII",
     "tradingName": "Fundo: 28.737.771/0001-85"}
  ]
}
```

O `acronym` é comparado com a raiz do ticker (sem o sufixo numérico). O
resultado é cacheado por 30 dias (`fundos_listados_<TIPO>`).

#### `GetListClassFund`

```text
GET https://sistemaswebb3-listados.b3.com.br/fundsListedProxy/Search/
    GetListClassFund/{BASE64}
```

**Entrada**

```json
{
  "language": "pt-br",
  "idFNET": "870",
  "idCEM": "ALZR",
  "typeFund": "FII"
}
```

**Saída:** lista de classes do fundo:

```json
[
  {"id": "870", "idMain": null, "fundName": "...", "tradingName": "Fundo: 28.737.771/0001-85"},
  {"id": "20294", "idMain": "870", "fundName": "...", "tradingName": "28.737.771/0001-85"}
]
```

A aplicação prefere o registro com `idMain` não nulo. O `id` resultante é o
`idFNET` usado nos relatórios; o `tradingName` é usado para extrair o CNPJ do
fundo quando aplicável.

**Saída normalizada:** `B3Fund(ticker, fnet_id, primary_id, name, trading_name)`.

**Cache:** candidatos e resolução de ticker por 30 dias.

### 3.2 `codeCVM` e nome de empresas listadas

**Módulo:** `infrastructure/b3/funds_client/code_cvm.py`

```text
GET https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/
    GetInitialCompanies/{BASE64}
```

**Entrada**

```json
{
  "language": "pt-br",
  "pageNumber": 1,
  "pageSize": 120,
  "company": "PETR"
}
```

**Saída**

```json
{
  "page": {"pageNumber": 1, "pageSize": 120, "totalPages": 1},
  "results": [
    {"issuingCompany": "PETR", "codeCVM": "009512",
     "tradingName": "PETROBRAS", "companyName": "PETROLEO BRASILEIRO S.A. PETROBRAS"}
  ]
}
```

**Normalização:** `codeCVM` sem zeros à esquerda e nome de exibição
(`tradingName`, com fallback para `companyName`). O resultado é cacheado por
30 dias.

### 3.3 Relatórios estruturados (`GetStructuredReports`)

**Módulos:** `infrastructure/b3/funds_client/documentos.py`,
`infrastructure/b3/reports_repository.py`

```text
GET https://sistemaswebb3-listados.b3.com.br/fundsListedProxy/Search/
    GetStructuredReports/{BASE64}
```

**Entrada**

```json
{
  "language": "pt-br",
  "dataInicial": "2026-01-01",
  "dataFinal": "2026-07-29",
  "pageNumber": 1,
  "pageSize": 20,
  "idFNET": "20294",
  "typeFund": "FII",
  "type": 41
}
```

Tipos usados:

| Código | Conteúdo |
| --- | --- |
| `41` | Rendimentos e amortizações |
| `40` | Informe Mensal Estruturado |

**Saída**

```json
{
  "page": {"pageNumber": 1, "pageSize": 20, "totalRecords": 2, "totalPages": 1},
  "results": [
    {
      "urlViewerFundosNet": "https://fnet.bmfbovespa.com.br/fnet/publico/exibirDocumento?id=1252542",
      "referenceDateFormat": "17/07/2026",
      "deliveryDateFormat": "18/07/2026",
      "referenceDate": "2026-07-17T00:00:00-03:00",
      "version": 1,
      "describleType": "Rendimentos e Amortizações",
      "status": "1 (Ativo)"
    }
  ]
}
```

**Normalização**

- Lista de referências `B3ReportReference(document_id, reference_date,
  delivery_date, report_type, status, viewer_url, version)`.
- O HTML do documento é baixado do FNET por `id` e o informe mensal é extraído
  como `B3InformeMensal` (cotistas, patrimônio líquido, cotas emitidas,
  valor patrimonial da cota, CNPJ, administrador e classificação
  autorregulação).
- Proventos são extraídos do HTML como `DocumentoProvento` (entidade,
  provento e metadados).

**Cache:** listagem por 1 dia; HTML do documento por 30 dias; o conteúdo é
compartilhado entre `type=40` e `type=41` pelo `id` do documento.

### 3.4 Documentos relevantes (`GetReportsRelevants`)

**Módulos:** `infrastructure/b3/funds_client/documentos_relevantes.py`,
`infrastructure/b3/documentos_relevantes.py`

```text
GET https://sistemaswebb3-listados.b3.com.br/fundsListedProxy/Search/
    GetReportsRelevants/{BASE64}
```

**Entrada**

```json
{
  "language": "pt-br",
  "dataInicial": "2026-01-01",
  "dataFinal": "2026-12-31",
  "pageNumber": 1,
  "pageSize": 20,
  "idFNET": "20294",
  "typeFund": "FII",
  "category": 7
}
```

Categorias consultadas:

| Código | Categoria | Slug local |
| --- | --- | --- |
| `1` | Fato Relevante | `fato-relevante` |
| `2` | Assembleia | `assembleia` |
| `3` | Comunicado ao Mercado | `comunicado` |
| `7` | Relatorio | `relatorio` |

**Saída**

```json
{
  "page": {"pageNumber": 1, "pageSize": 20, "totalRecords": 2, "totalPages": 1},
  "results": [
    {
      "urlFundosNet": "https://fnet.bmfbovespa.com.br/fnet/publico/visualizarDocumento?id=1252542",
      "urlViewerFundosNet": "https://fnet.bmfbovespa.com.br/fnet/publico/visualizarDocumento?id=1252542",
      "referenceDateFormat": "17/07/2026",
      "deliveryDateFormat": "17/07/2026",
      "referenceDate": "2026-07-17T00:00:00-03:00",
      "version": 1,
      "describleType": "AGE",
      "describleCategory": "Assembleia",
      "describleKind": "Ata de Assembleia Geral Ordinária",
      "subjects": "Aprovação de contas",
      "status": "1 (Ativo)"
    }
  ]
}
```

**Normalização:** `DocumentoRelevante(ticker, id_fnet, id_documento,
categoria, descricao, data_referencia, data_entrega, url, tamanho_bytes,
data_extracao)`.

**Cache:** listagem por 1 dia. Os PDFs são persistidos sem expiração em
`<cache>/documentos-relevantes/<TICKER>/<AAAA>/<MM>/<categoria>/<id>.pdf`.

### 3.5 Material facts (`GetMaterialFacts`)

**Módulos:** `infrastructure/b3/funds_client/material_facts.py`,
`material_facts_convert.py`

```text
GET https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall/
    GetMaterialFacts/{BASE64}
```

**Entrada**

```json
{
  "language": "pt-br",
  "codeCVM": "9512",
  "year": 2026,
  "dateInitial": "2026-01-01",
  "dateFinal": "2026-12-31",
  "category": "4",
  "pageNumber": 1,
  "pageSize": 20
}
```

Categorias:

| Código | Categoria |
| --- | --- |
| `1` | Assembleias |
| `3` | Avisos aos acionistas |
| `4` | Fatos relevantes |
| `48` | Avisos aos debenturistas |
| `107` | Relatório de proventos |

**Saída**

```json
{
  "page": {"pageNumber": 1, "pageSize": 20, "totalRecords": 1, "totalPages": 1},
  "results": [
    {
      "company": {
        "codeCVM": "009512",
        "companyName": "PETROLEO BRASILEIRO S.A. PETROBRAS",
        "tradingName": "PETROBRAS"
      },
      "dateReference": "16/04/2026 14:16",
      "deliveryDate": "28/04/2026 19:19:42",
      "status": "Ativo",
      "category": "Fatos Relevantes",
      "type": "",
      "kind": "",
      "version": "1",
      "subject": "Tomada de Contas-Votação do Relatório da Administração",
      "urlSearch": "https://www.rad.cvm.gov.br/ENETWEB/frmExibirArquivoIPEExterno.aspx?ID=1510187",
      "urlDownload": "https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?Tela=ext"
    }
  ]
}
```

**Normalização:** `DocumentoMaterialFact` e subtipos `FatoRelevante`,
`Assembleia`, `AvisoAcionista` e `AvisoDebenturista`, escolhidos pela
categoria. O documento pode ser serializado em `to_dict()` e `to_text()`.

**Cache:** 1 dia por `codeCVM`, categoria e período.

### 3.6 Documentos no FNET (HTML e PDF)

**Módulos:** `infrastructure/b3/funds_client/documentos.py`,
`documentos_relevantes.py`

```text
GET https://fnet.bmfbovespa.com.br/fnet/publico/exibirDocumento?id=<id>
GET https://fnet.bmfbovespa.com.br/fnet/publico/visualizarDocumento?id=<id>
```

- `exibirDocumento` é usado para baixar o HTML dos relatórios estruturados
  (`type=40/41`) e os PDFs dos documentos relevantes.
- `visualizarDocumento` aparece nas URLs de listagem retornadas pela B3.
- O conteúdo é validado (HTML não vazio ou assinatura `%PDF`) e o `403`
  intermitente do FNET é tratado como repetível.
- O PDF dos documentos relevantes é salvo no cache sem expiração.

### 3.7 Programas de aquisição de ações

**Módulo:** `infrastructure/b3/funds_client/regulatorio.py`

```text
GET https://sistemaswebb3-listados.b3.com.br/stockProgramProxy/
    StockProgramCall/GetListedCompany/{BASE64}
```

**Entrada**

```json
{
  "keyword": "",
  "date": "2026-10-14",
  "language": "pt-br",
  "pageNumber": 1,
  "pageSize": 60
}
```

**Saída**

```json
{
  "page": {"pageNumber": 1, "pageSize": 60, "totalPages": 1},
  "results": [
    {
      "company": "EMPRESA X S.A.",
      "aprrovedDate": "01/09/2026",
      "startDate": "01/10/2026",
      "endDate": "30/09/2027",
      "quantity": "1.000.000",
      "observation": "BANCO Y"
    }
  ]
}
```

> O nome `aprrovedDate` (com dois `r`) é a grafia retornada pela API e é
> consumido como está.

**Normalização:** `ProgramaAquisicao(empresa, data_aprovacao, data_inicio,
data_fim, quantidade, intermediarios)`.

**Cache:** 7 dias por data de referência.

---

## 4. B3 — notícias e regulatório

### 4.1 Plantão de Notícias

**Módulos:** `infrastructure/b3/funds_client/noticias.py`,
`noticias_convert.py`, `infrastructure/b3/noticias_aquisicao.py`

#### Listagem

```text
GET https://sistemasweb.b3.com.br/PlantaoNoticias/Noticias/ListarTitulosNoticias
    ?agencia=18
    &palavra=<termo>
    &dataInicial=AAAA-MM-DD
    &dataFinal=AAAA-MM-DD
    &pageNumber=<n>
```

**Entrada**

| Parâmetro | Descrição |
| --- | --- |
| `agencia` | Agência fixa `18` |
| `palavra` | Filtro textual opcional |
| `dataInicial` / `dataFinal` | Janela de datas |
| `pageNumber` | Página, quando a resposta informar `totalPages` |

**Saída**

A API retorna uma lista de itens no formato `{"NwsMsg": {...}}` (formatos
legados com `results` ou campos achatados também são aceitos):

```json
[
  {
    "NwsMsg": {
      "IdAgencia": 18,
      "content": null,
      "dateTime": "2026-09-11 15:12:32",
      "headline": "EXXON MOBIL (EXXO) - Aviso aos Acionistas - 11/09/26",
      "id": 3480343
    }
  }
]
```

**Normalização:** `NoticiaB3(titulo, data_publicacao, url, agencia)`. Quando
o item não traz `url`, a aplicação monta a página de detalhe:

```text
GET https://sistemasweb.b3.com.br/PlantaoNoticias/Noticias/Detail
    ?agencia=18
    &idNoticia=<id>
    &dataNoticia=AAAA-MM-DD
```

O HTML do artigo é baixado dessa URL e cacheado em
`<cache>/noticias/<AAAA>/<MM>/<sha1>.html`. Itens sem URL usam o próprio
registro como conteúdo.

**Cache da listagem:** chave por agência, período, palavra e hora; o TTL é de
1 dia, mas a chave horária renova o snapshot a cada hora.

#### Avisos aos acionistas de BDR

**Módulos:** `infrastructure/b3/bdr/`

O mesmo Plantão é consultado mês a mês por até 12 meses, usando a raiz do
ticker como `palavra`. São mantidos apenas títulos que contenham
`Aviso aos Acionistas` e `(<RAIZ>)`. A página `Detail` é baixada e o link do
documento é resolvido para o visualizador da CVM RAD, cujo PDF é baixado e
interpretado como dividendo/identidade do BDR.

**Cache:** listagem de avisos por 1 dia; PDFs em `<cache>/bdr/`.

### 4.2 Censuras públicas e condições excepcionais

**Módulos:** `infrastructure/b3/funds_client/regulatorio.py`,
`infrastructure/b3/structured_parser/`

```text
GET https://www.b3.com.br/pt_br/regulacao/regulacao-de-emissores/censuras-publicas/
GET https://www.b3.com.br/pt_br/regulacao/regulacao-de-emissores/condicoes-excepcionais/
```

**Entrada:** nenhuma.

**Saída:** HTML estático, interpretado com BeautifulSoup.

**Normalização**

- `CensuraPublica(titulo, ticker, data, conteudo)`.
- `CondicaoExcepcional(companhia, segmento, condicao, data_concessao, prazo)`.

**Cache:** 7 dias por página.

### 4.3 Documento vinculado em notícia

**Módulos:** `infrastructure/b3/noticias_vinculo.py`,
`domain/noticias/vinculo.py`

Algumas notícias trazem apenas um apontador para um documento. A aplicação
reconhece URLs dos visualizadores:

| Host | Página | Resolvedor |
| --- | --- | --- |
| `rad.cvm.gov.br` | `frmExibirArquivoIPEExterno.aspx` | CVM RAD |
| `fnet.bmfbovespa.com.br` | `visualizarDocumento` | FNET |

O conteúdo real é baixado sob demanda (ao selecionar a notícia ou ao resumir
pendentes), validado como PDF e extraído com `pypdf`; em falha, o corpo
original é preservado.

---

## 5. CVM — Dados Abertos

**Módulos:** `infrastructure/cvm/`

Todos os arquivos são públicos. A aplicação usa `GET` e revalidação
condicional (`HEAD` com `If-Modified-Since`/`If-None-Match`, com fallback para
`GET`), no máximo a cada 6 horas. Os arquivos brutos são mantidos em
`<cache>/cvm/<DATASET>/<ANO>/` (por exemplo, `cvm/inf_mensal`,
`cvm/FII-INF-ANUAL`, `cvm/FII-INF-TRIMESTRAL`, `cvm/FII-DFIN`, `cvm/fre` e
`cvm/fca`), acompanhados de `SHA256` e `metadata.json`.

### 5.1 Informe Mensal (`INF_MENSAL`)

```text
GET https://dados.cvm.gov.br/dados/FII/DOC/INF_MENSAL/DADOS/
    inf_mensal_fii_{ANO}.zip
```

**Saída:** ZIP com CSVs como `inf_mensal_fii_{ANO}.csv`,
`inf_mensal_fii_geral_{ANO}.csv` e `inf_mensal_fii_complemento_{ANO}.csv`.

Colunas relevantes (o parser aceita aliases atuais e legados):

| Campo canônico | Colunas aceitas |
| --- | --- |
| `cnpj` | `CNPJ_Fundo_Classe`, `CNPJ_Fundo`, `CNPJ_FUNDO` |
| `nome` | `Nome_Fundo_Classe`, `Nome_Fundo` |
| `tipo` | `Tipo_Fundo_Classe`, `Tipo_Fundo` |
| `competencia` | `Data_Referencia`, `DT_COMPTC` |
| `patrimonio` | `VL_PATRIM_LIQ`, `Patrimonio_Liquido` |
| `cotas` | `QT_COTA`, `QUANT_COTA`, `Cotas_Emitidas`, `Quantidade_Cotas_Emitidas` |
| `cotistas` | `NR_COTST`, `Total_Numero_Cotistas` |
| `vp_cota` | `Valor_Patrimonial_Cotas` |
| `versao` | `Versao`, `VERSAO`, `Nu_Versao` |
| `recebimento` | `Data_Recebimento`, `DT_RECEB`, `Data_Entrega` |

**Normalização:** `MonthlyReport(ticker, cnpj_fundo_classe, reference_date,
raw_rows, source_file, source_hash, is_latest)`. É selecionado o registro mais
recente até a data de referência, preferindo a maior `versao`.

**Uso:** patrimônio líquido, cotas, cotistas e VP/Cota (fonte de fallback da
B3); também fornece a identidade CNPJ do fundo.

### 5.2 Informe Anual (`INF_ANUAL`)

```text
GET https://dados.cvm.gov.br/dados/FII/DOC/INF_ANUAL/DADOS/
    inf_anual_fii_{ANO}.zip
```

**Saída:** ZIP com `inf_anual_fii_geral_{ANO}.csv` e
`inf_anual_fii_complemento_{ANO}.csv`.

Colunas relevantes:

- `CNPJ_Fundo_Classe`, `Data_Referencia`, `Versao`
- `Nome_Administrador`, `CNPJ_Administrador`
- `Nome_Gestor`, `CNPJ_Gestor`
- `Nome_Custodiante`, `CNPJ_Custodiante`
- `Nome_Auditor_Independente`, `CNPJ_Auditor_Independente`

**Normalização:** `AnnualReport` com gestor, administrador, custodiante e
auditor, selecionando o registro mais recente até a data de referência.

### 5.3 Informe Trimestral (`INF_TRIMESTRAL`)

```text
GET https://dados.cvm.gov.br/dados/FII/DOC/INF_TRIMESTRAL/DADOS/
    inf_trimestral_fii_{ANO}.zip
```

**Saída:** ZIP com CSVs, incluindo
`inf_trimestral_fii_complemento_{ANO}.csv`.

O parser aceita dois layouts:

- **Longo/legado:** `CNPJ_Fundo_Classe;Data_Referencia;Codigo;Descricao;Valor;Versao;Data_Recebimento`
- **Largo:** uma coluna monetária por componente contábil-financeiro.

**Normalização:** lista de `FFOComponent`, com código, descrição, valor,
versão, proveniência e classificação determinística (recorrente, não
recorrente, valor justo etc.). Reapresentações são resolvidas pela maior
`Versao`.

**Uso:** FFO calculado pelo motor determinístico (fallback do Fundamentus) e
percentuais por indexador (`IGP-M`, `INPC`, `IPCA`, `INCC`) lidos do
complemento.

### 5.4 Demonstrações Financeiras (`DFIN`)

```text
GET https://dados.cvm.gov.br/dados/FII/DOC/DFIN/DADOS/dfin_fii_{ANO}.csv
```

**Saída:** CSV (não ZIP) com:

```text
CNPJ_Fundo_Classe;Data_Referencia;Lucro_Prejuizo
28.737.771/0001-85;2026-06-30;800000,00
```

**Normalização:** `Decimal` com o resultado reportado mais recente até a data
de referência. Usado para reconciliar o FFO calculado.

### 5.5 Formulário Cadastral (`FCA`) e Formulário de Referência (`FRE`)

**Módulo:** `infrastructure/cvm/acionistas.py`

```text
GET https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FCA/DADOS/
    fca_cia_aberta_{ANO}.zip
GET https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/DADOS/
    fre_cia_aberta_{ANO}.zip
```

Arquivos internos usados:

- `fca_cia_aberta_valor_mobiliario_{ANO}.csv`
- `fre_cia_aberta_distribuicao_capital_{ANO}.csv`

Colunas relevantes:

| Arquivo | Colunas |
| --- | --- |
| FCA | `Codigo_Negociacao`, `CNPJ_Companhia` |
| FRE | `CNPJ_Companhia`, `Quantidade_Acionistas_PF`, `Quantidade_Acionistas_PJ`, `Quantidade_Acionistas_Investidores_Institucionais`, `Quantidade_Total_Acoes_Circulacao`, `Versao` |

**Normalização**

- Mapa `ticker → CNPJ`.
- Mapa `CNPJ → quantidade de acionistas` (soma PF + PJ + institucionais).
- Mapa `CNPJ → total de ações em circulação` (free float).

**Uso:** número de acionistas de ações, free float e cálculo de métricas de
_short interest_. O mapa normalizado é cacheado por hash do arquivo e versão
do parser.

### 5.6 Visualizador RAD — PDF (`ExibirPDF`)

**Módulo:** `infrastructure/cvm/pdf.py`

O download é feito em duas etapas, porque o `GET` renova a sessão/token:

```text
GET https://www.rad.cvm.gov.br/ENETWEB/frmExibirArquivoIPEExterno.aspx
    ?ID=<numeroProtocolo>

POST https://www.rad.cvm.gov.br/ENETWEB/frmExibirArquivoIPEExterno.aspx/ExibirPDF
Content-Type: application/json

{
  "codigoInstituicao": "2",
  "numeroProtocolo": "<numeroProtocolo>",
  "token": "",
  "versaoCaptcha": ""
}
```

**Saída**

```json
{"d": "<conteúdo do PDF em Base64>"}
```

O conteúdo decodificado precisa começar com `%PDF`; caso contrário é
descartado. É usado para PDFs de material facts e de avisos aos acionistas de
BDR.

---

## 6. Fundamentus

**Módulos:** `infrastructure/fii/fundamentus/`,
`infrastructure/fii/ffo_provider.py`

### 6.1 Página de detalhes

```text
GET https://fundamentus.com.br/detalhes.php?papel={TICKER}
```

Headers: `User-Agent: FlowScope/1.0`. Quando há cache condicional, envia
`If-None-Match` e `If-Modified-Since`. O acesso respeita `robots.txt` e um
rate-limit padrão de 1 segundo entre requisições.

**Saída:** HTML com tabelas de rótulo/valor.

**Normalização:** `AtivoFundamental`, com:

- identidade: ticker, tipo, espécie, setor, subsetor, segmento, gestão, nome;
- cotação: `cotacao`, `data_ultima_cotacao`, mínima/máxima de 52 semanas,
  volume médio de 2 meses, cotas/ações emitidas;
- `oscilacoes`: dia, mês, 30 dias, 12 meses e anos;
- `indicadores`: P/L, P/VP, P/EBIT, PSR, P/Ativos, P/Cap. Giro,
  P/Ativ Circ Liq, Div. Yield, EV/EBITDA, EV/EBIT, LPA, VPA, margens, ROIC,
  ROE, liquidez, dívida líquida/patrimônio, FFO Yield, FFO/Cota,
  Dividendo/cota, VP/Cota etc.;
- `balanco`, `demonstrativos_12m`, `demonstrativos_3m`,
  `composicao_ativos`, `imoveis` e `raw` (rótulo → valor original).

**Cache:** condicional com frescor de 1 hora, revalidação a cada 1 hora,
TTL de segurança de 24 horas e retenção de 30 dias. O validador primário é a
`Data últ cot`; os HTTP (`ETag`/`Last-Modified`) são secundários.

### 6.2 Proventos de ações e FIIs

```text
GET https://fundamentus.com.br/proventos.php?papel={TICKER}
GET https://fundamentus.com.br/fii_proventos.php?papel={TICKER}
GET https://fundamentus.com.br/robots.txt
```

A página de ações é consultada primeiro; se não houver proventos, a página de
FII/FIAGRO é consultada.

**Saída:** HTML.

**Normalização:** `list[DividendoConsolidado]` com data-base, valor e fonte
`FUNDAMENTUS`, filtrada até a data de referência.

**Cache:** 1 dia por ticker e tipo de página.

### 6.3 FFO reportado

O FFO de 12 e 3 meses é extraído das linhas `FFO` da página de detalhes
(`metodologia = SOURCE_REPORTED`). Quando indisponível, o fallback é o motor
determinístico da CVM (`INF_TRIMESTRAL`, `metodologia = FLOWSCOPE_DERIVED`).

---

## 7. LLM (opcional)

**Módulos:** `infrastructure/llm/`, `application/resumo_documento.py`,
`application/chat/`

As chamadas usam `litellm.completion` com o formato de mensagens
`{"role": "user" | "assistant" | "system", "content": str}`. O adaptador envia:

```json
{
  "model": "<modelo configurado>",
  "messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}],
  "api_key": "<chave configurada>",
  "api_base": "<opcional>",
  "custom_llm_provider": "openai"
}
```

`api_base` e `custom_llm_provider` só são enviados quando há uma API URL
configurada.

**Saída:** `choices[0].message.content` e o bloco `usage` (tokens de entrada,
saída e cache), normalizados em `LLMResposta`/`LLMUsage`.

Presets e endpoints padrão:

| Provedor | API URL |
| --- | --- |
| `openai` | `https://api.openai.com/v1` |
| `gemini` | `https://generativelanguage.googleapis.com/v1beta/openai/` |
| `copilot` | `https://models.inference.ai.azure.com` |
| `claude` | `https://api.anthropic.com/v1` |
| `deepseek` | `https://api.deepseek.com/v1` |
| `ollama` | `http://localhost:11434/v1` |
| `custom` | preenchido pelo usuário |

Enquanto o provedor for `none`, nenhuma chamada de rede é feita. Os payloads
detalhados de resumo de documentos, resumo de notícias, avaliação de guidance
e Chat AI estão em [llm-payloads.md](llm-payloads.md).

---

## 8. GitHub Releases

**Módulo:** `infrastructure/releases/client.py`

```text
GET https://github.com/amaurycarvalho/flowscope/releases/latest
```

Segue o redirecionamento até `.../releases/tag/<tag>`. A tag é validada e
normalizada para `(versao, url)`; falha de rede, timeout ou tag inválida
resultam em `None` (a aplicação continua funcionando sem aviso de nova
versão).

---

## 9. Fontes locais

### 9.1 Arquivo de watchlist

**Módulos:** `presentation/cli_acoes.py`,
`presentation/gui/widgets/ticker_list_utils.py`

Formato: texto simples, um ticker por linha. Linhas vazias são ignoradas e os
tickers são normalizados para maiúsculas.

```text
PETR4
VALE3
HGLG11
```

O comando `flowscope carregar watchlist <arquivo>` persiste a lista em
`~/.flowscope/config.json` (`last_tickers` e `last_ticker_file`).

### 9.2 `~/.flowscope/config.json`

Arquivo de configuração do usuário. Chaves relevantes:

| Chave | Conteúdo |
| --- | --- |
| `last_tickers` | Lista de tickers da última watchlist carregada |
| `last_ticker_file` | Caminho do arquivo da watchlist |
| `last_date` | Última data de referência usada |
| `last_fundamentals` | `{data, fetched_at}` da última carga de fundamentos |
| `llm.chat` | Provedor ativo, presets, modelos, URLs, chaves e RPM |
| `llm.embedding` | Configuração reservada para indexação vetorial |

### 9.3 Cache local

Além dos caches por data, a aplicação mantém:

| Caminho | Conteúdo |
| --- | --- |
| `<cache>/AAAA-MM-DD.csv` | Cotações diárias da B3 |
| `<cache>/portfolio_<ÍNDICE>.json` | Carteiras de índice |
| `<cache>/fundos_listados_<TIPO>.json` | Listagem de fundos |
| `<cache>/documentos-relevantes/...` | PDFs de documentos relevantes |
| `<cache>/noticias/...` | HTML e índice de notícias |
| `<cache>/bdr/...` | PDFs de avisos de BDR |
| `<cache>/document-summaries/...` | Resumos de documentos/notícias |
| `<cache>/document-texts/...` | Textos extraídos de documentos/notícias |
| `<cache>/guidance/...` | Guidance de distribuição por FII |
| `<cache>/cvm/<DATASET>/<ANO>/` | ZIPs/CSVs brutos, hash e metadados da CVM |

O catálogo de notícias e a árvore de conhecimento do Chat AI/MCP leem apenas
esse cache local; a atualização de novos itens acontece por ação explícita de
carregamento.

---

## 10. Prioridade das fontes nos fundamentos

A composição dos fundamentos segue a ordem abaixo; o primeiro valor
disponível para cada campo é usado.

| Dado | Fonte primária | Fallbacks |
| --- | --- | --- |
| Nome, identidade e classificação de FII | Fundamentus | B3 (fundos/informe mensal), CVM (INF_ANUAL) |
| CNPJ de companhia aberta | Fundamentus | B3 (empresas listadas), CVM (FCA) |
| Cotação e preço de fechamento | B3 (dados de negociação) | — |
| Patrimônio, cotas, cotistas e VP/Cota | B3 (informe mensal) | CVM (INF_MENSAL) |
| Proventos e dividendos | B3 (relatórios estruturados) | Fundamentus; BDR para ativos BDR |
| Dividendos de BDR | B3 (Plantão + CVM RAD) | — |
| FFO | Fundamentus (reportado) | CVM (INF_TRIMESTRAL + motor determinístico) |
| Número de acionistas e free float | CVM (FCA/FRE) | — |
| Ações alugadas (_short interest_) | B3 (BDI) | — |
| Percentuais por indexador | CVM (INF_TRIMESTRAL) | — |
| Documentos e guidance | B3 (FNET), CVM RAD | — |
| Notícias e informações regulatórias | B3 (Plantão e páginas regulatórias) | — |

---

## 11. Mapa de implementação

| Fonte | Principais módulos |
| --- | --- |
| B3 — cotações e índices | `infrastructure/b3/client.py`, `parser.py` |
| B3 — _short interest_ | `infrastructure/b3/emprestimos.py` |
| B3 — fundos e documentos | `infrastructure/b3/funds_client/` |
| B3 — notícias e regulatório | `infrastructure/b3/funds_client/noticias.py`, `regulatorio.py`, `noticias_aquisicao.py` |
| B3 — documentos relevantes | `infrastructure/b3/documentos_relevantes.py`, `documentos_aquisicao.py` |
| B3 — BDR | `infrastructure/b3/bdr/` |
| CVM — dados abertos | `infrastructure/cvm/` |
| CVM — PDF RAD | `infrastructure/cvm/pdf.py` |
| Fundamentus | `infrastructure/fii/fundamentus/` |
| LLM | `infrastructure/llm/` |
| GitHub Releases | `infrastructure/releases/client.py` |
| Cache local | `infrastructure/cache.py`, `conditional_cache.py` |
