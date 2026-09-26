# Painéis do FlowScope — Interface Gráfica

## Estrutura Geral

A interface é dividida em três grandes regiões:

```
┌──────────────────────────────────────────────────────────────────────────┐
│  [Data] [Hoje] [Carregar] [Período] [Amostragem] [Copiar Dados]           │
├──────────────────────────────────┬───────────────────────────────────────┤
│  Aba Principal                   │  Filtro de Tickers                    │
│  ┌────────────────────────────┐  │  (lista editável)                     │
│  │  Sub-abas                  │  │                                       │
│  │                            │  │  Orientação                           │
│  │                            │  │  (ajuda contextual)                   │
│  └────────────────────────────┘  │                                       │
├──────────────────────────────────┴───────────────────────────────────────┤
│  Status: mensagens, progresso e indicadores                              │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Barra Superior

### Seletor de Data

- **Componente:** `DateEntry` (tkcalendar)
- **Descrição:** Campo de seleção de data no formato `YYYY-MM-DD`.
- **Objetivo:** Definir a data de referência para carregamento dos dados da B3.
- **Uso:** Digite a data manualmente ou use o calendário suspenso. Pressione Enter ou clique em "Carregar" para iniciar a carga.

### Botão "Hoje"

- **Descrição:** Atalho para definir a data atual e carregar automaticamente.
- **Objetivo:** Agilizar a consulta do pregão mais recente disponível.

### Botão "Carregar"

- **Descrição:** Dispara o carregamento dos dados da B3 para a data selecionada.
- **Objetivo:** Obter os dados consolidados de negociação (TradeInformationConsolidated), processar todos os indicadores e popular a interface.

### Seletor de Período

- **Componente:** `ttk.Combobox` (somente leitura)
- **Descrição:** Define a janela de tempo usada na análise. Opções: "Últimos 30 dias", "Últimos 60 dias (cache)" e "Últimos 90 dias (cache)".
- **Objetivo:** Controlar quantos dias corridos entram no cálculo dos indicadores e nos painéis históricos. As opções de 60 e 90 dias usam apenas dados já em cache (sem download da B3); a de 30 dias baixa da B3 o que faltar.
- **Uso:** Ao trocar a opção com dados já carregados, a análise é recalculada automaticamente.

### Seletor de Amostragem

- **Componente:** `ttk.Combobox` (somente leitura)
- **Descrição:** Define o método de seleção das datas dentro do período. Opções: "Fibonacci", "Fibonacci reverso", "Fibonacci duplo", "Monte Carlo", "Monte Carlo duplo" e "Todos os dias".
- **Objetivo:** Priorizar datas recentes, antigas, as margens do período ou o conjunto completo, dependendo do que se quer investigar.
- **Uso:** Ao trocar a opção com dados já carregados, a análise é recalculada automaticamente. Um rótulo ao lado descreve o efeito da opção escolhida.

### Botão "Copiar Dados"

- **Descrição:** Copia para a área de transferência o conteúdo adequado ao contexto ativo:
  - **Análise Geral → Fundamentos:** CSV da tabela de fundamentos dos tickers exibidos.
  - **Análise do Ticker → Documentos:** o texto atual do campo de pré-visualização.
  - **Análise Geral → Notícias:** o texto atual do campo de pré-visualização.
  - **Chat AI:** o conteúdo da sessão de chat.
  - **Demais sub-abas:** CSV bruto de negociação (`RptDt;TckrSymb;MinPric;MaxPric;TradAvrgPric;LastPric;TradQty;FinInstrmQty;NtlFinVol`).
- **Objetivo:** Exportação rápida para análise externa (planilhas, relatórios) ou cópia de um documento/resumo.
- **Atalho:** `Ctrl+Shift+C`.

---

## Aba Principal: "Análise Geral"

### Sub-aba: VWAP

- **Objetivo:** Comparar a distribuição de preços de todos os ativos em relação ao seu respectivo VWAP no período.
- **Responde a pergunta:** _Quem está acima do preço justo e quem está abaixo?_
- **Indicadores envolvidos:** VWAP (preço médio ponderado), volume por bucket de preço (volume profile), preço de fechamento (LastPric), preço mínimo e máximo (MinPric, MaxPric).
- **Como interpretar:** O VWAP é a referência de preço justo do período. Negociações acima do VWAP indicam viés comprador; abaixo, viés vendedor. A largura do violino mostra em quais faixas de preço houve maior concentração de volume. O último preço (losango vermelho) em relação ao VWAP indica se o fechamento reforça ou contradiz a tendência do período.

### Sub-aba: Quadrantes

- **Objetivo:** Classificar ativos em quatro quadrantes com base no CLV (eixo X) e no desvio do VWAP (eixo Y), revelando a interação entre fluxo comprador/vendedor e posição relativa ao preço justo.
- **Responde a pergunta:** _Quem dominou o fechamento? O preço terminou acima ou abaixo do valor justo? Quanto volume financeiro sustentou esse comportamento?_
- **Indicadores envolvidos:** CLV (Close Location Value), VWAP Distance (desvio percentual do último preço em relação ao VWAP diário), Volume (FinInstrmQty como tamanho da bolha).
- **Como interpretar:**
  - Q1 (CLV > 0, acima do VWAP): compra forte confirmada — fechamento na metade superior do range e acima do VWAP.
  - Q2 (CLV < 0, acima do VWAP): venda relativa — ativo acima do VWAP mas perdeu força no fechamento (possível realização).
  - Q3 (CLV < 0, abaixo do VWAP): venda forte confirmada — vendedores dominaram o dia.
  - Q4 (CLV > 0, abaixo do VWAP): compra em desconto — reação compradora insuficiente para recuperar o VWAP.
  - Se apenas um ticker for selecionado, as setas cinzas mostram a trajetória dos dias anteriores, evidenciando a evolução temporal de cada ativo.

### Sub-aba: Dominância do Pregão

- **Objetivo:** Visualizar rapidamente quais ativos tiveram dominância compradora ou vendedora no último pregão.
- **Responde a pergunta:** _Quem venceu a disputa diária pelo preço?_
- **Indicadores envolvidos:** CLV (Close Location Value) para direção/intensidade, Money Flow Volume (MFV) para capital envolvido.
- **Como interpretar:** Barras para a direita indicam dominância compradora (CLV positivo); para a esquerda, vendedora (CLV negativo). Quanto maior o comprimento, mais intensa a dominância. O traço horizontal sobre a barra representa o volume financeiro que sustentou o movimento. Passe o mouse sobre as barras para ver detalhes do ticker.

### Sub-aba: Rede de Correlação

- **Objetivo:** Revelar a topologia da carteira — quem se agrupa com quem — distinguindo o co-movimento de curto prazo (correlação) do vínculo de equilíbrio de longo prazo (cointegração do spread), em vez de uma matriz N×N ilegível.
- **Responde a pergunta:** _Quais papéis se movem juntos e quais mantêm uma relação de equilíbrio no tempo?_
- **Indicadores envolvidos:** correlação assinada dos retornos entre observações consecutivas; cointegração par-a-par (Engle-Granger + ADF, com defasagem escolhida por BIC); meia-vida de reversão do spread; comunidades, centralidade (grau) e modularidade da rede.
- **Como interpretar:**
  - Cada nó é um ticker e cada aresta um par com relação relevante. A **cor da aresta** representa a correlação de curto prazo em escala divergente fixa de −1 a +1 (azul para negativa, vermelho para positiva), com colorbar. O **estilo e a espessura** representam a cointegração: traço sólido e grosso quando o par é cointegrado; tracejado e fino caso contrário, com legenda.
  - A **cor do nó** representa a comunidade (cluster) e o **tamanho** representa a centralidade (grau) do papel na rede. Só entram arestas com |correlação| acima do limiar (`0,5`) ou pares cointegrados, evitando grafos densos demais.
  - **Uso dos combos globais:** a rede é calculada sobre os dados já carregados, conforme o período e a amostragem dos combos globais e restrita aos tickers selecionados no Listbox. Não há seletor de janela próprio; mudar período ou amostragem recarrega os dados e recalcula a rede.
  - **Gates de densidade:** a correlação exige ao menos 30 observações alinhadas e a cointegração, no mínimo 40. Com menos de 30 o painel fica vazio; entre 30 e 39 exibe apenas as arestas de correlação e avisa que a cointegração requer 40.
  - **Limitações da amostragem:** a amostragem esparsa da B3 (Fibonacci) cria intervalos irregulares; o diagnóstico no topo informa o número de observações, o período coberto e os gaps mínimo/mediana/máximo em dias úteis. A cointegração é um indício exploratório sob espaçamento irregular; para densificar a grade, use a amostragem "Todos os dias" com um período maior. O resultado do Engle-Granger é direcional (a direção da regressão é fixada pela ordem alfabética dos tickers) e, com muitos pares, alguns falsos positivos são esperados.
  - **Barra de ferramentas:** a mesma da sub-aba VWAP — Início, Voltar, Avançar, Mover, Ampliar, Salvar e "Copiar Gráfico" (copia a figura para a área de transferência como imagem).
- **Reprodutibilidade:** o layout force-directed usa semente fixa, de modo que a mesma seleção e a mesma grade de observações produzem a mesma disposição de nós.

### Sub-aba: Fundamentos

- **Objetivo:** Consolidar, por ticker da watchlist, a identidade, a classificação, os dividendos, o P/L, a quantidade de cotas emitidas, o número de cotistas/acionistas, as métricas de short interest e — para FIIs elegíveis — as métricas fundamentalistas de FFO.
- **Responde a pergunta:** _Quais ativos estão na carteira, que tipo são e quão barato ou caro está o ativo frente ao lucro (ou último dividendo), ao FFO e ao patrimônio?_
- **Indicadores envolvidos:**
  - **Identidade:** ticker, nome, tipo (`Papel` para ações, ETFs e BDRs; `FII`) e sub-tipo (FII: prefixo `Tijolo:`/`Papel:` seguido de segmento e gestão; Papel: espécie, setor e subsetor; sem dados do Fundamentus, usa os rótulos determinísticos tijolo/papel/híbrido/fiagro/fiinfra ou ordinária/preferencial/ETF).
  - **Cotação e valor:** P (Cotação), Preço Típico (média de 52 semanas), P / PT (desconto/prêmio da cotação frente ao preço típico), VP (VP/Cota) e P/VP.
  - **P/L:** para ações, o indicador reportado pela fonte; para FIIs, a cotação dividida pelo último dividendo anualizado (× 12), em anos.
  - **Dividendos:** Dividend Yield, última data-com, último dividendo (Rendimento), dividendo anterior e tendência do dividendo (último vs. anterior em cinco faixas).
  - **Short interest:** Shorts% (ações alugadas ÷ free float, em percentual com uma casa decimal), Volume de Shorts (classificação do Shorts%: Inexistente para 0%/N/A, Muito Baixo < 1%, Baixo < 3%, Alto ≤ 10% e Muito Alto > 10%), Fechamento Shorts (SIR, ações alugadas ÷ volume médio diário de negociação, em dias com uma casa decimal e sufixo `d`) e Risco Fechamento (classificação do SIR: Inexistente para 0/N/A, Muito Baixo < 2, Baixo < 4, Alto ≤ 5 e Muito Alto > 5). As ações alugadas vêm do empréstimo de ativos da B3 (BDI, "Posições em aberto"); o free float vem do CVM FRE. Na ausência do free float, o denominador do Shorts% é o total emitido (FIIs usam o total de cotas).
  - **Métricas FFO (apenas FII):** FFO/Receita (12m e 3m), FFO Trend, Dividendos/Receita (12m e 3m) e Dividendos/FFO (12m e 3m), em percentual com uma casa decimal.
  - **Cotas e cotistas:** quantidade de cotas/ações emitidas, número de cotistas do FII ou quantidade de acionistas da companhia (CVM), suas classificações, patrimônio e data de referência.
  - **Informações adicionais:** LPA, ROE e ROIC (ação); Qtd Imóveis, Cap Rate, Vacância Média e percentuais por indexador (FII).
  - **Dados fiscais:** CNPJ e, para FIIs, administrador e gestor.
- **Como interpretar:** O P/L de um FII anualiza o último dividendo mensal (preço ÷ (último dividendo × 12)) para expressar a quantidade de anos, enquanto o P/L de uma ação é o lucro reportado pela fonte; N/A indica ausência do dado. O Preço Típico é a referência de preço médio de 52 semanas ((máxima + mínima + cotação) / 3); o P / PT expressa o desconto (negativo) ou prêmio (positivo) da cotação frente a esse preço típico. O FFO/Receita indica quanto da receita vira caixa operacional; o Dividendos/Receita, quanto da receita é destinado a dividendos; e o Dividendos/FFO, quanto do caixa operacional é consumido pelos dividendos (abaixo de 100% o FFO cobre os dividendos, acima de 100% os dividendos superam o FFO e negativo o FFO foi negativo no período). O Shorts% expressa a magnitude relativa da aposta baixista sobre o free float (para FIIs, sobre o total de cotas, na ausência de free float) e o Fechamento Shorts expressa a dificuldade operacional de fechamento em dias, com valores acima de 5 considerados altos. O número de cotistas de FIIs vem do informe mensal e o de ações, da quantidade de acionistas publicada pela CVM. A quantidade de cotas emitidas de um FII vem da B3/CVM, com o Fundamentus como fallback; a de ações vem do Fundamentus e dimensiona o tamanho da companhia. O FFO Trend compara FFO/Receita (3m) com FFO/Receita (12m) em pontos percentuais, com os rótulos Forte Alta (≥ +20 p.p.), Leve Alta (≥ +5 p.p.), Estável, Leve Queda (≥ −20 p.p.) e Forte Queda (< −20 p.p.); a tendência do dividendo usa os rótulos Forte Alta (≥ +5%), Leve Alta, Estável, Leve Queda e Forte Queda (≤ −5%). Ativos do tipo Papel exibem N/A nas colunas de razões sobre a receita. O P/VP compara o valor de mercado com o patrimônio líquido; valores de P/VP abaixo de 1 indicam cota negociando abaixo do patrimônio. Informações adicionais reúnem indicadores do ativo (LPA, ROE e ROIC em ações; imóveis, Cap Rate, Vacância Média e percentuais por indexador em FIIs) e Dados fiscais reúnem o CNPJ e, para FIIs, o administrador e o gestor; itens sem dado em nenhuma fonte são omitidos. Os valores são calculados com precisão decimal completa e arredondados somente na apresentação. As colunas Ticker e Nome permanecem congeladas à esquerda enquanto as demais 32 colunas rolam horizontalmente; a fronteira entre os painéis é a borda direita de Nome, e a largura da região congelada é a soma das larguras dessas duas colunas, recalculada automaticamente ao redimensioná-las. A rolagem vertical é compartilhada e a seleção de uma linha é espelhada entre os dois painéis, mantendo apenas uma linha selecionada por vez.

### Sub-aba: Notícias

- **Objetivo:** Navegar pelas notícias do Plantão B3 e pelas informações regulatórias e de mercado da RFC-004 (censuras públicas, condições excepcionais e programas de aquisição de ações), baixar o corpo dos itens com URL e resumi-los com I.A.
- **Responde a pergunta:** _O que foi publicado no mercado no período e o que isso significa?_
- **Layout do painel:** Painel dividido horizontalmente (`PanedWindow`), com barra de controles no topo:
  ```
  ┌───────────────────────────────────────────────────────────────┐
  │  [Atualizar] [Abrir] [I.A.] [Resumir pendentes]               │
  ├──────────────────────────────┬────────────────────────────────┤
  │  Notícias                    │  Pré-visualização              │
  │  └ categoria de topo          │  (campo somente-leitura)       │
  │    ano → mês → categoria →    │                                │
  │    itens                      │                                │
  └──────────────────────────────┴────────────────────────────────┘
  ```
- **Carga inicial a partir do cache:** ao abrir a sub-aba (ou trocar de aba), a árvore é montada **somente com o cache local** — o índice de metadados (`~/.cache/flowscope/noticias/index.json`), o HTML, os textos e os resumos já gravados — sem consultar a B3. É o botão "Atualizar" que faz a carga (listagem e download) em segundo plano, como na sub-aba "Documentos".
- **Barra de controles:**
  - **"Atualizar":** adquire os itens das quatro categorias em segundo plano, com barra de progresso e cancelamento. A barra de status anuncia e acompanha cada categoria ("Censuras Públicas", "Condições Excepcionais", "Programas de Aquisição de Ações" e "Geral") antes e durante a carga; a "Geral" avança **dia a dia**, do mais recente ao mais antigo, pulando os dias já baixados. Ao concluir, grava o cache/índice e remonta a árvore a partir do cache local. Interromper a carga preserva na árvore o que já foi carregado, pois os metadados são indexados a cada item processado.
  - **"Abrir":** abre a URL do item selecionado no navegador padrão. Permanece desabilitado enquanto nenhum item com URL estiver selecionado.
  - **"I.A.":** abre o diálogo de configuração do provedor de LLM, o mesmo da sub-aba "Documentos".
  - **"Resumir pendentes":** gera em lote os resumos dos itens com texto e sem resumo; permanece desabilitado sem LLM configurada ou sem itens pendentes.
- **Árvore hierárquica:** raiz "Notícias" → categorias de topo ("Censuras Públicas", "Condições Excepcionais", "Programas de Aquisição de Ações" e, por último, "Geral") → ano → mês → categoria → itens. Ao carregar (inicialmente ou após "Atualizar"), a árvore é exibida **expandida só até o primeiro nível**: a raiz fica aberta e as categorias de topo ficam recolhidas; a expansão é manual a partir daí. A "Geral" fica por último por ser a carga mais pesada (um download por artigo), de modo que a extração de texto e os resumos em lote só a processam depois das fontes regulatórias. O nível de categoria é o **tipo de notícia** na "Geral" (ver abaixo), o ticker/emissor em censuras, o segmento em condições e a empresa em programas. **Tipos da "Geral":** cada notícia é classificada pelo título, a partir da whitelist, em "Negociação", "Listagem e Registro", "Ofertas e OPA", "Participações", "Reorganização Societária", "Recuperação e Liquidação", "Eventos de Capital", "Governança e Auditoria" ou "Esclarecimentos e Oscilações"; títulos que não se enquadram vão para "Outros". Pastas expandem e recolhem com duplo clique; somente itens abrem. Selecionar a raiz exibe a lista de todas as categorias com itens.
- **Aquisição e cache:** a categoria **"Geral"** lista as notícias **excepcionais** do Plantão B3 do **último ano**, **dia a dia**, do mais recente ao mais antigo, baixando o HTML de cada artigo a partir da URL; a whitelist de eventos fora da curva é mantida (suspensão/reabertura/retirada de negociação, negociação não contínua, início/prorrogação/adiamento de negociação, incorporação/fusão/cisão/reorganização, recuperação judicial/extrajudicial, falência, liquidação, intervenção, grupamento/desdobramento/bonificação, redução/aumento de capital, amortização, deslistagem/cancelamento de listagem/registro, conversão de categoria, oferta pública/OPA e modificações de oferta, aquisição/alienação de participação, direito de preferência, mudança de auditor, ato homologatório, transação entre partes relacionadas, esclarecimentos CVM/B3 e oscilação atípica), ficando de fora a rotina, os anúncios de distribuição, a liberação de negociação das cotas, a subscrição privada e o fato relevante. As categorias **"Censuras Públicas"**, **"Condições Excepcionais"** e **"Programas de Aquisição de Ações"** são carregadas da RFC-004 com o **histórico completo** da fonte (páginas estáticas e endpoint de programas com retry, pois responde 404 intermitente). Quando o item tem URL, o corpo é baixado; quando não tem, o próprio registro é o conteúdo. A falha de uma fonte ou de um item é tolerada sem interromper as demais. O cache é próprio, em `~/.cache/flowscope/noticias/<AAAA>/<MM>/<hash>.html` (chave `sha1` da URL ou da identidade do item), e nunca sobrescreve conteúdo existente. Como o caminho não carrega título, seção, categoria, data nem URL, a aquisição grava esses metadados em `~/.cache/flowscope/noticias/index.json` (indexados pelo caminho relativo do HTML), permitindo que a exibição e o contexto do chat leiam só o cache; uma reexecução de "Atualizar" reconstrói o índice sem rebaixar os corpos já em cache. A carga da "Geral" é **incremental**: o dia mais recente é sempre recarregado e o índice guarda a data mais antiga já processada e a referência da última carga (`geral_mais_antiga`/`geral_referencia`), de modo que só os dias ainda não baixados (ou a lacuna desde a referência anterior) são lidos. As escritas do índice são **agrupadas** (fontes regulatórias e "Geral" gravam a cada 25 unidades e ao final), reduzindo regravações.
- **Pré-visualização do item:** ao selecionar um item, o texto é extraído do HTML em cache (`BeautifulSoup`) e exibido sob demanda. Para a categoria **"Geral"**, a extração usa o corpo do artigo do Plantão B3 (`#conteudoDetalhe`), ignorando a moldura de busca/navegação e o rodapé da página; os itens regulatórios usam o texto integral da página. **Documento vinculado sob demanda:** quando o corpo da "Geral" é apenas um apontador, o documento é baixado, extraído e passa a ser o corpo da notícia, também no processamento de "Resumir pendentes"; o texto fica no cache de textos e não é rebaixado. São suportados o visualizador da **CVM RAD** (`GET` do visualizador + `POST` `ExibirPDF` em base64 → PDF via `pypdf`) e o do **FNET** (`GET` do visualizador → `GET` do `iframe` `exibirDocumento` → PDF, com retry). Captcha habilitado, falha de rede ou formato inesperado mantêm apenas o corpo. Com resumo longo preenchido, a caixa exibe o resumo, seguido do texto integral; sem resumo e com a LLM configurada, os resumos curto e longo são gerados e persistidos; itens sem texto extraível mostram mensagem informativa.
- **Resumos com I.A.:** reutilizam o serviço de resumo dos documentos (curto até 280 e longo até 1.500 caracteres), persistidos em `~/.cache/flowscope/document-summaries/NOTICIAS-<ANO>-<MES>.json` (particionados por ano e mês; o formato anterior `NOTICIAS.json` é migrado automaticamente). No lote, uma falha por item é registrada e os demais continuam.
- **Estado vazio:** nenhuma categoria com itens no cache exibe mensagem informativa; antes da primeira atualização, orienta a acionar "Atualizar". Entradas do índice sem HTML correspondente são ignoradas.
- **Chat AI:** os itens em cache das quatro categorias também são oferecidos como fonte de contexto da aba "Chat AI", em **duas camadas**. No primeiro prompt vai um **índice compacto** — uma linha por item com `[seção] data — tipo — título (chave curta)`, intercalando as seções e ordenando do mais recente ao mais antigo para que todas as categorias apareçam — mais a instrução de pedir as chaves desejadas. A LLM devolve as chaves no campo `documentos` da resposta e a segunda chamada entrega o resumo longo/curto e/ou o texto resolvido da notícia (tetos de 12.000 caracteres por item e 48.000 globais). A resolução soma a cascata de documentos por ticker e as notícias no mesmo gate de confirmação. Quando o texto é um apontador cujo documento vinculado (CVM RAD/FNET) ainda não foi baixado, a fonte sinaliza a indisponibilidade em vez de apresentar a URL como conteúdo.

