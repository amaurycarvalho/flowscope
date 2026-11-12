## Why

Os FIAGROs da watchlist (como `KNCA11` e `BBGO11`) continuam com `Dados fiscais` incompletos: o Informe Mensal da B3 desses fundos rotula o campo como `CNPJ do Fundo` (sem `/Classe`), que o parser atual não reconhece, e o gestor não é extraído do informe. Como o Informe Anual da CVM só cobre `FII` (não inclui FIAGROs), o fallback de gestor nunca preenche o campo. O resultado é `CNPJ` e `Gestor` vazios mesmo após a resolução de identidade B3 funcionar.

## What Changes

- Extrair o CNPJ do fundo do Informe Mensal aceitando os rótulos `CNPJ do Fundo/Classe` e `CNPJ do Fundo`, sem invalidar os demais campos quando o rótulo variar.
- Extrair do Informe Mensal do FundosNet o gestor (nome e CNPJ), ao lado do administrador já suportado, ampliando o modelo normalizado do informe e o provider fundamentalista da B3.
- Passar o gestor do FII/FIAGRO a ser resolvido primeiro pelo Informe Mensal da B3, mantendo o Informe Anual da CVM (`INF_ANUAL`) como fallback quando a B3 não fornecer o dado.
- Reutilizar a identidade persistida `ticker → idFNET → CNPJ` (já gravada pela solução de resiliência da resolução de fundos) como fonte do `idFNET` na leitura do Informe Mensal e como fallback do CNPJ fiscal quando o informe não o trouxer ou a B3 estiver indisponível, sem criar um segundo cache.
- Tornar a listagem de documentos do `GetStructuredReports` resistente a respostas vazias intermitentes: repetir uma vez a primeira página vazia, versionar a chave de cache e não persistir vazio persistente, para que administrador e gestor não desapareçam por um cache envenenado.
- Manter a proveniência (`B3`/`CVM`) por campo e a omissão de itens sem valor em nenhuma fonte.

## Capabilities

### New Capabilities

(nenhuma)

### Modified Capabilities

- `b3-fii-extraction`: a extração da identidade fiscal do Informe Mensal passa a reconhecer as variantes de rótulo de CNPJ e a extrair também gestor (nome e CNPJ); a identidade persistida por ticker (`idFNET`/CNPJ) passa a ser usada como fallback do informe e do CNPJ fiscal.
- `fundamental-source-fallback`: a prioridade da identidade fiscal passa a obter o CNPJ do Informe Mensal ou da identidade persistida da B3 e o gestor do Informe Mensal, com o Informe Anual da CVM como fallback, cobrindo FIAGROs que não constam no `INF_ANUAL` de FIIs.

## Impact

- Código: `infrastructure/b3/informe_mensal_parser.py`, `domain/b3/models.py`, `infrastructure/fii/b3_fundamental_provider.py`, `infrastructure/fii/b3_fundamental_repository.py` (leitura da identidade persistida) e `infrastructure/b3/funds_client/documentos.py` (listagem resiliente).
- Specs relacionadas: `b3-fii-extraction`, `fundamental-source-fallback`; `cvm-annual-fund-data` permanece como fallback inalterado.
- Reuso do store existente `infrastructure/b3/fund_identity_store.py` (arquivo `fund_identity/<TICKER>.json`); nenhum cache novo, nenhuma migração de schema e nenhuma invalidação das identidades já gravadas.
- Sem novas dependências e sem mudança em contratos externos da B3/CVM.
- Dados já gravados no histórico diário não são reescritos por uma leitura normal do mesmo dia; a observação existente só é substituída quando a análise é forçada (`force_refresh`, usado por “Atualizar fundamentos” e pela CLI de atualização) ou na próxima data de referência.
