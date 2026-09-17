## 1. Dependência e preparação

- [ ] 1.1 Adicionar `pypdf>=4` a `pyproject.toml` e `requirements.txt` e verificar que a instalação e o import de `pypdf` funcionam no ambiente
- [ ] 1.2 Confirmar por teste/inspeção que o cache B3 é indexado por `typeFund` e que `GetStructuredReports` usa o `idFNET` da classe

## 2. Resolução B3 multi-tipo (b3-fii-extraction)

- [ ] 2.1 Definir a coleção de tipos de fundo (`FII`, `FIAGRO`, `FIP`, `FIDC`) em constantes do cliente B3 e verificar que não há literais duplicados nos métodos de aquisição
- [ ] 2.2 Alterar a resolução primária para iterar os tipos até encontrar o `acronym`, reutilizando o cache por tipo, e verificar com teste que `BBGO11`/`KNCA11` resolvem via `FIAGRO`
- [ ] 2.3 Garantir que tickers sem correspondência em nenhum tipo retornam ausência sem exceção e verificar com teste para um ticker inexistente
- [ ] 2.4 Verificar que `resolver_identidade` obtém CNPJ de 14 dígitos a partir do `tradingName` da classe FIAGRO, com teste

## 3. Classificação FIAGRO (fii-classification)

- [ ] 3.1 Estender a classificação determinística de sufixo `11` para reconhecer FIAGRO via resolução B3 e retornar `FII` + `SubTipoFii.FIAGRO`, e verificar com teste para `BBGO11`/`KNCA11`
- [ ] 3.2 Garantir que FIAGRO não é elegível ao FFO e verificar com teste de elegibilidade
- [ ] 3.3 Garantir que ticker `11` não reconhecido permanece `DESCONHECIDO`, com teste

## 4. Proventos de FII no Fundamentus (fundamentus-fundamental-provider)

- [ ] 4.1 Adicionar a URL de rendimentos de FII ao cliente Fundamentus e verificar com teste de URL/parâmetros
- [ ] 4.2 Implementar o parser da tabela de FII (`Última Data Com`/`Tipo`/`Data de Pagamento`/`Valor`, tipo `Rendimento`) e verificar com fixture HTML que data-base e valor são extraídos
- [ ] 4.3 Fazer o provider de histórico tentar `proventos.php` e, se vazio, `fii_proventos.php`, e verificar com teste que o fallback é acionado
- [ ] 4.4 Verificar com teste que o P/L derivado de um FII/FIAGRO sem `Dividendo/cota` passa a ser calculado a partir do histórico

## 5. Módulo BDR — listagem e cache (bdr-dividend-fallback)

- [ ] 5.1 Criar o módulo `infrastructure/b3/bdr/` com o listador de avisos mês a mês (12 meses) e verificar com fixture JSON que apenas `({RAIZ})` + `Aviso aos Acionistas` são retornados
- [ ] 5.2 Implementar a resolução do documento na página `Detail` e verificar com fixture HTML que a URL do documento é extraída
- [ ] 5.3 Implementar o download do PDF via POST `ExibirPDF` (base64 → `%PDF`) e verificar com mock que conteúdo não-PDF é rejeitado
- [ ] 5.4 Implementar o cache `<cache>/bdr/<TICKER>/<AAAA>/<MM>/<id>.pdf` sem TTL e verificar com teste que a segunda leitura não baixa novamente
- [ ] 5.5 Tratar falha de rede por aviso e janela sem avisos, e verificar com teste que a lista é vazia sem exceção

## 6. Módulo BDR — extração de texto e dividendos

- [ ] 6.1 Implementar a extração de texto com `pypdf` e verificar com PDF fixture que o texto contém valor e data-com
- [ ] 6.2 Implementar o parser de dividendos (valor por BDR, data-com, data de pagamento, tipo, ISIN, depositário, empresa) e verificar com o texto de exemplo que `0,455484428` e `10/02/2026` são extraídos
- [ ] 6.3 Ignorar avisos sem valor/data-com extraíveis e verificar com teste
- [ ] 6.4 Implementar o provider de dividendos de BDR como fonte secundária (`DividendHistoryProvider`) e verificar com teste de integração que data-com, último/anterior e tendência são preenchidos

## 7. Métricas e apresentação

- [ ] 7.1 Implementar P/L e Dividend Yield de BDR com anualização trimestral (×4) e verificar com teste os cenários de cálculo e de insumo ausente/zero
- [ ] 7.2 Estender `AnaliseFundamental` com `bdr_cache_path`, `nome_depositario`, `nome_empresa_bdr` e `isin` e verificar que os campos são preenchidos apenas para BDR
- [ ] 7.3 Expor o caminho de cache em `Informações adicionais` e depositário/empresa/ISIN em `Dados fiscais` para BDR, e verificar com testes de linha da tabela
- [ ] 7.4 Garantir que ativos não-BDR não acionam a fonte de BDR e verificar com teste de composição

## 8. Integração e regressão

- [ ] 8.1 Integrar a fonte de BDR na composição de dividendos do caso de uso e verificar com teste que a origem é preservada
- [ ] 8.2 Verificar com teste de integração que `BBGO11`, `KNCA11` e `EXXO34` produzem linhas com os campos-alvo preenchidos (sem depender de rede real)
- [ ] 8.3 Adicionar fixtures de contrato (HTML `fii_proventos.php`, JSON `ListarTitulosNoticias`/`Detail`, PDF base64) e verificar que os testes de contrato falham se um rótulo/coluna for removido

## 9. Quality Gate

- [ ] 9.1 Executar `make lint` e corrigir avisos/erros introduzidos
- [ ] 9.2 Executar `make test` e garantir que todos os testes passam
- [ ] 9.3 Executar `openspec validate fix-fundamentos-fiagro-bdr` e garantir que a change permanece válida