---

## Aba Principal: "Análise do Ticker"

O ticker analisado é determinado pelo primeiro item selecionado na TickerList (painel direito). Se nenhum ticker estiver selecionado, usa o primeiro da lista. Se a lista estiver vazia, exibe "Selecione um ticker". Os dados são atualizados automaticamente ao trocar de ticker ou de sub-aba.

### Sub-aba: Evolução da Dominância ✅

- **Objetivo:** Visualizar a evolução temporal da dominância compradora/vendedora para o ticker selecionado.
- **Responde a pergunta:** _Quem venceu a disputa diária pelo preço?_
- **Componente gráfico:** Gráfico de barras horizontais (CLV por pregão), com linha horizontal representando o fluxo financeiro diário (Daily Money Flow).
- **Indicadores envolvidos:** CLV (Close Location Value) nas barras, Daily Money Flow (traço horizontal), Eficiência (convicção no tooltip).
- **Como interpretar:** Cada barra representa um pregão. Direita = compradores dominaram; Esquerda = vendedores dominaram. O traço horizontal indica o fluxo financeiro diário (intensidade codificada pela espessura/opacidade). O rodapé mostra a proporção de dias compradores vs. vendedores. Passe o mouse sobre as barras para ver detalhes da dominância e convicção do movimento.

