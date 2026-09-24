## 1. Pré-requisitos e Spike

- [ ] 1.1 Verificar que a `llm-chat` expõe o ponto de extensão de contexto da aba "Chat AI" e registrar o resultado
- [ ] 1.2 Spike: confirmar que a URL da notícia retorna HTML server-rendered com o corpo extraível, e registrar a conclusão
- [ ] 1.3 Criar a estrutura de diretórios da aquisição e do painel de notícias

## 2. Aquisição e Cache

- [ ] 2.1 Listagem das notícias do período via `RegulacaoRepository`, e verificar com mock
- [ ] 2.2 Chave surrogate estável (`sha1` de URL ou de data|agência|título), e verificar os dois casos
- [ ] 2.3 Download do corpo do artigo com `baixar` injetável e cache `noticias/<AAAA>/<MM>/<hash>.html`, e verificar gravação
- [ ] 2.4 Tolerância por item (sem URL, sem conteúdo, erro de rede) e deduplicação no cache, e verificar reexecução
- [ ] 2.5 Progresso e cancelamento (padrão de `AquisicaoDocumentos`), e verificar callback e token

## 3. Extração e Resumos

- [ ] 3.1 Extração do texto do HTML do artigo para os stores existentes, e verificar com fixture
- [ ] 3.2 Reuso do serviço de resumo para resumo curto/longo por notícia, e verificar persistência
- [ ] 3.3 Falha da LLM no lote não interrompe os demais, e verificar item que falha
- [ ] 3.4 Estado sem LLM configurada orienta a configuração, e verificar mensagem

## 4. Painel — Sub-aba "Notícias"

- [ ] 4.1 `NoticiasPanel` em `tkinter` (árvore + preview via `ReadonlyText`), e verificar construção
- [ ] 4.2 Botões "Atualizar", "Abrir", "I.A." e "Resumir pendentes" com barra de progresso, e verificar ações
- [ ] 4.3 Abertura do artigo no navegador e estado vazio/sem texto, e verificar cenários
- [ ] 4.4 Registro da sub-aba "Notícias" no notebook da Análise Geral, e verificar presença

## 5. Integração com o Chat

- [ ] 5.1 Registro das notícias como fonte adicional no contexto da aba "Chat AI", e verificar presença
- [ ] 5.2 Relevância por ticker inferida pela LLM a partir da pergunta, e verificar cenário
- [ ] 5.3 Cache frio de notícias não quebra a montagem do contexto, e verificar cenário

## 6. Testes

- [ ] 6.1 Aquisição/cache com `responses` e caches temporários
- [ ] 6.2 Painel: estados, preview, abertura e resumos com LLM mockada
- [ ] 6.3 Integração com o contexto de chat (fonte adicional, cache frio e ticker inferido)

## 7. Quality Gate

- [ ] 7.1 `make lint` e `make complexity` limpos
- [ ] 7.2 `pytest -m "not llm"` passa
- [ ] 7.3 Testes existentes sem regressão
- [ ] 7.4 Executar `openspec validate noticias-b3` e garantir que a change permanece válida

## 8. Documentação

- [ ] 8.1 Atualize README.md, indicators.md e panels.md com o que foi implementado nessa change.
