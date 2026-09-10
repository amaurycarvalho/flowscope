## 1. Consistência de constantes e versionamento

- [x] 1.1 Adicionar em `funds_client.py` a constante de versão do parser/aquisição, as constantes de TTL por tipo de dado e os prefixos de chave, e verificar por inspeção que nenhum método mantém TTL literal duplicado
- [x] 1.2 Adicionar um helper que monta a chave versionada (prefixo + versão + partes) e verificar com teste unitário que a chave inclui a versão

## 2. Cache do HTML do documento FundosNet

- [x] 2.1 Envolver `buscar_html_documento` em `CacheManager.get_or_fetch` com payload `{"html": ...}` e chave versionada pelo `id` do documento, e verificar com teste que a segunda chamada não realiza requisição HTTP
- [x] 2.2 Verificar com teste que proventos (`type=41`) e informe mensal (`type=40`) que compartilham o mesmo `id` de documento baixam o HTML uma única vez
- [x] 2.3 Verificar com teste que, em falha de rede com HTML em cache, o conteúdo armazenado é servido e que, sem cache, a indisponibilidade é sinalizada
- [x] 2.4 Verificar com teste que subir a versão do parser invalida o HTML em cache e refaz a aquisição

## 3. Cache da identidade do fundo

- [x] 3.1 Envolver `listar_candidatos` (`GetListClassFund`) em `CacheManager.get_or_fetch` com chave versionada pelo `id` primário e verificar com teste que a segunda resolução não realiza requisição HTTP
- [x] 3.2 Verificar com teste que um resultado vazio não é armazenado (chave invalidada) e que uma nova chamada volta a consultar a fonte
- [x] 3.3 Verificar com teste que o vencimento do TTL reconsulta a fonte e substitui o cache

## 4. Verificação integrada

- [x] 4.1 Executar `pytest` e verificar que todos os testes passam
- [x] 4.2 Executar `ruff check src/` e o lint do projeto e verificar que não há violações
- [x] 4.3 Validar a change com `openspec validate "b3-cache-documentos-identidade"` e verificar que é válida
