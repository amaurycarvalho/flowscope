# llm-chat-gui Specification

## Purpose

Fornece o widget de chat e a aba de topo "Chat AI" na interface gráfica, com os comportamentos de configuração, cópia, atalhos e tratamento de erro.

## Requirements

### Requirement: Widget ChatPanel reutilizável

O sistema DEVE fornecer um widget `ChatPanel(tkinter.Frame)` com área de mensagens com scroll, campo de entrada, botão "Enviar" e copy/paste livre. As respostas DEVEM ser exibidas em campo somente-leitura que permita seleção de texto, cursor visível e atalhos de teclado.

#### Scenario: ChatPanel sem escopo fixo
- **WHEN** `ChatPanel(root)` é criado
- **THEN** o painel DEVE consultar o contexto da watchlist completa, sem seletor de escopo

#### Scenario: Respostas somente-leitura com atalhos
- **WHEN** o usuário interage com o campo de respostas
- **THEN** a edição DEVE ser bloqueada, preservando cursor, seleção e Ctrl+A/C

### Requirement: Aba "Chat AI"

O sistema DEVE expor a aba de topo "Chat AI" na janela principal, entre "Análise do Ticker" e "Sobre", como ponto único de entrada do chat. A aba DEVE permanecer visível e a LLM DEVE inferir o ticker referido na pergunta, sem seletor de escopo.

#### Scenario: Aba posicionada e visível
- **WHEN** a janela principal é exibida
- **THEN** a aba "Chat AI" DEVE estar presente entre "Análise do Ticker" e "Sobre"

#### Scenario: Ticker inferido pela LLM
- **WHEN** o usuário pergunta sobre um ticker
- **THEN** a LLM DEVE identificar o ticker a partir da pergunta, sem que a interface ofereça um seletor de escopo

### Requirement: Estado não configurado e botão "Configuração"

Quando `llm.chat.provider` está ausente ou é `none`, a aba "Chat AI" DEVE permanecer visível, com o campo de entrada desabilitado e exibindo orientação para configurar a LLM. O cabeçalho DEVE ter os botões "Copiar chat" e "Configuração", este último sempre visível logo após "Copiar chat" e abrindo o diálogo de configuração fornecido pela `llm-core`. Ao salvar a configuração, o estado DEVE ser reavaliado.

#### Scenario: Provedor não configurado
- **WHEN** `llm.chat.provider` está ausente ou é `none`
- **THEN** a aba DEVE exibir a orientação de configuração com a entrada desabilitada e o botão "Configuração" disponível

#### Scenario: Configuração salva
- **WHEN** o usuário salva uma configuração válida no diálogo
- **THEN** o campo de entrada DEVE ser habilitado

#### Scenario: Configuração sempre acessível
- **WHEN** a aba "Chat AI" está exibida
- **THEN** o botão "Configuração" DEVE estar visível no cabeçalho, logo após "Copiar chat"

### Requirement: Copiar chat e CSV

O sistema DEVE oferecer um botão "Copiar chat" na aba, que copia o conteúdo da sessão para a área de transferência. A cópia de dados CSV DEVE incluir o conteúdo do chat quando a aba "Chat AI" estiver ativa.

#### Scenario: Copiar chat
- **WHEN** o usuário clica em "Copiar chat"
- **THEN** o conteúdo da sessão DEVE ser copiado para a área de transferência

#### Scenario: CSV com chat ativo
- **WHEN** a aba "Chat AI" está ativa e o usuário aciona a cópia de dados
- **THEN** o conteúdo do chat DEVE ser incluído na cópia

### Requirement: Limpar conversa

O sistema DEVE oferecer um botão "Limpar" no cabeçalho, antes de "Copiar chat", que reinicia a sessão como se estivesse começando agora, limpando as mensagens exibidas e o histórico em memória. Antes de executar, o sistema DEVE pedir confirmação (Sim/Não) ao usuário; se o usuário recusar, a sessão NÃO DEVE ser alterada.

