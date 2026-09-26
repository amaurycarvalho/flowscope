"""Regra pura do marcador de ausência de texto extraído.

O marcador distingue um documento já processado e sem texto de um documento
ainda pendente de conversão; é tratado como ausência por todos os consumidores.
"""

#: Marcador gravado no cache quando a conversão não produz texto.
SEM_TEXTO = "Sem texto extraível para pré-visualização."


def tem_texto(texto: str | None) -> bool:
    """Indica se o texto contém conteúdo extraído (e não o marcador de ausência)."""
    if not texto:
        return False
    limpo = texto.strip()
    return bool(limpo) and limpo != SEM_TEXTO
