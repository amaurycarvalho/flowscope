## Why

O painel "Amplitude de Preço" atualmente espalha três métricas correlatas — posição no range, amplitude relativa e eficiência — em quatro sub-gráficos empilhados com eixos desalinhados. Isso dificulta a correlação visual entre elas: o usuário precisa "virar a cabeça" entre o timeline (Y=datas) e o Range % Histórico (X=datas), e a eficiência fica isolada num gauge que só mostra o último dia. A fusão num único axes elimina a redundância, alinha os eixos e permite ler as três respostas num golpe de vista por pregão.

## What Changes

- **Unificar** Price Range Timeline, Range % Histórico e Eficiência Diária num único gráfico matplotlib (mesmo axes)
- **Eliminar** o sub-gráfico "Range % Histórico" — substituído pelo tamanho do marcador de fechamento (●)
- **Eliminar** o sub-gráfico "Eficiência Diária" — substituído por uma barra horizontal de fundo por row
- **Manter** o sub-gráfico CLV como gauge compacto abaixo do gráfico principal
- **Atualizar** tooltip para incluir Range % (amplitude relativa) na tooltip
- **Atualizar** nomenclatura: "Price Range Timeline" → "Trajetória no Range", "Range %" → "Amplitude Relativa"
- **Atualizar** texto de orientação no app.py para refletir a nova visualização e o resumo "Onde / Quanto / Se andou com convicção"

## Capabilities

### New Capabilities

Nenhuma — a funcionalidade é a mesma, apenas a visualização é reorganizada.

### Modified Capabilities

Nenhuma — não há mudança de requisitos no nível de spec, apenas de implementação da UI.

## Impact

- **Arquivo principal**: `src/flowscope/presentation/gui/charts/price_range_panel.py` — reescrita dos métodos de plotagem
- **GridSpec**: muda de 4 rows para 2 rows (timeline unificado + CLV)
- **Tooltip**: expandida para incluir Range %
- **Texto de orientação**: `src/flowscope/presentation/gui/app.py` (constantes de help text)
- **Nenhuma mudança** no domínio, estratégias, dados ou API pública
