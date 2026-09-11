## Why

O texto de orientação da sub-aba "Fundamentos" (`app_tabs.py`) foi escrito antes das últimas evoluções da tabela e não descreve as colunas que passaram a ser exibidas — Preço Típico, P / PT, Dividend Payout, Informações adicionais e Dados fiscais — nem orienta como interpretá-las. O painel de orientação fica desatualizado em relação ao que o usuário vê na tabela.

## What Changes

- Atualizar o campo **Indicadores envolvidos** do conteúdo de orientação da sub-aba "Fundamentos" para descrever todas as colunas exibidas: identidade, cotação (P), Preço Típico e P / PT, VP/Cota, P/VP, P/L, Dividend Yield, datas e valores de dividendo, tendências, Dividend Payout, métricas FFO, cotistas/acionistas, patrimônio e as colunas finais **Informações adicionais** (LPA/ROE/ROIC para Papel; Qtd Imóveis/Cap Rate/Vacância Média e indexadores para FII) e **Dados fiscais** (CNPJ; administrador e gestor para FII).
- Ampliar o campo **Como interpretar** com orientações sucintas sobre a leitura dessas colunas: significado do Preço Típico e do P / PT (desconto/prêmio frente ao preço típico de 52 semanas), do Dividend Payout, dos itens de Informações adicionais e da identidade fiscal.
- Manter o padrão existente de quatro campos na ordem **Objetivo → Responde a pergunta → Indicadores envolvidos → Como interpretar**, com formatação rica (negrito nos cabeçalhos, itálico na pergunta).

## Capabilities

### New Capabilities
<!-- Nenhuma nova capability. -->

### Modified Capabilities
- `gui-interface`: o Requirement "OrientationPanel para a sub-aba Fundamentos" passa a exigir que o texto de orientação descreva as colunas Preço Típico, P / PT, Dividend Payout, Informações adicionais e Dados fiscais e inclua orientações de interpretação para elas.

## Impact

- **Código**: `src/flowscope/presentation/gui/app_tabs.py` (entrada `("Análise Geral", "Fundamentos")` em `TAB_CONTENT`).
- **Testes**: `tests/test_presentation/test_fundamental_table.py` (`TestWiringSubAba`) ganha verificações das novas descrições no corpo de orientação.
- **Docs**: `panels.md` pode ser atualizado para refletir o mesmo conteúdo, se houver seção de Fundamentos.
- **Comportamento observável**: apenas o texto do OrientationPanel muda; a tabela e o CSV permanecem inalterados.