### Sub-aba: Amplitude de Preço ✅

- **Objetivo:** Visualizar como o preço percorreu sua faixa de negociação ao longo dos pregões, identificando se a oscilação resultou em movimento direcional convincente ou se compradores e vendedores permaneceram equilibrados.
- **Responde a pergunta:** _O preço apenas oscilou ou houve um movimento direcional convincente durante o pregão? Como a posição do fechamento dentro do range evoluiu nos últimos dias?_
- **Layout do painel:** O painel é composto por dois componentes gráficos organizados verticalmente (GridSpec com `height_ratios=[3, 0.6]`):
  ```
  ┌──────────────────────────────────────────┐
  │  Price Range Timeline       [Classificação]│
  │  (com eficiência como barra de fundo)    │
  ├──────────────────────────────────────────┤
  │  CLV Gauge                               │
  └──────────────────────────────────────────┘
  ```
- **Componentes:**
  - **Price Range Timeline (painel superior, 3/4 da altura):** Gráfico horizontal que normaliza o range [Min, Max] de cada pregão em 0-100% no eixo X. O eixo Y lista as datas cronologicamente (mais recente no topo). Cada linha possui uma **barra de fundo** cujo comprimento é a Eficiência Diária (substitui o gauge separado de eficiência): vermelha (≤ 0,30), amarela (0,30-0,60), verde (> 0,60). Sobre a barra de fundo, uma linha cinza horizontal percorre 0-100%.
    - Dia atual: exibe todos os marcadores de referência — ● (Close, tamanho proporcional ao Range%), **M** (Median Price), **T** (Typical Price), **V** (VWAP), **W** (Weighted Close).
    - Dias anteriores: ● com opacidade reduzida, conectados por setas cinzas que traçam a trajetória do fechamento.
    - **Classificação qualitativa** no canto superior direito, baseada na combinação de Range% e Eficiência Diária:
      - **Pregão Lateral:** Range% ≤ mediana histórica e Eficiência ≤ 0,30 — oscilação dentro do normal, sem direção.
      - **Volatilidade sem Direção:** Range% > mediana e Eficiência ≤ 0,30 — range ampliado mas sem convicção.
      - **Movimento Consistente:** Range% ≤ mediana e Eficiência > 0,30 — movimento direcionado mesmo com amplitude moderada.
      - **Movimento Direcional Forte:** Range% > mediana e Eficiência > 0,30 — range amplo com convicção direcional.
    - Mínima e máxima do dia mais recente exibidas como labels abaixo do eixo X.
  - **CLV Gauge (painel inferior, ~1/4 da altura):** Barra horizontal (-1 a +1) indicando onde o preço fechou dentro do range. Verde para CLV positivo (pressão compradora), vermelho para negativo (pressão vendedora), com labels "Vendedores ←" e "Compradores →".
