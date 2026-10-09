## MODIFIED Requirements

### Requirement: Pré-visualização textual

Ao selecionar um arquivo, o sistema DEVE exibir uma pré-visualização textual em caixa de texto somente-leitura ao lado da árvore. Para arquivos HTML, o texto DEVE ser derivado do HTML; para PDFs, o texto DEVE ser extraído com `pypdf`. A extração DEVE ocorrer fora da thread da interface, com estado de carregamento, e DEVE resultar em mensagem informativa quando não houver texto extraível. A extração de PDF DEVE tolerar falhas por página, preservando o texto das páginas legíveis. O texto do documento DEVE ser lido do cache persistente de texto por documento; a conversão do arquivo DEVE ocorrer apenas quando o texto ainda não estiver em cache, e o resultado DEVE ser gravado no cache para os acessos seguintes. A pré-visualização de um documento DEVE ser composta pelo `long_summary`, por uma linha em branco, pelo texto do guidance do Relatório Gerencial quando houver, por outra linha em branco, por uma linha contendo `---`, outra linha em branco e o texto integral do documento. O guidance exibido DEVE ser o do Relatório Gerencial específico selecionado e DEVE usar a mesma formatação do item da coluna `Informações adicionais` da sub-aba "Fundamentos". Para documento que não seja um Relatório Gerencial ou sem guidance avaliado, o guidance DEVE ser omitido, mantendo-se a composição pelo `long_summary`, linha em branco, `---`, linha em branco e o texto integral; na ausência de `long_summary`, o guidance, quando houver, DEVE figurar imediatamente antes do `---`.

A leitura do cache de texto e a avaliação de necessidade de resumo/guidance do documento DEVEM ocorrer fora da thread da interface; a thread do Tk DEVE apenas publicar o estado de carregamento e exibir o resultado final.

Quando o PDF estiver protegido por senha e o texto não puder ser extraído com senha vazia, o sistema DEVE solicitar a senha ao usuário em caixa de diálogo, na thread da interface, e tentar novamente a extração com a senha informada, fora da thread da interface. A solicitação DEVE ser limitada a 3 tentativas por documento/seleção (parametrizável), avisando sobre a senha incorreta e parando ao esgotar o limite. O texto obtido DEVE ser gravado no cache e a senha NÃO DEVE ser persistida. Cancelar a solicitação DEVE resultar na mensagem informativa de ausência de texto, sem erro. A solicitação DEVE ocorrer apenas no fluxo interativo de pré-visualização; o resumo em lote NÃO DEVE abrir diálogo de senha.

Quando a extração resultar parcial (ao menos uma página não extraída), a pré-visualização DEVE anotar a quantidade de páginas não extraídas antes do conteúdo. O texto parcial NÃO DEVE ser gravado no cache nem usado para gerar resumo, de modo que o documento permaneça pendente. A extração parcial DEVE ser retentada automaticamente quando o documento for selecionado ou clicado novamente e quando "Resumir pendentes" for acionado, sem controle dedicado de "Tentar novamente".

#### Scenario: Seleção de PDF
- **WHEN** o usuário seleciona um arquivo PDF
- **THEN** o sistema DEVE exibir o texto extraído do PDF na caixa somente-leitura

#### Scenario: Seleção de HTML
- **WHEN** o usuário seleciona um arquivo HTML
- **THEN** o sistema DEVE exibir o texto derivado do HTML na caixa somente-leitura

#### Scenario: Extração sem texto
- **WHEN** o arquivo não tem texto extraível
- **THEN** o sistema DEVE exibir uma mensagem informativa, sem erro

#### Scenario: Página ilegível preserva o restante
- **WHEN** um PDF tem uma página ilegível e outras legíveis
- **THEN** o sistema DEVE exibir o texto das páginas legíveis, sem erro

#### Scenario: Texto parcial é anotado
- **WHEN** um PDF é extraído parcialmente
- **THEN** a pré-visualização DEVE exibir a anotação com o número de páginas não extraídas antes do texto

#### Scenario: Texto parcial não gera resumo
- **WHEN** um PDF é extraído parcialmente e a LLM está configurada
- **THEN** o sistema NÃO DEVE gerar resumo nem persistir o texto parcial, mantendo o documento pendente

#### Scenario: Selecionar novamente retenta a extração parcial
- **WHEN** o documento foi extraído parcialmente e o usuário o seleciona ou clica nele novamente
- **THEN** o sistema DEVE refazer a extração do documento, sem exigir controle dedicado

#### Scenario: Resumir pendentes retenta a extração parcial
- **WHEN** o documento foi extraído parcialmente e o usuário aciona "Resumir pendentes"
- **THEN** o sistema DEVE refazer a extração do documento e, se completa, gerar o resumo; se ainda parcial, mantê-lo pendente

