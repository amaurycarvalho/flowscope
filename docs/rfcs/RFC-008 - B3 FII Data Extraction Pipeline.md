# RFC-008 — B3 FII Data Extraction Pipeline

**Status:** Proposed
**Projeto:** FlowScope
**Tipo:** Operational / Data Acquisition
**Domínio:** Brazilian Real Estate Investment Funds (FII)
**Fonte primária:** B3 — Fundos Listados / FundosNet / SIG
**Linguagem de referência:** Python 3.11+
**Objetivo:** definir um processo determinístico para obter, a partir do ticker de um FII, seu identificador B3/FNET e os dados necessários para análises fundamentalistas e de mercado.

---

## 1. Objetivo

Esta RFC define como o FlowScope deve extrair, de forma determinística, os seguintes conjuntos de dados para um FII:

1. identificação interna do fundo a partir do ticker;
2. informações/documentos relevantes do fundo;
3. resumo mensal de negociações;
4. rendimentos e amortizações em formato estruturado;
5. informes mensais em formato estruturado.

O processo deve ser aplicável a qualquer FII listado, sem codificar valores específicos de um fundo.

O exemplo utilizado nesta RFC é:

```text
Ticker: ALZR
```

---

# 2. Arquitetura da aquisição

O pipeline deve seguir a sequência:

```text
Ticker
  |
  v
[1] B3 GetListClassFund
  |
  +--> id = identificador principal
  |
  +--> idFNET = identificador usado nos relatórios
  |
  v
[2] GetReportsRelevants
  |
  v
[3] GetStructuredReports(type=41)
  |
  +--> Rendimentos e Amortizações
  |
  v
[4] GetStructuredReports(type=40)
  |
  +--> Informe Mensal Estruturado
  |
  v
[5] SIG / FormConsultaNegociacoes.asp
  |
  +--> resumo de negociações
  |
  v
Normalized FII Dataset
```

Uma característica importante é que o ticker **não deve ser utilizado diretamente nas APIs `GetReportsRelevants` e `GetStructuredReports`**.

Primeiro deve-se resolver o ticker para o identificador B3/FNET.

---

# 3. Identificação do fundo pelo ticker

## 3.1 Endpoint

```text
GET
https://sistemaswebb3-listados.b3.com.br/fundsListedProxy/Search/GetListClassFund/{BASE64}
```

O `{BASE64}` contém um JSON codificado em Base64.

Para:

```text
ALZR
```

o payload observado é:

```json
{
  "language": "pt-br",
  "idFNET": "870",
  "idCEM": "ALZR",
  "typeFund": "FII"
}
```

O endpoint retorna, no exemplo, dois registros:

```json
[
  {
    "id": "870",
    "idMain": null,
    "fundName": "ALIANZA TRUST RENDA IMOBILIÁRIA - FUNDO DE INVESTIMENTO IMOBILIÁRIO RESPONSABILIDADE LIMITADA",
    "tradingName": "Fundo: 28.737.771/0001-85"
  },
  {
    "id": "20294",
    "idMain": "870",
    "fundName": "ALIANZA TRUST RENDA IMOBILIÁRIA - FUNDO DE INVESTIMENTO IMOBILIÁRIO RESPONSABILIDADE LIMITADA",
    "tradingName": "28.737.771/0001-85"
  }
]
```

### Regra

O FlowScope deve tratar o resultado como uma relação:

```text
id
idMain
fundName
tradingName
```

e **não assumir que o primeiro registro é necessariamente o identificador usado pelas consultas subsequentes**.

No exemplo:

```text
id = 870
idMain = null

id = 20294
idMain = 870
```

As consultas de relatórios utilizam:

```text
idFNET = 20294
```

Portanto:

```text
idFNET = registro cujo idMain referencia o registro principal
```

é uma heurística válida para o padrão observado, mas deve ser encapsulada em uma função de resolução e validada pelo resultado das consultas seguintes.

---

# 4. Construção do parâmetro Base64

## 4.1 Função genérica

```python
import base64
import json


def encode_b3_payload(payload: dict) -> str:
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    return base64.b64encode(raw).decode("ascii")
```

Uso:

```python
payload = {
    "language": "pt-br",
    "idFNET": "870",
    "idCEM": "ALZR",
    "typeFund": "FII",
}

encoded = encode_b3_payload(payload)

print(encoded)
```

Resultado:

```text
eyJsYW5ndWFnZSI6InB0LWJyIiwiaWRGTkVUIjoiODcwIiwiaWRDRU0iOiJBTFpSIiwidHlwZUZ1bmQiOiJGSUkifQ==
```

---

# 5. Resolução do ticker

## 5.1 Implementação

