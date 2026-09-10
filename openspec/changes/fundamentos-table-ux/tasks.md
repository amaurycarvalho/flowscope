## 1. Persistência de larguras

- [x] 1.1 Adicionar `fundamental_column_widths` ao `DEFAULT_CONFIG` e verificar com teste de `load_preferences`/`save_preferences`
- [x] 1.2 Aplicar larguras iniciais no `FundamentalTablePanel` e capturar mudanças de coluna, verificando com teste do painel (com display)
- [x] 1.3 Salvar as larguras em `_on_close` e restaurar na construção, verificando o round-trip de preferências

## 2. Resultado de cache e status

- [x] 2.1 Propagar o `CacheOutcome` do adapter até o caso de uso, agregando cache/rede por ticker, e verificar com testes do provider composto
- [x] 2.2 Emitir o sufixo `" - cached"` no progresso por ticker e verificar com teste do job/presenter
- [x] 2.3 Exibir a mensagem final de desfecho (sucesso/mitigação/falha catastrófica) e verificar os três cenários

## 3. Cursor de espera

- [x] 3.1 Reter o cursor "watch" até o término do job fundamental e verificar que ele só é liberado em `on_fundamental_result`/erro
- [x] 3.2 Verificar que o cursor permanece ativo quando todos os dados vêm do cache

## 4. Verificação integrada

- [x] 4.1 Rodar a suíte de apresentação (`pytest tests/test_presentation`) e verificar que passa
- [x] 4.2 Rodar `openspec validate fundamentos-table-ux --strict` e verificar que não há erros
