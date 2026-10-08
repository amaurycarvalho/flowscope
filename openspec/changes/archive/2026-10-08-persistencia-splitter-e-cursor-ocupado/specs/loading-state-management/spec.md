## ADDED Requirements

### Requirement: Cursor de espera sem vazamento em widgets criados durante a operação
O sistema DEVE garantir que um widget criado após a entrada no estado ocupado — por exemplo um diálogo, painel ou tooltip aberto durante o processamento — não permaneça com o cursor "watch" ao final da operação. Ao reafirmar o cursor de espera sobre o widget sob o ponteiro, o sistema DEVE registrar o cursor de repouso desse widget caso ele ainda não esteja rastreado, de modo que a saída do estado ocupado restaure todos os widgets tocados, inclusive os criados depois do início da operação.

#### Scenario: Widget criado durante a operação não retém o watch
- **WHEN** um widget novo recebe o ponteiro enquanto a operação está ativa
- **THEN** ao término da operação esse widget DEVE voltar ao cursor de repouso, não permanecendo "watch"

#### Scenario: Diálogo aberto durante a operação
- **WHEN** um diálogo é aberto durante a operação e o ponteiro passa sobre um de seus widgets
- **THEN** ao término da operação o widget tocado do diálogo DEVE voltar ao cursor de repouso

### Requirement: Auto-limpeza do cursor de espera na ociosidade
Enquanto o ponteiro se move, o sistema DEVE verificar se há alguma operação ou job de background ativo na autoridade única de estado global. Quando não houver nada ativo, o sistema NÃO DEVE reafirmar o cursor "watch"; em vez disso DEVE remover o cursor de espera residual e encerrar a reafirmação, de modo que um cursor "watch" preso seja limpo no primeiro movimento do ponteiro.

#### Scenario: Movimento do ponteiro sem operação ativa limpa o watch residual
- **WHEN** não há operação nem job de background global ativo e o ponteiro se move sobre um widget que exibia "watch"
- **THEN** o cursor DEVE voltar ao cursor de repouso e a reafirmação do cursor de espera DEVE ser encerrada

#### Scenario: Managers locais não contam como ocupado global
- **WHEN** apenas um envio de chat ou uma pré-visualização de documento está ativo em um manager local
- **THEN** o cursor global NÃO DEVE ser alterado para "watch"
