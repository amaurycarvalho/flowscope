# llm-chat-tokens Specification

## Purpose

Acumula, por sessão, os tokens de entrada e saída gastos na aba "Chat AI" e os exibe em um rótulo persistente da barra de status, dando visibilidade ao custo do chat sem poluir as demais abas.

## Requirements

### Requirement: Acúmulo de tokens da sessão de chat

O sistema DEVE acumular, por sessão da aba "Chat AI", os tokens de entrada e de saída reportados pelo provedor em cada completion disparada pelo envio do chat, somando todas as chamadas da cascata (resumos e texto integral). O total acumulado DEVE ser zerado ao limpar o chat e na inicialização da sessão.

#### Scenario: Envio soma os tokens da completion

- **WHEN** uma pergunta é enviada e o provedor reporta tokens de entrada e de saída
- **THEN** o acumulado da sessão DEVE ser somado com os tokens reportados

#### Scenario: Cascata soma as duas chamadas

- **WHEN** o envio escala para a segunda chamada com o texto integral dos alvos
- **THEN** os tokens das duas chamadas DEVEM compor o mesmo total acumulado

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

O sistema DEVE exibir o acumulado em um rótulo próprio na barra de status, com os valores de entrada e de saída formatados em milhares com sufixo `K` e uma casa decimal. O rótulo DEVE ficar visível somente quando a aba "Chat AI" estiver ativa e DEVE persistir após o término do envio. O rótulo DEVE ser atualizado durante o processamento, à medida que cada completion é concluída, e NÃO DEVE ser sobrescrito pelas mensagens de status de outras operações.

#### Scenario: Visível somente na aba Chat AI

- **WHEN** a aba "Chat AI" está ativa
- **THEN** o rótulo de tokens DEVE estar visível
- **WHEN** outra aba de topo é selecionada
- **THEN** o rótulo DEVE ficar oculto

#### Scenario: Formato em milhares com uma casa

- **WHEN** o acumulado é de 5540 tokens de entrada e 340 de saída
- **THEN** o rótulo DEVE exibir os valores como `5.5K` de entrada e `0.3K` de saída

#### Scenario: Atualização durante o processamento

- **WHEN** a primeira completion da cascata é concluída e a segunda ainda está em andamento
- **THEN** o rótulo DEVE exibir o acumulado parcial

#### Scenario: Persistência após o término

- **WHEN** o envio termina com sucesso e o status volta para "Pronto."
- **THEN** o rótulo DEVE continuar exibindo o total acumulado da sessão
