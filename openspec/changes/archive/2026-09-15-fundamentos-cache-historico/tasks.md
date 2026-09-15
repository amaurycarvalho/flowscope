## 1. Serialização estruturada

- [x] 1.1 Definir a constante de versão do schema da análise fundamentalista (`SCHEMA_VERSION_FUNDAMENTOS`) e o serializador `AnaliseFundamental` ↔ `dict` (`Decimal` como string, `date` em ISO, enums pelo valor, dataclasses aninhadas e `indexadores`); verificar com teste de round-trip cobrindo todos os tipos de campo
- [x] 1.2 Garantir que o `dict` serializado inclui a versão do schema e a `data_referencia`; verificar com teste que lê a versão de um registro gravado

## 2. Porta e store histórico

- [x] 2.1 Adicionar a porta `FundamentalHistoryStore` (`obter`, `historico`, `datas`, `registrar`) em `application/fundamental_ports.py`; verificar que a suíte de portas continua passando
- [x] 2.2 Implementar o store em infraestrutura com um JSON por ticker em `~/.cache/flowscope/fundamentos/{TICKER}.json` (mapa `data -> observação`), escrita atômica (tmp + rename), prune de 365 dias na escrita e tolerância a corrupção; verificar com testes de persistência
- [x] 2.3 Implementar a leitura com HIT estrito por versão, histórico best-effort identificando a versão e descarte de observações expiradas; verificar com testes de versionamento e expiração
- [x] 2.4 Verificar recuperação por data específica, lista de datas e intervalo sem tocar as fontes; verificar com testes do store (`obter`, `datas`, `historico`)

## 3. Read-through no caso de uso

- [x] 3.1 Injetar o store opcional no `FundamentalAnalysisUseCase` e consultar `obter` antes de `_analisar_ticker`, servindo o HIT sem executar o pipeline; verificar com teste que o provider não é chamado em HIT
- [x] 3.2 Registrar a observação no MISS apenas quando `analise.erro is None`; verificar que linhas com erro não são gravadas
- [x] 3.3 Implementar a política de parcialidade: observação parcial (sem identidade do Fundamentus) sobrescrevível no mesmo dia; completa imutável no dia; verificar com testes dos dois casos
- [x] 3.4 Implementar o bypass `force_refresh` no `execute`, ignorando o HIT e sobrescrevendo a observação do dia inclusive quando completa; verificar com teste de atualização forçada
- [x] 3.5 Verificar que os resultados em memória não vazam entre datas e que a troca de data usa apenas observações da data corrente; verificar com teste de troca de data

## 4. Wiring da interface

- [x] 4.1 Instanciar o store e injetá-lo no `FundamentalAnalysisUseCase` no wiring do controlador, ligado por padrão; verificar que a carga de fundamentos continua populando a tabela
- [x] 4.2 Expor a ação de atualização forçada como botão da barra da lista de tickers (ícone `edit-redo.png`, tooltip "Atualizar fundamentos", após "Desmarcar Todos"), visível apenas na sub-aba "Fundamentos" e desabilitado durante a carga, chamando o `execute` com bypass e repopulando a tabela; verificar com teste de presenter/GUI da ação
- [x] 4.3 Verificar que recarregar a mesma data reutiliza o cache histórico e não refaz aquisição; verificar com teste de recarga da mesma data
- [x] 4.4 Adicionar tooltips descritivos aos botões de índice IBOV/IDIV/IFIX com apenas a descrição do índice; verificar com teste dos tooltips

## 5. Documentação e verificação integrada

- [x] 5.1 Atualizar o `CHANGELOG.md` com o cache histórico de Fundamentos e o bypass
- [x] 5.2 Executar `make lint` e `make test` e confirmar que passam sem regressões
- [x] 5.3 Validar a change com `openspec validate fundamentos-cache-historico` e confirmar que não há erros (avisos de RFC 2119 são esperados, pois as specs do projeto usam `DEVE`)
