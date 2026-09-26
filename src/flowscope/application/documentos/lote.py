"""Gancho de persistência do resumo em lote dos documentos.

Decide, para cada item, se o resumo deve ser gravado na própria thread de
trabalho (à prova de interrupção) ou apenas gerado para gravação posterior na
thread do Tk. O painel expõe os métodos do protocolo; a decisão vive aqui, na
camada de aplicação.
"""

from typing import Protocol

from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.domain.documents import DocumentoArquivo


class PainelLote(Protocol):
    """Contrato do painel usado pelo gancho de persistência do lote."""

    def persistir_no_lote(self: "PainelLote") -> bool:
        """Indica se o lote deve gravar o resumo na thread de trabalho."""
        ...

    def gerar_e_persistir(
        self: "PainelLote", arquivo: DocumentoArquivo, texto: str
    ) -> ResumoDocumento | None:
        """Gera o resumo e o grava no store, sem tocar em widgets."""
        ...

    def gerar_resumo_estrito(
        self: "PainelLote", arquivo: DocumentoArquivo, texto: str
    ) -> ResumoDocumento | None:
        """Gera o resumo propagando falhas, sem gravar."""
        ...


def gerar_resumo_do_lote(
    painel: PainelLote, arquivo: DocumentoArquivo, texto: str
) -> ResumoDocumento | None:
    """Gera o resumo pelo caminho exigido pelo painel.

    Painéis que gravam no worker chamam ``gerar_e_persistir``; os demais apenas
    geram e deixam a gravação para a thread do Tk.
    """
    if painel.persistir_no_lote():
        return painel.gerar_e_persistir(arquivo, texto)
    return painel.gerar_resumo_estrito(arquivo, texto)
