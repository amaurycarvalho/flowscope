## Context

Ver `proposal.md` — Why. O entrypoint de um container MCP precisa executar atualizações opcionais antes de iniciar o servidor stdio. O código atual e a documentação já têm os pontos de extensão necessários, mas com três atritos:

- sem `--data`, `_data_efetiva` usa `resolver_data_referencia() or date.today()`, o que faz uma atualização de hoje reutilizar a data da última carga;
- `resumir documentos` exige um ticker posicional, forçando o entrypoint a ler a watchlist e chamar o comando uma vez por ticker;
- a saída de `resumir documentos` é agregada, sem desfecho por ticker.

Além disso, `atualizar documentos` já registra o desfecho por ticker como strings (`"atualizado"`, `"nada_novo"`, `"falha"`), enquanto `executar_resumos` captura erros por item e os entrega ao contexto do lote; o `_ContextoHeadless` atual apenas imprime esses erros em `stderr`. O design precisa definir como essa diferença aparece no resultado do lote de resumos.

## Goals / Non-Goals

**Goals:**

- Fazer `atualizar fundamentos`, `atualizar documentos` e `atualizar noticias` usarem a data local de hoje quando `--data` for omitido.
- Permitir `resumir documentos` sem ticker, percorrendo `last_tickers` com uma única montagem do núcleo e uma única checagem de LLM.
- Expor um desfecho por ticker que distinga sucesso, falha e itens não conclusivos, sem abortar o lote na primeira falha.
- Simplificar o entrypoint documentado do container, removendo o laço shell e a dependência de `FLOWSCOPE_REFERENCE_DATE` para o caso padrão.
- Manter `--data`, o ticker explícito e a saída atual de `resumir documentos <ticker>` como overrides previsíveis.

**Non-Goals:**

- Não adicionar flags de atualização ao subcomando `mcp`; o entrypoint do container compõe os comandos existentes antes de `flowscope mcp`.
- Não alterar o formato de cache, a resolução da data de referência usada pela árvore de conhecimento ou o comportamento de `nav`/MCP.
- Não alterar o formato de `atualizar documentos` nem o comportamento de `executar_resumos` para os demais chamadores.
- Não paralelizar as atualizações nem os resumos.
- Não transformar a preparação do container em best-effort: uma falha continua abortando a inicialização.

## Decisions

### 1. Data padrão única para as ações de atualização

`_data_efetiva` passa a devolver `date.today()` quando `--data` não for informado, sem consultar `resolver_data_referencia`. A resolução da data de referência continua existindo para a árvore de navegação e para `nav_data_referencia`, mas não para disparar uma atualização.

Alternativa considerada: manter a data de referência e adicionar uma flag `--hoje`. Rejeitada porque o caso de uso dominante de uma ação de atualização headless é trazer o estado para o presente, e a flag extra só aumentaria o acoplamento do entrypoint.

Consequência aceita: em um dia não útil, `atualizar fundamentos` registra a data de hoje em `last_fundamentals`; a navegação recua para a observação mais recente disponível. Quem precisa de uma data específica usa `--data`.

### 2. Ticker opcional com desfecho e falha por ticker

O parser passa a usar `nargs="?"` para o ticker. `resumir_documentos` aceita `ticker: str | None` e compartilha o núcleo entre os modos:

- **com ticker**: valida contra `last_tickers`, exige LLM e devolve o JSON agregado atual;
- **sem ticker**: valida que `last_tickers` não está vazio, exige LLM uma única vez, normaliza os tickers (`strip().upper()`), remove duplicatas preservando a ordem e processa cada um.

O lote reusa `_pendentes_documentos`, `_PainelHeadless` e `executar_resumos`. Para conseguir distinguir uma falha de um sucesso, o `_ContextoHeadless` passa a acumular os erros recebidos em `erro()` além de publicá-los em `stderr`. A função auxiliar de um ticker devolve `(desfecho, falhou)`:

- sem erros no contexto e sem exceção: `desfecho = _resumo_json(resultado, len(pendentes))`, `falhou = False`;
- com exceção em `_pendentes_documentos`/setup ou com erro registrado pelo contexto: `desfecho = {"erro": {"motivo": "falha_resumo", "detalhe": str(primeiro_erro)}}`, `falhou = True`.

O lote captura a exceção de cada ticker, registra um aviso no log e continua para o próximo. `executar_resumos` mantém o default `continuar_em_erro=False`: uma falha de item interrompe os itens restantes daquele ticker, mas não os demais tickers. Itens não conclusivos de extração (`parcial`, `protegido`, `sem_texto`, `apontador`) continuam contabilizados no desfecho e não configuram falha do ticker por si só.

