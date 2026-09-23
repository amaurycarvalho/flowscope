"""Ações alugadas (short interest) a partir das Posições em Aberto da B3.

O *spike* de aquisição (RFC-014) localizou a base oficial de **empréstimo de
ativos (BTC)** no BDI da B3: capítulo "Empréstimos de ativos", tabela
``BTBLendingOpenPosition`` ("Posições em aberto"). A tabela é servida por um
``POST`` JSON em
``/bdi/table/BTBLendingOpenPosition/{data}/{data}/{página}/{take}`` e traz, por
ticker e mercado de negociação, o ``StockBalance`` (saldo em quantidade do
ativo) e uma linha ``Total`` por ticker.

A coleta percorre as páginas (``take`` máximo de 1000), agrega por ticker
preferindo as linhas ``Total`` e usa cache diário com falha tolerada
(``None`` → ``N/A``). Como a B3 publica a posição do pregão anterior, uma data
ainda não publicada (tipicamente a data corrente) recua até a data disponível
mais recente dentro de uma janela de dias, conforme a retenção ``D-21`` da
tabela.
"""

import logging
from collections.abc import Callable
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from flowscope.infrastructure.cache import CacheManager

logger = logging.getLogger("flowscope")

#: Endpoint BDI da tabela de Posições em Aberto de empréstimo de ativos.
URL_BASE = (
    "https://arquivos.b3.com.br/bdi/table/BTBLendingOpenPosition"
)

#: Tamanho de página aceito pelo endpoint (máximo observado no spike).
_TAMANHO_PAGINA = 1000

#: Janela de dias anteriores usada quando a data pedida ainda não foi publicada.
_JANELA_DIAS = 7

#: Versão do formato de cache, usada para invalidar mapas de fontes anteriores.
_CACHE_VERSAO = "btb-v1"

#: Nome da coluna com o ticker e com o saldo em quantidade.
_COLUNA_TICKER = "TckrSymb"
_COLUNA_MERCADO = "Market"
_COLUNA_SALDO = "StockBalance"

#: Rótulo da linha agregada por ticker.
_MERCADO_TOTAL = "total"


def _numero(valor: object) -> Decimal | None:
    """Interpreta um valor numérico (JSON ou texto BR) como ``Decimal``."""
    if valor is None or isinstance(valor, bool):
        return None
    if isinstance(valor, (int, float, Decimal)):
        try:
            return Decimal(str(valor))
        except InvalidOperation:
            return None
    if isinstance(valor, str):
        texto = valor.strip()
        if not texto:
            return None
        if "," in texto:
            texto = texto.replace(".", "").replace(",", ".")
        try:
            return Decimal(texto)
        except InvalidOperation:
            return None
    return None


def _colunas_e_linhas(payload: object) -> tuple[list[str], list[list]]:
    """Extrai os nomes das colunas e as linhas de um payload da tabela BDI."""
    if not isinstance(payload, dict):
        return [], []
    tabela = payload.get("table")
    if not isinstance(tabela, dict):
        return [], []
    colunas = [
        str(coluna.get("name"))
        for coluna in (tabela.get("columns") or [])
        if isinstance(coluna, dict)
    ]
    linhas = [
        linha for linha in (tabela.get("values") or []) if isinstance(linha, list)
    ]
    return colunas, linhas


def _indices_colunas(colunas: list[str]) -> tuple[int, int, int] | None:
    """Localiza os índices das colunas relevantes, ou ``None`` se faltarem."""
    try:
        return (
            colunas.index(_COLUNA_TICKER),
            colunas.index(_COLUNA_MERCADO),
            colunas.index(_COLUNA_SALDO),
        )
    except ValueError:
        return None


def _linha_agregavel(
    linha: list, indices: tuple[int, int, int]
) -> tuple[str, Decimal, bool] | None:
    """Extrai ``(ticker, saldo, é_total)`` de uma linha, ou ``None`` se inválida."""
    i_ticker, i_mercado, i_saldo = indices
    if len(linha) <= max(indices):
        return None
    ticker = str(linha[i_ticker] or "").strip().upper()
    saldo = _numero(linha[i_saldo]) if ticker else None
    if saldo is None:
        return None
    mercado = str(linha[i_mercado] or "").strip().lower()
    return ticker, saldo, mercado == _MERCADO_TOTAL


def agregar_por_ticker(
    colunas: list[str], linhas: list[list]
) -> dict[str, Decimal]:
    """Agrega o saldo em quantidade de ações alugadas por ticker.

    Suma as linhas ``Total`` de cada ticker; para tickers sem linha ``Total``,
    usa a soma das demais linhas. A ausência de ``Total`` não deve ocorrer no
    dado publicado, mas o fallback evita perder o ticker.
    """
    indices = _indices_colunas(colunas)
    if indices is None:
        return {}
    totais: dict[str, Decimal] = {}
    demais: dict[str, Decimal] = {}
    com_total: set[str] = set()
    for linha in linhas:
        item = _linha_agregavel(linha, indices)
        if item is None:
            continue
        ticker, saldo, eh_total = item
        if eh_total:
            totais[ticker] = totais.get(ticker, Decimal(0)) + saldo
            com_total.add(ticker)
        else:
            demais[ticker] = demais.get(ticker, Decimal(0)) + saldo
    for ticker, saldo in demais.items():
        if ticker not in com_total:
            totais[ticker] = saldo
    return totais


