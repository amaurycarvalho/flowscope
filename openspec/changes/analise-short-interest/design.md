## Context

A análise fundamentalista já orquestra, por ticker, identidade → dividendos → métricas FFO, com portas desacopladas (`FundamentalDataProvider`, `FfoProvider`, `MarketPricePort`, etc.) e um cache histórico versionado por `(ticker, data)` (`fundamental-history-cache`). O pipeline injeta o `daily_data` por ticker no caso de uso (`controller_fundamental.py`), onde cada `TradeDay` traz `fin_instr_qty` (quantidade negociada em ações). Ver `proposal.md` para a motivação e os specs `short-interest` e `gui-interface` para os requisitos.

Spikes já realizados (read-only):

- O CSV `fre_cia_aberta_distribuicao_capital` do CVM FRE — já baixado e parseado pelo `CvmAcionistasSource` — contém `Quantidade_Total_Acoes_Circulacao` e `Percentual_Total_Acoes_Circulacao` (free float).
- A B3 publica o estoque diário de **empréstimo de ativos (BTC)** no **BDI**: capítulo "Empréstimos de ativos", tabela `BTBLendingOpenPosition` ("Posições em aberto", retenção `D-21`), servida por `POST` JSON em `/bdi/table/BTBLendingOpenPosition/{data}/{data}/{página}/{take}`. Cada linha traz `TckrSymb`, `Market` e `StockBalance` (saldo em quantidade do ativo), com uma linha `Total` por ticker.
- A página "Posições em Aberto" do mercado **Termo** (`.../mercado-a-vista/termo/posicoes-em-aberto/`) foi um falso positivo do spike inicial: os códigos terminam em `T` e o dado é de contratos a termo, não de empréstimos. Foi descartada.
- O endpoint `requestname` usado para `TradeInformationConsolidated` **não** serve empréstimos (`ConsolidatedLending` retorna 400); o portal de arquivos (`arquivos.b3.com.br/api`) não tem canal de empréstimos. O endpoint `requestname` continua funcional para as negociações, então o pipeline atual de preço/volume não é afetado.

## Goals / Non-Goals

**Goals:**

- Calcular `Shorts%` e `SIR` como funções puras em `Decimal`, com classificações determinísticas, seguindo o padrão de `classification_faixas.py`.
- Obter o *free float* do CVM FRE reutilizando o arquivo e o cache já existentes, com fallback para o total emitido.
- Obter as ações alugadas da B3 com um adapter tolerante a falhas, sem acoplar a análise ao sucesso da fonte.
- Exibir as quatro colunas no ponto definido e atualizar a orientação da sub-aba.
- Persistir os novos campos no cache histórico com bump de schema.

**Non-Goals:**

- Integração FINRA para BDRs (mapeamento BDR→símbolo US, free float da empresa estrangeira, licenciamento).
- Coleta histórica retroativa além da janela de ~3 meses da B3.
- Ajuste de free float em eventos corporativos em tempo real.

## Decisions

### Nova capability `short-interest` em vez de estender `fii-fundamental-metrics`

As métricas valem para `Papel` e `FII`, não só FIIs. `fii-fundamental-metrics` é específica de FIIs; criar `short-interest` mantém o contrato correto e evita diluir o escopo daquela capability. Alternativa descartada: adicionar a `fii-fundamental-metrics` (misturaria domínios e confundiria o escopo de "não elegível").

### Free float do CVM FRE, com `Quantidade_Total_Acoes_Circulacao` como denominador

Estender o `CvmAcionistasSource` para também extrair `Quantidade_Total_Acoes_Circulacao`, chaveado por CNPJ, reaproveitando download, cache por hash e seleção de versão. Usar a **quantidade em ações**, não o percentual, para manter a mesma unidade do numerador (ações alugadas). Bump de `PARSER_VERSION` invalida o cache normalizado. Alternativa descartada: buscar free float na B3 ("Empresas Listadas" é canal pago).

### Fallback de denominador para o total emitido

Quando o ticker não tem *free float* no FRE, o denominador é `cotas_emitidas` (Fundamentus), já disponível na análise. Isso preserva a métrica para FIIs (sem free float) e para Papéis sem FRE, ao custo de superestimar a magnitude relativa. Alternativa descartada: exibir `N/A` para todo ticker sem free float (perderia a métrica para FIIs, que têm empréstimos na B3).

### Ações alugadas via adapter B3 dedicado, com spike de aquisição

Um novo adapter encapsula a aquisição da tabela **`BTBLendingOpenPosition`** do BDI (`POST` JSON paginado, `take` de 1000), com sessão HTTP, agregação por ticker (linha `Total`), cache diário e tolerância a falha (retorna `None` → `N/A`). O ticker é o próprio `TckrSymb`; o saldo é o `StockBalance`.

A página de "Posições em Aberto" do mercado Termo, cogitada na primeira versão da change, foi descartada por não ser empréstimo de ativos; seus valores (muito menores) não representam o estoque de empréstimos. Alternativa descartada: usar o canal pago UP2DATA.

