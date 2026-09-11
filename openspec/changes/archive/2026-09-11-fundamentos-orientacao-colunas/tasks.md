## 1. Atualizar o texto de orientação da sub-aba Fundamentos

- [x] 1.1 Reescrever o campo "Indicadores envolvidos" da entrada `("Análise Geral", "Fundamentos")` em `src/flowscope/presentation/gui/app_tabs.py` para descrever todas as colunas exibidas — identidade, P (Cotação), Preço Típico, P / PT, VP (VP/Cota), P/VP, P/L, Dividend Yield, dividendos e tendências, FFO Yield, Dividend Payout (DY/FFOY), FFO Trend, P/FFO, cotistas/acionistas, patrimônio e as colunas finais Informações adicionais e Dados fiscais; verificar lendo `TAB_CONTENT[("Análise Geral", "Fundamentos")]`
- [x] 1.2 Ampliar o campo "Como interpretar" com orientações sucintas sobre Preço Típico e P / PT (desconto/prêmio frente ao preço médio de 52 semanas), Dividend Payout (DY/FFOY), Informações adicionais (LPA/ROE/ROIC em ações; imóveis, Cap Rate, Vacância Média e indexadores em FIIs) e Dados fiscais (CNPJ; administrador e gestor em FIIs); verificar lendo o corpo de orientação
- [x] 1.3 Confirmar que a ordem dos campos permanece Objetivo → Responde a pergunta → Indicadores envolvidos → Como interpretar e que os cabeçalhos seguem em negrito com a pergunta em itálico; verificar inspecionando a lista de tuplas de `TAB_CONTENT`

## 2. Testes de apresentação

- [x] 2.1 Estender `TestWiringSubAba` em `tests/test_presentation/test_fundamental_table.py` com asserções de que o texto de orientação menciona Preço Típico, P / PT, Dividend Payout, Informações adicionais e Dados fiscais; verificar com `pytest tests/test_presentation/test_fundamental_table.py -k TestWiringSubAba`
- [x] 2.2 Manter/ajustar as asserções existentes sobre "último dividendo" e "acionistas"; verificar que os testes passam

## 3. Verificação final

- [x] 3.1 Rodar `ruff check` e a suíte afetada (`pytest tests/test_presentation`) sem regressões
- [x] 3.2 Validar a change com `openspec validate fundamentos-orientacao-colunas --strict`
- [x] 3.3 Atualizar `panels.md` para refletir o mesmo conteúdo de orientação da sub-aba Fundamentos, se aplicável

## 4. Correção da descrição de Tipo e Sub-tipo

- [x] 4.1 Corrigir o campo "Identidade" em `app_tabs.py` e `panels.md` para refletir o Tipo (`Papel`/`FII`) e o Sub-tipo implementados (prefixo `Tijolo:`/`Papel:` + segmento e gestão; espécie/setor/subsetor; fallback determinístico)
- [x] 4.2 Atualizar o spec delta (`gui-interface`) e os testes de apresentação; verificar com `pytest tests/test_presentation/test_fundamental_table.py -k TestWiringSubAba`
