## 1. Domínio

- [x] 1.1 Criar `domain/noticias/` com a classificação (`TERMOS_EXCEPCIONAIS`, `TIPOS_NOTICIA`, `TIPO_OUTROS`, `normalizar_texto`, `noticia_excepcional`, `classificar_tipo`) e as entidades `NoticiaArquivo`, `SecaoNoticias`, `CatalogoNoticias`, `TITULO_NOTICIAS`; verificar com testes de classificação, igualdade e propriedade `vazio`
- [x] 1.2 Atualizar os importadores para a classificação e as entidades de domínio; verificar `make test` verde sem mudança de comportamento

## 2. Aplicação

- [x] 2.1 Criar a porta de catálogo de notícias e o caso de uso de consulta em `application`, reaproveitando `montar_catalogo` de `application/documentos` e montando as seções; verificar com testes puros de montagem e seções
- [x] 2.2 Criar a ordenação do lote (`pendentes_ordenados` e chave determinista) em `application/noticias`, operando sobre a data ordinal preparada; verificar com testes puros de ordem por grupo e desempate estável
- [x] 2.3 Mover a montagem do índice compacto do chat e a intercalação por seção para `application/noticias`, mantendo os tetos de caracteres; verificar com testes puros de índice, cobertura de seções e truncamento

## 3. Infraestrutura

- [x] 3.1 Fazer `infrastructure/b3/noticias_catalogo.py` implementar a porta de catálogo (leitura de índice/shards) usando as entidades de domínio e o read-model; preparar a data de publicação ordenável; verificar `test_noticias_catalogo.py`
- [x] 3.2 Garantir que `noticias_index`/`noticias_shards`/`noticias_carga`/`noticias_vinculo` permaneçam adaptadores de I/O e cumpram as portas de store/texto; verificar `test_noticias_shards.py` e `test_noticias_vinculo.py`

## 4. Apresentação e composition root

- [x] 4.1 Injetar caso de uso e portas no `NoticiasPanel` removendo imports de `infrastructure` e preservando a ordenação do lote vinda da aplicação; verificar que os módulos de notícias não constam mais na allowlist
- [x] 4.2 Atualizar `app_wiring.py`/`app_tab_layout.py` e a fonte de notícias do chat para fornecer os adaptadores; verificar o painel com fakes e `make test` verde
- [x] 4.3 Atualizar `NoticiasTreeView` e `presentation/gui/chat/noticias.py` para consumir entidades/read-model de `domain`/`application`, sem importar `infrastructure`

## 5. Testes e allowlist

- [x] 5.1 Migrar os testes puros de notícias (classificação, ordenação do lote, índice do chat, extração) para `tests/test_domain`/`tests/test_application` e deixar no painel apenas wiring, estado e thread; verificar contagem e ausência de `DISPLAY` nos testes puros
- [x] 5.2 Remover as 3 entradas de notícias da allowlist; verificar `tests/architecture` verde sem entradas obsoletas
- [x] 5.3 Rodar `make test` e `make quality-gate` e confirmar tudo verde com paridade de comportamento
