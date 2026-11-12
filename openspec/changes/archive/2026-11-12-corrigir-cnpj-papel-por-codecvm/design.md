## Context

Ver `proposal.md` — Why. A investigação sobre a watchlist atual (76 tickers) mostrou 4 Papéis com `cnpj` nulo na análise de `2026-11-12`: `BPAC11`, `CMIN3`, `MBRF3` e `CSNA3`. O `CvmPapelCnpjProvider` usa `CvmAcionistasSource.obter_cnpj`, que hoje só consulta o FCA por `Codigo_Negociacao`.

O FCA atual não traz o ticker nesses registros:

- `BPAC11` (BTG Pactual Units): `Codigo_Negociacao = 000000`
- `MBRF3` (Marfrig): `Codigo_Negociacao = ADR`
- `CMIN3` (CSN Mineração): `Codigo_Negociacao = 25585`
- `CSNA3` (CSN): `Codigo_Negociacao = 4030`

Os quatro têm `codeCVM` resolvido na B3 (`22616`, `20788`, `25585`, `4030`) e o cadastro `cad_cia_aberta.csv` da CVM mapeia `CD_CVM → CNPJ_CIA` para os CNPJs corretos. O `CvmDatasetDownloader` já suporta CSV direto (`zipado=False`), com cache condicional, hash e versão de parser.

## Goals / Non-Goals

**Goals:**
- Preencher o CNPJ fiscal dos Papéis cujo FCA não traz o ticker literal, reutilizando o `codeCVM` já resolvido/cacheado na B3.
- Manter o FCA como primeira fonte e preservar o comportamento atual para os tickers que já funcionam.
- Cachear o cadastro de companhias com hash e versão, sem novo processamento quando o arquivo não mudou.
- Manter tolerância a falhas por ticker e não impactar FIIs/BDRs.

**Non-Goals:**
- Alterar a prioridade global Fundamentus → B3 → CVM → Papel.
- Resolver CNPJ por similaridade de nome ou heurística de ticker.
- Substituir o FCA ou baixar novamente os arquivos já cacheados sem necessidade.
- Reescrever retroativamente as observações diárias já gravadas sem CNPJ.

## Decisions

### 1. Resolução em duas etapas: FCA literal e fallback por codeCVM

`CvmAcionistasSource._resolver_cnpj` continua tentando o mapa `ticker → CNPJ` do FCA. Se não encontrar, resolve o `codeCVM` via B3 e consulta o mapa `codeCVM → CNPJ` do cadastro de companhias. O FCA permanece a fonte preferencial porque cobre a maioria e não exige a resolução B3; o fallback cobre Units, ADRs e códigos numéricos.

- **Alternativa descartada**: usar apenas o cadastro por codeCVM. Aumentaria a dependência da API B3 para todos os Papéis e mudaria o comportamento de tickers que já resolvem no FCA.
- **Alternativa descartada**: casar por nome da empresa no FCA. Nomes mudam e exigiriam normalização/fuzzy matching; o `codeCVM` é um identificador estável.

### 2. Reutilização do resolvedor de codeCVM existente

Adicionar `B3FundRepository.resolver_code_cvm(ticker)` delegando ao cliente B3 já existente (`FundosCodeCvmMixin`), que usa `GetInitialCompanies` e cache de 30 dias. O `CvmAcionistasSource` recebe essa função como dependência opcional (`resolver_code_cvm`), mantendo o construtor compatível com testes e usos atuais.

- **Alternativa descartada**: instanciar um cliente B3 dentro do `CvmAcionistasSource`. Duplicaria configuração de cache/rate-limit e dificultaria testes.
- **Alternativa descartada**: resolver codeCVM via CVM. O dado já vem da B3 e é o mesmo usado na classificação/identidade.

### 3. Cadastro de companhias como CSV direto no `CvmDatasetDownloader``

Criar um downloader com `CvmDatasetDownloader(base_url=CVM_CAD_URL, arquivo=lambda _ano: "cad_cia_aberta.csv", dataset="cad", zipado=False, parser_version=PARSER_VERSION)`. O arquivo é revalidado pelo mecanismo condicional já existente e o mapa normalizado é cacheado por hash + versão, como os mapas do FRE/FCA.

- **Alternativa descartada**: baixar o CSV manualmente no `CvmAcionistasSource`. Perderia revalidação condicional, hash e versionamento já padronizados.
- **Alternativa descartada**: usar o FCA para descobrir o CNPJ por `CNPJ_Companhia` quando o `Codigo_Negociacao` é numérico. Só funcionaria para parte dos casos e não cobre `000000`/`ADR`.

### 4. Normalização de `CD_CVM` e CNPJ

O parser remove zeros à esquerda de `CD_CVM` (mesma convenção de `_normalizar_code_cvm`) e normaliza `CNPJ_CIA` para 14 dígitos. A busca usa o mesmo código normalizado, evitando divergência entre `"04030"`, `"4030"` e o valor do B3.

- **Alternativa descartada**: comparar strings cruas. O FCA/B3 e o cadastro podem divergir em zeros à esquerda.

### 5. Injeção na composição e falha tolerada

