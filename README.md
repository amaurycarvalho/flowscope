# flowscope
Plataforma de análise quantitativa de fluxo de ordens a partir dos dados consolidados de negociações da bolsa, com indicadores como CVD, VWAP e Volume Profile, visualização gráfica, exportação de dados e identificação automática de estratégias de fluxo institucional.

[![Spec-Driven Development](https://img.shields.io/badge/SDD-OpenSpec-yellow)](openspec/specs/project-constitution/spec.md)

## Descrição

FlowScope é uma ferramenta open source de análise quantitativa de fluxo de ordens (Order Flow Analytics) baseada nos dados públicos consolidados de negociações disponibilizados pelas bolsas de valores. A aplicação permite calcular indicadores como Cumulative Volume Delta (CVD), Volume Weighted Average Price (VWAP) e Volume Profile, visualizar gráficos interativos, exportar resultados em CSV e identificar automaticamente padrões de atuação institucional, como Trend Continuation (Institutional Trend Re-entry) e Absorption Reversal. Desenvolvido em Python, oferece interface gráfica (GUI) e linha de comando (CLI), com suporte multiplataforma para Linux, Windows e macOS.

## Instalação

### 1. Manual (código fonte)

```bash
pip install -e .
```

Requisitos:
- Python 3.10+
- matplotlib, Pillow, pyxclip e tkcalendar (veja `pyproject.toml`)

### 2. Via Makefile (build local)

```bash
make install   # cria .venv/ e instala dependências
make build     # gera executável em dist/
```

O executável será gerado em `dist/flowscope` (Linux), `dist/flowscope.exe` (Windows) ou `dist/flowscope` (macOS).

### 3. Binário pré-compilado

Baixe o binário da plataforma desejada na [página de releases](https://github.com/amaurycarvalho/flowscope/releases):

| Plataforma | Arquivo |
|------------|---------|
| Linux | `flowscope-linux` |
| Windows | `flowscope-windows.exe` |
| macOS | `flowscope-macos` |

## Como usar

### A partir do código fonte

```bash
python3 -m flowscope                     # consultar dados
python3 -m flowscope --gui               # interface gráfica
python3 -m flowscope --create-shortcut   # criar atalho no desktop (Linux)
python3 -m flowscope --help              # exibir ajuda com todos os parâmetros
python3 -m flowscope --version           # exibir versão
```

### A partir do executável gerado pelo Makefile

```bash
dist/flowscope                           # consultar dados
dist/flowscope --gui                     # interface gráfica
dist/flowscope --create-shortcut         # criar atalho no desktop (Linux)
dist/flowscope --help                    # exibir ajuda com todos os parâmetros
dist/flowscope --version                 # exibir versão
```

### A partir do binário pré-compilado

```bash
./flowscope-linux                        # consultar data atual
./flowscope-linux --gui                  # interface gráfica
./flowscope-linux --create-shortcut      # criar atalho no desktop (Linux)
./flowscope-linux --help                 # exibir ajuda com todos os parâmetros
./flowscope-linux --version              # exibir versão
```

Substitua `flowscope-linux` pelo nome do arquivo da sua plataforma.



### Testes

#### Manual (via Makefile)

```bash
make test
```

#### CI (pytest)

```bash
pip install pytest
pytest
```

## Saiba mais

- [Repositório do projeto](https://github.com/amaurycarvalho/flowscope)
- [Releases com binários pré-compilados](https://github.com/amaurycarvalho/flowscope/releases)
- [Hub de dados públicos na B3](https://www.b3.com.br/pt_br/dados/hub-de-dados-publicos/)