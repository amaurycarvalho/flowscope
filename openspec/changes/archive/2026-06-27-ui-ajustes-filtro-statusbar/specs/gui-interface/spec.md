## MODIFIED Requirements

### Requirement: Campo multilinha de seleção de tickers
O sistema DEVE fornecer um campo de texto multilinha onde o usuário pode editar a lista de tickers (um por linha). O sistema DEVE fornecer um botão "Filtrar" ao lado de "Salvar Tickers" e "Carregar Tickers". As alterações no campo de texto NÃO DEVEM atualizar os gráficos automaticamente. O filtro DEVE ser aplicado apenas quando o botão "Filtrar" for pressionado manualmente. O botão "Carregar Tickers" DEVE preencher o campo sem aplicar o filtro automaticamente.

#### Scenario: Filtro manual via botão "Filtrar"
- **WHEN** o usuário edita a lista de tickers e clica no botão "Filtrar"
- **THEN** os gráficos DEVEM ser atualizados para refletir apenas os tickers presentes no campo

#### Scenario: Edição manual não atualiza gráficos
- **WHEN** o usuário digita ou apaga tickers no campo texto
- **THEN** os gráficos NÃO DEVEM ser atualizados

#### Scenario: Carregar tickers de arquivo não atualiza gráficos
- **WHEN** o usuário clica em "Carregar Tickers" e seleciona um arquivo
- **THEN** o campo DEVE ser preenchido com os tickers do arquivo, e os gráficos NÃO DEVEM ser atualizados
