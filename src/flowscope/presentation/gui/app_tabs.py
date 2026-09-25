"""Dados das abas e textos de orientação da interface gráfica do FlowScope."""

#: Texto da aba de nível superior com informações institucionais.
ABOUT_TAB = "Sobre"

#: Texto da aba de nível superior de chat com I.A.
CHAT_AI_TAB = "Chat AI"

TAB_CONFIGS = [
    ("Evolução dos Fundamentos", "cotacao", "vp_cota", "p_vp", "dividend_yield",
     "ultimo_dividendo", "cotistas", "cotas", "shorts_pct"),
    ("Evolução da Dominância", "clv", "daily_efficiency", "dominance_score", "daily_money_flow"),
    ("Amplitude de Preço", "range", "range_percentual", "typical_price", "median_price", "weighted_close"),
    ("Fluxo Financeiro", "clv", "money_flow_multiplier", "money_flow_volume",
     "buying_pressure", "selling_pressure", "vwap_distance"),
    ("Participação Institucional", "average_trade_size", "average_financial_ticket"),
    ("Eficiência do Movimento", "daily_efficiency"),
    ("Resumo Geral", None),
    ("Documentos", None),
]

ENABLED_TABS = {
    "Evolução da Dominância",
    "Amplitude de Preço",
    "Fluxo Financeiro",
    "Evolução dos Fundamentos",
    "Documentos",
}