Em `montar_nucleo`, `fundamental_acionistas_provider` recebe `resolver_code_cvm=b3_fund_repository.resolver_code_cvm`. O caminho de renda fixa pode continuar sem o resolvedor; o fallback é opcional. Qualquer falha de codeCVM/cadastro retorna `None` e a análise segue.

- **Alternativa descartada**: tornar o resolvedor obrigatório. Quebraria construções/testes que não têm B3 disponível e ampliaria o acoplamento.

### 6. Fallback para o cache persistido de codeCVM

Quando a B3 falhar após as retentativas, `_identidade_empresa` passa a ler o metadado persistido da chave `codecvm_<versão>_<TICKER>` e devolver o `codeCVM`/`nome` armazenados, mesmo com TTL expirado, sem gravar novo valor. Sem metadado persistido, mantém o comportamento atual (`None` sem cache negativo). Isso evita que uma indisponibilidade transitória da B3 derrube o CNPJ de Papel quando o `codeCVM` já era conhecido.

- **Alternativa descartada**: servir cache expirado apenas se `codeCVM` não for nulo. Um `None` persistido de uma resposta válida também é informação útil e não piora o resultado; a distinção adicionaria complexidade sem ganho.
- **Alternativa descartada**: aumentar o TTL para evitar expiração. Não cobre indisponibilidade prolongada e adia a atualização do código CVM.

### 7. Razão social do Papel logo após o CNPJ

O cadastro de companhias já fornece `DENOM_SOCIAL`; o parser passa a guardar `razao_social` junto do CNPJ no mapa por `codeCVM`. `CvmAcionistasSource.obter_identidade_papel` devolve `(CNPJ, razão social)` para o `CvmPapelCnpjProvider`, que emite `CAMPO_RAZAO_SOCIAL`. A coluna `Dados fiscais` exibe `Razão social <nome>` imediatamente após `CNPJ` apenas para Papel (não FII/BDR), omitindo o item quando ausente.

- **Alternativa descartada**: usar o `nome` da tabela como razão social. É o nome de exibição/trading name (ex.: `BTGP BANCO UNT`, `CSNMINERACAO ON N2`), não a denominação social.
- **Alternativa descartada**: exibir razão social também para FIIs. O nome do fundo já aparece na coluna `Nome` e os dados fiscais de FII têm outro conjunto (CNPJ, administrador e gestor); incluir a razão social exigiria uma fonte adicional sem ganho claro.
- **Alternativa descartada**: buscar a razão social no FCA por nome. O `Nome_Empresarial` do FCA cobre o caminho literal, mas o cadastro por `codeCVM` é uniforme e cobre também os tickers não literais que motivaram a change.

### 8. Versionamento do cache do cadastro e tolerância ao formato anterior

O cache normalizado do cadastro foi gravado por uma versão anterior como `CD_CVM → string`; a versão nova espera `CD_CVM → {cnpj, razao_social}`. Sem invalidação, o CNPJ de `BPAC11`, `CMIN3`, `MBRF3` e `CSNA3` desaparecia porque `_identidade_cadastro` não reconhecia o valor string. O `PARSER_VERSION` sobe para `cvm-acionistas-v3` para forçar a reprocessar o CSV, e `_identidade_cadastro` tolera um valor string legado convertendo-o em `{cnpj, razao_social: ""}`.

- **Alternativa descartada**: manter `v2` e apenas tolerar string. O CNPJ voltaria, mas a razão social só apareceria após a expiração/manual limpeza do cache; o bump garante a reconstrução imediata.
- **Alternativa descartada**: apagar arquivos de cache manualmente. Não é uma migração reproduzível para outros usuários.

## Risks / Trade-offs

- **Cadastro da CVM muda com frequência** → revalidação condicional existente (padrão de 6h) e cache por hash; falha de rede retorna ausência sem bloquear a análise.
- **codeCVM divergente/ausente na B3** → o fallback simplesmente não é aplicado; o comportamento atual (CNPJ ausente) permanece.
- **CD_CVM duplicado no cadastro** → o parser usa a primeira ocorrência estável (`setdefault`); o registro ativo mais recente é o esperado pela CVM.
- **Aumento de uma requisição de cadastro por ano** → o downloader condicional evita downloads repetidos e o mapa normalizado evita reprocessar o CSV.
- **Observações já gravadas sem CNPJ ou sem razão social** → a correção aparece na próxima carga; não há migração retroativa.
- **Razão social ausente ou cadastro indisponível** → o CNPJ continua sendo exibido e o item de razão social é omitido, sem erro.
- **Cache normalizado em formato anterior** → a versão do parser invalida o mapa e o fallback tolera string, evitando que o CNPJ desapareça; o CSV bruto é reprocessado uma vez.
- **FCA literal sem codeCVM** → o CNPJ aparece, mas a razão social fica ausente porque o cadastro é a fonte escolhida para o nome; a decisão preserva o comportamento atual do CNPJ.

## Migration Plan

1. Publicar o código com o novo downloader e fallback; o FCA continua sendo consultado primeiro.
2. Na primeira análise de um Papel sem correspondência no FCA, resolver o `codeCVM` e baixar/reutilizar o cadastro.
3. Rollback: remover a injeção do resolvedor e o fallback; o cache do cadastro fica inerte e o FCA volta a ser a única fonte.

## Open Questions

Nenhuma.
