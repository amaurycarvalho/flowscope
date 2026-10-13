## Context

Referências a arquivos do projeto aparecem em código (`src/`), testes (`tests/`), scripts (`scripts/`), documentação (`docs/`, `README.md`) e nas instruções de ferramentas/agentes (`.opencode/commands/`, `.opencode/skills/`, `.agents/skills/`). Hoje não há regra normativa que proíba caminhos absolutos específicos da máquina.

Uma varredura por `/home/amaury`, `/Users/` e `C:\` não encontra ocorrências em código, testes ou scripts. As ocorrências de `/home/user/...` estão apenas em specs (ex.: `openspec/specs/ui-polish/spec.md:152`) como exemplo ilustrativo de diretório do usuário, e os `/tmp/...` em testes (`tests/test_presentation/test_copy_chart.py:12`, `tests/test_domain/test_noticias.py:30`) são diretórios temporários, não referências a arquivos do projeto.

Ver `proposal.md` — Why para a motivação. A delta de spec `specs/engineering-standards/spec.md` já define o requirement "Referências de caminho portáveis".

## Goals / Non-Goals

**Goals:**
- Normatizar a portabilidade de referências a arquivos do projeto no `engineering-standards`.
- Auditar e corrigir eventuais violações existentes no código, testes, scripts e documentação.
- Estender a mesma regra às instruções de ferramentas e agentes que acessam arquivos do projeto.

**Non-Goals:**
- Reescrever exemplos ilustrativos em specs que usam diretórios do usuário (`/home/user/dados`) apenas para descrever comportamento.
- Substituir caminhos temporários de teste (`tempfile`, `/tmp`) — não são arquivos do projeto.
- Introduzir uma ferramenta de lint dedicada a caminhos absolutos (avaliado como Open Question).

## Decisions

**D1 — Normatizar via delta do `engineering-standards`.** Adicionar o requirement na spec existente em vez de criar um standard novo. Mantém uma única fonte normativa para gates e convenções de engenharia. Alternativa: novo standard `path-portability` — rejeitada por fragmentar regras transversais.

**D2 — Definir "arquivo do projeto".** Aplica-se a arquivos rastreados no repositório. Caminhos temporários (`tempfile`, `/tmp`) e exemplos ilustrativos de diretórios do usuário ficam fora do escopo. Sem essa delimitação a regra geraria falsos positivos em testes.

**D3 — Forma de resolução permitida.** Caminho relativo à raiz do repositório ou derivado em runtime de `__file__`/configuração (ex.: `Path(__file__).parent`, `importlib.resources`). Alternativa única de caminho absoluto fixo — rejeitada por quebrar portabilidade.

**D4 — Estender a ferramentas/agentes via spec.** A regra para ferramentas e agentes é codificada no próprio `engineering-standards` (spec de definições/standards do projeto), que é normativo e versionado. Alternativa: editar as instruções geradas em `.opencode/` e `.agents/skills/` — rejeitada porque são artefatos gerados pela tooling OpenSpec (`generatedBy: "1.12.0"`) e seriam sobrescritos; alternativa `AGENTS.md` — rejeitada em favor da spec normativa já existente. Sem mecanismo de enforcement próprio.

**D5 — Auditoria por varredura.** Buscar padrões de caminho absoluto (`/home/<user>`, `/Users/`, `C:\`, drive letters) em arquivos rastreados e corrigir as referências a arquivos do projeto que apareçam. Correção por caminho relativo à raiz ou derivação em runtime.

## Risks / Trade-offs

- [Falsos positivos em fixtures e diretórios temporários] → excluir explicitamente `tempfile`/`/tmp` do escopo (D2) e revisar ocorrências caso a caso.
- [Exemplos absolutos em specs existentes] → tratar como ilustrativos, não como arquivos do projeto; documentar a decisão para evitar revisões recorrentes.
- [Ausência de enforcement automatizado] → a regra é normativa e depende de revisão de código; um check de grep poderia ser adicionado depois (Open Question), mas não faz parte desta change.
- [Ambiguidade de "raiz" em subpacotes] → preferir `__file__`/configuração quando o diretório de trabalho não for garantidamente a raiz (ex.: execução empacotada via PyInstaller, que já usa `sys._MEIPASS` em `tests/test_presentation/test_main.py:111`).

## Migration Plan

1. Varredura de padrões absolutos nos arquivos rastreados; para cada referência a arquivo do projeto, converter para caminho relativo à raiz ou derivação em runtime.
2. Sem migração de dados: a change é de convenção e documentação; nenhum dado persistido é afetado.
3. Rollback trivial: reverter as edições textuais.

## Open Questions

- Vale adicionar um check de grep no `make quality-gate` para barrar caminhos absolutos? Pode ser decidido depois sem alterar as specs nem a abordagem; nesta change o enforcement permanece por revisão.
