# cvm-renda-fixa Specification

## Purpose

Ingerir os títulos de renda fixa associados a um ticker a partir dos datasets abertos da CVM, normalizando obrigações emitidas e direitos mantidos com proveniência, idempotência e cache por ticker.

## ADDED Requirements

### Requirement: Aquisição dos datasets CVM de renda fixa

O sistema DEVE adquirir os datasets anuais/trimestrais da CVM necessários à renda fixa usando o downloader CVM existente, com cache condicional, hash e metadados de revalidação:

- Formulário de Referência (FRE), arquivo `fre_cia_aberta_outro_valor_mobiliario_<ano>.csv`;
- Informe Mensal de CRI, arquivos `inf_mensal_cri_geral_<ano>.csv`, `inf_mensal_cri_classe_<ano>.csv`, `inf_mensal_cri_cedente_devedor_<ano>.csv`, `inf_mensal_cri_creditos_<ano>.csv`, `inf_mensal_cri_ativo_passivo_<ano>.csv` e `inf_mensal_cri_carteira_<ano>.csv`;
- Informe Mensal de CRA, arquivos `inf_mensal_cra_geral_<ano>.csv`, `inf_mensal_cra_classe_<ano>.csv`, `inf_mensal_cra_cedente_devedor_<ano>.csv`, `inf_mensal_cra_direitos_creditorios_<ano>.csv` e `inf_mensal_cra_ativo_passivo_<ano>.csv`;
- Informe Trimestral de FII, arquivo `inf_trimestral_fii_ativo_<ano>.csv`;
- Informe Mensal de FII, arquivo `inf_mensal_fii_ativo_passivo_<ano>.csv`.

O sistema DEVE reutilizar o arquivo bruto já cacheado quando a fonte remota não tiver avançado, revalidando no máximo a cada 6 horas, e DEVE tolerar a falha de um dataset sem interromper os demais.

#### Scenario: Dataset anual reutilizado do cache
- **WHEN** o ZIP anual do FRE, SECURIT ou FII já está em cache e a fonte remota não avançou
- **THEN** o sistema DEVE reutilizar o arquivo local sem novo download

#### Scenario: Falha isolada por dataset
- **WHEN** a aquisição do SECURIT falha por indisponibilidade
- **THEN** o sistema DEVE continuar a normalização do FRE e da carteira de FII e sinalizar a ausência do SECURIT

#### Scenario: Seleção da versão mais recente
- **WHEN** existem múltiplas versões ou datas de referência para o mesmo CNPJ e título
- **THEN** o sistema DEVE usar a versão de maior número e a data de referência mais recente aplicável

### Requirement: Normalização de obrigações a partir do FRE

O sistema DEVE extrair do FRE as linhas de `outro_valor_mobiliario` cujo `Valor_Mobiliario` represente renda fixa — Debêntures, Debêntures Conversíveis, Nota Comercial, Certificados de Recebíveis Imobiliários, Certificado de Recebíveis do Agronegócio e Letras Financeiras — e normalizá-las como obrigações do CNPJ da companhia.

Cada obrigação DEVE preservar, quando informados: identificação do valor mobiliário, data de emissão, data de vencimento, quantidade, valor, saldo devedor, restrição de circulação, características da dívida, condição de alteração de direitos e outras características relevantes, além da fonte, da data de referência e da versão. Valores mobiliários que não sejam de renda fixa NÃO DEVEM ser incluídos.

#### Scenario: Debêntures da companhia
- **WHEN** o CNPJ da companhia possui linhas de Debêntures no FRE
- **THEN** cada série DEVE virar uma obrigação com emissão, vencimento, quantidade, valor, saldo devedor e características

#### Scenario: CRI/CRA reportado pela companhia devedora
- **WHEN** o CNPJ da companhia possui linha de CRI ou CRA no FRE
- **THEN** o título DEVE ser classificado como CRI ou CRA e associado à companhia como devedora econômica

#### Scenario: Valor mobiliário fora do escopo
- **WHEN** a linha do FRE representa Ações, Bônus de Subscrição ou Título de Investimento Coletivo
- **THEN** a linha NÃO DEVE ser incluída como título de renda fixa

#### Scenario: Reapresentação do FRE
- **WHEN** o mesmo título aparece em mais de uma versão do FRE
- **THEN** apenas a versão mais recente DEVE ser considerada

### Requirement: Enriquecimento de CRI/CRA com o SECURIT

O sistema DEVE enriquecer cada CRI/CRA com os dados do SECURIT, casando preferencialmente pelo código CETIP/ISIN e, na ausência dele, pelo CNPJ do devedor econômico no arquivo `cedente_devedor`.

O enriquecimento DEVE acrescentar, quando disponíveis: emissor legal (securitizadora), devedor/cedente, lastro, garantias, coobrigação, sobrecolateralização, subordinação, classificação de risco, situação (adimplente/inadimplente), créditos vencidos, atrasos, contingências, impacto de eventos, desempenho e LTV com a respectiva data.

#### Scenario: CRI casado pelo código CETIP/ISIN
- **WHEN** o código CETIP/ISIN do CRI no FRE ou na carteira do FII existe no SECURIT
- **THEN** o título DEVE receber os dados de LTV, garantias, situação e contingências do SECURIT

#### Scenario: CRI casado pelo devedor
- **WHEN** o código não está disponível, mas o CNPJ do devedor econômico casa com `cedente_devedor`
- **THEN** o sistema DEVE usar o SECURIT correspondente para enriquecer o título

