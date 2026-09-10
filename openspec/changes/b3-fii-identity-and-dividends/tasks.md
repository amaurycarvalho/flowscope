## 1. Reconciliação de contrato B3

- [ ] 1.1 Gravar/atualizar fixtures de contrato da B3 (`fund_alzr.json`, `distributions_alzr.json`) em `tests/fixtures/b3/` e verificar que os testes de contrato leem os arquivos sem depender de rede
- [ ] 1.2 Escrever teste de contrato que confirma as chaves de data (`dataInicial`/`dataFinal` vs `dateInitial`/`dateFinal`) e a URL de download de documento (`exibirDocumento` vs `visualizarDocumento`) e verificar que o teste passa contra o comportamento real
- [ ] 1.3 Ajustar `funds_client.py` para usar a heurística de resolução por `idMain` da RFC-008 e verificar que os testes de resolução continuam passando

## 2. Encoder, retry e rate-limit

- [ ] 2.1 Extrair `encode_b3_payload` para `infrastructure/b3/encoder.py` e reutilizá-lo no cliente, verificando que os testes de token existentes continuam passando
- [ ] 2.2 Implementar retry com espera crescente que repete apenas erros transitórios e não repete HTTP 400/404, verificando com teste que simula falha e sucesso
- [ ] 2.3 Implementar serialização de requisições por host (máximo uma por vez), verificando com teste que não há chamadas concorrentes ao mesmo host

## 3. Modelos e repositórios de aquisição B3

- [ ] 3.1 Criar os modelos `B3Fund`, `B3ReportReference`, `AcquisitionMetadata` e `AcquisitionResult` em `domain/b3/`, verificando que distinguem lista vazia de falha por teste unitário
- [ ] 3.2 Implementar `fund_repository.find_by_ticker` retornando `B3Fund | None`, verificando com teste de fixture ALZR (`idFNET=20294`) e de ticker sem dados
- [ ] 3.3 Implementar `reports_repository.get_distributions` (type 41, paginado) e verificar com testes de página única e múltiplas páginas
- [ ] 3.4 Reutilizar `structured_extractor` para extrair `DocumentoProvento` dos documentos listados, verificando com teste de documento completo e de documento sem provento
- [ ] 3.5 Preservar resposta bruta e metadados de aquisição e verificar que o resultado registra `errors` em falha de listagem (não lista vazia)

## 4. Adaptador fundamentalista e Dividend Yield

- [ ] 4.1 Implementar `FiiFundamentalRepository` apoiado na camada B3 (nome e proventos), verificando com teste que resolve nome e proventos do ALZR
- [ ] 4.2 Desacoplar o Dividend Yield no `FundamentalAnalysisUseCase` (`dividendos_12m_por_cota / preço`), verificando que DY é preenchido mesmo sem NAV/FFO e que as colunas de FFO/NAV permanecem `N/A`
- [ ] 4.3 Cobrir com testes de caso de uso a isolamento de falha por ticker e a ausência de dados B3

## 5. Execução em background e wiring da GUI

- [ ] 5.1 Adicionar progress callback ao `FundamentalAnalysisUseCase` e verificar que reporta etapas por ticker
- [ ] 5.2 Implementar o worker em thread com fila e consumo via `after`, verificando que nenhum widget é tocado fora da thread do Tk
- [ ] 5.3 Instanciar repositório B3, `B3MarketPricePort` e `FundamentalAnalysisUseCase` no wiring (`app.py`/`controller.py`) e disparar a análise após cada carga
- [ ] 5.4 Implementar o token de geração e verificar por teste que resultados de carga anterior são descartados
- [ ] 5.5 Atualizar `_do_update`/`_on_tab_changed` para passar as análises ao `FundamentalTablePanel` e verificar que a sub-aba exibe as linhas reais sem reexecutar aquisição

## 6. Verificação integrada

- [ ] 6.1 Executar `pytest` e verificar que todos os testes passam
- [ ] 6.2 Executar `ruff check` e o gate de qualidade configurado no projeto e verificar que não há violações
- [ ] 6.3 Validar a change com `openspec validate "b3-fii-identity-and-dividends"` e verificar que é válida
