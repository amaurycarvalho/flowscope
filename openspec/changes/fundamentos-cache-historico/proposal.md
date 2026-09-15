## Why

Hoje a sub-aba "Fundamentos" recalcula a análise completa (Fundamentus, B3, CVM, FFO, preço) sempre que o usuário recarrega a mesma data, e os resultados só existem em memória durante a sessão. Como o resultado por ticker é estável dentro do mesmo dia, isso desperdiça tempo e rede, e não deixa nenhum registro histórico. Persistir o conteúdo da linha por `(ticker, data)` acelera recargas e habilita, no futuro, consultas da evolução do ticker.

## What Changes

- Introduzir um cache estruturado do resultado da análise fundamentalista (o conteúdo da linha da tabela "Fundamentos"), chaveado por `(ticker, data escolhida na GUI)`, com a `data_referencia` guardada dentro do registro.
- Persistir o `AnaliseFundamental` estruturado (não os valores formatados), com `schema_version` por observação, em um arquivo JSON por ticker contendo um mapa `data -> observação`.
- Reter um histórico deslizante de 365 dias, com prune na escrita e observações expiradas ignoradas na leitura.
- Integrar o cache como read-through no `FundamentalAnalysisUseCase`: em HIT, pular todo o pipeline de aquisição; em MISS, executar o caminho atual e registrar.
- Nunca gravar observações com `erro`; observações parciais (sem identidade do Fundamentus) podem ser sobrescritas no mesmo dia; observações completas são imutáveis no dia (first-write-wins).
- Tornar a leitura estrita para o HIT do dia (exige `schema_version` atual) e tolerante para consultas de histórico (best-effort, marcando a versão).
- Expor uma porta de recuperação (`obter`, `historico`, `datas`, `registrar`) para as futuras consultas de evolução do ticker.
- Ligar o cache por padrão e oferecer um caminho explícito de bypass para forçar recomputo e sobrescrever a observação do mesmo dia.
- Aplicar a todos os tickers (FII e Papel).

## Capabilities

### New Capabilities

- `fundamental-history-cache`: cache estruturado e histórico por `(ticker, data)` do resultado da análise fundamentalista, com read-through, retenção de 365 dias, versionamento por observação, política de falhas/parcialidade e porta de recuperação histórica.

### Modified Capabilities

- `gui-interface`: comportamento da sub-aba "Fundamentos" passa a reutilizar o cache histórico para a mesma `(ticker, data)` e a oferecer um caminho de bypass para forçar recomputo no mesmo dia.

## Impact

- **Código**: novo módulo de infraestrutura do store histórico; serializador de `AnaliseFundamental`; porta em `application`; integração read-through em `application/fundamental_analysis.py`; wiring no controlador/`controller_fundamental.py`; bypass na GUI.
- **Dados**: novo diretório `~/.cache/flowscope/fundamentos/{TICKER}.json`; até 365 observações por ticker.
- **Dependências/APIs**: nenhuma dependência nova; reutiliza as primitivas de escrita atômica do `CacheManager`.
- **Compatibilidade**: o read-through preserva o resultado atual; sem store configurado, o comportamento é o de hoje. A porta é aditiva.
