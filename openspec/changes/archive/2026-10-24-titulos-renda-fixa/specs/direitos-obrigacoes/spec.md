## REMOVED Requirements

### Requirement: Ramos placeholder de Direitos e Obrigações

**Reason**: O ramo deixa de ser um placeholder e passa a exibir títulos de renda fixa reais, com tipos, títulos individuais, agregados e ausência de fonte explícita.

**Migration**: Os consumidores devem passar a navegar a estrutura definida nos requisitos adicionados abaixo; os caminhos `/direitos-obrigacoes/direitos` e `/direitos-obrigacoes/obrigacoes` permanecem como raízes dos sub-ramos.

## ADDED Requirements

### Requirement: Estrutura de Obrigações e Direitos com Títulos

A árvore de "Direitos e obrigações" DEVE conter os sub-ramos "Obrigações" e "Direitos"; cada um DEVE conter o sub-ramo "Títulos"; cada "Títulos" DEVE conter um nó por tipo de título aplicável — Debêntures, Nota Comercial, CRI, CRA, LCI, LCA, CDB, Letras Financeiras e Outros — e cada tipo DEVE conter os títulos individuais, um nó agregado ou um nó de ausência de fonte.

Títulos individuais DEVEM ter um identificador estável e compacto no caminho, derivado da chave da fonte, e um rótulo humano legível no nó. O nó agregado DEVE ser usado apenas quando existir total por ticker na fonte. O nó de ausência de fonte DEVE ser usado quando não houver título nem total público por emissor.

#### Scenario: Obrigações de uma companhia
- **WHEN** a companhia possui debêntures e CRI reportados no FRE
- **THEN** a árvore DEVE exibir Obrigações → Títulos → Debêntures e CRI, com um nó por título

#### Scenario: Direitos de um FII
- **WHEN** o FII possui CRI/CRA e LCI/LCA na carteira
- **THEN** a árvore DEVE exibir Direitos → Títulos → CRI, CRA, LCI e LCA, com um nó por posição

#### Scenario: Título individual com identificador estável
- **WHEN** o mesmo título é exibido em duas aquisições sem mudança de fonte
- **THEN** o caminho do nó DEVE permanecer o mesmo e o rótulo humano DEVE continuar legível

#### Scenario: Agregado de debêntures de FII
- **WHEN** o FII possui apenas o total de debêntures no informe mensal
- **THEN** a árvore DEVE exibir um nó agregado de Debêntures com valor, fonte e data de referência

#### Scenario: Ausência de fonte para CDB de companhia
- **WHEN** a companhia não possui título nem total público por emissor de CDB
- **THEN** a árvore DEVE exibir o nó de CDB com a indicação explícita de ausência de fonte

### Requirement: Regra do devedor econômico para CRI/CRA em Obrigações

Um CRI ou CRA DEVE aparecer em "Obrigações" do ticker cujo CNPJ seja o devedor econômico do lastro, ainda que o emissor legal seja uma securitizadora. O emissor legal DEVE ser exibido como metadado do título.

O vínculo DEVE vir do FRE da companhia ou do CNPJ de devedor válido no SECURIT. Um CNPJ de devedor inválido, ausente ou não correspondente ao ticker NÃO DEVE criar o vínculo. O fato de a companhia ser apenas emissora legal do CRI/CRA NÃO DEVE, por si só, criar uma obrigação para ela.

#### Scenario: Companhia devedora de CRI
- **WHEN** o CNPJ da companhia aparece como devedor econômico de um CRI no FRE ou no SECURIT
- **THEN** o CRI DEVE ser exibido em Obrigações da companhia com a securitizadora como emissor legal

#### Scenario: CNPJ de devedor inválido
- **WHEN** o SECURIT informa um CNPJ de devedor inválido, vazio ou genérico
- **THEN** o título NÃO DEVE ser associado a nenhum ticker por esse vínculo

#### Scenario: Companhia apenas emissora legal
- **WHEN** a companhia é a securitizadora emissora, mas não é o devedor econômico do lastro
- **THEN** o CRI/CRA NÃO DEVE ser criado como obrigação pelo critério do devedor econômico

### Requirement: Conteúdo de cada título individual

Cada título individual DEVE expor "Informações gerais", "Informações adicionais", "LTV" quando aplicável e "Documentos relacionados".

