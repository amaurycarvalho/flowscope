## 1. Domínio: tendência

- [ ] 1.1 Trocar os valores de `TendenciaDividendo` para `CRESCIMENTO`/`REDUCAO`/`NEUTRO`/`N_A` e verificar com teste unitário do enum
- [ ] 1.2 Remover a banda de `calcular_tendencia` e implementar a comparação estrita, verificando os três cenários (maior, menor, igual) em testes unitários
- [ ] 1.3 Ajustar `calcular_ultimo_dividendo` e `_rotulo_dividendo` para os novos rótulos e verificar a renderização na tabela

## 2. Consolidação de fontes

- [ ] 2.1 Definir a porta/estrutura de histórico consolidado com origem por dividendo e verificar com teste de contrato da porta
- [ ] 2.2 Consolidar B3 → CVM → Fundamentus com deduplicação por data-base/valor e verificar com teste que cobre fonte ausente em B3
- [ ] 2.3 Usar `Dividendo/cota` do Fundamentus como fallback quando não houver histórico e verificar com teste do caso sem B3/CVM

## 3. Verificação integrada

- [ ] 3.1 Rodar a suíte afetada (`pytest tests/test_presentation/test_fundamental_table.py` e testes de `domain/fii`) e verificar que passa
- [ ] 3.2 Rodar `openspec validate fundamental-dividend-consolidation --strict` e verificar que não há erros
