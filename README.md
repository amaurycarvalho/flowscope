# FlowScope

FlowScope é uma ferramenta open source de análise quantitativa de fluxo de ordens baseada nos dados públicos consolidados de negociações (pregões) disponibilizados pela bolsa de valores B3.

[![Spec-Driven Development](https://img.shields.io/badge/SDD-OpenSpec-yellow)](openspec/specs/project-constitution/spec.md)

## Descrição

A principal diretriz do FlowScope é explicar o mercado, não apenas exibir [indicadores](indicators.md). Cada painel busca responder a uma única pergunta em linguagem simples, com um gráfico limpo, uma classificação qualitativa e um breve resumo textual. O foco da interface é traduzir, via [painéis](panels.md) simples, os [indicadores](indicators.md) envolvidos em respostas claras sobre quem dominou o pregão, quanto capital foi necessário para mover o preço, se há sinais de atuação institucional e quão convincente foi o movimento.

Desenvolvido em Python, oferece interface gráfica (GUI) e linha de comando (CLI), com suporte multiplataforma para Linux, Windows e macOS.

---

## ✨ Funcionalidades

- **Análise Geral** — visão comparativa de toda a carteira (watchlist):
  - **VWAP:** distribuição de preços dos ativos frente ao preço médio ponderado pelo volume.
  - **Quadrantes:** classificação por CLV × desvio do VWAP.
  - **Dominância do Pregão:** quem venceu a disputa diária pelo preço.
  - **Rede de Correlação:** grafo da carteira com a correlação assinada (cor da aresta), a cointegração (estilo/espessura) e as comunidades (cor do nó), a partir dos dados já carregados pelos combos de período e amostragem.
  - **Tabela de Fundamentos:** consolida, por ticker, identidade e classificação, cotação, Preço Típico, P/L, P/VP, Dividend Yield, dividendos, *short interest* (Shorts%, Volume de Shorts, Fechamento Shorts em dias e Risco Fechamento), nº de cotas/cotistas, patrimônio e métricas de FFO dos FIIs; com colunas congeladas, ordenável e exportável em CSV.
  - **Notícias:** árvore com as categorias de topo **"Censuras Públicas"**, **"Condições Excepcionais"**, **"Programas de Aquisição de Ações"** e, por último, **"Geral"** (a carga mais pesada fica no fim). A "Geral" traz as notícias **excepcionais** do Plantão B3 do último ano (lidas **dia a dia** com carga incremental por marcadores persistidos, agrupadas em ano → mês → **tipo de notícia**: "Negociação", "Listagem e Registro", "Ofertas e OPA", "Participações", "Reorganização Societária", "Recuperação e Liquidação", "Eventos de Capital", "Governança e Auditoria" e "Esclarecimentos e Oscilações", com "Outros" para títulos não classificados), filtrando apenas eventos fora da curva (suspensões, M&A, recuperações, ofertas/OPA, participações relevantes, entre outros) e descartando rotina (informes, atas, comunicados, boletins diários, distribuições e liberações/subscrições); as demais vêm da RFC-004 com o histórico completo da fonte. A sub-aba abre lendo **somente o cache local** (índice de metadados, HTML, textos e resumos), sem consultar a B3, com a árvore expandida só até o primeiro nível; é o botão "Atualizar" que lista e baixa novos itens em segundo plano, anunciando na barra de status cada categoria, carregando a "Geral" dia a dia (incremental, pulando os dias já baixados) e preservando na árvore o que já foi carregado se a carga for interrompida. Artigos com URL têm o corpo baixado; itens sem URL (censuras, condições e programas) têm o próprio registro como conteúdo. Há pré-visualização textual (para a "Geral", extraída do corpo do artigo, sem a moldura da página), resumo por I.A. e abertura no navegador padrão quando há URL. Quando o corpo da "Geral" é apenas um apontador para um documento — no visualizador da CVM RAD (`rad.cvm.gov.br`, ex.: "Esclarecimentos de questionamentos CVM/B3") ou do FNET (`fnet.bmfbovespa.com.br`, ex.: esclarecimentos e avisos de oferta de FIIs) —, o conteúdo vinculado é baixado sob demanda (na seleção e em "Resumir pendentes"), extraído (PDF via `pypdf`) e substitui o apontador no corpo, sendo cacheado.
- **Análise do Ticker** — aprofundamento do ativo selecionado:
  - **Evolução dos Fundamentos:** small multiples (oito mini-gráficos) com a série histórica do cache do ticker — Cotação, VP/Cota, P/VP, Dividend Yield, Último dividendo, Nº de cotistas, Nº de cotas e Shorts% — com datas em dia/mês/ano (`DD/MM/AA`) e tooltip de data e valor ao passar o mouse sobre cada ponto.
  - **Evolução da Dominância**, **Amplitude de Preço** e **Fluxo Financeiro**.
  - **Lista de Documentos:** árvore dos documentos em cache do ticker (avisos aos acionistas, informes mensais e documentos relevantes), com pré-visualização textual e abertura no aplicativo padrão.
- **Resumo de documentos com I.A. (opcional):** ao selecionar um documento, o FlowScope usa uma LLM para gerar um resumo curto (até 280 caracteres) e um longo (até 1.500 caracteres); os resumos são persistidos em cache e reaproveitados, e a lista de documentos exibe o resumo curto de cada item.
- **Resumo de notícias com I.A. (opcional):** na sub-aba "Notícias", o mesmo serviço de resumo gera resumos curto e longo para cada item, persistidos; "Resumir pendentes" processa o lote em segundo plano tolerando falhas por item.
- **Chat com I.A. (opcional):** a aba de topo **Chat AI**, única e sempre visível, responde perguntas em linguagem natural sobre os dados já carregados, os documentos e as notícias/informações regulatórias em cache e o próprio FlowScope. O contexto cobre a watchlist completa e a LLM infere o ticker referido na pergunta. A resposta usa uma cascata de contexto — conhecimento do FlowScope, tabela de fundamentos e resumos/documentos em cache — e as notícias e informações regulatórias entram como fonte adicional em **duas camadas**: um índice compacto de todos os itens das quatro categorias no primeiro prompt e a leitura do resumo/texto integral sob demanda pelas chaves que a LLM pedir (somadas aos documentos no gate de confirmação, com documento vinculado não baixado sinalizado em vez de apresentar a URL como conteúdo); há confirmação antes de ler o texto integral de muitos documentos, tetos de contexto, histórico multi-turno (teto de 10 mensagens e 8.000 caracteres), botão "Copiar chat" e cancelamento do envio em andamento. O "Enviar" só habilita com a LLM configurada e fundamentos carregados; "Limpar", "Copiar chat" e "Configuração" desabilitam durante o envio e "Limpar"/"Copiar chat" exigem conteúdo na conversa. Sem RAG vetorial (a indexação vetorial é uma evolução separada, a change `llm-chat-rag`).
- **Painel de orientação:** ao lado direito da janela, o quadro de texto orientativo descreve a aba/sub-aba ativa, incluindo as abas **"Chat AI"** e **"Sobre"**; esse mesmo texto compõe o conhecimento do próprio FlowScope usado pela I.A.

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
./flowscope-linux --help                 # exibir ajuda com todos os parâmetros
./flowscope-linux --version              # exibir versão
```

### Recursos de I.A. (opcional)

Os binários publicados na [página de releases](https://github.com/amaurycarvalho/flowscope/releases) já incluem o liteLLM, então os recursos de I.A. funcionam sem instalação adicional.

Ao instalar a partir do código-fonte, os recursos de I.A. exigem o grupo opcional `[llm]`, que instala o liteLLM:

```bash
pip install flowscope[llm]
```

Na sub-aba "Documentos", o botão "I.A." (logo após "Abrir documento") abre o diálogo de configuração do provedor, onde é possível escolher um preset, informar a chave de API, ajustar o RPM e testar a conexão. Na sub-aba "Notícias", o botão "I.A." tem a mesma função. Na aba "Chat AI", o mesmo diálogo é aberto pelo botão "Configuração", sempre visível no cabeçalho. Enquanto o provedor for `none`, nenhuma chamada de rede é realizada.

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
python3 -m flowscope --help              # exibir ajuda com todos os parâmetros
python3 -m flowscope --version           # exibir versão
```

#### A partir do executável gerado pelo Makefile

```bash
dist/flowscope                           # interface gráfica
dist/flowscope --gui                     # interface gráfica
dist/flowscope --create-shortcut         # criar atalho no desktop (Linux)
dist/flowscope --help                    # exibir ajuda com todos os parâmetros
dist/flowscope --version                 # exibir versão
```

---

## Saiba Mais

- [Repositório do projeto](https://github.com/amaurycarvalho/flowscope)
- [Releases com binários pré-compilados](https://github.com/amaurycarvalho/flowscope/releases)
- [Hub de dados públicos na B3](https://www.b3.com.br/pt_br/dados/hub-de-dados-publicos/)