- **Indicadores envolvidos:**
  - **Range** e **Range Percentual** medem a amplitude da oscilação diária.
  - **CLV (Close Location Value)** indica onde o preço fechou dentro dessa faixa.
  - **Daily Efficiency** mostra quanto da amplitude foi convertida em deslocamento líquido (usado como barra de fundo).
  - **Median Price**, **Typical Price**, **Weighted Close** e **VWAP** servem como referências para comparar a posição do fechamento.
- **Como interpretar:**
  - Uma amplitude elevada indica maior volatilidade, mas não significa necessariamente uma tendência forte.
  - Um **CLV** próximo de **+1** indica fechamento perto da máxima do dia; próximo de **−1**, fechamento perto da mínima.
  - Uma **Eficiência Diária** elevada mostra que a oscilação foi convertida em avanço efetivo, sugerindo convicção.
  - Quando a amplitude é alta mas a eficiência é baixa, o pregão foi marcado por disputa sem direção.
  - Dias com barra de fundo verde consecutiva = sequência direcional forte.
  - Passe o mouse sobre os marcadores do timeline para ver valores detalhados de cada pregão.

### Sub-aba: Fluxo Financeiro

- **Objetivo:** Mostrar se o movimento do preço foi acompanhado por fluxo financeiro suficiente para indicar convicção compradora ou vendedora.
- **Responde a pergunta:** _O movimento de hoje foi sustentado por fluxo financeiro?_
- **Layout do painel:** Três subplots empilhados verticalmente (GridSpec com `height_ratios=[3, 2, 3]`):
  ```
  ┌──────────────────────────────────────────┐
  │  Card de Classificação (sem eixos)       │
  │  (título, classificação, DMF,            │
  │   MFV acumulado, Range%)                 │
  ├──────────────────────────────────────────┤
  │  CLV / Score Bar                         │
  │  (marcador CLV, labels Comprador/Vendedor)│
  ├──────────────────────────────────────────┤
  │  Pressão no Range (B×S)                  │
  │  (barra empilhada Buy/Sell Pressure)     │
  └──────────────────────────────────────────┘
  ```
