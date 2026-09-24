"""Mapeamento dos dados já carregados para o painel de rede de correlação.

Extrai, a partir de ``_current_data`` e da seleção do Listbox, as séries
``(data, last_price)`` de cada ticker e reúne os rótulos e formatações
exibidos no painel. Preços ausentes ou não positivos são descartados e os
tickers sem nenhuma observação utilizável são reportados à parte.
"""

from dataclasses import dataclass
from datetime import date
from math import isfinite

from flowscope.domain.network_analysis import (
    MIN_OBS_COINT,
    MIN_OBS_CORR,
    NetworkResult,
    SamplingDiagnostics,
)

#: Texto exibido quando não há tickers suficientes com dados.
MENSAGEM_SEM_TICKERS = "Selecione ao menos dois tickers com dados carregados"

#: Texto exibido quando a densidade alinhada é insuficiente para correlação.
MENSAGEM_POUCAS_OBS = (
    "Poucas observações alinhadas. A rede requer ao menos "
    f"{MIN_OBS_CORR} observações; use um período maior ou a amostragem "
    "\"Todos os dias\""
)

#: Aviso de que a cointegração exige mais observações que a correlação.
AVISO_COINT_INDISPONIVEL = (
    "Cointegração requer no mínimo "
    f"{MIN_OBS_COINT} observações alinhadas"
)


@dataclass(frozen=True)
class DadosRede:
    """Séries utilizáveis e tickers descartados do painel de rede."""

    series: dict[str, tuple[tuple[date, float], ...]]
    sem_dados: tuple[str, ...]


def _preco_valido(valor: object) -> float | None:
    """Valida o preço como float, rejeitando ausentes e não positivos."""
    try:
        preco = float(valor)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if preco > 0 and isfinite(preco):
        return preco
    return None


def _observacoes(info: object) -> list[tuple[date, float]]:
    """Extrai observações ``(data, preço)`` válidas de um ticker."""
    if not isinstance(info, dict):
        return []
    por_data: dict[date, float] = {}
    for dia in info.get("daily_data", []) or []:
        if not isinstance(dia, dict):
            continue
        data = dia.get("date")
        preco = _preco_valido(dia.get("last_price"))
        if isinstance(data, date) and preco is not None:
            por_data[data] = preco
    return sorted(por_data.items())


def extrair_series(
    current_data: dict, tickers: list[str] | None = None
) -> DadosRede:
    """Monta as séries da rede a partir dos dados já carregados.

    Restringe-se aos ``tickers`` informados (ou a todas as chaves de
    ``current_data``). Tickers sem observação válida entram em ``sem_dados``.
    """
    selecionados = list(tickers) if tickers is not None else list(current_data)
    series: dict[str, tuple[tuple[date, float], ...]] = {}
    sem_dados: list[str] = []
    for ticker in selecionados:
        observacoes = _observacoes(current_data.get(ticker))
        if observacoes:
            series[ticker] = tuple(observacoes)
        else:
            sem_dados.append(ticker)
    return DadosRede(series, tuple(sem_dados))


def formatar_correlacao(valor: float) -> str:
    """Formata uma correlação com sinal e duas casas decimais."""
    return f"{valor:+.2f}".replace(".", ",")


def formatar_half_life(
    half_life_obs: float | None, half_life_days: float | None
) -> str:
    """Formata a meia-vida do spread em observações e dias úteis."""
    if half_life_obs is None:
        return "sem reversão"
    texto = f"{half_life_obs:.1f} obs".replace(".", ",")
    if half_life_days is not None:
        texto += f" (~{half_life_days:.1f} dias úteis)".replace(".", ",")
    return texto


def formatar_modularidade(valor: float) -> str:
    """Formata a modularidade da partição de comunidades."""
    return f"modularidade {valor:.2f}".replace(".", ",")


def rotulo_diagnostico(diagnostics: SamplingDiagnostics) -> str:
    """Descreve n de observações, span e gaps da amostragem alinhada."""
    if diagnostics.n_observations == 0:
        return "Sem observações alinhadas"
    mediana = f"{diagnostics.gap_median:.1f}".replace(".", ",")
    return (
        f"{diagnostics.n_observations} observações · "
        f"{diagnostics.span_days} dias corridos · "
        f"gaps {diagnostics.gap_min}/{mediana}/{diagnostics.gap_max} dias úteis"
    )


def mensagem_indisponivel(dados: DadosRede, resultado: NetworkResult) -> str:
    """Mensagem de estado vazio conforme a causa da indisponibilidade."""
    if not resultado.tickers or len(resultado.tickers) < 2:
        if not dados.series and dados.sem_dados:
            return "Sem dados carregados para os tickers selecionados"
        return MENSAGEM_SEM_TICKERS
    return MENSAGEM_POUCAS_OBS
