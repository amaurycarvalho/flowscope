## 1. Modelo e normalizadores

- [ ] 1.1 Criar o modelo `AtivoFundamental` (Decimal/date, campos opcionais, mapa bruto) em `domain/fii/` e verificar com teste unitário
- [ ] 1.2 Implementar normalizadores de número/percentual/data no formato brasileiro e verificar com testes de `R$ 691.996.000.000`, `-0,08%` e célula vazia
- [ ] 1.3 Verificar que campos ausentes retornam `None` sem impedir o restante do modelo

## 2. Fetch, parser e fixtures

- [ ] 2.1 Implementar o fetch de `detalhes.php?papel={TICKER}` com rate-limit de 1 req/s e respeito ao `robots.txt` e verificar com teste de serialização
- [ ] 2.2 Implementar o parser de cabeçalho, oscilações, indicadores, balanço e demonstrativos (12m/3m) e verificar com fixture de ação
- [ ] 2.3 Implementar a detecção de tipo (FII/ação) e a extração de imóveis/composição e verificar com fixture de FII
- [ ] 2.4 Adicionar fixtures HTML estáticas (ação e FII) e testes de contrato que falham quando um rótulo obrigatório desaparece

## 3. Erros e robustez do provider

- [ ] 3.1 Implementar `FundamentusError`/`TickerNotFound`/`LayoutChanged`/`NetworkError` e verificar com testes de ticker inexistente, layout alterado e falha de rede
- [ ] 3.2 Verificar que a falha de um ticker não interrompe o processamento dos demais

## 4. Composição com fallback e proveniência

- [ ] 4.1 Definir a porta `FundamentalDataProvider` (campos normalizados + origem) e verificar com teste de contrato do protocolo
- [ ] 4.2 Implementar `CompositeFundamentalProvider` com prioridade por campo (Fundamentus primário; B3/CVM/motor de FFO fallback) e verificar que campo presente no primário não consulta o fallback
- [ ] 4.3 Verificar que campo ausente no Fundamentus é buscado no fallback e que a origem fica registrada
- [ ] 4.4 Verificar que a ordem de prioridade é configurável, com Fundamentus primário por padrão

## 5. Integração e compatibilidade

- [ ] 5.1 Integrar o provider composto ao `FundamentalAnalysisUseCase` como caminho primário e verificar que `FFO Yield`, `Dividend Yield`, `P/VP` e `FFO Trend` são preenchidos quando o Fundamentus fornece os dados
- [ ] 5.2 Verificar que, com o Fundamentus indisponível, a análise cai para o fallback e mantém a linha do ticker
- [ ] 5.3 Manter `obter_ffo` como adaptador de compatibilidade e verificar que os testes existentes de FFO continuam passando
- [ ] 5.4 Ajustar o wiring em background (change B3) para usar o provider composto e verificar que a tabela exibe os valores com origem

## 6. Verificação integrada

- [ ] 6.1 Executar `pytest` e verificar que todos os testes passam
- [ ] 6.2 Executar `ruff check` e o gate de qualidade do projeto e verificar que não há violações
- [ ] 6.3 Validar a change com `openspec validate "fundamentus-fundamental-provider"` e verificar que é válida
