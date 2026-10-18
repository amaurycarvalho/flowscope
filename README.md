# FlowScopeBR

FlowScopeBR é uma plataforma open source de análise de ativos da B3 que reúne a leitura do fluxo de ordens dos pregões, a consolidação de fundamentos de ações e FIIs, o acompanhamento de dividendos, short interest e documentos corporativos, e a curadoria de notícias e informações regulatórias — com recursos opcionais de IA para resumir documentos e conversar sobre os dados.

[![Spec-Driven Development](https://img.shields.io/badge/SDD-OpenSpec-yellow)](openspec/specs/project-constitution/spec.md)

## Descrição

A principal diretriz do FlowScopeBR é explicar o mercado, não apenas exibir [indicadores](docs/misc/indicators.md). Cada painel busca responder a uma única pergunta em linguagem simples, com um gráfico limpo, uma classificação qualitativa e um breve resumo textual. O foco da interface é traduzir, via [painéis](docs/misc/panels.md) simples, os [indicadores](docs/misc/indicators.md) envolvidos em respostas claras sobre quem dominou o pregão, quanto capital foi necessário para mover o preço, se há sinais de atuação institucional e quão convincente foi o movimento.

Desenvolvido em Python, oferece interface gráfica (GUI) e linha de comando (CLI), com suporte multiplataforma para Linux, Windows e macOS.

---

## ✨ Funcionalidades

- **Análise Geral** — visão comparativa de toda a carteira (watchlist):
  - **VWAP:** distribuição de preços dos ativos frente ao preço médio ponderado pelo volume.
  - **Quadrantes:** classificação por CLV × desvio do VWAP.
  - **Dominância do Pregão:** quem venceu a disputa diária pelo preço.
  - **Rede de Correlação:** grafo da carteira com a correlação assinada (cor da aresta), a cointegração (estilo/espessura) e as comunidades (cor do nó), a partir dos dados já carregados pelos combos de período e amostragem.
  - **Tabela de Fundamentos:** consolida, por ticker, identidade e classificação, cotação, Preço Típico, P/L, P/VP, Dividend Yield, dividendos, _short interest_ (Shorts%, Volume de Shorts, Fechamento Shorts em dias e Risco Fechamento), nº de cotas/cotistas, patrimônio e métricas de FFO dos FIIs; com colunas congeladas, ordenável e exportável em CSV.
  - **Notícias:** árvore com as categorias de topo **"Censuras Públicas"**, **"Condições Excepcionais"**, **"Programas de Aquisição de Ações"** e, por último, **"Geral"** (a carga mais pesada fica no fim). A "Geral" traz as notícias **excepcionais** do Plantão B3 do último ano (lidas **dia a dia** com carga incremental por marcadores persistidos, agrupadas em ano → mês → **tipo de notícia**: "Negociação", "Listagem e Registro", "Ofertas e OPA", "Participações", "Reorganização Societária", "Recuperação e Liquidação", "Eventos de Capital", "Governança e Auditoria" e "Esclarecimentos e Oscilações", com "Outros" para títulos não classificados), filtrando apenas eventos fora da curva (suspensões, M&A, recuperações, ofertas/OPA, participações relevantes, entre outros) e descartando rotina (informes, atas, comunicados, boletins diários, distribuições e liberações/subscrições); as demais vêm da RFC-004 com o histórico completo da fonte. A sub-aba abre lendo **somente o cache local** (índice de metadados, HTML, textos e resumos), sem consultar a B3, com a árvore expandida só até o primeiro nível; é o botão "Atualizar" que lista e baixa novos itens em segundo plano, anunciando na barra de status cada categoria, carregando a "Geral" dia a dia (incremental, pulando os dias já baixados) e preservando na árvore o que já foi carregado se a carga for interrompida. Artigos com URL têm o corpo baixado; itens sem URL (censuras, condições e programas) têm o próprio registro como conteúdo. Há pré-visualização textual (para a "Geral", extraída do corpo do artigo, sem a moldura da página), resumo por I.A. e abertura no navegador padrão quando há URL. Quando o corpo da "Geral" é apenas um apontador para um documento — no visualizador da CVM RAD (`rad.cvm.gov.br`, ex.: "Esclarecimentos de questionamentos CVM/B3") ou do FNET (`fnet.bmfbovespa.com.br`, ex.: esclarecimentos e avisos de oferta de FIIs) —, o conteúdo vinculado é baixado sob demanda (na seleção e em "Resumir pendentes"), extraído (PDF via `pypdf`) e substitui o apontador no corpo, sendo cacheado.
- **Análise do Ticker** — aprofundamento do ativo selecionado:
  - **Evolução dos Fundamentos:** small multiples (oito mini-gráficos) com a série histórica do cache do ticker — Cotação, VP/Cota, P/VP, Dividend Yield, Último dividendo, Nº de cotistas, Nº de cotas e Shorts% — com datas em dia/mês/ano (`DD/MM/AA`) e tooltip de data e valor ao passar o mouse sobre cada ponto.
  - **Evolução da Dominância**, **Amplitude de Preço** e **Fluxo Financeiro**.
  - **Lista de Documentos:** árvore do ticker com os ramos **Guidance** (entradas de distribuição dos Relatórios Gerenciais), **Documentos** (avisos aos acionistas, informes mensais e documentos relevantes) e **Direitos e obrigações** (placeholder), com pré-visualização textual e abertura no aplicativo padrão.
- **Resumo de documentos com I.A. (opcional):** ao selecionar um documento, o FlowScopeBR usa uma LLM para gerar um resumo curto (até 280 caracteres) e um longo (até 1.500 caracteres); os resumos são persistidos em cache e reaproveitados, e a lista de documentos exibe o resumo curto de cada item.
- **Resumo de notícias com I.A. (opcional):** na sub-aba "Notícias", o mesmo serviço de resumo gera resumos curto e longo para cada item, persistidos; "Resumir pendentes" processa o lote em segundo plano tolerando falhas por item.
- **Chat com I.A. (opcional):** a aba de topo **Chat AI**, única e sempre visível, responde perguntas em linguagem natural navegando uma **árvore de conhecimento** montada a partir do estado local — conhecimento do próprio FlowScopeBR, fundamentos da watchlist, documentos, guidance, direitos/obrigações (placeholder) e notícias/informações regulatórias em cache. A LLM identifica o ticker referido na pergunta e percorre a árvore por um protocolo JSON determinístico (`listar`, `obter`, `contar`, `existe`, `buscar`, `buscar_semantico` e `resetar_navegacao`), com manifesto estável cacheável (teto de 4.000 tokens), histórico de no máximo 10 mensagens/8.000 caracteres e até 10 ciclos de navegação. A leitura é estritamente do cache local (nunca resume, extrai ou baixa durante a conversa), há confirmação do custo de turnos pesados, seletor de modelo no cabeçalho, contador de tokens na barra de status, botão "Copiar chat" e cancelamento do envio em andamento. O "Enviar" só habilita com a LLM configurada e fundamentos carregados. Sem RAG vetorial (a busca semântica responde `indice_indisponivel`; a indexação vetorial é a evolução separada `llm-chat-rag`).
- **Painel de orientação:** ao lado direito da janela, o quadro de texto orientativo descreve a aba/sub-aba ativa, incluindo as abas **"Chat AI"** e **"Sobre"**; esse mesmo texto compõe o conhecimento do próprio FlowScopeBR usado pela I.A.

---

## 🧑‍💻 Para Usuários

### Como Instalar

Baixe o binário da plataforma desejada na [página de releases](https://github.com/amaurycarvalho/flowscope/releases):

| Plataforma | Arquivo                 |
| ---------- | ----------------------- |
| Linux      | `flowscope-linux`       |
| Windows    | `flowscope-windows.exe` |
| macOS      | `flowscope-macos`       |

### Como Usar

Substitua `flowscope-linux` pelo nome do arquivo da sua plataforma.

```bash
./flowscope-linux                        # interface gráfica
./flowscope-linux --gui                  # interface gráfica
./flowscope-linux --create-shortcut      # criar atalho no desktop (Linux)
./flowscope-linux mcp                    # servidor MCP (stdio)
./flowscope-linux mcp --watchlist carteira.txt --data 2026-10-14   # preparar e servir
./flowscope-linux nav listar /noticias/grupos   # navegar a árvore de conhecimento
./flowscope-linux nav data-referencia    # ler a data de referência resolvida
./flowscope-linux --help                 # exibir ajuda com todos os parâmetros
./flowscope-linux --version              # exibir versão
```

Leituras de dados: `exportar` materializa dados calculados localmente e
`consultar` busca dados remotos da B3 (a saída é JSON em `stdout`; `--saida`
grava em arquivo):

```bash
./flowscope-linux exportar vwap                                            # grava vwap_<AAAA-MM-DD>.csv
./flowscope-linux exportar vwap --tickers carteira.txt --saida relatorio.csv
./flowscope-linux consultar proventos ALZR11 --data-inicio 2026-01-01 --data-fim 2026-07-29
./flowscope-linux consultar fatos PETR4 --categoria 4
./flowscope-linux consultar noticias --palavra PETROBRAS
./flowscope-linux consultar regulacao --saida regulacao.json
```

Ações de atualização headless, para agendamento externo (cron, systemd, CI). A
saída é JSON em `stdout` (`--pretty` formata), o progresso vai para `stderr` e
as escritas ocorrem sob um lock global de ação (`--esperar <s>` aguarda o lock).
As ações `atualizar ...` sem `--data` usam a data de hoje; `--data` tem
precedência:

```bash
./flowscope-linux carregar watchlist carteira.txt
./flowscope-linux atualizar fundamentos          # usa a data de hoje
./flowscope-linux atualizar fundamentos --data 2026-10-14
./flowscope-linux atualizar documentos PETR4
./flowscope-linux atualizar documentos          # itera a watchlist carregada
./flowscope-linux atualizar noticias
./flowscope-linux resumir documentos PETR4
./flowscope-linux resumir documentos            # processa toda a watchlist
./flowscope-linux resumir noticias
```

Toda invocação da CLI é registrada no log da aplicação (comando, argumentos
permitidos, duração e código de saída), omitindo segredos e preservando o
`stdout` de cada comando.

### Servidor MCP

O FlowScopeBR expõe a sua árvore de conhecimento local — fundamentos, documentos,
guidance e notícias em cache — como um servidor **MCP via stdio**, para chats e
modelos externos, sem abrir portas de rede. O servidor é somente-leitura e
opcional: o chat interno não depende dele.

```bash
./flowscope-linux mcp
./flowscope-linux mcp --watchlist carteira.txt --data 2026-10-14
```

O catálogo de tools `nav_*`, os subcomandos `flowscope nav ...`, a configuração
de clientes e o uso do servidor em um container Docker estão em
[Servidor MCP e subcomandos `nav`](docs/misc/mcp.md). No container, a
inicialização pode executar opcionalmente as etapas de atualização antes de
servir (seção 8 daquele documento).

### Recursos de I.A. (opcional)

Os binários publicados na [página de releases](https://github.com/amaurycarvalho/flowscope/releases) já incluem o liteLLM, então os recursos de I.A. funcionam sem instalação adicional.

Ao instalar a partir do código-fonte, os recursos de I.A. exigem o grupo opcional `[llm]`, que instala o liteLLM:

```bash
pip install flowscope[llm]
```

Nas sub-abas "Documentos" e "Notícias", o seletor de modelo na barra de controles expõe o botão "Configuração", que abre o diálogo do provedor, onde é possível escolher um preset, informar a chave de API, ajustar o RPM e testar a conexão. Na aba "Chat AI", o mesmo diálogo é aberto pelo botão de configuração no seletor de modelo do cabeçalho. Enquanto o provedor for `none`, nenhuma chamada de rede é realizada.

---

## 👨‍🔧 Para Desenvolvedores

### Como Instalar

#### Baixando o codigo fonte

```bash
git clone https://github.com/amaurycarvalho/flowscope.git
```

#### Como Compilar

```bash
make install   # cria .venv/ e instala dependências
make build     # gera executável em dist/
```

O executável será gerado em `dist/flowscope` (Linux), `dist/flowscope.exe` (Windows) ou `dist/flowscope` (macOS).

Requisitos:

- Python 3.10+
- matplotlib, Pillow, pyxclip e tkcalendar (veja `pyproject.toml`)

#### Linting e Testes Unitários

```bash
make lint test
```

#### Quality Gate

O _quality gate_ impõe limites para complexidade, duplicação, cobertura, mutação e segurança (RFC-005).

Execute-o localmente com:

```bash
make quality-gate
```

Verificações individuais: `make complexity`, `make duplication`, `make mutation-check`,
`make security`. Saiba mais em [Quality Gate](docs/adrs/ADR-003.md).

### Mutation testing

Garanta que tudo esteja instalado:

```bash
make install-quality-tools
```

Execute-o localmente (isso pode levar muito tempo e exigir processamento significativo):

```bash
make mutation-run
```

Em seguida, gere o relatório de resultados e utilize-o com seu agente de IA para corrigir seus testes unitários:

```bash
make mutation-results
```

Por fim, execute novamente os testes de mutação e verifique se eles passam pelo _quality gate_.

### Como Usar

#### A partir do código fonte

```bash
python3 -m flowscope                     # interface gráfica
python3 -m flowscope --gui               # interface gráfica
python3 -m flowscope --create-shortcut   # criar atalho no desktop (Linux)
python3 -m flowscope mcp                 # servidor MCP (stdio)
python3 -m flowscope nav listar /noticias/grupos   # navegar a árvore de conhecimento
python3 -m flowscope --help              # exibir ajuda com todos os parâmetros
python3 -m flowscope --version           # exibir versão
```

#### A partir do executável gerado pelo Makefile

```bash
dist/flowscope                           # interface gráfica
dist/flowscope --gui                     # interface gráfica
dist/flowscope --create-shortcut         # criar atalho no desktop (Linux)
dist/flowscope mcp                       # servidor MCP (stdio)
dist/flowscope nav listar /noticias/grupos   # navegar a árvore de conhecimento
dist/flowscope --help                    # exibir ajuda com todos os parâmetros
dist/flowscope --version                 # exibir versão
```

---

## Fontes de Dados

O FlowScopeBR consome dados públicos da B3, da CVM e do Fundamentus, além de APIs opcionais de LLM e da consulta de releases no GitHub. Para cada fonte, o documento [Fontes de Dados](docs/misc/datasources.md) detalha as URLs, os parâmetros/payloads, os formatos de entrada e saída, o cache local e as regras de fallback.

---

## Saiba Mais

- [Fontes de dados: URLs, payloads e formatos](docs/misc/datasources.md)
- [Repositório do projeto](https://github.com/amaurycarvalho/flowscope)
- [Releases com binários pré-compilados](https://github.com/amaurycarvalho/flowscope/releases)
- [Servidor MCP e subcomandos `nav`](docs/misc/mcp.md)
- [Hub de dados públicos na B3](https://www.b3.com.br/pt_br/dados/hub-de-dados-publicos/)