- **Componentes:**
  - **Card de Classificação (painel superior, eixos ocultos):** Exibe o título "Fluxo Financeiro — {ticker}", a classificação qualitativa (ex.: "Fluxo Forte"), e os valores do último pregão: Volume Financeiro (R$ X,XXM), DMF (R$ X,XXM), MFV Acumulado (R$ X,XXM) e Range% (X,X%). Borda colorida conforme a classificação.
  - **Gráfico CLV / Score (painel médio):** Barra horizontal na escala −1 a +1. Verde para fluxo comprador (CLV positivo), vermelho para vendedor (CLV negativo). Marcador triangular na posição exata do CLV, rótulos "◄ Vendedor" / "Comprador ►", escala percentual (−100% a +100%).
  - **Barra de Pressão no Range (painel inferior):** Barra empilhada horizontal com Buying Pressure (verde) e Selling Pressure (vermelha). Rótulos "Compra {bp}%" e "Venda {sp}%". Fórmulas BP e SP como referência.
- **Indicadores envolvidos:**
  - `Daily Money Flow (DMF)` — CLV × Volume Financeiro do pregão, exibido em milhões
  - `Money Flow Volume (MFV) acumulado` — soma do DMF no período, exibido em milhões
  - `CLV (Close Location Value)` — posição do fechamento no range (−1 a +1)
  - `Buying Pressure / Selling Pressure` — domínio do range (0 a 1)
  - `Score normalizado` — DMF / Volume Financeiro (comparável entre ativos)
  - `Range Percentual` — amplitude relativa do dia
