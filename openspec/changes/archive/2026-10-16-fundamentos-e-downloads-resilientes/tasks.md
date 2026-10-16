## 1. Fundamentus — host do certificado

- [x] 1.1 Trocar as URLs do Fundamentus (`detalhes.php`, `proventos.php`, `fii_proventos.php`, `robots.txt`) para o host coberto pelo certificado (apex `fundamentus.com.br`), derivando-as de uma única constante em `fundamentus/client.py`; verificar com teste de unidade que as três URLs de dados e a de `robots.txt` usam o host esperado
- [x] 1.2 Ajustar o tratamento de erro do cliente para classificar falha de verificação TLS como indisponibilidade da fonte (distinta de ticker ausente), propagando o erro tipado; verificar com teste de cliente simulado que uma `SSLError` vira indisponibilidade e não `TickerNotFound`
- [x] 1.3 Verificar manualmente que os três endpoints respondem `200` no host do certificado (ex.: `curl -sS -o /dev/null -w '%{http_code}' 'https://fundamentus.com.br/detalhes.php?papel=MXRF11'`)

## 2. Fundamentos — nome de exibição pela identidade B3

- [x] 2.1 Expor o nome de negociação a partir da identidade B3 já consultada (`GetInitialCompanies`: `companyName`/`tradingName`), reaproveitando o cache da resolução; verificar com teste que o nome é retornado para uma ação e que o cache é reutilizado (sem nova chamada)
- [x] 2.2 Remover o fallback do cadastro `empresas-listadas.csv` (URL, `montar_indice_code_cvm`, métodos `_consultar_code_cvm_no_cadastro`/`_carregar_indice_code_cvm`/`_baixar_cadastro_empresas`, TTL e exports) e tornar `resolver_code_cvm` API-only; verificar com testes atualizados que a API indisponível NÃO dispara download de cadastro e que a resolução bem-sucedida segue retornando o `codeCVM`
- [x] 2.3 Deixar de cachear falha de resolução como ausência: em erro de rede/HTTP, propagar sem gravar no cache; cachear `None` apenas quando a API respondeu sem correspondência; verificar com teste de que, após falha, o cache permanece vazio e uma nova chamada reconsulta a API
- [x] 2.4 Injetar o nome da identidade B3 como fallback de `CAMPO_NOME` para ações/BDR na análise (mantendo `fundName` para FII), sem acionar fonte nova; verificar com teste do uso de análise que, sem a fonte primária, o nome de uma ação não fica `N/A` quando a identidade B3 existe

## 3. Helper de download resiliente compartilhado

- [x] 3.1 Estender `executar_com_retry` com um parâmetro opcional de validação de conteúdo (retrocompatível) que trate conteúdo inválido como repetível; verificar com testes de unidade que conteúdo inválido consome tentativa e conteúdo válido retorna na primeira
- [x] 3.2 Criar o helper de download que encapsula sessão, resolução de URL (direta ou `visualizarDocumento → iframe`), override de status por ponto de chamada e **orçamento total por item** (`_Prazo`); verificar com testes de unidade de orçamento esgotado, cancelamento e conteúdo inválido
- [x] 3.3 Cobrir no helper a **renovação de sessão** do `rad.cvm.gov.br` (GET página → POST `ExibirPDF`, refazendo o GET após falha do POST) sob o orçamento; verificar com teste que uma falha do POST dispara novo GET antes da nova tentativa

## 4. Consumidores do helper

- [x] 4.1 Fazer `baixar_pdf_documento` (documentos relevantes) usar o helper com validação `%PDF` e override de `403` do FNET; verificar com testes de que `200` não-PDF é repetido e que o orçamento esgotado não cria arquivo nem interrompe os demais
- [x] 4.2 Fazer `buscar_html_documento` (informe mensal e proventos de Fundamentos) usar o helper com validação de HTML reconhecível, evitando cachear challenge HTML; verificar com testes de que HTML inesperado é repetido e não é persistido
- [x] 4.3 Fazer a resolução do documento vinculado de Notícias (`noticias_vinculo`) delegar ao helper mantendo o orçamento já existente; verificar com testes de que o conteúdo inválido mantém o corpo original e a notícia permanece pendente
- [x] 4.4 Fazer `baixar_pdf_cvm` (material facts de ações/BDR) usar o fluxo com renovação de sessão do `rad.cvm.gov.br`; verificar com teste de que falha transitória do POST renova a página e conclui quando a nova tentativa sucede

## 5. Observabilidade e desfecho

- [x] 5.1 Adicionar callback opcional `on_item(ticker)` ao `FundamentalAnalysisUseCase.execute` (chamado antes de cada ticker) e ligá-lo a `ctx.descrever` no `fundamental_job`; verificar com teste de que o job descreve o ticker corrente antes de processá-lo
- [x] 5.2 Padronizar o registro da fonte indisponível por ticker na composição de fontes; verificar com teste que a fonte e o ticker aparecem no registro e a análise prossegue
- [x] 5.3 Fazer a aquisição de documentos devolver um resultado com contagem de novos/reutilizados/falhas e compor a mensagem de desfecho distinguindo falha de ausência; verificar com testes de apresentação dos três desfechos (adquiridos, nada novo, falhas)

## 6. Dia não útil

- [x] 6.1 Garantir que a janela de datas de negociação exclua dias não úteis e que a ausência/`400` em dia não útil seja tratada como ausência de pregão (sem warning de erro); verificar com teste de calendário/ingestão que um feriado não é requisitado e que a ausência não gera erro

## 7. Verificação da alteração

- [x] 7.1 Rodar `make lint` e `make complexity` e corrigir os apontamentos; verificar com a saída dos comandos
- [x] 7.2 Rodar os testes relacionados/impactados (fundamentos, fundamentus, downloads/documentos, notícias, calendário/ingestão) e corrigir regressões; verificar com a saída do `pytest`
- [x] 7.3 Rodar a suíte completa `make test` por se tratar de alteração transversal (contrato de download compartilhado e `executar_com_retry`).
