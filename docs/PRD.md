# PRD — FlowScope

## 1. Problema

Pequenos investidores pessoa física não têm acesso a ferramentas gratuitas e objetivas que traduzam os dados brutos de fluxo de ordens da B3 em respostas claras sobre dominância de compradores vs. vendedores, convicção dos movimentos e atuação institucional.

## 2. Público-Alvo

- Pequenos investidores pessoa física que operam no mercado acionário brasileiro
- Analistas técnicos e quantitativos autônomos
- Profissionais que desejam exportar indicadores para planilhas externas

## 3. Funcionalidades

**Essenciais:**

- Carregar dados consolidados de negociação da B3 (TradeInformationConsolidated) para uma ou mais datas
- Calcular indicadores de fluxo de ordens: VWAP, CLV, Money Flow Volume, Daily Efficiency, Dominance Score, entre outros
- Exibir 3 painéis na aba "Análise Geral": VWAP (violino + barras), Quadrantes (CLV vs VWAP Distance), Dominância do Pregão (ranking CLV)
- Exibir painéis na aba "Análise do Ticker": Evolução da Dominância, Amplitude de Preço, Fluxo Financeiro
- Filtro de tickers editável com seleção múltipla e suporte a índices (IBOV, IDIV, IFIX)
- Orientação contextual que explica o significado de cada painel
- Exportar dados brutos como CSV para área de transferência

**Secundárias:**

- Exportar gráficos como imagem para área de transferência
- Sampling strategies para datas (Fibonacci, Monte Carlo, etc.)
- Atalho de teclado e botão "Hoje" para carga rápida
- Criação de atalho no desktop (Linux)

## 4. Restrições

- Fonte de dados: API pública da B3 (sem cadastro, sem chave)
- Interface gráfica obrigatória; CLI como alternativa
- Binário único distribuível por plataforma (PyInstaller)
- Deve funcionar offline com dados em cache
- Interface e documentação em português brasileiro
- Licença MIT

## 5. Critérios de Sucesso

- Um analista consegue, em menos de 3 cliques, identificar quais ativos tiveram dominância compradora ou vendedora em um pregão
- Os indicadores são autoexplicativos com o painel de orientação
- Dados de um pregão com ~50 ativos são carregados e processados em <30s
