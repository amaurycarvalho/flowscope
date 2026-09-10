"""Conversão de itens brutos de material facts em entidades de domínio."""

from flowscope.domain.structured import (
    Assembleia,
    AvisoAcionista,
    AvisoDebenturista,
    CategoriaMaterialFact,
    DocumentoMaterialFact,
    FatoRelevante,
)
from flowscope.infrastructure.b3.funds_client.texto import (
    _normalizar_rotulo,
    _string_ou_none,
)


def _codigo_categoria(categoria: CategoriaMaterialFact | str) -> str:
    """Valida e retorna o código numérico de uma categoria do material fact."""
    if isinstance(categoria, CategoriaMaterialFact):
        return categoria.value
    codigo = str(categoria)
    try:
        return CategoriaMaterialFact(codigo).value
    except ValueError:
        raise ValueError(f"Categoria GetMaterialFacts inválida: {categoria!r}") from None


_ROTULOS_CLASSES: dict[str, type] = {
    "assembleia": Assembleia,
    "assembleias": Assembleia,
    "fatorelevante": FatoRelevante,
    "fatosrelevantes": FatoRelevante,
    "avisoacionista": AvisoAcionista,
    "avisoacionistas": AvisoAcionista,
    "avisoaosacionistas": AvisoAcionista,
    "avisodebenturista": AvisoDebenturista,
    "avisodebenturistas": AvisoDebenturista,
    "avisoaosdebenturistas": AvisoDebenturista,
}


def _classe_material_fact(categoria: str) -> type:
    """Retorna a classe de entidade correspondente à categoria da API."""
    if not categoria:
        return DocumentoMaterialFact
    return _ROTULOS_CLASSES.get(_normalizar_rotulo(categoria), DocumentoMaterialFact)


def _converter_item_material_fact(
    item: dict, *, ticker: str, code_cvm: str
) -> DocumentoMaterialFact:
    """Monta a entidade de domínio a partir de um item bruto do ``GetMaterialFacts``."""
    company = item.get("company")
    empresa = ""
    if isinstance(company, dict):
        empresa = _string_ou_none(company.get("companyName")) or ""
    categoria = _string_ou_none(item.get("category")) or ""
    campos = {
        "code_cvm": code_cvm,
        "empresa": empresa,
        "ticker": ticker,
        "data_referencia": _string_ou_none(item.get("dateReference")) or "",
        "data_entrega": _string_ou_none(item.get("deliveryDate")),
        "categoria": categoria,
        "tipo": _string_ou_none(item.get("type")),
        "especie": _string_ou_none(item.get("kind")),
        "status": _string_ou_none(item.get("status")),
        "assunto": _string_ou_none(item.get("subject")) or "",
        "url_documento": _string_ou_none(item.get("urlSearch")),
        "url_download": _string_ou_none(item.get("urlDownload")),
    }
    classe = _classe_material_fact(categoria)
    if classe is Assembleia:
        return Assembleia(
            **campos,
            tipo_assembleia=campos["tipo"],
            especie_documento=campos["especie"],
        )
    return classe(**campos)
