# RFC-010 — Deterministic FFO Engine

**Status:** Proposed
**Projeto:** FlowScope
**Domínio:** Fundos de Investimento Imobiliário — FII
**Objetivo:** cálculo determinístico do Funds From Operations (FFO) de FIIs brasileiros
**Dependências:** B3 FII Data Provider, CVM Open Data Provider
**Escopo:** FFO calculado pelo FlowScope
**Fora do escopo:** FFO explicitamente divulgado por gestores/administradores

---

## 1. Objetivo

Esta RFC define o algoritmo determinístico para cálculo do:

- FFO mensal;
- FFO trimestral;
- FFO acumulado em 12 meses;
- FFO por cota;
- FFO Yield;
- P/FFO.

O cálculo deve utilizar exclusivamente dados estruturados provenientes de fontes regulatórias/mercado e regras determinísticas de classificação.

A RFC não considera o FFO eventualmente divulgado pelo administrador ou gestor em relatório gerencial.

---

# 2. Princípio fundamental

O FlowScope não deve procurar um campo denominado `FFO`.

O FFO será derivado dos componentes econômicos divulgados pelo fundo.

```text
Dados regulatórios
       |
       v
Classificação dos componentes
       |
       +-- recorrente
       +-- fair value
       +-- alienação
       +-- não recorrente
       +-- desconhecido
       |
       v
FFO Engine
       |
       +--> FFO
       +--> FFO/cota
       +--> FFO Yield
       +--> P/FFO
```

---

# 3. Fontes

O mecanismo utilizará quatro fontes complementares.

| Fonte                              | Função                                                     |
| ---------------------------------- | ---------------------------------------------------------- |
| B3 `GetListClassFund`              | Resolver ticker → identificador FNET                       |
| B3 `GetStructuredReports(type=40)` | Identificar Informes Mensais Estruturados                  |
| B3 `GetStructuredReports(type=41)` | Rendimentos e amortizações                                 |
| CVM Informe Mensal                 | PL, cotas, cotistas e dados cadastrais/financeiros mensais |
| CVM Informe Trimestral             | Componentes de resultado estruturado                       |
| CVM DFIN                           | Demonstrações financeiras e reconciliação                  |

O conjunto CVM de Informe Mensal é atualizado semanalmente e contém os cinco anos mais recentes, além do histórico desde 2016.

O conjunto de Informe Trimestral possui a mesma política de atualização e histórico desde 2016.

As Demonstrações Financeiras estão disponíveis em arquivos anuais CSV.

---

# 4. Resolução do fundo

O ticker deve primeiro ser convertido para o identificador utilizado pela B3.

```text
ticker
  |
  v
GetListClassFund
  |
  v
CNPJ / ID FNET
```

Para ALZR, o fluxo anteriormente especificado resulta em:

```text
ticker = ALZR
idFNET = 20294
```

O FNET ID deve ser armazenado juntamente com o CNPJ do fundo/classe.

---

# 5. Identificação CVM

O cálculo não deve utilizar o ticker como chave primária na CVM.

A chave recomendada é:

```text
CNPJ_Fundo_Classe
```

A partir de 2025 a CVM alterou os conjuntos de FII para utilizar explicitamente:

```text
Tipo_Fundo_Classe
CNPJ_Fundo_Classe
Nome_Fundo_Classe
```

em lugar dos nomes anteriores.

O FlowScope deve manter um cadastro de correspondência:

```text
ticker
    |
    +-- CNPJ_Fundo_Classe
    |
    +-- idFNET
    |
    +-- Codigo_CVM
```

---

# 6. Dados B3 utilizados

A B3 não será utilizada como fonte contábil primária do FFO.

Ela será utilizada para:

### 6.1 Identificação

`GetListClassFund`

Campos:

```text
id
idMain
fundName
tradingName
```

### 6.2 Documentos

`GetReportsRelevants`

Campos relevantes:

```text
urlFundosNet
urlViewerFundosNet
referenceDate
referenceDateFormat
deliveryDateFormat
version
describleType
describleCategory
describleKind
status
```

