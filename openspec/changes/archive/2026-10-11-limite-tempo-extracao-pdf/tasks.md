## 1. Extração de páginas reutilizável

- [x] 1.1 Refatorar `application/document_preview.py` para expor a extração de páginas do PDF (abrir/descriptografar e iterar páginas tolerando falhas) reutilizada por `extrair_pdf`; verificar com `tests/test_application/test_document_preview.py` verde.
- [x] 1.2 Garantir que a iteração de páginas tolera `LimitReachedError` (subclasse de `PyPdfError`) por página: prossegue para as seguintes, conta a página como falha e resulta em `PARCIAL`, sem propagar; verificar com teste unitário que injeta a exceção em uma página e preserva o texto das demais (sem PDF real).

## 2. Extrator com orçamento de tempo

- [x] 2.1 Criar `application/extracao_orcada.py` com um auxiliar puro de acumulação/prazo (fonte de mensagens e relógio injetáveis) e `extrair_arquivo_com_orcamento(caminho, seletor=None, senha=None, *, timeout=EXTRACAO_TIMEOUT_S)` com `EXTRACAO_TIMEOUT_S = 90.0` (abaixo de `LIMITE_INATIVIDADE_S = 120 s` do watchdog, verificado por teste de guarda), executando PDF em processo separado (`multiprocessing` com contexto `spawn`), transmitindo as páginas por `Pipe` e encerrando o filho no estouro; HTML extraído no processo corrente; verificar com teste unitário do auxiliar puro cobrindo estouro com texto → `PARCIAL` (preservando o texto) e estouro sem texto → `FALHA`.
- [x] 2.2 Testes de integração do extrator limitado que rodam em qualquer máquina, sem o PDF problemático: PDF pequeno existente (`tests/fixtures/b3/bdr_aviso_exxo.pdf.b64`) dentro do orçamento → texto `OK`; orçamento nulo → `FALHA` com o filho encerrado (sem processo vivo); HTML → imediato; senha repassada ao PDF; verificar com `pytest tests/test_application/test_extracao_orcada.py`.
- [x] 2.3 Garantir a preservação da ausência de texto: leitura concluída sem texto continua `SEM_TEXTO`, e estouro de orçamento/`LimitReachedError` produzem `PARCIAL`/`FALHA`, nunca `SEM_TEXTO`; verificar com teste unitário cobrindo os dois casos (sem PDF problemático).

## 3. Adoção nos pontos de chamada

- [x] 3.1 Trocar `document_flow_mixin._texto_do_arquivo` (base) para usar `extrair_arquivo_com_orcamento`; verificar com `tests/test_presentation/test_document_flow.py` e `tests/test_presentation/test_document_flow_password.py` verdes.
- [x] 3.2 Trocar `noticias_panel._texto_do_arquivo` para usar `extrair_arquivo_com_orcamento`; verificar com `tests/test_presentation/test_noticias_panel.py` verde.
- [x] 3.3 Adicionar `multiprocessing.freeze_support()` ao ponto de entrada (`presentation/main.py`) para o build congelado; verificar que `flowscope --version` executa e que importar `flowscope.application.extracao_orcada` não dispara subprocesso.

## 4. Verificação integrada

- [x] 4.1 Verificar o comportamento do lote quando a extração de um documento retorna `PARCIAL` por estouro (extrator fake que devolve `PARCIAL`, sem PDF real): o documento é contabilizado, permanece pendente e a fase avança para o próximo; verificar com teste headless de `_preparar_textos`/`executar_resumos`.
- [x] 4.2 Rodar `pytest` (marker padrão) e confirmar a suíte verde, e rodar `openspec validate limite-tempo-extracao-pdf --strict`.
- [x] 4.3 Conferir manualmente (observação, não teste do repositório e sem o PDF problemático versionado) que "Resumir pendentes" do AGRO3 avança além do documento problemático, deixando-o pendente, sem travar a fase.
