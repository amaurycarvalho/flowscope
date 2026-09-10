## Context

A coluna `P/VP` precisa de patrimônio líquido e cotas, hoje ausentes em produção. O `CvmFiiAdapter` atual (`infrastructure/fii/cvm.py`) já lê o CSV do Informe Mensal, mas: (a) espera o schema legado (`CNPJ_FUNDO`, `QUANT_COTA`, `DT_COMPTC`); (b) recebe um `resolver_cnpj` externo que nada fornece no wiring; (c) não trata reapresentações, hash ou metadados. A RFC-009 especifica a extração determinística por CNPJ sobre os dados abertos anuais. Ver `proposal.md` para motivação.

A change `b3-fii-identity-and-dividends` fornece `B3Fund`, cujo `tradingName` do registro derivado é o CNPJ do fundo (ex.: `28.737.771/0001-85`), permitindo resolver a identidade sem uma nova fonte.

## Goals / Non-Goals

**Goals:**
- Obter o Informe Mensal Estruturado por CNPJ de forma determinística e cacheada.
- Normalizar patrimônio/cotas/cotistas e alimentar `P/VP`.
- Suportar schema atual e legado com versionamento explícito.

**Non-Goals:**
- Informe Trimestral e DFIN (fase do motor de FFO, RFC-010).
- Substituir o cálculo de métricas do domínio; apenas fornecer a entrada de patrimônio.
- `pandas`; mantém-se `zipfile`+`csv` da stdlib.

## Decisions

### 1. Aquisição por dados abertos anuais, não scraping

Download de `inf_mensal_fii_<ano>.zip` e extração dos CSVs com `zipfile`+`csv`, filtrando por CNPJ normalizado. **Alternativa:** scraping da página da CVM — rejeitado pela RFC-009 §39 e por fragilidade.

### 2. Schema versioning por conjunto de colunas

Resolução de colunas por aliases (`CNPJ_Fundo_Classe`/`CNPJ_Fundo`, `QT_COTA`/`QUANT_COTA`) e erro explícito quando faltam colunas obrigatórias. **Alternativa:** decidir por ano (`>=2025`) — rejeitado pela RFC-009 §36.

### 3. Identidade a partir da camada B3 + cadastro CVM

`ticker → B3Fund.tradingName (CNPJ)` com fallback para o cadastro CVM (`resolver_code_cvm`/`code-cvm-resolution`). O CNPJ é normalizado (sem pontuação) e validado contra o registro retornado (RFC-009 §33).

### 4. Índice e reapresentações

Ao carregar um ano, construir um índice `CNPJ + competência → registros` e selecionar a versão mais recente por campos de versão/recebimento, marcando `is_latest` e preservando as anteriores. **Alternativa:** `drop_duplicates` cego — rejeitado (RFC-009 §21).

### 5. Encapsular o adapter existente

O novo repositório fornece `PatrimonioFii` e o `CvmFiiAdapter` passa a delegar a ele, preservando o contrato consumido pelo `FundamentalRepository`. **Alternativa:** manter o adapter legado e criar um paralelo — duplicaria lógica de parsing.

### 6. Persistência sob o CacheManager

Arquivo bruto, `SHA256` e `metadata.json` em `~/.cache/flowscope/cvm/inf_mensal/<ano>/`, seguindo a convenção do projeto; reutiliza `CacheManager.get_or_fetch` com chave por dataset+ano+hash.

## Risks / Trade-offs

- **[Risco] ZIPs grandes e atualização semanal** → Cache por ano+hash; baixar somente quando o hash mudar; sem download por ticker.
- **[Risco] Mudança de layout da CVM (Resolução 175)** → Aliases e erro de schema explícito com `SOURCE_SCHEMA_VERSION`.
- **[Risco] Encoding latin1 e separador `;`** → Parser configurável e tolerante, como o adapter atual.
- **[Trade-off] P/VP depende de preço e cotas consistentes** → Usa o preço de fechamento já carregado e a competência mais recente até a data de referência.
- **[Trade-off] Reapresentações aumentam o volume** → Seleção determinística e preservação apenas do bruto.

## Migration Plan

1. Introduzir o repositório/serviço CVM por CNPJ e os testes com fixtures de CSV (schema atual e legado).
2. Ligar a resolução de identidade (B3/cadastro) ao wiring do `FundamentalRepository`.
3. Fazer o `CvmFiiAdapter` delegar ao novo repositório.
4. Remover o `resolver_cnpj` sem fonte quando o wiring novo estiver ativo.
5. Rollback: manter o adapter atual como fallback quando o novo repositório não estiver configurado.
