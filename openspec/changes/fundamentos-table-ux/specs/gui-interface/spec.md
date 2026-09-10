## ADDED Requirements

### Requirement: Persistência da largura das colunas da tabela fundamentalista
O sistema DEVE armazenar no arquivo de configuração (`config.json`) a largura de cada coluna da tabela fundamentalista quando o usuário a ajusta e DEVE restaurá-las na próxima execução, associando cada largura ao identificador estável da coluna.

#### Scenario: Largura restaurada na próxima execução
- **WHEN** o usuário redimensiona uma coluna e reabre a aplicação
- **THEN** a coluna DEVE reaparecer com a largura ajustada

#### Scenario: Sem preferência salva
- **WHEN** não há larguras salvas para a tabela fundamentalista
- **THEN** o sistema DEVE usar as larguras padrão

### Requirement: Mensagens de status da análise fundamentalista
O sistema DEVE exibir, na barra de status, o sufixo `" - cached"` no progresso de um ticker cujo dado veio do cache (`HIT` ou `REVALIDATED`) e, ao final da carga, DEVE exibir uma mensagem de desfecho: `"Dados atualizados com sucesso."` sem falhas, `"Dados atualizados com mitigação de falhas."` quando houver falha recuperável, e `"Falha ao atualizar dados"` em falha catastrófica.

#### Scenario: Dado vindo do cache
- **WHEN** o dado de um ticker é servido do cache durante a análise
- **THEN** o progresso do ticker DEVE exibir o sufixo `" - cached"`

#### Scenario: Carga concluída sem falhas
- **WHEN** a análise fundamentalista termina sem falha na captura
- **THEN** a barra de status DEVE exibir `"Dados atualizados com sucesso."`

#### Scenario: Carga concluída com falha recuperável
- **WHEN** a análise fundamentalista termina com ao menos uma falha recuperável
- **THEN** a barra de status DEVE exibir `"Dados atualizados com mitigação de falhas."`

#### Scenario: Falha catastrófica
- **WHEN** a análise fundamentalista não consegue concluir
- **THEN** a barra de status DEVE exibir `"Falha ao atualizar dados"`
