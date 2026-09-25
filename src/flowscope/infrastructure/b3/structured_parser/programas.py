"""Extração dos programas de aquisição de ações em andamento da B3.

A fonte é o endpoint JSON ``stockProgramProxy/StockProgramCall/GetListedCompany``,
cujo payload traz ``results`` com ``company``, ``aprrovedDate``, ``startDate``,
``endDate``, ``quantity`` e ``observation``.
"""

from flowscope.domain.structured import ProgramaAquisicao


def extrair_programas_aquisicao(payload: object) -> list[ProgramaAquisicao]:
    """Extrai os programas de aquisição do payload JSON da API da B3."""
    programas: list[ProgramaAquisicao] = []
    for item in _resultados(payload):
        programa = _programa(item)
        if programa is not None:
            programas.append(programa)
    return programas


def _resultados(payload: object) -> list[dict]:
    """Extrai a lista de resultados do payload, tolerando formatos inválidos."""
    if not isinstance(payload, dict):
        return []
    resultados = payload.get("results")
    if not isinstance(resultados, list):
        return []
    return [item for item in resultados if isinstance(item, dict)]


def _programa(item: dict) -> ProgramaAquisicao | None:
    """Monta um ``ProgramaAquisicao`` do item bruto, ou ``None`` sem empresa."""
    empresa = _texto_ou_none(item.get("company"))
    if not empresa:
        return None
    return ProgramaAquisicao(
        empresa=empresa,
        data_aprovacao=_texto_ou_none(item.get("aprrovedDate")),
        data_inicio=_texto_ou_none(item.get("startDate")),
        data_fim=_texto_ou_none(item.get("endDate")),
        quantidade=_texto_ou_none(item.get("quantity")),
        intermediarios=_texto_ou_none(item.get("observation")),
    )


def _texto_ou_none(valor: object) -> str | None:
    """Normaliza um valor textual, devolvendo ``None`` quando vazio."""
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None
