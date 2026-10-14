## 1. Núcleo de navegação

- [ ] 1.1 Extrair `NavegacaoCore` em `src/flowscope/application/navegacao/` com `listar`, `obter`, `contar`, `existe`, `buscar`, `buscar_semantico` e manifesto, centralizando os limites (`50`, `200`, `12000`, timeout de regex, teto de manifesto) vindos de `arvore.py`/`manifesto.py`; verificar com os testes de contrato do núcleo passando
- [ ] 1.2 Adicionar ordenação determinística por caminho nas listagens e verificar com teste que duas chamadas sem mudança de estado devolvem a mesma ordem
- [ ] 1.3 Implementar codificação/decodificação do cursor opaco (base64url de `{v, op, caminho, pos}`), com `nextCursor` apenas quando houver mais e página de 100 em `listar`; verificar com teste de continuação até o fim dos resultados
- [ ] 1.4 Recusar cursors malformados, de versão desconhecida ou de operação/caminho divergentes com `cursor_invalido`; verificar com teste por cada caso
- [ ] 1.5 Recusar segmentos `.` e `..` em `normalizar_caminho`, devolvendo `caminho_invalido`; verificar com teste de traversal
- [ ] 1.6 Garantir que falhas internas viram erro recuperável de erro interno, sem encerrar o núcleo; verificar com teste de exceção inesperada
- [ ] 1.7 Verificar que o núcleo não expõe reset nem lote e que executa operações na ordem submetida; verificar com teste de catálogo e de agregação determinística

## 2. Adaptador do chat

- [ ] 2.1 Converter `ProtocoloNavegacao` em adaptador fino sobre o `NavegacaoCore`, preservando `interpretar`, `serializar`, `[RESULTADO_NAVEGACAO]`, `foco` e o limite de 8 operações por turno; verificar com os testes existentes de `protocolo`/`consultar` passando
- [ ] 2.2 Remover do núcleo o caminho de reset (mantendo `resetar_navegacao` como preocupação do loop do chat em `consultar.py`) e verificar com teste do descarte de navegação/foco
- [ ] 2.3 Verificar que o manifesto e a assinatura de estado permanecem byte-a-byte estáveis e que a ordem ordenada de `listar` não quebra o chat; verificar com os testes de manifesto e de chat

## 3. CLI de navegação

- [ ] 3.1 Adicionar subparsers `nav` (`listar`, `obter`, `contar`, `existe`, `buscar`, `buscar-semantico`, `manifesto`) em `presentation/cli.py`, reusando o `NavegacaoCore`; verificar com teste de parsing e de execução de `flowscope nav listar`
- [ ] 3.2 Implementar as flags `--offset`/`--limite` (`obter`), `--regex`/`--em`/`--max` (`buscar`), `--consulta`/`--max` (`buscar-semantico`) e `--cursor` (listagens); verificar com testes dos argumentos
- [ ] 3.3 Emitir JSON em `stdout` com `--pretty` opcional e erros estruturados em `stdout` com diagnóstico em `stderr`; verificar com teste de saída e de erro recuperável
- [ ] 3.4 Garantir que `--mcp` não colide com o dispatch das flags atuais e que sem subcomando `nav` o comportamento existente permanece; verificar com os testes de `main`/`cli`

## 4. Servidor MCP

- [ ] 4.1 Criar o módulo do servidor MCP em `presentation/` com loop JSON-RPC newline-delimited em `stdin`/`stdout` e encerramento em EOF; verificar com teste de eco de requisição e encerramento limpo
- [ ] 4.2 Implementar `server/discover` (versões suportadas incluindo `2026-07-28`, capacidades e identidade) e negociação por `_meta` com `UnsupportedProtocolVersionError`; verificar com testes de discover, sucesso e versão não suportada
- [ ] 4.3 Implementar `tools/list` com as sete tools `nav_*` em ordem alfabética, `title` e anotações completas; verificar com teste que compara o catálogo e a ordem
- [ ] 4.4 Implementar `tools/call` para as tools `nav_*`, incluindo validação de schemas, `cursor` nas listagens, `nextCursor`, erros recuperáveis sem `isError` e falha interna com `isError`; verificar com testes por tool e por envelope de erro
- [ ] 4.5 Garantir que `stdout` só recebe JSON-RPC e que logs vão para `stderr`, com suporte a `notifications/cancelled`; verificar com teste que captura `stdout` e não encontra linhas não-JSON-RPC
- [ ] 4.6 Adicionar a flag `--mcp` em `main.py`/`cli.py` como ponto de entrada do servidor e verificar a inicialização por teste de integração do parser
- [ ] 4.7 Confirmar que nenhuma dependência nova é introduzida e que o empacotamento segue sem hidden import adicional; verificar build/import conforme o fluxo atual e o `flowscope.spec` inalterado

## 5. Documentação

- [ ] 5.1 Atualizar `README.md` citando `--mcp` e `flowscope nav ...` nas duas seções "Como Usar" e adicionar o link para o guia do servidor MCP em "Saiba Mais"; verificar que os comandos e o link estão presentes e renderizam
- [ ] 5.2 Criar `docs/misc/mcp.md` no padrão dos guias existentes, cobrindo: início por `flowscope --mcp` (stdio), configuração de cliente MCP, catálogo de tools `nav_*` e schemas, paginação por cursor e envelopes de erro, subcomandos `flowscope nav ...`, confinamento de leitura e a fronteira "MCP é opcional; o chat não o usa"; verificar com revisão de conteúdo e links válidos

## 6. Verificação final

- [ ] 6.1 Rodar `make lint` e `make complexity` e corrigir apontamentos relacionados à mudança; verificar execução sem erros
- [ ] 6.2 Rodar os testes relacionados à mudança (núcleo, chat, CLI, MCP) e garantir que passam; verificar execução limpa
- [ ] 6.3 [Manual/usuário] Rodar a suíte completa (`make test`) e o quality gate (`make quality-gate`) quando autorizado, pela amplitude dos contratos compartilhados; verificar aprovação
