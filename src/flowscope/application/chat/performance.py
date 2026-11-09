"""Ramo ``/performance`` da árvore de conhecimento a partir do snapshot.

O ramo é montado exclusivamente do snapshot estável de performance, sem
recalcular, baixar ou consultar fontes externas. Snapshot ausente ou inválido
omite o ramo; snapshot sem resultados expõe a configuração e uma orientação.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from datetime import date

from flowscope.application.chat.arvore import No, no_folha, no_interno

logger = logging.getLogger("flowscope")

#: Orientação exibida quando o snapshot não possui benchmark ou ticker elegível.
ORIENTACAO_SEM_RESULTADOS = (
    "O snapshot de Performance não possui benchmark ou ticker elegível. "
    "Execute 'flowscope atualizar performance' após carregar a watchlist."
)

#: Aviso de evento societário exibido nas folhas de ticker.
AVISO_EVENTO_SUSPEITO = (
    "Possível evento societário: retorno pode estar distorcido"
)


def carregar_snapshot_performance(
    provider: Callable[[], dict | None] | None,
) -> dict | None:
    """Lê o snapshot de Performance para a árvore, sem ruído por ausência.

    A ausência é registrada em ``DEBUG`` para não repetir ``WARNING`` a cada
    mensagem do chat; apenas falhas de leitura geram ``WARNING``.
    """
    if provider is None:
        return None
    try:
        snapshot = provider()
    except Exception:
        logger.warning(
            "Performance: falha ao ler o snapshot na montagem da árvore",
            exc_info=True,
        )
        return None
    if snapshot is None:
        logger.debug("Performance: snapshot ausente na montagem da árvore")
        return None
    return snapshot


class FontePerformance:
    """Provedor do ramo ``/performance`` a partir do snapshot já carregado."""

    def __init__(
        self: FontePerformance,
        snapshot: Mapping[str, object] | None,
    ) -> None:
        """Guarda o snapshot validado de performance, quando houver."""
        self._snapshot = snapshot

    def construir(self: FontePerformance) -> No | None:
        """Constrói o ramo ``/performance``, ou ``None`` sem snapshot."""
        if not isinstance(self._snapshot, Mapping):
            return None
        raiz = no_interno("/performance", "performance")
        raiz.filho(self._configuracao())
        benchmarks = self._benchmarks()
        if benchmarks.filhos:
            raiz.filho(benchmarks)
        if not benchmarks.filhos:
            raiz.filho(
                no_folha(
                    "/performance/orientacao",
                    "orientacao",
                    conteudo=ORIENTACAO_SEM_RESULTADOS,
                    campos={"orientacao": ORIENTACAO_SEM_RESULTADOS},
                )
            )
        return raiz

    def _configuracao(self: FontePerformance) -> No:
        """Monta a folha ``/performance/configuracao`` com o contexto do cálculo."""
        snapshot = self._snapshot or {}
        ref_date = _texto(snapshot.get("ref_date"))
        periodo = _texto(snapshot.get("period_days"))
        amostragem = _texto(snapshot.get("sampling_method"))
        cached_at = _texto(snapshot.get("cached_at"))
        origem = _texto(snapshot.get("source"))
        bases = _bases(snapshot)
        conteudo = "\n".join(
            (
                f"data_referencia: {ref_date}",
                f"periodo_dias: {periodo}",
                f"amostragem: {amostragem}",
                f"calculado_em: {cached_at}",
                f"origem: {origem}",
                f"benchmarks: {', '.join(_nomes_benchmarks(snapshot)) or '-'}",
                f"bases_retorno: {bases or '-'}",
            )
        )
        return no_folha(
            "/performance/configuracao",
            "configuracao",
            conteudo=conteudo,
            metadado=_resumo_configuracao(ref_date, periodo, amostragem),
            campos={
                "configuracao": conteudo,
                "data": ref_date,
                "periodo": periodo,
                "amostragem": amostragem,
                "benchmarks": ", ".join(_nomes_benchmarks(snapshot)),
            },
        )

    def _benchmarks(self: FontePerformance) -> No:
        """Monta o nó ``/performance/benchmarks`` com um ramo por benchmark."""
        raiz = no_interno("/performance/benchmarks", "benchmarks")
        resultados = (self._snapshot or {}).get("results")
        if not isinstance(resultados, Mapping):
            return raiz
        for benchmark in _nomes_benchmarks(self._snapshot or {}):
            resultado = resultados.get(benchmark)
            if isinstance(resultado, Mapping):
                raiz.filho(self._ramo_benchmark(benchmark, resultado))
        return raiz

    def _ramo_benchmark(
        self: FontePerformance, benchmark: str, resultado: Mapping[str, object]
    ) -> No:
        """Monta o ramo de um benchmark com resumo e folhas por ticker."""
        raiz = no_interno(f"/performance/benchmarks/{benchmark}", benchmark)
        raiz.filho(_resumo(benchmark, resultado))
        tickers = resultado.get("tickers")
        if isinstance(tickers, list):
            for item in tickers:
                if isinstance(item, Mapping) and item.get("ticker"):
                    raiz.filho(_ticker(benchmark, item))
        return raiz


def _resumo(benchmark: str, resultado: Mapping[str, object]) -> No:
    """Monta ``/performance/benchmarks/<benchmark>/resumo``."""
    base = f"/performance/benchmarks/{benchmark}/resumo"
    disponivel = bool(resultado.get("index_available", True))
    base_retorno = _texto(resultado.get("return_basis"))
    tickers = _tickers(resultado)
    nomes = ", ".join(item["ticker"] for item in tickers) or "-"
    conteudo = "\n".join(
        (
            f"benchmark: {benchmark}",
            f"indice_disponivel: {'sim' if disponivel else 'nao'}",
            f"base_retorno: {base_retorno}",
            f"tickers_elegiveis: {len(tickers)}",
            f"tickers: {nomes}",
        )
    )
    return no_folha(
        base,
        "resumo",
        conteudo=conteudo,
        metadado=(
            f"índice {'disponível' if disponivel else 'indisponível'}; "
            f"base {base_retorno}"
        ),
        campos={
            "resumo": conteudo,
            "benchmark": benchmark,
            "indice": "disponivel" if disponivel else "indisponivel",
            "base": base_retorno,
            "tickers": nomes,
        },
    )


def _ticker(benchmark: str, item: Mapping[str, object]) -> No:
    """Monta ``/performance/benchmarks/<benchmark>/tickers/<ticker>``."""
    nome = _texto(item.get("ticker"))
    base = f"/performance/benchmarks/{benchmark}/tickers/{nome}"
    aviso = (
        f"\n{AVISO_EVENTO_SUSPEITO}"
        if bool(item.get("suspicious_event", False))
        else ""
    )
    conteudo = (
        f"ticker: {nome}\n"
        f"benchmark: {benchmark}\n"
        f"retorno_ticker: {_texto(item.get('ticker_return'))}\n"
        f"retorno_indice: {_texto(item.get('index_return'))}\n"
        f"excesso_pp: {_texto(item.get('excess_pp'))}\n"
        f"observacoes: {_texto(item.get('observations'))}"
        f"{aviso}"
    )
    return no_folha(
        base,
        nome,
        conteudo=conteudo,
        campos={
            "ticker": nome,
            "retorno": _texto(item.get("ticker_return")),
            "excesso": _texto(item.get("excess_pp")),
            "observacoes": _texto(item.get("observations")),
        },
    )


def _nomes_benchmarks(snapshot: Mapping[str, object]) -> list[str]:
    """Lista os benchmarks do snapshot, preservando a ordem declarada."""
    declarados = snapshot.get("benchmarks")
    if isinstance(declarados, list):
        nomes = [str(nome) for nome in declarados if isinstance(nome, str)]
        if nomes:
            return nomes
    resultados = snapshot.get("results")
    if isinstance(resultados, Mapping):
        return sorted(str(nome) for nome in resultados)
    return []


def _tickers(resultado: Mapping[str, object]) -> list[Mapping[str, object]]:
    """Lista os itens de ticker válidos do resultado."""
    itens = resultado.get("tickers")
    if not isinstance(itens, list):
        return []
    return [item for item in itens if isinstance(item, Mapping)]


def _bases(snapshot: Mapping[str, object]) -> str:
    """Resume a base de retorno de cada benchmark do snapshot."""
    resultados = snapshot.get("results")
    if not isinstance(resultados, Mapping):
        return ""
    base = []
    for nome in _nomes_benchmarks(snapshot):
        resultado = resultados.get(nome)
        if isinstance(resultado, Mapping):
            base.append(f"{nome}={_texto(resultado.get('return_basis'))}")
    return ", ".join(base)


def _resumo_configuracao(ref_date: str, periodo: str, amostragem: str) -> str:
    """Monta um metadado curto da configuração."""
    partes = [parte for parte in (ref_date, f"{periodo}d", amostragem) if parte]
    return " / ".join(partes)


def _texto(valor: object) -> str:
    """Converta um valor do snapshot em texto estável."""
    if valor is None:
        return ""
    if isinstance(valor, date):
        return valor.isoformat()
    return str(valor)