def parse_btb_lending(payload: object) -> dict[str, Decimal]:
    """Mapeia ticker para as ações alugadas em um payload da tabela BDI."""
    colunas, linhas = _colunas_e_linhas(payload)
    return agregar_por_ticker(colunas, linhas)


class B3ShortInterestSource:
    """Obtém as ações alugadas de um ticker nas Posições em Aberto da B3."""

    def __init__(
        self: "B3ShortInterestSource",
        cache: CacheManager | None = None,
        fetch: Callable[[str], dict] | None = None,
        url: str = URL_BASE,
        page_size: int = _TAMANHO_PAGINA,
    ) -> None:
        """Inicializa a fonte com cache, função de download e URL configuráveis."""
        self._cache = cache or CacheManager()
        self._fetch = fetch or self._baixar
        self._url = url
        self._page_size = page_size

    def obter_acoes_alugadas(
        self: "B3ShortInterestSource", ticker: str, reference_date: date
    ) -> Decimal | None:
        """Retorna as ações alugadas do ticker, ou ``None`` quando indisponível.

        Recua até a data publicada mais recente dentro da janela quando a data
        pedida ainda não tem posição publicada; para tickers sem posição na data
        publicada, retorna ``None`` (``N/A``).
        """
        normalizado = ticker.strip().upper()
        try:
            for dia in self._dias(reference_date):
                mapa = self._mapa(dia)
                if mapa:
                    return mapa.get(normalizado)
            return None
        except Exception:  # aquisição tolerante por ticker
            logger.warning(
                "Falha ao obter ações alugadas de %s", ticker, exc_info=True
            )
            return None

    @staticmethod
    def _dias(reference_date: date) -> list[date]:
        """Retorna a data pedida e os dias anteriores dentro da janela."""
        return [reference_date - timedelta(days=i) for i in range(_JANELA_DIAS)]

    def _mapa(self: "B3ShortInterestSource", reference_date: date) -> dict[str, Decimal]:
        """Retorna o mapa ticker→ações alugadas do dia, usando cache diário."""
        chave = f"b3_emprestimos_{_CACHE_VERSAO}_{reference_date.isoformat()}"
        cacheado = self._cache.read_meta(chave)
        if cacheado is not None and isinstance(cacheado.get("data"), dict):
            return self._mapa_de_payload(cacheado["data"])
        colunas: list[str] = []
        linhas: list[list] = []
        pagina = 1
        while True:
            payload = self._fetch(self._url_pagina(reference_date, pagina))
            colunas_pagina, linhas_pagina = _colunas_e_linhas(payload)
            if pagina == 1:
                colunas = colunas_pagina
            linhas.extend(linhas_pagina)
            total_paginas = self._total_paginas(payload)
            if pagina >= total_paginas:
                break
            pagina += 1
        mapa = agregar_por_ticker(colunas, linhas)
        self._cache.write_meta(chave, {"data": {k: str(v) for k, v in mapa.items()}})
        return mapa

    @staticmethod
    def _total_paginas(payload: object) -> int:
        """Retorna o número de páginas do payload, com mínimo de 1."""
        if isinstance(payload, dict):
            tabela = payload.get("table")
            if isinstance(tabela, dict):
                paginas = tabela.get("pageCount")
                if isinstance(paginas, int) and paginas > 0:
                    return paginas
        return 1

    @staticmethod
    def _mapa_de_payload(payload: dict) -> dict[str, Decimal]:
        """Reconstrói o mapa de ações alugadas a partir do cache."""
        mapa: dict[str, Decimal] = {}
        for ticker, valor in payload.items():
            saldo = _numero(valor)
            if saldo is not None:
                mapa[str(ticker)] = saldo
        return mapa

    def _url_pagina(
        self: "B3ShortInterestSource", reference_date: date, pagina: int
    ) -> str:
        """Monta a URL da página da tabela para a data informada."""
        dia = reference_date.isoformat()
        return f"{self._url}/{dia}/{dia}/{pagina}/{self._page_size}"

    def _baixar(self: "B3ShortInterestSource", url: str) -> dict:
        """Baixa uma página da tabela BDI via POST JSON."""
        import requests

        resposta = requests.post(
            url,
            json={},
            timeout=60,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120 Safari/537.36"
                ),
                "Accept": "application/json",
            },
        )
        resposta.raise_for_status()
        return resposta.json()