```python
import requests


B3_FUNDS_BASE = (
    "https://sistemaswebb3-listados.b3.com.br"
    "/fundsListedProxy/Search"
)


def get_fund_candidates(ticker: str) -> list[dict]:
    ticker = ticker.upper().strip()

    payload = {
        "language": "pt-br",
        "idFNET": "870",
        "idCEM": ticker,
        "typeFund": "FII",
    }

    encoded = encode_b3_payload(payload)

    url = f"{B3_FUNDS_BASE}/GetListClassFund/{encoded}"

    response = requests.get(
        url,
        timeout=30,
        headers={
            "Accept": "application/json",
            "User-Agent": "FlowScope/1.0",
        },
    )

    response.raise_for_status()

    return response.json()
```

### Observação importante

O campo:

```json
"idFNET": "870"
```

no request de busca **não deve ser interpretado como o ID do fundo pesquisado**.

Ele aparece como parte do contrato utilizado pelo portal para executar a pesquisa por:

```json
"idCEM": "ALZR"
```

O identificador efetivamente resolvido deve ser obtido da resposta.

---

# 6. Resolver o ID utilizado nos relatórios

```python
def resolve_fnet_id(ticker: str) -> tuple[str, dict]:
    candidates = get_fund_candidates(ticker)

    if not candidates:
        raise ValueError(
            f"FII não encontrado na B3: {ticker}"
        )

    # Preferir registro que possui idMain.
    derived = [
        item
        for item in candidates
        if item.get("idMain") is not None
    ]

    if derived:
        selected = derived[0]
    else:
        selected = candidates[0]

    return selected["id"], selected
```

Exemplo:

```python
fnet_id, fund = resolve_fnet_id("ALZR")

print(fnet_id)
print(fund)
```

Resultado esperado para o exemplo:

```text
20294
```

---

# 7. Endpoint de informações/documentos relevantes

## 7.1 Endpoint

```text
GET
https://sistemaswebb3-listados.b3.com.br/
fundsListedProxy/Search/GetReportsRelevants/{BASE64}
```

Payload:

```json
{
  "language": "pt-br",
  "pageNumber": 1,
  "pageSize": 20,
  "dateInitial": "2026-01-01",
  "dateFinal": "2026-07-29",
  "idFNET": "20294",
  "typeFund": "FII",
  "category": 2
}
```

A resposta possui a estrutura:

```json
{
  "page": {
    "pageNumber": 1,
    "pageSize": 20,
    "totalRecords": 8,
    "totalPages": 1
  },
  "results": [
    {
      "urlFundosNet": "...",
      "urlViewerFundosNet": "...",
      "referenceDateFormat": "...",
      "deliveryDateFormat": "...",
      "referenceDate": "...",
      "version": 1,
      "describleType": "AGE",
      "describleCategory": "Assembleia",
      "describleKind": "Ata da Assembleia",
      "subjects": "...",
      "status": "1 (Ativo)"
    }
  ]
}
```

---

# 8. Consulta genérica de relatórios relevantes

```python
from datetime import date


def get_reports_relevant(
    fnet_id: str,
    start_date: date,
    end_date: date,
    page_number: int = 1,
    page_size: int = 20,
) -> dict:

    payload = {
        "language": "pt-br",
        "pageNumber": page_number,
        "pageSize": page_size,
        "dateInitial": start_date.isoformat(),
        "dateFinal": end_date.isoformat(),
        "idFNET": str(fnet_id),
        "typeFund": "FII",
        "category": 2,
    }

    encoded = encode_b3_payload(payload)

    url = (
        f"{B3_FUNDS_BASE}"
        f"/GetReportsRelevants/{encoded}"
    )

    response = requests.get(
        url,
        timeout=30,
        headers={
            "Accept": "application/json",
            "User-Agent": "FlowScope/1.0",
        },
    )

    response.raise_for_status()

    return response.json()
```

---

# 9. Paginação

O campo:

```json
"page": {
    "pageNumber": 1,
    "pageSize": 20,
    "totalRecords": 8,
    "totalPages": 1
}
```

deve ser tratado como parte do contrato.

Não assumir:

```text
totalPages = 1
```

A implementação deve continuar até:

```text
page_number > totalPages
```

ou até recuperar todos os registros.

```python
def get_all_relevant_reports(
    fnet_id: str,
    start_date: date,
    end_date: date,
) -> list[dict]:

    page_number = 1
    results = []

    while True:
        data = get_reports_relevant(
            fnet_id=fnet_id,
            start_date=start_date,
            end_date=end_date,
            page_number=page_number,
            page_size=20,
        )

        page = data["page"]
        results.extend(data.get("results", []))

        if page_number >= page["totalPages"]:
            break

        page_number += 1

    return results
```

