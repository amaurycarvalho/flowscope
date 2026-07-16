# FlowScope

FlowScope é uma ferramenta open source de análise quantitativa de fluxo de ordens baseada nos dados públicos consolidados de negociações (pregões) disponibilizados pela bolsa de valores B3.

[![Spec-Driven Development](https://img.shields.io/badge/SDD-OpenSpec-yellow)](openspec/specs/project-constitution/spec.md)

## Descrição

A principal diretriz do FlowScope é explicar o mercado, não apenas exibir [indicadores](indicators.md). Cada painel busca responder a uma única pergunta em linguagem simples, com um gráfico limpo, uma classificação qualitativa e um breve resumo textual. O foco da interface é traduzir, via [painéis](panels.md) simples, os [indicadores](indicators.md) envolvidos em respostas claras sobre quem dominou o pregão, quanto capital foi necessário para mover o preço, se há sinais de atuação institucional e quão convincente foi o movimento.

Desenvolvido em Python, oferece interface gráfica (GUI) e linha de comando (CLI), com suporte multiplataforma para Linux, Windows e macOS.

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
