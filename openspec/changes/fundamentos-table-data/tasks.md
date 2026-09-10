## 1. Fundamentus: campos de classificação

- [ ] 1.1 Adicionar `discriminador`, `especie`, `setor`, `subsetor`, `segmento` e `gestao` a `AtivoFundamental` e verificar com teste unitário do dataclass
- [ ] 1.2 Extrair no parser o discriminador (`Papel`/`FII`) e os rótulos `Tipo`, `Setor`, `Subsetor`, `Segmento`, `Gestão` e verificar com testes de contrato sobre fixtures atualizadas
- [ ] 1.3 Atualizar as fixtures do Fundamentus (ação e FII) com os novos rótulos e `Qtd imóveis`, e verificar que `test_parse_acao`/`test_parse_fii` passam
- [ ] 1.4 Ajustar `_detectar_tipo` para usar o rótulo do campo de ticker (`Papel`/`FII`) e verificar com cenário de ação e de FII

## 2. Classificação de exibição e fallback

- [ ] 2.1 Implementar função pura que compõe `Tipo` e `Sub-tipo` a partir dos campos do Fundamentus (`Tipo; Setor; Subsetor` e `Tijolo:/Papel: Segmento; Gestão`) e verificar com testes unitários
- [ ] 2.2 Aplicar o fallback `classificar_ticker` quando os campos do Fundamentus estiverem ausentes e verificar com teste de ticker sem dados
- [ ] 2.3 Expor a classificação composta em `AnaliseFundamental` e verificar que `montar_linhas` usa o novo valor

## 3. Novas colunas e preenchimento

- [ ] 3.1 Expor número de cotistas, patrimônio, classes e data de referência em `AnaliseFundamental` e verificar com teste do caso de uso
- [ ] 3.2 Mapear `Patrim Líquido`/`Nro. Cotas` do Fundamentus como fonte primária de patrimônio, com CVM como fallback, e verificar com teste do provider composto
- [ ] 3.3 Adicionar as cinco novas colunas em `_COLUNAS` e a formatação correspondente em `montar_linhas`/`montar_csv`, verificando o cabeçalho e uma linha de exemplo
- [ ] 3.4 Remover o gate `elegivel_ffo` do preenchimento das métricas e verificar que ativos antes não elegíveis exibem FFO/DY/P/VP quando a fonte fornece o dado

## 4. Verificação integrada

- [ ] 4.1 Rodar a suíte de testes afetada (`pytest tests/test_presentation/test_fundamental_table.py tests/test_infrastructure/test_fundamentus_provider.py`) e verificar que passa
- [ ] 4.2 Rodar `openspec validate fundamentos-table-data --strict` e verificar que não há erros