### 6.3 Informe Mensal

`GetStructuredReports(type=40)`

Campos de controle:

```text
urlViewerFundosNet
referenceDate
referenceDateFormat
deliveryDateFormat
version
describleType
status
```

### 6.4 Rendimentos

`GetStructuredReports(type=41)`

Campos de controle:

```text
urlViewerFundosNet
referenceDate
referenceDateFormat
deliveryDateFormat
version
describleType
status
```

---

# 7. Papel da B3 no FFO Engine

Os dados B3 servem principalmente para:

```text
1. localizar o fundo;
2. localizar o documento regulatório;
3. obter o período de referência;
4. controlar versão;
5. rastrear a origem.
```

O cálculo financeiro deve utilizar os dados estruturados da CVM.

Isso evita que o algoritmo dependa do HTML ou do layout do portal B3.

---

# 8. Dados CVM — Informe Mensal

O Informe Mensal será utilizado para os dados de mercado e posição patrimonial.

Campos de identidade:

```text
Tipo_Fundo_Classe
CNPJ_Fundo_Classe
Nome_Fundo_Classe
Data_Referencia
```

Campos financeiros/quantitativos necessários:

```text
VL_PATRIM_LIQ
VL_PATRIM_LIQ_COTA
QT_COTA
NR_COTST
```

Quando disponíveis na versão correspondente do layout, o FlowScope deve preservar também os campos relacionados a:

```text
valor total de ativos
valor de mercado
quantidade de cotas
valor da cota
patrimônio líquido
número de cotistas
```

A RFC de aquisição do Informe Mensal define a forma de localizar e carregar essas colunas.

---

# 9. Dados CVM — Informe Trimestral

O Informe Trimestral é a principal fonte estruturada para o cálculo dos componentes de resultado.

O FlowScope deve utilizar os registros correspondentes às categorias econômicas do formulário:

## Receitas imobiliárias

```text
Receitas de aluguéis
Receitas de venda de imóveis
```

## Despesas imobiliárias

```text
Despesas de manutenção e conservação
Custos associados às propriedades
```

## Ajustes de avaliação

```text
Ajuste ao valor justo
Ajuste ao valor de realização
```

## Ativos financeiros

```text
Receitas de juros
Ajustes ao valor justo
Resultado na venda
```

## Aplicações financeiras

```text
Receitas de juros
Ajuste ao valor justo
Resultado na venda
```

## Despesas administrativas

```text
Taxa de administração
Taxa de performance
Custódia
Auditoria
Consultoria
Comissões
Taxas
Outras despesas administrativas
```

## Derivativos

```text
Resultado líquido com derivativos
```

O FlowScope deve preservar o código/identificador da linha original do Informe Trimestral, e não apenas seu texto descritivo.

---

# 10. Dados CVM — Demonstrações Financeiras

As DFIN serão utilizadas como fonte de reconciliação.

A base disponibiliza arquivos anuais:

```text
dfin_fii_2026.csv
dfin_fii_2025.csv
...
```

e a CVM atualiza os arquivos conforme sua política de dados.

A DFIN deverá ser utilizada para validar:

```text
resultado líquido
receitas
despesas
patrimônio líquido
resultado acumulado
```

O DFIN não substitui o Informe Trimestral no cálculo mensal.

---

# 11. Definição operacional de FFO

O FlowScope define:

```text
FFO =
resultado recorrente
gerado pela atividade econômica
do fundo
```

Excluindo:

```text
efeitos de fair value
ganhos/perdas de alienação
eventos não recorrentes
```

Formalmente:

```text
FFO =
Σ COMPONENTES_RECORRENTES_POSITIVOS
-
Σ COMPONENTES_RECORRENTES_NEGATIVOS
```

---

# 12. Classificação dos componentes

Cada componente deve possuir:

```python
class FFOComponentType(Enum):
    RECURRING = "RECURRING"
    FAIR_VALUE = "FAIR_VALUE"
    DISPOSAL = "DISPOSAL"
    NON_RECURRING = "NON_RECURRING"
    UNKNOWN = "UNKNOWN"
```

---

# 13. Regra de inclusão

Somente:

```text
RECURRING
```

entra automaticamente no FFO.

```text
FAIR_VALUE
DISPOSAL
NON_RECURRING
```

são excluídos.

```text
UNKNOWN
```

não entra no FFO.

Essa regra é deliberadamente conservadora.

---

# 14. FII de tijolo

Para um FII predominantemente imobiliário:

### Inclui

```text
Receita de aluguel
Receita recorrente de exploração imobiliária
Receita recorrente de estacionamento
Receita recorrente de serviços associados ao imóvel
```

quando explicitamente identificadas como recorrentes.

### Exclui

```text
Ajuste a valor justo de imóveis
Ganho na venda de imóveis
Perda na venda de imóveis
Ajuste ao valor de realização de estoques
```

### Despesas

Inclui:

```text
manutenção
conservação
administração
gestão
custódia
auditoria
consultoria
taxas recorrentes
```

---

# 15. FII de papel

Para FII de papel:

### Inclui

```text
juros de CRI
rendimentos de CRI
juros de outros ativos imobiliários
receitas recorrentes de aplicações financeiras
```

quando associados à operação recorrente.

### Exclui

```text
ganho por marcação a mercado
perda por marcação a mercado
ganho na venda de CRI
perda na venda de CRI
```

Portanto:

```text
juros de CRI
       |
       +--> FFO

MTM de CRI
       |
       +--> não FFO

ganho de venda de CRI
       |
       +--> não FFO
```

---

# 16. FII híbrido

Um FII híbrido deve ser calculado pela soma das fontes recorrentes:

```text
FFO =
FFO imobiliário
+
FFO financeiro
```

Não deve existir uma fórmula diferente apenas porque o fundo é classificado como híbrido.

---

# 17. FoF

Para fundos de fundos:

```text
rendimentos recorrentes de FIIs
```

são receita operacional recorrente.

Já:

```text
ganho de capital na venda de cotas
```

é classificado como:

```text
DISPOSAL
```

e excluído.

---

# 18. Aplicações financeiras

O FlowScope deve diferenciar:

```text
rendimento/juros
```

de:

```text
ganho de avaliação
```

e:

```text
ganho de alienação.
```

Assim:

```text
juros recorrentes
       -> +FFO

fair value
       -> 0

venda de ativo
       -> 0
```

---

# 19. Outras receitas/despesas

O campo genérico:

```text
Outras receitas/despesas
```

não deve ser automaticamente considerado recorrente.

Regra:

```text
se classificação explícita:
    aplicar classificação

caso contrário:
    UNKNOWN
```

Portanto:

```text
UNKNOWN -> excluído do FFO
```

---

# 20. Regra para componentes UNKNOWN

Quando uma linha não puder ser classificada:

```python
if component.type == UNKNOWN:
    component.included_in_ffo = False
```

Mas o valor deve permanecer disponível para auditoria.

Exemplo:

```json
{
  "description": "Outras receitas",
  "value": 125000,
  "classification": "UNKNOWN",
  "included_in_ffo": false
}
```

---

# 21. FFO mensal

O Informe Trimestral não deve ser tratado como se fosse uma série mensal independente.

Quando houver dados acumulados no trimestre:

```text
Q1 = Jan + Fev + Mar
Q2 = Abr + Mai + Jun
Q3 = Jul + Ago + Set
Q4 = Out + Nov + Dez
```

Quando a estrutura fornecer apenas acumulado:

```text
Mês 1 = Q1 acumulado
Mês 2 = Q2 acumulado
...
```

não é permitido inferir meses sem uma base matemática suficiente.

Para derivar um mês:

```text
FFO_M2 = FFO_Acumulado_M2 - FFO_Acumulado_M1
```

somente quando ambos os valores tiverem a mesma base temporal e contábil.

---

# 22. FFO 12M

