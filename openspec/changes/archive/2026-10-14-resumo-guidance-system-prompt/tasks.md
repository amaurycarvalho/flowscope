## 1. Resumo de documentos e notícias

- [x] 1.1 Em `src/flowscope/application/resumo_documento.py`, mover as instruções para uma constante de módulo `SYSTEM_PROMPT` (texto enxuto adaptado: fórmula XYZ, tetos, 1 a 2 frases/parágrafos, sem markdown ou comentários, fidelidade ao documento) e alterar `resumir` para enviar `[{"role": "user", "content": entrada}]` com `system_prompt=SYSTEM_PROMPT`, removendo `_montar_prompt` e o trailer `Documento:`; verificar rodando `pytest tests/test_application/test_resumo_documento.py`.
- [x] 1.2 Ajustar `tests/test_application/test_resumo_documento.py` para inspecionar o `system_prompt` (fórmula XYZ, orçamentos, frases/parágrafos, regras de formato) e a mensagem `user` (apenas o documento truncado ao orçamento); verificar rodando `pytest tests/test_application/test_resumo_documento.py`.

## 2. Avaliação de guidance

- [x] 2.1 Em `src/flowscope/application/avaliar_guidance.py`, mover as instruções para uma constante de módulo `SYSTEM_PROMPT` (texto enxuto adaptado: quatro linhas, `NAO` ⇒ campos vazios, valor único ⇒ mínimo igual ao máximo, ponto decimal sem símbolo, na dúvida `NAO`) e alterar `_tentar_llm` para enviar `[{"role": "user", "content": texto}]` com `system_prompt=SYSTEM_PROMPT`, removendo `_montar_prompt` e o trailer `Trecho:`; verificar rodando `pytest tests/test_application/test_avaliar_guidance.py`.
- [x] 2.2 Ajustar o `_LLMFake` e as asserções de `tests/test_application/test_avaliar_guidance.py` para registrar e checar o `system_prompt` e a mensagem `user` separadamente; verificar rodando `pytest tests/test_application/test_avaliar_guidance.py`.

## 3. Documentação

- [x] 3.1 Atualizar `docs/misc/llm-payloads.md` §1.1 (resumo) e §1.5 (guidance) para o payload com mensagem `system` (instruções estáveis) mais `user` (texto/trecho), ajustando a afirmação atual de "sem `system_prompt`"; verificar por leitura do documento.

## 4. Verificação

- [x] 4.1 Rodar `make lint` e `make complexity`.
- [x] 4.2 Rodar os testes impactados (`pytest tests/test_application/test_resumo_documento.py tests/test_application/test_avaliar_guidance.py tests/test_infrastructure/test_llm/test_adapter.py`) e confirmar que passam.
- [x] 4.3 (manual, usuário) Executar a suíte completa (`make test`) ou o quality gate apenas se desejar cobertura ampla por precaução.

## 5. Orçamento de caracteres compatível com o XYZ

- [x] 5.1 Elevar os tetos em `src/flowscope/application/resumo_documento.py` (`LIMITE_CURTO` 280 → 450, `LIMITE_LONGO` 1500 → 2000) e adicionar os orçamentos de prompt `ORCAMENTO_CURTO = 400` e `ORCAMENTO_LONGO = 1800`; atualizar o `SYSTEM_PROMPT` para usar os orçamentos e instruir a planejar X, Y e Z sem cortar a conclusão; verificar rodando `pytest tests/test_application/test_resumo_documento.py`.
- [x] 5.2 Atualizar testes para orçamento/cap (`test_system_prompt_contem_formula_xyz_e_limites`, `test_orcamento_cabe_no_teto`, `test_system_prompt_orca_o_xyz`); verificar rodando `pytest tests/test_application/test_resumo_documento.py`.
- [x] 5.3 Atualizar `docs/misc/llm-payloads.md` (§1.1/§1.3), `docs/misc/panels.md` e `docs/misc/indicators.md` para os novos valores.
- [x] 5.4 Atualizar as specs `documento-summary` (delta e principal) e o `proposal.md`/`design.md` da change para os novos orçamentos e tetos.
