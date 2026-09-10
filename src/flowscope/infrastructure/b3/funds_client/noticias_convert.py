"""Conversão de itens brutos do Plantão B3 em entidades de domínio."""

from flowscope.domain.structured import NoticiaB3
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


def _converter_item_noticia(item: dict, *, agencia: str) -> NoticiaB3:
    """Monta a entidade ``NoticiaB3`` a partir de um item bruto do Plantão B3."""
    titulo = (
        _string_ou_none(item.get("titulo"))
        or _string_ou_none(item.get("title"))
        or ""
    )
    data_publicacao = (
        _string_ou_none(item.get("dataPublicacao"))
        or _string_ou_none(item.get("dataNoticia"))
        or _string_ou_none(item.get("data"))
        or ""
    )
    url = _string_ou_none(item.get("url")) or _string_ou_none(item.get("link"))
    return NoticiaB3(
        titulo=titulo,
        data_publicacao=data_publicacao,
        url=url,
        agencia=str(agencia),
    )
