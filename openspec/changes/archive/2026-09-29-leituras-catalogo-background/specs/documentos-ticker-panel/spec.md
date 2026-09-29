## ADDED Requirements

### Requirement: Leitura do catálogo fora da thread da interface

O sistema DEVE ler o catálogo de documentos do ticker fora da thread da interface e montar a árvore a partir de um evento na thread do Tk. Enquanto a leitura ocorre, a sub-aba DEVE exibir um estado de carregamento, e a thread do Tk DEVE permanecer responsiva. Trocar de ticker ou acionar a atualização DEVE descartar a leitura anterior em favor da mais recente.

#### Scenario: Ativação com estado de carregamento
- **WHEN** a sub-aba "Documentos" se torna ativa para o ticker apresentado
- **THEN** a leitura do catálogo DEVE ocorrer fora da thread da interface e a árvore DEVE ser montada por evento ao concluir

#### Scenario: Interface responsiva durante a varredura
- **WHEN** a varredura do catálogo de um ticker com muitos documentos está em andamento
- **THEN** a thread do Tk DEVE continuar processando eventos

#### Scenario: Cache frio resulta em estado vazio
- **WHEN** o ticker não tem documentos em cache
- **THEN** a sub-aba DEVE exibir a mensagem de ausência de documentos, sem erro

#### Scenario: Atualização manual relê em background
- **WHEN** o usuário aciona o controle de atualização
- **THEN** a nova varredura DEVE ocorrer fora da thread da interface e remontar a árvore por evento

#### Scenario: Troca de ticker descarta leitura obsoleta
- **WHEN** o ticker apresentado muda enquanto uma leitura de catálogo está em andamento
- **THEN** o resultado da leitura anterior NÃO DEVE ser aplicado ao novo ticker
