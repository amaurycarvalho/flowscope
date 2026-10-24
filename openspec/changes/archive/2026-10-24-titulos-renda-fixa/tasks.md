## 1. Modelo e tipos de renda fixa

- [x] 1.1 Criar o pacote de domínio de títulos com os enums `TipoTitulo` e `PapelTitulo` e os read-models `TituloRendaFixa`, `TituloAgregado` e `AusenciaFonte`; verificar com testes unitários de construção e rótulos de exibição
- [x] 1.2 Implementar a chave de fonte determinística e o identificador curto (`sha1` truncado) para FRE, SECURIT, carteira de FII e agregados; verificar estabilidade, ausência de colisão prática e rejeição de caracteres inválidos em testes unitários
- [x] 1.3 Implementar o construtor da árvore normalizada (ticker → Obrigações/Direitos → Títulos → tipo → título/agregado/sem-fonte) a partir dos read-models; verificar com testes para companhia com debêntures, FII com CRI, agregado, `sem-fonte` e ramo vazio

## 2. Parsers e normalização dos datasets CVM

- [x] 2.1 Implementar o parser e o filtro do FRE `outro_valor_mobiliario` para tipos de renda fixa, com seleção da versão/data mais recente e preservação de fonte, data e hash; verificar com fixture de CSV e testes de tipos fora do escopo
- [x] 2.2 Implementar os parsers do SECURIT CRI/CRA (`geral`, `classe`, `cedente_devedor`, `creditos`/`direitos_creditorios`, `ativo_passivo`, `carteira`) e a normalização de emissor legal, devedor, garantias, situação, rating, contingências e atrasos; verificar com fixtures e testes de linhas inválidas
- [x] 2.3 Implementar os parsers do FII `inf_trimestral_fii_ativo` (CRI/CRA e LCI/LCA por título) e do `inf_mensal_fii_ativo_passivo` (agregados de `Debentures` e `Certificados_Deposito_Valores_Mobiliarios`), usando a última data/versão; verificar com testes de posições, agregados e ausência de dados
- [x] 2.4 Implementar o join de CRI/CRA por código CETIP/ISIN e, como fallback, por CNPJ de devedor válido; verificar com testes de casamento por código, por devedor, sem correspondência e CNPJ inválido
- [x] 2.5 Implementar a extração de LTV (`Indice_LTV`/`Data_LTV`) e o fallback explícito "não informado"; verificar que CRA e debêntures não recebem LTV inventado

## 3. Aquisição e cache por ticker

- [x] 3.1 Implementar o serviço `AquisicaoTitulos` com resolução de CNPJ (identidade do FII e FCA para companhia), seleção dos datasets e filtro por ticker; verificar com downloader fake e testes de ticker sem CNPJ e de falha por fonte
- [x] 3.2 Implementar o cache `<cache>/direitos-obrigacoes/<TICKER>.json` com assinatura, `fonte`, `data_referencia`, `parser_version`, `adquirido_em` e escrita atômica; verificar primeira gravação, reutilização sem mudança e substituição com mudança
- [x] 3.3 Implementar a preservação do último cache válido por fonte em falha parcial e a mesclagem de obrigações/direitos; verificar com testes de falha isolada de SECURIT e de FII
- [x] 3.4 Implementar a listagem de material facts da categoria 48 (Aviso aos Debenturistas) como links de documentos relacionados, sem baixar PDF; verificar com cliente B3 fake e teste de links sem download
- [x] 3.5 Verificar a idempotência da aquisição repetida sem mudança de fonte e a não duplicação de títulos; cobrir com teste de execução consecutiva

## 4. Sub-aba Documentos

- [x] 4.1 Estender `DocumentTreeView` para montar Obrigações/Direitos → Títulos → tipos → título/agregado/sem-fonte e registrar os nós no mapa de títulos; verificar com testes de estrutura, agregado, `sem-fonte` e ramo vazio
- [x] 4.2 Estender `DocumentTreePanel` e `DocumentFlowMixin` para selecionar título/agregado/`sem-fonte`, renderizar o Markdown de informações gerais, adicionais, LTV e documentos relacionados, e manter "Abrir documento" desabilitado nesses nós; verificar com testes de pré-visualização e de estado do botão
- [x] 4.3 Preservar expansão e seleção dos nós de títulos ao remontar a árvore do mesmo ticker; verificar com testes de estado de expansão e reseleção
- [x] 4.4 Estender o fluxo do botão "Atualizar" para executar documentos e títulos no mesmo job, com progresso e desfecho distinguíveis, tolerância a falha parcial e remontagem única; verificar com testes de orquestração e de mensagens de status
- [x] 4.5 Garantir que abrir a sub-aba não aciona aquisição de títulos e que a árvore lê apenas o cache; verificar com teste que falha se houver chamada de rede ao exibir

## 5. Chat AI e manifesto

- [x] 5.1 Refatorar `FonteDireitosObrigacoes` para receber o caso de uso/repositório de títulos e montar a árvore aninhada a partir do cache, incluindo `data-referencia`, agregados e `sem-fonte`; verificar com testes de companhia, FII, cache frio e ramo vazio
- [x] 5.2 Atualizar `manifesto.py` com os padrões de caminho de `/direitos-obrigacoes` e a linha de playbook de títulos, anunciando apenas os tipos presentes; verificar com testes de manifesto (incluindo o teto de tokens)
- [x] 5.3 Incluir os arquivos de cache de títulos na lista de caminhos da assinatura do estado em `chat_panel.py` e `cli.py`; verificar que a assinatura muda quando o cache de títulos muda
- [x] 5.4 Conectar a fonte de títulos em `ChatPanel`, `montar_core_navegacao` e composição headless; verificar com testes de composição e de navegação CLI/MCP sem rede

## 6. Documentação e referências

- [x] 6.1 Atualizar `docs/misc/datasources.md` com os datasets FRE/SECURIT/FII, joins, cobertura e limitações (CDB/LCI/LCA sem fonte por emissor); verificar por revisão do documento
- [x] 6.2 Atualizar referências de arquitetura/README que citem o ramo placeholder de Direitos e Obrigações; verificar por busca textual e revisão

## 7. Verificação da change

- [x] 7.1 Executar `make lint` e corrigir os problemas encontrados; verificar saída sem erros
- [x] 7.2 Executar `make complexity` e corrigir os problemas encontrados; verificar saída sem erros
- [x] 7.3 Executar os testes relacionados/impactados (domínio, aplicação, infraestrutura CVM, apresentação, chat/manifesto) e corrigir falhas; verificar a suíte relacionada verde
- [x] 7.4 Executar `make test`