O FFO de 12 meses é:

```text
FFO_12M =
Σ FFO_Month_i
```

dos últimos 12 meses completos.

Não utilizar:

```text
últimos 12 registros
```

sem validar a competência.

A janela deve ser:

```text
[reference_date - 11 meses, reference_date]
```

---

# 23. FFO por cota

Definição:

```text
FFO_per_share =
FFO_12M / weighted_average_shares
```

Quando o número médio ponderado de cotas não estiver diretamente disponível:

```text
weighted_average_shares =
Σ(QT_COTA_i × days_i)
/
Σ days_i
```

Exemplo:

```python
weighted_shares = (
    sum(qty * days for qty, days in observations)
    / sum(days for _, days in observations)
)
```

---

# 24. FFO Yield

Definição:

```text
FFO_Yield =
FFO_per_share_12M
/
market_price
```

ou:

```text
FFO_Yield =
FFO_12M
/
market_cap
```

Resultado:

```text
FFO_Yield_percent =
FFO_Yield × 100
```

---

# 25. P/FFO

Definição:

```text
P_FFO =
market_price
/
FFO_per_share_12M
```

ou:

```text
P_FFO =
market_cap
/
FFO_12M
```

As duas formas devem produzir o mesmo resultado quando utilizarem a mesma quantidade de cotas.

---

# 26. Relação matemática

Para valores positivos:

```text
P/FFO = 1 / FFO Yield
```

Se:

```text
FFO Yield = 12%
```

então:

```text
P/FFO = 8.333x
```

---

# 27. Preço de mercado

O preço utilizado no FFO Yield/P-FFO deve ser explicitamente identificado.

Fonte:

```text
B3 negociação
```

preferencialmente:

```text
preço de fechamento da data de referência
```

Nunca utilizar:

```text
preço atual
```

para calcular um indicador histórico.

---

# 28. Data de referência

O cálculo deve utilizar:

```text
financial_reference_date
+
market_reference_date
```

Exemplo:

```text
financial_reference_date = 2026-07-31
market_reference_date    = 2026-07-31
```

Caso não exista negociação na data:

```text
último pregão anterior
```

deve ser utilizado, registrando:

```text
market_price_date
```

separadamente.

---

# 29. Reconciliação

O resultado calculado deve ser reconciliado com:

```text
DFIN
```

e:

```text
Informe Trimestral
```

Diferenças superiores ao limite configurado devem gerar warning.

Exemplo:

```python
difference = abs(
    calculated_result - reported_result
) / abs(reported_result)
```

O valor limite recomendado inicialmente:

```text
1%
```

---

# 30. Proveniência

Cada componente do FFO deve possuir:

```json
{
  "source": "CVM",
  "dataset": "INF_TRIMESTRAL",
  "file": "inf_trimestral_fii_2026.zip",
  "cnpj_fundo_classe": "...",
  "reference_date": "2026-06-30",
  "field": "...",
  "value": 123456.78,
  "classification": "RECURRING"
}
```

Isso permite explicar:

> "Por que o FlowScope chegou a este FFO?"

---

# 31. Exemplo Python

```python
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal


class FFOType(Enum):
    RECURRING = "RECURRING"
    FAIR_VALUE = "FAIR_VALUE"
    DISPOSAL = "DISPOSAL"
    NON_RECURRING = "NON_RECURRING"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class FFOComponent:
    value: Decimal
    classification: FFOType


def calculate_ffo(
    components: list[FFOComponent],
) -> Decimal:

    result = Decimal("0")

    for component in components:

        if component.classification == FFOType.RECURRING:
            result += component.value

    return result
```

---

# 32. Exemplo

```python
components = [
    FFOComponent(
        Decimal("10000000"),
        FFOType.RECURRING,
    ),
    FFOComponent(
        Decimal("-2000000"),
        FFOType.RECURRING,
    ),
    FFOComponent(
        Decimal("5000000"),
        FFOType.FAIR_VALUE,
    ),
    FFOComponent(
        Decimal("3000000"),
        FFOType.DISPOSAL,
    ),
]

ffo = calculate_ffo(components)

assert ffo == Decimal("8000000")
```