---

# 10. Rendimentos e amortizações

## 10.1 Endpoint

```text
GET
https://sistemaswebb3-listados.b3.com.br/
fundsListedProxy/Search/GetStructuredReports/{BASE64}
```

Payload:

```json
{
  "language": "pt-br",
  "dateInitial": "2026-01-01",
  "dateFinal": "2026-07-29",
  "pageNumber": 1,
  "pageSize": 20,
  "idFNET": "20294",
  "typeFund": "FII",
  "type": 41
}
```

O valor:

```text
type = 41
```

corresponde, no endpoint observado, a:

```text
Rendimentos e Amortizações
```

Para ALZR, o endpoint retornou sete registros no período de janeiro a julho de 2026.

---

# 11. Função genérica para Structured Reports

```python
def get_structured_reports(
    fnet_id: str,
    report_type: int,
    start_date: date,
    end_date: date,
    page_number: int = 1,
    page_size: int = 20,
) -> dict:

    payload = {
        "language": "pt-br",
        "dateInitial": start_date.isoformat(),
        "dateFinal": end_date.isoformat(),
        "pageNumber": page_number,
        "pageSize": page_size,
        "idFNET": str(fnet_id),
        "typeFund": "FII",
        "type": report_type,
    }

    encoded = encode_b3_payload(payload)

    url = (
        f"{B3_FUNDS_BASE}"
        f"/GetStructuredReports/{encoded}"
    )

    response = requests.get(
        url,
        timeout=30,
        headers={
            "Accept": "application/json",
            "User-Agent": "FlowScope/1.0",
        },
    )

    response.raise_for_status()

    return response.json()
```

---

# 12. Rendimentos e amortizações

```python
def get_distributions(
    fnet_id: str,
    start_date: date,
    end_date: date,
) -> list[dict]:

    data = get_structured_reports(
        fnet_id=fnet_id,
        report_type=41,
        start_date=start_date,
        end_date=end_date,
    )

    return data.get("results", [])
```

Uso:

```python
from datetime import date

distributions = get_distributions(
    fnet_id="20294",
    start_date=date(2026, 1, 1),
    end_date=date(2026, 7, 29),
)

for item in distributions:
    print(
        item["referenceDateFormat"],
        item["describleType"],
        item["status"],
    )
```

---

# 13. Informe Mensal Estruturado

## 13.1 Endpoint

É utilizado o mesmo endpoint:

```text
GetStructuredReports
```

mas com:

```json
"type": 40
```

Payload:

```json
{
  "language": "pt-br",
  "dateInitial": "2026-01-01",
  "dateFinal": "2026-07-29",
  "pageNumber": 1,
  "pageSize": 20,
  "idFNET": "20294",
  "typeFund": "FII",
  "type": 40
}
```

No exemplo ALZR, a resposta contém seis informes mensais, de janeiro a junho de 2026.

---

# 14. Consulta dos informes mensais

```python
def get_monthly_reports(
    fnet_id: str,
    start_date: date,
    end_date: date,
) -> list[dict]:

    data = get_structured_reports(
        fnet_id=fnet_id,
        report_type=40,
        start_date=start_date,
        end_date=end_date,
    )

    return data.get("results", [])
```

Uso:

```python
monthly_reports = get_monthly_reports(
    fnet_id="20294",
    start_date=date(2026, 1, 1),
    end_date=date(2026, 7, 29),
)

for item in monthly_reports:
    print(
        item["referenceDateFormat"],
        item["urlViewerFundosNet"],
    )
```

---

# 15. Importante: StructuredReports retorna índice de documentos

O endpoint `GetStructuredReports` não deve ser confundido com o conteúdo integral do informe.

A resposta observada contém:

```json
{
  "urlViewerFundosNet": "...",
  "referenceDateFormat": "06/2026",
  "deliveryDateFormat": "15/07/2026 19:48",
  "referenceDate": "2026-06-01T00:00:00-03:00",
  "version": 1,
  "describleType": "Informe Mensal Estruturado",
  "status": "1 (Ativo)"
}
```

Portanto, o pipeline possui duas etapas:

```text
GetStructuredReports
       |
       v
document URL / document ID
       |
       v
FundosNet document
       |
       v
structured content
```

A RFC deve manter essas duas responsabilidades separadas.

---

# 16. Identificação do documento FundosNet

A URL:

```text
https://fnet.bmfbovespa.com.br/fnet/publico/visualizarDocumento?id=1250291
```

contém:

```text
document_id = 1250291
```

A extração pode ser feita de forma determinística:

