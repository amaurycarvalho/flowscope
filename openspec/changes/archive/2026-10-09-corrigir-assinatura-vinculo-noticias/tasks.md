## 1. Correção do contrato

- [x] 1.1 Tornar `senha` posicional-or-keyword em `baixar_conteudo_vinculado` (noticias_vinculo.py), mantendo `sessao`/`timeout` keyword-only, e verificar que a suíte de `test_noticias_vinculo` continua verde
- [x] 1.2 Isolar a chamada `self._baixar_vinculo(resultado.texto, senha)` em `_texto_do_arquivo` (noticias_panel.py) com `try/except Exception`, log de aviso e retorno do corpo original

## 2. Testes de regressão

- [x] 2.1 Adicionar teste em `test_noticias_vinculo` que chame `baixar_conteudo_vinculado(corpo, "senha")` posicionalmente e verifique que a senha chega a `extrair_pdf` sem `TypeError`
- [x] 2.2 Adicionar teste em `test_noticias_panel` que injete o resolvedor real `baixar_conteudo_vinculado` (rede mockada) e verifique que `_texto_do_arquivo` resolve o vínculo sem erro
- [x] 2.3 Adicionar teste em `test_noticias_panel` que injete um resolvedor que levanta exceção e verifique que `_texto_do_arquivo` devolve o corpo original

## 3. Verificação final

- [x] 3.1 Rodar `pytest tests/test_presentation/test_noticias_panel.py tests/test_infrastructure/test_regulacao/test_noticias_vinculo.py` e confirmar sucesso
- [x] 3.2 Rodar `ruff check` e `flake8` nos arquivos alterados e confirmar ausência de erros
- [x] 3.3 Validar a change com `openspec validate corrigir-assinatura-vinculo-noticias` (o aviso de RFC 2119 é esperado em specs em português)
