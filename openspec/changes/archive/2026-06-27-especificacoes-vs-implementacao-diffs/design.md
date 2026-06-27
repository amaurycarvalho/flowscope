## Context

Change de auditoria: comparar cada spec em `openspec/specs/` contra o código em `src/flowscope/` e `tests/`. As diferenças identificadas devem ser documentadas para decisão posterior de correção ou atualização das specs.

## Goals / Non-Goals

**Goals:**
- Registrar todas as divergências entre spec e implementação
- Corrigir specs que descrevem comportamento incorreto (ex: POST vs GET)
- Corrigir exemplos numéricos incorretos nas specs
- Corrigir `requirements.txt` e `README.md`

**Non-Goals:**
- Alterar comportamento do código (a implementação é a referência correta)
- Implementar novos testes (apenas registrar ausência)

## Decisions

1. **Spec é a fonte do erro**: Quando spec e implementação divergem e a implementação está funcional, a spec deve ser corrigida para refletir a realidade do código.
2. **README e requirements.txt**: Devem ser corrigidos para alinhar com o código, não o contrário.

## Risks / Trade-offs

- Atualizar specs sem alterar código pode criar expectativas erradas se o código mudar no futuro. Mitigação: manter o changelog e o histórico de alterações.
