## Context

Ver `proposal.md` — Why. O registro de URLs por escopo existe (`infrastructure/url_downloads.py`, change `resumos-pendentes-e-downloads`), assim como o registro de hashes de conteúdo por escopo (`infrastructure/content_hashes.py`). A deduplicação de conteúdo é coordenada por `DeduplicacaoConteudo` (`application/deduplicacao.py`), cujo `processar` devolve um booleano: `False` quando o conteúdo já está registrado, sem informar qual é o arquivo canônico. Os chamadores (`_persistir_material_fact`, `DocumentosRelevantesProvider.persistir`, `AquisicaoNoticias._persistir`) só registram a URL quando gravam um arquivo novo, deixando a URL órfã no caso de duplicata.

## Goals / Non-Goals

**Goals:**
- Registrar a URL sempre que o download tem sucesso, inclusive quando o conteúdo é descartado por duplicidade.
- Fazer a URL registrada apontar para o caminho canônico real do arquivo.
- Reusar o canônico sem nova requisição em execuções posteriores, em documentos e notícias.

**Non-Goals:**
- Migrar/realocar arquivos legados gravados no mês de fallback (permanecem como canônicos; a URL passa a apontar para eles).
- Alterar a política "primeiro hash vence" nem o housekeeping.
- Persistir o registro de URL em outro formato ou mudar o schema.

## Decisions

### 1. O serviço de deduplicação expõe o canônico do descarte

Adicionar `DeduplicacaoConteudo.processar_e_resolver(conteudo, caminho, gravar) -> tuple[bool, str | None]`, que grava quando novo e devolve o relativo gravado; quando duplicata, devolve `(False, canonico)` consultando o registro de hashes. `processar` passa a ser um invólucro que descarta o canônico, preservando o contrato atual e os testes. Alternativa: consultar o `JsonHashStore` diretamente nos chamadores — rejeitada por vazar a composição interna do serviço.

### 2. A URL é registrada apontando para o canônico

Nos três pontos de aquisição, usar `processar_e_resolver`; se houver canônico, registrar a URL para `cache_root / canonico` e considerar o item reutilizado (arquivo existente). Assim a mesma URL nunca é rebaixada de novo, mesmo que o caminho derivado mude. Alternativa: registrar a URL para o caminho derivado — falha porque o arquivo não está lá e `caminho_registrado` voltaria a `None`.

### 3. Reuso uniforme em documentos e notícias

Documentos: escopo por ticker (`url-downloads/<TICKER>.json`); notícias: escopo global (`noticias/url-downloads.json`). O código já centraliza o registro em `JsonUrlStore`; a mudança é apenas passar a chamá-lo também no caminho de duplicata. Em notícias, a entrada de índice passa a apontar para o canônico quando a duplicata é descartada.

### 4. Poda inalterada

`podar_documento`/`podar_noticia` já removem as URLs cujo valor é o relativo removido (`remover_relativo`). Como várias URLs podem apontar para o mesmo canônico, remover o canônico libera todas — coerente com o comportamento desejado.

## Risks / Trade-offs

- [URL pode mapear para um caminho canônico de outro mês/categoria] → aceitável: documentos da CVM são imutáveis por premissa; a identidade passa a ser a URL, não o caminho derivado.
- [Migração: um rebaixamento por URL legada na primeira atualização após a correção] → mitigação: é uma única vez; depois o canônico é reusado. Alternativa não adotada: procurar o PDF pelo id em todo o subdiretório do ticker, evitando até esse download — mais caro e fora do escopo.
- [Registro de URL cresce com muitas URLs por ticker] → arquivo JSON pequeno, por escopo; já existente.
- [URL mutável servida no mesmo endereço] → a URL registrada pula a requisição; se o conteúdo mudar, o novo não é baixado. Mitigação: imutabilidade da CVM/FNET; para notícias, a URL é a identidade do artigo; a poda libera a URL quando o arquivo some.
- [I/O adicional por item] → leitura/gravação de um JSON pequeno por item, já existente para o caminho feliz; o caminho de duplicata passa a gravar uma vez.

## Migration Plan

Sem migração obrigatória. Na primeira atualização após a correção, cada URL legada cujo caminho derivado mudou é baixada uma vez, identificada como duplicata e então registrada apontando ao canônico; das próximas vezes é reusada. Rollback: voltar a registrar a URL apenas no caminho de gravação.

## Open Questions

Nenhuma pendente.
