## Context

Ver `proposal.md` — Why. A investigação sobre o ticker `KNCA11` confirmou, pelo HTML do Informe Mensal em cache (`informe-mensal/KNCA11/2026/09/1350966.html`):

- O rótulo do CNPJ é `CNPJ do Fundo: 41745701000137`; os demais FIIs usam `CNPJ do Fundo/Classe`. O parser atual só reconhece a segunda forma, então `B3InformeMensal.cnpj` fica `None`.
- O mesmo informe contém `Nome do Gestor: KINEA INVESTIMENTOS LTDA` e `CNPJ do Gestor: 08604187000144`, mas o modelo/parser não têm campos de gestor e o provider B3 não os emite.
- O Informe Anual da CVM (`FII/DOC/INF_ANUAL`) não possui registro de FIAGROs como `KNCA11` (só fundos do tipo FII), portanto o fallback de gestor via CVM não preenche o campo.
- A resolução de identidade B3 já funciona (`fund_identity/KNCA11.json` contém `id_fnet` e CNPJ), e a composição já consulta B3 antes da CVM; o problema está na extração dos campos, não na ordem das fontes.
- O cache persistente `ticker → idFNET → CNPJ` (`JsonFundIdentityStore`) já é gravado por `B3FundRepository.find_by_ticker` e injetado no `B3FundamentalRepository`. A change não cria outro cache: passa a consumir explicitamente esse registro como fallback do `idFNET` na leitura do informe e do CNPJ fiscal.
- Evidência do defeito em produção: em `2026-11-12`, a chave `fund_docs_21549_40_2024-11-12_2026-11-12_1` foi gravada com `totalRecords: 0` (enquanto a janela de 12 meses tinha 9 documentos e a consulta ao vivo voltava a retornar 9). Sem o informe, `obter_informe` retornava `None` e o CNPJ aparecia apenas pelo cache de idFNET, com administrador e gestor ausentes.
- Após a correção, a verificação sobre o cache real retornou o informe `1350966` com CNPJ `41745701000137`, administrador `INTRAG DTVM LTDA.` e gestor `KINEA INVESTIMENTOS LTDA`.
- A observação do dia `2026-11-12` já estava persistida sem administrador/gestor antes da correção. Como o histórico diário é imutável para observações completas, ela não é reescrita por uma leitura normal; a regravação exige `force_refresh` (botão “Atualizar fundamentos” ou CLI de atualização) ou ocorre na próxima data.

## Goals / Non-Goals

**Goals:**
- Preencher CNPJ, administrador e gestor de FIAGROs a partir do próprio Informe Mensal da B3.
- Usar o `idFNET`/CNPJ já persistidos por ticker como fallback quando a fonte B3 não responder ou o informe não trouxer o CNPJ.
- Manter o Informe Anual da CVM como fallback de gestor para FIIs que não o tragam na B3.
- Preservar a proveniência por campo e a tolerância a rótulos ausentes.

**Non-Goals:**
- Reescrever observações já persistidas no histórico diário (a correção vale a partir da próxima análise).
- Alterar a ordem de prioridade global das fontes (Fundamentus → B3 → CVM → Papel).
- Passar a baixar o Informe Anual de FIAGROs da CVM (dataset distinto) ou introduzir novas fontes.

## Decisions

### 1. Alias de rótulo para CNPJ no parser do Informe Mensal

Adicionar `cnpjdofundo` à tupla de rótulos de CNPJ, ao lado de `cnpjdofundoclasse`. Como `_normalizar` remove pontuação, ambos os formatos convergem para chaves estáveis e não colidem com `cnpjdoadministrador`/`cnpjdogestor`.

- **Alternativa descartada**: casar por prefixo `cnpjdofundo`, que também aceitaria rótulos inesperados e dificultaria o teste de contrato por rótulo exato.

### 2. Gestor como campo de primeira classe do Informe Mensal

Estender `B3InformeMensal` com `nome_gestor` e `cnpj_gestor`; o parser os extrai dos rótulos `Nome do Gestor` e `CNPJ do Gestor`; o `B3FundamentalDataProvider` emite `CAMPO_GESTOR` e `CAMPO_CNPJ_GESTOR` com fonte `B3`. A composição já para no primeiro provider que fornece cada campo, então o `CvmAnnualFundDataProvider` continua como fallback natural quando a B3 não trouxer o gestor.

