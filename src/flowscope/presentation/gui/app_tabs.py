"""Dados das abas e textos de orientação da interface gráfica do FlowScope."""

TAB_CONFIGS = [
    ("Evolução da Dominância", "clv", "daily_efficiency", "dominance_score", "daily_money_flow"),
    ("Amplitude de Preço", "range", "range_percentual", "typical_price", "median_price", "weighted_close"),
    ("Fluxo Financeiro", "clv", "money_flow_multiplier", "money_flow_volume",
     "buying_pressure", "selling_pressure", "vwap_distance"),
    ("Participação Institucional", "average_trade_size", "average_financial_ticket"),
    ("Eficiência do Movimento", "daily_efficiency"),
    ("Resumo Geral", None),
]

ENABLED_TABS = {"Evolução da Dominância", "Amplitude de Preço", "Fluxo Financeiro"}

TAB_CONTENT = {
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
