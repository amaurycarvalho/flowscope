"""Resolução API-only do codeCVM e do nome de negociação de um ticker na B3."""

import logging

import requests

from flowscope.infrastructure.b3.funds_client.constants import TTL_CODIGO_CVM_DIAS
from flowscope.infrastructure.b3.funds_client.cvm import _normalizar_code_cvm

logger = logging.getLogger(__name__)

#: Tamanho de página usado na consulta de empresas listadas (máximo aceito).
_PAGE_SIZE_EMPRESAS = 120


def _raiz_ticker(ticker: str) -> str:
    """Remove o sufixo numérico do ticker, devolvendo a raiz de negociação."""
    raiz = ticker.strip().upper().rstrip("0123456789")
    return raiz or ticker.strip().upper()


def _registro_da_raiz(dados: object, raiz: str) -> dict | None:
    """Retorna o registro cujo ``issuingCompany`` é a raiz do ticker."""
    if not isinstance(dados, dict):
        return None
    for item in dados.get("results", []):
        if not isinstance(item, dict):
            continue
        emissor = str(item.get("issuingCompany") or "").strip().upper()
        if emissor == raiz:
            return item
    return None


def _nome_do_registro(item: dict) -> str | None:
    """Extrai o nome de exibição do registro, preferindo ``tradingName``."""
    for chave in ("tradingName", "companyName"):
        valor = item.get(chave)
        if valor is not None and str(valor).strip():
            return str(valor).strip()
    return None


def _total_paginas(dados: object) -> int:
    """Retorna o número de páginas da resposta, com no mínimo 1."""
    pagina = dados.get("page", {}) if isinstance(dados, dict) else {}
    return int(pagina.get("totalPages", 1) or 1) if pagina else 1


class FundosCodeCvmMixin:
    """Mixin com resolução de ticker→codeCVM e nome, exclusivamente via API."""

    def resolver_code_cvm(self: "FundosCodeCvmMixin", ticker: str) -> str | None:
        """Resolve o ticker para o ``codeCVM`` na B3, exclusivamente via API.

        Consulta ``GetInitialCompanies`` pela raiz do ticker e retorna ``None``
        para tickers sem código CVM. Uma falha de resolução (rede/HTTP após as
        retentativas) retorna ``None`` sem cachear o resultado, de modo que uma
        nova tentativa futura volte a consultar a API.
        """
        return self._identidade_empresa(ticker).get("codeCVM")

    def obter_nome_negociacao(
        self: "FundosCodeCvmMixin", ticker: str
    ) -> str | None:
        """Retorna o nome de exibição da empresa listada, ou ``None``.

        Reaproveita a mesma consulta ``GetInitialCompanies`` (e o mesmo cache)
        usada pela resolução de codeCVM, sem nova fonte de dados.
        """
        return self._identidade_empresa(ticker).get("nome")

    def _identidade_empresa(
        self: "FundosCodeCvmMixin", ticker: str
    ) -> dict[str, object]:
        """Obtém ``{"codeCVM", "nome"}`` da API, cacheando por 30 dias.

        O resultado só é gravado no cache quando a API respondeu (com ou sem
        correspondência). Uma falha de rede/HTTP NÃO é cacheada: a exceção é
        propagada por ``get_or_fetch`` sem gravar nada e tratada aqui.
        """
        key = self._chave_cache("codecvm", ticker.strip().upper())

        def _fetch() -> dict[str, object]:
            return self._consultar_empresa_por_api(ticker)

        try:
            payload = self._cache.get_or_fetch(
                key, ttl_days=TTL_CODIGO_CVM_DIAS, fetch_fn=_fetch
            )
        except requests.RequestException:
            logger.warning(
                "Falha ao resolver identidade do ticker %s", ticker, exc_info=True
            )
            return {"codeCVM": None, "nome": None}
        return {
            "codeCVM": payload.get("codeCVM"),
            "nome": payload.get("nome"),
        }

    def _consultar_empresa_por_api(
        self: "FundosCodeCvmMixin", ticker: str
    ) -> dict[str, object]:
        """Consulta a API de empresas listadas pela raiz de negociação do ticker.

        Usa ``GetInitialCompanies`` filtrando por ``company`` e casa o registro
        cujo ``issuingCompany`` é a raiz do ticker, já que o filtro textual pode
        trazer outras empresas cujo nome contém a raiz.
        """
        raiz = _raiz_ticker(ticker)
        page_number = 1
        while True:
            dados = self._consultar_empresas(raiz, page_number)
            item = _registro_da_raiz(dados, raiz)
            if item is not None:
                codigo = item.get("codeCVM")
                return {
                    "codeCVM": _normalizar_code_cvm(str(codigo)) if codigo else None,
                    "nome": _nome_do_registro(item),
                }
            if page_number >= _total_paginas(dados):
                return {"codeCVM": None, "nome": None}
            page_number += 1

    def _consultar_empresas(
        self: "FundosCodeCvmMixin", raiz: str, page_number: int
    ) -> object:
        """Consulta uma página de empresas listadas filtradas pela raiz."""
        return self._get_listed_json(
            "GetInitialCompanies",
            {
                "language": "pt-br",
                "pageNumber": page_number,
                "pageSize": _PAGE_SIZE_EMPRESAS,
                "company": raiz,
            },
        )
