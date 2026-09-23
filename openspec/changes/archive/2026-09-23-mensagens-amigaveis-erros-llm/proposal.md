## Why

Quando a LLM responde com sobrecarga temporária (HTTP 503 "high demand"), a barra de status do botão "Resumir pendentes" e o campo de status do botão "Testar" do diálogo "I.A." exibem a string crua do liteLLM, com `Error code: 503`, nomes de módulos e o JSON do provedor. A mensagem é longa, técnica e não orienta o usuário; além disso, o 503 cai no mesmo `LLMProviderError` genérico de autenticação/requisição inválida, então a interface não consegue distinguir "tente novamente" de "corrija a configuração".

## What Changes

- Humanizar as mensagens de erro de I.A. exibidas ao usuário no botão "Resumir pendentes" e no botão "Testar" do diálogo "I.A.", por categoria de falha (`LLMServiceUnavailableError`, `LLMRateLimitError`, `LLMCommunicationError`, `LLMConfigurationError`, `LLMProviderError` e `LLMUnavailableError`), mantendo `str(exc)` técnico e os registros de log inalterados.
- Introduzir o subtipo de domínio `LLMServiceUnavailableError` para sobrecarga/erro 5xx do provedor.
- Mapear `ServiceUnavailableError` e `InternalServerError` do liteLLM para o novo subtipo, antes da entrada genérica `APIError`.
- Extrair a tradução tipo-de-erro → texto para um helper de apresentação, sem que a GUI dependa do liteLLM.
- Preservar o texto bruto para exceções que não forem da camada de LLM (ex.: falha de conversão de PDF).
- Silenciar o banner de depuração do liteLLM (`Give Feedback / Get Help` e `LiteLLM.Info`) impresso no terminal quando uma falha do provedor é mapeada, mantendo `str(exc)` e os registros de log intactos.

## Capabilities

### New Capabilities
<!-- Nenhuma nova capability. -->

### Modified Capabilities
- `llm-provider`: acrescenta `LLMServiceUnavailableError` à hierarquia tipada, define o mapeamento de erros 5xx/sobrecarga para ele e determina que falhas do provedor não imprimam o banner de depuração do liteLLM no terminal.
- `llm-gui`: o botão "Testar" passa a exibir um motivo amigável por categoria de falha, mantendo o registro em log com o erro original.
- `documentos-ticker-panel`: a interrupção do lote por erro reporta o motivo da falha de forma amigável na barra de status.
- `documento-summary`: a propagação de exceções tipadas passa a incluir `LLMServiceUnavailableError`.

## Impact

- `src/flowscope/domain/llm/exceptions.py` e `src/flowscope/domain/llm/__init__.py`: novo subtipo e exportação.
- `src/flowscope/infrastructure/llm/adapter.py`: novas entradas no mapeamento de exceções, antes de `APIError`, e desabilitação do banner de depuração do liteLLM.
- `src/flowscope/presentation/gui/llm/mensagens.py` (novo): helper de tradução erro → texto.
- `src/flowscope/presentation/gui/app_resumos_actions.py`: uso do helper na interrupção do lote.
- `src/flowscope/presentation/gui/llm/config_dialog.py`: uso do helper no desfecho do teste.
- Testes de domínio, adaptador, diálogo e helper de mensagens.
- Sem mudanças de formato de dados, dependências ou compatibilidade; `str(exc)` e os registros de log permanecem como estão.
