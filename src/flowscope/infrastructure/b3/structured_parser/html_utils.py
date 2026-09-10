"""Utilitários de navegação e normalização de HTML."""

from bs4 import BeautifulSoup, PageElement, Tag


def parse_html(html: str) -> BeautifulSoup:
    """Analisa uma string HTML em um objeto BeautifulSoup."""
    return BeautifulSoup(html, "html.parser")


def _texto_do_proximo_sibling(node: PageElement) -> str | None:
    """Retorna o texto do primeiro elemento irmão subsequente não vazio."""
    atual: PageElement | None = node
    while atual is not None:
        valor = _texto_do_irmao_seguinte(atual)
        if valor:
            return valor
        atual = atual.parent
    return None


def _texto_apos_rotulo(marcador: object, texto_rotulo: str) -> str | None:
    """Extrai o valor imediatamente posterior ao nó do rótulo no HTML."""
    if ":" in texto_rotulo:
        valor = texto_rotulo.split(":", 1)[1].strip()
        if valor:
            return valor
    atual = getattr(marcador, "parent", None)
    visitados: set[int] = set()
    while isinstance(atual, PageElement):
        visitados.add(id(atual))
        restante = _texto_apos_no_parent(atual, atual, visitados)
        if restante:
            return restante
        valor = _texto_do_irmao_seguinte(atual)
        if valor:
            return valor
        atual = atual.parent
    return None


def _texto_do_irmao_seguinte(node: PageElement) -> str | None:
    """Retorna o texto do próximo nó irmão com conteúdo, ignorando espaços."""
    proximo = node.next_sibling
    while proximo is not None:
        if isinstance(proximo, Tag):
            valor = proximo.get_text(" ", strip=True)
        else:
            valor = str(proximo).strip()
        if valor:
            return valor
        proximo = proximo.next_sibling
    return None


def _texto_apos_no_parent(
    parent: Tag, node: PageElement, visitados: set[int] | None = None
) -> str | None:
    """Retorna o texto do elemento pai posterior ao nó informado.

    O nó informado deve ser um filho direto do elemento pai. Nós já
    visitados pelo caminho de busca ascendente são ignorados.
    """
    partes: list[str] = []
    capturar = False
    for conteudo in parent.contents:
        if conteudo is node:
            capturar = True
            continue
        if not capturar:
            continue
        if visitados is not None and isinstance(conteudo, Tag) and id(conteudo) in visitados:
            continue
        if isinstance(conteudo, Tag):
            texto = conteudo.get_text(" ", strip=True)
        else:
            texto = str(conteudo).strip()
        if texto:
            partes.append(texto)
    valor = " ".join(partes).strip()
    return valor or None


def _celulas_da_linha(row: Tag) -> list[str]:
    """Retorna o texto das células (td ou th) de uma linha de tabela."""
    return [td.get_text(" ", strip=True) for td in row.find_all(["td", "th"])]


def _normalizar(texto: str) -> str:
    """Normaliza texto para comparação de cabeçalhos (minúsculas, sem acentos)."""
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
        ":": "",
        " ": "",
    }
    resultado = texto.strip().lower()
    for origem, destino in trocas.items():
        resultado = resultado.replace(origem, destino)
    return resultado


def _valor_ou_none(valor: str) -> str | None:
    """Retorna ``None`` quando o valor da célula é vazio."""
    return valor if valor else None
