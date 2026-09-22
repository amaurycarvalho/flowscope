# RFC-014: Análise de Short Interest com Dados Oficiais (B3/FINRA)

## 1. Problem (Problema)

Investidores e analistas frequentemente utilizam dados de *short interest* sem uma metodologia clara para interpretação e hierarquização do risco. No mercado brasileiro e americano, as fontes oficiais (B3 e FINRA) fornecem os dados brutos — quantidade de ações alugadas, estoque de posições em aberto — mas a tradução desses números em métricas acionáveis de risco de fechamento (*short squeeze*) permanece subjetiva e fragmentada.

Os principais problemas são:

- **Fontes dispersas e periodicidade distinta**: A B3 divulga estoque de empréstimos de ativos diariamente , enquanto a FINRA reporta duas vezes por mês, com publicação defasada de aproximadamente 10 a 11 dias .
- **Ausência de um padrão consolidado**: Não há um *framework* único que combine *Shorts%*, volume absoluto e *Short Interest Ratio* em uma escala qualitativa de risco.
- **Interpretação equivocada**: Números brutos de ações alugadas, sem normalização pelo *free float* ou pelo volume negociado, levam a conclusões distorcidas sobre a magnitude real do risco de fechamento.

---

## 2. Root Cause (Causa Raiz)

A causa raiz reside na **natureza dos dados reportados pelas bolsas**: eles são matéria-prima operacional (contratos de empréstimo, posições em aberto), não métricas de sentimento ou risco. A B3 disponibiliza o estoque de empréstimos como parte dos serviços de compensação e liquidação , e a FINRA exige o reporte de *short interest* como obrigação regulatória de transparência .

Ambas as fontes **não calculam** as métricas derivadas — *Shorts%*, *Short Interest Ratio* ou classificações de risco. Isso força o analista a:

1. Coletar os dados brutos de fontes primárias (B3/FINRA);
2. Obter o *free float* e o volume médio de negociação de fontes secundárias (provedores de dados, relatórios de empresas);
3. Construir manualmente os indicadores e as escalas de interpretação.

Sem um *framework* padronizado, cada analista adota critérios próprios, gerando inconsistência na avaliação do mesmo ativo por diferentes observadores.

---

## 3. Options (Opções)

### Opção A: Utilizar apenas o volume bruto de ações alugadas
- **Prós**: Simples, disponível diretamente nos dados da B3/FINRA.
- **Contras**: Ignora o tamanho da empresa (*free float*) e a liquidez do ativo. Uma empresa com 1 milhão de ações alugadas pode ter risco completamente diferente dependendo do seu porte e volume.

### Opção B: Utilizar apenas o *Shorts%* (Short Interest como % do Free Float)
- **Prós**: Normaliza pelo tamanho da empresa, permitindo comparação entre ativos.
- **Contras**: Não captura a dimensão de **liquidez**. Uma ação com *Shorts%* alto mas volume diário altíssimo pode ter baixo risco de *squeeze*.

### Opção C: Utilizar apenas o *Short Interest Ratio* (Days to Cover)
- **Prós**: Mede diretamente a dificuldade de fechamento, incorporando liquidez.
- **Contras**: Pode ser volátil em ativos com volume irregular; um único dia de volume anormal distorce a métrica.

### Opção D: Combinação dos três campos com escalas qualitativas
- **Prós**: Cobertura abrangente — magnitude relativa (*Shorts%*), dimensão absoluta (Volume de Shorts) e risco de fechamento (*SIR*).
- **Contras**: Requer mais dados de entrada e definição de *thresholds*.

---

## 4. Better Solution (Solução Superior)

A solução superior é a **Opção D**: um sistema unificado com os seguintes campos, cada um respondendo a uma pergunta distinta sobre a posição vendida a descoberto.

### 4.1 Campo: Shorts% (Short Interest)

**Significado**: Percentual do *free float* (ações disponíveis para negociação) que está alugado e não foi devolvido. Mede a magnitude relativa da aposta baixista.

**Fórmula**:
```
Shorts% = (Número de Ações Alugadas / Free Float) × 100
```


