"""Normalização de códigos CVM obtidos do cadastro de empresas listadas da B3."""


def _normalizar_code_cvm(valor: str) -> str:
    """Remove os zeros à esquerda de um código CVM."""
    valor = valor.strip()
    normalizado = valor.lstrip("0")
    return normalizado or "0"
