## 1. Pré-requisito

- [x] 1.1 Confirmar que a listagem type=40 (`listar_documentos(..., 40)`) e o download HTML (`buscar_html_documento`) já existem e são reutilizáveis
- [x] 1.2 Confirmar que `B3InformeMensal`, `informe_mensal_parser` e `B3ReportsRepository` permanecem inalterados

## 2. Cache de arquivo do informe mensal

- [x] 2.1 Implementar a gravação do HTML em `<cache>/informe-mensal/<TICKER>/<AAAA>/<MM>/<id>.html`, de forma atômica e sem TTL
- [x] 2.2 Derivar ano/mês da data de referência, com fallback para a data de entrega e, por fim, a data corrente
- [x] 2.3 Reutilizar o arquivo existente sem novo download (cache hit)
- [x] 2.4 Tratar falha de download sinalizando o documento, sem criar arquivo e sem interromper outros tickers

## 3. Leitura da árvore

- [x] 3.1 Expor listagem dos documentos em cache de um ticker, ordenados do mais recente ao mais antigo
- [x] 3.2 Retornar lista vazia para ticker sem cache, sem erro

## 4. Testes

- [x] 4.1 Testar gravação, cache hit e caminho por ticker/ano/mês com diretório temporário
- [x] 4.2 Testar derivação de ano/mês (referência, entrega e fallback corrente)
- [x] 4.3 Testar falha de download sem arquivo criado
- [x] 4.4 Testar leitura ordenada e ticker sem documentos

## 5. Quality Gate

- [x] 5.1 Executar `make lint` e corrigir avisos/erros introduzidos
- [x] 5.2 Executar `make test` e garantir que todos os testes passam
- [x] 5.3 Executar `openspec validate informe-mensal` e garantir que a change permanece válida
