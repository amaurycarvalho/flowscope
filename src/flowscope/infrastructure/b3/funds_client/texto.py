"""Normalização de texto para comparação de rótulos e valores da API."""


def _string_ou_none(valor: object) -> str | None:
    """Retorna a string do valor, ou ``None`` quando vazio."""
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto if texto else None


def _normalizar_rotulo(rotulo: str) -> str:
    """Normaliza um rótulo para comparação, sem acentos e espaços."""
    trocas = {
        "ç": "c",
        "á": "a",
        "ã": "a",
        "à": "a",
        "â": "a",
        "é": "e",
        "ê": "e",
        "í": "i",
        "ó": "o",
        "ô": "o",
        "õ": "o",
        "ú": "u",
    }
    texto = rotulo.strip().lower()
    for origem, destino in trocas.items():
        texto = texto.replace(origem, destino)
    return "".join(texto.split())
