## Context

Ver `proposal.md - Why`. O estado atual relevante para as decisões:

- `structured_extractor.extrair_documento_provento` foi validado apenas contra fixtures sintéticas (`FLAT_HTML`, `TABLE_HTML`) que marcam o tipo com `X`. O documento real da B3 é uma tabela de duas colunas (`Rendimento | Amortização`), sem `X`, e com o rótulo `Data-base (último dia de negociação "com" direito ao provento)`. Isso faz `identificar_tipo_provento` retornar `Amortização` e `data_base` ficar `None`; `dividendos_de_proventos` descarta ambos os casos e a análise cai no `Dividendo/cota` do Fundamentus (valor único, sem data).
- O `FundamentalAnalysisUseCase` aceita `historico_dividendos: DividendHistoryProvider`, mas o controller nunca injeta um provider e não há implementação de produção — só o `Protocol`.
- `B3FundamentalRepository.obter_proventos` resolve a identidade com `typeFund="FII"`, então ações não têm histórico pela B3.
- O adapter do Fundamentus só lê o indicador `VP/Cota`; ações usam `VPA`.
- A página `proventos.php?papel={TICKER}` do Fundamentus expõe uma tabela `Data | Valor | Tipo | Data de Pagamento | ...` com histórico amplo (ex.: 477 linhas para ITUB4), já acessível pelo mesmo host/cliente do Fundamentus.

## Goals / Non-Goals

**Goals:**
- Corrigir a extração do documento FundosNet para o layout real, sem regredir os layouts já suportados.
- Preencher data-com, último/anterior e tendência para FII (B3) e Papel (Fundamentus).
- Preencher `VP/Cota` para ações via `VPA`.
- Uniformizar a formatação numérica da tabela.

**Non-Goals:**
- Não alterar a heurística de identidade B3 nem o fluxo de Informe Mensal (type=40).
- Não introduzir nova fonte de proventos de ações via API B3 de empresas listadas (o Fundamentus cobre o caso).
- Não mudar a regra de tendência (comparação direta) nem o alinhamento das colunas.

## Decisions

### 1. Corrigir o parser no ponto de extração, preservando os layouts legados

A causa é a interpretação da tabela, não a listagem. O `structured_extractor` passa a:
- reconhecer o layout de duas colunas e decidir o tipo pela coluna que contém o valor (Rendimento vs Amortização), mantendo o caminho de marcador `X` como fallback;
- extrair `Data-base` por rótulo normalizado, ignorando o texto entre parênteses.

Alternativas: criar um parser específico por versão de documento (duplica lógica); tratar no domínio após a extração (o `data_base` já se perdeu). Escolhido corrigir as estratégias existentes e cobrir com fixture real.

### 2. Fundamentus `proventos.php` como `DividendHistoryProvider` para ações

Implementar um provider que busca `proventos.php?papel={TICKER}` com o mesmo `FundamentusClient`/cache e mapeia cada linha para `DividendoConsolidado` (data-base = `Data`, valor = `Valor`, fonte `FUNDAMENTUS`), tratando `DIVIDENDO`, `DIVIDENDO MENSAL`, `JRS CAP PROPRIO` e `JUROS` como rendimento.

Alternativas: endpoint de proventos de empresas listadas da B3 (exigiria reconciliar contrato e novo host); reusar apenas o `Dividendo/cota` do detalhes (já existe, mas é valor único sem data — não resolve o problema). O Fundamentus é a opção com menor custo e maior cobertura para Papel, e serve de fallback para FII.

### 3. Injeção de `historico_dividendos` no wiring, mantendo B3 como primária

No `controller.py`, passar o provider de proventos do Fundamentus como `historico_dividendos`. Em `_ultimo_dividendo`, a B3 continua primária; o histórico secundário complementa e preenche ações. A consolidação já existe (`consolidar_dividendos`) e preserva a origem; nenhuma mudança de regra é necessária.

Alternativa: tornar o Fundamentus primário — contraria a spec `dividend-metrics` (B3 primária) e o custo de rede por ticker.

### 4. `VPA` como fallback de `vp_cota` no adapter

No `campos_do_ativo`, usar `VP/Cota` e, quando ausente, `VPA`. É a menor mudança que preenche a coluna para Papel sem afetar FIIs.

### 5. Formatação fixa em 2 casas na apresentação

Fixar `formatar_valor` em 2 casas e o payout em 2 casas. A função `formatar_valor` é usada exatamente pelas 4 colunas-alvo; `formatar_ratio` e `formatar_percentual` (Demais colunas) permanecem inalterados.

Alternativa: um formatador por coluna — mais flexível, porém desnecessário no escopo.

## Risks / Trade-offs

- **[Risco] Regex frágil no documento B3 real** → Fixture real + teste de contrato; o caminho de marcador `X` permanece como fallback.
- **[Risco] `proventos.php` mudar de layout ou bloquear scraping** → Parser orientado a cabeçalhos (`Data`, `Valor`, `Tipo`), tolerante a linhas vazias, com cache e tratamento de falha distinto de lista vazia.
- **[Trade-off] "Último dividendo" de FII passa a ser o rendimento mensal mais recente (ex.: 0,91) em vez do valor agregado do Fundamentus** → Mais correto e datado; muda a leitura, por isso marcado como BREAKING.
- **[Trade-off] 2 casas decimais podem arredondar rendimentos fracionários (< 0,10)** → Aceito conforme pedido; `N/A` e valores normais não são afetados.
- **[Risco] Custo de rede extra por ticker no histórico do Fundamentus** → Cache por ticker com TTL, reutilizando o `CacheManager` já existente.

## Migration Plan

1. Corrigir o parser B3 e adicionar a fixture real (sem tocar no wiring).
2. Adicionar o provider de proventos do Fundamentus e o fallback de `VPA`.
3. Injetar `historico_dividendos` no controller e validar o preenchimento de Papel/FII.
4. Ajustar a formatação da tabela e os testes.
5. Rollback: o wiring é reversível (basta não injetar o provider); a formatação é isolada na apresentação.

## Open Questions

- Nenhuma pendente que altere specs, abordagem ou tarefas.
