## Why

Quatro defeitos fazem o botão "Resumir pendentes" permanecer ativo sem trabalho útil e provocam re-download de URLs já baixadas: (1) documentos/notícias com ausência definitiva de texto continuam contando como pendentes; (2) um Relatório Gerencial com avaliação de guidance cuja IA falha (ex.: cota esgotada) mantém o botão travado indefinidamente; (3) material facts são baixados de novo porque a data de referência com hora não é interpretada e o caminho de cache muda; (4) a regeneração de resumos truncados foi aplicada a "Documentos" mas não a "Notícias", deixando resumos incompletos congelados. O problema é observável no cache real (GGRC11, RBVA11, XPLG11, BBDC3, CACR11) e no log (erros 429 de cota).

## What Changes

- **Pendência considera ausência definitiva de texto**: documentos e notícias cujo texto em cache é conclusivamente vazio (marcador `Sem texto extraível…` ou apenas whitespace) deixam de contar como pendentes e não mantêm o botão habilitado. Itens de notícia cujo corpo é um apontador ainda não resolvido continuam pendentes (retentativa por desenho).
- **Pendência de guidance não trava o botão em falha da IA**: um RG já resumido que permanece `deterministico` porque a avaliação por IA falhou não mantém o botão habilitado para sempre; a falha é registrada/exibida e o RG volta a ser elegível quando a IA estiver funcional.
- **Data de referência de material fact com hora**: `dateReference` no formato `DD/MM/AAAA HH:MM` passa a ser interpretado (hora descartada), estabilizando o caminho de cache e evitando re-download por mudança de mês.
- **Registro de URLs baixadas com sucesso**: novo registro por escopo (ticker para documentos; global para notícias) consultado antes do download, para não baixar novamente uma URL já concluída com sucesso, independentemente de data/slug/categoria derivados.
- **Regeneração de resumos truncados em Notícias**: a lista de pendentes de notícias passa a considerar desatualizado o resumo que não termina em pontuação final, alinhando-se ao comportamento já existente em Documentos.

## Capabilities

### New Capabilities
- `deduplicacao-url`: registro de URLs baixadas com sucesso por escopo, consultado antes do download para impedir nova tentativa da mesma URL; poda consistente com o cache.

### Modified Capabilities
- `documentos-ticker-panel`: a definição de pendência do botão/lote deixa de contar documentos com ausência definitiva de texto.
- `noticias-panel`: a definição de pendência de notícias exclui ausência definitiva de texto e passa a regenerar resumos truncados, mantendo apontadores não resolvidos pendentes.
- `relatorio-gerencial-guidance`: a pendência de guidance não mantém o botão habilitado indefinidamente quando a avaliação por IA falha repetidamente.
- `material-facts-extraction`: a data de referência com componente de hora passa a ser interpretada.
- `documentos-aquisicao`: reuso de cache passa a considerar o registro de URL e a data de referência interpretada, evitando novo download de documento já adquirido.

## Impact

- Código: `presentation/gui/charts/document_flow_mixin.py`, `application/documentos/document_guidance.py`, `application/avaliar_guidance.py`, `application/noticias/lote.py`, `presentation/gui/charts/noticias_panel.py`, `infrastructure/b3/documentos_aquisicao.py`, `infrastructure/b3/documentos_relevantes.py`, `infrastructure/b3/noticias_aquisicao.py`, `infrastructure/content_hashes.py` (novo registro), `infrastructure/fii/fundamentus/normalizers.py` (parse de data com hora).
- Cache: novo arquivo de registro de URLs por ticker e global de notícias; sem migração obrigatória (registro é populado conforme os downloads ocorrem).
- Sem quebra de contrato de dados existente; resumos truncados de notícias passam a ser regenerados quando o usuário aciona o lote.