Como a B3 publica a posição do **pregão anterior**, uma data ainda não publicada (tipicamente a data corrente) recua até a data disponível mais recente dentro de uma janela de 7 dias, evitando `N/A` quando há estoque publicado recentemente. Além da janela, o resultado é `N/A`, conforme o spec.

### Volume médio diário a partir do `daily_data` em memória

Reutilizar `TradeDay.fin_instr_qty` do mesmo `daily_data` já injetado, sem nova porta. O volume médio é a média dos dias disponíveis; `N/A` sem dias. Alternativa descartada: criar uma porta de volume com download próprio (duplicaria a aquisição já existente).

### Classificações determinísticas reutilizando o padrão existente

Novos enums `ClasseShorts` e `ClasseRiscoFechamento` e funções `classificar_*` em `classification_faixas.py`, com os cinco rótulos e faixas da RFC-014:

- `Volume de Shorts` (Shorts%): `Inexistente` (0% ou `N/A`), `Muito Baixo` (>0% e <1%), `Baixo` (≥1% e <3%), `Alto` (≥3% e ≤10%), `Muito Alto` (>10%).
- `Risco Fechamento` (SIR): `Inexistente` (0 ou `N/A`), `Muito Baixo` (<2), `Baixo` (<4), `Alto` (≤5), `Muito Alto` (>5).

`0` e `N/A` classificam como `Inexistente` (as colunas numéricas `Shorts%`/`Fechamento Shorts` seguem `N/A`). `Fechamento Shorts` é exibido em dias, com uma casa decimal e sufixo `d`. Alternativa descartada: reutilizar `TendenciaFfo` (semântica incompatível).

### Persistência no cache histórico com bump de schema

Adicionar os campos estruturados a `AnaliseFundamental` e ao codec, subindo `SCHEMA_VERSION_FUNDAMENTOS` de `1` para `2`. O mecanismo de acerto do dia exige a versão atual, forçando recomputo das observações antigas (comportamento já especificado em `fundamental-history-cache`).

### Posição e alinhamento das colunas

Inserir as quatro colunas em `_COLUNAS` imediatamente após `tendencia_dividendo`; `Shorts%` e `Fechamento Shorts` entram em `_COLUNAS_DIREITA` (numéricas) e `Volume de Shorts`/`Risco Fechamento` ficam à esquerda (categóricas). `_linha_sintetica` se autoajusta por `len(_COLUNAS)`.

## Risks / Trade-offs

- **Disponibilidade do endpoint BDI da B3** (`POST /bdi/table/BTBLendingOpenPosition/...`) → adapter com cache diário e falha tolerada (`N/A`); nunca bloquear a análise.
- **Retenção `D-21` e publicação do pregão anterior** → a data corrente recua para a data publicada mais recente dentro de uma janela de 7 dias; além da janela, `N/A`.
- **Defasagem do free float do FRE** (periódico, por versão) → documentar; usar a quantidade em ações e o fallback de total emitido.
- **Janela de volume variável** (depende do range carregado, não garante 20–30 dias) → média dos dias disponíveis e `N/A` sem dias; registrar a limitação na orientação.
- **Denominador de FII = total de cotas** (não é free float) → o spec explicita que FIIs usam o total de cotas; leitura deve ser interpretada como piso conservador.
- **Largura da tabela** (30 → 34 colunas, 28 → 32 roláveis) → conferir largura mínima e rolagem horizontal; sem mudança estrutural no congelamento.
- **Alternativa fora do escopo**: o BDI também publica o conteúdo "Empréstimos de Ativos – Posição em aberto (BDI)" (com variante em PDF no boletim diário); registrado como contingência/uso manual, não implementado.

## Migration Plan

1. Fase 1 — domínio + apresentação + cache: funções, enums, colunas, formatadores, codec e bump de schema. Entrega as colunas com `N/A` enquanto não há fonte.
2. Fase 2 — free float via CVM FRE (extensão do `CvmAcionistasSource`).
3. Fase 3 — spike de aquisição + adapter B3 de empréstimos.
4. Fase 4 — volume/SIR pelo `daily_data` em memória (se ainda não coberto na Fase 1).

Rollback: reverter a versão de schema e a ordem das colunas é suficiente; não há migração de dados destrutiva (observações de schema antigo são recomputadas).

## Open Questions

- Mecanismo exato de aquisição do empréstimo de ativos — **resolvido no spike da Fase 3**: a fonte é a tabela `BTBLendingOpenPosition` do BDI (`POST /bdi/table/BTBLendingOpenPosition/{data}/{data}/{página}/{take}`), com agregação pela linha `Total`. A página do mercado Termo foi descartada por não representar o estoque de empréstimos.
- Cobertura de empréstimos para `ETF`/`FIAGRO` (se ausente, cai em `N/A`, já previsto).
