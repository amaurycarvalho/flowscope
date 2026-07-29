## ADDED Requirements

### Requirement: VectorStore em SQLite puro
O sistema DEVE implementar um `VectorStore` usando `sqlite3` da stdlib, sem dependências externas, com tabela `chunks` contendo colunas `id`, `ticker`, `categoria`, `id_documento`, `descricao`, `data_referencia`, `url`, `texto`, `embedding` (BLOB JSON) e `chunk_index`. O banco DEVE ser armazenado em `~/.flowscope/fii_docs.db`.

#### Scenario: Criação do banco na primeira execução
- **WHEN** `VectorStore(db_path)` é instanciado com um path que não existe
- **THEN** o banco SQLite e a tabela `chunks` DEVEM ser criados automaticamente

#### Scenario: Inserção com deduplicação
- **WHEN** `add()` é chamado com um chunk cujo `id` já existe
- **THEN** o chunk existente NÃO DEVE ser sobrescrito (`INSERT OR IGNORE`)

### Requirement: Busca por cosine similarity
O sistema DEVE implementar busca top-k por cosine similarity em Python puro, calculando `dot(a,b) / (norm(a) * norm(b))` para cada linha e retornando as k mais similares, com filtro opcional por `ticker`.

#### Scenario: Busca sem filtro de ticker
- **WHEN** `search(query_embedding, k=5)` é chamado sem `ticker`
- **THEN** todas as linhas da tabela DEVEM ser avaliadas e as top-5 retornadas

#### Scenario: Busca com filtro de ticker
- **WHEN** `search(query_embedding, ticker="ALZR11", k=3)` é chamado
- **THEN** apenas chunks com `ticker = "ALZR11"` DEVEM ser avaliados

#### Scenario: Banco vazio
- **WHEN** `search()` é chamado com banco sem chunks
- **THEN** lista vazia DEVE ser retornada sem erro

### Requirement: Chunker de texto
O sistema DEVE implementar `chunk_text(texto: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]` em Python puro, dividindo por parágrafos e juntando parágrafos adjacentes até atingir `chunk_size` com sobreposição de `overlap` caracteres entre chunks consecutivos.

#### Scenario: Texto menor que chunk_size
- **WHEN** `chunk_text("texto curto", chunk_size=1000)` é chamado
- **THEN** uma lista com um único elemento DEVE ser retornada

#### Scenario: Texto com múltiplos chunks
- **WHEN** um texto de 3000 caracteres é processado com `chunk_size=1000, overlap=200`
- **THEN** 4 chunks DEVEM ser gerados, cada um com sobreposição ao anterior

#### Scenario: Texto vazio
- **WHEN** `chunk_text("")` é chamado
- **THEN** lista vazia DEVE ser retornada
