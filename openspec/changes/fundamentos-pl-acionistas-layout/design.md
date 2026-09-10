## Context

Ver `proposal.md - Why`. A tabela de Fundamentos é alimentada por `FundamentalAnalysisUseCase`, que compõe `AnaliseFundamental` a partir de campos normalizados do Fundamentus (`fundamental_ports.CAMPO_*`), do patrimônio/cotistas do Informe Mensal da CVM e do histórico de dividendos. O parser do Fundamentus já coleta `P/L` (em `_INDICADORES`), mas o adapter não o expõe; não há campo de P/L no domínio nem coluna na tabela. Não existe resolução ticker→CNPJ para ações (o `B3FundRepository` é FII-only) nem qualquer fonte de quantidade de acionistas. As larguras de coluna são persistidas por id estável (`fundamental_table.py`), então reordenar colunas não invalida a configuração do usuário.

## Goals / Non-Goals

**Goals:**
- Expor P/L para Papel (fonte) e FII (derivado) com uma única coluna.
- Preencher "Nº de cotistas" no Papel com a quantidade de acionistas da CVM, reutilizando a classificação existente.
- Reordenar as colunas e adicionar P/L após P/VP.
- Unificar os rótulos descritivos de tendência e aplicar bandas percentuais de ±5% à tendência do dividendo.

**Non-Goals:**
- Cotas alugadas (indisponível nas fontes atuais).
- Série histórica de acionistas ou detalhamento por classe de ação (apenas o total).
- Alterar a fonte de cotistas dos FIIs (permanece Informe Mensal/B3).
- Mudar os limiares da tendência do FFO (±20%/±5%).

## Decisions

### P/L do Papel vem do provider; P/L do FII é derivado por função pura

Adicionar `CAMPO_P_L = "p_l"` em `fundamental_ports.py` e mapear `_INDICADOR_P_L = "P/L"` no adapter do Fundamentus. O caso de uso preenche `AnaliseFundamental.p_l` assim: se a fonte reportou `p_l`, usa-o (Papel); senão, para FII, calcula por função pura `p_l(preco, ultimo_dividendo)` em `domain/fii/metrics.py`, que anualiza o dividendo mensal (`preco / (ultimo_dividendo × 12)`) para que o P/L represente a quantidade de anos, tal como o P/L de uma ação, retornando `None` quando o dividendo for ausente/zero.

- **Alternativa descartada**: derivar P/L do Papel de `Preço / LPA` — o Fundamentus já reporta `P/L` diretamente e o LPA pode estar ausente.
- **Alternativa descartada**: calcular o P/L do FII na apresentação (como `_payout`) — a decisão é manter a métrica determinística e testável no domínio.
- **Detecção de FII**: a derivação usa o **tipo de exibição** (discriminador `FII` do Fundamentus), não a taxonomia determinística `TAXONOMIA_FII_PADRAO`, que cobre apenas 11 tickers. Usar a taxonomia deixaria a maioria dos FIIs reais (fora da lista) sem P/L, pois `classificar_ticker` os retorna como `DESCONHECIDO`.

### Reuso de `cotistas` e da classificação existente para ações

`AnaliseFundamental.cotistas` continua sendo o campo único. Para FII, segue vindo de `PatrimonioFii.cotistas`; para Papel, quando ausente, é preenchido por uma nova porta de acionistas. `classificar_cotistas` (limiares RFC-006) é reutilizado sem alteração. O cabeçalho permanece "Nº de cotistas" para ambos os tipos.

- **Trade-off**: as faixas foram calibradas para FIIs; uma companhia com ~1,18M acionistas cai em `GIGANTE`. Aceito por ora, pois o rótulo é qualitativo e a escala não colide.

### Nova porta de acionistas, implementada sobre FRE + FCA

Nova porta `AcionistasProvider.obter_acionistas(ticker, reference_date) -> int | None`. Implementação CVM:

```
ticker --(FCA valor_mobiliario: Codigo_Negociacao->CNPJ_Companhia)--> CNPJ
CNPJ   --(FRE distribuicao_capital: ultima Versao)--> PF + PJ + Institucionais
```