"Informações gerais" DEVE conter, quando informados: emissor legal, devedor econômico, identificação do título, emissão, série, data de emissão, vencimento, indexador, taxa, quantidade, valor, saldo devedor ou valor da posição, fonte e data de referência.

"Informações adicionais" DEVE reunir, quando informados: garantias, coobrigação, lastro, sobrecolateralização, subordinação, covenants/restrições, eventos de inadimplemento, vencimento antecipado, condição de alteração de direitos, situação, classificação de risco, contingências, impacto de eventos e desempenho.

"LTV" DEVE ser exibido como informação própria quando a fonte informar o índice e a data; caso contrário, DEVE ser declarado como não informado, sem valor inventado.

"Documentos relacionados" DEVE listar links para documentos já cacheados e URLs oficiais da CVM/B3, sem extração, resumo ou interpretação por LLM.

#### Scenario: Título com informações completas
- **WHEN** o FRE e o SECURIT informam os campos do título
- **THEN** a pré-visualização DEVE exibir informações gerais e adicionais com os valores e a fonte

#### Scenario: CRI com LTV
- **WHEN** o SECURIT informa `Indice_LTV` e `Data_LTV` para um CRI
- **THEN** o título DEVE exibir o LTV e a data como informação própria

#### Scenario: Título sem LTV
- **WHEN** a fonte não informa LTV para o título
- **THEN** o sistema DEVE declarar o LTV como não informado, sem calcular ou inferir valor

#### Scenario: Documentos relacionados por link
- **WHEN** existem material facts ou notícias relacionadas ao título ou ao emissor
- **THEN** o título DEVE listar os links correspondentes, sem baixar nem resumir conteúdo durante a navegação

### Requirement: Agregados e ausência de fonte explícita

Um nó agregado DEVE representar apenas um total por ticker publicado pela fonte, com valor, fonte e data de referência; ele NÃO DEVE ser apresentado como título individual nem somar datas ou versões distintas.

Um nó de ausência de fonte DEVE explicar que não há título nem total público por emissor para aquele tipo, sem criar valores ou nós vazios que aparentem dados.

#### Scenario: Total agregado por ticker
- **WHEN** o FII possui total de CDB no informe mensal
- **THEN** o nó agregado DEVE exibir o total da última data/versão, com a fonte e a data

#### Scenario: Não somar meses
- **WHEN** o informe mensal contém o mesmo fundo em várias datas
- **THEN** o agregado DEVE usar a última data/versão, não a soma de todas as datas

#### Scenario: Ausência de fonte
- **WHEN** não existe título nem total por emissor para um tipo
- **THEN** o nó DEVE exibir a explicação de ausência de fonte, sem erro

### Requirement: Data de referência e proveniência

A árvore DEVE expor o nó `/direitos-obrigacoes/data-referencia` com as datas de referência das fontes de obrigações e direitos e o instante da última aquisição. Cada título e cada agregado DEVE citar a fonte e a data de referência que originaram seus valores.

#### Scenario: Nó de data de referência
- **WHEN** a árvore de direitos e obrigações é montada
- **THEN** o nó `/direitos-obrigacoes/data-referencia` DEVE existir com as datas das fontes e a data de aquisição

#### Scenario: Proveniência por título
- **WHEN** o usuário abre um título
- **THEN** a pré-visualização DEVE citar a fonte e a data de referência dos dados exibidos

### Requirement: Navegação cache-only e tolerante no Chat AI

A árvore de conhecimento do Chat AI DEVE montar o ramo `/direitos-obrigacoes` exclusivamente a partir do cache normalizado por ticker, sem baixar, extrair, resumir ou consultar a CVM/B3 durante a conversa. O ramo DEVE ser navegável quando não houver dados, sinalizando a ausência sem erro.

#### Scenario: Navegação sem cache
- **WHEN** o ticker não possui cache de direitos e obrigações
- **THEN** o ramo DEVE existir com a indicação de ausência de dados, sem erro

#### Scenario: Navegação com cache
- **WHEN** o ticker possui cache normalizado
- **THEN** a LLM DEVE conseguir listar e obter os nós de Obrigações e Direitos, tipos, títulos, agregados e ausência de fonte

#### Scenario: Sem efeitos colaterais
- **WHEN** a LLM navega o ramo
- **THEN** nenhum download, extração, resumo ou chamada à CVM/B3 DEVE ocorrer
