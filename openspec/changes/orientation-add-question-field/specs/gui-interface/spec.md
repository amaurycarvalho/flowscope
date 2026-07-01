## MODIFIED Requirements

### Requirement: OrientationPanel para conteúdo explicativo
O sistema DEVE exibir um OrientationPanel na barra lateral direita contendo título e texto explicativo fixo associado à sub-aba ativa. Cada sub-aba DEVE ter seu próprio conteúdo explicativo composto por (objetivo, pergunta respondida, indicadores envolvidos, como interpretá-lo), nesta ordem.

#### Scenario: OrientationPanel atualizado ao trocar sub-aba
- **WHEN** o usuário seleciona a sub-aba "VWAP"
- **THEN** o OrientationPanel DEVE exibir o título "VWAP — Volume Weighted Average Price" e o texto explicativo correspondente, contendo os campos Objetivo, Responde a pergunta, Indicadores envolvidos e Como interpretar, nesta ordem

#### Scenario: OrientationPanel da sub-aba VWAP contém a pergunta
- **WHEN** o usuário seleciona a sub-aba "VWAP"
- **THEN** o texto do OrientationPanel DEVE conter "Responde a pergunta: _Quem está acima do preço justo e quem está abaixo?_"

#### Scenario: OrientationPanel da sub-aba Quadrantes contém a pergunta
- **WHEN** o usuário seleciona a sub-aba "Quadrantes"
- **THEN** o texto do OrientationPanel DEVE conter "Responde a pergunta: _Quem dominou o fechamento?_"

#### Scenario: OrientationPanel da sub-aba Dominância do Pregão contém a pergunta
- **WHEN** o usuário seleciona a sub-aba "Dominância do Pregão"
- **THEN** o texto do OrientationPanel DEVE conter "Responde a pergunta: _Quem venceu a disputa diária pelo preço?_"

#### Scenario: OrientationPanel da sub-aba Evolução da Dominância contém a pergunta
- **WHEN** o usuário seleciona a sub-aba "Evolução da Dominância"
- **THEN** o texto do OrientationPanel DEVE conter "Responde a pergunta: _Quem venceu a disputa diária pelo preço?_"

#### Scenario: OrientationPanel da sub-aba Amplitude de Preço contém a pergunta
- **WHEN** o usuário seleciona a sub-aba "Amplitude de Preço"
- **THEN** o texto do OrientationPanel DEVE conter "Responde a pergunta" seguido da pergunta sobre movimento direcional e evolução do fechamento

#### Scenario: OrientationPanel da sub-aba Fluxo Financeiro contém a pergunta
- **WHEN** o usuário seleciona a sub-aba "Fluxo Financeiro"
- **THEN** o texto do OrientationPanel DEVE conter "Responde a pergunta: _O movimento ocorreu com dinheiro ou apenas por falta de liquidez?_"

#### Scenario: OrientationPanel da sub-aba Participação Institucional contém a pergunta
- **WHEN** o usuário seleciona a sub-aba "Participação Institucional"
- **THEN** o texto do OrientationPanel DEVE conter "Responde a pergunta: _Quem parece estar negociando? Grandes participantes ou varejo?_"

#### Scenario: OrientationPanel da sub-aba Eficiência do Movimento contém a pergunta
- **WHEN** o usuário seleciona a sub-aba "Eficiência do Movimento"
- **THEN** o texto do OrientationPanel DEVE conter "Responde a pergunta: _O mercado caminhou com convicção ou apenas oscilou?_"

#### Scenario: OrientationPanel da sub-aba Resumo Geral contém a pergunta
- **WHEN** o usuário seleciona a sub-aba "Resumo Geral"
- **THEN** o texto do OrientationPanel DEVE conter "Responde a pergunta: _O que realmente aconteceu neste ativo?_"