- **Aquisição**: reutilizar `CvmDatasetDownloader` (`infrastructure/cvm/datasets.py`), que já baixa/extrai/hasheia/cacheia datasets anuais com revalidação condicional. Instanciar um downloader para o FRE (`fre_cia_aberta_<ano>.zip`, CSV `fre_cia_aberta_distribuicao_capital_<ano>.csv`) e outro para o FCA (`fca_cia_aberta_<ano>.zip`, CSV `fca_cia_aberta_valor_mobiliario_<ano>.csv`).
- **Vigência**: dentro do arquivo anual, selecionar o registro de maior `Versao` por CNPJ, sem filtrar por `Data_Referencia` (que pode ser futura). Se o ano corrente não tiver o CNPJ, tentar anos anteriores.
- **Alternativa descartada**: usar `listedCompaniesProxy`/`codeCVM` — o FRE é chaveado por CNPJ, não por codeCVM, então a ponte seria indireta e exigiria mais um dataset.

### Cache em dois níveis: arquivo bruto e informação normalizada

O cache deve cobrir tanto os arquivos anuais quanto as informações derivadas:

1. **Arquivo bruto** — `CvmDatasetDownloader` já grava o ZIP anual, o `SHA256` e os metadados de revalidação (ETag/Last-Modified) sob o cache do FlowScope. FRE e FCA passam a usar esse fluxo.
2. **Informação normalizada** — o mapa ticker→CNPJ (do FCA) e a quantidade de acionistas por CNPJ (do FRE) DEVEM ser cacheados com `CacheManager`, associados ao hash do arquivo de origem e à versão do parser. Assim, análises repetidas não reescaneiam os CSVs; o cache é invalidado quando o hash do arquivo ou a versão do parser muda.

- **Alternativa descartada**: cachear apenas o arquivo bruto e reprocessar o CSV a cada análise — o FRE tem 653 companhias e o FCA centenas de tickers; o reescaneio por ticker seria desperdício.
- **Consistência**: seguir o padrão do `FundamentusProvider` (cache versionado por `parser_version`) e do `CvmMonthlyReportRepository` (hash do arquivo de origem).

### `TendenciaDividendo` passa a ter cinco faixas com os rótulos do FFO

Trocar os valores de `TendenciaDividendo` para `FORTE_ALTA`/`ALTA`/`ESTAVEL`/`QUEDA`/`FORTE_QUEDA` (+ `N_A`) e classificar a variação percentual `(último − anterior) / anterior` com limiares ±5%. `calcular_tendencia` passa a receber os dois valores e calcular a fração.

- **Alternativa descartada**: manter `CRESCIMENTO`/`REDUCAO`/`NEUTRO` e mapear para os cinco rótulos na apresentação — não expressa as quatro intensidades pedidas.
- **Bordas**: `anterior == 0` e `último > 0` → `FORTE_ALTA`; ambos zero → `ESTAVEL`.
- `TendenciaFfo` e `TendenciaDividendo` permanecem enums separados (semântica distinta), mas a apresentação usa um único mapa de rótulos (`Forte Alta`, `Leve Alta`, `Estável`, `Leve Queda`, `Forte Queda`).

### Reordenação da tabela e alinhamento

Reordenar a tupla `_COLUNAS` para a ordem do proposal, inserindo `("p_l", "P/L")` após `p_vp`, e atualizar as tuplas de `_linha_analise`/`_linha_sintetica` na mesma ordem. Adicionar `p_l` a `_COLUNAS_DIREITA`.

## Risks / Trade-offs

- **[CSV/cópia e testes quebram com a nova ordem]** → atualizar `gui-interface` (feito nas specs), o cabeçalho de `test_fundamental_table.py` e os índices de coluna; o `clipboard-export` reusa `montar_csv`, então herda a ordem automaticamente.
- **[Download anual do FRE é ~8 MB/ano]** → cache anual com revalidação condicional já existente; a informação normalizada também é cacheada, evitando reescaneio; a análise tolera falha de rede retornando `N/A`.
- **[`Data_Referencia` futura no FRE]** → selecionar por `Versao`, nunca por data; registrar a suposição nos testes de contrato.
- **[P/L heterogêneo entre Papel e FII]** → documentar no OrientationPanel que, para FII, o P/L anualiza o último dividendo (preço ÷ (último dividendo × 12)), enquanto o de Papel é o lucro reportado; ambos expressam anos para recuperar o investimento.
- **[Mudança de valores de `TendenciaDividendo`]** → atualizar `test_dividends.py` e `test_fundamental_use_case.py`, que hoje esperam `CRESCIMENTO`/`N_A`.

## Migration Plan

Sem migração de dados. O cache do Fundamentus é versionado por parser; os novos datasets CVM usam chaves anuais novas. Rollback = reverter a change.

## Open Questions

- Se a CVM não publicar o ticker no FCA de um ano, vale tentar o ano anterior para a ponte? (pode ser respondido na implementação sem alterar as specs).
