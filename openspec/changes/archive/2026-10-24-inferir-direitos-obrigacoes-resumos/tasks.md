## 1. Domínio e cache de inferências

- [x] 1.1 Criar o read-model `InferenciaTitulo` com tipo, papel, descrição, documento de origem, chave/hash do resumo, trecho, confiança, data de referência e fonte; verificar com testes de construção e rótulos
- [x] 1.2 Implementar `RepositorioInferenciasJson` em `<cache>/direitos-obrigacoes/inferencias/<TICKER>.json` com escrita atômica, `parser_version` e idempotência por `(chave_documento, hash_resumo, parser_version)`; verificar primeira gravação, reutilização e substituição
- [x] 1.3 Implementar a combinação oficial + inferido com precedência do oficial e ausência apenas quando não houver nenhum dos dois; verificar conflito, item apenas inferido e ausência explícita

## 2. Caso de uso de inferência

- [x] 2.1 Implementar `InferirDireitosObrigacoesUseCase` recebendo catálogo/resumos, repositório oficial, porta `LLMPort`, repositório de inferências e versão do prompt; verificar com LLM fake e resumos em cache
- [x] 2.2 Selecionar apenas Relatório Gerencial e informe mensal do FII com `long_summary` persistido, sem reabrir PDF; verificar que documentos sem resumo ou de outras categorias são ignorados
- [x] 2.3 Montar o prompt estável e validar a resposta JSON (tipo conhecido, papel, evidência e documento obrigatórios); verificar resposta válida, tipo desconhecido e item sem evidência
- [x] 2.4 Implementar elegibilidade por flag `renda_fixa.inferir_no_resumo`, LLM disponível e cobertura oficial vazia/parcial; verificar flag desligada, cobertura completa e cobertura parcial
- [x] 2.5 Implementar falha tolerante e cancelamento cooperativo preservando resumos e itens já gravados; verificar exceção da LLM, cancelamento e cache parcial

## 3. Integração ao lote "Resumir pendentes"

- [x] 3.1 Estender `ResultadoResumos` e a orquestração do lote com o desfecho próprio da inferência (executada, itens, falhas, cancelada), sem alterar as contagens de resumo; verificar com testes de orquestração
- [x] 3.2 Executar a fase após a gravação dos resumos e antes da finalização, publicando progresso "inferência de direitos e obrigações"; verificar ordem das fases e preservação dos resumos em falha
- [x] 3.3 Atualizar o estado do botão "Resumir pendentes" para habilitar quando existir inferência elegível, consultando a pendência fora da thread do Tk; verificar inferência pendente, flag desligada e cobertura completa
- [x] 3.4 Remontar a árvore após a inferência preservando a seleção existente; verificar que os nós inferidos aparecem e que a pré-visualização mostra a proveniência

## 4. Apresentação e Chat AI

- [x] 4.1 Exibir itens inferidos em Obrigações/Direitos com rótulo "inferido pela IA" e proveniência (documento, data, trecho/confiança); verificar com testes do painel de documentos
- [x] 4.2 Estender a montagem da árvore do Chat AI e o manifesto para anunciar os itens inferidos nos caminhos canônicos, mantendo a navegação cache-only; verificar manifesto e `listar`/navegação sem rede

## 5. CLI e configuração

- [x] 5.1 Estender `flowscope resumir documentos` para executar a inferência após os resumos e reportar o desfecho próprio no JSON, sem quebrar as chaves existentes; verificar ticker único e watchlist
- [x] 5.2 Garantir que falha da inferência por ticker não aborta os demais e encerra com código 1; verificar lote com falha parcial
- [x] 5.3 Documentar a flag `renda_fixa.inferir_no_resumo`, o cache de inferências, a precedência oficial e a proveniência em `docs/misc/datasources.md`; verificar por revisão textual

## 6. Verificação da change

- [x] 6.1 Executar `make lint` e corrigir os problemas encontrados; verificar saída sem erros
- [x] 6.2 Executar `make complexity` e corrigir os problemas encontrados; verificar saída sem erros
- [x] 6.3 Executar os testes relacionados/impactados (domínio, aplicação, infraestrutura, GUI, Chat AI, manifesto e CLI) e corrigir falhas; verificar a suíte relacionada verde