- **Como interpretar:** O DMF é o indicador principal. Score > 8% sugere fluxo forte. MFV acumulado mostra tendência multidia. CLV indica onde o preço fechou. Passe o mouse sobre o card para detalhes numéricos completos.

### Sub-aba: Evolução dos Fundamentos

- **Objetivo:** Acompanhar como os fundamentos do ticker selecionado evoluíram ao longo das datas já observadas e retidas no cache histórico.
- **Responde a pergunta:** _Os fundamentos do ativo melhoraram ou pioraram desde a observação mais antiga do cache?_
- **Origem dos dados:** Exclusivamente o cache histórico de fundamentos (`~/.cache/flowscope/fundamentos/{TICKER}.json`). Nenhuma aquisição de rede é feita ao abrir a sub-aba; só existem pontos para os dias em que os dados do ticker já foram carregados.
- **Campos exibidos:** Cotação (R$), VP (VP/Cota) (R$), P/VP, Dividend Yield (%), Último dividendo (R$), Nº de cotistas, Nº de cotas e Shorts% (%).
- **Layout do painel:** Small multiples — oito mini-gráficos de linha (grade 4×2), um por campo, com eixo de datas compartilhado e escala vertical própria, para não misturar unidades.
  ```
  ┌───────────────────────────┬───────────────────────────┐
  │ Cotação (R$)              │ VP (VP/Cota) (R$)         │
  ├───────────────────────────┼───────────────────────────┤
  │ P/VP                      │ Dividend Yield (%)        │
  ├───────────────────────────┼───────────────────────────┤
  │ Último dividendo (R$)     │ Nº de cotistas            │
  ├───────────────────────────┼───────────────────────────┤
  │ Nº de cotas               │ Shorts%                   │
  └───────────────────────────┴───────────────────────────┘
  ```
- **Amostragem das datas:** As datas partem da observação mais recente e recuam com intervalos que crescem na sequência de Fibonacci (1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377 dias), aproximando cada alvo para a data de cache mais próxima. A data mais antiga e a mais recente aparecem sempre; o gráfico as exibe em ordem crescente (mais antiga → mais recente).
- **Como interpretar:** Em cada painel, a linha vai da observação mais antiga (esquerda) para a mais recente (direita); o ponto vermelho destaca o valor mais recente. Linha subindo indica que o indicador cresceu no período; descendo, que recuou. As datas do eixo exibem dia, mês e ano (`DD/MM/AA`) e aparecem no painel inferior com dado de cada coluna. Campos sem valor em uma observação deixam uma lacuna; campos sem nenhum valor no cache mostram "sem dado". Quando o ticker não tem histórico retido, o painel exibe um aviso de ausência.
- **Interação:** Passe o mouse sobre um ponto para ver um tooltip com a data e o valor correspondente. Um duplo clique em uma linha da sub-aba "Fundamentos" (aba "Análise Geral") usa o ticker daquela linha e ativa esta sub-aba. O preenchimento é preguiçoso, ocorrendo apenas quando a sub-aba é selecionada.

### Sub-aba: Documentos

- **Objetivo:** Navegar e inspecionar os documentos já baixados e mantidos no cache local para o ticker selecionado, com resumo automático por I.A.
- **Responde a pergunta:** _Quais documentos deste ativo eu já tenho em cache e o que há dentro deles?_
- **Layout do painel:** Painel dividido horizontalmente (`PanedWindow`), com barra de controles no topo:
  ```
  ┌───────────────────────────────────────────────────────────────┐
  │  [Atualizar] [Abrir documento] [I.A.]                         │
  ├──────────────────────────────┬────────────────────────────────┤
  │  Árvore de documentos        │  Pré-visualização              │
  │  ticker → ano → mês →        │  (campo somente-leitura)       │
  │  categoria → arquivos        │                                │
  └──────────────────────────────┴────────────────────────────────┘
  ```
- **Barra de controles:**
  - **"Atualizar":** re-varre o cache do ticker, aciona a aquisição de novos documentos quando aplicável e remonta a árvore.
  - **"Abrir documento":** abre o arquivo selecionado no aplicativo padrão (PDF no leitor de PDFs, HTML no navegador). Permanece desabilitado enquanto nenhum arquivo (ou uma pasta) estiver selecionado.
  - **"I.A.":** abre o diálogo de configuração do provedor de LLM (preset, chave de API, RPM e teste de conexão). Disponível mesmo sem documentos ou ticker selecionado.
