"""Validação de argumentos das tools MCP."""

from __future__ import annotations


def validar_schema(schema: dict, argumentos: object) -> str | None:
    """Valida os argumentos contra o schema, devolvendo o erro ou ``None``."""
    if not isinstance(argumentos, dict):
        return "os argumentos devem ser um objeto"
    propriedades = schema.get("properties", {})
    for nome in schema.get("required", ()):
        if nome not in argumentos:
            return f"campo obrigatório ausente: {nome}"
    for nome, valor in argumentos.items():
        if nome not in propriedades:
            return f"campo desconhecido: {nome}"
        erro = _validar_valor(propriedades[nome], valor, nome)
        if erro:
            return erro
    return None


def _validar_valor(spec: dict, valor: object, nome: str) -> str | None:
    """Valida um valor individual conforme o tipo e as faixas do schema."""
    tipo = spec.get("type")
    if tipo == "array":
        return _validar_array(spec, valor, nome)
    erro = _validar_escalar(tipo, valor, nome)
    if erro:
        return erro
    permitidos = spec.get("enum")
    if permitidos is not None and valor not in permitidos:
        return f"o campo '{nome}' deve ser um de: {', '.join(map(str, permitidos))}"
    return _validar_faixa(spec, valor, nome)


def _validar_escalar(tipo: object, valor: object, nome: str) -> str | None:
    """Valida o tipo de um valor escalar (texto, inteiro ou booleano)."""
    if tipo == "string" and not isinstance(valor, str):
        return f"o campo '{nome}' deve ser texto"
    if tipo == "integer" and (isinstance(valor, bool) or not isinstance(valor, int)):
        return f"o campo '{nome}' deve ser um inteiro"
    if tipo == "boolean" and not isinstance(valor, bool):
        return f"o campo '{nome}' deve ser booleano"
    return None


def _validar_array(spec: dict, valor: object, nome: str) -> str | None:
    """Valida uma lista e os seus elementos contra o schema do item."""
    if not isinstance(valor, list):
        return f"o campo '{nome}' deve ser uma lista"
    item = spec.get("items")
    for elemento in valor:
        if item is not None and (erro := _validar_valor(item, elemento, nome)):
            return erro
    return None


def _validar_faixa(spec: dict, valor: object, nome: str) -> str | None:
    """Valida os limites ``minimum``/``maximum`` de um valor numérico."""
    if isinstance(valor, bool) or not isinstance(valor, int):
        return None
    minimo = spec.get("minimum")
    maximo = spec.get("maximum")
    if minimo is not None and valor < minimo:
        return f"o campo '{nome}' deve ser no mínimo {minimo}"
    if maximo is not None and valor > maximo:
        return f"o campo '{nome}' deve ser no máximo {maximo}"
    return None


__all__ = ["validar_schema"]