```python
from urllib.parse import urlparse, parse_qs


def extract_fundosnet_document_id(url: str) -> int:
    query = parse_qs(urlparse(url).query)

    value = query.get("id")

    if not value:
        raise ValueError(
            f"ID do documento não encontrado: {url}"
        )

    return int(value[0])
```

---

# 17. Resumo de negociações

## 17.1 Endpoint legado

```text
https://bvmf.bmfbovespa.com.br/SIG/FormConsultaNegociacoes.asp
```

Parâmetros:

```text
strTipoResumo=RES_NEGOCIACOES
strSocEmissora=ALZR
strDtReferencia=06/2026
strIdioma=P
intCodNivel=1
intCodCtrl=100
```

A chamada lógica é:

```text
GET /SIG/FormConsultaNegociacoes.asp
```

com query string:

```python
params = {
    "strTipoResumo": "RES_NEGOCIACOES",
    "strSocEmissora": ticker,
    "strDtReferencia": "06/2026",
    "strIdioma": "P",
    "intCodNivel": 1,
    "intCodCtrl": 100,
}
```

---

# 18. Python — consulta de negociações

```python
import requests


SIG_URL = (
    "https://bvmf.bmfbovespa.com.br"
    "/SIG/FormConsultaNegociacoes.asp"
)


def get_trading_summary(
    ticker: str,
    reference_month: str,
) -> str:

    params = {
        "strTipoResumo": "RES_NEGOCIACOES",
        "strSocEmissora": ticker.upper(),
        "strDtReferencia": reference_month,
        "strIdioma": "P",
        "intCodNivel": 1,
        "intCodCtrl": 100,
    }

    response = requests.get(
        SIG_URL,
        params=params,
        timeout=30,
        headers={
            "User-Agent": "FlowScope/1.0",
        },
    )

    response.raise_for_status()

    # Endpoint legado pode retornar HTML.
    response.encoding = response.apparent_encoding

    return response.text
```

Exemplo:

```python
html = get_trading_summary(
    ticker="ALZR",
    reference_month="06/2026",
)

print(html[:1000])
```

---

# 19. Parsing do resumo de negociações

Como o endpoint SIG é uma interface HTML legada, o parser não deve depender de posições absolutas de elementos HTML.

Evitar:

```python
table = soup.find_all("table")[3]
```

Preferir:

```python
from bs4 import BeautifulSoup


def parse_tables(html: str):
    soup = BeautifulSoup(html, "html.parser")

    tables = []

    for table in soup.find_all("table"):
        rows = []

        for tr in table.find_all("tr"):
            cells = [
                cell.get_text(" ", strip=True)
                for cell in tr.find_all(["th", "td"])
            ]

            if cells:
                rows.append(cells)

        if rows:
            tables.append(rows)

    return tables
```

O parser específico do FlowScope deve localizar a tabela pelo conteúdo textual de seus cabeçalhos.

Exemplo conceitual:

```python
def find_table_containing(tables, text: str):
    text = text.lower()

    for table in tables:
        flattened = " ".join(
            " ".join(row).lower()
            for row in table
        )

        if text in flattened:
            return table

    return None
```

Isso reduz a dependência do layout físico da página.

---

# 20. Datas

As APIs B3 utilizam:

```text
YYYY-MM-DD
```

para os filtros:

```text
dateInitial
dateFinal
```

Enquanto a página SIG utiliza:

```text
MM/YYYY
```

Exemplo:

```text
2026-06-01
```

na API estruturada versus:

```text
06/2026
```

no SIG.

O FlowScope deve manter datas internamente como:

```python
datetime.date
```

e formatá-las somente no adaptador de cada fonte.

---

# 21. Modelo de domínio recomendado

O código não deve propagar os nomes originais da B3 por toda a aplicação.

Recomenda-se:

```python
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class B3Fund:
    ticker: str
    fnet_id: str
    primary_id: str | None
    name: str
    trading_name: str | None


@dataclass(frozen=True)
class B3ReportReference:
    document_id: int
    reference_date: date | None
    delivery_date: str | None
    report_type: str
    status: str
    viewer_url: str
```

---

# 22. Modelo de aquisição

Uma camada específica deve encapsular a B3:

```text
flowscope/
    infrastructure/
        b3/
            client.py
            encoder.py
            fund_repository.py
            reports_repository.py
            negotiations_repository.py
            parsers/
                structured_reports.py
                negotiations.py
```

A aplicação não deve conhecer:

```text
GetStructuredReports
GetReportsRelevants
GetListClassFund
```

diretamente.

Ela deve consumir:

```python
fund_repository.find_by_ticker("ALZR")

reports_repository.get_monthly_reports(...)

reports_repository.get_distributions(...)

negotiations_repository.get_monthly_summary(...)
```

---

# 23. Cliente HTTP

Recomenda-se uma única implementação HTTP:

```python
class B3HttpClient:

    def __init__(self):
        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": "FlowScope/1.0",
            "Accept": "application/json",
        })

    def get_json(self, url: str) -> dict | list:
        response = self.session.get(
            url,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    def get_text(self, url: str) -> str:
        response = self.session.get(
            url,
            timeout=30,
        )

        response.raise_for_status()

        response.encoding = response.apparent_encoding

        return response.text
```

---

# 24. Retry

Como os endpoints são externos, devem existir retries para erros transitórios.

Recomendação:

```text
tentativa 1: imediata
tentativa 2: 1 segundo
tentativa 3: 3 segundos
tentativa 4: 10 segundos
```

Não repetir automaticamente erros HTTP claramente permanentes, como:

```text
400
404
```

Uma implementação simples:

```python
import time


RETRY_DELAYS = [0, 1, 3, 10]


def request_with_retry(fn):

    last_error = None

    for delay in RETRY_DELAYS:

        if delay:
            time.sleep(delay)

        try:
            return fn()

        except requests.RequestException as exc:
            last_error = exc

    raise last_error
```

---

# 25. Rate limiting

O FlowScope não deve executar consultas em paralelo indiscriminadamente.

Recomenda-se:

```text
1 request por vez por host
```

para:

```text
sistemaswebb3-listados.b3.com.br
```

e uma limitação independente para:

```text
bvmf.bmfbovespa.com.br
```

Além disso:

- cachear respostas;
- não consultar novamente documentos já conhecidos;
- não baixar o mesmo documento duas vezes;
- evitar polling agressivo.

---

# 26. Cache

O cache deve ser baseado nos parâmetros completos.

Exemplo:

```text
B3/
  GetListClassFund/
    ALZR
  GetReportsRelevants/
    20294/
      2026-01-01/
      2026-07-29/
  GetStructuredReports/
    20294/
      type-40/
      2026-01-01/
      2026-07-29/
    type-41/
```

A chave conceitual deve ser:

```python
(
    endpoint,
    normalized_payload,
)
```

e não simplesmente:

```text
ticker
```

---

# 27. Determinismo

A aquisição deve produzir o mesmo resultado para:

```text
ticker
+
dateInitial
+
dateFinal
+
endpoint
```

quando a fonte B3 não tiver sido alterada.

Toda resposta deve preservar:

```text
request URL
request payload
retrieval timestamp
HTTP status
raw response
parser version
```

Exemplo:

```python
@dataclass(frozen=True)
class AcquisitionMetadata:
    source: str
    endpoint: str
    request_payload: dict
    retrieved_at: str
    http_status: int
    parser_version: str
```

---

# 28. Raw data

O FlowScope deve preservar o dado bruto antes de normalizar.

Exemplo:

```text
data/raw/b3/

    ALZR/
        fund/
            2026-09-10.json

        reports/
            relevant/
                2026-01-01_2026-07-29.json

            distributions/
                2026-01-01_2026-07-29.json

            monthly/
                2026-01-01_2026-07-29.json

        negotiations/
            2026-06.html
```

Isso permite:

```text
reprocessamento
auditoria
debug
comparação de parser
```

sem consultar novamente a B3.

---

# 29. Pipeline completo

Exemplo de implementação de alto nível:

```python
from datetime import date


def acquire_fii_data(
    ticker: str,
    start_date: date,
    end_date: date,
):

    # 1. Resolve ticker
    fnet_id, fund_data = resolve_fnet_id(ticker)

    # 2. Relevant reports
    relevant_reports = get_all_relevant_reports(
        fnet_id=fnet_id,
        start_date=start_date,
        end_date=end_date,
    )

    # 3. Distributions
    distributions = get_distributions(
        fnet_id=fnet_id,
        start_date=start_date,
        end_date=end_date,
    )

    # 4. Monthly reports
    monthly_reports = get_monthly_reports(
        fnet_id=fnet_id,
        start_date=start_date,
        end_date=end_date,
    )

    return {
        "fund": fund_data,
        "fnet_id": fnet_id,
        "relevant_reports": relevant_reports,
        "distributions": distributions,
        "monthly_reports": monthly_reports,
    }
```

---

# 30. Consulta de negociações no pipeline

A consulta de negociações deve ser feita por mês, pois o SIG utiliza:

```text
MM/YYYY
```

Exemplo:

```python
def month_string(year: int, month: int) -> str:
    return f"{month:02d}/{year}"


html = get_trading_summary(
    ticker="ALZR",
    reference_month=month_string(2026, 6),
)
```

Para um intervalo:

```python
def iter_months(start: date, end: date):
    year = start.year
    month = start.month

    while (year, month) <= (end.year, end.month):
        yield f"{month:02d}/{year}"

        month += 1

        if month > 12:
            month = 1
            year += 1
```

