## ADDED Requirements

### Requirement: Troca de modelo não recalcula o rótulo

Ao trocar o provedor/modelo ativo no meio da sessão, o sistema NÃO DEVE recalcular nem republicar o percentual da janela de contexto do rótulo de tokens combinando o `prompt_tokens` da completion anterior com a janela do novo modelo. O rótulo DEVE permanecer com o último snapshot publicado até a completion seguinte, cujo numerador e denominador passam a ser ambos do mesmo modelo. A sessão da conversa e a cota de navegação DEVEM ser herdadas na troca, sem reinício.

#### Scenario: Troca ociosa não altera o rótulo

- **WHEN** o modelo ativo é trocado e nenhuma nova completion é executada
- **THEN** o rótulo DEVE permanecer com o valor e o percentual publicados pela última completion

#### Scenario: Próxima completion usa o novo modelo

- **WHEN** uma nova pergunta é enviada após a troca de modelo
- **THEN** o rótulo DEVE ser recalculado com o `prompt_tokens` da nova completion e a janela do novo modelo

#### Scenario: Contexto herdado na troca

- **WHEN** o modelo é trocado no meio da sessão
- **THEN** o histórico da conversa e a cota de navegação acumulada DEVEM permanecer disponíveis para o novo modelo
