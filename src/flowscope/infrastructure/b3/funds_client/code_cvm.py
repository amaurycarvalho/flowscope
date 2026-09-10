"""Resolução do codeCVM de um ticker na B3."""

import logging

import requests

from flowscope.infrastructure.b3.funds_client.constants import (
    _CADASTRO_EMPRESAS_URL,
    TTL_CADASTRO_EMPRESAS_DIAS,
    TTL_CODIGO_CVM_DIAS,
)
from flowscope.infrastructure.b3.funds_client.cvm import (
    _normalizar_code_cvm,
    montar_indice_code_cvm,
)

logger = logging.getLogger(__name__)


class FundosCodeCvmMixin:
    """Mixin com resolução de ticker→codeCVM, com fallback no cadastro."""

    def resolver_code_cvm(self: "FundosCodeCvmMixin", ticker: str) -> str | None:
        """Resolve o ticker para o ``codeCVM`` na B3.

        Consulta a API ``listedCompaniesProxy`` e, quando indisponível, baixa o
        cadastro de empresas listadas como alternativa. Retorna ``None`` para
        tickers sem código CVM, sem lançar exceção. O resultado, inclusive
        ``None``, é cacheado por 30 dias.
        """
        key = f"codecvm_{ticker.strip().upper()}"

        def _fetch() -> dict[str, object]:
            try:
                return {"codeCVM": self._consultar_code_cvm_por_api(ticker)}
            except requests.RequestException as e:
                logger.warning(
                    "API de empresas indisponível para %s, usando cadastro: %s",
                    ticker,
                    e,
                )
                return {"codeCVM": self._consultar_code_cvm_no_cadastro(ticker)}

        try:
            payload = self._cache.get_or_fetch(key, ttl_days=TTL_CODIGO_CVM_DIAS, fetch_fn=_fetch)
        except requests.RequestException:
            logger.warning(
                "Falha ao resolver codeCVM do ticker %s", ticker, exc_info=True
            )
            return None
        return payload.get("codeCVM")

    def _consultar_code_cvm_por_api(self: "FundosCodeCvmMixin", ticker: str) -> str | None:
        """Consulta a API de empresas listadas por ticker."""
        dados = self._get_listed_json(
            "GetListedCompany",
            {
                "language": "pt-br",
                "pageNumber": 1,
                "pageSize": 20,
                "tradingName": ticker.strip().upper(),
            },
        )
        resultados = dados.get("results", []) if isinstance(dados, dict) else []
        for item in resultados:
            if not isinstance(item, dict):
                continue
            codigo = item.get("codeCVM")
            if codigo:
                return _normalizar_code_cvm(str(codigo))
        return None

    def _consultar_code_cvm_no_cadastro(self: "FundosCodeCvmMixin", ticker: str) -> str | None:
        """Busca o codeCVM no cadastro de empresas listadas da B3."""
        indice = self._carregar_indice_code_cvm()
        return indice.get(ticker.strip().upper())

    def _carregar_indice_code_cvm(self: "FundosCodeCvmMixin") -> dict[str, str]:
        """Baixa e cacheia o índice ticker→codeCVM do cadastro de empresas."""
        key = "cadastro_empresas_code_cvm"

        def _fetch() -> dict[str, object]:
            texto = self._baixar_cadastro_empresas()
            return {"indice": montar_indice_code_cvm(texto)}

        payload = self._cache.get_or_fetch(key, ttl_days=TTL_CADASTRO_EMPRESAS_DIAS, fetch_fn=_fetch)
        indice = payload.get("indice")
        return indice if isinstance(indice, dict) else {}

    def _baixar_cadastro_empresas(self: "FundosCodeCvmMixin") -> str:
        """Baixa o CSV do cadastro de empresas listadas da B3."""
        logger.info("Baixando cadastro de empresas via %s", _CADASTRO_EMPRESAS_URL)
        resp = self._requisicao_get(_CADASTRO_EMPRESAS_URL, timeout=60)
        resp.encoding = resp.apparent_encoding or "utf-8"
        return resp.text
