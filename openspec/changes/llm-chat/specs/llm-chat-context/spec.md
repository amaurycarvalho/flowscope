## Purpose

Monta o contexto que a LLM recebe ao responder, combinando o conhecimento do próprio FlowScope, os fundamentos carregados e uma cascata de recuperação sobre os documentos em cache.

## ADDED Requirements

### Requirement: Conhecimento do próprio FlowScope

O sistema DEVE compor o conhecimento do FlowScope a partir dos textos de orientação das sub-abas e das informações da aba Sobre (apresentação, licença, versão), disponibilizando esse bloco a ambos os chats, inclusive para perguntas sobre o próprio aplicativo.

#### Scenario: Pergunta sobre o próprio FlowScope
- **WHEN** o usuário pergunta o que é o FlowScope ou como funciona uma sub-aba
- **THEN** o contexto DEVE conter os textos de orientação das sub-abas e as informações da aba Sobre

#### Scenario: Bloco presente nos dois chats
- **WHEN** uma pergunta é feita no Chat Geral ou no Chat Ticker
- **THEN** o bloco de conhecimento do FlowScope DEVE estar presente no contexto

### Requirement: Contexto de fundamentos

O sistema DEVE incluir no contexto os dados da tabela de fundamentos carregada no momento, cobrindo a watchlist completa. O ticker referido na pergunta DEVE ser identificado pela LLM a partir do texto da pergunta, sem seletor de escopo na interface. Quando não houver dados carregados, o sistema DEVE orientar o usuário a carregá-los, sem falhar.

#### Scenario: Fundamentos da watchlist
- **WHEN** há fundamentos carregados e uma pergunta é feita na aba "Chat AI"
- **THEN** o contexto DEVE incluir os dados dos tickers da watchlist completa

#### Scenario: Identificação do ticker pela LLM
- **WHEN** a pergunta menciona um ticker específico
- **THEN** a LLM DEVE identificar o ticker a partir da pergunta, sem que a interface ofereça um seletor de escopo

#### Scenario: Sem dados carregados
- **WHEN** não há fundamentos carregados
- **THEN** o sistema DEVE orientar a carregar os dados, sem erro

### Requirement: Cascata de recuperação de documentos

O sistema DEVE recuperar o contexto documental em cascata sobre os caches mantidos pela sub-aba "Documentos": primeiro os resumos curtos, depois os resumos longos e, por fim, o texto integral dos documentos-alvo, interrompendo a cascata assim que houver resposta. Quando o texto ou o resumo não estiverem em cache, o sistema DEVE prepará-los sob demanda. O escopo documental DEVE ser a watchlist completa e a LLM DEVE selecionar os documentos-alvo, por chave, a partir da pergunta.

#### Scenario: Resposta a partir dos resumos
- **WHEN** os resumos curtos ou longos bastam para responder
- **THEN** o sistema NÃO DEVE ler o texto integral e DEVE devolver a resposta

#### Scenario: Escalada para o texto integral
- **WHEN** os resumos não bastam e há documentos-alvo
- **THEN** o sistema DEVE ler o texto integral desses alvos

#### Scenario: Cache frio
- **WHEN** não há resumo nem texto em cache para um documento do escopo
- **THEN** o sistema DEVE preparar o texto/resumo sob demanda antes de usá-lo

#### Scenario: Escopo único
- **WHEN** a pergunta é feita na aba "Chat AI"
- **THEN** o escopo documental DEVE ser a watchlist completa

#### Scenario: Seleção do ticker inferido
- **WHEN** a pergunta se refere a um ticker específico
- **THEN** a LLM DEVE indicar os documentos-alvo desse ticker pelas suas chaves

### Requirement: Fontes adicionais de contexto

O sistema DEVE permitir registrar fontes adicionais de contexto no chat, além do conhecimento do FlowScope, dos fundamentos e dos documentos, renderizando-as no prompt sem alterar a ordem da cascata de documentos. Falha ou ausência de conteúdo de uma fonte adicional NÃO DEVE impedir a resposta.

#### Scenario: Fonte adicional presente
- **WHEN** uma fonte adicional retorna conteúdo para a pergunta
- **THEN** o contexto DEVE conter o bloco dessa fonte

#### Scenario: Fonte adicional indisponível
- **WHEN** uma fonte adicional falha ou retorna vazio
- **THEN** o contexto DEVE ser montado sem ela, sem erro

### Requirement: Confirmação por quantidade de documentos-alvo

Antes de ler o texto integral, o sistema DEVE confirmar com o usuário conforme a quantidade de documentos-alvo: até 3 documentos prossegue automaticamente; de 4 a 7, lista os nomes e pede confirmação; 8 ou mais, informa a quantidade e pede confirmação. A ausência de confirmação NÃO DEVE interromper a interface.

#### Scenario: Até três documentos
- **WHEN** há até 3 documentos-alvo
- **THEN** o sistema DEVE prosseguir sem confirmação

#### Scenario: Entre quatro e sete documentos
- **WHEN** há entre 4 e 7 documentos-alvo
- **THEN** o sistema DEVE listar os nomes e pedir confirmação antes de prosseguir

#### Scenario: Oito ou mais documentos
- **WHEN** há 8 ou mais documentos-alvo
- **THEN** o sistema DEVE informar a quantidade e pedir confirmação antes de prosseguir

### Requirement: Orçamento de contexto

O sistema DEVE limitar o volume de texto enviado à LLM, com teto por documento e teto global, truncando o excedente e registrando aviso no log quando o limite for atingido.

#### Scenario: Limite excedido
- **WHEN** o contexto montado excede o teto global
- **THEN** o conteúdo DEVE ser truncado e um aviso DEVE ser registrado no log