#### Scenario: PDF protegido solicita senha
- **WHEN** o usuário seleciona um PDF protegido cujo texto não foi extraído com senha vazia
- **THEN** o sistema DEVE abrir uma caixa de diálogo solicitando a senha

#### Scenario: Senha correta extrai e cacheia
- **WHEN** o usuário informa a senha correta do PDF protegido
- **THEN** o sistema DEVE extrair o texto, gravá-lo no cache e exibi-lo na pré-visualização

#### Scenario: Senha incorreta permite nova tentativa
- **WHEN** o usuário informa uma senha incorreta e ainda há tentativas disponíveis
- **THEN** o sistema DEVE informar a falha e permitir nova tentativa ou cancelamento

#### Scenario: Limite de tentativas atingido
- **WHEN** o usuário esgota as 3 tentativas de senha do documento
- **THEN** o sistema DEVE parar de solicitar a senha e exibir a mensagem informativa, sem erro

#### Scenario: Cancelamento exibe ausência de texto
- **WHEN** o usuário cancela a solicitação de senha
- **THEN** o sistema DEVE exibir a mensagem informativa de ausência de texto, sem erro

#### Scenario: Lote não solicita senha
- **WHEN** o resumo em lote processa um PDF protegido
- **THEN** o sistema NÃO DEVE abrir diálogo de senha e DEVE pular o documento

#### Scenario: Documento com resumo longo
- **WHEN** o documento selecionado tem `long_summary` preenchido
- **THEN** a caixa DEVE exibir o `long_summary`, seguido de linha em branco, `---`, linha em branco e o texto integral do documento

#### Scenario: RG com guidance intercala o texto
- **WHEN** o usuário seleciona um Relatório Gerencial com guidance avaliado
- **THEN** a caixa DEVE exibir o `long_summary`, uma linha em branco, o texto do guidance, uma linha em branco, `---`, uma linha em branco e o texto integral do documento

#### Scenario: RG sem guidance mantém a composição
- **WHEN** o usuário seleciona um Relatório Gerencial sem guidance avaliado
- **THEN** a caixa DEVE exibir a composição sem o item de guidance

#### Scenario: Documento de outra categoria não exibe guidance
- **WHEN** o usuário seleciona um documento que não é um Relatório Gerencial e existe guidance no ledger do ticker
- **THEN** a caixa NÃO DEVE exibir o item de guidance

#### Scenario: Texto lido do cache
- **WHEN** o texto de um documento já está em cache e o documento é selecionado
- **THEN** a caixa DEVE exibir o texto do cache, sem reconverter o arquivo

#### Scenario: Conversão apenas no primeiro acesso
- **WHEN** o texto de um documento não está em cache e o documento é selecionado
- **THEN** o sistema DEVE converter o arquivo, gravar o texto no cache e exibir a pré-visualização

#### Scenario: Interface não bloqueada pela leitura de cache
- **WHEN** um documento já está em cache e é selecionado
- **THEN** a thread do Tk NÃO DEVE ler o cache nem avaliar resumo/guidance antes de exibir o estado de carregamento

#### Scenario: Resultado do preview é publicado na thread do Tk
- **WHEN** o worker de pré-visualização conclui a leitura do cache e a geração do resumo
- **THEN** a pré-visualização DEVE ser aplicada à caixa somente-leitura na thread do Tk

#### Scenario: Documento já resumido abre direto
- **WHEN** o documento tem texto em cache e resumo disponível
- **THEN** a pré-visualização DEVE ser exibida sem reavaliação síncrona na thread do Tk

#### Scenario: Lote recompõe o preview com o guidance
- **WHEN** o resumo em lote é aplicado ao documento atualmente selecionado e há guidance avaliado para ele
- **THEN** a pré-visualização recomposta DEVE incluir o item de guidance

### Requirement: Botão "Resumir pendentes" na barra de documentos

A sub-aba "Documentos" DEVE exibir um botão "Resumir pendentes" na barra de controles, imediatamente após o seletor de modelo ativo e o botão de configuração, sempre visível. O botão DEVE estar habilitado somente quando a LLM estiver configurada, nenhum resumo em lote estiver em andamento e existir, no ticker apresentado, ao menos um documento sem `long_summary` ou — quando a IA estiver ativa — ao menos um Relatório Gerencial (documento da categoria `Relatorio`, própria de FII) cuja avaliação de guidance no ledger esteja ausente ou não marcada como `ia`; caso contrário DEVE estar desabilitado. O Relatório Gerencial É o documento de FII usado como gatilho; não se DEVE depender da classificação de tipo do ticker, indisponível no painel. A LLM DEVE ser considerada configurada quando o provedor for diferente de `none` e as dependências `[llm]` estiverem presentes. A verificação de pendências de guidance DEVE consultar o ledger fora da thread da interface, junto da leitura do catálogo, e a thread do Tk NÃO DEVE ler o ledger ao reavaliar o botão. Ao salvar a configuração ou trocar o provedor pelo combobox, o estado do botão DEVE ser reavaliado. Durante o lote e durante as cargas de dados, o botão DEVE ser desabilitado e restaurado ao término, junto com os demais controles do painel.

