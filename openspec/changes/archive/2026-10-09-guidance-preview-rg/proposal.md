## Why

Ao ler um Relatório Gerencial (RG) na sub-aba "Documentos", o usuário vê o resumo e o texto integral, mas o guidance de distribuição já avaliado para aquele RG não aparece — ele só é visível indiretamente na coluna `Informações adicionais` da sub-aba "Fundamentos", que mostra o guidance corrente do FII. Ter o guidance do próprio RG no ponto de leitura evita que o usuário precise cruzar as duas telas.

## What Changes

- A pré-visualização de um RG com guidance passa a exibir o texto do guidance entre o resumo e o separador `---`, com uma linha em branco antes e depois.
- O texto exibido é o guidance do RG específico (entrada do ledger daquele documento), formatado exatamente como na coluna `Informações adicionais` da sub-aba "Fundamentos".
- A formatação do item de guidance (`Guidance R$ …/cota (…, mmm/aa)`) é extraída para uma função compartilhada, reusada pela coluna e pela pré-visualização.
- O caminho do lote de resumos ("Resumir pendentes") também propaga a avaliação de guidance por RG, para que a pré-visualização recomposta ao fim do lote já contenha o guidance.
- O botão "Resumir pendentes" passa a ser habilitado, com a IA ativa, também quando houver Relatórios Gerenciais (documentos da categoria `Relatorio`, próprios de FIIs) já resumidos cuja avaliação de guidance esteja pendente (entrada ausente no ledger ou não marcada como `ia`), mesmo sem nenhum documento sem `long_summary`.
- O lote passa a avaliar o guidance desses RGs pendentes, pulando a geração de resumo dos que já o possuem e reaproveitando resumos e texto em cache.
- A verificação de pendências de guidance consulta o ledger fora da thread do Tk, no mesmo worker que lê o catálogo, preservando a regra de não fazer I/O de cache na thread da interface.
- Quando o RG não possui guidance avaliado (ausência registrada, avaliação indisponível ou documento não avaliado), a pré-visualização permanece como hoje.

## Capabilities

### New Capabilities
<!-- Nenhuma. -->

### Modified Capabilities
- `documentos-ticker-panel`: a composição da pré-visualização de um RG passa a incluir o guidance do RG entre o `long_summary` e a linha `---`; o botão "Resumir pendentes" passa a considerar, com IA ativa, Relatórios Gerenciais (categoria `Relatorio`, própria de FII) já resumidos porém pendentes de avaliação de guidance, e o lote passa a avaliá-los.
- `relatorio-gerencial-guidance`: a avaliação do RG lida na sub-aba "Documentos" passa a ser exposta para exibição na própria pré-visualização, além de alimentar a coluna `Informações adicionais`; o lote passa a avaliar o guidance de RGs já resumidos que estejam pendentes de avaliação.

## Impact

- **Apresentação**: `presentation/gui/charts/document_flow_mixin.py` (composição da pré-visualização, propagação do resultado do worker e verificação de pendências do botão), `presentation/gui/resumos_job.py` e `presentation/gui/app_resumos_actions.py` (propagação no lote), `presentation/gui/charts/document_tree_panel.py` (estado do botão) e `presentation/gui/app_actions.py` (propagação do conjunto de pendentes do worker de catálogo).
- **Aplicação**: `application/fundamental/linhas.py` ganha a função de formatação compartilhada do item de guidance; `application/documentos/document_guidance.py` expõe a verificação de pendência de avaliação de um RG.
- **Sem novas dependências** e sem mudança de formato de cache.
