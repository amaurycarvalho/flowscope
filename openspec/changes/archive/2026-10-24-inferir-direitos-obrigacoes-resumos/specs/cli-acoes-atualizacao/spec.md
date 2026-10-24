## ADDED Requirements

### Requirement: Inferência de direitos e obrigações em `resumir documentos`

O comando `flowscope resumir documentos` DEVE executar a fase opcional de inferência de direitos e obrigações após o processamento dos resumos, reusando as mesmas regras de flag, elegibilidade, cache e proveniência da interface gráfica. A fase DEVE usar os resumos persistidos e NÃO DEVE reabrir PDFs. O JSON de saída DEVE distinguir o desfecho da inferência do desfecho dos resumos, sem quebrar as chaves `pendentes`, `sem_texto`, `nao_conclusivos` e `apontadores` já existentes. Falha da inferência para um ticker NÃO DEVE abortar o lote dos demais.

#### Scenario: Inferência após resumir um ticker
- **WHEN** `flowscope resumir documentos PETR4` conclui os resumos com a inferência habilitada
- **THEN** a inferência DEVE ser executada e o JSON DEVE reportar o desfecho próprio da inferência

#### Scenario: Flag desligada
- **WHEN** a flag de inferência está desligada
- **THEN** o comando DEVE processar apenas os resumos e o JSON NÃO DEVE exigir a chave de inferência

#### Scenario: Falha da inferência não aborta a watchlist
- **WHEN** a inferência falha para um ticker no lote da watchlist
- **THEN** os demais tickers DEVEM continuar, o desfecho daquele ticker DEVE registrar a falha e o comando DEVE encerrar com código 1

#### Scenario: Sem LLM configurada
- **WHEN** nenhum provedor de LLM está configurado
- **THEN** o comando DEVE manter o erro estruturado `llm_nao_configurada` antes de processar qualquer ticker
