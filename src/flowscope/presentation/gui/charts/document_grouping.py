"""Renderização Markdown dos agrupamentos da árvore de documentos.

O nó selecionado é o cabeçalho de nível ``#`` e cada sub-agrupamento
incrementa o nível. Cada documento vira um item de lista com o resumo curto ou
a mensagem de indisponibilidade.
"""

from dataclasses import dataclass
from pathlib import Path

from flowscope.application.documentos.mensagens import (
    RESUMO_INDISPONIVEL,
    SUFIXO_LLM_AUSENTE,
    SUFIXO_LLM_CONFIGURADA,
    mensagem_indisponivel,
)
from flowscope.domain.documents import (
    AnoDocumentos,
    CatalogoTicker,
    CategoriaDocumentos,
    DocumentoArquivo,
    MesDocumentos,
)

__all__ = [
    "RESUMO_INDISPONIVEL",
    "SUFIXO_LLM_AUSENTE",
    "SUFIXO_LLM_CONFIGURADA",
    "Agrupamento",
    "mensagem_indisponivel",
    "render_grupo",
]

#: Profundidade de cada tipo de agrupamento na hierarquia.
_PROFUNDIDADE = {"ticker": 1, "ano": 2, "mes": 3, "categoria": 4}


@dataclass(frozen=True)
class Agrupamento:
    """Payload de um nó de agrupamento da árvore."""

    tipo: str
    titulo: str
    ano: int | None = None
    mes: int | None = None
    categoria: str | None = None


def render_grupo(
    catalogo: CatalogoTicker,
    agrupamento: Agrupamento,
    por_caminho: dict[Path, DocumentoArquivo],
    mensagem: str,
) -> str:
    """Renderiza a lista Markdown do agrupamento com níveis relativos."""
    base = _PROFUNDIDADE[agrupamento.tipo]
    linhas: list[str] = []
    if agrupamento.tipo == "ticker":
        linhas.append(f"# {catalogo.ticker}")
    for ano in _filtrar_anos(catalogo, agrupamento):
        _acrescentar_titulo(linhas, 2, base, ano.ano)
        for mes in _filtrar_meses(ano, agrupamento):
            _acrescentar_titulo(linhas, 3, base, f"{mes.mes:02d}")
            for categoria in _filtrar_categorias(mes, agrupamento):
                _acrescentar_titulo(linhas, 4, base, categoria.nome)
                _linhas_arquivos(linhas, categoria.arquivos, por_caminho, mensagem)
    return "\n".join(linhas)


def _acrescentar_titulo(
    linhas: list[str], nivel: int, base: int, texto: object
) -> None:
    """Acrescenta o cabeçalho quando ele não é anterior ao agrupamento."""
    if base <= nivel:
        linhas.append(f"{'#' * (nivel - base + 1)} {texto}")


def _filtrar_anos(
    catalogo: CatalogoTicker, agrupamento: Agrupamento
) -> tuple[AnoDocumentos, ...]:
    """Filtra os anos do catálogo pelo agrupamento selecionado."""
    if agrupamento.ano is None:
        return catalogo.anos
    return tuple(ano for ano in catalogo.anos if ano.ano == agrupamento.ano)


def _filtrar_meses(
    ano: AnoDocumentos, agrupamento: Agrupamento
) -> tuple[MesDocumentos, ...]:
    """Filtra os meses do ano pelo agrupamento selecionado."""
    if agrupamento.mes is None:
        return ano.meses
    return tuple(mes for mes in ano.meses if mes.mes == agrupamento.mes)


def _filtrar_categorias(
    mes: MesDocumentos, agrupamento: Agrupamento
) -> tuple[CategoriaDocumentos, ...]:
    """Filtra as categorias do mês pelo agrupamento selecionado."""
    if agrupamento.categoria is None:
        return mes.categorias
    return tuple(
        categoria
        for categoria in mes.categorias
        if categoria.nome == agrupamento.categoria
    )


def _linhas_arquivos(
    linhas: list[str],
    arquivos: tuple[DocumentoArquivo, ...],
    por_caminho: dict[Path, DocumentoArquivo],
    mensagem: str,
) -> None:
    """Acrescenta um item de lista por documento, com o resumo curto."""
    for arquivo in arquivos:
        atual = por_caminho.get(arquivo.caminho, arquivo)
        texto = atual.short_summary or mensagem
        linhas.append(f"- {arquivo.nome} — {texto}")