#### Scenario: Botão disponível na barra

- **WHEN** o usuário navega para a sub-aba "Documentos"
- **THEN** o botão "Resumir pendentes" DEVE ser exibido imediatamente após o seletor de modelo ativo e o botão de configuração

#### Scenario: Habilitado com pendentes e LLM configurada

- **WHEN** a LLM está configurada e o ticker apresentado tem ao menos um documento sem `long_summary`
- **THEN** o botão "Resumir pendentes" DEVE estar habilitado

#### Scenario: Habilitado com RGs já resumidos pendentes de guidance

- **WHEN** a LLM está configurada, todos os documentos do ticker apresentado já têm `long_summary` e ao menos um Relatório Gerencial (categoria `Relatorio`) não tem avaliação de guidance marcada como `ia`
- **THEN** o botão "Resumir pendentes" DEVE estar habilitado

#### Scenario: Desabilitado com pendências de guidance sem IA

- **WHEN** a IA não está configurada e o único pendente é um Relatório Gerencial já resumido sem avaliação de guidance marcada como `ia`
- **THEN** o botão "Resumir pendentes" DEVE estar desabilitado

#### Scenario: Sem Relatório Gerencial não habilita por guidance

- **WHEN** o ticker apresentado só tem documentos de outras categorias, todos com `long_summary`, ainda que exista guidance no ledger
- **THEN** o botão "Resumir pendentes" DEVE estar desabilitado

#### Scenario: Desabilitado sem LLM configurada

- **WHEN** a LLM não está configurada
- **THEN** o botão "Resumir pendentes" DEVE estar desabilitado, sem ser ocultado

#### Scenario: Desabilitado sem pendentes

- **WHEN** todos os documentos do ticker apresentado já têm `long_summary` e não há Relatório Gerencial pendente de guidance
- **THEN** o botão "Resumir pendentes" DEVE estar desabilitado

#### Scenario: Reavaliação quando o catálogo muda

- **WHEN** o último documento pendente passa a ter `long_summary` por um resumo individual (sem troca de aba) e não há RGs pendentes de guidance
- **THEN** o botão "Resumir pendentes" DEVE ser reavaliado e ficar desabilitado

#### Scenario: Reavaliação após salvar a configuração

- **WHEN** o usuário salva uma configuração de LLM válida no diálogo de configuração e há documentos pendentes
- **THEN** o botão "Resumir pendentes" DEVE passar a estar habilitado

#### Scenario: Reavaliação após trocar o modelo

- **WHEN** o usuário troca o provedor ativo pelo combobox e há documentos pendentes
- **THEN** o botão "Resumir pendentes" DEVE ser reavaliado conforme a disponibilidade da LLM

#### Scenario: Desabilitado durante o lote e cargas de dados

- **WHEN** um resumo em lote ou uma carga de dados está em andamento
- **THEN** o botão "Resumir pendentes" DEVE ser desabilitado junto com os demais controles do painel e restaurado ao término

### Requirement: Resumo em lote dos documentos pendentes

Ao acionar o botão "Resumir pendentes", o sistema DEVE processar, fora da thread da interface, os documentos do ticker apresentado sem `long_summary` e os Relatórios Gerenciais (categoria `Relatorio`, própria de FII) já resumidos cuja avaliação de guidance esteja pendente (entrada ausente no ledger ou não marcada como `ia`, com a IA ativa), em duas fases: preparar o texto — reutilizando o texto em cache e convertendo apenas quando ausente — e gerar o resumo via LLM, como se cada documento tivesse sido selecionado. Para os Relatórios Gerenciais já resumidos, a geração de resumo DEVE ser pulada e apenas a avaliação de guidance DEVE ocorrer, reaproveitando os resumos e o texto em cache, sem reextrair o arquivo. Cada resumo gerado DEVE ser gravado no cache persistente imediatamente após a sua geração e antes de processar o próximo documento, na própria thread de trabalho, de modo que uma interrupção — cancelamento, fechamento do aplicativo ou falha — preserve todos os resumos já gerados e perca no máximo o documento em processamento. O `short_summary` e o `long_summary` resultantes DEVEM ser refletidos no catálogo do documento. O andamento DEVE ser exibido na barra de status com a barra de progresso, uma fase por vez. Documentos sem texto extraível DEVEM ser pulados, sem chamada à LLM. Ao concluir, o sistema DEVE exibir o desfecho e reavaliar o estado do botão.

