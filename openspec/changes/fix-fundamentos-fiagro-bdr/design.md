## Context

Ver `proposal.md - Why`. A sub-aba Fundamentos é alimentada por `FundamentalAnalysisUseCase`, que compõe fontes via `CompositeFundamentalProvider` (Fundamentus → B3 → CVM) e resolve dividendos por B3/Fundamentus. A investigação confirmou empiricamente:

- FIAGROs não estão em `GetListFunds(typeFund="FII")`; a B3 os expõe em `typeFund="FIAGRO"` (49 fundos). `GetListClassFund(typeFund="FIAGRO")` devolve a classe com `idMain` e `tradingName` com CNPJ de 14 dígitos; `GetStructuredReports` funciona com o `idFNET` da classe independentemente de `typeFund`.
- FIIs/FIAGROs têm histórico em `fii_proventos.php` (colunas `Última Data Com`/`Tipo`/`Data de Pagamento`/`Valor`), enquanto o provider atual lê `proventos.php` (ações), retornando vazio.
- BDRs não têm página no Fundamentus (`LayoutChanged`) nem identidade de fundo. O Plantão de Notícias lista `Aviso aos Acionistas` mês a mês; a página `Detail` aponta para o documento no visualizador da CVM; o PDF é obtido por POST `frmExibirArquivoIPEExterno.aspx/ExibirPDF` retornando JSON `{"d": "<base64>"}` (captcha desabilitado hoje). O texto usa fontes embutidas com `/ToUnicode`, exigindo biblioteca de extração.

## Goals / Non-Goals

**Goals:**
- Preencher os campos hoje vazios de FIAGROs (cotistas, indexadores, dados fiscais, data-com, dividendo anterior, tendência, P/L) reaproveitando a cadeia B3/CVM existente.
- Preencher dividendos de BDRs (data-com, último/anterior, tendência, P/L e Dividend Yield com anualização trimestral) sem introduzir dependência de scraping de terceiros (statusinvest/brapi/yfinance).
- Expor o caminho do cache de PDFs e a identidade fiscal (depositário, empresa, ISIN) de BDRs na tabela.

**Non-Goals:**
- Fundamentos de valuation de BDRs (P/VP, VP/Cota, FFO) — não há fonte integrada; permanecem `N/A`.
- OCR de PDFs escaneados.
- Adicionar yfinance/brapi/statusinvest.
- Generalizar a anualização de dividendos de BDR por inferência de frequência; fica fixa em trimestral (×4).

## Decisions

### 1. Resolução B3 multi-tipo em vez de taxonomia FIAGRO estática

**Decisão**: `B3FundRepository`/`FundosListagemMixin` iteram `typeFund` em `("FII", "FIAGRO", "FIP", "FIDC")`, reutilizando `GetListFunds`/`GetListClassFund` e o cache por tipo.

**Alternativas**: (a) manter uma taxonomia estática de FIAGROs (frágil, 49 tickers e cresce); (b) consultar apenas `FIAGRO` quando o tipo `FII` falha e o ticker não é ETF (mais requisições, mesma cobertura). A iteração com cache por tipo é determinística e desbloqueia toda a cadeia CVM via `resolver_identidade` (CNPJ do `tradingName`).

### 2. Classificação FIAGRO derivada da resolução B3

**Decisão**: a classificação determinística de fallback reconhece FIAGRO consultando a mesma resolução de fundo (tipo `FIAGRO`) e retorna `FII` + `SubTipoFii.FIAGRO`. O `SubTipoFii.FIAGRO` já existe no domínio.

**Alternativas**: estender `TAXONOMIA_FII_PADRAO` (não cobre FIAGRO) ou inferir por nome (proibido pela spec de classificação). Derivar da B3 mantém o determinismo e evita manutenção manual.

**Impacto**: `elegivel_ffo()` retorna `False` para `FIAGRO`, mantendo-os fora do motor FFO (são fundos de crédito).

### 3. Parser de `fii_proventos.php` com fallback em cascata

**Decisão**: o client ganha a URL de rendimentos de FII e o parser uma função dedicada à tabela de FII. O provider de histórico tenta `proventos.php` e, se vazio, `fii_proventos.php`; ambos cacheados por ticker/TTL de 1 dia.

**Alternativas**: detectar o tipo pelo sufixo do ticker (impreciso para ETFs/unidades). A tentativa em cascata é robusta e cobre também FIIs clássicos.

