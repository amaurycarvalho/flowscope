## ADDED Requirements

### Requirement: Revalidação remota do arquivo anual da CVM

O sistema DEVE revalidar o arquivo anual da CVM contra a fonte remota antes de reutilizar o ZIP local, rebaixando-o apenas quando a fonte indicar alteração, de modo que o ano corrente reflita meses e reapresentações publicados após o primeiro download.

#### Scenario: Fonte inalterada

- **WHEN** os validadores remotos indicam que o arquivo anual não mudou
- **THEN** o sistema DEVE reutilizar o ZIP local sem baixá-lo novamente

#### Scenario: Fonte alterada

- **WHEN** os validadores remotos indicam que o arquivo anual mudou
- **THEN** o sistema DEVE baixar o arquivo novamente e atualizar o hash e os metadados

#### Scenario: Novo mês no ano corrente

- **WHEN** um novo mês é publicado no ZIP do ano corrente
- **THEN** o sistema DEVE rebaixar o arquivo e passar a considerar o novo mês nas consultas

### Requirement: Comportamento stale-on-failure na revalidação da CVM

O sistema DEVE servir o arquivo anual local quando a revalidação remota falhar por indisponibilidade, mantendo a análise funcional e registrando o aviso.

#### Scenario: Falha de rede durante a revalidação

- **WHEN** a checagem remota falha e existe ZIP local
- **THEN** o sistema DEVE utilizar o ZIP local e registrar o aviso, sem interromper a análise

### Requirement: Metadados de revalidação registrados

O sistema DEVE registrar os validadores remotos e o instante da última revalidação junto aos metadados do arquivo anual, permitindo auditoria e decisões futuras de revalidação.

#### Scenario: Metadados atualizados após revalidação

- **WHEN** o arquivo anual é revalidado
- **THEN** os metadados DEVEM registrar os validadores remotos e o instante da revalidação
