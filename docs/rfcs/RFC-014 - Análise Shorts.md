# RFC-014: Análise de Short Interest com Dados Oficiais (B3/FINRA)

## 1. Problem (Problema)

Investidores e analistas frequentemente utilizam dados de _short interest_ sem uma metodologia clara para interpretação e hierarquização do risco. No mercado brasileiro e americano, as fontes oficiais (B3 e FINRA) fornecem os dados brutos — quantidade de ações alugadas, estoque de posições em aberto — mas a tradução desses números em métricas acionáveis de risco de fechamento (_short squeeze_) permanece subjetiva e fragmentada.

Os principais problemas são:

- **Fontes dispersas e periodicidade distinta**: A B3 divulga estoque de empréstimos de ativos diariamente , enquanto a FINRA reporta duas vezes por mês, com publicação defasada de aproximadamente 10 a 11 dias .
- **Ausência de um padrão consolidado**: Não há um _framework_ único que combine _Shorts%_, volume absoluto e _Short Interest Ratio_ em uma escala qualitativa de risco.
- **Interpretação equivocada**: Números brutos de ações alugadas, sem normalização pelo _free float_ ou pelo volume negociado, levam a conclusões distorcidas sobre a magnitude real do risco de fechamento.

---

## 2. Root Cause (Causa Raiz)

A causa raiz reside na **natureza dos dados reportados pelas bolsas**: eles são matéria-prima operacional (contratos de empréstimo, posições em aberto), não métricas de sentimento ou risco. A B3 disponibiliza o estoque de empréstimos como parte dos serviços de compensação e liquidação , e a FINRA exige o reporte de _short interest_ como obrigação regulatória de transparência .

Ambas as fontes **não calculam** as métricas derivadas — _Shorts%_, _Short Interest Ratio_ ou classificações de risco. Isso força o analista a:

1. Coletar os dados brutos de fontes primárias (B3/FINRA);
2. Obter o _free float_ e o volume médio de negociação de fontes secundárias (provedores de dados, relatórios de empresas);
3. Construir manualmente os indicadores e as escalas de interpretação.

Sem um _framework_ padronizado, cada analista adota critérios próprios, gerando inconsistência na avaliação do mesmo ativo por diferentes observadores.

---

## 3. Options (Opções)

### Opção A: Utilizar apenas o volume bruto de ações alugadas

- **Prós**: Simples, disponível diretamente nos dados da B3/FINRA.
- **Contras**: Ignora o tamanho da empresa (_free float_) e a liquidez do ativo. Uma empresa com 1 milhão de ações alugadas pode ter risco completamente diferente dependendo do seu porte e volume.

### Opção B: Utilizar apenas o _Shorts%_ (Short Interest como % do Free Float)

- **Prós**: Normaliza pelo tamanho da empresa, permitindo comparação entre ativos.
- **Contras**: Não captura a dimensão de **liquidez**. Uma ação com _Shorts%_ alto mas volume diário altíssimo pode ter baixo risco de _squeeze_.

### Opção C: Utilizar apenas o _Short Interest Ratio_ (Days to Cover)

- **Prós**: Mede diretamente a dificuldade de fechamento, incorporando liquidez.
- **Contras**: Pode ser volátil em ativos com volume irregular; um único dia de volume anormal distorce a métrica.

### Opção D: Combinação dos três campos com escalas qualitativas

- **Prós**: Cobertura abrangente — magnitude relativa (_Shorts%_), dimensão absoluta (Volume de Shorts) e risco de fechamento (_SIR_).
- **Contras**: Requer mais dados de entrada e definição de _thresholds_.

---

## 4. Better Solution (Solução Superior)

A solução superior é a **Opção D**: um sistema unificado com os seguintes campos, cada um respondendo a uma pergunta distinta sobre a posição vendida a descoberto.

### 4.1 Campo: Shorts% (Short Interest)

**Significado**: Percentual do _free float_ (ações disponíveis para negociação) que está alugado e não foi devolvido. Mede a magnitude relativa da aposta baixista.

**Fórmula**:

```
Shorts% = (Número de Ações Alugadas / Free Float) × 100
```

**Interpretação**: Quanto maior o _Shorts%_, maior a concentração de posições vendidas em relação ao estoque disponível, elevando o potencial de _short squeeze_ se o preço subir.

---

### 4.2 Campo: Volume de Shorts

**Significado**: Escala qualitativa derivada do _Shorts%_ para classificar a intensidade da aposta baixista em termos absolutos de sentimento. Este campo não é o número bruto de ações, mas a **classificação** do _Shorts%_.

**Fórmula**: Classificação categórica do _Shorts%_ calculado acima.

**Tabela de Classificação**:

| Shorts%   | Classificação |
| --------- | ------------- |
| 0% ou N/A | Inexistente   |
| < 1%      | Muito Baixo   |
| < 3%      | Baixo         |
| ≤ 10%     | Alto          |
| > 10%     | Muito Alto    |

**Interpretação**: A escala reflete o consenso acadêmico e de mercado de que valores a partir de 3% já sinalizam sentimento pessimista relevante, e acima de 10% representam uma aposta muito significativa contra a empresa.

---

### 4.3 Campo: Fechamento Shorts (Short Interest Ratio)

**Significado**: Número de dias necessários para que todos os vendedores a descoberto recomprem as ações emprestadas, ao volume médio diário de negociação. Mede a **dificuldade operacional de fechamento**.

**Fórmula**:

```
SIR = Número de Ações Alugadas / Volume Médio Diário de Negociação
```

O valor é apresentado em **dias**, com uma casa decimal e sufixo `d` (ex.: `5,0d`).

**Interpretação**: Um SIR elevado indica que, se os shorts tentarem fechar posições simultaneamente, o mercado pode não absorver a demanda sem uma forte pressão de alta nos preços . Tradicionalmente, valores acima de 5 são considerados altos .

---

### 4.4 Campo: Risco Fechamento

**Significado**: Escala qualitativa derivada do _Short Interest Ratio_ para classificar o risco de _short squeeze_ e a dificuldade de liquidação das posições vendidas.

**Fórmula**: Classificação categórica do _SIR_ calculado acima.

**Tabela de Classificação**:

| SIR      | Risco Fechamento |
| -------- | ---------------- |
| 0 ou N/A | Inexistente      |
| < 2      | Muito Baixo      |
| < 4      | Baixo            |
| ≤ 5      | Alto             |
| > 5      | Muito Alto       |

**Interpretação**: O risco de fechamento mede a probabilidade de um evento de _squeeze_ desordenado. SIR entre 4 e 5 já sinaliza alerta; acima de 5, a condição é de vulnerabilidade severa a movimentos de alta no preço .

---

## 5. Evaluate (Avaliação)

### Vantagens da Solução

- **Cobertura multidimensional**: Combina magnitude relativa (_Shorts%_), classificação de sentimento (Volume de Shorts) e risco operacional (_SIR_ / Risco Fechamento).
- **Ancoragem em dados oficiais**: B3 e FINRA são as fontes primárias de _short interest_, garantindo precisão e auditabilidade .
- **Escalas acionáveis**: As classificações permitem _screening_ rápido de ativos e priorização de análise.

### Limitações e Mitigações

| Limitação                                         | Mitigação                                                                                                                            |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| B3 atualiza diariamente; FINRA apenas 2x/mês      | Para ativos brasileiros, utilizar dados diários da B3; para americanos, reconhecer a defasagem e monitorar tendências entre reportes |
| _Free float_ pode variar por eventos corporativos | Atualizar o _free float_ em cada evento de custódia ou recompra                                                                      |
| Volume médio pode ser distorcido por _outliers_   | Utilizar média de 20 a 30 dias em vez de média mensal simples                                                                        |

### Conclusão