Uso:

```python
for reference_month in iter_months(
    date(2026, 1, 1),
    date(2026, 7, 31),
):
    html = get_trading_summary(
        ticker="ALZR",
        reference_month=reference_month,
    )
```

---

# 31. Validações obrigatórias

## 31.1 Ticker

```text
1 <= len(ticker) <= 6
ticker = uppercase
ticker não pode conter espaços internos
```

## 31.2 FNET ID

Deve ser numérico:

```python
assert str(fnet_id).isdigit()
```

## 31.3 Datas

```text
dateInitial <= dateFinal
```

## 31.4 Resposta

Para endpoints JSON:

```python
response.headers["Content-Type"]
```

deve ser compatível com JSON.

Além disso:

```python
isinstance(response.json(), (dict, list))
```

## 31.5 Paginação

Validar:

```text
pageNumber
pageSize
totalRecords
totalPages
```

## 31.6 Documento

Todo registro com:

```text
urlViewerFundosNet
```

deve possuir um `id` extraível.

---

# 32. Status dos documentos

Não considerar automaticamente qualquer documento retornado como válido.

Exemplo:

```text
1 (Ativo)
1 (Cancelado)
```

No caso observado de `GetReportsRelevants`, existem documentos cancelados e ativos na mesma resposta.

Portanto:

```python
def is_active(status: str) -> bool:
    return status.startswith("1 (Ativo)")
```

e:

```python
active = [
    item
    for item in reports
    if is_active(item.get("status", ""))
]
```

O dado bruto, entretanto, deve preservar também os cancelados.

---

# 33. Controle de versão

Os registros possuem:

```json
"version": 1
```

O FlowScope não deve descartar versões diferentes.

A chave lógica de um documento deve considerar:

```text
document_id
version
reference_date
```

Caso a B3 disponibilize uma nova versão, o pipeline deve preservar a versão anterior.

---

# 34. Separação entre aquisição e interpretação

A arquitetura deve seguir:

```text
                    +----------------------+
                    | B3 HTTP endpoints    |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Acquisition Layer    |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Raw Documents        |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Parsing Layer        |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Normalization Layer  |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | Domain Model         |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    | FII Analytics        |
                    +----------------------+
```

Isso é particularmente importante para o FlowScope porque a mesma informação pode posteriormente alimentar:

```text
Dividend Yield
FFO Yield
P/FFO
Patrimônio
Número de cotistas
Vacância
Receita
Resultado
Liquidez
Volume
Número de negócios
```

sem acoplar os cálculos financeiros ao formato específico da B3.

---

# 35. Contratos dos endpoints

## Endpoint A — resolução do ticker

```text
GET /fundsListedProxy/Search/GetListClassFund/{payload}
```

Input:

```json
{
  "language": "pt-br",
  "idFNET": "870",
  "idCEM": "<TICKER>",
  "typeFund": "FII"
}
```

Output:

```text
list[FundCandidate]
```

---

## Endpoint B — documentos relevantes

```text
GET /fundsListedProxy/Search/GetReportsRelevants/{payload}
```

Input:

```json
{
  "language": "pt-br",
  "pageNumber": 1,
  "pageSize": 20,
  "dateInitial": "<YYYY-MM-DD>",
  "dateFinal": "<YYYY-MM-DD>",
  "idFNET": "<ID>",
  "typeFund": "FII",
  "category": 2
}
```

Output:

```text
Paginated[RelevantReport]
```

---

## Endpoint C — rendimentos/amortizações

```text
GET /fundsListedProxy/Search/GetStructuredReports/{payload}
```

Input:

```json
{
  "language": "pt-br",
  "dateInitial": "<YYYY-MM-DD>",
  "dateFinal": "<YYYY-MM-DD>",
  "pageNumber": 1,
  "pageSize": 20,
  "idFNET": "<ID>",
  "typeFund": "FII",
  "type": 41
}
```

Output:

```text
Paginated[StructuredReport]
```

---

## Endpoint D — informe mensal

```text
GET /fundsListedProxy/Search/GetStructuredReports/{payload}
```

Input:

```json
{
  "language": "pt-br",
  "dateInitial": "<YYYY-MM-DD>",
  "dateFinal": "<YYYY-MM-DD>",
  "pageNumber": 1,
  "pageSize": 20,
  "idFNET": "<ID>",
  "typeFund": "FII",
  "type": 40
}
```

Output:

```text
Paginated[StructuredReport]
```

---

## Endpoint E — negociações

```text
GET /SIG/FormConsultaNegociacoes.asp
```

Input:

```text
strTipoResumo=RES_NEGOCIACOES
strSocEmissora=<TICKER>
strDtReferencia=<MM/YYYY>
strIdioma=P
intCodNivel=1
intCodCtrl=100
```

Output:

```text
HTML
```

---

# 36. Fonte oficial e estabilidade

A B3 disponibiliza uma página oficial de FIIs listados e mantém um catálogo de APIs/dados para o segmento de listados.

Entretanto, os endpoints aqui especificados possuem características de interfaces utilizadas pelo próprio portal:

```text
fundsListedProxy
FormConsultaNegociacoes.asp
```

e seus contratos não devem ser tratados como uma API pública versionada.

Consequentemente:

**não utilizar o formato atual da URL como contrato eterno.**

O contrato do FlowScope deve ser definido pela camada de adaptação:

```text
B3Adapter
```

e coberto por testes de contrato.

---

# 37. Testes de contrato

O projeto deve manter fixtures reais, anonimizadas quando necessário:

```text
tests/
    fixtures/
        b3/
            fund_alzr.json
            relevant_reports_alzr.json
            distributions_alzr.json
            monthly_reports_alzr.json
            negotiations_alzr_2026_06.html
```

Teste:

```python
def test_alzr_fnet_id():
    candidates = load_fixture("fund_alzr.json")

    assert candidates

    fnet_id = resolve_fnet_id_from_candidates(
        candidates
    )

    assert fnet_id == "20294"
```

Teste:

```python
def test_monthly_report_type():
    data = load_fixture(
        "monthly_reports_alzr.json"
    )

    assert all(
        item["describleType"]
        == "Informe Mensal Estruturado"
        for item in data["results"]
    )
```

Teste:

```python
def test_distribution_report_type():
    data = load_fixture(
        "distributions_alzr.json"
    )

    assert all(
        item["describleType"]
        == "Rendimentos e Amortizações"
        for item in data["results"]
    )
```

---

# 38. Teste de regressão

O pipeline deve detectar alterações na estrutura da B3.

Exemplos:

```text
campo removido
campo renomeado
tipo JSON -> HTML
HTML -> JSON
alteração de paginação
alteração do Base64
alteração do endpoint
mudança de status
mudança no nome do relatório
```

O teste deve falhar explicitamente em vez de produzir dados parcialmente incorretos.

---

# 39. Política de falha

Nunca retornar um dataset parcialmente válido sem indicar sua incompletude.

Exemplo:

```python
@dataclass
class AcquisitionResult:
    fund: B3Fund
    relevant_reports: list
    distributions: list
    monthly_reports: list
    negotiations: list

    warnings: list[str]
    errors: list[str]
```

Se:

```text
GetStructuredReports(type=40)
```

falhar, o resultado deve indicar:

```text
monthly_reports unavailable
```

em vez de:

```text
monthly_reports = []
```

porque:

```text
[] != erro de aquisição
```

---

# 40. Segurança

Não são necessários:

```text
username
password
API key
client secret
certificate
```

para os endpoints públicos observados nesta RFC.

Não devem ser armazenados cookies de sessão ou credenciais de usuário.

O FlowScope deve operar somente com:

```text
HTTP GET
```

para os endpoints especificados.

---

# 41. User-Agent

Recomenda-se identificar claramente o consumidor:

```text
User-Agent: FlowScope/<version>
```

Exemplo:

```text
FlowScope/0.1.0
```

Em vez de tentar se passar pelo navegador.

---

# 42. Observabilidade

Cada operação deve registrar:

```text
timestamp
ticker
fnet_id
endpoint
request parameters
HTTP status
duration
number of records
number of pages
parser version
```

Exemplo:

```text
B3 acquisition
ticker=ALZR
fnet_id=20294
operation=structured_reports
type=40
records=6
pages=1
status=200
duration_ms=428
```

Não registrar conteúdo financeiro sensível além do necessário.

---

# 43. Resultado normalizado esperado

Depois da aquisição, o FlowScope deverá possuir algo conceitualmente semelhante a:

```python
{
    "fund": {
        "ticker": "ALZR",
        "fnet_id": "20294",
        "name": "...",
        "trading_name": "..."
    },

    "relevant_reports": [...],

    "distributions": [
        {
            "reference_date": "2026-07-17",
            "document_id": 1252542,
            "type": "Rendimentos e Amortizações",
            "status": "active"
        }
    ],

    "monthly_reports": [
        {
            "reference_month": "2026-06",
            "document_id": 1250291,
            "type": "Informe Mensal Estruturado",
            "status": "active"
        }
    ],

    "negotiations": {
        "2026-06": {
            "source": "B3_SIG",
            "raw_document": "..."
        }
    }
}
```

---

