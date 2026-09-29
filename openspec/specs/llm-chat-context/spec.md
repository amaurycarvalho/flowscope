# llm-chat-context Specification

## Purpose

Monta o contexto que a LLM recebe ao responder, combinando o conhecimento do próprio FlowScope, os fundamentos carregados e uma cascata de recuperação sobre os documentos em cache.

## Requirements

### Requirement: Conhecimento do próprio FlowScope

O sistema DEVE compor o conhecimento do FlowScope a partir dos textos de orientação das sub-abas e das informações da aba Sobre (apresentação, licença, versão), disponibilizando esse bloco a ambos os chats, inclusive para perguntas sobre o próprio aplicativo. Com o parâmetro `input_limitado` ativo, o bloco NÃO DEVE integrar automaticamente o prefixo estável; ele DEVE ser disponibilizado sob demanda, conforme o requisito de contexto inicial sob demanda.

#### Scenario: Pergunta sobre o próprio FlowScope
- **WHEN** o usuário pergunta o que é o FlowScope ou como funciona uma sub-aba
- **THEN** o contexto DEVE conter os textos de orientação das sub-abas e as informações da aba Sobre

#### Scenario: Bloco presente nos dois chats
- **WHEN** uma pergunta é feita no Chat Geral ou no Chat Ticker
- **THEN** o bloco de conhecimento do FlowScope DEVE estar presente no contexto

#### Scenario: Conhecimento carregado sob demanda com janela limitada
- **WHEN** `input_limitado` está ativo e a LLM solicita o recurso de conhecimento
- **THEN** o bloco de conhecimento DEVE ser acrescentado ao contexto daquela resposta

### Requirement: Contexto de fundamentos

O sistema DEVE incluir no contexto os dados da tabela de fundamentos carregada no momento, cobrindo a watchlist completa. O ticker referido na pergunta DEVE ser identificado pela LLM a partir do texto da pergunta, sem seletor de escopo na interface. Quando não houver dados carregados, o sistema DEVE orientar o usuário a carregá-los, sem falhar. Com o parâmetro `input_limitado` ativo, os fundamentos NÃO DEVEM integrar automaticamente o prefixo estável; eles DEVEM ser disponibilizados sob demanda, conforme o requisito de contexto inicial sob demanda.

#### Scenario: Fundamentos da watchlist
- **WHEN** há fundamentos carregados e uma pergunta é feita na aba "Chat AI"
- **THEN** o contexto DEVE incluir os dados dos tickers da watchlist completa

#### Scenario: Identificação do ticker pela LLM
- **WHEN** a pergunta menciona um ticker específico
- **THEN** a LLM DEVE identificar o ticker a partir da pergunta, sem que a interface ofereça um seletor de escopo

#### Scenario: Sem dados carregados
- **WHEN** não há fundamentos carregados
- **THEN** o sistema DEVE orientar a carregar os dados, sem erro

#### Scenario: Fundamentos carregados sob demanda com janela limitada
- **WHEN** `input_limitado` está ativo e a LLM solicita o recurso de fundamentos
- **THEN** os dados da tabela de fundamentos da watchlist DEVEM ser acrescentados ao contexto daquela resposta

### Requirement: Cascata de recuperação de documentos

O sistema DEVE recuperar o contexto documental em cascata sobre os caches mantidos pela sub-aba "Documentos", sem gerar nem extrair conteúdo durante o chat. A primeira camada DEVE conter os resumos cacheados (curto e longo) dos documentos do escopo; a segunda, quando a LLM devolver as chaves dos alvos, o texto integral dos documentos-alvo já extraído e em cache. Documentos pendentes de resumo ou de extração NÃO DEVEM ser preparados, resumidos, extraídos nem citados: eles DEVEM ser omitidos do contexto em silêncio. Quando não houver resumo nem texto em cache, o sistema DEVE montar o contexto sem a seção documental, sem erro e sem executar chamadas de completion adicionais para prepará-la. O escopo documental DEVE ser a watchlist completa e a LLM DEVE selecionar os documentos-alvo, por chave, a partir da pergunta. Com o parâmetro `input_limitado` ativo, os resumos NÃO DEVEM integrar automaticamente a primeira camada; eles DEVEM ser disponibilizados sob demanda, e, uma vez carregados, o sistema DEVE seguir a cascata para o texto integral dos documentos-alvo.

#### Scenario: Resposta a partir dos resumos

- **WHEN** há resumos cacheados no escopo e eles bastam para responder
- **THEN** o sistema NÃO DEVE ler o texto integral, NÃO DEVE gerar resumos e DEVE devolver a resposta

#### Scenario: Escalada para o texto integral

- **WHEN** os resumos cacheados não bastam e a LLM devolve chaves de documentos-alvo
- **THEN** o sistema DEVE usar o texto integral desses alvos do cache, sem extraí-lo sob demanda

#### Scenario: Cache frio

- **WHEN** nenhum documento do escopo tem resumo ou texto em cache
- **THEN** o contexto DEVE ser montado sem a seção documental, sem erro e sem chamadas de completion para prepará-la

#### Scenario: Documento pendente é omitido em silêncio

