## 1. Domínio — Classificação de tipo/sub-tipo

- [ ] 1.1 Criar enums `TipoAtivo` (ACAO/FII/ETF/BDR/DESCONHECIDO), `SubTipoAcao` (ORDINARIA/PREFERENCIAL/ETF) e `SubTipoFii` (TIJOLO/PAPEL/HIBRIDO/FIAGRO/FIINFRA/DESCONHECIDO) em `domain/fii/classification.py` e verificar que os valores correspondem à especificação
- [ ] 1.2 Implementar a taxonomia versionada `TaxonomiaFii` (mapa `ticker → SubTipoFii`) com versão explícita e verificar que tickers não mapeados retornam `DESCONHECIDO`
- [ ] 1.3 Implementar o classificador sintático de ticker (tipo + sub-tipo de ação) combinado com `code-cvm-resolution` e verificar os cenários de ação/FII/ETF/BDR
- [ ] 1.4 Implementar a função de elegibilidade (TIJOLO/HIBRIDO) e verificar que papel/fiagro/ação/etf retornam não elegível

## 2. Domínio — Métricas de dividendo

- [ ] 2.1 Implementar a extração de última data-com e último dividendo (somente `Rendimento`, ignorando `Amortização`) em `domain/fii/dividends.py` e verificar os cenários de provento/amortização
- [ ] 2.2 Implementar a tendência do dividendo (último vs. anterior, banda ±5% configurável) e verificar os cenários SUBINDO/CAINDO/MANTEVE/N/A
- [ ] 2.3 Escrever testes unitários para `dividend-metrics` e verificar que passam (`pytest tests/test_domain`)

## 3. Domínio — Métricas fundamentalistas de FII

- [ ] 3.1 Implementar funções puras em `domain/fii/metrics.py` (`market_value`, `ffo_yield`, `p_ffo`, `p_vp`, `dividend_yield`, `ffo_momentum`) com `decimal.Decimal` e verificar os cenários de exemplo (HGBS11: FFO Yield 0,0816, P/FFO 12,25, P/VP 0,92)
- [ ] 3.2 Implementar a classificação de tendência do FFO e as faixas de cotistas e patrimônio em `domain/fii/classification_faixas.py` e verificar os limiares da RFC-006
- [ ] 3.3 Implementar a regra de FFO não positivo (métricas N/A) e a checagem de consistência `P/FFO × FFO Yield ≈ 1` e verificar a geração de `DATA_INCONSISTENCY`
- [ ] 3.4 Implementar a evidência por métrica (`MetricEvidence`) e verificar que registra fórmula, entradas, fontes e versão de cálculo
- [ ] 3.5 Escrever testes golden (fixture HGBS11 congelada) e testes de invariantes matemáticas e verificar que passam

## 4. Aplicação — Use case de análise fundamentalista

- [ ] 4.1 Definir as portas (`FiiFundamentalRepository`, `FfoProvider`, `MarketPricePort`) em `application/fundamental_ports.py` e verificar que desacoplam a aplicação da infraestrutura
- [ ] 4.2 Implementar `FundamentalAnalysisUseCase` orquestrando identidade → classificação → dividendos → (Fase B) métricas FFO, com isolamento por ticker e verificar que falha de um ticker não invalida os demais
- [ ] 4.3 Escrever testes do use case com fixtures determinísticos e verificar que passam

## 5. Infraestrutura — Fase A (reuso de provento e identidade)

- [ ] 5.1 Implementar `FiiFundamentalRepository` consumindo `Provento`/`Entidade` (de `structured-earnings`) e `code-cvm-resolution` (de `regulacao-mercado`), com resolução tolerante (vazio quando não houver dados) e verificar via testes de integração mockados
- [ ] 5.2 Integrar `MarketPricePort` aos dados B3 já existentes (fechamento `LastPric`) e verificar que retorna o último fechamento até a data de referência

## 6. Infraestrutura — Fase B (CVM + provedor de FFO)

- [ ] 6.1 Implementar `CVMAdapter` (NAV, nº de cotas, nº de cotistas) via informes mensal/trimestral estruturados, com `SOURCE_SCHEMA_VERSION` e verificar o parsing com fixture de dados CVM
- [ ] 6.2 Implementar `FundamentusProvider` (FFO 12m/3m) com metodologia `SOURCE_REPORTED` e verificar a extração com fixture congelada
- [ ] 6.3 Integrar cache (`CacheManager`) para CVM e FFO e verificar que a aquisição é reutilizada em execuções repetidas

## 7. Apresentação GUI — Sub-aba Fundamentos

- [ ] 7.1 Implementar `FundamentalTablePanel` (ttk.Treeview) em `presentation/gui/charts/fundamental_table.py`, renderizando as colunas especificadas e `N/A` para não elegíveis, e verificar a renderização em teste de apresentação
- [ ] 7.2 Conectar a sub-aba "Fundamentos" em `_build_general_tabs()` (`app_tab_layout.py`) e registrar o painel em `_GENERAL`, verificando que a sub-aba aparece na "Análise Geral"
- [ ] 7.3 Adicionar o conteúdo explicativo da sub-aba em `TAB_CONTENT` (`app_tabs.py`) e verificar que o OrientationPanel exibe o texto ao selecionar "Fundamentos"
- [ ] 7.4 Verificar a integração ponta a ponta: carregar watchlist com FIIs e ações, confirmar colunas de identidade/dividendo para todos e métricas FFO apenas para FIIs elegíveis

## 8. Qualidade

- [ ] 8.1 Rodar `make lint test` e verificar que não há erros de lint nem falhas de teste
- [ ] 8.2 Verificar que nenhum módulo de domínio importa infraestrutura (dependência de camadas conforme RFC-007)