### 4. Dividendos de BDR via Plantão de Notícias + PDF da CVM

**Decisão**: novo módulo `infrastructure/b3/bdr/` com três etapas: (a) listagem mês a mês no `ListarTitulosNoticias` filtrando `({RAIZ})` + `Aviso aos Acionistas`; (b) resolução do documento em `Detail?idNoticia=...` e download via POST `ExibirPDF` (base64 → `%PDF`); (c) extração de texto com `pypdf` e parsing de valor por BDR, data-com, data de pagamento, tipo, ISIN, depositário e empresa.

**Alternativas**: statusinvest (HTTP 403 Cloudflare), brapi (token + fundamental PRO pago), yfinance (dependência pesada e não-oficial). A via B3/CVM é a única sem custo e sem scraping de terceiros, alinhada ao padrão do projeto (B3 + CVM + Fundamentus).

**Anualização**: fixa em trimestral (×4) para BDR, conforme decisão do usuário; não reutiliza a convenção mensal (×12) de FII.

### 5. Cache de PDFs em árvore por ticker/ano/mês

**Decisão**: `<cache_dir>/bdr/<TICKER>/<AAAA>/<MM>/<id>.pdf`, sem TTL (documentos históricos não mudam). Reutiliza `CacheManager.get_cache_dir()` como raiz. O caminho da pasta do ticker é exposto em `Informações adicionais`.

**Alternativas**: cache JSON do `CacheManager` (não comporta binário grande); nome achatado `bdr_{id}.pdf` (perde a organização pedida). A árvore por ticker/ano/mês atende ao requisito e facilita inspeção manual.

### 6. `pypdf` como dependência

**Decisão**: adicionar `pypdf>=4` (pura Python) para extrair texto dos PDFs. O texto usa `/ToUnicode`; extração manual (zlib + operadores) se mostrou inviável.

**Alternativas**: `pdfminer.six`/`pdfplumber` (mais pesados); `PyPDF2` (legado, já citado em outra change, mas o projeto não o tem instalado). `pypdf` é o sucessor direto e leve.

### 7. Campos de BDR no modelo e na apresentação

**Decisão**: estender `AnaliseFundamental` com `bdr_cache_path`, `nome_depositario`, `nome_empresa_bdr` e `isin`, preenchidos apenas para BDR. Em `fundamental_rows`, `Informações adicionais` exibe o caminho de cache e `Dados fiscais` exibe depositário/empresa/ISIN quando não houver CNPJ/administrador/gestor.

**Alternativas**: reaproveitar `indexadores` para carregar texto (semântica errada). Campos explícitos mantêm o modelo legível e testável.

## Risks / Trade-offs

- **[Risco] `ExibirPDF` passar a exigir captcha (`hdnHabilitaCaptcha=S`)** → Mitigação: cache de PDFs em disco; falha isolada por aviso/ticker; o restante dos dados continua.
- **[Risco] `pypdf` não extrair texto de PDFs com encoding atípico** → Mitigação: retornar vazio e ignorar o aviso; log de warning; testes de contrato com PDF fixture.
- **[Risco] `ListarTitulosNoticias` retornar vazio para janelas longas** → Mitigação: consulta obrigatoriamente mês a mês (comportamento já exigido na spec).
- **[Trade-off] Anualização fixa ×4** → BDRs com frequência diferente terão P/L e DY aproximados; aceitável conforme decisão do usuário e documentado na spec.
- **[Risco] Aumento de requisições B3 na resolução multi-tipo** → Mitigação: cache por tipo (30 dias) e ordem de tentativa com `FII` primeiro.
- **[Trade-off] FIAGROs permanecem inelegíveis ao FFO** → Correto para fundos de crédito; o Fundamentus já fornece FFO/Receita para eles.

## Migration Plan

1. Adicionar `pypdf` às dependências e instalar no ambiente.
2. Implementar resolução multi-tipo e classificação FIAGRO (sem migração de dados; caches antigos de `typeFund="FII"` são reaproveitados, os de FIAGRO são criados na primeira execução).
3. Implementar `fii_proventos.php` e o provider de BDR.
4. Expor os novos campos na tabela.
5. Rollback: as mudanças são aditivas e isoladas por tipo de ativo; reverter o módulo BDR e a iteração de `typeFund` restaura o comportamento anterior.

## Open Questions

- Nenhuma pendente que afete specs, abordagem ou tarefas. A frequência de anualização foi fixada em trimestral (×4) por decisão do usuário.