- **Árvore hierárquica:** o nome do ticker no topo e, abaixo, os níveis de ano, mês e categoria, e por fim os arquivos. Pastas expandem e recolhem com duplo clique; somente arquivos abrem. Categorias incluem Aviso aos Acionistas (PDFs de BDR), Informe Mensal (HTML) e, para documentos relevantes, a subpasta de categoria (Assembleia, Comunicado ao Mercado, Fato Relevante, Relatorio).
- **Lista Markdown do agrupamento:** ao selecionar um agrupamento (ticker, ano, mês ou categoria), o campo de texto exibe uma lista em Markdown com os documentos contidos, usando o agrupamento como cabeçalho (`#`) e cada sub-agrupamento com um nível a mais (`##`, `###`, …). Cada documento aparece como item de lista seguido do seu resumo curto (`short_summary`).
- **Pré-visualização do documento:** ao selecionar um arquivo, o texto é extraído sob demanda (HTML derivado do HTML, PDF via `pypdf`) e exibido ao lado da árvore. Com resumo longo (`long_summary`) preenchido, a caixa exibe o resumo, seguido de linha em branco, `---`, linha em branco e o texto integral. Sem resumo e com a LLM configurada, os resumos curto e longo são gerados (fórmula XYZ), persistidos e exibidos; sem LLM configurada/funcional, é exibida a mensagem de indisponibilidade. Arquivos sem texto extraível mostram mensagem informativa.
- **Resumos com I.A.:** o resumo curto tem até 280 caracteres e o longo até 1.500. São persistidos em `~/.cache/flowscope/document-summaries/{TICKER}.json` (um JSON por ticker, escrita atômica) e reaproveitados nas próximas aberturas. A geração ocorre fora da thread da interface, com estado de carregamento ("Gerando resumo…"); resultados de seleções anteriores são descartados quando a seleção muda. Enquanto o provedor for `none`, nenhuma chamada de rede é realizada.
- **Interação e cópia:** duplo clique, Enter ou o botão "Abrir documento" abrem o arquivo. O campo é somente-leitura, mas aceita `Ctrl+A`, `Ctrl+C`, `Shift+setas` e navegação, com cursor de foco. O botão "Copiar Dados" copia o conteúdo do campo de texto nesta sub-aba (habilitado mesmo sem dados da B3 carregados).
- **Persistência da configuração de I.A.:** "Salvar" no diálogo grava o bloco `llm.chat` em `~/.flowscope/config.json` e fecha o diálogo; a configuração sobrevive ao fechamento da aplicação e reaparece preenchida na próxima abertura.
- **Estado vazio:** ticker sem documentos em cache exibe mensagem informativa; nenhum ticker selecionado exibe "Selecione um ticker".

### Sub-aba: Participação Institucional 🔒

- **Status:** Placeholder — sub-aba desabilitada (implementação futura).
- **Objetivo:** Estimar o perfil dos participantes do pregão (institucional vs. varejo) com base no tamanho médio das negociações.
- **Responde a pergunta:** _Quem parece estar negociando? Grandes participantes ou varejo?_
- **Indicadores envolvidos:**
  - `Average Trade Size` — Quantidade média de ações por negócio
  - `Average Financial Ticket` — Valor financeiro médio por negócio

### Sub-aba: Eficiência do Movimento 🔒

- **Status:** Placeholder — sub-aba desabilitada (implementação futura).
- **Objetivo:** Medir se o range do dia resultou em deslocamento efetivo do preço ou foi apenas ruído (oscilação sem direção).
- **Responde a pergunta:** _O mercado caminhou com convicção ou apenas oscilou?_
- **Indicadores envolvidos:**
  - `Daily Efficiency` — `|Fechamento − Preço Médio| / Range`

### Sub-aba: Resumo Geral 🔒

- **Status:** Placeholder — sub-aba desabilitada (implementação futura).
- **Objetivo:** Consolidar todos os indicadores disponíveis em uma única visualização para o ticker selecionado.
- **Responde a pergunta:** _O que realmente aconteceu neste ativo? Quem parece estar negociando? Grandes participantes ou varejo?_
- **Indicadores envolvidos:**
  - **Preço:** Range, Range%, Typical Price, Median Price, Weighted Close
  - **Fluxo:** CLV, Money Flow Multiplier, Money Flow Volume, Buying Pressure, Selling Pressure
  - **Tamanho:** Average Trade Size, Average Financial Ticket
  - **Eficiência:** Daily Efficiency, Dominance Score
  - **Densidade:** Financial Density, Trade Density, Volume Density
  - **Adicionais:** VWAP Distance, VWAP do período, Money Flow Volume acumulado

---

## Aba Principal: "Chat AI"

- **Objetivo:** Responder perguntas em linguagem natural sobre a watchlist, os documentos em cache e o próprio FlowScope, sem sair da interface.
- **Responde a pergunta:** _O que você pode me dizer sobre esses ativos, os documentos que baixei e o próprio FlowScope?_
- **Posição:** aba de topo única e sempre visível, entre "Análise do Ticker" e "Sobre".
- **ChatPanel:** widget `ChatPanel(tkinter.Frame)` sem seletor de escopo. O contexto cobre sempre a watchlist completa; a LLM infere o ticker referido na pergunta (e pede esclarecimento quando ela for ambígua).
- **Contexto enviado à LLM (em cascata):**
  - **Conhecimento do FlowScope:** apresentação, licença, versão e os textos de orientação das sub-abas (aba "Sobre" + `TAB_CONTENT`), enviados como bloco de sistema estável.
  - **Fundamentos carregados:** tabela de fundamentos serializada de forma compacta, uma linha por ticker da watchlist completa.
  - **Documentos:** resumos curtos e longos dos documentos em cache da watchlist. Quando a resposta exige mais detalhe, a LLM devolve as chaves dos documentos-alvo e o texto integral é lido.
  - **Fontes adicionais:** ponto de extensão renderizado como seção própria. Os itens da sub-aba "Notícias" em cache entram por esse ponto como "Notícias e informações regulatórias da B3" (categoria, título, data e resumo/texto), com teto próprio de 12.000 caracteres e sem filtro por ticker na montagem — a LLM seleciona os itens relacionados ao ticker inferido da pergunta. Evoluções futuras (recuperação vetorial em `llm-chat-rag`) também usam o ponto. Falha ou ausência de conteúdo é omitida sem impedir a resposta.
