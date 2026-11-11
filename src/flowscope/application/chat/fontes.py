"""Derivação e merge das fontes consultadas no chat.

A extração é dirigida pela operação de navegação, e não pelo formato de
``dados``: ``obter`` gera o próprio caminho do resultado, ``listar`` gera os
itens e as buscas geram os ``resultados``. O merge associa os rótulos
declarados pela LLM aos caminhos derivados e valida as declarações na árvore.
"""

from __future__ import annotations

import logging

from flowscope.application.chat.arvore import ErroNavegacao, normalizar_caminho
from flowscope.application.chat.protocolo import ProtocoloNavegacao
from flowscope.domain.chat import FonteChat

logger = logging.getLogger("flowscope")

#: Teto defensivo de fontes declaradas aceitas por resposta.
MAX_FONTES_DECLARADAS = 50


def extrair(resultados: list[dict]) -> list[str]:
    """Extrai os caminhos consultados dos resultados de navegação.

    Resultados com erro não geram fonte; os caminhos são deduplicados
    preservando a primeira ocorrência.
    """
    caminhos: list[str] = []
    for resultado in resultados:
        if "erro" in resultado:
            continue
        op = resultado.get("op")
        dados = resultado.get("dados")
        if op == "obter":
            caminho = resultado.get("caminho")
            if isinstance(caminho, str) and caminho:
                caminhos.append(caminho)
        elif op == "listar":
            caminhos.extend(_caminhos_dos_itens(dados))
        elif op in ("buscar", "buscar_semantico") and isinstance(dados, dict):
            caminhos.extend(_caminhos_dos_itens(dados.get("resultados")))
    return list(dict.fromkeys(caminhos))


def mesclar(
    derivadas: list[str],
    declaradas: list[FonteChat],
    protocolo: ProtocoloNavegacao,
) -> list[FonteChat]:
    """Combina as fontes derivadas com as declaradas validadas na árvore.

    Caminhos declarados são normalizados e validados; os inexistentes ou
    inválidos são descartados com registro em log. A ordem final preserva as
    fontes derivadas e acrescenta ao final as declaradas ainda não derivadas.
    """
    rotulos = _rotulos_declarados(declaradas, protocolo)
    fontes = [
        FonteChat(caminho=caminho, rotulo=rotulos.get(caminho)) for caminho in derivadas
    ]
    derivados = {fonte.caminho for fonte in fontes}
    fontes.extend(
        FonteChat(caminho=caminho, rotulo=rotulo)
        for caminho, rotulo in rotulos.items()
        if caminho not in derivados
    )
    return fontes


def _caminhos_dos_itens(itens: object) -> list[str]:
    """Lista os caminhos dos itens de uma lista, descartando entradas inválidas."""
    if not isinstance(itens, list):
        return []
    return [
        item["caminho"]
        for item in itens
        if isinstance(item, dict)
        and isinstance(item.get("caminho"), str)
        and item["caminho"]
    ]


def _rotulos_declarados(
    declaradas: list[FonteChat], protocolo: ProtocoloNavegacao
) -> dict[str, str | None]:
    """Mapeia cada caminho declarado válido para o seu rótulo."""
    rotulos: dict[str, str | None] = {}
    for declarada in declaradas[:MAX_FONTES_DECLARADAS]:
        caminho = _caminho_declarado_valido(declarada, protocolo)
        if caminho is None:
            continue
        if caminho not in rotulos or (rotulos[caminho] is None and declarada.rotulo):
            rotulos[caminho] = declarada.rotulo
    return rotulos


def _caminho_declarado_valido(
    declarada: FonteChat, protocolo: ProtocoloNavegacao
) -> str | None:
    """Normaliza e valida um caminho declarado, registrando descartes em log."""
    try:
        caminho = normalizar_caminho(declarada.caminho)
    except ErroNavegacao:
        logger.warning("Fonte declarada inválida descartada: %r", declarada.caminho)
        return None
    try:
        if protocolo.existe(caminho):
            return caminho
    except ErroNavegacao:
        pass
    logger.warning("Fonte declarada inexistente descartada: %r", declarada.caminho)
    return None
