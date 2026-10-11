"""Listagem de censuras públicas, condições excepcionais e programas da B3."""

import logging
from datetime import date, datetime, timezone

import requests

from flowscope.infrastructure.b3.funds_client.constants import (
    _CENSURAS_URL,
    _CONDICOES_URL,
    _PROGRAMAS_PAGE_SIZE,
    _PROGRAMAS_URL,
    TTL_PAGINA_ESTATICA_DIAS,
)
from flowscope.infrastructure.b3.structured_parser import (
    extrair_censuras,
    extrair_condicoes_excepcionais,
    extrair_programas_aquisicao,
)
from flowscope.infrastructure.http_retry import executar_com_retry

logger = logging.getLogger(__name__)

#: Tentativas da API de programas, que responde 404 de forma intermitente.
_PROGRAMAS_TENTATIVAS = 5

#: Espera (segundos) entre as tentativas da API de programas.
_PROGRAMAS_ESPERA = 0.5

#: Timeout (segundos) das requisições às páginas/endpoints regulatórios.
_TIMEOUT = 30


class FundosRegulatorioMixin:
    """Mixin com listagem de páginas estáticas regulatórias da B3."""

    def listar_censuras(self: "FundosRegulatorioMixin") -> list:
        """Lista as censuras públicas da página da B3, com cache de 7 dias."""
        html = self._html_cacheado(
            "censuras_publicas", _CENSURAS_URL, "página de censuras públicas"
        )
        return extrair_censuras(html)

    def listar_condicoes_excepcionais(self: "FundosRegulatorioMixin") -> list:
        """Lista as condições excepcionais da página da B3, com cache de 7 dias."""
        html = self._html_cacheado(
            "condicoes_excepcionais",
            _CONDICOES_URL,
            "página de condições excepcionais",
        )
        return extrair_condicoes_excepcionais(html)

    def listar_programas_aquisicao(
        self: "FundosRegulatorioMixin",
        reference_date: date | None = None,
    ) -> list:
        """Lista os programas de aquisição de ações em andamento, com cache."""
        data = (reference_date or datetime.now(timezone.utc).date()).isoformat()
        chave = f"programas_aquisicao_{data}"

        def _fetch() -> dict[str, object]:
            return {"programas": self._coletar_programas(data)}

        try:
            payload = self._cache_com_fallback(
                chave, TTL_PAGINA_ESTATICA_DIAS, _fetch
            )
        except requests.RequestException:
            logger.warning(
                "Falha ao listar programas de aquisição da B3", exc_info=True
            )
            return []
        return extrair_programas_aquisicao(
            {"results": payload.get("programas") or []}
        )

    def _coletar_programas(
        self: "FundosRegulatorioMixin", data: str
    ) -> list[dict]:
        """Coleta os programas paginando enquanto a API informar páginas."""
        resultados: list[dict] = []
        pagina = 1
        while True:
            payload = {
                "keyword": "",
                "date": data,
                "language": "pt-br",
                "pageNumber": pagina,
                "pageSize": _PROGRAMAS_PAGE_SIZE,
            }
            dados = self._get_programas_json(payload)
            if not isinstance(dados, dict):
                break
            resultados.extend(
                item
                for item in (dados.get("results") or [])
                if isinstance(item, dict)
            )
            page = dados.get("page")
            total = int((page or {}).get("totalPages", 1) or 1)
            if pagina >= total:
                break
            pagina += 1
        return resultados

    def _get_programas_json(
        self: "FundosRegulatorioMixin", payload: dict[str, object]
    ) -> object:
        """Consulta a API de programas repetindo o 404 intermitente por override."""
        token = self._build_token(payload)
        url = f"{_PROGRAMAS_URL}/{token}"
        logger.info("Consultando %s", url)
        delays = tuple(
            _PROGRAMAS_ESPERA * tentativa
            for tentativa in range(_PROGRAMAS_TENTATIVAS)
        )

        def _fazer() -> requests.Response:
            resposta = self._session.get(url, timeout=_TIMEOUT)
            resposta.raise_for_status()
            return resposta

        with self._serializador.serializar(url):
            resposta = executar_com_retry(
                _fazer,
                metodo="GET",
                transitorios_extra=frozenset({404}),
                delays=delays,
            )
        return resposta.json()

    def _html_cacheado(self: "FundosRegulatorioMixin", key: str, url: str, descricao: str) -> str:
        """Baixa e cacheia o HTML de uma página estática da B3 por 7 dias."""
        def _fazer() -> requests.Response:
            resposta = requests.get(url, timeout=_TIMEOUT)
            resposta.raise_for_status()
            resposta.encoding = resposta.apparent_encoding or "utf-8"
            return resposta

        def _fetch() -> dict[str, object]:
            logger.info("Baixando %s", url)
            resposta = executar_com_retry(_fazer, metodo="GET")
            return {"html": resposta.text}

        try:
            payload = self._cache.get_or_fetch(key, ttl_days=TTL_PAGINA_ESTATICA_DIAS, fetch_fn=_fetch)
        except requests.RequestException as e:
            raise RuntimeError(f"Não foi possível acessar a {descricao}: {e}") from e
        return str(payload.get("html") or "")