TAB_CONTENT = {
    (ABOUT_TAB, ABOUT_TAB): (
        "Sobre — Informações do FlowScope",
        [
            ("Objetivo: ", "bold"),
            ("Apresentar o FlowScope, a versão e a data de release em uso, a licença de software livre e os atalhos para o repositório e para o log da aplicação.\n\n", ""),
            ("Responde a pergunta: ", "bold"),
            ("\"O que é o FlowScope, qual a versão que estou usando e onde encontro o código e o log?\"\n\n", "italic"),
            ("Conteúdo: ", "bold"),
            (("• Apresentação do projeto: ferramenta open source de análise quantitativa de fluxo de ordens sobre dados públicos da B3, com interface gráfica e linha de comando;\n"
              "• Versão e data de release, licença (GNU GPLv3) e endereço do repositório oficial;\n"
              "• Aviso de nova versão disponível, quando houver, com atalho para a página da release.\n\n"), ""),
            ("Como interpretar: ", "bold"),
            (("Use \"Repositório no GitHub\" para abrir o código-fonte no navegador e \"Abrir log da aplicação\" para inspecionar o arquivo de log. "
              "As mesmas informações institucionais compõem o conhecimento do próprio FlowScope usado pela aba \"Chat AI\"."), ""),
        ]
    ),
    (CHAT_AI_TAB, CHAT_AI_TAB): (
        "Chat AI — Conversa sobre a watchlist e os caches",
        [
            ("Objetivo: ", "bold"),
            ("Conversar em linguagem natural com a I.A. sobre os dados já carregados, os documentos e as notícias em cache e o próprio FlowScope.\n\n", ""),
            ("Responde a pergunta: ", "bold"),
            ("\"O que os dados, os documentos e as notícias dizem sobre este ativo?\"\n\n", "italic"),
            ("Como usar: ", "bold"),
            (("O campo de envio só é habilitado quando a LLM está configurada em \"Configuração\" e há fundamentos carregados pela análise. "
              "Não há seletor de escopo: o contexto cobre a watchlist completa e a I.A. identifica o ticker referido na pergunta, "
              "pedindo esclarecimento quando ela for ambígua.\n\n"), ""),
            ("Contexto enviado: ", "bold"),
            (("• Conhecimento do próprio FlowScope (orientações das sub-abas e informações da aba \"Sobre\");\n"
              "• Fundamentos da watchlist carregada;\n"
              "• Documentos em cache, lidos em cascata (resumos curtos e longos e, se necessário, o texto integral dos alvos);\n"
              "• Notícias e informações regulatórias da sub-aba \"Notícias\", quando houver cache do período.\n\n"), ""),
            ("Como interpretar: ", "bold"),
            (("Pressione Enter para enviar (Shift+Enter quebra a linha). Enquanto a I.A. responde, o botão ao lado de \"Enviar\" cancela o envio "
              "e a conversa guarda o histórico dos turnos anteriores. \"Limpar\" reinicia a conversa mediante confirmação; \"Copiar chat\" copia o "
              "texto exibido; \"Configuração\" abre o mesmo diálogo de LLM da sub-aba \"Documentos\". Se a resposta exigir ler o texto integral de "
              "vários documentos, o FlowScope pede confirmação antes de prosseguir."), ""),
        ]
    ),
    ("Análise Geral", "VWAP"): (
        "VWAP — Volume Weighted Average Price",
        [
            ("Objetivo: ", "bold"),
            ("Identificar o preço médio ponderado pelo volume negociado no período, revelando o valor justo da ação sob a ótica do fluxo de ordens.\n\n", ""),
            ("Responde a pergunta: ", "bold"),
            ("\"Quem está acima do preço justo e quem está abaixo?\"\n\n", "italic"),
            ("Indicadores envolvidos: ", "bold"),
            ("VWAP (preço médio ponderado), volume por bucket de preço (volume profile), preço de fechamento (LastPric), preço mínimo e máximo (MinPric, MaxPric).\n\n", ""),
            ("Como interpretar: ", "bold"),
            (("O VWAP é a referência de preço justo do período. Negociações acima do VWAP indicam viés comprador; abaixo, viés vendedor. "
             "A largura do violino mostra em quais faixas de preço houve maior concentração de volume. "
             "O último preço (losango vermelho) em relação ao VWAP indica se o fechamento reforça ou contradiz a tendência do período."), ""),
        ]
    ),
    ("Análise Geral", "Quadrantes"): (
        "Quadrantes — CLV vs VWAP Distance",
        [
            ("Objetivo: ", "bold"),
            (("Classificar ativos em quatro quadrantes com base no CLV (eixo X) e no desvio do VWAP (eixo Y), "
             "revelando a interação entre fluxo comprador/vendedor e posição relativa ao preço justo.\n\n"), ""),
            ("Responde a pergunta: ", "bold"),
            ("\"Quem dominou o fechamento? O preço terminou acima ou abaixo do valor justo? Quanto volume financeiro sustentou esse comportamento?\"\n\n", "italic"),
            ("Indicadores envolvidos: ", "bold"),
            (("CLV (Close Location Value), VWAP Distance (desvio percentual do último preço "
             "em relação ao VWAP diário), Volume (FinInstrmQty como tamanho da bolha).\n\n"), ""),
            ("Como interpretar:\n", "bold"),
            (("• Q1 (CLV > 0, acima do VWAP): compra forte confirmada — fechamento na metade superior do range e acima do VWAP.\n"
             "• Q2 (CLV < 0, acima do VWAP): venda relativa — ativo acima do VWAP mas perdeu força no fechamento (possível realização).\n"
             "• Q3 (CLV < 0, abaixo do VWAP): venda forte confirmada — vendedores dominaram o dia.\n"
             "• Q4 (CLV > 0, abaixo do VWAP): compra em desconto — reação compradora insuficiente para recuperar o VWAP.\n\n"
             "As setas cinzas mostram a trajetória dos dias anteriores, evidenciando a evolução temporal de cada ativo."), ""),
        ]
    ),
    ("Análise Geral", "Dominância do Pregão"): (
        "Dominância do Pregão — Ranking de Tickers por CLV",
        [
            ("Objetivo: ", "bold"),
            ("Visualizar rapidamente quais ativos tiveram dominância compradora ou vendedora no último pregão.\n\n", ""),
            ("Responde a pergunta: ", "bold"),
            ("\"Quem venceu a disputa diária pelo preço?\"\n\n", "italic"),
            ("Indicadores envolvidos: ", "bold"),
            ("CLV (Close Location Value) para direção/intensidade, Money Flow Volume (MFV) para capital envolvido.\n\n", ""),
            ("Como interpretar: ", "bold"),
            (("Barras para a direita indicam dominância compradora (CLV positivo); para a esquerda, vendedora (CLV negativo). "
             "Quanto maior o comprimento, mais intensa a dominância. O traço horizontal sobre a barra representa o volume financeiro que sustentou o movimento. "
             "Passe o mouse sobre as barras para ver detalhes do ticker."), ""),
        ]
    ),
    ("Análise Geral", "Rede de Correlação"): (
        "Rede de Correlação — Topologia de Correlação e Cointegração",
        [
            ("Objetivo: ", "bold"),
            ("Revelar a topologia da carteira — quem se agrupa com quem — distinguindo o co-movimento de curto prazo (correlação) do vínculo de equilíbrio de longo prazo (cointegração do spread), em vez de uma matriz N×N ilegível.\n\n", ""),
            ("Responde a pergunta: ", "bold"),
            ("\"Quais papéis se movem juntos e quais mantêm uma relação de equilíbrio no tempo?\"\n\n", "italic"),
            ("Indicadores envolvidos: ", "bold"),
            (("• Correlação assinada dos retornos entre observações consecutivas;\n"
             "• Cointegração par-a-par (Engle-Granger + ADF), com defasagem por BIC;\n"
             "• Meia-vida de reversão do spread;\n"
             "• Comunidades, centralidade (grau) e modularidade da rede.\n\n"), ""),
            ("Como interpretar: ", "bold"),
            (("Cada nó é um ticker e cada aresta um par com relação relevante. A cor da aresta representa a correlação de curto prazo, em escala divergente fixa de −1 a +1 (azul para correlação negativa, vermelho para positiva), com colorbar. "
             "O estilo e a espessura da aresta representam a cointegração de longo prazo: traço sólido e grosso quando o par é cointegrado; tracejado e fino caso contrário. "
             "A cor do nó representa a comunidade (cluster) e o tamanho representa a centralidade (grau) do papel na rede. Só entram arestas com |correlação| acima do limiar ou pares cointegrados, evitando grafos densos demais.\n\n"
             "A rede é calculada sobre os dados já carregados, conforme o período e a amostragem dos combos globais, restrita aos tickers selecionados; um seletor de janela próprio não é necessário. Mudar período ou amostragem recalcula a rede.\n\n"
             "Gates de densidade: a correlação exige ao menos 30 observações alinhadas e a cointegração, no mínimo 40. Com menos de 30 o painel fica vazio; entre 30 e 39 exibe apenas as arestas de correlação e avisa que a cointegração requer 40. "
             "A amostragem esparsa da B3 (Fibonacci) cria intervalos irregulares: o diagnóstico no topo informa o número de observações, o período coberto e os gaps mínimo/mediana/máximo em dias úteis. A cointegração é um indício exploratório sob espaçamento irregular; para densificar a grade, use \"Todos os dias\" com um período maior. O resultado do Engle-Granger é direcional (a direção da regressão é fixada pela ordem alfabética dos tickers) e, com muitos pares, alguns falsos positivos são esperados."), ""),
        ]
    ),
    ("Análise Geral", "Fundamentos"): (
        "Fundamentos — Métricas Fundamentalistas e Dividendos",
        [
            ("Objetivo: ", "bold"),
            ("Consolidar, por ticker da watchlist, a identidade, a classificação, os dividendos, o P/L, o número de cotistas/acionistas e — para FIIs elegíveis — as métricas fundamentalistas de FFO.\n\n", ""),
            ("Responde a pergunta: ", "bold"),
            ("\"Quais ativos estão na carteira, que tipo são e quão barato ou caro está o ativo frente ao lucro (ou último dividendo), ao FFO e ao patrimônio?\"\n\n", "italic"),
            ("Indicadores envolvidos: ", "bold"),
            (("• Identidade: ticker, nome, tipo (`Papel` para ações, ETFs e BDRs; `FII`) e sub-tipo (FII: prefixo `Tijolo:`/`Papel:` seguido de segmento e gestão; Papel: espécie, setor e subsetor; sem dados do Fundamentus, usa os rótulos determinísticos tijolo/papel/híbrido/fiagro/fiinfra ou ordinária/preferencial/ETF);\n"
             "• Cotação e valor: P (Cotação), Preço Típico (média de 52 semanas), P / PT (desconto/prêmio da cotação frente ao preço típico), VP (VP/Cota) e P/VP;\n"
             "• P/L: para ações, o indicador reportado pela fonte; para FIIs, a cotação dividida pelo último dividendo anualizado (× 12), em anos;\n"
             "• Dividendos: Dividend Yield, última data-com, último dividendo (Rendimento), dividendo anterior e tendência do dividendo (último vs. anterior em cinco faixas);\n"
             "• Short interest: Shorts% (ações alugadas ÷ free float, em percentual com uma casa decimal), Volume de Shorts (classificação do Shorts%: Inexistente para 0%/N/A, Muito Baixo < 1%, Baixo < 3%, Alto ≤ 10% e Muito Alto > 10%), Fechamento Shorts (SIR, ações alugadas ÷ volume médio diário de negociação, em dias com uma casa decimal e sufixo `d`) e Risco Fechamento (classificação do SIR: Inexistente para 0/N/A, Muito Baixo < 2, Baixo < 4, Alto ≤ 5 e Muito Alto > 5);\n"
             "• Métricas FFO (apenas FII): FFO/Receita (12m e 3m), FFO Trend, Dividendos/Receita (12m e 3m) e Dividendos/FFO (12m e 3m), em percentual com uma casa decimal;\n"
             "• Cotas e cotistas: quantidade de cotas/ações emitidas, número de cotistas do FII ou quantidade de acionistas da companhia (CVM), suas classificações, patrimônio e data de referência;\n"
             "• Informações adicionais: LPA, ROE e ROIC (ação); Qtd Imóveis, Cap Rate, Vacância Média e percentuais por indexador (FII); Guidance (valor ou faixa por cota e período de validade) quando presente no cache do FII;\n"
             "• Dados fiscais: CNPJ e, para FIIs, administrador e gestor.\n\n"), ""),
            ("Como interpretar: ", "bold"),
            (("O P/L de um FII anualiza o último dividendo mensal (preço ÷ (último dividendo × 12)) para expressar a quantidade de anos, enquanto o P/L de uma ação é o lucro reportado pela fonte; "
             "N/A indica ausência do dado. O Preço Típico é a referência de preço médio de 52 semanas ((máxima + mínima + cotação) / 3); o P / PT expressa o desconto (negativo) ou prêmio (positivo) da cotação frente a esse preço típico. "
             "O FFO/Receita indica quanto da receita vira caixa operacional; o Dividendos/Receita, quanto da receita é destinado a dividendos; e o Dividendos/FFO, quanto do caixa operacional é consumido pelos dividendos (abaixo de 100% o FFO cobre os dividendos, acima de 100% os dividendos superam o FFO e negativo o FFO foi negativo no período). "
             "O Shorts% expressa a magnitude relativa da aposta baixista sobre o free float (para FIIs, sobre o total de cotas, na ausência de free float); o Fechamento Shorts expressa a dificuldade operacional de fechamento em dias, com valores acima de 5 considerados altos. "
             "O número de cotistas de FIIs vem do informe mensal e o de ações, da quantidade de acionistas publicada pela CVM. "
             "A quantidade de cotas emitidas de um FII vem da B3/CVM (fonte mais precisa), com o Fundamentus como fallback; a de ações vem do Fundamentus (`Nro. Ações`) e dimensiona o tamanho da companhia. "
             "O FFO Trend compara FFO/Receita (3m) com FFO/Receita (12m) em pontos percentuais, com os rótulos Forte Alta (≥ +20 p.p.), Leve Alta (≥ +5 p.p.), Estável, Leve Queda (≥ −20 p.p.) e Forte Queda (< −20 p.p.); a tendência do dividendo usa os rótulos Forte Alta (≥ +5%), Leve Alta, Estável, Leve Queda e Forte Queda (≤ −5%). "
             "Ativos do tipo Papel exibem N/A nas colunas de razões sobre a receita. O P/VP compara o valor de mercado "
             "com o patrimônio líquido; valores de P/VP abaixo de 1 indicam cota negociando abaixo do patrimônio. "
             "Informações adicionais reúnem indicadores do ativo (LPA, ROE e ROIC em ações; imóveis, Cap Rate, Vacância Média, percentuais por indexador e o guidance de distribuição quando disponível no cache em FIIs) e "
             "Dados fiscais reúnem o CNPJ e, para FIIs, o administrador e o gestor; itens sem dado em nenhuma fonte são omitidos. "
             "Os valores são calculados com precisão decimal completa e arredondados somente na apresentação."), ""),
        ]
    ),
    ("Análise Geral", "Notícias"): (
        "Notícias — Plantão B3",
        [
            ("Objetivo: ", "bold"),
            ("Navegar pelas notícias do Plantão B3 do período, baixar o corpo dos artigos e resumi-los com I.A.\n\n", ""),
            ("Responde a pergunta: ", "bold"),
            ("\"O que foi publicado no mercado no período e o que isso significa?\"\n\n", "italic"),
            ("Indicadores envolvidos: ", "bold"),
            (("• Árvore por ano → mês → agência → artigos;\n"
             "• Pré-visualização do texto do artigo extraído do HTML em cache;\n"
             "• Resumo curto e longo gerados pela LLM a partir do texto.\n\n"), ""),
            ("Como interpretar: ", "bold"),
            (("Use \"Atualizar\" para baixar o corpo dos artigos do período; a aquisição roda em segundo plano com "
             "progresso e pode ser interrompida. Selecione um artigo para ver o resumo e o texto extraído. Use \"Abrir\" "
             "para abrir a notícia no navegador e \"Resumir pendentes\" para gerar em lote os resumos que faltam. "
             "As notícias também são oferecidas como fonte adicional de contexto na aba \"Chat AI\"."), ""),
        ]
    ),
    ("Análise do Ticker", "Evolução da Dominância"): (
        "Evolução da Dominância — Histórico de CLV por Pregão",
        [
            ("Objetivo: ", "bold"),
            ("Visualizar a evolução temporal da dominância compradora/vendedora para o ticker selecionado.\n\n", ""),
            ("Responde a pergunta: ", "bold"),
            ("\"Quem venceu a disputa diária pelo preço?\"\n\n", "italic"),
            ("Indicadores envolvidos: ", "bold"),
            ("CLV (Close Location Value) nas barras, Daily Money Flow (traço horizontal sobre a barra).\n\n", ""),
            ("Como interpretar: ", "bold"),
            (("Cada barra representa um pregão. Direita = compradores dominaram; Esquerda = vendedores dominaram. "
             "O traço horizontal indica o fluxo financeiro diário. Passe o mouse sobre as barras para ver detalhes da dominância e convicção do movimento."), ""),
        ]
    ),
    ("Análise do Ticker", "Amplitude de Preço"): (
        "Amplitude de Preço — Painel Visual",
        [
            ("Objetivo: ", "bold"),
            (("Analisar se o preço apenas oscilou ou houve um movimento direcional convincente durante o pregão, "
             "mostrando como a posição do fechamento dentro do range evoluiu nos últimos dias.\n\n"), ""),
            ("Responde a pergunta: ", "bold"),
            ("\"Onde o preço andou (trajetória)? Quanto andou (amplitude)? Andou com convicção (eficiência)?\"\n\n", "italic"),
            ("Indicadores envolvidos:\n", "bold"),
            (("• Trajetória: onde o preço se posicionou dentro da faixa do dia (0%=perto do preço mínimo, "
             "100%=perto do preço máximo), acompanhado dos marcadores ● (preço de fechamento, no tamanho da amplitude), "
             "M (Median), T (Typical), V (VWAP) e W (Weighted Close);\n"
             "• Amplitude: quanto o preço oscilou, em percentual do preço médio (pequeno=pouco, grande=muito);\n"
             "• Eficiência: o movimento teve convicção ou foi ruído (0%=muito ruído, 100%=muita convicção);\n"
             "• CLV: Close Location Value, indicando pressão vendedora (negativo) ou compradora (positivo);\n"
             "• Classificação do pregão: \"Pregão Lateral\" (Amplitude Relativa ≤ mediana histórica e Eficiência ≤ 0,30), "
             "\"Volatilidade sem Direção\" (Amplitude Relativa > mediana e Eficiência ≤ 0,30), "
             "\"Movimento Consistente\" (Amplitude Relativa ≤ mediana e Eficiência > 0,30) e "
             "\"Movimento Direcional Forte\" (Amplitude Relativa > mediana e Eficiência > 0,30).\n\n"), ""),
            ("Como interpretar: ", "bold"),
            (("Uma Amplitude elevada indica maior volatilidade, mas não significa necessariamente uma tendência forte. "
             "A Eficiência elevada mostra que a oscilação foi convertida em avanço efetivo, sugerindo convicção. "
             "Um CLV próximo de +1 indica fechamento perto da máxima (pressão compradora); próximo de -1, perto da mínima "
             "(pressão vendedora). Dias com barra de fundo verde consecutiva = sequência direcional forte.\n\n"
             "Classificações:\n"
             "• \"Pregão Lateral\": amplitude baixa e eficiência baixa — o preço andou pouco e sem convicção. "
             "Indecisão total, mercado sem direção.\n"
             "• \"Volatilidade sem Direção\": amplitude alta e eficiência baixa — o preço oscilou muito mas sem rumo. "
             "Mercado nervoso, barulho sem sinal direcional.\n"
             "• \"Movimento Consistente\": amplitude baixa e eficiência alta — movimento eficiente com pouca oscilação. "
             "Compradores ou vendedores agiram com foco e sem dispersão.\n"
             "• \"Movimento Direcional Forte\": amplitude alta e eficiência alta — volatilidade com convicção. "
             "Movimento forte e direcionado, indicando consenso no fluxo de ordens.\n\n"
             "Passe o mouse sobre os marcadores para ver valores detalhados."), ""),
        ]
    ),
    ("Análise do Ticker", "Fluxo Financeiro"): (
        "Fluxo Financeiro — Daily Money Flow",
        [
            ("Objetivo: ", "bold"),
            ("Mostrar se o movimento do preço foi acompanhado por fluxo financeiro suficiente para indicar convicção compradora ou vendedora.\n\n", ""),
            ("Responde a pergunta: ", "bold"),
            ("\"O movimento de hoje foi sustentado por fluxo financeiro?\"\n\n", "italic"),
            ("Indicadores envolvidos: ", "bold"),
            (("• Daily Money Flow (DMF): fluxo líquido do pregão = CLV × Volume Financeiro\n"
             "• Money Flow Volume acumulado: soma do DMF no período\n"
             "• CLV (Close Location Value): posição do fechamento no range\n"
             "• Buying Pressure / Selling Pressure: domínio do range\n"
             "• Score normalizado: DMF / Volume Financeiro (comparável entre ativos)\n"
             "• Range Percentual: amplitude relativa do dia\n\n"), ""),
            ("Como interpretar: ", "bold"),
            (("O DMF é o indicador principal: positivo indica fluxo comprador; negativo, fluxo vendedor. "
             "O score normalizado (DMF / Volume Financeiro) permite comparar a intensidade do fluxo entre ativos de diferentes liquidez. "
             "Um DMF elevado com score > 8% sugere fluxo forte. "
             "O MFV acumulado mostra se a tendência de hoje reforça ou contradiz o fluxo dos dias anteriores. "
             "O CLV (subplot central) indica onde o preço fechou no range. "
             "Buying + Selling Pressure mostram quem dominou o range. "
             "DMF e MFV acumulado são exibidos em milhões de reais."), ""),
        ]
    ),
    ("Análise do Ticker", "Evolução dos Fundamentos"): (
        "Evolução dos Fundamentos — Série Histórica do Cache",
        [
            ("Objetivo: ", "bold"),
            ("Acompanhar como os fundamentos do ticker selecionado evoluíram ao longo das datas já observadas e retidas no cache histórico.\n\n", ""),
            ("Responde a pergunta: ", "bold"),
            ("\"Os fundamentos do ativo melhoraram ou pioraram desde a observação mais antiga do cache?\"\n\n", "italic"),
            ("Indicadores envolvidos: ", "bold"),
            (("• Cotação (R$);\n"
             "• VP — Valor Patrimonial por cota (R$);\n"
             "• P/VP — relação entre preço e valor patrimonial;\n"
             "• Dividend Yield (%);\n"
             "• Último dividendo (R$);\n"
             "• Nº de cotistas (FII) ou acionistas (ação);\n"
             "• Nº de cotas ou ações emitidas;\n"
             "• Shorts% — ações alugadas sobre o free float (ou total emitido), em percentual.\n\n"), ""),
            ("Como interpretar: ", "bold"),
            (("O painel mostra oito mini-gráficos (small multiples), um por indicador, cada um com a sua própria escala para que os valores "
             "não sejam misturados. Em cada gráfico, a linha vai da observação mais antiga (esquerda) para a mais recente (direita), e o ponto "
             "vermelho destaca o valor mais recente do cache. Uma linha subindo indica que o indicador cresceu no período; descendo, que recuou. "
             "O Shorts% expressa a magnitude relativa da aposta baixista sobre o free float (para FIIs, sobre o total de cotas). "
             "Passe o mouse sobre um ponto para ver a data e o valor correspondente.\n\n"
             "As datas exibidas são amostradas a partir da observação mais recente com intervalos que crescem na sequência de Fibonacci "
             "(1, 2, 3, 5, 8, 13, ... dias), ficando mais próximas no presente e mais espaçadas no passado. A data mais antiga e a mais recente "
             "do cache aparecem sempre. A origem dos dados é exclusivamente o cache histórico de fundamentos: só existem pontos para os dias em "
             "que os dados do ticker já foram carregados, portanto alguns indicadores podem ficar constantes ou ter poucos pontos. Quando o ticker "
             "não tem nenhuma observação retida, o painel exibe um aviso de ausência de histórico."), ""),
        ]
    ),
    ("Análise do Ticker", "Documentos"): (
        "Documentos — Arquivos em Cache por Ticker",
        [
            ("Objetivo: ", "bold"),
            ("Navegar e inspecionar os documentos já baixados e mantidos no cache local para o ticker selecionado.\n\n", ""),
            ("Responde a pergunta: ", "bold"),
            ("\"Quais documentos deste ativo eu já tenho em cache e o que há dentro deles?\"\n\n", "italic"),
            ("Indicadores envolvidos: ", "bold"),
            (("• Árvore hierárquica por ticker → ano → mês → categoria → arquivos;\n"
             "• Categorias: Aviso aos Acionistas (PDFs de BDR), Informe Mensal (HTML) e, para documentos relevantes, a subpasta de categoria (Assembleia, Comunicado ao Mercado, Fato Relevante, Relatorio);\n"
             "• Pré-visualização textual do arquivo selecionado, extraída de HTML ou PDF.\n\n"), ""),
            ("Como interpretar: ", "bold"),
            (("Expanda ano, mês e categoria para localizar os arquivos. O nome exibido é o identificador do documento no cache; "
             "a posição na árvore informa a data de referência. Ao selecionar um arquivo, o texto é extraído sob demanda e exibido à direita "
             "(PDFs escaneados podem não ter texto extraível). Dê duplo-clique em um arquivo, pressione Enter ou use o botão \"Abrir\" para "
             "abri-lo no aplicativo padrão — PDF no leitor de PDFs e HTML no navegador. Use \"Atualizar\" para re-varrer o cache do ticker. "
             "Somente a data de referência (caminho) e o id do arquivo identificam o documento; pastas expandem e recolhem, e apenas arquivos abrem."), ""),
        ]
    ),
    ("Análise do Ticker", "Participação Institucional"): (
        "Participação Institucional — Tamanho dos Negócios",
        [
            ("Objetivo: ", "bold"),
            ("Estimar o perfil dos participantes com base no tamanho médio das negociações.\n\n", ""),
            ("Responde a pergunta: ", "bold"),
            ("\"Quem parece estar negociando? Grandes participantes ou varejo?\"\n\n", "italic"),
            ("Indicadores envolvidos: ", "bold"),
            ("Average Trade Size (ações por negócio), Average Financial Ticket (valor por negócio).\n\n", ""),
            ("Como interpretar: ", "bold"),
            (("Tickets médios mais altos sugerem participação institucional (grandes blocos). Tickets baixos sugerem "
             "predomínio de pessoa física. Acompanhar a evolução ao longo dos dias revela mudanças na composição do fluxo."), ""),
        ]
    ),
    ("Análise do Ticker", "Eficiência do Movimento"): (
        "Eficiência do Movimento",
        [
            ("Objetivo: ", "bold"),
            ("Medir quanto do range diário resultou em deslocamento efetivo do preço.\n\n", ""),
            ("Responde a pergunta: ", "bold"),
            ("\"O mercado caminhou com convicção ou apenas oscilou?\"\n\n", "italic"),
            ("Indicadores envolvidos: ", "bold"),
            ("Daily Efficiency = |Fechamento − Preço Médio| / Range.\n\n", ""),
            ("Como interpretar: ", "bold"),
            (("Próximo de 0 → pregão lateral (preço andou mas voltou). Próximo de 1 → movimento direcional "
             "(o range inteiro resultou em deslocamento). Valores baixos indicam indecisão; altos, convicção."), ""),
        ]
    ),
    ("Análise do Ticker", "Resumo Geral"): (
        "Resumo Geral — Todos os Indicadores",
        [
            ("Objetivo: ", "bold"),
            ("Consolidar todos os indicadores do ticker em uma única visualização.\n\n", ""),
            ("Responde a pergunta: ", "bold"),
            ("\"O que realmente aconteceu neste ativo?\"\n\n", "italic"),
            ("Indicadores envolvidos: ", "bold"),
            (("Range, Range%, Typical Price, Median Price, Weighted Close, CLV, "
             "Money Flow Multiplier, Money Flow Volume, Buying/Selling Pressure, Average Trade Size, "
             "Average Financial Ticket, Daily Efficiency, Financial Density, Trade Density, Volume Density.\n\n"), ""),
            ("Como interpretar: ", "bold"),
            (("Use este painel para uma visão panorâmica de todos os indicadores disponíveis "
             "para o ticker selecionado."), ""),
        ]
    ),
}
