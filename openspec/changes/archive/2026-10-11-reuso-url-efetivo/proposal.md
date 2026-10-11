## Why

O registro de URLs baixadas (`deduplicacao-url`) não é populado quando o conteúdo baixado é descartado por já existir no registro de hashes. Como a change anterior passou a interpretar a hora da data de referência, o caminho derivado de muitos documentos relevantes mudou (ex.: assembleias da BBDC3 com `dateReference` em `DD/MM/AAAA HH:MM` foram gravadas no mês da aquisição e agora derivam o mês real). No "Atualizar", o caminho novo não existe, o documento é baixado de novo, o conteúdo coincide com o já registrado e é descartado — mas a URL **nunca** entra no registro. Resultado: os mesmos PDFs são rebaixados a cada atualização (observado em BBDC3/BBAS3).

## What Changes

- **Registrar a URL mesmo com conteúdo duplicado**: quando o download de um documento/notícia tem sucesso mas o conteúdo é descartado por duplicidade exata, a URL DEVE ser registrada apontando para o caminho relativo canônico do arquivo já existente, em vez de ser esquecida.
- **Reuso efetivo do canônico**: uma URL já registrada — inclusive a registrada no descarte por duplicidade — DEVE reutilizar o arquivo canônico sem nova requisição, ainda que o caminho derivado (data/categoria/slug) seja diferente.
- **Serviço de deduplicação expõe o canônico**: o descarte por duplicidade DEVE devolver o caminho relativo canônico do conteúdo, para que o chamador registre a URL correspondente.
- **Mesmo comportamento em Notícias**: o registro global de URLs passa a ser populado também no descarte por duplicidade.

## Capabilities

### New Capabilities
- `reuso-url-efetivo`: registro da URL no descarte por duplicidade e reuso do arquivo canônico por essa URL, em documentos (por ticker) e notícias (global).

### Modified Capabilities
- `deduplicacao-conteudo`: o descarte de duplicata exata passa a expor o caminho relativo canônico do conteúdo já registrado.

## Impact

- Código: `application/deduplicacao.py` (expor o canônico no descarte), `infrastructure/b3/documentos_aquisicao.py` (material facts), `infrastructure/b3/documentos_relevantes.py` (FIIs), `infrastructure/b3/noticias_carga.py` (notícias).
- Cache: nenhum formato novo; o registro de URLs já existente passa a receber entradas no caso de duplicata. Migração: um único rebaixamento por URL legada na primeira atualização após a correção; depois, reuso.
- Sem quebra de contrato de dados; a poda continua removendo a URL ao remover o arquivo canônico.