- **Alternativa descartada**: consultar novamente o HTML do informe em outro provider só para o gestor. Duplicaria download/parse e quebraria a proveniência única por campo.
- **Alternativa descartada**: manter gestor apenas na CVM e criar um fallback específico para FIAGRO. O dado já está na B3 e o dataset anual de FII não cobre FIAGRO; a fonte B3 é mais direta e atual.

### 3. Sem mudança de composição e sem novo cache

A ordem `Fundamentus → B3FundamentalDataProvider → CvmAnnualFundDataProvider → CvmPapelCnpjProvider` já atende à prioridade desejada. O HTML do informe é cacheado por documento e reprocessado a cada leitura, portanto a mudança de parser passa a valer na próxima análise sem invalidação de cache.

- **Alternativa descartada**: versionar/invalidar o cache de HTML. O cache guarda o HTML bruto, não o resultado do parser; reprocessá-lo já aplica o novo parser.
- **Alternativa descartada**: criar um store fiscal separado. O store de identidade existente já contém `idFNET` e CNPJ por ticker com escrita atômica e versionamento; duplicá-lo criaria duas fontes de verdade para o CNPJ.

### 4. Reuso do cache persistente de idFNET/CNPJ como fallback fiscal

`JsonFundIdentityStore` já grava, a cada resolução bem-sucedida, `idFNET`, CNPJ, nome e tipo por ticker. `B3FundRepository.find_by_ticker` o consulta quando a listagem B3 está incompleta ou indisponível, e `B3FundamentalRepository` já resolve a identidade por esse repositório; portanto o `idFNET` persistido já alimenta a listagem do Informe Mensal. A mudança acrescenta uma leitura pública dessa identidade para o `B3FundamentalDataProvider` emitir o CNPJ persistido quando `informe.cnpj` for ausente, mantendo o valor do informe como prioritário.

- **Alternativa descartada**: ler o arquivo do store diretamente no provider. Manteria o caminho de resolução duplicado; a identidade deve continuar a ser resolvida pelo `B3FundRepository`, que já aplica a precedência "listagem completa > store persistido".
- **Alternativa descartada**: persistir administrador e gestor nesse mesmo registro. O store é de identidade de fundo (idFNET/CNPJ) e mudar seu schema invalidaria os registros existentes; o objetivo aqui é apenas reutilizar o idFNET/CNPJ já gravados.

### 5. Listagem de documentos vazia não é cacheada e é repetida uma vez

A B3 responde intermitentemente com `totalRecords: 0` para o `GetStructuredReports`, mesmo havendo documentos no período; esse vazio era gravado no cache por 1 dia e impedia a extração do informe, derrubando administrador e gestor. A chave da listagem passa a ser versionada por `PARSER_VERSION` e uma primeira página vazia é descartada do cache e consultada novamente uma vez. Se permanecer vazia, a chave é removida para não congelar a ausência.

- **Alternativa descartada**: reduzir a janela de 24 para 12 meses. Os dados de cache mostram vazios intermitentes também em janelas de 12 meses; a janela não é a causa.
- **Alternativa descartada**: repetir via retry HTTP com backoff longo. A falha é semântica (HTTP 200 com lista vazia) e o backoff de até 14s penalizaria fundos legitimamente sem documentos; uma repetição imediata resolve o caso observado.

## Risks / Trade-offs

- **Informe com ambos os rótulos de CNPJ** → `_valor` retorna o primeiro na ordem do documento; os formatos observados são mutuamente exclusivos. Coberto por teste com fixture de FIAGRO.
- **Gestor da B3 divergir do gestor da CVM** → a B3 prevalece por ser a fonte primária definida; a CVM segue como fallback e a origem é registrada por campo.
- **Observações diárias já completas não são reescritas** → a observação do dia continua sem os campos até uma recomputação forçada; orientar o uso de “Atualizar fundamentos”/CLI, que usam `force_refresh`, para ver a correção no mesmo dia. Não há migração retroativa.
- **Rótulo de gestor ausente em alguns informes** → os campos permanecem `None` sem invalidar CNPJ/administrador, mantendo a tolerância já existente.
- **CNPJ persistido desatualizado** → o valor do informe prevalece sempre que disponível; o store só atua como fallback quando o CNPJ do informe está ausente ou a B3 não responde, e é atualizado na próxima resolução bem-sucedida.
- **Identidade persistida ausente/corrompida** → o fallback simplesmente não é aplicado; o comportamento atual (campo ausente) é mantido, sem gravar resultado negativo.
