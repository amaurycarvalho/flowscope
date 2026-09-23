"""Ações da aba "Sobre": atalhos externos e verificação de nova versão."""

import logging
import threading
import webbrowser

from flowscope import __version__
from flowscope.domain.version import is_newer
from flowscope.infrastructure.releases import obter_ultima_release
from flowscope.presentation.gui.document_actions import abrir_no_aplicativo
from flowscope.presentation.gui.widgets.about_panel import REPOSITORIO_URL
from flowscope.presentation.log_paths import log_file_path

logger = logging.getLogger("flowscope")


class AboutActionsMixin:
    """Lida com os atalhos e a verificação de versão da aba "Sobre"."""

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
        threading.Thread(
            target=self._consultar_versao_publicada, daemon=True
        ).start()

    def _consultar_versao_publicada(self: "AboutActionsMixin") -> None:
        """Consulta a última release e publica o aviso na thread da interface."""
        try:
            resultado = obter_ultima_release()
        except Exception:
            logger.warning("Falha inesperada na verificação de versão", exc_info=True)
            return
        if resultado is None:
            return
        versao, url = resultado
        if not is_newer(versao, __version__):
            return
        self.after(0, lambda: self._notificar_nova_versao(versao, url))

    def _notificar_nova_versao(
        self: "AboutActionsMixin", versao: str, url: str
    ) -> None:
        """Exibe o aviso de nova versão no painel "Sobre"."""
        painel = getattr(self, "_about_panel", None)
        if painel is None:
            return
        painel.show_update(versao, lambda: self._abrir_url(url))
