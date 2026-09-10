# RFC-009 — CVM Data Extraction Pipeline

**Status:** Proposed
**Projeto:** FlowScope
**Fonte:** CVM Dados Abertos
**Dataset:** FII — Documentos: Informe Mensal Estruturado
**Objetivo:** obter, de forma determinística, os Informes Mensais Estruturados de um FII a partir do ticker.

---

# 1. Objetivo

Aquisição de Informe Mensal Estruturado por Ticker

Implementar um adaptador que permita:

```text
ticker
   ↓
CVM identification
   ↓
CNPJ_Fundo_Classe
   ↓
arquivo anual
   ↓
Informe Mensal
   ↓
registros do fundo
```

A fonte não deve ser consultada por página HTML da CVM.

O método oficial será o download dos arquivos de dados abertos.

---

# 2. Fonte

Dataset:

```text
FII: Documentos: Informe Mensal Estruturado
```

O conjunto é definido pela CVM como documento eletrônico periódico do FII, encaminhado pelo Sistema Fundos.NET.

A CVM informa que:

```text
últimos 5 anos
+
histórico desde 2016
```

estão disponíveis.

Os arquivos são atualizados semanalmente, inclusive com reapresentações.

---

# 3. URLs

Dataset:

```text
https://dados.cvm.gov.br/dataset/fii-doc-inf_mensal
```

Diretório:

```text
https://dados.cvm.gov.br/dados/FII/DOC/INF_MENSAL/
```

Dados:

```text
https://dados.cvm.gov.br/dados/FII/DOC/INF_MENSAL/DADOS/
```

Metadados:

```text
https://dados.cvm.gov.br/dados/FII/DOC/INF_MENSAL/META/
```

O diretório atualmente contém, entre outros, arquivos:

```text
inf_mensal_fii_2022.zip
inf_mensal_fii_2023.zip
inf_mensal_fii_2024.zip
inf_mensal_fii_2025.zip
inf_mensal_fii_2026.zip
```

conforme o índice oficial.

---

# 4. Ausência de autenticação

O download dos arquivos é público.

Não são necessários:

```text
API key
username
password
OAuth
cookie
sessão
```

O FlowScope deve utilizar HTTP/HTTPS diretamente.

---

# 5. Não baixar um arquivo por ticker

A CVM disponibiliza os dados agrupados por ano.

Portanto, para:

```text
ALZR
```

não existe:

```text
ALZR.csv
```

O processo é:

```text
inf_mensal_fii_2026.zip
       |
       v
extrair CSVs
       |
       v
filtrar CNPJ_Fundo_Classe
```

---

# 6. Problema fundamental: ticker não é chave CVM

A CVM trabalha com identificadores regulatórios.

O ticker:

```text
ALZR
```

não deve ser utilizado diretamente como chave de filtro do dataset.

A chave operacional deve ser:

```text
CNPJ_Fundo_Classe
```

O FlowScope deve manter uma tabela de identidade:

```text
ticker
CNPJ_Fundo_Classe
Codigo_CVM
idFNET
Nome_Fundo_Classe
```

---

# 7. Obtenção do CNPJ

O CNPJ pode ser obtido através do cadastro regulatório do fundo.

Para a arquitetura do FlowScope:

```text
B3 GetListClassFund
        +
CVM cadastro
        ↓
FundIdentity
```

Exemplo:

```python
@dataclass(frozen=True)
class FundIdentity:
    ticker: str
    cnpj_fundo_classe: str
    codigo_cvm: str | None
    id_fnet: str | None
    name: str
```

---

# 8. Normalização do CNPJ

O CNPJ deve ser armazenado sem pontuação.

```python
import re


def normalize_cnpj(value: str) -> str:
    return re.sub(r"\D", "", value)
```

Exemplo:

```text
28.737.771/0001-85
```

vira:

```text
28737771000185
```

---

# 9. Seleção do arquivo anual

Para uma competência:

```text
2026-07-31
```

o arquivo será:

```text
inf_mensal_fii_2026.zip
```

Função:

```python
def monthly_zip_url(year: int) -> str:

    return (
        "https://dados.cvm.gov.br/"
        "dados/FII/DOC/INF_MENSAL/DADOS/"
        f"inf_mensal_fii_{year}.zip"
    )
```

