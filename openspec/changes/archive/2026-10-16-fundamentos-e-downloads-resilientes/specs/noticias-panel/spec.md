## ADDED Requirements

### Requirement: Resolução resiliente do documento vinculado

A resolução do documento vinculado de uma notícia "Geral" (visualizadores do FNET e da CVM RAD) DEVE usar o download resiliente compartilhado (`download-conteudo-resiliente`): validar o conteúdo baixado (PDF) e, em host intermitente, repetir a requisição e renovar a sessão/token do visualizador dentro do orçamento por item já aplicado à resolução. Ao esgotar o orçamento ou obter conteúdo inválido, o corpo original DEVE ser mantido, sem erro, e a notícia DEVE permanecer pendente para nova tentativa.

#### Scenario: Documento do FNET validado e repetido
- **WHEN** o visualizador do FNET devolve uma resposta de sucesso sem PDF válido
- **THEN** o sistema DEVE repetir a resolução dentro do orçamento e só usar o conteúdo se for um PDF válido

#### Scenario: Documento da CVM renovado após falha
- **WHEN** o pedido do PDF ao visualizador da CVM falha com erro transitório
- **THEN** o sistema DEVE re-obter a página do documento (novo token/sessão) e repetir o pedido do PDF

#### Scenario: Conteúdo inválido mantém o corpo original
- **WHEN** a resolução termina sem PDF válido ou com o orçamento esgotado
- **THEN** o corpo original DEVE ser mantido e a notícia DEVE permanecer pendente, sem erro
