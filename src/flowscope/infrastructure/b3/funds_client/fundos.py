"""Listagem de fundos e resolução de ticker na API de fundos listados."""

import logging
from dataclasses import dataclass, field

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
from flowscope.infrastructure.http_retry import ConteudoInvalido

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ListagemFundos:
    """Resultado da listagem de fundos, com indicador de completude."""

    fundos: list[dict] = field(default_factory=list)
    completa: bool = False
    total_records: int = 0


@dataclass(frozen=True)
class ResolucaoCandidato:
    """Candidato selecionado e se a listagem que o originou estava completa."""

    candidato: dict | None
    completa: bool
    tipo_fund: str | None = None


class _ListagemIncompleta(Exception):
    """Sinaliza coleta parcial para não sobrescrever o cache completo."""

    def __init__(self: "_ListagemIncompleta", listagem: ListagemFundos) -> None:
        """Guarda a listagem parcial coletada."""
        super().__init__("listagem de fundos incompleta")
        self.listagem = listagem


class FundosListagemMixin:
    """Mixin com listagem paginada de fundos e resolução de identidade."""

    def listar_fundos(self: "FundosListagemMixin", type_fund: str = "FII") -> list[dict]:
        """Lista os fundos listados do tipo, de forma tolerante a falhas.

        Wrapper de :meth:`obter_listagem` que devolve apenas a lista, vazia em
        falha, preservando o contrato dos chamadores existentes.
        """
        return self.obter_listagem(type_fund).fundos

    def obter_listagem(
        self: "FundosListagemMixin", type_fund: str = "FII"
    ) -> ListagemFundos:
        """Obtém a listagem de fundos do tipo e informa se está completa.

        A listagem só é gravada no cache quando a coleta atinge ``totalRecords``;
        uma coleta parcial preserva a última listagem completa já armazenada.
        """
        key = self._chave_cache("fundos_listados", type_fund)

        def _fetch() -> dict[str, object]:
            listagem = self._coletar_fundos(type_fund)
            if not listagem.completa:
                raise _ListagemIncompleta(listagem)
            return {
                "results": listagem.fundos,
                "total_records": listagem.total_records,
            }

        try:
            payload = self._cache.get_or_fetch(
                key, ttl_days=TTL_FUNDOS_DIAS, fetch_fn=_fetch
            )
        except _ListagemIncompleta as incompleta:
            listagem = incompleta.listagem
            logger.warning(
                "Listagem de fundos %s incompleta: %d de %d registro(s)",
                type_fund,
                len(listagem.fundos),
                listagem.total_records,
            )
            return listagem
        except requests.RequestException:
            logger.warning("Falha ao listar fundos da B3", exc_info=True)
            return ListagemFundos()
        resultados = payload.get("results") or []
        fundos = [item for item in resultados if isinstance(item, dict)]
        total = int(payload.get("total_records") or len(fundos))
        if not fundos:
            self._cache.invalidate(key)
        return ListagemFundos(fundos, True, total)

    def _coletar_fundos(
        self: "FundosListagemMixin", type_fund: str
    ) -> ListagemFundos:
        """Coleta todas as páginas do ``GetListFunds`` com validação de página."""
        fundos: list[dict] = []
        page_number = 1
        total_pages = 1
        total_records: int | None = None
        while page_number <= total_pages:
            dados = self._obter_pagina_fundos(type_fund, page_number)
            if dados is None:
                return ListagemFundos(
                    fundos, False, total_records if total_records is not None else 0
                )
            pagina, resultados = _partes_pagina(dados)
            fundos.extend(resultados)
            total_pages, total_records = _atualizar_contadores(
                pagina, total_pages, total_records
            )
            page_number += 1
        return _listagem_resultado(fundos, total_records)

    def _obter_pagina_fundos(
        self: "FundosListagemMixin", type_fund: str, page_number: int
    ) -> object | None:
        """Obtém e valida uma página da listagem, ou ``None`` se persistir vazia."""
        try:
            return self._get_json(
                "GetListFunds",
                {
                    "language": "pt-br",
                    "typeFund": type_fund,
                    "pageNumber": page_number,
                    "pageSize": _PAGE_SIZE,
                },
                validar=lambda resposta: _pagina_valida(resposta, page_number),
            )
        except ConteudoInvalido:
            logger.warning(
                "Página %d da listagem de %s permaneceu vazia",
                page_number,
                type_fund,
            )
            return None

    def listar_candidatos(
        self: "FundosListagemMixin",
        ticker: str,
        type_fund: str | None = None,
    ) -> list[dict]:
        """Lista as classes do fundo do ticker na B3, de forma tolerante.

        Sem ``type_fund`` explícito, itera os tipos de fundo conhecidos até
        encontrar o registro primário e consulta ``GetListClassFund`` com o
        ``id`` encontrado como ``idFNET``.
        """
        return self._listar_candidatos_com_status(ticker, type_fund)[0]

    def _listar_candidatos_com_status(
        self: "FundosListagemMixin",
        ticker: str,
        type_fund: str | None = None,
    ) -> tuple[list[dict], bool]:
        """Lista as classes do ticker e informa se a consulta foi conclusiva."""
        tipo, primario, completa = self._resolver_primario_e_tipo(ticker, type_fund)
        if primario is None:
            return [], completa
        return self._candidatos_do_primario(ticker, tipo, primario)

    def _candidatos_do_primario(
        self: "FundosListagemMixin",
        ticker: str,
        tipo: str | None,
        primario: dict,
    ) -> tuple[list[dict], bool]:
        """Consulta ``GetListClassFund`` para o registro primário encontrado."""
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
            return [], False
        candidatos = payload.get("candidatos") or []
        if not isinstance(candidatos, list) or not candidatos:
            self._cache.invalidate(chave)
            return [], False
        return [item for item in candidatos if isinstance(item, dict)], True

    def _resolver_primario_e_tipo(
        self: "FundosListagemMixin",
        ticker: str,
        type_fund: str | None = None,
    ) -> tuple[str | None, dict | None, bool]:
        """Localiza o registro primário e informa se a listagem foi completa.

        Com ``type_fund`` explícito consulta apenas aquele tipo; sem ele,
        percorre ``TIPOS_FUNDO`` e retorna o primeiro tipo cujo ``acronym``
        corresponde à raiz do ticker. Ticker sem correspondência retorna
        ``(None, None, completa)`` sem lançar exceção.
        """
        tipos = (type_fund,) if type_fund else TIPOS_FUNDO
        completa = True
        for tipo in tipos:
            listagem = self.obter_listagem(tipo)
            if not listagem.completa:
                completa = False
            primario = _buscar_primario(ticker, listagem.fundos)
            if primario is not None:
                return tipo, primario, listagem.completa
        return None, None, completa

    def tipo_fundo(
        self: "FundosListagemMixin",
        ticker: str,
        type_fund: str | None = None,
    ) -> str | None:
        """Retorna o tipo de fundo do ticker na B3, ou ``None`` sem dados."""
        tipo, primario, _ = self._resolver_primario_e_tipo(ticker, type_fund)
        return tipo if primario is not None else None

    def obter_candidato(
        self: "FundosListagemMixin",
        ticker: str,
        type_fund: str | None = None,
    ) -> ResolucaoCandidato:
        """Seleciona o candidato e propaga se a origem estava completa."""
        tipo, primario, completa = self._resolver_primario_e_tipo(ticker, type_fund)
        if primario is None:
            return ResolucaoCandidato(None, completa, tipo)
        candidatos, classes_completas = self._candidatos_do_primario(
            ticker, tipo, primario
        )
        candidato = _selecionar_fund(candidatos)
        if candidato is None:
            return ResolucaoCandidato(None, False, tipo)
        return ResolucaoCandidato(candidato, classes_completas, tipo)

    def selecionar_candidato(
        self: "FundosListagemMixin",
        ticker: str,
        type_fund: str | None = None,
    ) -> dict | None:
        """Seleciona o registro de fundo usado nas consultas subsequentes."""
        return self.obter_candidato(ticker, type_fund).candidato

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
            candidato = self.obter_candidato(ticker, type_fund).candidato
            id_fnet = candidato.get("id") if candidato else None
            return {"idFNET": str(id_fnet) if id_fnet else None}

        key = self._chave_cache("fund_resolution", ticker.upper())
        try:
            payload = self._cache.get_or_fetch(
                key, ttl_days=TTL_RESOLUCAO_TICKER_DIAS, fetch_fn=_fetch
            )
        except requests.RequestException:
            logger.warning("Falha ao resolver ticker %s", ticker, exc_info=True)
            return None
        id_fnet = payload.get("idFNET")
        if not id_fnet:
            self._cache.invalidate(key)
            return None
        return str(id_fnet)