Sem `last_tickers`, o comando falha com `watchlist_ausente` antes de montar o núcleo. Sem LLM, falha com `llm_nao_configurada` antes de processar qualquer ticker.

Alternativa considerada: chamar `resumir_documentos(ticker)` uma vez por ticker. Rejeitada porque repetiria `montar_nucleo`, a leitura de `config.json` e a checagem de LLM, além de dificultar a captura do erro do contexto.

### 3. Formato de saída retrocompatível, mas não idêntico ao de documentos

Com ticker explícito, o formato atual `{"pendentes", "sem_texto", "nao_conclusivos", "apontadores"}` é preservado. Sem ticker, a saída é:

```json
{
  "resultados": {
    "PETR4": {
      "pendentes": 3,
      "sem_texto": 0,
      "nao_conclusivos": 0,
      "apontadores": 0
    },
    "VALE3": {
      "erro": {
        "motivo": "falha_resumo",
        "detalhe": "..."
      }
    }
  },
  "falha": true
}
```

`falha` é sempre presente. O formato é análogo ao mapa por ticker de `atualizar documentos`, mas não idêntico: lá o valor é um rótulo de desfecho; aqui o sucesso carrega as contagens e a falha carrega o erro. Não foi escolhido reutilizar as strings de `atualizar documentos` porque o resumo precisa expor as contagens e o detalhe da falha para diagnóstico.

Alternativa considerada: manter as contagens também no ticker que falhou, acrescentando `erro` ao objeto. Rejeitada para manter o contrato simples e o valor de falha inequívoco; o próximo lote retoma os pendentes.

### 4. Container usa os comandos existentes, com data opcional

O entrypoint documentado executa `flowscope carregar watchlist`, os `atualizar` e `resumir documentos` sem ticker antes do `exec flowscope mcp`, redirecionando o JSON para `/dev/null`, pois o `stdout` do MCP deve conter apenas JSON-RPC.

`FLOWSCOPE_REFERENCE_DATE` deixa de ser calculada por padrão. Quando definida, o entrypoint acrescenta `--data "$FLOWSCOPE_REFERENCE_DATE"`; quando ausente, omite a flag e deixa a CLI usar `date.today()` no fuso do container. Isso evita o descompasso entre a data do host e a do container e mantém um override explícito para reprodutibilidade.

A etapa `resumir-documentos` deixa de verificar a existência do arquivo de watchlist e de percorrer os tickers em shell: passa a ser uma única chamada a `flowscope resumir documentos`. Se `last_tickers` estiver persistido no volume de configuração, o comando funciona mesmo sem o arquivo montado; se estiver vazio, falha com erro estruturado.

A preparação nativa de `flowscope mcp --watchlist ... --data ...` não muda; sem `--data`, ela continua sem atualizar e usando a data de referência resolvida.

## Risks / Trade-offs

- **Mudança de default pode surpreender agendadores que dependiam da data de referência** → `--data` continua disponível e passa a ser o mecanismo explícito de reprodutibilidade; a documentação de `mcp` registra o novo default.
- **Atualização em dia não útil grava a data de hoje no marcador** → a navegação recua para a observação mais recente; agendadores que não querem isso devem rodar apenas em dias úteis ou passar `--data`.
- **Resumo de toda a watchlist pode demorar, consumir cota da LLM e atrasar o handshake do MCP** → a operação é opt-in no container, o resultado expõe o desfecho por ticker e a documentação deve alertar sobre o tempo de inicialização e sobre `FLOWSCOPE_INIT_UPDATES=all` exigir LLM.
- **Falha de um ticker ainda encerra o container com código 1** → é coerente com a política atual de abortar a inicialização em qualquer falha; o lote apenas garante que os demais tickers sejam tentados antes do encerramento. Uma política best-effort seria uma mudança separada.
- **Erro de LLM/extração pode parecer sucesso se o contexto não for observado** → o `_ContextoHeadless` passa a acumular erros e os testes devem cobrir falha de item e falha de ticker.
- **Vazamento de JSON de atualização no `stdout` do MCP** → o entrypoint redireciona a saída dos comandos de preparação para `/dev/null` e mantém apenas o `exec flowscope mcp` no canal padrão.

## Migration Plan

Não há migração de dados. O comportamento antigo é recuperável passando `--data` explicitamente ou definindo `FLOWSCOPE_REFERENCE_DATE`. A documentação do entrypoint passa a tratar a variável como opcional e remove o laço de resumo por ticker. Reverter a change restaura a resolução pela data de referência e o ticker obrigatório.

## Open Questions

Nenhuma.
