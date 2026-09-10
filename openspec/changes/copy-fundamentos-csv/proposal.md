## Why

Hoje o botão "Copiar Dados" sempre copia o CSV bruto de negociações (`RptDt;TckrSymb;...`), mesmo quando o usuário está na sub-aba "Fundamentos" da Análise Geral, cuja tabela mostra métricas fundamentalistas. O usuário precisa de um atalho para levar exatamente os dados que está vendo para a área de transferência (planilha, e-mail, etc.).

## What Changes

- Quando a aba principal for "Análise Geral" e a sub-aba selecionada for "Fundamentos", o botão "Copiar Dados" (e `Ctrl+Shift+C`) copia o conteúdo da tabela de Fundamentos (cabeçalho + uma linha por ticker exibido) em vez do CSV bruto de negociações.
- A cópia da tabela reutiliza o mesmo mecanismo de clipboard (`pyxclip` primário, fallback Tkinter) e o mesmo feedback na statusbar do fluxo existente.
- Fora dessa combinação de abas, o fluxo de cópia atual permanece inalterado.

## Capabilities

### New Capabilities

<!-- Nenhuma: a mudança estende um comportamento existente. -->

### Modified Capabilities

- `clipboard-export`: Adiciona a cópia dos dados da sub-aba Fundamentos quando ela está selecionada na Análise Geral, mantendo o CSV bruto nos demais casos.

## Impact

- **Código afetado**: `src/flowscope/presentation/gui/app_csv.py` (ramo de cópia por aba/sub-aba), `src/flowscope/presentation/gui/charts/fundamental_table.py` (expor a montagem do CSV a partir das mesmas linhas da tabela).
- **Comportamento observável**: novo conteúdo copiado apenas na sub-aba Fundamentos; demais abas inalteradas.
- **Dependências**: nenhuma nova; reaproveita `pyxclip`/clipboard do Tkinter já usados.
- **Compatibilidade**: mantém o atalho `Ctrl+Shift+C` e o botão existentes; nenhuma API pública alterada.