#### Scenario: Limpar confirmado
- **WHEN** o usuário clica em "Limpar" e confirma a operação
- **THEN** a sessão e a área de mensagens DEVEM ficar vazias, como uma conversa recém-iniciada

#### Scenario: Limpar cancelado
- **WHEN** o usuário clica em "Limpar" e recusa a confirmação
- **THEN** a conversa DEVE permanecer inalterada

#### Scenario: Posição do botão
- **WHEN** a aba "Chat AI" está exibida
- **THEN** o botão "Limpar" DEVE estar no cabeçalho, antes de "Copiar chat"

### Requirement: Tratamento de erros da LLM

Falhas da LLM durante o chat DEVEM ser exibidas na barra de status com mensagem amigável e registradas no log do sistema.

#### Scenario: Falha durante o chat
- **WHEN** a LLM fica ou está indisponível durante uma pergunta
- **THEN** a mensagem DEVE aparecer na barra de status e o erro DEVE ser registrado no log

### Requirement: Cancelar o envio da mensagem

O sistema DEVE exibir, ao lado do botão "Enviar", um botão de cancelamento com o ícone `process-stop.png`, habilitado somente enquanto houver um envio em processamento. Ao acioná-lo, o sistema DEVE solicitar a interrupção do processamento, habilitar novamente o botão "Enviar" e desabilitar o botão de cancelamento, sem aguardar o término da thread de trabalho. O desfecho tardio do provedor DEVE ser descartado, sem ser exibido nem registrado na sessão, e a interrupção NÃO DEVE ser tratada como falha.

#### Scenario: Botão desabilitado em repouso
- **WHEN** o painel está ocioso e nenhum envio está em processamento
- **THEN** o botão de cancelamento DEVE estar desabilitado

#### Scenario: Botão habilitado durante o envio
- **WHEN** uma pergunta é enviada e o processamento está em andamento
- **THEN** o botão de cancelamento DEVE ficar habilitado e o botão "Enviar" desabilitado

#### Scenario: Cancelamento restaura os botões
- **WHEN** o usuário aciona o botão de cancelamento durante o processamento
- **THEN** o botão "Enviar" DEVE voltar a ficar habilitado e o de cancelamento desabilitado

#### Scenario: Desfecho tardio é descartado
- **WHEN** o processamento é cancelado e a thread de trabalho conclui ou falha depois
- **THEN** nenhuma mensagem do assistente DEVE ser acrescentada à sessão e nenhuma falha DEVE ser registrada no log

### Requirement: Sessão não persistente

Cada abertura da aba DEVE começar com uma sessão limpa, sem persistência de histórico.

#### Scenario: Reabertura da aba
- **WHEN** a aba "Chat AI" é reaberta
- **THEN** a sessão DEVE iniciar vazia, sem mensagens anteriores

### Requirement: Histórico da conversa enviado ao modelo

No momento do envio e na thread do Tk, o painel DEVE capturar as mensagens bem-sucedidas da sessão, excluindo a pergunta atual e as mensagens marcadas como fora do histórico, e passá-las ao caso de uso, para que a LLM tenha ciência do contexto da conversa. O botão "Limpar" DEVE reiniciar também esse histórico.

#### Scenario: Segundo turno com contexto
- **WHEN** o usuário faz uma segunda pergunta após uma resposta bem-sucedida
- **THEN** o histórico com o primeiro par pergunta/resposta DEVE ser enviado ao caso de uso

#### Scenario: Erro não compõe o histórico
- **WHEN** uma falha da LLM é exibida na conversa e o usuário faz uma nova pergunta
- **THEN** a mensagem de erro NÃO DEVE integrar o histórico enviado

#### Scenario: Limpar reinicia o histórico
- **WHEN** o usuário limpa a conversa
- **THEN** a próxima pergunta DEVE ser enviada sem histórico anterior

### Requirement: Habilitação do botão "Enviar" pelos fundamentos

O botão "Enviar" DEVE habilitar apenas quando a LLM estiver configurada E houver dados de fundamentos carregados pela sub-aba "Fundamentos". Sem fundamentos, o botão DEVE permanecer desabilitado, e a mudança de fundamentos DEVE reavaliar o estado do painel.

