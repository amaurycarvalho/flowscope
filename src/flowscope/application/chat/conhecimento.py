"""Bloco de conhecimento do próprio FlowScope para o contexto do chat.

Compõe os textos de orientação das sub-abas e as informações institucionais da
aba "Sobre". A montagem e a ordem das seções são regras de aplicação; os textos
de interface (``TAB_CONTENT`` e as informações da aba "Sobre") são fornecidos
pela apresentação como entrada.
"""

from collections.abc import Mapping

#: Cabeçalho da seção institucional do bloco de conhecimento.
_CABECALHO_SOBRE = "Sobre o FlowScope"

#: Cabeçalho da seção de orientação das sub-abas.
_CABECALHO_ORIENTACAO = "Orientação das sub-abas"


def _texto_da_orientacao(corpo: list[tuple[str, str]]) -> str:
    """Concatena os fragmentos de uma entrada de ``TAB_CONTENT``."""
    return "".join(texto for texto, _estilo in corpo).strip()


def _secoes_orientacao(
    tab_content: Mapping[object, tuple[str, list[tuple[str, str]]]],
) -> list[str]:
    """Monta uma seção de texto por sub-aba com orientação cadastrada."""
    secoes: list[str] = []
    for titulo, corpo in tab_content.values():
        texto = _texto_da_orientacao(corpo)
        if not texto:
            continue
        secoes.append(f"### {titulo}\n{texto}")
    return secoes


def montar_bloco_conhecimento(
    tab_content: Mapping[object, tuple[str, list[tuple[str, str]]]],
    *,
    apresentacao: str,
    licenca: str,
    versao: str,
    release_date: str,
    repositorio: str,
) -> str:
    """Monta o bloco de conhecimento do FlowScope.

    Reúne a apresentação, a licença e a versão do aplicativo com os textos de
    orientação das sub-abas, em um bloco enviado como contexto de sistema na
    aba "Chat AI".
    """
    partes = [
        f"# {_CABECALHO_SOBRE}",
        apresentacao,
        f"Licença: {licenca}",
        f"Versão: v{versao} ({release_date})",
        f"Repositório: {repositorio}",
        "",
        f"# {_CABECALHO_ORIENTACAO}",
    ]
    partes.extend(_secoes_orientacao(tab_content))
    return "\n".join(partes)
