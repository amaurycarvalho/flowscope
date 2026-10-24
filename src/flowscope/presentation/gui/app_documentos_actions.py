"""Leitura e aquisição dos documentos da sub-aba Documentos."""

from __future__ import annotations

from flowscope.application.documentos.aquisicao import ResultadoAquisicao
from flowscope.presentation.gui.atualizacao_mensagens import (
    mensagem_atualizacao,
    mensagem_documentos,
)
from flowscope.presentation.gui.background.events import Outcome
from flowscope.presentation.gui.background.job import Politica
from flowscope.presentation.gui.documentos_job import (
    GRUPO,
    POLITICA,
    ResultadoAtualizacao,
    executar_atualizacao,
    executar_documentos,
)

#: Grupo e política da leitura do catálogo de documentos (fora da aquisição).
GRUPO_LEITURA_DOCUMENTOS = "documentos-leitura"
POLITICA_LEITURA = Politica.LATEST_WINS


class DocumentosAquisicaoMixin:
    """Executa a leitura cache-only e a aquisição explícita de documentos."""

    def _update_documents(self: DocumentosAquisicaoMixin) -> None:
        """Submete a leitura do catálogo de documentos do ticker apresentado."""
        self._submeter_leitura_documentos(self._ticker_apresentado())

    def _submeter_leitura_documentos(
        self: DocumentosAquisicaoMixin, ticker: str | None
    ) -> None:
        """Lê o catálogo do ticker fora da thread do Tk e remonta por evento."""
        painel = getattr(self, "_documents_panel", None)
        if painel is None:
            return
        if not ticker:
            painel.aplicar_catalogo(None, None)
            return
        background = getattr(self, "_background", None)
        if background is None:
            painel.update(ticker)
            return
        painel.mostrar_carregando(ticker)

        def trabalho(ctx: object) -> None:
            catalogo = painel.carregar_catalogo(ticker)
            pendentes, guidances = painel.carregar_guidance(ticker, catalogo)
            sem_texto = painel.carregar_ausencia_catalogo(catalogo)
            inferencia = painel.carregar_inferencia_pendente(ticker)
            titulos = painel.carregar_titulos(ticker)
            ctx.resultado(
                valor=(
                    catalogo,
                    pendentes,
                    guidances,
                    sem_texto,
                    inferencia,
                    titulos,
                )
            )

        background.submit(
            trabalho,
            grupo=GRUPO_LEITURA_DOCUMENTOS,
            politica=POLITICA_LEITURA,
            chave=ticker,
            ao_resultado=lambda evento: self._aplicar_catalogo_documentos(
                ticker, evento.valor
            ),
        )

    def _aplicar_catalogo_documentos(
        self: DocumentosAquisicaoMixin, ticker: str | None, valor: object
    ) -> None:
        """Aplica o catálogo e o guidance se o ticker não mudou."""
        painel = getattr(self, "_documents_panel", None)
        if painel is None or ticker != self._ticker_apresentado():
            return
        catalogo, pendentes, guidances, sem_texto, *resto = valor
        pendente = bool(resto[0]) if resto else False
        titulos = resto[1] if len(resto) > 1 else None
        definir = getattr(painel, "definir_inferencia_pendente", None)
        if callable(definir):
            definir(pendente)
        painel.aplicar_catalogo(
            ticker, catalogo, pendentes, guidances, sem_texto, titulos
        )

    def _adquirir_documentos(
        self: DocumentosAquisicaoMixin, ticker: str
    ) -> None:
        """Adquire documentos (e títulos, quando ligados) em background."""
        painel = getattr(self, "_documents_panel", None)
        aquisicao = getattr(self, "_aquisicao_documentos", None)
        if painel is None:
            return
        if aquisicao is None or not ticker:
            self._submeter_leitura_documentos(ticker)
            return
        background = getattr(self, "_background", None)
        if background is None or background.tem_ativo(GRUPO):
            return
        painel.mostrar_carregando(ticker)
        deduplicar = getattr(self, "_deduplicar_documentos", None)
        aquisicao_titulos = getattr(self, "_aquisicao_titulos", None)
        estado: dict = {"resultado": ResultadoAquisicao()}

        def trabalho(ctx: object) -> None:
            estado["resultado"] = self._executar_aquisicao(
                ctx, aquisicao, aquisicao_titulos, ticker, deduplicar
            )

        background.submit(
            trabalho,
            grupo=GRUPO,
            politica=POLITICA,
            cancelavel=True,
            ao_progresso=lambda evento: self._presenter.on_progress(
                evento.atual, evento.total, evento.detalhe
            ),
            ao_termino=lambda evento: self._finalizar_documentos(
                ticker, evento, estado["resultado"]
            ),
        )

    def _executar_aquisicao(
        self: DocumentosAquisicaoMixin,
        ctx: object,
        aquisicao: object,
        aquisicao_titulos: object | None,
        ticker: str,
        deduplicar: object,
    ) -> object:
        """Executa documentos isoladamente ou junto da aquisição de títulos."""
        referencia = self._data_referencia()
        if aquisicao_titulos is None:
            return executar_documentos(
                ctx, aquisicao, ticker, referencia, deduplicar
            )
        return executar_atualizacao(
            ctx,
            aquisicao,
            aquisicao_titulos,
            ticker,
            referencia,
            deduplicar,
        )

    def _finalizar_documentos(
        self: DocumentosAquisicaoMixin,
        ticker: str,
        evento: object,
        resultado: object,
    ) -> None:
        """Relê o catálogo e informa o desfecho honesto da aquisição."""
        if ticker == self._ticker_apresentado():
            self._submeter_leitura_documentos(ticker)
        if evento.outcome is not Outcome.SUCESSO:
            return
        mensagem = (
            mensagem_atualizacao(resultado)
            if isinstance(resultado, ResultadoAtualizacao)
            else mensagem_documentos(resultado)
        )
        if isinstance(resultado, ResultadoAtualizacao) or mensagem[1]:
            self._flash_status(mensagem[0], mensagem[1])
        elif mensagem[0] == "Documentos atualizados!":
            self._flash_status(mensagem[0])
        else:
            self._flash_status(mensagem[0], mensagem[1])