# 44. Regra fundamental do pipeline

O fluxo deve ser:

```text
TICKER
  ↓
GetListClassFund
  ↓
FNET ID
  ↓
GetReportsRelevants
  ↓
GetStructuredReports(type=41)
  ↓
GetStructuredReports(type=40)
  ↓
SIG negotiations
  ↓
RAW DATA
  ↓
NORMALIZED DATA
  ↓
FINANCIAL METRICS
```

Nunca:

```text
TICKER
  ↓
assumir ID
  ↓
consultar relatórios
```

O identificador deve ser sempre resolvido pela própria B3.

---

# 45. Exemplo completo mínimo

```python
from datetime import date


def main():

    ticker = "ALZR"

    start = date(2026, 1, 1)
    end = date(2026, 7, 29)

    # Resolve ticker -> B3/FNET ID
    fnet_id, fund = resolve_fnet_id(ticker)

    print("FNET ID:", fnet_id)
    print("Fund:", fund["fundName"])

    # Relevant documents
    relevant = get_all_relevant_reports(
        fnet_id,
        start,
        end,
    )

    print(
        "Relevant reports:",
        len(relevant),
    )

    # Distributions
    distributions = get_distributions(
        fnet_id,
        start,
        end,
    )

    print(
        "Distributions:",
        len(distributions),
    )

    # Monthly reports
    monthly = get_monthly_reports(
        fnet_id,
        start,
        end,
    )

    print(
        "Monthly reports:",
        len(monthly),
    )

    # Negotiations
    for month in iter_months(start, end):

        html = get_trading_summary(
            ticker,
            month,
        )

        print(
            month,
            len(html),
            "bytes",
        )


if __name__ == "__main__":
    main()
```

---

# 46. Critério de aceitação

A implementação desta RFC será considerada concluída quando, para um ticker válido:

```text
ALZR
```

o sistema for capaz de:

1. resolver o ticker para o identificador B3/FNET;
2. identificar o `fnet_id = 20294` no exemplo;
3. consultar documentos relevantes;
4. consultar rendimentos/amortizações;
5. consultar informes mensais;
6. consultar o resumo de negociações;
7. tratar paginação;
8. preservar as respostas brutas;
9. extrair IDs de documentos FundosNet;
10. distinguir documentos ativos de cancelados;
11. registrar erros de aquisição separadamente de listas vazias;
12. executar novamente o processo de forma determinística;
13. funcionar para outro FII sem alteração do código específico do fundo.

---

# 47. Referências

**B3 — APIs / Developers**

[B3 for Developers — APIs Listados](https://developers.b3.com.br/apis/api-listados?utm_source=chatgpt.com)

A B3 informa no portal de desenvolvedores que as APIs documentadas são destinadas a clientes B2B.

**B3 — FIIs listados**

[B3 — FIIs listados](https://www.b3.com.br/en_us/products-and-services/trading/equities/investment-funds/fii/fiis-listados/?utm_source=chatgpt.com)

**B3 — Dados disponíveis**

[B3 — Dados disponíveis](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/up2data/dados-disponiveis/?utm_source=chatgpt.com)

A B3 descreve nesse canal os dados públicos disponíveis para produtos listados, incluindo Cadastro de Instrumentos e Negócios Consolidados.

**Endpoints observados**

```text
https://sistemaswebb3-listados.b3.com.br/
    fundsListedProxy/Search/GetListClassFund/

https://sistemaswebb3-listados.b3.com.br/
    fundsListedProxy/Search/GetReportsRelevants/

https://sistemaswebb3-listados.b3.com.br/
    fundsListedProxy/Search/GetStructuredReports/

https://bvmf.bmfbovespa.com.br/
    SIG/FormConsultaNegociacoes.asp
```

---

# 48. Decisão arquitetural

O FlowScope deve implementar os endpoints acima como um **B3 Source Adapter**, e não espalhar suas URLs, payloads Base64 e nomes de campos pela aplicação.

A fronteira recomendada é:

```text
                    FlowScope Domain
                           |
                           |
                 +---------v----------+
                 | B3FiiDataProvider  |
                 +---------+----------+
                           |
                 +---------v----------+
                 | B3 Adapter        |
                 |                   |
                 | GetListClassFund  |
                 | GetReports...     |
                 | Structured...     |
                 | SIG               |
                 +---------+----------+
                           |
                    External B3
```

Essa decisão permite substituir posteriormente a fonte por:

```text
B3 API contratada
CVM
FundosNet
UP2Data
outra fonte licenciada
```

sem alterar os cálculos do FlowScope.

**Conclusão:** a B3 deve ser tratada como uma fonte externa instável, enquanto o contrato estável deve ser o modelo normalizado do FlowScope.
