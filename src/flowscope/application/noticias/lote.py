"""Ordenação do resumo em lote das notícias.

A ordem é explícita e independe da ordem de inserção na árvore: as categorias
de topo seguem ``SECOES_ORDEM`` e, dentro de cada grupo, a data de publicação é
decrescente, com desempate determinista. A aplicação recebe a data já
interpretada em ``data_ordinal`` pelo adaptador.
"""

from collections.abc import Callable

from flowscope.application.resumo_documento import resumo_completo
from flowscope.domain.documents import DocumentoArquivo
from flowscope.domain.noticias import SECOES_ORDEM

#: Índice de cada categoria de topo na ordem de processamento do lote.
_INDICE_SECAO = {secao: indice for indice, secao in enumerate(SECOES_ORDEM)}


def precisa_resumo(arquivo: DocumentoArquivo) -> bool:
    """Indica se o item precisa de resumo pela regra compartilhada.

    Trata como desatualizado o resumo persistido que não termina em pontuação
    final, alinhando Notícias ao comportamento já existente em Documentos. Não
    conhece a ausência de texto, que é resolvida pelo worker e aplicada pelo
    filtro injetado pela apresentação.
    """
    return not resumo_completo(arquivo.short_summary, arquivo.long_summary)


def pendentes_ordenados(
    arquivos: list[DocumentoArquivo],
    precisa: Callable[[DocumentoArquivo], bool] | None = None,
) -> list[DocumentoArquivo]:
    """Retorna os itens pendentes por grupo e da data mais recente à mais antiga.

    ``precisa`` sobrepõe a regra padrão de resumo, permitindo à apresentação
    excluir itens com ausência definitiva de texto sem refazer I/O na thread do
    Tk.
    """
    filtro = precisa if precisa is not None else precisa_resumo
    pendentes = [arquivo for arquivo in arquivos if filtro(arquivo)]
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
