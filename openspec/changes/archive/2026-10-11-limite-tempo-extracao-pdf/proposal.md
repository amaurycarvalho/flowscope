## Why

A extração de texto de alguns PDFs reais do FlowScope é patologicamente lenta no
`pypdf`: um `/ToUnicode` com `bfrange <0000> <FFFF>` (65.536 entradas) é expandido
inteiro em Python, levando de dezenas de segundos a minutos por documento (caso
observado em assembleias do AGRO3, ex.: `1569599.pdf`, 414 páginas, > 3 min).
Como a fase "Preparando textos" do "Resumir pendentes" extrai um documento por
vez de forma síncrona e sem orçamento de tempo, o lote fica parado no último
contador concluído (ex.: `Preparando textos — 3/21`) sem progresso nem
cancelamento, parecendo travado. Um único PDF ruim bloqueia toda a operação.

## What Changes

- **Orçamento de tempo por documento**: a extração de texto de cada arquivo PDF
  passa a ser executada em um processo separado, com um orçamento de **90
  segundos** por documento (abaixo do limite de inatividade de 120 s do job de
  background, para não ser encerrado pelo watchdog). O processo filho extrai
  página a página e devolve o texto já produzido ao processo pai.
- **Desfecho por estouro de orçamento com texto parcial**: se a extração exceder
  o orçamento, o processo filho é encerrado e o resultado é o **texto parcial já
  extraído**, classificado como `PARCIAL` (sem propagar exceção). O documento
  **permanece pendente** para nova tentativa — não é marcado como ausência
  definitiva de texto — e o lote **prossegue para o próximo documento**, sem
  bloquear a fase.
- **Tolerância a limite de recursos por página**: quando a extração de uma
  página falhar com `LimitReachedError` (subclasse de `PyPdfError`), o sistema
  NÃO DEVE descartar o documento: prossegue para as páginas seguintes,
  contabiliza a página como falha e classifica o resultado como `PARCIAL`. É a
  garantia explícita de um comportamento hoje implícito na tolerância por página.
- **Preservação de documentos sem texto**: o comportamento atual de documentos
  vazios permanece — ausência definitiva (`SEM_TEXTO`) é persistida, sai dos
  pendentes e não gera resumo. O estouro de orçamento e o erro de limite
  classificam como `PARCIAL`/`FALHA`, nunca `SEM_TEXTO`, para não transformar uma
  extração interrompida em ausência definitiva.
- **Aplicação em pré-visualização e lote**: o mesmo caminho limitado atende a
  pré-visualização sob demanda e a fase de preparação do lote de resumos, em
  Documentos e Notícias (a extração de HTML permanece imediata, sem subprocesso).
- **Suporte a build congelado**: o ponto de entrada passa a chamar
  `multiprocessing.freeze_support()` para o subprocesso funcionar no executável
  empacotado.
- **Sem dependência nova**: usa apenas `multiprocessing` da biblioteca padrão.

## Capabilities

### New Capabilities

(nenhuma)

### Modified Capabilities

- `extracao-texto-pdf`: novos requisitos de (a) orçamento de tempo da extração de
  arquivo em processo separado, com `PARCIAL`/`FALHA` ao exceder o orçamento, e
  (b) tolerância por página a `LimitReachedError`, com classificação `PARCIAL`.
- `documentos-ticker-panel`: novo requisito garantindo que a pré-visualização e
  a preparação do lote não bloqueiem indefinidamente quando um documento excede
  o orçamento, mantendo o item pendente e a fase avançando.

## Impact

- Código: novo extrator limitado na camada de aplicação (execução em
  subprocesso com orçamento); adoção em
  `presentation/gui/charts/document_flow_mixin.py` (`_texto_do_arquivo` da base)
  e `presentation/gui/charts/noticias_panel.py`; `multiprocessing.freeze_support()`
  em `presentation/main.py`.
- Comportamento observável: um documento com extração lenta deixa de travar a
  fase de preparação; ele retorna com o texto parcial (`PARCIAL`), permanece
  pendente e o lote segue. Como `PARCIAL` não é persistido nem resumido pelo
  desenho atual, o documento continua elegível para nova tentativa. Extrações
  normais permanecem inalteradas.
- Testes: novos testes na camada de aplicação que rodam em qualquer máquina
  (HTML imediato, PDF pequeno dentro do orçamento, estouro determinístico via
  orçamento nulo e falha de `LimitReachedError` injetada por página), **sem**
  depender do PDF problemático. Testes existentes de pré-visualização e lote
  permanecem verdes.