A integração dos quatro campos — _Shorts%_, Volume de Shorts, _Short Interest Ratio_ e Risco Fechamento — em um _framework_ único, ancorado nas divulgações oficiais da B3 e FINRA, fornece uma visão completa do posicionamento vendido a descoberto. Cada campo responde a uma pergunta distinta: **Quanto?** (_Shorts%_), **Quão grave?** (Volume de Shorts), **Quão difícil fechar?** (_SIR_) e **Qual o nível de risco?** (Risco Fechamento). Essa estrutura elimina a ambiguidade interpretativa e permite decisões mais informadas sobre exposição a ativos com alta concentração de _shorts_.

---

## 6. Fontes de Dados e Decisões de Implementação

Esta seção registra as decisões concretas adotadas na materialização desta RFC (change `analise-short-interest`). Elas refinam, sem alterar, a solução da seção 4.

### 6.1 Ações alugadas — B3/BDI (fonte oficial)

O estoque de **empréstimo de ativos (BTC)** é obtido da tabela **`BTBLendingOpenPosition`** ("Posições em aberto"), do capítulo **"Empréstimos de ativos"** do **BDI** da B3. A tabela tem retenção de **D-21** (cerca de 21 dias úteis) e divulga a posição do **pregão anterior**.

- **Aquisição**: `POST https://arquivos.b3.com.br/bdi/table/BTBLendingOpenPosition/{data}/{data}/{página}/{take}` (JSON paginado; `take` de até 1000).
- **Campos usados**: `TckrSymb` (ticker), `Market` (mercado de negociação) e `StockBalance` (saldo em quantidade do ativo).
- **Agregação por ticker**: usa-se a linha `Market = "Total"`; na ausência de `Total`, soma-se as demais linhas.
- **Data ainda não publicada** (tipicamente a data corrente): recua-se até a data publicada mais recente dentro de uma janela de poucos dias.
- **Falha de aquisição**: tolerada — o ticker resulta em `N/A` sem afetar as demais colunas.
- **Cache**: diário, versionado por formato de fonte.

A página "Posições em Aberto" do mercado **Termo** (`.../mercado-a-vista/termo/posicoes-em-aberto/`) foi avaliada e **descartada**: seus códigos terminam em `T` e representam contratos a termo, não o estoque de empréstimos, com ordem de grandeza distinta. O endpoint `requestname` (`ConsolidatedLending`) e o portal de arquivos (`arquivos.b3.com.br/api`) **não** servem empréstimos.

### 6.2 Free float — CVM FRE

O denominador do _Shorts%_ é o **free float** do CSV `fre_cia_aberta_distribuicao_capital` do **FRE** da CVM (`Quantidade_Total_Acoes_Circulacao`), já baixado e parseado pelo `CvmAcionistasSource` e chaveado por CNPJ. Quando o _free float_ é ausente, o denominador passa a ser o **total emitido** (ações/cotas); FIIs usam o total de cotas.

### 6.3 Volume médio — dados em memória

O _SIR_ usa o volume médio diário derivado do `fin_instr_qty` do `daily_data` já carregado para o ticker (média dos dias disponíveis em memória), sem fonte nova. Sem dias disponíveis ou com volume médio zero, o _SIR_ é `N/A`. A janela é variável (depende do range carregado) e não garante os 20–30 dias recomendados na seção 5.

### 6.4 Escopo e não-objetivos

- **FINRA/BDRs**: fora do escopo desta materialização (exigiria mapeamento BDR→símbolo US, _free float_ da empresa estrangeira e licenciamento).
- **Coleta histórica** além da janela `D-21` da B3: fora do escopo.

### 6.5 Alternativa avaliada (fora do escopo)

O **Boletim Diário (BDI)** da B3 também publica o conteúdo **"Empréstimos de Ativos – Posição em aberto (BDI)"** (havendo variante em **PDF**, além de "Empréstimos de Ativos – Empréstimos Registrados (BDI)" e "Negócio a negócio – Empréstimo de ativos"). É uma via alternativa de obter a informação, mas **fica fora do escopo corrente**: por ser um relatório agregado, é menos adequada à leitura por ticker e à automação diária do que a tabela `BTBLendingOpenPosition`. Registrado para eventual uso manual ou futuro (ex.: contingência caso a tabela mude).
