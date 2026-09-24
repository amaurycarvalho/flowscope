"""Bloco de conhecimento do próprio FlowScope para o contexto do chat.

Compõe, uma única vez, os textos de orientação das sub-abas e as informações
institucionais da aba "Sobre". O bloco é estável entre turnos e respondido como
contexto de sistema para perguntas sobre o próprio aplicativo.
"""

from flowscope import __release_date__, __version__
from flowscope.presentation.gui.app_tabs import TAB_CONTENT
from flowscope.presentation.gui.widgets.about_panel import (
    APRESENTACAO,
    LICENCA,
    REPOSITORIO_URL,
)

#: Cabeçalho da seção institucional do bloco de conhecimento.
_CABECALHO_SOBRE = "Sobre o FlowScope"

#: Cabeçalho da seção de orientação das sub-abas.
_CABECALHO_ORIENTACAO = "Orientação das sub-abas"


def _texto_da_orientacao(corpo: list[tuple[str, str]]) -> str:
    """Concatena os fragmentos de uma entrada de ``TAB_CONTENT``."""
    return "".join(texto for texto, _estilo in corpo).strip()


def _secoes_orientacao() -> list[str]:
    """Monta uma seção de texto por sub-aba com orientação cadastrada."""
    secoes: list[str] = []
    for titulo, corpo in TAB_CONTENT.values():
        texto = _texto_da_orientacao(corpo)
        if not texto:
            continue
        secoes.append(f"### {titulo}\n{texto}")
    return secoes


def montar_bloco_conhecimento() -> str:
    """Monta o bloco de conhecimento do FlowScope a partir da GUI.

    Reúne a apresentação, a licença e a versão do aplicativo com os textos de
    orientação das sub-abas, em um bloco enviado como contexto de sistema na
    aba "Chat AI".
    """
    partes = [
        f"# {_CABECALHO_SOBRE}",
        APRESENTACAO,
        f"Licença: {LICENCA}",
        f"Versão: v{__version__} ({__release_date__})",
        f"Repositório: {REPOSITORIO_URL}",
        "",
        f"# {_CABECALHO_ORIENTACAO}",
    ]
    partes.extend(_secoes_orientacao())
    return "\n".join(partes)
