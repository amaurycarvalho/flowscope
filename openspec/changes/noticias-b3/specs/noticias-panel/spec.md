## Purpose

Fornece a sub-aba "Notícias" na Análise Geral, com árvore dos artigos, pré-visualização do conteúdo, resumos por LLM e controles de atualização.

## ADDED Requirements

### Requirement: Sub-aba "Notícias" na Análise Geral

O sistema DEVE expor a sub-aba "Notícias" na "Análise Geral", organizando as notícias em uma árvore e exibindo o conteúdo do artigo selecionado em um campo de texto. A sub-aba DEVE oferecer botões "Atualizar", "Abrir", "I.A." (configuração) e "Resumir pendentes", com barra de progresso durante a aquisição.

#### Scenario: Árvore e pré-visualização
- **WHEN** a sub-aba "Notícias" é exibida com notícias em cache
- **THEN** a árvore DEVE listar as notícias e a seleção DEVE exibir o texto do artigo

#### Scenario: Atualização com progresso
- **WHEN** o usuário aciona "Atualizar"
- **THEN** a aquisição DEVE rodar em segundo plano com progresso e reexibir a árvore ao concluir

#### Scenario: Sem notícias
- **WHEN** não há notícias para o período
- **THEN** a sub-aba DEVE exibir um estado vazio, sem erro

### Requirement: Pré-visualização e abertura do artigo

O sistema DEVE extrair o texto do HTML do artigo em cache para a pré-visualização e DEVE permitir abrir a URL do artigo no navegador padrão. Artigos sem texto extraível DEVEM exibir uma mensagem informativa.

#### Scenario: Artigo com texto
- **WHEN** um artigo com HTML legível é selecionado
- **THEN** o texto extraído DEVE ser exibido na pré-visualização

#### Scenario: Artigo sem texto extraível
- **WHEN** o HTML do artigo não produz texto
- **THEN** a pré-visualização DEVE exibir a mensagem de ausência de texto

#### Scenario: Abrir no navegador
- **WHEN** o usuário aciona "Abrir" em uma notícia com URL
- **THEN** a URL DEVE ser aberta no navegador padrão

### Requirement: Resumo curto e longo por LLM

O sistema DEVE gerar, para cada notícia, um resumo curto e um longo usando a LLM, persistindo-os em cache por notícia. A geração DEVE reutilizar o serviço de resumo existente e tolerar falhas da LLM sem interromper o processamento em lote. Quando a LLM não estiver configurada, a sub-aba DEVE orientar a configuração.

#### Scenario: Geração de resumo
- **WHEN** a LLM está configurada e o artigo tem texto, mas não tem resumo
- **THEN** os resumos curto e longo DEVEM ser gerados e persistidos

#### Scenario: LLM não configurada
- **WHEN** a LLM não está configurada
- **THEN** a sub-aba DEVE orientar a configuração, sem gerar resumos

#### Scenario: Falha da LLM no lote
- **WHEN** a geração de resumo de um item falha durante o lote
- **THEN** o erro DEVE ser registrado e os demais itens DEVEM continuar
