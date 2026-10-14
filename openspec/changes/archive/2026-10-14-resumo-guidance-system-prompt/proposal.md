## Why

Hoje as instruções de resumo (Documentos/Notícias) e de avaliação de guidance vão coladas ao texto variável em uma única mensagem `user`, sem `system_prompt`. O prefixo enviado ao provedor muda a cada item, o que impede cache de prompt, e as instruções ficam embutidas em uma string de caso de uso, dificultando leitura e manutenção. Separar as instruções estáveis em uma mensagem `system` torna o prefixo idêntico entre itens, melhora a legibilidade/manutenabilidade e habilita cache de prompt quando o provedor suportar.

## What Changes

- **Resumo de documentos e notícias**: `ResumirDocumentoUseCase` passa a enviar as instruções em um `system_prompt` constante e o texto do documento como única mensagem `user`. Cobre as sub-abas "Documentos" e "Notícias", que reutilizam o mesmo caso de uso.
- **Avaliação de guidance**: `AvaliarGuidanceUseCase` aplica o mesmo padrão — instruções em `system_prompt` constante e o trecho como mensagem `user`.
- **Ajustes pontuais de prompt**: incorporar à versão enxuta regras relevantes da versão mais detalhada (não usar markdown/listas; não escrever nada antes de `CURTO:`/`LONGO:`; basear-se exclusivamente no conteúdo fornecido; guidance vazio ⇒ saída vazia; valor único ⇒ mínimo igual ao máximo; ponto decimal sem `R$`; na dúvida em guidance, usar `NAO`).
- **Orçamento de caracteres compatível com o XYZ**: elevar os tetos de salvaguarda do resumo (curto 280 → 450, longo 1500 → 2000) e declarar no prompt um orçamento logo abaixo deles (400 / 1800), instruindo a planejar X, Y e Z dentro do orçamento sem cortar a conclusão. Motivo: com a fórmula XYZ aplicada também ao resumo longo, a resposta passou a exceder os tetos antigos e o truncamento em fronteira descartava justamente a conclusão (`Conclui-se…`).
- **Documentação**: atualizar `docs/misc/llm-payloads.md` (§1.1 e §1.5) com o payload separado em `system`/`user`.
- Sem mudança no comportamento de persistência, truncamento, limites ou parser de resposta; o provedor de cache é efeito oportunista, não requisito.

## Capabilities

### New Capabilities
<!-- Nenhuma nova capability. -->

### Modified Capabilities
- `documento-summary`: as instruções de resumo passam a residir em um prefixo de sistema estável (`system_prompt`) e a mensagem `user` passa a conter apenas o texto do documento; o prompt DEVE manter a fórmula XYZ, as frases/parágrafos e agora declara um orçamento de caracteres (400 / 1.800) compatível com o XYZ, com os tetos de salvaguarda elevados para 450 / 2000, acrescendo regras de formato e de fidelidade ao documento.
- `relatorio-gerencial-guidance`: as instruções de avaliação passam a residir em um prefixo de sistema estável (`system_prompt`) e a mensagem `user` passa a conter apenas o trecho; o prompt DEVE manter o formato de quatro linhas e acrescer regras de saída vazia, valor único e separador decimal.

## Impact

- Código: `application/resumo_documento.py` (constante de sistema + `system_prompt`), `application/avaliar_guidance.py` (idem).
- Testes: `tests/test_application/test_resumo_documento.py` (ajustar helpers/asserções para o par system/user) e os testes de guidance correspondentes.
- Docs: `docs/misc/llm-payloads.md`.
- Sem novas dependências; a porta `LLMPort` e o adaptador já suportam `system_prompt`.