#### Scenario: CRI sem correspondência no SECURIT
- **WHEN** não há correspondência por código nem por devedor
- **THEN** o título DEVE permanecer com os dados do FRE e o LTV DEVE ser sinalizado como não informado

#### Scenario: LTV ausente em CRA ou debênture
- **WHEN** o título é CRA ou debênture e a fonte não informa LTV
- **THEN** o sistema NÃO DEVE inventar LTV; o campo DEVE ser ausente ou sinalizado como não informado

### Requirement: Normalização de direitos a partir da carteira de FII

Para um ticker FII, o sistema DEVE extrair do `inf_trimestral_fii_ativo` as posições do CNPJ do fundo nos tipos CRI/CRA e LCI/LCA, usando a data de referência e a versão mais recentes. Cada posição DEVE preservar: tipo, emissor, CNPJ do emissor, emissão, série, código, nome do ativo, vencimento, quantidade e valor.

O sistema DEVE enriquecer as posições de CRI/CRA com o SECURIT pelo código CETIP/ISIN. Para debêntures e CDB, o sistema DEVE extrair do `inf_mensal_fii_ativo_passivo`, na data de referência e versão mais recentes do fundo, os totais das colunas `Debentures` e `Certificados_Deposito_Valores_Mobiliarios`, respectivamente, como agregados de direitos.

#### Scenario: CRI/CRA na carteira do FII
- **WHEN** o FII possui posição em CRI/CRA no informe trimestral
- **THEN** cada código DEVE virar um direito individual com emissor, emissão, série, vencimento, quantidade e valor

#### Scenario: LCI/LCA na carteira do FII
- **WHEN** o FII possui posição em LCI/LCA no informe trimestral
- **THEN** cada posição DEVE virar um direito individual com emissor, CNPJ do emissor, quantidade e valor

#### Scenario: Debêntures agregadas
- **WHEN** o FII possui valor positivo em `Debentures` no informe mensal
- **THEN** o sistema DEVE criar um direito agregado de debêntures com o valor, a data de referência e a fonte

#### Scenario: CDB agregado
- **WHEN** o FII possui valor positivo em `Certificados_Deposito_Valores_Mobiliarios` no informe mensal
- **THEN** o sistema DEVE criar um direito agregado de CDB com o valor, a data de referência e a fonte

#### Scenario: FII sem posições de renda fixa
- **WHEN** o FII não possui posições nos tipos cobertos
- **THEN** o ramo de direitos DEVE sinalizar a ausência de dados, sem erro

### Requirement: Cache por ticker idempotente e cache-aware

O sistema DEVE resolver o CNPJ do ticker — identidade do FII para fundos e FCA para companhias — e gravar os títulos normalizados em um arquivo por ticker em `<cache>/direitos-obrigacoes/<TICKER>.json`, com escrita atômica.

O arquivo DEVE conter a assinatura do conteúdo normalizado, a fonte, a data de referência, a versão do parser e o instante de aquisição. Se a assinatura não mudou, o sistema DEVE reutilizar o cache sem reescrever; se mudou, DEVE substituir o arquivo atomicamente. Uma falha de uma fonte NÃO DEVE apagar o último cache válido das demais.

#### Scenario: Primeira aquisição
- **WHEN** não existe cache do ticker
- **THEN** o sistema DEVE gravar o JSON com as obrigações e os direitos normalizados

#### Scenario: Cache sem mudança
- **WHEN** a aquisição é repetida e a assinatura do conteúdo normalizado não mudou
- **THEN** o sistema DEVE reutilizar o arquivo sem reescrevê-lo

#### Scenario: Cache com mudança
- **WHEN** a fonte remota ou a versão do parser muda o conteúdo normalizado
- **THEN** o sistema DEVE substituir o arquivo atomicamente e atualizar a assinatura

#### Scenario: Falha parcial preserva o cache
- **WHEN** a fonte de direitos falha, mas a de obrigações responde
- **THEN** o sistema DEVE manter o último cache válido de direitos e atualizar as obrigações

#### Scenario: Ticker sem CNPJ resolvido
- **WHEN** o CNPJ do ticker não pode ser resolvido
- **THEN** o sistema NÃO DEVE iniciar a aquisição nem criar cache, sem erro fatal

### Requirement: Aquisição explícita e separada da aquisição de documentos

A aquisição de títulos DEVE ser um serviço próprio, com progresso e resultado próprios, acionado pelo botão "Atualizar" da sub-aba "Documentos" de forma internamente separada da aquisição de documentos. Ela NÃO DEVE baixar ou extrair conteúdo durante a navegação do Chat AI e NÃO DEVE usar LLM para interpretar documentos.

#### Scenario: Progresso separado
- **WHEN** o usuário aciona "Atualizar" para um ticker
- **THEN** o sistema DEVE reportar o andamento de documentos e de títulos de forma distinguível

#### Scenario: Reexecução idempotente
- **WHEN** o usuário aciona "Atualizar" novamente sem mudança de fonte
- **THEN** o sistema DEVE reutilizar o cache e não duplicar títulos

#### Scenario: Sem download no chat
- **WHEN** a LLM navega `/direitos-obrigacoes` no Chat AI
- **THEN** o sistema NÃO DEVE baixar, extrair, resumir ou consultar a CVM/B3
