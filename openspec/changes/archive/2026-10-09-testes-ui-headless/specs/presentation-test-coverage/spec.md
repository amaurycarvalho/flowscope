## ADDED Requirements

### Requirement: Costura testável em componentes de apresentação

Componentes de apresentação cuja lógica NÃO depende intrinsecamente de Tk DEVEM expor uma costura que permita verificar essa lógica sem a variável de ambiente `DISPLAY` e sem instanciar `tk.Tk`/`tk.Toplevel`. Em particular: a construção de figura (`Figure`/`Axes`) de painéis de gráfico DEVE ser separável do invólucro Tk (canvas e barra de ferramentas), e decisões que resultam em estado de widget DEVEM ser deriváveis como valor puro antes de serem aplicadas ao widget.

#### Scenario: Painel de gráfico verificado sem Tk

- **WHEN** a lógica de desenho, estado vazio, títulos, eixos ou tooltip de um painel de gráfico é coberta por teste
- **THEN** o teste DEVE operar sobre uma `Figure`/`Axes` sem instanciar `tk.Tk` nem o canvas Tk

#### Scenario: Decisão de habilitação verificada sem Tk

- **WHEN** o estado habilitado/desabilitado de um controle de painel (por exemplo, resumir, abrir documento ou bloco de configuração) é coberto por teste
- **THEN** a decisão DEVE ser observável como valor puro, sem exigir `DISPLAY`

#### Scenario: UI restrita ao invólucro

- **WHEN** um teste exige interface gráfica
- **THEN** ele DEVE verificar apenas o invólucro Tk — layout/geometria, eventos de ponteiro, `Treeview`/notebooks reais, campo somente-leitura, overlay/modal — ou o binding fio-a-fio do estado decidido ao widget
