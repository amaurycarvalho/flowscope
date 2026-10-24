## Why

A sub-aba "Documentos" e a árvore de conhecimento do Chat AI expõem hoje apenas um placeholder de "Direitos e obrigações". O FlowScope já ingere dados da B3 e da CVM, mas não mostra os títulos de renda fixa associados a um ticker — debêntures, CRI, CRA, LCI, LCA, CDB, letras financeiras e afins — nem as informações de emissão, garantias, LTV, situação e eventos. Sem isso, o usuário não consegue responder, no próprio app, "quais títulos este ticker emitiu ou mantém?" nem avaliar risco de crédito e lastro.

## What Changes

- Ingerir títulos de renda fixa **emitidos** por companhias a partir do `FRE` da CVM (`outro_valor_mobiliario`), tratando CRI/CRA pelo **devedor econômico** do lastro.
- Complementar CRI/CRA com o `INF_MENSAL_CRI`/`INF_MENSAL_CRA` da CVM (SECURIT): emissor legal, devedor/cedente, garantias, subordinação, rating, situação, atrasos, contingências, impacto, desempenho e **LTV**.
- Ingerir a carteira de FIIs a partir do `INF_TRIMESTRAL/ativo` para os **direitos** por título (CRI/CRA, LCI/LCA) e do `INF_MENSAL/ativo_passivo` para os **agregados** de debêntures e CDB.
- Criar modelo de domínio e árvore de "Direitos e obrigações" com "Obrigações" e "Direitos", sub-ramo "Títulos", tipo do título e títulos individuais; usar nós **agregados** rotulados quando só houver total por ticker e nós `sem-fonte` explícitos quando não houver fonte pública.
- Expor, para cada título, "Informações gerais", "Informações adicionais", "LTV" (quando aplicável) e "Documentos relacionados", com resumo estruturado e **links** — sem extração por IA nesta change.
- Adicionar `AquisicaoTitulos` como serviço explícito, idempotente e cache-aware, acionado pelo mesmo botão "Atualizar" da sub-aba Documentos, internamente separado da aquisição de documentos.
- Estender a árvore do Chat AI com os caminhos canônicos de Obrigações e Direitos, incluindo agregados e `sem-fonte`, mantendo a navegação **cache-only**.
- Manter fora de escopo: `InstrumentRegistration` do BDI da B3 (fase 2), extração/sumarização de eventos por LLM e granularidade por título para CDB/LCI/LCA no lado Obrigações.

## Capabilities

### New Capabilities
- `cvm-renda-fixa`: aquisição, normalização e cache por ticker dos títulos de renda fixa a partir dos datasets da CVM (FRE, SECURIT CRI/CRA, carteira de FII), com proveniência, idempotência e reuso de ZIPs anuais.

### Modified Capabilities
- `direitos-obrigacoes`: substitui o placeholder pelo ramo real de Obrigações e Direitos, com tipos de título, títulos individuais, agregados, `sem-fonte`, LTV, informações adicionais e documentos relacionados.
- `documentos-ticker-panel`: estende a árvore e a pré-visualização da sub-aba "Documentos" para os nós de títulos.
- `documentos-aquisicao-painel`: o botão "Atualizar" passa a orquestrar a aquisição de documentos e de títulos, com progresso, bloqueio, tolerância a falhas e desfecho combinados.
- `llm-chat-tree`: o manifesto e o playbook passam a anunciar os caminhos canônicos aninhados de `/direitos-obrigacoes` (Obrigações/Direitos → Títulos → tipo → título/agregado/sem-fonte) e a navegação permanece cache-only.

## Impact

- **Infraestrutura CVM:** novos adaptadores para FRE `outro_valor_mobiliario`, SECURIT `INF_MENSAL_CRI`/`INF_MENSAL_CRA` e FII `INF_TRIMESTRAL/ativo`; reuso de `CvmDatasetDownloader` e do cache condicional.
- **Aplicação:** novo caso de uso/serviço `AquisicaoTitulos`, portas de repositório, modelo de títulos e renderização da árvore.
- **Domínio:** entidades e enums de tipo de título, papel (obrigação/direito), informações gerais/adicionais, LTV e documentos relacionados.
- **GUI:** `DocumentTreeView`, `DocumentTreePanel` e o fluxo do botão "Atualizar"; novos tipos de agrupamento e mapeamento de nós para títulos.
- **Chat AI/MCP/CLI:** `FonteDireitosObrigacoes` passa a ler o cache normalizado; manifesto e playbook ganham os novos caminhos; composição headless reutiliza a mesma fonte.
- **Cache:** novo JSON por ticker em `<cache>/direitos-obrigacoes/<TICKER>.json`, com assinatura, `fonte`, `data_referencia` e `adquirido_em`.
- **Testes:** parsing dos novos datasets, normalização, joins por CETIP/ISIN, idempotência/cache, árvore da GUI, árvore do chat, manifesto e integração com o botão "Atualizar".
