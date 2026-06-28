## Why

A interface atual usa texto em todos os botões, ocupando espaço horizontal excessivo na top bar e na sidebar. Substituir por ícones reconhecíveis torna a UI mais compacta, moderna e alinhada com padrões de ferramentas financeiras. Os índices IBOV/IDIV/IFIX atualmente ficam em uma linha separada dos demais botões, desperdiçando espaço vertical — movê-los para a mesma linha dos botões de ação aproveita melhor o layout.

## What Changes

- **Top bar**: botões "Hoje", "Carregar" e "Copiar Dados" passam a exibir apenas ícone (sem texto), com tooltip mantido
- **Sidebar (TickerList)**: botões "Salvar Tickers", "Carregar Tickers" e "Filtrar" passam a exibir apenas ícone (sem texto)
- **Sidebar (TickerList)**: botões IBOV, IDIV e IFIX movidos para a mesma linha dos botões de ação (ao lado direito), eliminando a segunda fileira de botões
- **Tooltips**: todos os tooltips existentes são preservados; tooltips são adicionados aos botões que atualmente não possuem (Salvar Tickers, Carregar Tickers, Filtrar)

## Capabilities

### New Capabilities

Nenhuma. Esta é uma mudança puramente visual, sem introdução de nova capacidade funcional.

### Modified Capabilities

Nenhuma. Nenhum requisito em nível de spec é alterado: o comportamento e os tooltips permanecem idênticos.

## Impact

- **Arquivos alterados**: `src/flowscope/presentation/gui/app.py` (top bar) e `src/flowscope/presentation/gui/widgets/ticker_list.py` (sidebar buttons)
- **Dependências**: Pillow já é dependência do projeto e será usado para carregar PNGs como `PhotoImage`
- **Ícones**: todos os 6 ícones já existem em `src/flowscope/icons/` — nenhum novo asset necessário
- **Nenhuma quebra de API ou funcionalidade** — mudança puramente cosmética