---

# 10. Download

```python
import requests


def download_monthly_dataset(year: int) -> bytes:

    url = monthly_zip_url(year)

    response = requests.get(
        url,
        timeout=60,
    )

    response.raise_for_status()

    return response.content
```

---

# 11. Armazenamento local

O FlowScope deve manter:

```text
data/raw/cvm/
    inf_mensal/
        2024/
        2025/
        2026/
```

Exemplo:

```text
data/raw/cvm/inf_mensal/2026/
    inf_mensal_fii_2026.zip
```

---

# 12. Hash

Cada download deve ser identificado por hash.

```python
import hashlib


def sha256(data: bytes) -> str:

    return hashlib.sha256(data).hexdigest()
```

Isso permite identificar alteração do arquivo oficial.

---

# 13. Extração

```python
from io import BytesIO
from zipfile import ZipFile


def extract_zip(data: bytes) -> dict[str, bytes]:

    result = {}

    with ZipFile(BytesIO(data)) as archive:

        for name in archive.namelist():

            if name.endswith(".csv"):
                result[name] = archive.read(name)

    return result
```

---

# 14. Estrutura interna

A CVM disponibiliza o conjunto como ZIP porque o Informe Mensal é composto por tabelas/arquivos estruturados.

O código não deve assumir que haverá apenas um CSV.

Deve descobrir os arquivos:

```python
csv_files = [
    name
    for name in archive.namelist()
    if name.lower().endswith(".csv")
]
```

---

# 15. Leitura com pandas

```python
import pandas as pd
from io import BytesIO


def read_csv(
    data: bytes,
) -> pd.DataFrame:

    return pd.read_csv(
        BytesIO(data),
        sep=";",
        encoding="latin1",
        low_memory=False,
    )
```

O parser deve ser configurável porque layouts históricos podem apresentar diferenças de encoding/estrutura.

---

# 16. Schema discovery

Antes de processar o dataset:

```python
def inspect_schema(df):

    return {
        "columns": list(df.columns),
        "rows": len(df),
        "dtypes": df.dtypes.astype(str).to_dict(),
    }
```

O FlowScope deve registrar:

```text
arquivo
versão
colunas
quantidade de registros
```

---

# 17. Campos de identidade

Para o layout atual, utilizar:

```text
Tipo_Fundo_Classe
CNPJ_Fundo_Classe
Nome_Fundo_Classe
```

A mudança desses campos foi oficialmente registrada pela CVM em janeiro de 2025.

Para dados históricos, o adaptador deve aceitar também:

```text
CNPJ_Fundo
Nome_Fundo
```

como aliases legados.

---

# 18. Compatibilidade de schema

```python
COLUMN_ALIASES = {
    "CNPJ_Fundo_Classe": [
        "CNPJ_Fundo_Classe",
        "CNPJ_Fundo",
    ],

    "Nome_Fundo_Classe": [
        "Nome_Fundo_Classe",
        "Nome_Fundo",
    ],

    "Tipo_Fundo_Classe": [
        "Tipo_Fundo_Classe",
        "Tipo_Fundo",
    ],
}
```

Função:

```python
def resolve_column(
    df,
    canonical_name: str,
) -> str:

    for candidate in COLUMN_ALIASES[canonical_name]:

        if candidate in df.columns:
            return candidate

    raise KeyError(
        f"Column not found: {canonical_name}"
    )
```

---

# 19. Filtragem por CNPJ

```python
def filter_fund(
    df,
    cnpj: str,
):
    column = resolve_column(
        df,
        "CNPJ_Fundo_Classe",
    )

    normalized = (
        df[column]
        .astype(str)
        .map(normalize_cnpj)
    )

    return df[
        normalized == normalize_cnpj(cnpj)
    ].copy()
```

---

# 20. Filtragem por competência

Depois de identificar a coluna de referência:

```python
reference_column = resolve_reference_column(df)
```

o filtro deve ser:

```python
df[
    df[reference_column]
    == reference_date
]
```

Nunca utilizar a posição física do registro no CSV.

---

# 21. Reapresentações

