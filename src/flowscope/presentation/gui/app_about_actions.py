"""Ações da aba "Sobre": atalhos externos e verificação de nova versão."""

import logging
import webbrowser

from flowscope import __version__
from flowscope.application.releases import ReleaseChecker, verificar_nova_versao
from flowscope.presentation.gui.background.context import JobContext
from flowscope.presentation.gui.background.job import Politica
from flowscope.presentation.gui.document_actions import abrir_no_aplicativo
from flowscope.presentation.gui.widgets.about_panel import REPOSITORIO_URL
from flowscope.presentation.log_paths import log_file_path

logger = logging.getLogger("flowscope")

#: Grupo de exclusão da verificação de nova versão.
GRUPO_VERSAO = "versao"


class AboutActionsMixin:
    """Lida com os atalhos e a verificação de versão da aba "Sobre"."""

    #: Consulta a última release; injetada pelo composition root.
    _release_checker: ReleaseChecker | None = None

    def _abrir_url(self: "AboutActionsMixin", url: str) -> None:
        """Abre ``url`` no navegador padrão, informando falhas na barra de status."""
        try:
            webbrowser.open(url)
        except webbrowser.Error:
            self._set_status("Não foi possível abrir o navegador.", "⚠")

    def _abrir_repositorio(self: "AboutActionsMixin") -> None:
        """Abre o repositório do projeto no navegador padrão."""
        self._abrir_url(REPOSITORIO_URL)

    def _abrir_log_flowscope(self: "AboutActionsMixin") -> None:
        """Abre o log no aplicativo padrão ou informa a ausência na barra de status."""
        caminho = log_file_path()
        if not caminho.exists():
            self._set_status("O log da aplicação ainda não está disponível.", "⚠")
            return
        try:
            abrir_no_aplicativo(caminho)
        except OSError:
            self._set_status("Não foi possível abrir o log da aplicação.", "⚠")

    def _verificar_nova_versao(self: "AboutActionsMixin") -> None:
        """Dispara, uma vez por sessão, a verificação de nova versão em background."""
        if getattr(self, "_update_checked", False):
            return
        self._update_checked = True
        background = getattr(self, "_background", None)
        if background is None:
            return
        background.submit(
            self._consultar_versao_publicada,
            grupo=GRUPO_VERSAO,
            politica=Politica.PARALLEL,
            ao_resultado=lambda evento: self._notificar_nova_versao(
                *evento.valor
            ),
        )

    def _consultar_versao_publicada(self: "AboutActionsMixin", ctx: JobContext) -> None:
        """Consulta a última release e publica o aviso como evento."""
        checker = self._release_checker
        if checker is None:
            return
        try:
            resultado = verificar_nova_versao(__version__, checker)
        except Exception:
            logger.warning("Falha inesperada na verificação de versão", exc_info=True)
            return
        if resultado is None:
            return
        ctx.resultado(valor=resultado)

    def _notificar_nova_versao(
        self: "AboutActionsMixin", versao: str, url: str
    ) -> None:
        """Exibe o aviso de nova versão no painel "Sobre"."""
        painel = getattr(self, "_about_panel", None)
        if painel is None:
            return
        painel.show_update(versao, lambda: self._abrir_url(url))
