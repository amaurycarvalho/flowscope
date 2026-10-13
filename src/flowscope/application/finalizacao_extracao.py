"""Regras puras da finalização definitiva de extrações não conclusivas.

Quando o usuário aceita um resultado não conclusivo como definitivo, o texto
persistido recebe uma nota que descreve a limitação (extração parcial, erro
crítico de leitura ou PDF protegido por senha) e o resumo correspondente é
gerado. As notas e o resumo determinístico são regras de aplicação, sem I/O e
sem dependência da interface, verificáveis de forma headless.
"""

from dataclasses import dataclass

from flowscope.application.document_preview import StatusExtracao
from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.domain.documents import DocumentoArquivo

__all__ = [
    "MOTIVOS_FINALIZAVEIS",
    "ItemPendente",
    "nota_extracao",
    "resumo_deterministico",
    "texto_definitivo",
]

#: Status de extração que podem ser finalizados explicitamente como definitivos.
MOTIVOS_FINALIZAVEIS = (
    StatusExtracao.PARCIAL,
    StatusExtracao.FALHA,
    StatusExtracao.PROTEGIDO,
)

#: Nota embutida no texto quando a extração foi parcial.
_NOTA_PARCIAL = (
    "[Nota de extração: o texto foi obtido parcialmente; {paginas} "
    "página(s) não pôde(ram) ser extraída(s). Mencione que a extração foi "
    "parcial ao resumir este documento.]"
)

#: Nota embutida no texto quando a leitura falhou criticamente.
_NOTA_FALHA = (
    "[Nota de extração: não foi possível extrair o texto deste documento "
    "por erro crítico de leitura. Mencione esta limitação ao resumir.]"
)

#: Nota embutida no texto quando o documento está protegido por senha.
_NOTA_PROTEGIDO = (
    "[Nota de extração: este documento é um PDF protegido por senha e não "
    "pôde ser lido. Mencione esta limitação ao resumir.]"
)

#: Resumo determinístico (sem LLM) quando não há texto a resumir.
_RESUMO_FALHA = (
    "Não foi possível extrair o texto deste documento por erro crítico de "
    "leitura; por isso não há resumo disponível."
)
_RESUMO_PROTEGIDO = (
    "Este documento é um PDF protegido por senha e não pôde ser lido; por "
    "isso não há resumo disponível."
)


@dataclass(frozen=True)
class ItemPendente:
    """Item de extração não conclusiva capturado no término do lote."""

    arquivo: DocumentoArquivo
    status: StatusExtracao
    texto: str = ""
    paginas_com_falha: int = 0


def nota_extracao(
    status: StatusExtracao, paginas_com_falha: int = 0
) -> str:
    """Monta a nota de extração que descreve a limitação do item.

    Distingue extração parcial (com a quantidade de páginas não extraídas),
    erro crítico de leitura e proteção por senha. Levanta ``ValueError`` para
    status que não são finalizáveis.
    """
    if status is StatusExtracao.PARCIAL:
        return _NOTA_PARCIAL.format(paginas=paginas_com_falha)
    if status is StatusExtracao.FALHA:
        return _NOTA_FALHA
    if status is StatusExtracao.PROTEGIDO:
        return _NOTA_PROTEGIDO
    raise ValueError(f"Status de extração não finalizável: {status!r}")


def texto_definitivo(
    status: StatusExtracao, texto: str, paginas_com_falha: int = 0
) -> str:
    """Compõe o texto persistido de um item finalizado como definitivo.

    No parcial, acrescenta a nota ao texto extraído; na falha e no protegido,
    o texto persistido é apenas a nota (não há texto a conservar).
    """
    nota = nota_extracao(status, paginas_com_falha)
    if status is StatusExtracao.PARCIAL and texto and texto.strip():
        return f"{texto}\n\n{nota}"
    return nota


def resumo_deterministico(status: StatusExtracao) -> ResumoDocumento:
    """Produz o resumo fixo (sem LLM) de um resultado sem texto.

    Termina em pontuação final para ser considerado íntegro por
    ``resumo_completo``. Levanta ``ValueError`` para status sem resumo
    determinístico (apenas ``FALHA`` e ``PROTEGIDO``).
    """
    if status is StatusExtracao.FALHA:
        mensagem = _RESUMO_FALHA
    elif status is StatusExtracao.PROTEGIDO:
        mensagem = _RESUMO_PROTEGIDO
    else:
        raise ValueError(f"Status sem resumo determinístico: {status!r}")
    return ResumoDocumento(short_summary=mensagem, long_summary=mensagem)