- **WHEN** um documento do escopo não tem resumo nem texto em cache
- **THEN** ele NÃO DEVE aparecer no contexto, NÃO DEVE ser resumido nem extraído e NÃO DEVE ser citado na resposta

#### Scenario: Escopo único

- **WHEN** a pergunta é feita na aba "Chat AI"
- **THEN** o escopo documental DEVE ser a watchlist completa

#### Scenario: Seleção do ticker inferido

- **WHEN** a pergunta se refere a um ticker específico
- **THEN** a LLM DEVE indicar os documentos-alvo desse ticker pelas suas chaves

#### Scenario: Resumos carregados sob demanda com janela limitada

- **WHEN** `input_limitado` está ativo e a LLM solicita o recurso de resumos
- **THEN** os resumos cacheados DEVEM ser acrescentados ao contexto, e a LLM DEVE poder indicar os documentos-alvo para a leitura do texto integral

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

### Requirement: Contexto estável com revalidação por assinatura

O bloco de contexto estável (conhecimento do FlowScope, fundamentos da watchlist e resumos de documentos) DEVE ser renderizado de forma determinística e associado a uma **assinatura de conteúdo**. Enquanto a assinatura não mudar, o bloco renderizado DEVE ser reusado byte-a-byte; quando a assinatura mudar, o bloco DEVE ser reconstruído. Fontes cuja composição depende da pergunta NÃO DEVEM integrar o bloco estável.

#### Scenario: Reuso enquanto a assinatura não muda

- **WHEN** uma nova pergunta é feita e a assinatura do contexto permanece a mesma
- **THEN** o bloco estável anterior DEVE ser reusado, sem recomputar o texto do prefixo

#### Scenario: Reconstrução quando o conteúdo muda

- **WHEN** os fundamentos, a watchlist ou o conjunto de resumos muda entre turnos
- **THEN** a assinatura DEVE mudar e o bloco estável DEVE ser reconstruído naquele turno

#### Scenario: Determinismo do bloco

- **WHEN** o bloco estável é reconstruído com as mesmas entradas
- **THEN** o texto resultante DEVE ser idêntico byte-a-byte ao anterior

#### Scenario: Fontes voláteis fora do bloco estável

- **WHEN** uma fonte adicional depende da pergunta
- **THEN** ela NÃO DEVE compor o bloco estável nem a assinatura, permanecendo no sufixo volátil

### Requirement: Contexto inicial sob demanda com janela de entrada limitada

Quando o parâmetro `input_limitado` estiver ativo para o provedor/modelo, o sistema NÃO DEVE incluir automaticamente no prefixo estável o conhecimento do FlowScope, os fundamentos e os resumos. Em vez disso, o prefixo DEVE conter um manifesto informando a existência desses recursos, as chaves reservadas para solicitá-los (`conhecimento`, `fundamentos`, `resumos`) e a instrução de como requisitá-los. Os recursos DEVEM ser carregados no payload apenas quando solicitados explicitamente pela LLM, pela mesma cascata de recuperação usada pelos documentos. O manifesto e a omissão dos blocos DEVEM integrar a assinatura do contexto estável. Sem o parâmetro ativo, o comportamento atual DEVE ser preservado integralmente.

#### Scenario: Blocos omitidos com o flag ativo
- **WHEN** `input_limitado` está ativo e o contexto é montado
- **THEN** o prefixo estável NÃO DEVE conter o conhecimento, os fundamentos nem os resumos, mas DEVE conter o manifesto dos recursos

#### Scenario: Manifesto informa as chaves
- **WHEN** o manifesto é montado
- **THEN** ele DEVE listar as chaves reservadas dos recursos disponíveis e indicar que podem ser solicitadas

#### Scenario: Recursos carregados apenas sob solicitação
- **WHEN** a LLM não solicita recursos na primeira chamada
- **THEN** o conhecimento, os fundamentos e os resumos NÃO DEVEM ser enviados ao provedor

#### Scenario: Comportamento preservado sem o flag
- **WHEN** `input_limitado` está desligado
- **THEN** o prefixo estável DEVE conter o conhecimento, os fundamentos e os resumos, como antes

### Requirement: Confirmação de recursos iniciais sob demanda

Antes de carregar os recursos iniciais (conhecimento, fundamentos e resumos) solicitados pela LLM com `input_limitado` ativo, o sistema DEVE pedir confirmação ao usuário com um texto próprio, distinto do texto de leitura do texto integral de documentos. A recusa NÃO DEVE interromper a interface nem falhar; o sistema DEVE seguir sem os recursos recusados.

#### Scenario: Confirmação com texto próprio
- **WHEN** a LLM solicita recursos iniciais com `input_limitado` ativo
- **THEN** o sistema DEVE exibir um diálogo de confirmação com texto próprio de recursos, não o texto de texto integral de documentos

#### Scenario: Recusa prossegue sem os recursos
- **WHEN** o usuário recusa a confirmação dos recursos
- **THEN** o sistema DEVE seguir sem acrescentar os recursos recusados, sem erro

#### Scenario: Sem o flag não há confirmação de recursos
- **WHEN** `input_limitado` está desligado
- **THEN** nenhum diálogo de confirmação específico de recursos DEVE ser exibido