#### Scenario: Sem fundamentos carregados
- **WHEN** a LLM está configurada mas nenhum fundamento foi carregado
- **THEN** o botão "Enviar" DEVE estar desabilitado

#### Scenario: Fundamentos carregados
- **WHEN** há fundamentos carregados e a LLM está configurada
- **THEN** o botão "Enviar" DEVE estar habilitado

#### Scenario: Fundamentos chegam com a aba aberta
- **WHEN** os fundamentos são carregados com a aba "Chat AI" já exibida
- **THEN** o botão "Enviar" DEVE ser reavaliado e habilitado

### Requirement: Bloqueio do cabeçalho durante o envio

Enquanto houver um envio em processamento, os botões "Limpar", "Copiar chat" e "Configuração" DEVEM ficar desabilitados, além do "Enviar". Ao término do processamento (resposta, erro ou cancelamento), esses botões DEVEM ser reavaliados e voltar ao normal conforme o estado da conversa.

#### Scenario: Botões desabilitados durante o envio
- **WHEN** uma pergunta é enviada e o processamento está em andamento
- **THEN** "Limpar", "Copiar chat" e "Configuração" DEVEM estar desabilitados

#### Scenario: Botões restaurados ao término
- **WHEN** o processamento termina, com sucesso ou erro
- **THEN** "Configuração" DEVE voltar a ficar habilitado e "Limpar"/"Copiar chat" conforme a existência de conteúdo

#### Scenario: Botões restaurados ao cancelar
- **WHEN** o usuário cancela o envio
- **THEN** "Configuração" DEVE voltar a ficar habilitado, sem aguardar a thread de trabalho

### Requirement: Habilitação de "Limpar" e "Copiar chat" pelo conteúdo

Os botões "Limpar" e "Copiar chat" DEVEM habilitar apenas quando houver conteúdo textual na conversa e desabilitar quando ela estiver vazia, inclusive após "Limpar" e antes da primeira mensagem.

#### Scenario: Conversa vazia
- **WHEN** a conversa não possui mensagens
- **THEN** "Limpar" e "Copiar chat" DEVEM estar desabilitados

#### Scenario: Conversa com conteúdo
- **WHEN** já há texto exibido na conversa
- **THEN** "Limpar" e "Copiar chat" DEVEM estar habilitados

#### Scenario: Após limpar
- **WHEN** o usuário confirma "Limpar"
- **THEN** "Limpar" e "Copiar chat" DEVEM voltar a ficar desabilitados

### Requirement: Orientação no quadro textual da aba "Chat AI"

Quando a aba "Chat AI" estiver ativa, o quadro de texto orientativo DEVE exibir a orientação própria da aba, cobrindo objetivo, requisitos de configuração e de fundamentos, origens do contexto, inferência de ticker e uso dos botões.

#### Scenario: Aba ativa exibe orientação
- **WHEN** a aba "Chat AI" é selecionada
- **THEN** o quadro de texto orientativo DEVE exibir o texto da aba "Chat AI"

#### Scenario: Orientação entra no conhecimento da LLM
- **WHEN** o bloco de conhecimento do FlowScope é montado
- **THEN** a orientação da aba "Chat AI" DEVE integrá-lo por vir de `TAB_CONTENT`

### Requirement: Orientação no quadro textual da aba "Sobre"

Quando a aba "Sobre" estiver ativa, o quadro de texto orientativo DEVE exibir a orientação própria da aba, cobrindo o objetivo, o conteúdo (apresentação, versão, licença e repositório) e o uso dos atalhos de repositório e de log.

#### Scenario: Aba ativa exibe orientação
- **WHEN** a aba "Sobre" é selecionada
- **THEN** o quadro de texto orientativo DEVE exibir o texto da aba "Sobre"

#### Scenario: Orientação entra no conhecimento da LLM
- **WHEN** o bloco de conhecimento do FlowScope é montado
- **THEN** a orientação da aba "Sobre" DEVE integrá-lo por vir de `TAB_CONTENT`