- **Cascata em até duas chamadas:** a primeira usa os resumos; a segunda só ocorre quando a LLM pede o texto integral de documentos-alvo. A leitura é interrompida assim que houver resposta.
- **Confirmação por quantidade:** até 3 documentos-alvo prossegue automaticamente; de 4 a 7 lista os nomes; com 8 ou mais informa a quantidade e pede confirmação antes de ler o texto integral.
- **Orçamento de contexto:** teto por documento (12.000 caracteres) e global (40.000 caracteres); o excedente é truncado com aviso no log.
- **Histórico multi-turno:** cada pergunta é enviada com os turnos anteriores bem-sucedidos (usuário e assistente), em ordem, antecedendo a pergunta atual; as duas chamadas da cascata compartilham o mesmo histórico. O histórico tem teto de 10 mensagens e 8.000 caracteres, descartando os turnos mais antigos; erros e avisos não entram no histórico. O botão "Limpar" reinicia também esse histórico.
- **Sessão não persistente:** a aba começa limpa e não persiste histórico.
- **Interação:**
  - O campo de respostas é somente-leitura, com cursor, seleção, `Ctrl+A` e `Ctrl+C`; a entrada aceita colar livremente. `Enter` envia a pergunta; `Shift+Enter` quebra linha.
  - O cabeçalho tem os botões **"Limpar"**, **"Copiar chat"** e **"Configuração"**, este sempre visível logo após "Copiar chat". O botão "Copiar Dados" também copia o chat quando esta aba está ativa.
  - O botão **"Limpar"**, antes de "Copiar chat", reinicia a conversa como se estivesse começando agora; um pedido de confirmação (Sim/Não) é exibido antes de limpar, e a conversa permanece inalterada se o usuário recusar.
  - O rodapé tem o botão **"Enviar"** e, ao lado, um botão de cancelamento com o ícone `process-stop.png`, habilitado somente enquanto há um envio em processamento. Acioná-lo interrompe o envio de forma cooperativa, reabilita o "Enviar" e exibe "Envio cancelado." na barra de status; o desfecho tardio do provedor é descartado e não entra na conversa.
  - **Estado dos botões:** "Enviar" só habilita com a LLM configurada **e** com fundamentos carregados pela análise (reavaliado quando os dados chegam com a aba aberta). "Limpar" e "Copiar chat" só habilitam com conteúdo textual na conversa. Durante o envio, "Limpar", "Copiar chat" e "Configuração" ficam desabilitados e voltam ao normal ao término (resposta, erro ou cancelamento).
- **Orientação:** com a aba ativa, o quadro de texto orientativo exibe a orientação da aba "Chat AI" (objetivo, requisitos, contexto enviado e uso dos botões), proveniente de `TAB_CONTENT` — que também integra o bloco de conhecimento do FlowScope enviado à LLM.
- **Estado não configurado:** sem provedor `llm.chat` (ou com provedor `none`), a aba permanece visível, com a entrada desabilitada e orientação de configuração; a "Configuração" abre o diálogo da `llm-core`. Ao salvar, o estado é reavaliado.
- **Erros:** falhas da LLM aparecem na barra de status com mensagem amigável e são registradas no log.

---

## Aba Principal: "Sobre"

- **Objetivo:** Apresentar o FlowScope, a versão e a data de release em uso, a licença de software livre e os atalhos para o repositório e o log da aplicação.
- **Posição:** aba de topo, após "Chat AI".
- **Conteúdo:** apresentação do projeto, versão, data de release, licença (GNU GPLv3), endereço do repositório, botões "Repositório no GitHub" e "Abrir log da aplicação" e, quando houver, o aviso de nova versão disponível com atalho para a release.
- **Orientação:** com a aba ativa, o quadro de texto orientativo exibe a orientação da aba "Sobre" (objetivo, conteúdo e uso dos atalhos), proveniente de `TAB_CONTENT` — que também integra o bloco de conhecimento do FlowScope enviado à LLM.

---

## Painel Lateral Direito

### Filtro de Tickers (TickerList)

- **Componente:** `tk.Text` (modo edição) / `tk.Listbox` com `exportselection=False` (modo visualização)
- **Descrição:** Alterna entre edição (Text) e seleção múltipla (Listbox) via toggle "Editar lista de tickers". Permite salvar/carregar listas de arquivos `.txt`.
- **Objetivo:** Controlar quais tickers são exibidos nos gráficos e análises. Funciona como uma "carteira" ou "watchlist". A seleção no Listbox também determina o ticker analisado na aba "Análise do Ticker".
- **Funcionalidades:**
  - **Modo edição:** Texto multilinha, um ticker por linha. Duplo clique isola um ticker. Clique direito → menu de contexto (copiar, remover, selecionar todos, limpar).
  - **Modo visualização:** Listbox com seleção múltipla (`EXTENDED`). Ctrl+Click e Shift+Click para selecionar múltiplos tickers.
  - Botões "Selecionar Todos" e "Desmarcar Todos" na barra superior (visíveis apenas no modo visualização).
  - Botão "Salvar Tickers" → exporta a lista atual para arquivo.
  - Botão "Carregar Tickers" → importa lista de arquivo.
  - Se nenhum ticker for fornecido, o programa carrega automaticamente a carteira IDIV (Índice Dividendos) da B3.

### Painel de Orientação (OrientationPanel)

- **Componente:** `tk.Text` somente leitura com título
- **Descrição:** Exibe texto de ajuda contextual que se atualiza conforme o usuário navega entre abas e sub-abas.
- **Objetivo:** Guiar o usuário na interpretação do painel ativo, explicando o objetivo, os indicadores envolvidos e como interpretar os resultados.
- **Conteúdo:** Dinâmico — muda automaticamente ao selecionar uma sub-aba ou aba de topo diferente, incluindo as abas **"Chat AI"** e **"Sobre"**.

---

## Barra de Status

- **Componente:** `tk.Label` com `relief=SUNKEN`
- **Descrição:** Exibe mensagens de status, contagens e indicadores de progresso.
- **Objetivo:** Informar o usuário sobre o estado atual do programa (pronto, carregando, erros, confirmações).
- **Mensagens típicas:**
  - "Pronto. Selecione uma data e clique em Carregar."
  - "Carregando..." (com animação de pontos durante o carregamento)
  - "✓ 45 tickers carregados para 2025-06-15."
  - "✓ Dados copiados!"
  - "⚠ Não foi possível carregar os dados. ..."
