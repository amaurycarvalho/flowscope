"""Aquisição das notícias da sub-aba "Notícias" em segundo plano.

O mixin submete a aquisição ao gerenciador de background, traduz o progresso
para a barra de status e remonta a árvore ao final. Vive separado de
:mod:`app_actions` para manter a complexidade sob controle.
"""

from flowscope.presentation.gui.noticias_job import (
    GRUPO,
    POLITICA,
    executar_noticias,
)

#: Número máximo de reagendamentos da remontagem após cancelamento (~30s).
_LIMITE_REMONTAGEM = 300


class NoticiasActionsMixin:
    """Adquire as notícias e mantém a sub-aba "Notícias" atualizada."""

    def _update_noticias(self: "NoticiasActionsMixin") -> None:
        """Preenche o painel de notícias a partir do cache do período."""
        painel = getattr(self, "_noticias_panel", None)
        if painel is not None:
            painel.update(self._data_referencia())

    def _adquirir_noticias(self: "NoticiasActionsMixin") -> None:
        """Adquire as notícias do período em background e remonta a árvore."""
        painel = getattr(self, "_noticias_panel", None)
        aquisicao = getattr(self, "_aquisicao_noticias", None)
        if painel is None:
            return
        if aquisicao is None:
            painel.update(self._data_referencia())
            return
        background = getattr(self, "_background", None)
        if background is None or background.tem_ativo(GRUPO):
            return
        painel.mostrar_carregando()
        referencia: dict = {}
        referencia["handle"] = background.submit(
            lambda ctx: executar_noticias(
                ctx, aquisicao, self._data_referencia()
            ),
            grupo=GRUPO,
            politica=POLITICA,
            cancelavel=True,
            ao_progresso=lambda evento: self._presenter.on_progress(
                evento.atual, evento.total, evento.detalhe
            ),
            ao_termino=lambda evento: self._finalizar_noticias(
                referencia.get("handle"), evento.cancelado
            ),
        )

    def _finalizar_noticias(
        self: "NoticiasActionsMixin", handle: object, cancelado: bool
    ) -> None:
        """Encerra o job, remonta a árvore e libera o estado ocupado.

        Em cancelamento, o worker pode ainda estar terminando o item corrente e
        gravando no índice os metadados acumulados. Como a árvore lê o índice, a
        remontagem é repetida quando a thread encerrar, refletindo a carga
        parcial recém-persistida.
        """
        self._remontar_noticias()
        if cancelado:
            self._reagendar_remontagem(handle)
        else:
            self._flash_status("Notícias atualizadas!")

    def _remontar_noticias(self: "NoticiasActionsMixin") -> None:
        """Remonta a árvore de notícias a partir do cache local."""
        painel = getattr(self, "_noticias_panel", None)
        if painel is not None:
            painel.update(self._data_referencia())

    def _reagendar_remontagem(
        self: "NoticiasActionsMixin", handle: object, tentativas: int = 0
    ) -> None:
        """Remonta a árvore de novo quando o worker de cancelamento encerrar.

        Enquanto a thread estiver viva, a remontagem é adiada; ao encerrar (ou
        ao esgotar o limite), a árvore é remontada uma última vez — desde que
        nenhum novo "Atualizar" tenha começado, para não sobrescrever a carga
        mais recente.
        """
        thread = getattr(handle, "thread", None)
        if (
            thread is not None
            and thread.is_alive()
            and tentativas < _LIMITE_REMONTAGEM
        ):
            self.after(
                100, lambda: self._reagendar_remontagem(handle, tentativas + 1)
            )
            return
        background = getattr(self, "_background", None)
        if background is None or not background.tem_ativo(GRUPO):
            self._remontar_noticias()
