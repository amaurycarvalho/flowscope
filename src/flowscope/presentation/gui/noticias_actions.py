"""Aquisição das notícias da sub-aba "Notícias" em segundo plano.

O mixin conduz o job de aquisição em uma thread, drena a fila na thread do Tk,
traduz o progresso para a barra de status e remonta a árvore ao final. Vive
separado de :mod:`app_actions` para manter a complexidade sob controle.
"""

import logging
import queue
import time

from flowscope.presentation.gui.noticias_job import MENSAGEM_PROGRESSO, NoticiasJob

logger = logging.getLogger("flowscope")

#: Tempo máximo sem progresso antes de encerrar a aquisição de notícias.
_LIMITE_INATIVIDADE_NOTICIAS_S = 120.0


class NoticiasActionsMixin:
    """Adquire as notícias e mantém a sub-aba "Notícias" atualizada."""

    def _update_noticias(self: "NoticiasActionsMixin") -> None:
        """Preenche o painel de notícias a partir do cache do período."""
        painel = getattr(self, "_noticias_panel", None)
        if painel is not None:
            painel.update(self._data_referencia())

    def _adquirir_noticias(self: "NoticiasActionsMixin") -> None:
        """Adquire as notícias do período em thread e remonta a árvore."""
        painel = getattr(self, "_noticias_panel", None)
        aquisicao = getattr(self, "_aquisicao_noticias", None)
        if painel is None:
            return
        if aquisicao is None:
            painel.update(self._data_referencia())
            return
        if getattr(self, "_noticias_job", None) is not None:
            return
        painel.mostrar_carregando()
        job = NoticiasJob(
            aquisicao,
            self._data_referencia(),
            cancel_token=self._presenter.cancel_token,
        )
        self._noticias_job = job
        self._presenter.on_operation_started()
        self._presenter.job_cancelavel_iniciado()
        self._noticias_ultima_atividade = time.monotonic()
        try:
            job.iniciar()
        except Exception:
            logger.warning(
                "Falha ao iniciar a aquisição de notícias", exc_info=True
            )
            if getattr(self, "_noticias_job", None) is job:
                self._noticias_job = None
            self._presenter.job_cancelavel_finalizado()
            self._presenter.on_operation_finished()
            return
        self._poll_noticias_job(job)

    def _poll_noticias_job(self: "NoticiasActionsMixin", job: NoticiasJob) -> None:
        """Consome a fila do job na thread do Tk até a aquisição concluir."""
        terminou = self._drenar_fila_noticias(job)
        if not terminou and self._cancelamento_solicitado():
            terminou = True
        if not terminou and self._noticias_job_travado(job):
            logger.warning(
                "Aquisição de notícias sem progresso; encerrando para "
                "restaurar a interface."
            )
            terminou = True
        if terminou:
            self._finalizar_noticias_job(job)
            return
        self.after(50, lambda: self._poll_noticias_job(job))

    def _drenar_fila_noticias(self: "NoticiasActionsMixin", job: NoticiasJob) -> bool:
        """Esvazia a fila do job e informa se ele foi concluído."""
        terminou = False
        try:
            while True:
                mensagem = job.fila.get_nowait()
                if self._mensagem_de_progresso_noticias(mensagem):
                    self._tratar_progresso_noticias(mensagem)
                else:
                    terminou = True
        except queue.Empty:
            pass
        return terminou

    @staticmethod
    def _mensagem_de_progresso_noticias(mensagem: object) -> bool:
        """Indica se a mensagem é de progresso da aquisição de notícias."""
        return (
            isinstance(mensagem, tuple)
            and bool(mensagem)
            and mensagem[0] == MENSAGEM_PROGRESSO
        )

    def _tratar_progresso_noticias(
        self: "NoticiasActionsMixin", mensagem: tuple
    ) -> None:
        """Repassa o progresso ao presenter, registrando falhas sem abortar."""
        try:
            _tipo, current, total, label = mensagem
            self._noticias_ultima_atividade = time.monotonic()
            self._presenter.on_progress(current, total, label)
        except Exception:
            logger.exception("Erro ao tratar progresso da aquisição de notícias")

    def _finalizar_noticias_job(self: "NoticiasActionsMixin", job: NoticiasJob) -> None:
        """Encerra o job, remonta a árvore e libera o estado ocupado."""
        if getattr(self, "_noticias_job", None) is job:
            self._noticias_job = None
        painel = getattr(self, "_noticias_panel", None)
        if painel is not None:
            painel.update(self._data_referencia())
        self._presenter.job_cancelavel_finalizado()
        self._presenter.on_operation_finished()
        if not self._cancelamento_solicitado():
            self._flash_status("Notícias atualizadas!")

    def _noticias_job_travado(self: "NoticiasActionsMixin", job: NoticiasJob) -> bool:
        """Indica se o job morreu ou ficou sem progresso por tempo demais."""
        thread = getattr(job, "thread", None)
        if thread is not None and not thread.is_alive() and job.fila.empty():
            return True
        ultima = getattr(self, "_noticias_ultima_atividade", None)
        if ultima is None:
            return False
        return time.monotonic() - ultima > _LIMITE_INATIVIDADE_NOTICIAS_S