---

# 33. Qualidade do resultado

O FlowScope deve atribuir uma qualidade ao FFO:

```text
HIGH
MEDIUM
LOW
```

### HIGH

Todos os componentes relevantes foram classificados.

### MEDIUM

Existem componentes `UNKNOWN`, mas representam parcela pequena.

### LOW

Existem componentes materiais não classificados.

Exemplo:

```python
unknown_ratio = (
    abs(unknown_value)
    /
    abs(total_income)
)
```

---

# 34. Regra de materialidade

Inicialmente:

```text
UNKNOWN <= 1% do resultado
    -> HIGH/MEDIUM

UNKNOWN > 1%
    -> MEDIUM

UNKNOWN > 5%
    -> LOW
```

Esses limites devem ser configuráveis.

---

# 35. Resultado do FFO Engine

```json
{
  "ticker": "ALZR",
  "reference_date": "2026-07-31",
  "ffo_month": 1250000.0,
  "ffo_12m": 14800000.0,
  "weighted_average_shares": 1000000,
  "ffo_per_share": 14.8,
  "market_price": 105.0,
  "ffo_yield": 0.140952,
  "p_ffo": 7.0946,
  "quality": "HIGH"
}
```

---

# 36. Requisitos de implementação

O FFO Engine deve ser:

```text
determinístico
reproduzível
auditável
versionado
independente do ticker
independente do gestor
```

Nenhum LLM pode participar do cálculo.

LLM pode, posteriormente, auxiliar na classificação de uma descrição desconhecida, mas **não pode determinar o resultado financeiro em produção sem uma regra determinística equivalente e validada**.

---

# 37. Arquitetura

```text
B3 Adapter
     |
     +--> ticker / FNET / documents
     |
     v
CVM Adapter
     |
     +--> Informe Mensal
     +--> Informe Trimestral
     +--> DFIN
     |
     v
CVM Normalizer
     |
     v
FFO Component Classifier
     |
     v
FFO Engine
     |
     +--> FFO
     +--> FFO/cota
     +--> FFO Yield
     +--> P/FFO
```

---

# 38. Critérios de aceitação

A implementação será aceita quando:

1. receber qualquer ticker válido;
2. resolver o fundo na B3;
3. resolver sua identidade CVM;
4. carregar os dados CVM correspondentes;
5. classificar os componentes;
6. calcular FFO;
7. calcular FFO/cota;
8. calcular FFO Yield;
9. calcular P/FFO;
10. preservar a origem de cada componente;
11. detectar dados desconhecidos;
12. detectar reapresentações;
13. não depender de valores publicados pelo gestor como FFO.

---

# 39. Observação sobre mudanças de layout

Os conjuntos CVM são sujeitos a alterações de layout.

A própria CVM registra alterações recentes nos campos de identificação dos FIIs devido à adaptação à Resolução CVM 175.

Portanto, os nomes das colunas devem ser tratados por uma camada de schema versioning.

---

# 40. Fontes oficiais

- [CVM — Informe Mensal Estruturado](https://dados.cvm.gov.br/dataset/fii-doc-inf_mensal?utm_source=chatgpt.com)
- [CVM — Informe Trimestral Estruturado](https://dados.cvm.gov.br/dataset/fii-doc-inf_trimestral?utm_source=chatgpt.com)
- [CVM — Dados DFIN](https://dados.cvm.gov.br/dados/FII/DOC/DFIN/DADOS/?utm_source=chatgpt.com)
- [CVM — arquivos do Informe Mensal](https://dados.cvm.gov.br/dados/FII/DOC/INF_MENSAL/DADOS/?utm_source=chatgpt.com)
- [CVM — arquivos do Informe Trimestral](https://dados.cvm.gov.br/dados/FII/DOC/INF_TRIMESTRAL/DADOS/?utm_source=chatgpt.com)