**Interpretação**: Quanto maior o *Shorts%*, maior a concentração de posições vendidas em relação ao estoque disponível, elevando o potencial de *short squeeze* se o preço subir.

---

### 4.2 Campo: Volume de Shorts

**Significado**: Escala qualitativa derivada do *Shorts%* para classificar a intensidade da aposta baixista em termos absolutos de sentimento. Este campo não é o número bruto de ações, mas a **classificação** do *Shorts%*.

**Fórmula**: Classificação categórica do *Shorts%* calculado acima.

**Tabela de Classificação**:

| Shorts% | Classificação |
|---------|--------------|
| 0% | Inexistente |
| < 5% | Muito Baixo |
| < 10% | Baixo |
| ≤ 20% | Alto |
| > 20% | Muito Alto |

**Interpretação**: A escala reflete o consenso acadêmico e de mercado de que valores acima de 10% já indicam sentimento fortemente pessimista , e acima de 20% representam uma aposta muito significativa contra a empresa.

---

### 4.3 Campo: Fechamento Shorts (Short Interest Ratio)

**Significado**: Número de dias necessários para que todos os vendedores a descoberto recomprem as ações emprestadas, ao volume médio diário de negociação. Mede a **dificuldade operacional de fechamento**.

**Fórmula**:
```
SIR = Número de Ações Alugadas / Volume Médio Diário de Negociação
```


**Interpretação**: Um SIR elevado indica que, se os shorts tentarem fechar posições simultaneamente, o mercado pode não absorver a demanda sem uma forte pressão de alta nos preços . Tradicionalmente, valores acima de 5 são considerados altos .

---

### 4.4 Campo: Risco Fechamento

**Significado**: Escala qualitativa derivada do *Short Interest Ratio* para classificar o risco de *short squeeze* e a dificuldade de liquidação das posições vendidas.

**Fórmula**: Classificação categórica do *SIR* calculado acima.

**Tabela de Classificação**:

| SIR | Risco Fechamento |
|-----|-----------------|
| 0 | Inexistente |
| < 2 | Muito Baixo |
| < 4 | Baixo |
| ≤ 5 | Alto |
| > 5 | Muito Alto |

**Interpretação**: O risco de fechamento mede a probabilidade de um evento de *squeeze* desordenado. SIR entre 4 e 5 já sinaliza alerta; acima de 5, a condição é de vulnerabilidade severa a movimentos de alta no preço .

---

## 5. Evaluate (Avaliação)

### Vantagens da Solução

- **Cobertura multidimensional**: Combina magnitude relativa (*Shorts%*), classificação de sentimento (Volume de Shorts) e risco operacional (*SIR* / Risco Fechamento).
- **Ancoragem em dados oficiais**: B3 e FINRA são as fontes primárias de *short interest*, garantindo precisão e auditabilidade .
- **Escalas acionáveis**: As classificações permitem *screening* rápido de ativos e priorização de análise.

### Limitações e Mitigações

| Limitação | Mitigação |
|-----------|-----------|
| B3 atualiza diariamente; FINRA apenas 2x/mês  | Para ativos brasileiros, utilizar dados diários da B3; para americanos, reconhecer a defasagem e monitorar tendências entre reportes |
| *Free float* pode variar por eventos corporativos | Atualizar o *free float* em cada evento de custódia ou recompra  |
| Volume médio pode ser distorcido por *outliers* | Utilizar média de 20 a 30 dias em vez de média mensal simples |

### Conclusão

A integração dos quatro campos — *Shorts%*, Volume de Shorts, *Short Interest Ratio* e Risco Fechamento — em um *framework* único, ancorado nas divulgações oficiais da B3 e FINRA, fornece uma visão completa do posicionamento vendido a descoberto. Cada campo responde a uma pergunta distinta: **Quanto?** (*Shorts%*), **Quão grave?** (Volume de Shorts), **Quão difícil fechar?** (*SIR*) e **Qual o nível de risco?** (Risco Fechamento). Essa estrutura elimina a ambiguidade interpretativa e permite decisões mais informadas sobre exposição a ativos com alta concentração de *shorts*.
