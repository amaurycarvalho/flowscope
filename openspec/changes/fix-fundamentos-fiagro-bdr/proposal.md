## Why

Tickers FIAGRO (`BBGO11`, `KNCA11`) e BDRs (`EXXO34`) exibem campos vazios na sub-aba **Fundamentos** porque a resolução de identidade na B3 só consulta `typeFund="FII"` (FIAGROs ficam em `typeFund="FIAGRO"`), o histórico de proventos do Fundamentus só lê `proventos.php` (FIIs ficam em `fii_proventos.php`) e não há fonte de dividendos para BDRs — que o Fundamentus não cobre. O resultado é `N/A` em cotistas, indexadores, dados fiscais, data-com, dividendo anterior e tendência.

## What Changes

- Resolução de fundo na B3 passa a iterar os tipos de fundo `FII`, `FIAGRO`, `FIP` e `FIDC`, desbloqueando a cadeia B3/CVM para FIAGROs (nome, CNPJ, administrador, gestor, patrimônio, cotas, cotistas, indexadores e proventos B3).
- Histórico de proventos do Fundamentus passa a ler `fii_proventos.php` para FIIs/FIAGROs (tabela `Última Data Com`/`Tipo`/`Data de Pagamento`/`Valor`), preenchendo data-com, dividendo anterior, tendência e o P/L derivado.
- Classificação determinística de FIAGRO passa a reconhecê-los como `FII` com sub-tipo `FIAGRO`, eliminando `Desconhecido` no fallback e mantendo-os fora da elegibilidade FFO.
- Nova fonte de dividendos para BDRs via **Plantão de Notícias da B3**: lista `Aviso aos Acionistas` mês a mês, baixa o PDF do documento na CVM (POST `ExibirPDF`, base64), cacheia por ticker/ano/mês, extrai último dividendo, dividendo anterior, data-com, ISIN, depositário e empresa, e calcula P/L e Dividend Yield com anualização **trimestral (×4)**.
- A sub-aba Fundamentos passa a exibir, para BDRs, o caminho da pasta de cache dos PDFs em `Informações adicionais` e, quando não houver identidade fiscal, o depositário (ex.: `Banco B3 S.A.`), a empresa (ex.: `Exxon Mobil Corporation`) e o ISIN em `Dados fiscais`.

## Capabilities

### New Capabilities

- `bdr-dividend-fallback`: Extração de dividendos de BDRs a partir do Plantão de Notícias da B3 e dos PDFs de `Aviso aos Acionistas` da CVM — listagem mês a mês, download/cache por ticker/ano/mês, parsing do texto (valor por BDR, data-com, data de pagamento, ISIN, depositário, empresa), métricas derivadas (P/L trimestral e Dividend Yield) e exposição do caminho de cache e da identidade fiscal na tabela.

### Modified Capabilities

- `b3-fii-extraction`: a resolução de ticker para fundo B3 passa a consultar múltiplos `typeFund` (`FII`, `FIAGRO`, `FIP`, `FIDC`) em vez de apenas `FII`, com cache por tipo.
- `fii-classification`: a classificação determinística de fallback passa a reconhecer tickers FIAGRO como `FII` com sub-tipo `FIAGRO`.
- `fundamentus-fundamental-provider`: o histórico de proventos passa a ler `fii_proventos.php` quando a página de ações (`proventos.php`) não retornar proventos, cobrindo FIIs e FIAGROs.
- `fundamental-source-fallback`: a composição de fontes passa a incluir a fonte de dividendos de BDR como secundária e a expor o caminho de cache e a identidade fiscal de BDR quando as fontes primárias não os fornecerem.

## Impact

- **Código**: `infrastructure/b3/funds_client/fundos.py`, `infrastructure/b3/fund_repository.py`, `domain/fii/classification.py`, `infrastructure/fii/fundamentus/client.py`, `parser.py`, `dividend_provider.py`, `application/fundamental_providers.py`, `application/fundamental_analysis.py`, `domain/fii/analysis.py`, `presentation/gui/charts/fundamental_rows.py`, `presentation/gui/app.py`; novo submódulo `infrastructure/b3/bdr/`.
- **Dependências**: adicionar `pypdf>=4` (extração de texto dos PDFs da CVM; pura Python).
- **Cache**: nova árvore `~/.cache/flowscope/bdr/<TICKER>/<AAAA>/<MM>/<id>.pdf`; cache de fundos B3 passa a ser por `typeFund`.
- **APIs**: `GetListFunds`/`GetListClassFund` (múltiplos `typeFund`), `fii_proventos.php` (Fundamentus), `ListarTitulosNoticias`/`Detail` (B3) e `frmExibirArquivoIPEExterno.aspx/ExibirPDF` (CVM).
- **Compatibilidade**: sem quebra; tickers não-FIAGRO/BDR mantêm o comportamento atual.
