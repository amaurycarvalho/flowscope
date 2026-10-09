"""Orquestração do resumo em lote dos documentos e notícias pendentes.

O mixin submete o lote ao gerenciador de background, traduz o progresso para a
barra de status e aplica os resultados no painel de origem. Vive separado de
:mod:`app_actions` para manter a complexidade e o tamanho de cada módulo sob
controle.
"""

import logging
import time

from flowscope.presentation.gui.background.events import Erro, Progresso, Resultado
from flowscope.presentation.gui.llm.mensagens import mensagem_erro_llm
from flowscope.presentation.gui.progress import ProgressReporter
from flowscope.presentation.gui.resumos_job import (
    GRUPO,
    POLITICA,
    executar_resumos,
)

logger = logging.getLogger("flowscope")


class ResumosActionsMixin:
    """Conduz o resumo em lote dos documentos e das notícias pendentes."""

    def _resumos_em_andamento(self: "ResumosActionsMixin") -> bool:
        """Indica se há um resumo em lote em andamento."""
        background = getattr(self, "_background", None)
        return background is not None and background.tem_ativo(GRUPO)

    def _noticias_resumos_em_andamento(self: "ResumosActionsMixin") -> bool:
        """Indica se há um resumo em lote em andamento (notícias)."""
        return self._resumos_em_andamento()

    def _resumir_documentos_pendentes(self: "ResumosActionsMixin") -> None:
        """Gera em lote os resumos dos documentos pendentes do ticker."""
        painel = getattr(self, "_documents_panel", None)
        if painel is None:
            return
        if self._resumos_em_andamento():
            return
        sem_resumo = painel.documentos_sem_resumo()
        pendentes_guidance = getattr(
            painel, "documentos_pendentes_guidance", list
        )()
        pendentes = list(sem_resumo) + list(pendentes_guidance)
        if not pendentes:
            painel.refresh_resumir_button()
            return
        self._iniciar_lote_resumos(painel, pendentes, self._ticker_apresentado())

    def _resumir_noticias_pendentes(self: "ResumosActionsMixin") -> None:
        """Gera em lote os resumos das notícias pendentes do período."""
        painel = getattr(self, "_noticias_panel", None)
        if painel is None:
            return
        if self._resumos_em_andamento():
            return
        pendentes = painel.pendentes_ordenados()
        if not pendentes:
            painel.refresh_resumir_button()
            return
        self._iniciar_lote_resumos(painel, pendentes, None, continuar=True)

    def _iniciar_lote_resumos(
        self: "ResumosActionsMixin",
        painel: object,
        pendentes: list,
        guarda: object,
        continuar: bool = False,
    ) -> None:
        """Submete o lote de resumo e registra os callbacks de eventos."""
        background = getattr(self, "_background", None)
        if background is None:
            return
        self._resumos_painel = painel
        self._resumos_continuar = continuar
        self._resumos_falhas = 0
        self._resumos_resumidos = 0
        self._resumos_total = len(pendentes)
        self._resumos_persistir_worker = self._painel_persiste_no_worker(painel)
        self._resumos_fase = None
        self._resumos_fase_inicio = None
        self._resumos_interrompido = False
        self._resumos_reporter = ProgressReporter(
            on_update=self._presenter.on_progress
        )
        self._set_status(f"Resumindo {len(pendentes)} item(ns)…")
        estado = {"sem_texto": 0}

        def trabalho(ctx: object) -> None:
            estado["sem_texto"] = executar_resumos(
                ctx, painel, pendentes, continuar
            )

        background.submit(
            trabalho,
            grupo=GRUPO,
            politica=POLITICA,
            cancelavel=True,
            ao_progresso=self._tratar_progresso_resumos,
            ao_resultado=lambda evento: self._aplicar_resultado_resumo(
                evento, guarda
            ),
            ao_erro=self._interromper_resumos,
            ao_termino=lambda evento: self._finalizar_resumos_job(
                evento.cancelado, guarda, estado["sem_texto"]
            ),
        )

    def _tratar_progresso_resumos(
        self: "ResumosActionsMixin", evento: Progresso
    ) -> None:
        """Traduz o progresso do lote para o relator de fases."""
        reporter = getattr(self, "_resumos_reporter", None)
        if reporter is None:
            return
        detalhe = f"{evento.atual}/{evento.total}"
        if evento.dados != getattr(self, "_resumos_fase", None):
            self._resumos_fase = evento.dados
            self._resumos_fase_inicio = time.monotonic()
            reporter.start_phase(evento.detalhe, evento.total, weight=1)
            reporter.advance(0, detalhe)
        elif evento.atual and evento.atual > 0:
            reporter.advance(1, detalhe)

    def _painel_resumos(self: "ResumosActionsMixin") -> object | None:
        """Retorna o painel de origem do lote corrente."""
        painel = getattr(self, "_resumos_painel", None)
        if painel is not None:
            return painel
        return getattr(self, "_documents_panel", None)

    def _painel_persiste_no_worker(self: "ResumosActionsMixin", painel: object) -> bool:
        """Indica se o painel grava o resumo na thread de trabalho do lote."""
        metodo = getattr(painel, "persistir_no_lote", None)
        return bool(metodo()) if metodo is not None else False

    def _aplicar_resultado_resumo(
        self: "ResumosActionsMixin", evento: Resultado, guarda: object
    ) -> None:
        """Aplica um resumo e a avaliação de guidance, descartando se o escopo mudou."""
        arquivo = evento.dados
        resumo, avaliacao = evento.valor
        if guarda is not None and guarda != self._ticker_apresentado():
            return
        painel = self._painel_resumos()
        if painel is None:
            return
        if resumo is None:
            if avaliacao is not None:
                painel.refletir_guidance(arquivo, avaliacao)
            return
        if getattr(self, "_resumos_persistir_worker", False):
            painel.refletir_resumo(arquivo, resumo, avaliacao)
        else:
            painel.aplicar_resumo(arquivo, resumo, avaliacao)
        self._resumos_resumidos = getattr(self, "_resumos_resumidos", 0) + 1

    def _interromper_resumos(self: "ResumosActionsMixin", evento: Erro) -> None:
        """Registra e reporta uma falha do lote por item."""
        arquivo = evento.dados
        exc = evento.excecao
        if getattr(self, "_resumos_continuar", False):
            self._resumos_falhas = getattr(self, "_resumos_falhas", 0) + 1
        else:
            self._resumos_interrompido = True
        logger.error(
            "Falha no resumo em lote em %s: %s",
            arquivo.caminho,
            exc,
            exc_info=exc,
        )
        self._set_status(f"{arquivo.nome}: {mensagem_erro_llm(exc)}", "⚠")

    def _finalizar_resumos_job(
        self: "ResumosActionsMixin",
        cancelado: bool,
        guarda: object,
        sem_texto: int,
    ) -> None:
        """Encerra o lote, libera o estado ocupado e exibe o desfecho."""
        self.after(0, self._recarregar_painel_resumos)
        if cancelado:
            self._resumos_interrompido = True
        painel = self._painel_resumos()
        if painel is not None:
            painel.refresh_resumir_button()
        if getattr(self, "_resumos_interrompido", False):
            return
        if guarda is not None and guarda != self._ticker_apresentado():
            return
        total = getattr(self, "_resumos_total", 0)
        resumidos = getattr(self, "_resumos_resumidos", 0)
        if getattr(self, "_resumos_continuar", False):
            falhas = getattr(self, "_resumos_falhas", 0)
            mensagem = (
                f"Resumos gerados: {resumidos} de {total} "
                f"({sem_texto} sem texto, {falhas} falha(s))."
            )
        else:
            mensagem = (
                f"Resumos gerados: {resumidos} de {total} "
                f"({sem_texto} sem texto)."
            )
        self._flash_status(mensagem, "✓")

    def _recarregar_painel_resumos(self: "ResumosActionsMixin") -> None:
        """Remonta o painel de origem do lote a partir do cache atualizado.

        A remontagem é adiada para depois de o gerenciador remover o job — quando
        eventuais gravações do worker já terminaram — e reusa a leitura fora da
        thread do Tk. Notícias (lote contínuo) e documentos são despachados por
        origem.
        """
        if getattr(self, "_resumos_continuar", False):
            self._submeter_leitura_noticias(self._data_referencia())
        else:
            self._submeter_leitura_documentos(self._ticker_apresentado())
