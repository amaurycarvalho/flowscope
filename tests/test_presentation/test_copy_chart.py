"""Testes da cópia de gráfico: rendering no Tk e transferência em background."""

import threading
from pathlib import Path
from unittest.mock import MagicMock

from flowscope.application.clipboard_port import ClipboardError
from flowscope.presentation.gui.app_actions import GRUPO_CLIPBOARD, ActionsMixin
from flowscope.presentation.gui.background.manager import BackgroundManager
from flowscope.presentation.gui.presenter import FlowScopePresenter

_CAMINHO = Path("/tmp/flowscope_chart.png")


class _ClipboardFake:
    def __init__(
        self,
        erro: Exception | None = None,
        liberar: threading.Event | None = None,
    ) -> None:
        self.salvos: list = []
        self.transferidos: list = []
        self.erro = erro
        self.liberar = liberar

    def salvar_png(self, figure):
        self.salvos.append(figure)
        return _CAMINHO

    def transferir_png(self, path):
        if self.liberar is not None:
            self.liberar.wait(2)
        if self.erro is not None:
            raise self.erro
        self.transferidos.append(path)

    def copy_image(self, figure):
        self.salvos.append(figure)
        self.transferidos.append(_CAMINHO)


class _Host(ActionsMixin):
    def __init__(self, background=None, clipboard=None) -> None:
        self._clipboard = clipboard
        self._background = background
        self._presenter = MagicMock()
        self.eventos: list = []

    def _flash_status(self, msg, icon="✓", clear_ms=2500) -> None:
        self.eventos.append(msg)

    def _set_status(self, msg, icon="") -> None:
        self.eventos.append((msg, icon))


def _drenar(background: BackgroundManager, rounds: int = 5) -> None:
    for _ in range(rounds):
        handles = list(background.jobs_ativos)
        if not handles:
            break
        for handle in handles:
            if handle.thread is not None:
                handle.thread.join(2)
        background.drenar()


class TestCopyChartAsync:
    def test_rendering_no_tk_e_transferencia_no_worker(self):
        liberar = threading.Event()
        background = BackgroundManager()
        clipboard = _ClipboardFake(liberar=liberar)
        host = _Host(background, clipboard)

        host._copy_chart(object())

        assert len(clipboard.salvos) == 1
        assert clipboard.transferidos == []
        assert background.tem_ativo(GRUPO_CLIPBOARD) is True

        liberar.set()
        _drenar(background)

        assert clipboard.transferidos == [_CAMINHO]
        assert host.eventos == ["Gráfico copiado!"]

    def test_erro_de_clipboard_vira_status(self):
        background = BackgroundManager()
        clipboard = _ClipboardFake(erro=ClipboardError("xclip ausente"))
        host = _Host(background, clipboard)

        host._copy_chart(object())
        _drenar(background)

        assert host.eventos == [("Erro: xclip ausente", "⚠")]

    def test_erro_ao_salvar_vira_status_sem_submeter(self):
        class _Falha(_ClipboardFake):
            def salvar_png(self, figure):
                raise ClipboardError("sem espaço")

        background = BackgroundManager()
        host = _Host(background, _Falha())

        host._copy_chart(object())

        assert host.eventos == [("Erro: sem espaço", "⚠")]
        assert background.jobs_ativos == ()

    def test_sem_background_copia_sincrono(self):
        host = _Host(None, _ClipboardFake())

        host._copy_chart(object())

        assert host.eventos == ["Gráfico copiado!"]

    def test_sem_porta_nao_falha(self):
        host = _Host(BackgroundManager(), None)
        host._clipboard = None

        host._copy_chart(object())

        assert host.eventos == []

    def test_controles_restaurados_ao_fim(self):
        liberar = threading.Event()
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        background = BackgroundManager()
        background.ao_iniciar(lambda handle: presenter.enter())
        background.ao_terminar(lambda handle: presenter.exit())
        host = _Host(background, _ClipboardFake(liberar=liberar))
        host._presenter = presenter

        host._copy_chart(object())
        assert presenter._operacoes_ativas >= 1

        liberar.set()
        _drenar(background)

        assert presenter._operacoes_ativas == 0
        view.restore_all_buttons.assert_called_once()
        view.exit_busy.assert_called_once()
