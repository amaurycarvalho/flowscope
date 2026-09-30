# llm-chat-tokens Specification

## Purpose

Acumula, por sessão, os tokens de entrada e de saída gastos na aba "Chat AI" e os exibe em um rótulo persistente da barra de status, dando visibilidade ao custo do chat sem poluir as demais abas.

## Requirements

### Requirement: Acúmulo de tokens da sessão de chat

O sistema DEVE acumular, por sessão da aba "Chat AI", os tokens de entrada e de saída reportados pelo provedor em cada completion disparada pelo envio do chat, somando todas as chamadas do loop de navegação. Os tokens de entrada DEVEM ser acumulados como o valor **novo**, descontando os tokens servidos por cache de prompt (`entrada - entrada_cache`); os tokens de saída NÃO DEVEM ser ajustados. O total acumulado DEVE ser zerado ao limpar o chat e na inicialização da sessão.

#### Scenario: Envio soma os tokens da completion

- **WHEN** uma pergunta é enviada e o provedor reporta tokens de entrada e de saída
- **THEN** o acumulado da sessão DEVE ser somado com os tokens reportados

#### Scenario: Cache-hit descontado da entrada

- **WHEN** o provedor reporta `prompt_tokens` e tokens de cache-hit na mesma completion
- **THEN** o acumulado de entrada DEVE ser somado com `prompt_tokens - cache_hit` e o acumulado de saída com os tokens de saída, sem ajuste

#### Scenario: Uso sem informação de cache

- **WHEN** o provedor não reporta tokens de cache-hit
- **THEN** o acumulado de entrada NÃO DEVE ser descontado por cache nessa completion, salvo a estimativa determinística prevista na `llm-chat-llm`

#### Scenario: Cascata soma as duas chamadas

- **WHEN** o envio executa múltiplos ciclos de navegação
- **THEN** os tokens de todos os ciclos DEVEM compor o mesmo total acumulado

#### Scenario: Limpar zera o total

- **WHEN** o usuário confirma "Limpar" no chat
- **THEN** o total acumulado de tokens DEVE voltar a zero

#### Scenario: Inicialização zera o total

- **WHEN** o painel de chat é construído
- **THEN** o total acumulado DEVE iniciar em zero

#### Scenario: Falha não inventa tokens

- **WHEN** o envio termina em erro antes de o provedor reportar uso
- **THEN** o acumulado NÃO DEVE ser alterado

### Requirement: Rótulo persistente de tokens na barra de status

O sistema DEVE exibir o acumulado em um rótulo próprio na barra de status no formato `Tokens: <entrada> entrada / <saída> saída / <contexto> contexto (<N>%) · nav: <W>/32K`, com os valores numéricos formatados em milhares com sufixo `K` e uma casa decimal e separados por ` / `. O segmento final DEVE ser o `prompt_tokens` bruto da completion mais recente — a base do cálculo do percentual — rotulado `contexto`, seguido do percentual de ocupação da janela de contexto entre parênteses, sem casa decimal, e do segmento `nav: <W>/32K` com a cota de navegação acumulada e o seu teto. Quando a janela não for conhecida, o percentual DEVE ser omitido, mas o valor bruto rotulado `contexto` DEVE permanecer. O rótulo DEVE ficar visível somente quando a aba "Chat AI" estiver ativa e DEVE persistir após o término do envio. O rótulo DEVE ser atualizado durante o processamento, à medida que cada ciclo é concluído, e NÃO DEVE ser sobrescrito pelas mensagens de status de outras operações.

#### Scenario: Visível somente na aba Chat AI

- **WHEN** a aba "Chat AI" está ativa
- **THEN** o rótulo de tokens DEVE estar visível
- **WHEN** outra aba de topo é selecionada
- **THEN** o rótulo DEVE ficar oculto

#### Scenario: Formato em milhares com uma casa

- **WHEN** o acumulado é de 5540 tokens de entrada e 340 de saída, a completion mais recente tem `prompt_tokens` bruto de 6400 e a navegação acumulada é de 12000 tokens
- **THEN** o rótulo DEVE exibir `Tokens: 5.5K entrada / 0.3K saída / 6.4K contexto · nav: 12.0K/32K`

#### Scenario: Percentual da janela no rótulo

- **WHEN** a completion atual reporta `prompt_tokens` e a janela de contexto do modelo é conhecida
- **THEN** o rótulo DEVE exibir, após o valor bruto rotulado `contexto`, o percentual como um inteiro entre parênteses, sem casa decimal

#### Scenario: Atualização durante o processamento

- **WHEN** um ciclo do loop é concluído e o próximo ainda está em andamento
- **THEN** o rótulo DEVE exibir o acumulado parcial

#### Scenario: Persistência após o término

- **WHEN** o envio termina com sucesso e o status volta para "Pronto."
- **THEN** o rótulo DEVE continuar exibindo o total acumulado da sessão

### Requirement: Percentual de ocupação da janela de contexto

O sistema DEVE calcular o percentual de ocupação da janela de contexto a partir do `prompt_tokens` bruto da completion mais recente (cache incluído) dividido pela janela de contexto do modelo, arredondado para inteiro. A janela de contexto DEVE ser resolvida a partir do preset do provedor/modelo, enriquecida pela informação do liteLLM quando disponível. O valor bruto usado no cálculo DEVE integrar o rótulo rotulado `contexto`, formatado como os demais. Quando a janela não for conhecida, o percentual NÃO DEVE ser exibido, mantendo o valor bruto rotulado `contexto` no rótulo.

#### Scenario: Percentual a partir do prompt bruto

- **WHEN** a completion atual reporta `prompt_tokens` de 12.000 com janela de 128.000
- **THEN** o percentual exibido DEVE ser 9%, independentemente dos tokens de cache-hit

#### Scenario: Janela desconhecida omite o percentual

- **WHEN** a janela de contexto do modelo não é conhecida
- **THEN** o rótulo DEVE exibir o valor bruto da completion mais recente rotulado `contexto`, sem o parêntese de percentual, e NÃO DEVE exibir apenas entrada e saída

#### Scenario: Cache não altera a ocupação

- **WHEN** parte do prompt foi servida por cache
- **THEN** o percentual DEVE considerar o prompt completo, não o valor de entrada ajustado

### Requirement: Cotas separadas de diálogo e navegação

O sistema DEVE manter contadores separados para a cota de **diálogo** e a cota de **navegação**. A cota de diálogo DEVE selecionar mensagens com `enviar_ao_modelo` verdadeiro e conteúdo não vazio, de trás para frente, até 10 mensagens e 8.000 caracteres, registrando erros e avisos com `enviar_ao_modelo` falso. A cota de navegação DEVE contabilizar os tokens dos pares `(assistant, resultado)` reusados entre perguntas, com teto de 32.000 tokens.

#### Scenario: Diálogo limitado por mensagens e caracteres

- **WHEN** a sessão tem mais de 10 mensagens elegíveis ou mais de 8.000 caracteres
- **THEN** a cota de diálogo DEVE descartar os turnos mais antigos, preservando os mais recentes

#### Scenario: Erros fora da cota de diálogo

- **WHEN** uma mensagem de erro ou aviso está registrada na sessão
- **THEN** ela NÃO DEVE compor a cota de diálogo

#### Scenario: Navegação limitada por tokens

- **WHEN** os pares de navegação acumulados excedem 32.000 tokens
- **THEN** a cota de navegação DEVE descartar os pares mais antigos em conjunto
