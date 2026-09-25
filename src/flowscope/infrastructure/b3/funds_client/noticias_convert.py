"""Conversão de itens brutos do Plantão B3 em entidades de domínio."""

from datetime import date
from urllib.parse import urlencode

from flowscope.domain.structured import NoticiaB3
from flowscope.infrastructure.b3.funds_client.constants import (
    _NOTICIAS_DETALHE_URL,
)
from flowscope.infrastructure.b3.funds_client.texto import _string_ou_none


def _itens_de_noticias(dados: object) -> list[dict]:
    """Extrai os itens de notícia da resposta da API do Plantão B3."""
    if isinstance(dados, list):
        return [item for item in dados if isinstance(item, dict)]
    if not isinstance(dados, dict):
        return []
    return [
        item for item in (dados.get("results") or []) if isinstance(item, dict)
    ]


def _desembrulhar(item: dict) -> dict:
    """Desembrulha o item ``{"NwsMsg": {...}}`` retornado pelo Plantão B3."""
    interno = item.get("NwsMsg")
    return interno if isinstance(interno, dict) else item


def _id_noticia(item: dict) -> str | None:
    """Retorna o identificador da notícia, aceitando variações de chave."""
    for chave in ("idNoticia", "id_noticia", "id", "codigo"):
        valor = item.get(chave)
        if valor not in (None, ""):
            return str(valor)
    return None


def _data_iso(texto: str | None) -> str | None:
    """Normaliza a data de publicação para ``AAAA-MM-DD``, ou ``None``."""
    if not texto:
        return None
    try:
        return date.fromisoformat(texto[:10]).isoformat()
    except ValueError:
        return None


def _url_detalhe(item: dict, data_publicacao: str, agencia: str) -> str | None:
    """Monta a URL da página ``Detail`` da notícia a partir do id e da data."""
    identificador = _id_noticia(item)
    if not identificador:
        return None
    parametros = {"agencia": agencia, "idNoticia": identificador}
    data = _data_iso(data_publicacao)
    if data:
        parametros["dataNoticia"] = data
    return f"{_NOTICIAS_DETALHE_URL}?{urlencode(parametros)}"


def _converter_item_noticia(item: dict, *, agencia: str) -> NoticiaB3:
    """Monta a entidade ``NoticiaB3`` a partir de um item bruto do Plantão B3.

    Aceita o formato real ``{"NwsMsg": {...}}`` (``headline``/``dateTime``/
    ``id``) e formatos legados com campos achatados. Quando o item não traz
    URL explícita, ela é derivada da página ``Detail`` a partir do id e da data.
    """
    dados = _desembrulhar(item)
    titulo = (
        _string_ou_none(dados.get("titulo"))
        or _string_ou_none(dados.get("title"))
        or _string_ou_none(dados.get("headline"))
        or ""
    )
    data_publicacao = (
        _string_ou_none(dados.get("dataPublicacao"))
        or _string_ou_none(dados.get("dataNoticia"))
        or _string_ou_none(dados.get("data"))
        or _string_ou_none(dados.get("dateTime"))
        or ""
    )
    url = _string_ou_none(dados.get("url")) or _string_ou_none(dados.get("link"))
    if not url:
        url = _url_detalhe(dados, data_publicacao, agencia)
    return NoticiaB3(
        titulo=titulo,
        data_publicacao=data_publicacao,
        url=url,
        agencia=str(agencia),
    )
