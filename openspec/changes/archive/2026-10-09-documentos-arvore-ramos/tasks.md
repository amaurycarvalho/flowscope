## 1. Aplicação — leitura somente-leitura do guidance

- [x] 1.1 Adicionar em `GuidanceService` (`application/documentos/document_guidance.py`) um método que devolva as entradas do ledger com valor, por ano/mês da data do relatório, com a identidade do RG (`caminho_pdf`); verificar que ausências são excluídas e que o ledger não é alterado com teste de aplicação
- [x] 1.2 Adicionar o helper de rótulo curado do RG (`Relatório Gerencial — <mmm/aa> (<nome do arquivo>)`), com fallback para a data do ledger e o basename do caminho quando o documento não estiver no catálogo; verificar com casos com e sem documento

## 2. Worker — carregar o guidance junto do catálogo

- [x] 2.1 Estender `DocumentFlowMixin.carregar_pendentes_guidance` (ou novo método) para também resolver as entradas de guidance do ticker numa única leitura do ledger; verificar com teste headless
- [x] 2.2 Propagar `(catalogo, pendentes, guidances)` em `app_actions._submeter_leitura_documentos`/`_aplicar_catalogo_documentos` e guardar `_guidances` em `aplicar_catalogo`; verificar que nenhuma leitura de ledger ocorre na thread do Tk (teste headless)
- [x] 2.3 Invalidar `_guidances` em `_limpar`; verificar com teste de remontagem

## 3. Árvore de documentos — três ramos

- [x] 3.1 Montar em `DocumentTreeView` a raiz do ticker com os ramos Guidance, Documentos e Direitos e obrigações, mantendo a hierarquia de documentos sob Documentos; verificar estrutura em teste headless
- [x] 3.2 Exibir o ramo Guidance apenas quando houver documentos `Relatorio` no catálogo, agrupando por ano/mês com uma folha por guidance com valor (rótulo via `formatar_guidance`); verificar FII com/sem guidance e não-FII
- [x] 3.3 Adicionar os sub-ramos placeholder Direitos e Obrigações (vazios) e a mensagem de ausência de dados ao selecioná-los; verificar com teste
- [x] 3.4 Manter um índice reverso `caminho → nó` dos arquivos de documentos; verificar com teste de localização
- [x] 3.5 Expandir apenas o primeiro nível na primeira exibição do ticker na sessão e a cada troca de ticker, preservando expansão/seleção nas demais; verificar com teste

## 4. Interações do ramo Guidance

- [x] 4.1 Renderizar, ao selecionar o ramo Guidance/ano/mês, a lista Markdown de todos os guidances do agrupamento; verificar com teste de composição
- [x] 4.2 Ao selecionar uma folha, exibir o texto formatado e, em linha separada ao final, o rótulo curado do RG; verificar com teste
- [x] 4.3 No duplo-clique da folha, localizar o RG pelo índice reverso, expandir ancestrais, selecionar e `see`, sem abrir o arquivo; quando o RG não estiver no catálogo, não saltar nem falhar; verificar ambos os casos

## 5. Remontagem da árvore após "Resumir pendentes"

- [x] 5.1 Em `app_resumos_actions._finalizar_resumos_job`, agendar `self.after(0, self._recarregar_painel_resumos)` e despachar por origem (documentos → `_submeter_leitura_documentos`; notícias → `_submeter_leitura_noticias`); verificar com teste headless do despacho
- [x] 5.2 Separar a limpeza de nós da limpeza de pré-visualização/seleção e preservar o arquivo selecionado na remontagem, reexibindo a pré-visualização fora da thread do Tk; verificar com teste de seleção preservada na sub-aba Documentos
- [x] 5.3 Preservar o item selecionado na remontagem da árvore de notícias; verificar com teste na sub-aba Notícias

## 6. Navegação do Chat AI

- [x] 6.1 Criar `FonteGuidance` montando `/guidance/<ticker>/<ano>/<mes>/<folha>`, com a folha contendo o texto formatado e o rótulo curado do RG, omitindo tickers sem guidance com valor; verificar com teste da fonte
- [x] 6.2 Criar `FonteDireitosObrigacoes` montando `/direitos-obrigacoes/{direitos,obrigacoes}` como folhas-placeholder com conteúdo de ausência de dados; verificar navegação `listar`/`obter`
- [x] 6.3 Agregar as novas fontes em `chat_panel.montar_arvore` e passar os caminhos do ledger de guidance em `caminhos`, para a assinatura de estado; verificar que a gravação de um guidance invalida a assinatura
- [x] 6.4 Atualizar `manifesto.MAPA_ARVORE` com os novos caminhos canônicos e adicionar teste de teto de tokens do manifesto com os ramos novos

## 7. Verificação integrada

- [x] 7.1 Executar `make lint` e `make complexity` sem erros
- [x] 7.2 Executar `make test` (cobertura ≥ 85%) sem erros.
- [x] 7.3 Confirmar manualmente: os três ramos aparecem expandidos só no primeiro nível; o ramo Guidance navega, exibe texto + RG e o duplo-clique salta para o RG; Direitos/Obrigações aparecem vazios; o Chat AI navega `/guidance/...` e `/direitos-obrigacoes/...`; a árvore é remontada ao fim de "Resumir pendentes" nas duas sub-abas com a seleção preservada
