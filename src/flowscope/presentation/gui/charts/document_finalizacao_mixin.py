"""Orçamento de extração e persistência do texto/resumo definitivos.

Concentra o orçamento de tempo da extração e os ganchos usados pela finalização
explícita de extrações não conclusivas, mantendo o fluxo de pré-visualização
(:mod:`document_flow_mixin`) enxuto. Os ganchos não tocam em widgets: são
seguros para uso na thread de trabalho do lote.
"""

from flowscope.application.document_preview import StatusExtracao
from flowscope.application.extracao_orcada import EXTRACAO_TIMEOUT_S
from flowscope.application.finalizacao_extracao import texto_definitivo
from flowscope.application.resumo_documento import ResumoDocumento
from flowscope.domain.documents import DocumentoArquivo


class DocumentFinalizacaoMixin:
    """Orçamento de extração e persistência do texto/resumo definitivos."""

    def timeout_extracao(self: "DocumentFinalizacaoMixin") -> float:
        """Retorna o orçamento de tempo da extração, ajustável em memória."""
        return float(getattr(self, "_extracao_timeout", EXTRACAO_TIMEOUT_S))

    def definir_timeout_extracao(
        self: "DocumentFinalizacaoMixin", segundos: float
    ) -> None:
        """Ajusta em memória o orçamento de tempo da extração do painel."""
        self._extracao_timeout = float(segundos)

    def persistir_texto_definitivo(
        self: "DocumentFinalizacaoMixin",
        arquivo: DocumentoArquivo,
        status: StatusExtracao,
        texto: str,
        paginas_com_falha: int = 0,
    ) -> str:
        """Grava o texto definitivo de um item finalizado explicitamente.

        Monta a nota de extração (``texto + nota`` no parcial; apenas a nota na
        falha e no protegido), grava no cache de texto e memoiza o resultado.
        """
        definitivo = texto_definitivo(status, texto, paginas_com_falha)
        self._text_store.salvar(
            arquivo.ticker, self._summary.chave(arquivo), definitivo
        )
        self._preview_cache[arquivo.caminho] = definitivo
        return definitivo

    def persistir_resumo_definitivo(
        self: "DocumentFinalizacaoMixin",
        arquivo: DocumentoArquivo,
        resumo: ResumoDocumento,
    ) -> None:
        """Grava um resumo já produzido (caminho determinístico), sem widgets."""
        self._summary.persistir(arquivo, resumo)
