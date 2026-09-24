## Purpose

Armazena e recupera trechos de documentos por similaridade semântica usando apenas a biblioteca padrão, sem dependências nativas adicionais.

## ADDED Requirements

### Requirement: VectorStore em SQLite puro

O sistema DEVE implementar um `VectorStore` usando `sqlite3` da stdlib, sem dependências externas, com tabela de chunks contendo identificador, ticker, categoria, id do documento, descrição, data de referência, url, texto, embedding (BLOB JSON) e índice do chunk. O banco DEVE ser armazenado em `~/.flowscope/fii_docs.db`.

#### Scenario: Criação do banco na primeira execução
- **WHEN** `VectorStore(db_path)` é instanciado com um caminho inexistente
- **THEN** o banco SQLite e a tabela de chunks DEVEM ser criados automaticamente

#### Scenario: Inserção com deduplicação
- **WHEN** `add()` é chamado com um chunk cujo identificador já existe
- **THEN** o chunk existente NÃO DEVE ser sobrescrito

### Requirement: Busca por cosine similarity

O sistema DEVE implementar busca top-k por cosine similarity em Python puro, calculando `dot(a,b) / (norm(a) * norm(b))` para cada linha e retornando as k mais similares, com filtro opcional por ticker.

#### Scenario: Busca sem filtro de ticker
- **WHEN** `search(query_embedding, k=5)` é chamado sem ticker
- **THEN** todas as linhas DEVEM ser avaliadas e as top-5 retornadas

#### Scenario: Busca com filtro de ticker
- **WHEN** `search(query_embedding, ticker="ALZR11", k=3)` é chamado
- **THEN** apenas chunks com o ticker informado DEVEM ser avaliados

#### Scenario: Banco vazio
- **WHEN** `search()` é chamado com banco sem chunks
- **THEN** uma lista vazia DEVE ser retornada sem erro

### Requirement: Chunker de texto

O sistema DEVE implementar `chunk_text(texto, chunk_size=1000, overlap=200)` em Python puro, dividindo por parágrafos e juntando parágrafos adjacentes até atingir `chunk_size`, com sobreposição de `overlap` caracteres entre chunks consecutivos.

#### Scenario: Texto menor que chunk_size
- **WHEN** `chunk_text("texto curto", chunk_size=1000)` é chamado
- **THEN** uma lista com um único elemento DEVE ser retornada

#### Scenario: Texto vazio
- **WHEN** `chunk_text("")` é chamado
- **THEN** uma lista vazia DEVE ser retornada