#### Scenario: Lote com documentos pendentes
- **WHEN** o usuário aciona "Resumir pendentes" com a LLM configurada e documentos sem `long_summary`
- **THEN** o sistema DEVE gerar e persistir os resumos de cada documento pendente e exibir o desfecho

#### Scenario: Lote avalia guidance de RG já resumido
- **WHEN** o usuário aciona "Resumir pendentes" e há um Relatório Gerencial já resumido com avaliação de guidance pendente
- **THEN** o sistema DEVE avaliar o guidance desse RG sem regerar seu resumo, reaproveitando os resumos e o texto em cache

#### Scenario: Progresso em duas fases
- **WHEN** o lote está em andamento
- **THEN** a barra de status e a barra de progresso DEVEM exibir a fase corrente ("preparar texto" e, em seguida, "resumir") com o avanço de cada uma, indicando quantos documentos foram concluídos e o total (ex.: `Preparando textos — 3/40`)

#### Scenario: Avanço da fase é exibido durante o processamento
- **WHEN** uma fase processa vários documentos e cada um leva tempo para concluir
- **THEN** a barra de progresso e a barra de status DEVEM avançar a cada documento concluído, sem aguardar o término da fase

#### Scenario: Fase instantânea continua visível
- **WHEN** a preparação dos textos é instantânea (todos os textos já estão em cache) e o lote avança para a fase de resumo
- **THEN** a fase "preparar texto" DEVE ter sido exibida na barra de status antes de "resumir", ainda que por tempo mínimo

#### Scenario: Documento já resumido é pulado
- **WHEN** um documento do ticker já tem `long_summary` e não é um RG pendente de guidance
- **THEN** ele NÃO DEVE ser reprocessado no lote

#### Scenario: Documento sem texto extraível é pulado
- **WHEN** um documento pendente não tem texto extraível
- **THEN** o sistema NÃO DEVE chamar a LLM para ele e DEVE contabilizá-lo como pulado no desfecho

#### Scenario: Resumo gerado fica disponível na lista
- **WHEN** o lote conclui
- **THEN** uma seleção posterior do agrupamento DEVE exibir o `short_summary` dos documentos resumidos

#### Scenario: Persistência imediata por documento
- **WHEN** o lote gera o resumo de um documento e avança para o próximo
- **THEN** o resumo do documento anterior já DEVE estar gravado no cache persistente, antes da geração do próximo

#### Scenario: Interrupção preserva os resumos já gerados
- **WHEN** o lote é cancelado, o aplicativo é fechado ou falha após gerar resumos de alguns documentos
- **THEN** os resumos já gerados DEVEM estar gravados no cache persistente

#### Scenario: Interrupção por erro
- **WHEN** ocorre um erro em qualquer documento durante o lote
- **THEN** o lote DEVE ser interrompido, a barra de status DEVE reportar o documento e um motivo de falha amigável, e os controles DEVEM ser liberados

#### Scenario: Resultado do lote é descartado ao trocar de ticker
- **WHEN** o ticker apresentado muda enquanto o lote está em andamento
- **THEN** os resultados do lote anterior NÃO DEVEM ser aplicados ao novo ticker

### Requirement: Estado derivado do botão "Resumir pendentes" durante o lote

Enquanto um resumo em lote estiver em andamento, o estado derivado do botão "Resumir pendentes" DEVE permanecer desabilitado, ainda que o catálogo mude (documentos passando a ter `long_summary`) ou que a reavaliação de estado seja disparada no meio do processamento. Ao término do lote — conclusão ou interrupção — o estado DEVE ser reavaliado considerando a disponibilidade remanescente: habilitado se a LLM estiver configurada e ainda houver documentos sem `long_summary` ou, com IA ativa, Relatórios Gerenciais pendentes de guidance; desabilitado caso contrário.

#### Scenario: Reavaliação por documento resumido não reabilita durante o lote
- **WHEN** o lote está em andamento e documentos do ticker passam a ter `long_summary` a cada resultado aplicado
- **THEN** o botão "Resumir pendentes" DEVE permanecer desabilitado durante todo o processamento, até o término

#### Scenario: Reavaliação intermediária por resumo individual não reabilita durante o lote
- **WHEN** o lote está em andamento e uma reavaliação do catálogo é disparada (por resumo individual concorrente ou recarregamento do painel)
- **THEN** o botão "Resumir pendentes" DEVE permanecer desabilitado

#### Scenario: Reabilitação ao término com pendentes restantes
- **WHEN** o lote é interrompido por erro e ainda há documentos do ticker sem `long_summary` ou RGs pendentes de guidance
- **THEN** o botão "Resumir pendentes" DEVE voltar a ficar habilitado

#### Scenario: Desabilitado ao término sem pendentes restantes
- **WHEN** o lote conclui e todos os documentos do ticker já têm `long_summary` e não há RGs pendentes de guidance
- **THEN** o botão "Resumir pendentes" DEVE permanecer desabilitado
