"""Listagem de fundos e resolução de ticker na API de fundos listados."""

import logging

import requests

from flowscope.infrastructure.b3.funds_client.constants import (
    _PAGE_SIZE,
    _PREFIXO_IDENTIDADE,
    TIPOS_FUNDO,
    TTL_FUNDOS_DIAS,
    TTL_IDENTIDADE_DIAS,
    TTL_RESOLUCAO_TICKER_DIAS,
)
from flowscope.infrastructure.b3.funds_client.fundos_helpers import (
    _fund_root,
    _selecionar_fund,
)

logger = logging.getLogger(__name__)


class FundosListagemMixin:
    """Mixin com listagem paginada de fundos e resolução de identidade."""

    def listar_fundos(self: "FundosListagemMixin", type_fund: str = "FII") -> list[dict]:
        """Lista todos os fundos listados do tipo, paginando e cacheando.

        O ``GetListFunds`` é a fonte do ``id`` primário usado por
        ``GetListClassFund``; o resultado é cacheado por 30 dias.
        """
        key = f"fundos_listados_{type_fund}"

        def _fetch() -> dict[str, object]:
            return {"results": self._coletar_fundos(type_fund)}

        try:
            payload = self._cache.get_or_fetch(key, ttl_days=TTL_FUNDOS_DIAS, fetch_fn=_fetch)
        except requests.RequestException:
            logger.warning("Falha ao listar fundos da B3", exc_info=True)
            return []
        resultados = payload.get("results") or []
        fundos = [item for item in resultados if isinstance(item, dict)]
        if not fundos:
            self._cache.invalidate(key)
        return fundos

    def _coletar_fundos(self: "FundosListagemMixin", type_fund: str) -> list[dict]:
        """Coleta todas as páginas do ``GetListFunds``."""
        fundos: list[dict] = []
        page_number = 1
        while True:
            dados = self._get_json(
                "GetListFunds",
                {
                    "language": "pt-br",
                    "typeFund": type_fund,
                    "pageNumber": page_number,
                    "pageSize": _PAGE_SIZE,
                },
            )
            pagina = dados.get("page", {}) if isinstance(dados, dict) else {}
            resultados = dados.get("results") if isinstance(dados, dict) else []
            if isinstance(resultados, list):
                fundos.extend(item for item in resultados if isinstance(item, dict))
            total_pages = int(pagina.get("totalPages", 1) or 1) if pagina else 1
            if page_number >= total_pages:
                break
            page_number += 1
        return fundos

    def listar_candidatos(
        self: "FundosListagemMixin",
        ticker: str,
        type_fund: str | None = None,
    ) -> list[dict]:
        """Lista as classes do fundo do ticker na B3.

        Sem ``type_fund`` explícito, itera os tipos de fundo conhecidos até
        encontrar o registro primário e consulta ``GetListClassFund`` com o
        ``id`` encontrado como ``idFNET``.
        """
        tipo, primario = self._resolver_primario_e_tipo(ticker, type_fund)
        if primario is None:
            return []
        id_primario = str(primario.get("id"))
        chave = self._chave_cache(_PREFIXO_IDENTIDADE, id_primario)

        def _fetch() -> dict[str, object]:
            dados = self._get_json(
                "GetListClassFund",
                {
                    "language": "pt-br",
                    "idFNET": id_primario,
                    "idCEM": _fund_root(ticker),
                    "typeFund": tipo,
                },
            )
            candidatos = dados if isinstance(dados, list) else []
            return {"candidatos": candidatos}

        try:
            payload = self._cache.get_or_fetch(
                chave, ttl_days=TTL_IDENTIDADE_DIAS, fetch_fn=_fetch
            )
        except requests.RequestException as e:
            logger.warning("Falha ao listar candidatos de %s: %s", ticker, e)
            return []
        candidatos = payload.get("candidatos") or []
        if not isinstance(candidatos, list) or not candidatos:
            self._cache.invalidate(chave)
            return []
        return [item for item in candidatos if isinstance(item, dict)]

    def _resolver_primario(self: "FundosListagemMixin", ticker: str, type_fund: str) -> dict | None:
        """Localiza o registro primário do ticker em ``GetListFunds``."""
        alvo = _fund_root(ticker)
        for fundo in self.listar_fundos(type_fund):
            if str(fundo.get("acronym", "")).strip().upper() == alvo:
                return fundo
        return None

    def _resolver_primario_e_tipo(
        self: "FundosListagemMixin",
        ticker: str,
        type_fund: str | None = None,
    ) -> tuple[str | None, dict | None]:
        """Localiza o registro primário iterando os tipos de fundo em ordem.

        Com ``type_fund`` explícito consulta apenas aquele tipo; sem ele,
        percorre ``TIPOS_FUNDO`` e retorna o primeiro tipo cujo ``acronym``
        corresponde à raiz do ticker. Ticker sem correspondência retorna
        ``(None, None)`` sem lançar exceção.
        """
        tipos = (type_fund,) if type_fund else TIPOS_FUNDO
        for tipo in tipos:
            primario = self._resolver_primario(ticker, tipo)
            if primario is not None:
                return tipo, primario
        return None, None

    def tipo_fundo(
        self: "FundosListagemMixin",
        ticker: str,
        type_fund: str | None = None,
    ) -> str | None:
        """Retorna o tipo de fundo do ticker na B3, ou ``None`` sem dados."""
        tipo, primario = self._resolver_primario_e_tipo(ticker, type_fund)
        return tipo if primario is not None else None

    def selecionar_candidato(
        self: "FundosListagemMixin",
        ticker: str,
        type_fund: str | None = None,
    ) -> dict | None:
        """Seleciona o registro de fundo usado nas consultas subsequentes."""
        return _selecionar_fund(self.listar_candidatos(ticker, type_fund))

    def resolver_ticker(
        self: "FundosListagemMixin",
        ticker: str,
        type_fund: str | None = None,
    ) -> str | None:
        """Resolve o ticker para o ``idFNET`` na B3.

        Retorna ``None`` para tickers sem dados na API de fundos, sem lançar
        exceção. O resultado bem-sucedido é cacheado por 30 dias; uma ausência
        não é cacheada, para não congelar falhas transitórias.
        """

        def _fetch() -> dict[str, object]:
            candidato = _selecionar_fund(self.listar_candidatos(ticker, type_fund))
            id_fnet = candidato.get("id") if candidato else None
            return {"idFNET": str(id_fnet) if id_fnet else None}

        key = f"fund_resolution_{ticker.upper()}"
        try:
            payload = self._cache.get_or_fetch(key, ttl_days=TTL_RESOLUCAO_TICKER_DIAS, fetch_fn=_fetch)
        except requests.RequestException:
            logger.warning("Falha ao resolver ticker %s", ticker, exc_info=True)
            return None
        id_fnet = payload.get("idFNET")
        if not id_fnet:
            self._cache.invalidate(key)
            return None
        return str(id_fnet)
