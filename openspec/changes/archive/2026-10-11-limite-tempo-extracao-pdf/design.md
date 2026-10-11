## Context

Ver `proposal.md` — Why. Hoje `extrair_arquivo`/`extrair_pdf`
(`application/document_preview.py`) extraem de forma síncrona e sem orçamento de
tempo. A fase "Preparando textos" do lote (`presentation/gui/resumos_job.py`)
chama `painel.preparar_texto` documento a documento; com um PDF patológico, uma
única extração consome minutos. Evidência: um `/ToUnicode` com
`bfrange <0000> <FFFF>` (65.536 entradas) é expandido inteiro em Python pelo
`pypdf 6.19`; mediu-se 23,8 s para 29 páginas e > 180 s (não terminou) para 414
páginas (`AGRO3/2026/10/assembleia/1569599.pdf`). O `pypdf` é Python puro: numa
thread, a chamada não pode ser interrompida e continua consumindo o GIL.

## Goals / Non-Goals

**Goals:**
- Limitar a extração de cada PDF a 90 s por documento, sem travar a operação.
- Preservar o texto parcial já extraído no estouro e classificar como `PARCIAL`,
  deixando o documento pendente e seguindo para o próximo.
- Manter a extração de HTML imediata e o comportamento das extrações normais.

**Non-Goals:**
- Não corrigir o desempenho do `pypdf` nem baixar o limite de CMap (opção 2,
  descartada pelo usuário).
- Não passar a persistir/resumir `PARCIAL` (a política atual permanece).
- Não tornar o cancelamento responsivo durante a extração de um único documento
  (o orçamento limita o pior caso).

## Decisions

### 1. Extração em processo separado com prazo rígido

Executar a extração do PDF em um processo filho e aguardar até o orçamento no
pai; ao estourar, encerrar o filho. Alternativa: thread com timeout — rejeitada
porque uma thread não pode ser morta e mantém o GIL, então o travamento
permaneceria consumindo CPU. Alternativa: baixar `MAPPING_DICTIONARY_SIZE_LIMIT`
do `pypdf` (opção 2) — rejeitada pelo usuário. O orçamento DEVE ficar abaixo do
limite de inatividade do job de background (`LIMITE_INATIVIDADE_S = 120 s`),
pois a extração bloqueia o worker sem publicar progresso; por isso usa-se **90
s**, com margem para o watchdog não encerrar o lote por inatividade.

### 2. Transmissão página a página e texto parcial

O filho itera as páginas e envia cada resultado ao pai por um `Pipe`, terminando
com um marcador de fim. O pai acumula os textos. Ao estourar o orçamento, encerra
o filho e monta o resultado com o que já recebeu: `PARCIAL` (com o texto somado e
`paginas_com_falha` contando as falhas mais a página interrompida) quando houve
texto, ou `FALHA` (vazio) quando nenhuma página produziu texto. Alternativa:
descartar tudo e devolver `FALHA` — rejeitada por perder o texto parcial e por
não expressar "pendente com texto parcial". A decisão de acumulação/prazo é
extraída para um auxiliar puro (fonte de mensagens e relógio injetáveis) para
ser testável de forma determinística e independente de PDF real. Um resultado
interrompido NUNCA é `SEM_TEXTO`: `SEM_TEXTO` permanece reservado à leitura
concluída sem texto, preservando a semântica de ausência definitiva (persistida,
fora dos pendentes e sem resumo); estouro de orçamento e `LimitReachedError`
produzem `PARCIAL` ou `FALHA`.

### 3. Método de início `spawn`

Usar `multiprocessing.get_context("spawn")` para iniciar o filho. Alternativa:
`fork` (padrão no Linux) — rejeitada por ser inseguro em um processo com threads
(aplicação Tk) e locks de rede. O `spawn` reimporta os módulos no filho, o que
exige que o alvo seja uma função de topo de módulo importável e que o ponto de
entrada chame `multiprocessing.freeze_support()` no build congelado
(PyInstaller).

### 4. Extração de HTML fora do orçamento

Somente arquivos `.pdf` passam pelo processo separado; `.html`/`.htm` continuam
no processo corrente. Evita o custo de `spawn` no caso comum (notícias) e mantém
a semântica atual.

### 5. Refatorar `document_preview` para expor a extração por página

Extrair uma função de iteração de páginas a partir de `extrair_pdf`, reutilizada
por `extrair_pdf` (uso in-process) e pelo filho do extrator limitado, mantendo
um único ponto para abrir/descriptografar e tolerar falhas por página. A
tolerância por página DEVE capturar `LimitReachedError`/`PyPdfError` (e demais
exceções da página), contando-a como página com falha e prosseguindo — a
biblioteca deixa o `LimitReachedError` propagar de dentro da extração de texto,
então restringir a captura a `ValueError`/`IndexError` faria o documento inteiro
falhar. Esse comportamento é a garantia explícita do requisito "Tolerância a
limite de recursos da biblioteca por página".

### 6. Módulo e pontos de chamada

Novo `application/extracao_orcada.py` com
`extrair_arquivo_com_orcamento(caminho, seletor=None, senha=None, *,
timeout=EXTRACAO_TIMEOUT_S)`, `EXTRACAO_TIMEOUT_S = 90.0` e um tempo de carência
para colher o filho após a resposta. Adoção em
`presentation/gui/charts/document_flow_mixin._texto_do_arquivo` (base) e em
`presentation/gui/charts/noticias_panel._texto_do_arquivo`. Chamadas de
compatibilidade que operam sobre bytes já em memória (`extrair_pdf` em
`bdr/text.py` e `noticias_vinculo.py`) ficam fora do escopo desta change.

## Risks / Trade-offs

- [Custo de `spawn` por PDF] → Só PDFs pagam o custo (~0,1–0,5 s); HTML não.
- [Build congelado sem `freeze_support`] → Adicionar `multiprocessing.freeze_support()`
  no ponto de entrada; documentar como pré-requisito.
- [Processo filho órfão] → Sempre encerrar e colher (`terminate`/`kill` +
  `join`) em `finally`, com o filho `daemon=True`.
- [`PARCIAL` não é persistido e é retentado do zero] → Aceito: mantém a política
  vigente e a possibilidade de nova tentativa; revisitar persistência parcial
  fica para uma change futura.
- [Espera de até 90 s sem avanço de contador em documento patológico] → Aceito
  nesta change; um progresso mais fino por página (heartbeat) é melhoria futura.
  O orçamento DEVE permanecer abaixo de `LIMITE_INATIVIDADE_S` (120 s) para o
  watchdog não encerrar o lote.
- [Diferenças entre plataformas no `Pipe`/`spawn`] → Usar o mesmo `context` para
  `Pipe` e `Process`; selecionar o resultado pelo sufixo antes de decidir o
  caminho.

## Migration Plan

Sem migração de dados. Rollout: introduzir o módulo e trocar os dois pontos de
chamada; nenhum contrato de dados muda. Rollback: reverter os pontos de chamada
para `extrair_arquivo` e remover o módulo/`freeze_support`.

## Open Questions

Nenhuma pendente.
