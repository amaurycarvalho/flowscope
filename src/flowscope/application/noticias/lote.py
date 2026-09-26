"""Ordenação do resumo em lote das notícias.

A ordem é explícita e independe da ordem de inserção na árvore: as categorias
de topo seguem ``SECOES_ORDEM`` e, dentro de cada grupo, a data de publicação é
decrescente, com desempate determinista. A aplicação recebe a data já
interpretada em ``data_ordinal`` pelo adaptador.
"""

from flowscope.domain.documents import DocumentoArquivo
from flowscope.domain.noticias import SECOES_ORDEM

#: Índice de cada categoria de topo na ordem de processamento do lote.
_INDICE_SECAO = {secao: indice for indice, secao in enumerate(SECOES_ORDEM)}


def pendentes_ordenados(
    arquivos: list[DocumentoArquivo],
) -> list[DocumentoArquivo]:
    """Retorna os itens sem resumo por grupo e da data mais recente à mais antiga."""
    pendentes = [arquivo for arquivo in arquivos if arquivo.long_summary is None]
    return sorted(pendentes, key=chave_ordenacao)


def chave_ordenacao(arquivo: DocumentoArquivo) -> tuple:
    """Chave determinista: grupo, data decrescente e desempate estável."""
    secao = getattr(arquivo, "secao", "")
    return (
        _INDICE_SECAO.get(secao, len(SECOES_ORDEM)),
        -getattr(arquivo, "data_ordinal", 0),
        getattr(arquivo, "categoria", ""),
        arquivo.nome,
        str(arquivo.caminho),
    )
