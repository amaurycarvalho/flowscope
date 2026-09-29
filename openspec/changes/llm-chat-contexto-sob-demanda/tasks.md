## 1. Config — flag `input_limitado`

- [ ] 1.1 Incluir `input_limitado` em `_CHAT_FIELDS`/`DEFAULT_LLM_CONFIG` (`infrastructure/llm/config.py`) com default `False` e coerção booleana em `_normalizar_provedor`, e verificar leitura/gravação preservando os demais campos
- [ ] 1.2 Garantir que `save_llm_config`/`load_provider_configs` preservam o flag por provedor, e verificar com `config.json` temporário
- [ ] 1.3 Estender o contrato de `LLMConfigPort` (se necessário) e o adaptador, e verificar `default_config` incluindo o flag
- [ ] 1.4 Testes de config: default `false` quando ausente, `true` persistido, migração do formato plano inalterada

## 2. GUI — checkbox no diálogo

- [ ] 2.1 Adicionar `Checkbutton` "janela de entrada limitada" e variável booleana no `LLMConfigDialog`, e verificar a construção headless
- [ ] 2.2 Carregar/salvar o estado no fluxo existente (`_carregar`, `_carregar_provedor`, `_coletar_campos_provedor`, `_coletar_config`), e verificar troca de provedor e novo provedor
- [ ] 2.3 Ajustar `test_llm_config_dialog.py` para cobrir o checkbox (salvar, restaurar, provedor sem config)

## 3. Aplicação — Bloco estável condicional e manifesto

- [ ] 3.1 Propagar o flag `input_limitado` até `MontarContextoChat` no wiring/criação do painel, e verificar a montagem com/sem o flag
- [ ] 3.2 Com o flag ativo, omitir conhecimento, fundamentos e resumos de `_renderizar_bloco` e incluir o manifesto com as chaves reservadas, e verificar o texto do prefixo
- [ ] 3.3 Incluir o manifesto e a omissão na assinatura do bloco estável, e verificar determinismo e reuso da assinatura
- [ ] 3.4 Preservar byte-a-byte o comportamento sem o flag, e verificar com teste de regressão

## 4. Aplicação — Recursos sob demanda e gate

- [ ] 4.1 Estender `ContextoChat`/`ContextoDocumental` com os recursos (chave → texto) e a resolução que prioriza recursos e depois documentos, e verificar chaves mistas
- [ ] 4.2 Implementar o gate de confirmação próprio dos recursos, carregando o motivo/tipo até a apresentação, e verificar a escolha do texto de diálogo
- [ ] 4.3 Na recusa, prosseguir sem os recursos, e verificar que nenhuma exceção é lançada
- [ ] 4.4 Ajustar a instrução de formato para citar as chaves reservadas quando o flag está ativo, e verificar o texto enviado

## 5. Aplicação — Orçamento de três chamadas

- [ ] 5.1 Elevar o orçamento da cascata para três chamadas com o flag ativo, mantendo duas sem o flag, e verificar os cenários "resposta nos resumos", "texto integral" e "recursos sob demanda"
- [ ] 5.2 Compartilhar prefixo estável e histórico entre as três chamadas, e verificar a igualdade do prefixo
- [ ] 5.3 Encerrar a cascata quando uma chamada intermediária for conclusiva, e verificar que não há chamadas extras

## 6. Testes de Integração

- [ ] 6.1 Teste do fluxo com flag ativo: manifest → recursos → documentos, e verificar a ordem e o conteúdo das mensagens
- [ ] 6.2 Teste do fluxo com flag desligado: comportamento atual preservado, e verificar no máximo duas chamadas
- [ ] 6.3 Teste de recusa do gate de recursos, e verificar que a resposta segue sem os recursos

## 7. Quality Gate

- [ ] 7.1 `make lint` e `make complexity` limpos
- [ ] 7.2 `pytest -m "llm"` passa
- [ ] 7.3 Testes existentes sem regressão (config, gui, chat, contexto)
- [ ] 7.4 Executar `openspec validate llm-chat-contexto-sob-demanda` e garantir que a change permanece válida
