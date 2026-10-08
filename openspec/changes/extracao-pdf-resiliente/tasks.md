## 1. Extrator resiliente unificado (application)

- [x] 1.1 Definir `StatusExtracao`/`ExtracaoTexto` em `application/document_preview.py` e verificar com teste unitário que os cinco estados (`OK`, `PARCIAL`, `SEM_TEXTO`, `FALHA`, `PROTEGIDO`) são distinguíveis
- [x] 1.2 Implementar `extrair_pdf(dados, senha=None)` com tolerância por página e verificar com fixtures que: todas as páginas legíveis → `OK`; página ilegível entre legíveis → `PARCIAL` com `paginas_com_falha>0`; todas ilegíveis → `FALHA`
- [x] 1.3 Implementar a tentativa de `decrypt("")` e o uso da senha informada e verificar com fixtures de PDF criptografado: senha vazia extrai (`OK`), senha conhecida extrai (`OK`), senha desconhecida/ausente resulta em `PROTEGIDO`
- [x] 1.4 Manter `texto_de_pdf(...) -> str` como adaptador de compatibilidade e verificar que os testes existentes de PDF inválido continuam retornando string vazia

## 2. Semântica de cache e unificação da extração

- [x] 2.1 Alterar `DocumentFlowMixin._texto_do_arquivo` para devolver `ExtracaoTexto` e adaptar o override de `NoticiasPanel`, verificando com `test_document_flow` e `test_noticias_panel`
- [x] 2.2 Fazer `preparar_texto` gravar no store apenas em `OK`/`SEM_TEXTO` e verificar com teste que `PARCIAL`/`FALHA`/`PROTEGIDO` não chamam `salvar` e retornam o texto parcial (ou vazio)
- [x] 2.3 Memoizar apenas resultados definitivos e verificar com teste que `PARCIAL`/`FALHA`/`PROTEGIDO` não são gravados no cache persistente nem memoizados na sessão (permitindo a retentativa automática)
- [x] 2.4 Fazer `infrastructure/b3/bdr/text.extrair_texto` delegar a `extrair_pdf` e verificar com `test_bdr` e com os consumidores (BDR provider, guidance de FII)
- [x] 2.5 Garantir que o lote (`resumos_job`) pula `PARCIAL`/`FALHA`/`PROTEGIDO` sem diálogo, sem cachear e sem resumir, verificando com `test_resumos_job`

## 3. Senha no documento vinculado das Notícias

- [x] 3.1 Fazer `baixar_conteudo_vinculado` devolver `ExtracaoTexto | None` e aceitar `senha`, usando `extrair_pdf` no ramo PDF e mantendo `None` para "não resolvido", e verificar com `test_noticias_vinculo` (CVM e FNET, PDF protegido não colapsa em `None`)
- [x] 3.2 Ajustar o wiring (`app_wiring.py`, `app_tab_layout.py`) para o novo callable `Callable[[str, str | None], ExtracaoTexto | None]` e verificar com o teste de composição/importação
- [x] 3.3 Adaptar `NoticiasPanel._texto_do_arquivo`/`_texto_cacheado` para propagar `PROTEGIDO`/`PARCIAL` e manter a invalidação de apontador não resolvido, verificando com `test_noticias_panel`

## 4. Diálogo de senha, limite e nova extração (apresentação)

- [x] 4.1 Adicionar o seam `_solicitar_senha(arquivo) -> str | None` (padrão `None`) e o caminho de re-extração com senha e verificar com teste headless que `PROTEGIDO` interativo dispara a solicitação e re-submete a extração
- [x] 4.2 Implementar o diálogo modal em `DocumentTreePanel` e `NoticiasPanel` e verificar com testes de apresentação (monkeypatch do diálogo)
- [x] 4.3 Limitar a 3 tentativas por documento/seleção (`senha_max_tentativas` parametrizável) e verificar com teste que a 4ª tentativa não abre diálogo e exibe a mensagem informativa
- [x] 4.4 Tratar senha incorreta (nova solicitação) e cancelamento (ausência no Documentos; corpo original nas Notícias) e verificar com testes de ambos os caminhos
- [x] 4.5 Anotar texto parcial no preview (com o número de páginas) e verificar com teste que o parcial é anotado e não gera resumo
- [x] 4.6 Retentar automaticamente ao selecionar/clicar no documento novamente, incluindo o clique no nó já selecionado (que não dispara `<<TreeviewSelect>>`), e verificar com teste que a extração é refeita sem controle dedicado
- [x] 4.7 Garantir que o lote ("Resumir pendentes") retenta os não definitivos (reconverte e resume só se ficar completo) e nunca solicita senha, verificando com teste em ambas as abas
- [x] 4.8 Confirmar que a senha não é persistida nem logada, verificando o store, o cache de resumo e as chamadas de log no teste

## 5. Unificação do marcador de ausência

- [x] 5.1 Consolidar `SEM_TEXTO`/`tem_texto` em `domain/documents/texto.py` e re-exportar em `application/document_preview.py`, verificando os importadores e testes de marcador
- [x] 5.2 Atualizar os importadores para a fonte única e verificar que `ruff`/`flake8` não reportam imports órfãos

## 6. Verificação final

- [x] 6.1 Rodar a suíte de testes com cobertura (`fail_under = 85`) e confirmar aprovação
- [x] 6.2 Rodar lint e os testes de fronteira de arquitetura (`tests/architecture`) e confirmar aprovação
- [x] 6.3 Rodar `openspec validate extracao-pdf-resiliente` e confirmar que o change está válido (os avisos de SHALL/MUST são esperados por as specs do projeto serem em português)
