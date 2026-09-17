"""Listagem e filtragem de avisos aos acionistas de BDR no Plantão B3.

A consulta é feita mês a mês (no máximo um mês por requisição) ao longo da
janela configurada, usando a raiz do ticker como palavra-chave. Apenas itens
cujo título contenha ``({RAIZ})`` e o termo ``Aviso aos Acionistas`` são
considerados avisos do BDR.
"""

import logging
from collections.abc import Callable
from datetime import date, timedelta

from flowscope.domain.bdr import AvisoBdr
from flowscope.infrastructure.b3.bdr.constants import (
    AGENCIA,
    MESES_JANELA,
    TERMO_AVISO,
    TTL_AVISOS_DIAS,
)
from flowscope.infrastructure.cache import CacheManager

logger = logging.getLogger("flowscope")

_UM_DIA = timedelta(days=1)

#: Assinatura do callable que coleta notícias brutas de uma janela mensal.
ColetarNoticias = Callable[[str, str, date, date], list[dict]]


def raiz_ticker(ticker: str) -> str:
    """Remove o sufixo numérico do ticker, devolvendo a raiz usada no título."""
    normalizado = ticker.strip().upper()
    raiz = normalizado.rstrip("0123456789")
    return raiz or normalizado


def _desembrulhar(item: dict) -> dict:
    """Desembrulha o item ``{"NwsMsg": {...}}`` retornado pelo Plantão B3."""
    interno = item.get("NwsMsg")
    return interno if isinstance(interno, dict) else item


def itens_de_noticias(dados: object) -> list[dict]:
    """Extrai os itens de notícia da resposta da API do Plantão B3.

    A API retorna uma lista de itens ``{"NwsMsg": {...}}``; formatos legados
    com ``results`` ou itens já achatados também são aceitos.
    """
    if isinstance(dados, list):
        brutos = [item for item in dados if isinstance(item, dict)]
    elif isinstance(dados, dict):
        brutos = [item for item in (dados.get("results") or []) if isinstance(item, dict)]
    else:
        return []
    return [_desembrulhar(item) for item in brutos]


def id_noticia(item: dict) -> str | None:
    """Retorna o identificador da notícia, ou ``None`` quando ausente."""
    for chave in ("idNoticia", "id_noticia", "id", "codigo"):
        valor = item.get(chave)
        if valor not in (None, ""):
            return str(valor)
    return None


def titulo_item(item: dict) -> str:
    """Retorna o título da notícia, aceitando variações de chave."""
    for chave in ("headline", "titulo", "title", "tituloNoticia"):
        valor = item.get(chave)
        if valor:
            return str(valor)
    return ""


def data_publicacao_item(item: dict) -> str:
    """Retorna a data de publicação da notícia, aceitando variações de chave."""
    for chave in ("dateTime", "dataPublicacao", "dataNoticia", "data"):
        valor = item.get(chave)
        if valor:
            return str(valor)
    return ""


def titulo_e_aviso(titulo: str, raiz: str) -> bool:
    """Indica se o título identifica um aviso aos acionistas do BDR."""
    if TERMO_AVISO.lower() not in titulo.lower():
        return False
    return f"({raiz.upper()})" in titulo.upper()


def filtrar_avisos(itens: list[dict], ticker: str) -> list[AvisoBdr]:
    """Filtra os itens de notícia dos avisos aos acionistas do ticker."""
    raiz = raiz_ticker(ticker)
    avisos: list[AvisoBdr] = []
    for bruto in itens:
        item = _desembrulhar(bruto)
        titulo = titulo_item(item)
        if not titulo_e_aviso(titulo, raiz):
            continue
        identificador = id_noticia(item)
        if identificador is None:
            continue
        avisos.append(
            AvisoBdr(
                ticker=ticker.strip().upper(),
                id_noticia=identificador,
                titulo=titulo,
                data_publicacao=data_publicacao_item(item),
            )
        )
    return avisos


def janelas_mensais(
    reference_date: date, meses: int = MESES_JANELA
) -> list[tuple[date, date]]:
    """Gera janelas mensais ``(início, fim)`` dos últimos ``meses`` meses."""
    janelas: list[tuple[date, date]] = []
    ano, mes = reference_date.year, reference_date.month
    for _ in range(meses):
        inicio = date(ano, mes, 1)
        proximo = date(ano + 1, 1, 1) if mes == 12 else date(ano, mes + 1, 1)
        fim = min(proximo - _UM_DIA, reference_date)
        janelas.append((inicio, fim))
        ano, mes = (ano - 1, 12) if mes == 1 else (ano, mes - 1)
    return janelas


def listar_avisos(
    coletar: ColetarNoticias,
    ticker: str,
    reference_date: date,
    cache: CacheManager | None = None,
    meses: int = MESES_JANELA,
) -> list[AvisoBdr]:
    """Lista os avisos do BDR mês a mês, tolerando falha por janela.

    Cada janela é consultada com cache de 1 dia; uma falha em uma janela é
    registrada e não interrompe as demais. Uma janela sem avisos contribui com
    lista vazia, distinta de falha.
    """
    raiz = raiz_ticker(ticker)
    avisos: list[AvisoBdr] = []
    vistos: set[str] = set()
    for inicio, fim in janelas_mensais(reference_date, meses):
        itens = _coletar_janela(coletar, raiz, inicio, fim, cache)
        for aviso in filtrar_avisos(itens, ticker):
            if aviso.id_noticia in vistos:
                continue
            vistos.add(aviso.id_noticia)
            avisos.append(aviso)
    return avisos


def _coletar_janela(
    coletar: ColetarNoticias,
    raiz: str,
    inicio: date,
    fim: date,
    cache: CacheManager | None,
) -> list[dict]:
    """Coleta uma janela mensal, usando cache quando disponível e tolerando falha."""
    if cache is None:
        return _tentar_coletar(coletar, raiz, inicio, fim)

    chave = f"bdr_noticias_{AGENCIA}_{raiz}_{inicio.isoformat()}_{fim.isoformat()}"

    def _fetch() -> dict[str, object]:
        return {"itens": coletar(AGENCIA, raiz, inicio, fim)}

    try:
        payload = cache.get_or_fetch(chave, TTL_AVISOS_DIAS, _fetch)
    except Exception:  # falha de aquisição isolada por janela
        logger.warning(
            "Falha ao listar avisos de %s no período %s-%s",
            raiz,
            inicio,
            fim,
            exc_info=True,
        )
        return []
    itens = payload.get("itens") or []
    return [item for item in itens if isinstance(item, dict)]


def _tentar_coletar(
    coletar: ColetarNoticias, raiz: str, inicio: date, fim: date
) -> list[dict]:
    """Executa a coleta de uma janela, tolerando falha de aquisição."""
    try:
        return list(coletar(AGENCIA, raiz, inicio, fim))
    except Exception:  # falha de aquisição isolada por janela
        logger.warning(
            "Falha ao listar avisos de %s no período %s-%s",
            raiz,
            inicio,
            fim,
            exc_info=True,
        )
        return []