A CVM informa explicitamente que os arquivos são atualizados com eventuais reapresentações.

Portanto, pode haver mais de um registro para:

```text
CNPJ
+
competência
```

O FlowScope não deve simplesmente:

```python
df.drop_duplicates()
```

sem entender a versão.

---

# 22. Regra de reapresentação

Quando existirem múltiplas versões:

```text
CNPJ
+
competência
```

o FlowScope deve selecionar a versão mais recente conforme os campos de versão/data de recebimento disponibilizados pelo dataset.

A versão selecionada deve ser registrada:

```json
{
  "is_latest": true,
  "source_version": "...",
  "received_at": "..."
}
```

Os registros anteriores devem permanecer no RAW DATA.

---

# 23. Resultado do adaptador

```python
@dataclass(frozen=True)
class MonthlyReport:

    ticker: str

    cnpj_fundo_classe: str

    reference_date: date

    raw_rows: dict

    source_file: str

    source_hash: str
```

---

# 24. API interna

```python
class CVMMonthlyReportRepository:

    def get(
        self,
        cnpj_fundo_classe: str,
        reference_date: date,
    ) -> MonthlyReport:
        ...
```

E:

```python
class CVMMonthlyReportService:

    def get_by_ticker(
        self,
        ticker: str,
        reference_date: date,
    ) -> MonthlyReport:
        ...
```

---

# 25. Consulta de vários meses

```python
def get_months(
    ticker,
    cnpj,
    start_year,
    end_year,
):
    reports = []

    for year in range(
        start_year,
        end_year + 1,
    ):

        data = download_monthly_dataset(year)

        files = extract_zip(data)

        for filename, content in files.items():

            df = read_csv(content)

            fund = filter_fund(
                df,
                cnpj,
            )

            reports.append(
                (filename, fund)
            )

    return reports
```

Na implementação final, os arquivos devem ser carregados apenas uma vez por ano.

---

# 26. Otimização

Não fazer:

```text
download ZIP
    ↓
para cada ticker
```

Fazer:

```text
download ZIP
    ↓
cache
    ↓
índice CNPJ
    ↓
qualquer ticker
```

Exemplo:

```text
2026 ZIP
   |
   +-- CNPJ A
   +-- CNPJ B
   +-- CNPJ C
   +-- ...
```

---

# 27. Índice local

Recomenda-se criar:

```text
CVMMonthlyIndex
```

com:

```text
year
cnpj_fundo_classe
reference_date
source_file
row_location
source_hash
```

Isso torna consultas posteriores praticamente instantâneas.

---

# 28. Exemplo

```python
index = {
    (
        "28737771000185",
        "2026-07-31",
    ): {
        "file": "inf_mensal_fii_2026.csv",
        "row": 18234,
    }
}
```

---

# 29. Cache

A chave deve ser:

```text
dataset
+
year
+
source_hash
```

Exemplo:

```text
INF_MENSAL
2026
sha256:...
```

Se o hash não mudou:

```text
não baixar novamente
```

---

# 30. Atualização semanal

A CVM informa periodicidade semanal para o conjunto.

O FlowScope pode executar:

```text
weekly refresh
```

ou:

```text
refresh on demand
```

---

# 31. Modo incremental

Para uma consulta em:

```text
2026-07
```

o sistema deve:

1. verificar cache;
2. verificar hash/metadata;
3. baixar somente se necessário;
4. atualizar o índice;
5. selecionar a versão válida.

---

# 32. Validações

Após o filtro:

```python
if fund.empty:
    raise FundNotFoundError(...)
```

Se houver:

```python
len(fund) > 1
```

não considerar automaticamente erro.

Primeiro verificar:

```text
versão
reapresentação
competência
tipo de fundo/classe
```

---

# 33. Validação de identidade

O registro encontrado deve confirmar:

```text
CNPJ
+
Nome
+
Tipo
```

contra a identidade previamente resolvida.

Exemplo:

```python
assert normalize_cnpj(
    row["CNPJ_Fundo_Classe"]
) == cnpj
```

---

# 34. Ticker não deve ser gravado como dado CVM

O ticker é uma informação de integração:

```text
ticker -> identidade regulatória
```

Não se deve sobrescrever:

```text
Nome_Fundo_Classe
```

com o ticker.

O resultado normalizado deve manter:

```json
{
  "ticker": "ALZR",
  "cnpj_fundo_classe": "...",
  "nome_fundo_classe": "..."
}
```

---

# 35. Tratamento de histórico

A CVM mantém histórico desde 2016.

O FlowScope deve suportar:

```text
2016 → atual
```

mas aplicar o schema correto para cada período.

---

# 36. Versionamento de schema

```text
CVM-INF-MENSAL-v1
CVM-INF-MENSAL-v2
...
```

O parser deve identificar a estrutura pelo conjunto de colunas.

Não utilizar somente:

```text
ano >= 2025
```

como mecanismo de versão.

---

# 37. Dados brutos

Manter:

```text
data/raw/cvm/
    inf_mensal/
        2026/
            inf_mensal_fii_2026.zip
            SHA256
            metadata.json
```

---

# 38. Metadata

Exemplo:

```json
{
  "dataset": "FII-INF-MENSAL",
  "year": 2026,
  "url": "https://dados.cvm.gov.br/...",
  "downloaded_at": "2026-09-10T12:00:00Z",
  "sha256": "...",
  "parser_version": "1.0.0"
}
```

---

# 39. Não utilizar scraping

O adaptador CVM não deve:

```text
scrape HTML
```

nem:

```text
simular navegador
```

A fonte de dados deve ser:

```text
/dados/FII/DOC/INF_MENSAL/DADOS/
```

---

# 40. Diferença em relação à B3

### B3

```text
ticker
 ↓
endpoint
 ↓
document URL
 ↓
document
```

### CVM

```text
ticker
 ↓
CNPJ
 ↓
arquivo anual
 ↓
CSV
 ↓
filtro
```

Portanto, a implementação dos dois providers deve permanecer independente.

---

# 41. Interface comum

```python
class MonthlyFundDataProvider(Protocol):

    def get_monthly_data(
        self,
        fund_identity: FundIdentity,
        reference_date: date,
    ) -> dict:
        ...
```

Implementações:

```text
B3MonthlyFundDataProvider
CVMMonthlyFundDataProvider
```

---

# 42. Critérios de aceitação

Para:

```text
ticker = ALZR
reference_date = 2026-07-31
```

o sistema deve:

1. resolver a identidade CVM;
2. determinar o arquivo anual;
3. baixar/cachear `inf_mensal_fii_2026.zip`;
4. localizar os CSVs;
5. reconhecer o schema;
6. localizar `CNPJ_Fundo_Classe`;
7. filtrar o fundo;
8. filtrar a competência;
9. tratar reapresentações;
10. devolver os registros normalizados;
11. preservar o arquivo original;
12. registrar hash;
13. registrar versão do parser.

---

# 43. Relação com FFO-001

Esta RFC é uma dependência de:

```text
FFO-001
```

A separação deve ser:

```text
CVM-001
   |
   +--> aquisição
   +--> cache
   +--> schema
   +--> identidade
   +--> normalização
          |
          v
FFO-001
   |
   +--> classificação econômica
   +--> FFO
   +--> FFO/cota
   +--> FFO Yield
   +--> P/FFO
```

A RFC CVM-001 **não calcula FFO**.

---

# 44. Fonte oficial

[CVM — Informe Mensal Estruturado](https://dados.cvm.gov.br/dataset/fii-doc-inf_mensal?utm_source=chatgpt.com)

A página oficial informa que o conjunto é o Informe Mensal eletrônico previsto no Anexo 39-I, disponibiliza os cinco anos mais recentes, histórico desde 2016 e atualizações semanais com reapresentações.

[CVM — arquivos do Informe Mensal](https://dados.cvm.gov.br/dados/FII/DOC/INF_MENSAL/DADOS/?utm_source=chatgpt.com)

O diretório oficial atualmente disponibiliza os arquivos anuais de 2016 a 2026.

[CVM — metadados do Informe Mensal](https://dados.cvm.gov.br/dados/FII/DOC/INF_MENSAL/META/?utm_source=chatgpt.com)

O diretório de metadados disponibiliza o dicionário de dados do conjunto.
