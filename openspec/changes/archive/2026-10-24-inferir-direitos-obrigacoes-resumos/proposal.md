## Why

Os Relatórios Gerenciais e Relatórios Mensais de FII já resumidos pelo "Resumir pendentes" costumam citar direitos e obrigações de renda fixa que não aparecem nas fontes estruturadas da CVM, deixando ramos `sem-fonte` ou incompletos. Hoje essa informação fica apenas no texto do resumo, sem virar nós navegáveis da árvore.

## What Changes

- Adicionar inferência opcional de "Direitos e obrigações" ao lote "Resumir pendentes", executada após o resumo dos documentos e antes da finalização.
- Usar como entrada os resumos longos já persistidos de Relatórios Gerenciais e Relatórios Mensais, sem reabrir PDFs nem reextrair texto.
- Persistir as inferências em cache separado por ticker, com proveniência do documento, trecho de evidência, confiança e versão do prompt; nunca sobrescrever os dados oficiais da CVM.
- Exibir os itens inferidos como nós distintos ("inferido pela IA") em Obrigações e Direitos, mantendo o dado oficial como autoritativo em caso de conflito.
- Habilitar a inferência apenas quando a flag `renda_fixa.inferir_no_resumo` estiver ligada, houver LLM configurada e a cobertura oficial do ticker estiver vazia ou parcial.
- Estender `flowscope resumir documentos` para executar a mesma fase de inferência e reportar o desfecho no JSON.
- Manter fora de escopo: inferência para ações, uso de texto integral de PDF na inferência, substituição de fontes oficiais e extração de eventos.

## Capabilities

### New Capabilities
- `inferencia-direitos-obrigacoes`: extração estruturada, cache e resolução de direitos e obrigações a partir de resumos de documentos, com proveniência e precedência do dado oficial.

### Modified Capabilities
- `direitos-obrigacoes`: o ramo passa a aceitar nós inferidos, rotulados e com precedência dos dados oficiais.
- `documentos-ticker-panel`: o botão "Resumir pendentes" ganha a fase opcional de inferência e considera a cobertura oficial ao avaliar pendências.
- `cli-acoes-atualizacao`: `resumir documentos` passa a executar e reportar a fase de inferência.

## Impact

- **Aplicação:** novo caso de uso de inferência, portas de LLM e repositório de inferências; integração ao lote existente sem alterar a extração de texto.
- **Domínio:** read-model de inferência com tipo, papel, evidência, documento de origem e confiança.
- **Infraestrutura:** cache `<cache>/direitos-obrigacoes/inferencias/<TICKER>.json`, validação de resposta estruturada e leitura de resumos persistidos.
- **GUI/CLI:** fase adicional no lote e no comando headless, com progresso, cancelamento e desfecho próprios.
- **Chat AI/MCP:** a árvore cache-only passa a anunciar os nós inferidos quando existirem, sem chamadas de rede.
- **Configuração:** flag `renda_fixa.inferir_no_resumo` (padrão `false`) e versão de prompt para invalidação de cache.
- **Testes:** resposta válida/inválida, conflito com dado oficial, cache por documento, flag desligada, lote GUI e CLI.
