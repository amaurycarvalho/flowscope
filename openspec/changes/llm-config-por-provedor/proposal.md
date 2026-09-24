## Why

Hoje `llm.chat` guarda um único slot plano, então trocar de provedor sobrescreve a configuração anterior (inclusive a chave de API) e não há como voltar a um provedor já configurado restaurando o que foi feito para ele. Trocar para `none` e depois voltar também não restaura nada.

## What Changes

- Persistir a configuração de completion **por provedor** no bloco `llm.chat`: `provider` permanece como a seleção ativa e um novo mapa `providers` guarda `api_url`, `model`, `api_key` e `rpm` de cada provedor já configurado.
- Ao trocar o provedor no diálogo, restaurar automaticamente a configuração salva daquele provedor; quando não houver, aplicar os defaults do preset e limpar a chave (elimina o vazamento da chave entre provedores).
- Selecionar `none` limpa os campos sem apagar as configurações dos demais provedores, permitindo voltar a qualquer um e retomar o que foi salvo.
- Gravar no disco apenas ao clicar em "Salvar"; edições ainda não salvas ficam guardadas em memória durante a sessão do diálogo.
- Manter `load_llm_config()` devolvendo o dicionário plano resolvido do provedor ativo, preservando os consumidores atuais (`factory`, resumo de documentos, guidance, chat).
- Migrar automaticamente o formato antigo (plano, sem `providers`) na primeira gravação, sem perder a configuração existente.

## Capabilities

### New Capabilities

- *(nenhuma — todas as alterações são modificações em capacidades existentes)*

### Modified Capabilities

- `llm-config`: o bloco `llm.chat` passa a ter `provider` + mapa `providers`; nova requirement de memória por provedor e migração do formato plano anterior.
- `llm-gui`: ao trocar o preset no diálogo, a configuração salva do provedor selecionado é restaurada em vez de sobrescrever a do provedor anterior.

## Impact

- Código: `src/flowscope/infrastructure/llm/config.py` (leitura/gravação e migração) e `src/flowscope/presentation/gui/llm/config_dialog.py` (troca de preset e stash em memória).
- Consumidores preservados: `factory.py`, `document_summary.py`, `document_guidance.py`, `app_tab_layout.py` continuam usando `load_llm_config()` plano.
- Dados: `~/.flowscope/config.json` ganha o sub-mapa `llm.chat.providers`; arquivos antigos continuam legíveis.
- Testes: `tests/test_infrastructure/test_llm/test_config.py` e `tests/test_presentation/test_llm_config_dialog.py`.
- Não afeta `llm.embedding` (fica para a `llm-chat-rag`) nem o bloco `llm.guidance`.
