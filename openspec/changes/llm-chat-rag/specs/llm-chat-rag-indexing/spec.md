## Purpose

Indexa documentos das fontes disponíveis no VectorStore e responde perguntas por recuperação semântica seguida de prompt RAG.

## ADDED Requirements

### Requirement: Protocolo DocumentoIndexavel

O sistema DEVE definir um protocolo `DocumentoIndexavel` com o método `to_text() -> str`, que produz uma representação textual densa do documento, adequada para chunking e embedding. Entidades que já possuem `to_text()` satisfazem o protocolo.

#### Scenario: Documento com to_text
- **WHEN** `to_text()` é chamado em um documento que implementa o protocolo
- **THEN** o texto DEVE conter os metadados e valores do documento em formato legível

### Requirement: ABC DocumentSource

O sistema DEVE definir uma classe abstrata `DocumentSource` com a propriedade `categoria` e o método `obter_documentos(ticker=None) -> list[DocumentoIndexavel]`, e DEVE fornecer as fontes concretas `MaterialFactsSource` e `NoticiasSource`.

#### Scenario: Ticker sem dados em uma fonte
- **WHEN** uma fonte não tem documentos para o ticker
- **THEN** uma lista vazia DEVE ser retornada sem erro

#### Scenario: Falha em uma categoria
- **WHEN** a listagem de uma categoria de material facts falha
- **THEN** as demais categorias DEVEM continuar e o erro DEVE ser logado

### Requirement: Extração de texto para indexação

O sistema DEVE extrair texto de HTML (informe mensal) e de PDF (documentos relevantes e BDR) para indexação, tolerando documentos sem texto extraível sem interromper o pipeline.

#### Scenario: PDF sem texto extraível
- **WHEN** um PDF em cache não tem texto extraível
- **THEN** o documento DEVE ser ignorado, sem interromper os demais

### Requirement: IndexarDocumentosUseCase

O sistema DEVE expor `IndexarDocumentosUseCase`, que orquestra as `DocumentSource` disponíveis para um ticker: lista documentos → extrai texto → chunk → embed → grava no VectorStore com deduplicação. Erro em uma fonte NÃO DEVE interromper as outras, e o progresso DEVE ser reportado por callback.

#### Scenario: Falha em uma fonte
- **WHEN** uma fonte lança exceção
- **THEN** o caso de uso DEVE registrar o erro e continuar com as demais fontes

### Requirement: ConsultarDocumentosUseCase

O sistema DEVE expor `ConsultarDocumentosUseCase`, que recebe uma pergunta, o VectorStore, o `EmbeddingPort`, o `LLMPort` da `llm-core` e um ticker opcional, executando embed → busca semântica → prompt RAG → resposta com as fontes.

#### Scenario: Sem documentos indexados
- **WHEN** o VectorStore está vazio para o ticker
- **THEN** o sistema DEVE retornar uma orientação para indexar documentos primeiro

#### Scenario: Resposta com fontes
- **WHEN** há chunks relevantes para a pergunta
- **THEN** a resposta DEVE ser acompanhada dos metadados das fontes recuperadas

### Requirement: Construção de prompt RAG

O sistema DEVE construir o prompt RAG combinando um system prompt fixo com os chunks recuperados (fonte e data) e a pergunta do usuário, instruindo a LLM a responder apenas com base nos documentos e a citar as fontes.

#### Scenario: Prompt com contexto e pergunta
- **WHEN** o prompt é construído com 3 chunks e a pergunta "Qual o último rendimento?"
- **THEN** o prompt final DEVE conter as instruções do sistema, os 3 chunks formatados com fonte e data e a pergunta do usuário
