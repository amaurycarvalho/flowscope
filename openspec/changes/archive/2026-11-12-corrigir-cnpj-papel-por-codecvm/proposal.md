## Why

Na watchlist atual, 4 tickers de Papel ficam sem CNPJ em `Dados fiscais`: `BPAC11`, `CMIN3`, `MBRF3` e `CSNA3`. A ponte ticker → CNPJ usa apenas o casamento exato entre o ticker e `Codigo_Negociacao` do FCA, mas nesses casos o FCA traz um valor não literal (`000000` para Units, `ADR` para o ADR da Marfrig, ou o próprio codeCVM em vez do ticker). O B3 já resolve o `codeCVM` desses ativos e o cadastro `cad_cia_aberta.csv` da CVM mapeia `CD_CVM` para `CNPJ_CIA`, permitindo uma resolução robusta.

## What Changes

- Resolver o CNPJ de Papel em duas etapas: primeiro pelo casamento exato de `Codigo_Negociacao` no FCA; se não houver correspondência, resolver o `codeCVM` via B3 e usá-lo como chave no cadastro de companhias abertas da CVM.
- Adicionar a aquisição e o cache do dataset `CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv`, com parser `CD_CVM → CNPJ_CIA`, hash do arquivo e versão do parser.
- Expor a resolução `ticker → codeCVM` do `B3FundRepository` e injetá-la no `CvmAcionistasSource`, reutilizando o cache de 30 dias já existente.
- Servir o último `codeCVM` persistido quando a B3 estiver indisponível e o cache estiver expirado, evitando que uma falha transitória derrube o CNPJ de Papel.
- Exibir a razão social do Papel imediatamente após o CNPJ em `Dados fiscais`, usando `DENOM_SOCIAL` do cadastro de companhias; FIIs e BDRs mantêm o formato atual.
- Manter a resolução atual como primeira tentativa e preservar a tolerância a falhas: ausência de codeCVM, cadastro indisponível ou CNPJ inválido não devem impedir a análise dos demais tickers.
- Versionar o parser do cadastro e tolerar mapas normalizados em formato anterior, para que um cache antigo (valor string em vez de identidade) não faça o CNPJ do Papel desaparecer.
- Cobrir os quatro casos da watchlist com testes de regressão (`BPAC11`, `CMIN3`, `MBRF3`, `CSNA3`) e casos sintéticos de FCA literal e de fallback.

## Capabilities

### New Capabilities

(nenhuma)

### Modified Capabilities

- `cvm-fre-acionistas`: a ponte ticker → CNPJ passa a usar o FCA como primeira fonte e, quando o código de negociação não for o ticker, o `codeCVM` da B3 com o cadastro de companhias abertas da CVM; o dataset do cadastro passa a ser adquirido, cacheado e versionado.
- `code-cvm-resolution`: a resolução `ticker → codeCVM` passa a servir o último valor persistido quando a B3 falhar após as retentativas, sem gravar um novo resultado negativo.
- `fundamental-source-fallback`: a identidade fiscal de Papel passa a incluir a razão social, além do CNPJ, quando disponível na CVM.
- `gui-interface`: `Dados fiscais` de Papel passa a exibir `CNPJ` seguido de `Razão social <razão social>`; FIIs mantêm CNPJ, administrador e gestor.

## Impact

- Código: `infrastructure/cvm/acionistas.py`, `infrastructure/fii/cvm_fund_data_provider.py`, `infrastructure/b3/fund_repository.py`, `application/fundamental_ports.py`, `application/fundamental_analysis.py`, `application/fundamental/linhas.py`, `domain/fii/analysis.py`, `infrastructure/fii/fundamental_analysis_codec.py`, `presentation/gui/app_tabs.py`, `presentation/composicao.py`.
- Cache: novo dataset em `~/.cache/flowscope/cvm/cad/<ano>/cad_cia_aberta.csv` (hash + versão), além do cache normalizado `codeCVM → CNPJ`.
- Sem novas dependências; sem mudança de contrato externo da B3/CVM.
- A correção aparece na próxima carga de fundamentos após a atualização; os registros diários já gravados sem CNPJ não são reescritos retroativamente.
