## 1. Domínio: métricas e classificações

- [ ] 1.1 Adicionar `ClasseShorts` e `ClasseRiscoFechamento` (cinco rótulos cada) e as funções `classificar_volume_shorts` e `classificar_risco_fechamento` em `domain/fii/classification_faixas.py`, seguindo o padrão de `classificar_cotistas`; verificar com teste unitário dos limites (0, 5, 10, 20 para Shorts%; 0, 2, 4, 5 para SIR)
- [ ] 1.2 Adicionar as funções puras `shorts_percent(acoes_alugadas, denominador)` e `short_interest_ratio(acoes_alugadas, volume_medio)` em `domain/fii/metrics.py`, com `N/A` (retorno `None`) para insumo ausente ou denominador zero; verificar com teste unitário incluindo o caso de denominador zero
- [ ] 1.3 Adicionar o value object `MetricasShort` (Shorts%, Volume de Shorts, SIR, Risco Fechamento) e o campo `short` em `AnaliseFundamental` (`domain/fii/analysis.py`); verificar com teste de construção do dataclass e import via `flowscope.domain.fii`

## 2. Apresentação: colunas, rótulos e orientação

- [ ] 2.1 Inserir as quatro colunas em `_COLUNAS` (`charts/fundamental_rows.py`) imediatamente após `tendencia_dividendo` e antes de `ffo_receita_12m`, e adicionar `shorts_pct`/`sir` a `_COLUNAS_DIREITA`; verificar com teste da ordem dos cabeçalhos e do CSV
- [ ] 2.2 Estender `_linha_analise` para preencher as quatro posições, usando os formatadores de percentual/razão e o mapa de rótulos; verificar com teste que uma análise com métricas produz as células esperadas e que ausência produz `N/A`
- [ ] 2.3 Adicionar o mapa de rótulos (`Inexistente`, `Muito Baixo`, `Baixo`, `Alto`, `Muito Alto`) em `charts/fundamental_formatters.py`; verificar com teste dos cinco rótulos e de `N/A`
- [ ] 2.4 Atualizar o texto do OrientationPanel da sub-aba "Fundamentos" (`presentation/gui/app_tabs.py`) e `panels.md` descrevendo as colunas de short interest e como interpretá-las; verificar com teste do conteúdo de orientação e conferência visual do texto
- [ ] 2.5 Conferir a largura/rolagem horizontal da tabela com as 34 colunas (30 → 34) e ajustar larguras iniciais se necessário; verificar abrindo a sub-aba "Fundamentos" com display disponível

## 3. Cache histórico: persistência dos novos campos

- [ ] 3.1 Serializar e desserializar os campos de short interest em `infrastructure/fii/fundamental_analysis_codec.py` e subir `SCHEMA_VERSION_FUNDAMENTOS` de `1` para `2` em `application/fundamental_ports.py`; verificar com teste de round-trip do codec e de que uma observação de schema `1` não é servida como acerto do dia

## 4. Free float via CVM FRE

- [ ] 4.1 Estender o parser do `CvmAcionistasSource` (`infrastructure/cvm/acionistas.py`) para extrair `Quantidade_Total_Acoes_Circulacao` do CSV `fre_cia_aberta_distribuicao_capital`, chaveado por CNPJ, e subir `PARSER_VERSION`; verificar com teste unitário do parser sobre uma amostra do CSV
- [ ] 4.2 Expor o free float por uma porta (`FreeFloatProvider` ou extensão de `AcionistasProvider`) e resolver em `application/fundamental_providers.py`, com fallback para `cotas_emitidas`; verificar com teste de integração do caso de uso cobrindo free float presente e ausente

## 5. Ações alugadas via B3 (empréstimos)

- [ ] 5.1 Spike de aquisição: capturar o POST do formulário Lumis de "Posições em Aberto de Empréstimo de Ativos", o `fileId` retornado e o download via `fileDownload.jsp`, e documentar os campos/cookies no adapter; verificar baixando o arquivo de uma data e registrando o resultado no teste do adapter
- [ ] 5.2 Implementar o adapter B3 de empréstimos (sessão HTTP, POST, `fileId`, download, parse do estoque por ticker) com cache diário e falha tolerada (`None`); verificar com teste unitário do parser sobre uma amostra e teste de falha de rede retornando `None`
- [ ] 5.3 Adicionar a porta `ShortInterestProvider` e resolver as ações alugadas em `application/fundamental_analysis.py`, isolando falha por ticker; verificar com teste de integração cobrindo sucesso, ausência e exceção da fonte

## 6. Volume/SIR e integração final

- [ ] 6.1 Calcular o volume médio diário a partir do `daily_data` em memória (`fin_instr_qty`) e alimentar o `SIR`, com `N/A` sem dias; verificar com teste do caso de uso cobrindo dias presentes, ausentes e volume zero
- [ ] 6.2 Integrar as quatro métricas ao resultado da análise (Papel com free float, FII com total de cotas) e garantir que a ausência de um insumo não afeta as demais colunas; verificar com teste de integração por tipo de ativo

## 7. Validação e documentação

- [ ] 7.1 Cobrir com testes os cenários dos specs `short-interest` e `gui-interface` (limites de classificação, `N/A`, ordem e alinhamento das colunas) e garantir cobertura ≥ 85%; verificar com `python -m pytest tests/ --cov`
- [ ] 7.2 Atualizar a documentação de painéis (`panels.md`) e conferir a consistência com o OrientationPanel; verificar por inspeção do texto final
- [ ] 7.3 Rodar `make lint complexity` e corrigir pendências.
