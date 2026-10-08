"""Composição de fontes fundamentalistas com prioridade por campo.

O Fundamentus é a fonte primária por padrão; B3, CVM e o motor de FFO atuam
como fallback quando a fonte anterior falha ou não fornece um campo. Cada
campo resultante preserva a origem que o forneceu.
"""

import logging
from collections.abc import Sequence
from datetime import date

from flowscope.application.fundamental_ports import (
    CAMPOS_FUNDAMENTAIS,
    CampoFundamental,
    FfoProvider,
    FundamentalDataProvider,
    OrigemDados,
)
from flowscope.domain.fii.analysis import FfoObservacao
from flowscope.domain.fii.errors import TickerNaoEncontrado

logger = logging.getLogger("flowscope")


class CompositeFundamentalProvider:
    """Resolve cada campo pela primeira fonte que o fornecer, em ordem."""

    def __init__(
        self: "CompositeFundamentalProvider",
        providers: Sequence[FundamentalDataProvider],
    ) -> None:
        """Inicializa o composto com as fontes na ordem de prioridade."""
        self._providers = tuple(providers)

    @property
    def providers(
        self: "CompositeFundamentalProvider",
    ) -> tuple[FundamentalDataProvider, ...]:
        """Retorna as fontes na ordem de prioridade configurada."""
        return self._providers

    def obter(
        self: "CompositeFundamentalProvider", ticker: str, reference_date: date
    ) -> dict[str, CampoFundamental]:
        """Compõe os campos consultando as fontes por prioridade."""
        campos, _ = self.obter_com_resultado(ticker, reference_date)
        return campos

    def obter_com_resultado(
        self: "CompositeFundamentalProvider", ticker: str, reference_date: date
    ) -> tuple[dict[str, CampoFundamental], OrigemDados]:
        """Compõe os campos e reporta a origem do primeiro contribuinte."""
        resultado: dict[str, CampoFundamental] = {}
        origem = OrigemDados.REDE
        for provider in self._providers:
            if CAMPOS_FUNDAMENTAIS.issubset(resultado):
                break
            consulta = self._consultar(provider, ticker, reference_date)
            if consulta is None:
                continue
            campos, origem_fonte = consulta
            if campos and not resultado:
                origem = origem_fonte
            for chave, campo in campos.items():
                if chave not in resultado and campo.valor is not None:
                    resultado[chave] = campo
        return resultado, origem

    @staticmethod
    def _consultar(
        provider: FundamentalDataProvider, ticker: str, reference_date: date
    ) -> tuple[dict[str, CampoFundamental], OrigemDados] | None:
        """Consulta uma fonte, tolerando ticker ausente e falhas.

        Retorna ``None`` quando a fonte não contribui: ticker ausente é
        registrado em nível informativo, e falhas de layout/rede em aviso.
        """
        try:
            obter_com_resultado = getattr(provider, "obter_com_resultado", None)
            if callable(obter_com_resultado):
                return obter_com_resultado(ticker, reference_date)
            return provider.obter(ticker, reference_date), OrigemDados.REDE
        except TickerNaoEncontrado:
            logger.info(
                "Ticker sem dados na fonte %s: %s",
                type(provider).__name__,
                ticker,
            )
            return None
        except Exception:  # fonte indisponível: segue para o fallback
            logger.warning(
                "Fonte fundamentalista %s indisponível para %s",
                type(provider).__name__,
                ticker,
                exc_info=True,
            )
            return None


class CompositeFfoProvider:
    """Resolve o FFO pela primeira fonte que o fornecer, em ordem.

    O Fundamentus é a fonte primária; o motor determinístico da CVM entra como
    fallback quando o Fundamentus falha ou não traz o FFO.
    """

    def __init__(
        self: "CompositeFfoProvider",
        providers: Sequence[FfoProvider],
    ) -> None:
        """Inicializa o composto com as fontes na ordem de prioridade."""
        self._providers = tuple(providers)

    @property
    def providers(self: "CompositeFfoProvider") -> tuple[FfoProvider, ...]:
        """Retorna as fontes na ordem de prioridade configurada."""
        return self._providers

    def obter_ffo(
        self: "CompositeFfoProvider", ticker: str, reference_date: date
    ) -> FfoObservacao | None:
        """Retorna o FFO da primeira fonte que o fornecer."""
        for provider in self._providers:
            try:
                ffo = provider.obter_ffo(ticker, reference_date)
            except Exception:  # fonte indisponível: segue para o fallback
                logger.warning(
                    "Fonte de FFO %s indisponível para %s",
                    type(provider).__name__,
                    ticker,
                    exc_info=True,
                )
                continue
            if ffo is not None:
                return ffo
        return None
