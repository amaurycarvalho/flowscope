## 1. Cache tolerante à publicação da B3

- [x] 1.1 Em `B3ShortInterestSource._mapa`, não persistir mapa vazio e tratar cache vazio como *miss* (reconsulta do dia)
- [x] 1.2 Adicionar `_bust_stale_empty_cache` e chamá-lo no construtor para descartar caches vazios legados
- [x] 1.3 Cobrir com testes de infraestrutura: mapa vazio não é cacheado, cache vazio é reconsultado e o bust preserva caches com dados
- [x] 1.4 Validar o change e rodar os testes de infraestrutura e de análise fundamentalista
