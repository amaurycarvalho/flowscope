## Why

A aquisição B3 tem dois dados capturados que não passam pelo cache: o HTML bruto dos documentos do FundosNet (proventos `type=41` e informe mensal `type=40`) e as respostas de `GetListClassFund` usadas na resolução de identidade. Como resultado, cada execução da análise fundamentalista rebaixa os mesmos documentos (cerca de uma dezena por FII) e reconsulta a identidade de cada ticker, mesmo com o conteúdo imutável por `id` de documento e a identidade estável por fundo. A CVM já persiste seus arquivos anuais; falta fechar essa lacuna na B3 e uniformizar as políticas de cache.

## What Changes

- **Cachear o HTML do documento FundosNet** em `B3FundosClient.buscar_html_documento`, indexado pelo `id` do documento e aplicável tanto a proventos (`type=41`) quanto ao informe mensal (`type=40`), evitando o rebaixamento a cada análise.
- **Cachear `GetListClassFund`** em `B3FundosClient.listar_candidatos`, indexado pelo `id` primário do fundo, para que `B3FundRepository.find_by_ticker` não reconsulte a B3 a cada execução.
- **Consistência**: centralizar TTLs e nomes de chave em constantes do cliente e **versionar as chaves de cache** com a versão do parser/aquisição, de modo que uma mudança de parser invalide os registros anteriores.
- Cobrir com testes a ausência de requisição HTTP na segunda chamada (documento e identidade) e a invalidação por versão.

## Capabilities

### New Capabilities
<!-- Nenhuma capability nova: a mudança estende requisitos da aquisição B3 existente. -->

### Modified Capabilities
- `b3-fii-extraction`: novos requisitos de cache do documento FundosNet (proventos e informe mensal), cache da resposta de identidade (`GetListClassFund`) e chaves de cache versionadas com políticas centralizadas.

## Impact

- **Código**: `infrastructure/b3/funds_client.py` (cache de documento e de identidade, constantes de TTL/chave) e testes em `tests/test_infrastructure/test_structured_b3.py` e `tests/test_infrastructure/test_b3_acquisition.py`.
- **Cache**: novas chaves em `~/.cache/flowscope/` para HTML de documento e resposta de identidade; sem mudança de diretório.
- **Contratos**: nenhuma porta ou assinatura pública muda; o comportamento observável passa a evitar requisições repetidas e a servir cache em falha de rede quando houver conteúdo armazenado.
- **Fora de escopo**: Fundamentus (já cacheado), ZIPs/CSVs anuais da CVM (já cacheados) e qualquer alteração de parsing.
