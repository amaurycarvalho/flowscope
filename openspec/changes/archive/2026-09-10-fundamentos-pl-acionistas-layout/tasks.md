## 1. P/L do Papel (provider Fundamentus)

- [x] 1.1 Adicionar `CAMPO_P_L = "p_l"` a `fundamental_ports.py` e incluí-lo em `CAMPOS_FUNDAMENTAIS`; verificar com teste unitário de importação/constante
- [x] 1.2 Mapear o indicador `P/L` do Fundamentus para `CAMPO_P_L` no adapter (`infrastructure/fii/fundamentus/adapter.py`); verificar com teste que uma ação com `P/L` expõe o campo e uma página sem `P/L` (FII) o omite

## 2. P/L do FII (função pura de domínio)

- [x] 2.1 Implementar função pura `p_l(preco, ultimo_dividendo)` em `domain/fii/metrics.py`, anualizando o dividendo mensal (`preco / (ultimo_dividendo × 12)`), retornando `None` quando o dividendo for ausente/zero; verificar com testes dos casos normal, dividendo zero e ausente
- [x] 2.2 Adicionar o campo `p_l` a `AnaliseFundamental` (`domain/fii/analysis.py`) e preenchê-lo no `FundamentalAnalysisUseCase` (fonte para Papel, derivado para FII); verificar com testes de uso para ambos os tipos
- [x] 2.3 Exportar a nova função em `domain/fii/__init__.py`; verificar que o import público funciona

## 3. Quantidade de acionistas via CVM (FRE + FCA)

- [x] 3.1 Adicionar fixtures de contrato dos CSVs `fre_cia_aberta_distribuicao_capital` e `fca_cia_aberta_valor_mobiliario`; verificar que o parser extrai os valores esperados das fixtures
- [x] 3.2 Implementar a aquisição dos datasets FRE e FCA reutilizando `CvmDatasetDownloader`; verificar com teste que o cache/revalidação é usado e que falha de rede retorna ausência de valor
- [x] 3.3 Implementar o parser da ponte ticker→CNPJ (`valor_mobiliario`) e o parser de `distribuicao_capital` (soma PF+PJ+Institucionais, maior `Versao` por CNPJ, sem filtro por data); verificar com testes das fixtures, incluindo múltiplas versões e data de referência futura
- [x] 3.4 Definir a porta `AcionistasProvider` em `fundamental_ports.py` e a implementação CVM; verificar com teste que ticker presente resolve a quantidade e ticker ausente retorna `None`
- [x] 3.5 Ligar a porta ao `FundamentalAnalysisUseCase`: para Papel sem cotistas do repositório, preencher `cotistas` e reutilizar `classificar_cotistas`; verificar com teste que a ação recebe o total e a classe, e o FII mantém a fonte atual
- [x] 3.6 Cachear o mapa ticker→CNPJ e a quantidade por CNPJ com `CacheManager`, associando cada entrada ao hash do arquivo de origem e à versão do parser; verificar com teste que uma segunda resolução não reprocessa o CSV e que mudar o parser invalida o cache

## 4. Tendências (classificação e rótulos)

- [x] 4.1 Trocar os valores de `TendenciaDividendo` para `FORTE_ALTA`/`ALTA`/`ESTAVEL`/`QUEDA`/`FORTE_QUEDA`/`N_A` e ajustar `calcular_tendencia` para a variação percentual com limiares ±5%, tratando `anterior == 0`; verificar com testes de cada faixa e das bordas
- [x] 4.2 Ajustar `calcular_ultimo_dividendo_consolidado`/`calcular_ultimo_dividendo` e os pontos que referenciam `TendenciaDividendo.CRESCIMENTO`/`REDUCAO`/`NEUTRO`; verificar com a suíte de testes de dividendo e do caso de uso passando
- [x] 4.3 Implementar o mapa único de rótulos descritivos (`Forte Alta`, `Leve Alta`, `Estável`, `Leve Queda`, `Forte Queda`) para FFO Trend e Tendência do dividendo na tabela; verificar com testes dos cinco rótulos e de `N/A`

## 5. Layout da tabela

- [x] 5.1 Reordenar `_COLUNAS` para a ordem do proposal, inserindo `P/L` após `P/VP`, e atualizar `_linha_analise`/`_linha_sintetica` na mesma ordem; verificar com teste da ordem das colunas
- [x] 5.2 Adicionar `p_l` a `_COLUNAS_DIREITA`; verificar com teste de alinhamento à direita
- [x] 5.3 Atualizar o cabeçalho e os índices esperados em `tests/test_presentation/test_fundamental_table.py` e nos testes de CSV/cópia; verificar que a suíte de apresentação passa

## 6. Verificação final

- [x] 6.1 Atualizar o OrientationPanel da sub-aba Fundamentos explicando o P/L do FII (preço/último dividendo) e a origem dos acionistas; verificar que o texto aparece na sub-aba
- [x] 6.2 Rodar lint, typecheck e a suíte de testes do projeto; verificar que passam sem erros
- [x] 6.3 Rodar `openspec validate "fundamentos-pl-acionistas-layout"`; verificar que retorna `valid: true` sem erros
