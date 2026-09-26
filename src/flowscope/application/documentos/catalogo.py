"""Porta, read-model e caso de uso do catálogo de documentos.

O read-model ``montar_catalogo`` agrupa e ordena os arquivos na hierarquia
``ano → mês → categoria`` sem tocar em I/O. A varredura do cache é
responsabilidade do adaptador, que implementa ``CatalogoRepository``.
"""

from pathlib import Path
from typing import Protocol

from flowscope.application.document_text_port import DocumentTextStore
from flowscope.application.documentos.document_summary_port import (
    DocumentSummaryStore,
)
from flowscope.domain.documents import (
    AnoDocumentos,
    CatalogoTicker,
    CategoriaDocumentos,
    DocumentoArquivo,
    MesDocumentos,
)


def chave_documento(caminho: Path, base: Path) -> str:
    """Deriva a chave estável de um documento a partir do caminho relativo."""
    try:
        return Path(caminho).relative_to(Path(base)).as_posix()
    except ValueError:
        return Path(caminho).name


class CatalogoRepository(Protocol):
    """Contrato da varredura do catálogo de documentos em cache de um ticker."""

    def catalogo(self: "CatalogoRepository", ticker: str) -> CatalogoTicker:
        """Retorna o catálogo de documentos em cache do ticker informado."""
        ...


class CatalogoDocumentos(CatalogoRepository, Protocol):
    """Repositório de catálogo com as raízes e os stores de conteúdo.

    É o contrato mínimo consumido pela apresentação que precisa, além do
    catálogo, da raiz de cache e dos stores de resumo/texto associados.
    """

    @property
    def base_dir(self: "CatalogoDocumentos") -> Path:
        """Retorna o diretório raiz de cache varrido."""
        ...

    @property
    def summary_store(self: "CatalogoDocumentos") -> DocumentSummaryStore:
        """Retorna o store de resumos associado ao catálogo."""
        ...

    @property
    def text_store(self: "CatalogoDocumentos") -> DocumentTextStore:
        """Retorna o store de textos associado ao catálogo."""
        ...


class ConsultarCatalogoUseCase:
    """Consulta o catálogo de documentos de um ticker pelo repositório."""

    def __init__(
        self: "ConsultarCatalogoUseCase", repositorio: CatalogoRepository
    ) -> None:
        """Guarda o repositório que varre o cache."""
        self._repositorio = repositorio

    def executar(self: "ConsultarCatalogoUseCase", ticker: str) -> CatalogoTicker:
        """Retorna o catálogo de documentos do ticker informado."""
        return self._repositorio.catalogo(ticker)


def montar_catalogo(
    ticker: str, arquivos: list[DocumentoArquivo]
) -> CatalogoTicker:
    """Agrupa e ordena os arquivos na hierarquia ano → mês → categoria."""
    por_ano: dict[int, dict[int, dict[str, list[DocumentoArquivo]]]] = {}
    for arquivo in arquivos:
        por_ano.setdefault(arquivo.ano, {}).setdefault(
            arquivo.mes, {}
        ).setdefault(arquivo.categoria, []).append(arquivo)

    anos: list[AnoDocumentos] = []
    for ano in sorted(por_ano, reverse=True):
        meses: list[MesDocumentos] = []
        for mes in sorted(por_ano[ano], reverse=True):
            categorias = [
                CategoriaDocumentos(nome, _ordenar_arquivos(por_ano[ano][mes][nome]))
                for nome in sorted(por_ano[ano][mes])
            ]
            meses.append(MesDocumentos(mes, tuple(categorias)))
        anos.append(AnoDocumentos(ano, tuple(meses)))
    return CatalogoTicker(ticker, tuple(anos))


def _ordenar_arquivos(
    arquivos: list[DocumentoArquivo],
) -> tuple[DocumentoArquivo, ...]:
    """Ordena os arquivos do mais recente ao mais antigo pelo nome."""
    return tuple(sorted(arquivos, key=_chave_arquivo, reverse=True))


def _chave_arquivo(arquivo: DocumentoArquivo) -> tuple[int, int, str]:
    """Chave de ordenação numérica para nomes de arquivo por id."""
    identificador = arquivo.caminho.stem
    if identificador.isdigit():
        return (1, int(identificador), "")
    return (0, 0, identificador)
