"""Aquisição das notícias da sub-aba "Notícias" em segundo plano.

O mixin submete a aquisição ao gerenciador de background, traduz o progresso
para a barra de status e remonta a árvore ao final. Vive separado de
:mod:`app_actions` para manter a complexidade sob controle.
"""

from flowscope.presentation.gui.background.job import Politica
from flowscope.presentation.gui.noticias_job import (
    GRUPO,
    POLITICA,
    executar_noticias,
)

#: Grupo e política da leitura do cache local das notícias.
GRUPO_LEITURA = "noticias-leitura"
POLITICA_LEITURA = Politica.LATEST_WINS


class NoticiasActionsMixin:
    """Adquire as notícias e mantém a sub-aba "Notícias" atualizada."""

    def _update_noticias(self: "NoticiasActionsMixin") -> None:
        """Lê o cache local fora da thread do Tk e remonta a árvore por evento."""
        self._submeter_leitura_noticias(self._data_referencia())

    def _submeter_leitura_noticias(
        self: "NoticiasActionsMixin", reference_date: object
    ) -> None:
        """Submete a leitura do cache local das notícias ao gerenciador."""
        painel = getattr(self, "_noticias_panel", None)
        if painel is None:
            return
        painel.definir_referencia(reference_date)
        background = getattr(self, "_background", None)
        if background is None:
            painel.update(reference_date)
            return
        painel.mostrar_carregando()
        background.submit(
            lambda ctx: ctx.resultado(valor=painel.carregar_secoes()),
            grupo=GRUPO_LEITURA,
            politica=POLITICA_LEITURA,
            ao_resultado=lambda evento: painel.aplicar_secoes(evento.valor),
        )

    def _adquirir_noticias(self: "NoticiasActionsMixin") -> None:
        """Adquire as notícias do período em background e remonta a árvore."""
        painel = getattr(self, "_noticias_panel", None)
        aquisicao = getattr(self, "_aquisicao_noticias", None)
        if painel is None:
            return
        if aquisicao is None:
            self._submeter_leitura_noticias(self._data_referencia())
            return
        background = getattr(self, "_background", None)
        if background is None or background.tem_ativo(GRUPO):
            return
        painel.mostrar_carregando()
        deduplicar = getattr(self, "_deduplicar_noticias", None)
        background.submit(
            lambda ctx: executar_noticias(
                ctx, aquisicao, self._data_referencia(), deduplicar
            ),
            grupo=GRUPO,
            politica=POLITICA,
            cancelavel=True,
            ao_progresso=lambda evento: self._presenter.on_progress(
                evento.atual, evento.total, evento.detalhe
            ),
            ao_termino=lambda evento: self._finalizar_noticias(
                evento.cancelado
            ),
        )

    def _finalizar_noticias(
        self: "NoticiasActionsMixin", cancelado: bool
    ) -> None:
        """Agenda a remontagem pelo término do job e informa o desfecho.

        A remontagem é agendada com ``after(0)`` para rodar depois de o
        gerenciador remover o job, quando eventuais gravações do worker já
        terminaram. Não há polling da thread de trabalho na thread do Tk.
        """
        self.after(0, self._remontar_noticias)
        if not cancelado:
            self._flash_status("Notícias atualizadas!")

    def _remontar_noticias(self: "NoticiasActionsMixin") -> None:
        """Relê e remonta a árvore, exceto se uma aquisição nova estiver ativa.

        Preserva a precedência da carga mais recente: se um novo "Atualizar" já
        tiver começado, a remontagem do job encerrado não sobrescreve a árvore.
        """
        background = getattr(self, "_background", None)
        if background is not None and background.tem_ativo(GRUPO):
            return
        self._submeter_leitura_noticias(self._data_referencia())
