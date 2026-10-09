## 1. Resumos sem corte no meio da palavra

- [x] 1.1 Adicionar em `application/resumo_documento.py` um helper de truncamento em fronteira (frase → palavra → duro) e aplicá-lo a `curto`/`longo`, mantendo os tetos de 280/1500. Verificar com testes de resumo excedente
- [x] 1.2 Ajustar o prompt para pedir o resumo curto em 1–2 frases e o longo em parágrafos (mantendo XYZ e uma chamada por documento). Verificar com teste do prompt
- [x] 1.3 Verificar com teste que `short_summary`/`long_summary` nunca terminam no meio de uma palavra quando há fronteira no trecho

## 2. Regeneração de resumos truncados

- [x] 2.1 Detectar resumo persistido desatualizado (não termina em pontuação final após normalizar) e incluí-lo nos pendentes do lote "Resumir pendentes". Verificar com teste do lote
- [x] 2.2 Garantir que resumos íntegros não sejam refeitos. Verificar com teste

## 3. Leitura paginada do texto

- [x] 3.1 Aceitar `offset`/`limite` opcionais em `obter` (`application/chat/protocolo.py`), validando tipo/valor com erro estruturado `tipo_invalido` e dica. Verificar com teste de protocolo
- [x] 3.2 No ramo `/documentos`, `texto` guarda o texto completo e devolve a página `[offset, offset+limite)`, sinalizando `total`, `offset`, `limite` e `continua`; `offset` além do fim devolve vazio sem erro. Verificar com teste de árvore
- [x] 3.3 Substituir o truncamento fixo `TETO_DOCUMENTO` pelo limite de página padrão. Verificar com teste de documento longo

## 4. Orientação de paginação

- [x] 4.1 Adicionar ao manifesto/playbook (`application/chat/manifesto.py`) e ao `SYSTEM_PROMPT` (`application/chat/consultar.py`) a regra de ler textos longos em páginas sucessivas via `obter` com `offset`/`limite` até `continua` ser falso. Verificar com teste do manifesto/prompt

## 5. Verificação integrada

- [x] 5.1 Executar `make lint` e `make complexity` sem erros
- [x] 5.2 Executar `make test` (cobertura ≥ 85%) sem erros
- [x] 5.3 Confirmar manualmente no Chat AI que um RG longo é lido em páginas completas (sem corte no meio de palavra) e que os resumos curto/longo apresentam frases inteiras