def _buscar_primario(ticker: str, fundos: list[dict]) -> dict | None:
    """Localiza o registro cujo ``acronym`` corresponde à raiz do ticker."""
    alvo = _fund_root(ticker)
    for fundo in fundos:
        if str(fundo.get("acronym", "")).strip().upper() == alvo:
            return fundo
    return None


def _pagina_valida(dados: object, page_number: int) -> bool:
    """Rejeita página vazia após a primeira, tratando-a como transitória."""
    if not isinstance(dados, dict):
        return False
    resultados = dados.get("results")
    if not isinstance(resultados, list):
        return False
    return page_number <= 1 or bool(resultados)


def _partes_pagina(dados: object) -> tuple[dict, list[dict]]:
    """Separa o bloco ``page`` e os resultados válidos de uma resposta."""
    if not isinstance(dados, dict):
        return {}, []
    pagina = dados.get("page")
    resultados = dados.get("results")
    itens = (
        [item for item in resultados if isinstance(item, dict)]
        if isinstance(resultados, list)
        else []
    )
    return (pagina if isinstance(pagina, dict) else {}), itens


def _atualizar_contadores(
    pagina: dict, total_pages: int, total_records: int | None
) -> tuple[int, int | None]:
    """Atualiza o total de páginas e de registros a partir da página atual."""
    total_paginas = int(pagina.get("totalPages", total_pages) or total_pages or 1)
    if pagina.get("totalRecords") is not None:
        total_records = int(pagina.get("totalRecords") or 0)
    return total_paginas, total_records


def _listagem_resultado(
    fundos: list[dict], total_records: int | None
) -> ListagemFundos:
    """Monta o resultado final e decide se a coleta está completa."""
    total = len(fundos) if total_records is None else total_records
    return ListagemFundos(fundos, len(fundos) == total, total)
