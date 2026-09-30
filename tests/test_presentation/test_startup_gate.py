"""Testes do gate de inicialização e do escudo de bloqueio.

A lógica (quando bloquear/liberar, ordem do release, idempotência, gate dos
atalhos e liberação robusta) é verificada headless com fakes de view/presenter.
Apenas a existência/remoção do overlay e a cobertura de cliques exigem Tk.
"""

import logging
import os
import time
import tkinter as tk
from unittest.mock import MagicMock

import pytest
from tkcalendar import DateEntry

from flowscope.presentation.gui.app_actions import ActionsMixin
from flowscope.presentation.gui.app_csv import CsvMixin
from flowscope.presentation.gui.app_tab_layout import TabsLayoutMixin
from flowscope.presentation.gui.presenter import FlowScopePresenter
from flowscope.presentation.gui.startup_gate import (
    MENSAGEM_INICIALIZACAO,
    TIMEOUT_GATE_MS,
    StartupGate,
    StartupGateMixin,
)

needs_display = pytest.mark.skipif(
    not os.environ.get("DISPLAY"),
    reason="Test requires a display (no DISPLAY env var)",
)


class _EscudoFake:
    """View fake que registra a presença do escudo."""

    def __init__(self) -> None:
        self.visivel = False
        self.colocados = 0
        self.removidos = 0

    def colocar_escudo(self) -> None:
        self.visivel = True
        self.colocados += 1

    def remover_escudo(self) -> None:
        self.visivel = False
        self.removidos += 1


class _PresenterFake:
    """Apresentador fake que registra o estado ocupado e emula a ociosidade."""

    def __init__(self) -> None:
        self.enters = 0
        self.exits = 0
        self._ativos = 0
        self._ocioso_callbacks = []

    def enter(self) -> None:
        self.enters += 1
        self._ativos += 1

    def exit(self) -> None:
        self.exits += 1
        if self._ativos > 0:
            self._ativos -= 1
        if self._ativos == 0:
            callbacks = self._ocioso_callbacks
            self._ocioso_callbacks = []
            for callback in callbacks:
                callback()

    def ao_ficar_ocioso(self, callback) -> None:
        if self._ativos == 0:
            callback()
            return
        self._ocioso_callbacks.append(callback)


class TestStartupGate:
    def test_escudo_colocado_antes_de_entrar_e_removido_ao_ficar_ocioso(self):
        eventos: list[str] = []
        idle: list = []

        class View:
            def colocar_escudo(self) -> None:
                eventos.append("colocar")

            def remover_escudo(self) -> None:
                eventos.append("remover")

        class Presenter:
            def enter(self) -> None:
                eventos.append("enter")

            def exit(self) -> None:
                eventos.append("exit")

            def ao_ficar_ocioso(self, callback) -> None:
                idle.append(callback)

        gate = StartupGate(View(), Presenter())
        gate.iniciar()
        assert eventos == ["colocar", "enter"]

        eventos.clear()
        gate.finalizar()
        assert eventos == ["exit"]
        assert idle

        idle[0]()
        assert eventos == ["exit", "remover"]

    def test_chamadas_repetidas_sao_idempotentes(self):
        view = _EscudoFake()
        presenter = _PresenterFake()
        gate = StartupGate(view, presenter)

        gate.iniciar()
        gate.iniciar()
        assert presenter.enters == 1
        assert view.colocados == 1
        assert gate.inicializando is True

        gate.finalizar()
        gate.finalizar()
        assert presenter.exits == 1
        assert view.removidos == 1
        assert gate.inicializando is False

    def test_finalizar_sem_iniciar_nao_desbalanceia(self):
        view = _EscudoFake()
        presenter = _PresenterFake()
        gate = StartupGate(view, presenter)

        gate.finalizar()
        assert presenter.exits == 0
        assert view.removidos == 0

    def test_release_mantem_ocupado_enquanto_job_background_roda(self):
        view = MagicMock()
        presenter = FlowScopePresenter(view)
        escudo = _EscudoFake()
        gate = StartupGate(escudo, presenter)

        gate.iniciar()
        assert escudo.visivel is True
        assert presenter._operacoes_ativas == 1

        presenter.enter()
        assert presenter._operacoes_ativas == 2

        gate.finalizar()
        assert escudo.visivel is True
        assert presenter._operacoes_ativas == 1
        view.restore_all_buttons.assert_not_called()
        view.exit_busy.assert_not_called()

        presenter.exit()
        assert presenter._operacoes_ativas == 0
        assert escudo.visivel is False
        view.restore_all_buttons.assert_called_once()
        view.exit_busy.assert_called_once()


class _GateHeadlessHost(StartupGateMixin):
    """Host headless do gate com escudo e agendador fake."""

    def __init__(self) -> None:
        self._presenter = _PresenterFake()
        self.after = MagicMock()
        self.escudo_visivel = False
        self.escudo_colocados = 0

    def colocar_escudo(self) -> None:
        self.escudo_visivel = True
        self.escudo_colocados += 1

    def remover_escudo(self) -> None:
        self.escudo_visivel = False


class TestStartupGateMixin:
    def test_iniciar_gate_ativa_antes_do_mainloop(self):
        host = _GateHeadlessHost()

        host.iniciar_gate()

        assert host._inicializando is True
        assert host.escudo_visivel is True
        assert host._presenter.enters == 1

    def test_iniciar_gate_repetido_nao_duplica_escudo(self):
        host = _GateHeadlessHost()

        host.iniciar_gate()
        host.iniciar_gate()

        assert host.escudo_colocados == 1
        assert host._presenter.enters == 1

    def test_after_de_seguranca_forca_release(self):
        host = _GateHeadlessHost()
        host.iniciar_gate()

        assert host.after.call_count == 1
        ms, callback = host.after.call_args[0]
        assert ms == TIMEOUT_GATE_MS

        callback()

        assert host._inicializando is False
        assert host.escudo_visivel is False
        assert host._presenter.exits == 1

    def test_after_de_seguranca_apos_release_e_noop(self):
        host = _GateHeadlessHost()
        host.iniciar_gate()
        _, callback = host.after.call_args[0]

        host.finalizar_gate()
        callback()

        assert host._presenter.exits == 1
        assert host.escudo_visivel is False


class _FakeNotebook:
    def __init__(self, textos: list[str]) -> None:
        self._textos = list(textos)
        self.selecionado = None

    def index(self, _arg=None):
        return len(self._textos)

    def tab(self, indice, _opcao):
        return self._textos[indice]

    def select(self, indice):
        self.selecionado = indice


class _RestoreHost(TabsLayoutMixin, StartupGateMixin):
    """Host headless que exercita a restauração inicial de abas."""

    def __init__(self, main, general, ticker, presenter, erro=False) -> None:
        self._main_notebook = main
        self._general_notebook = general
        self._ticker_notebook = ticker
        self._presenter = presenter
        self.after = MagicMock()
        self.escudo_visivel = False
        self.eventos: list[str] = []
        self._erro = erro

    def colocar_escudo(self) -> None:
        self.escudo_visivel = True
        self.eventos.append("colocar")

    def remover_escudo(self) -> None:
        self.escudo_visivel = False
        self.eventos.append("remover")

    def _on_tab_changed(self) -> None:
        self.eventos.append("tab")
        if self._erro:
            raise RuntimeError("falha na restauração")


def _hosts_restore(view, erro=False):
    main = _FakeNotebook(["Análise Geral", "Análise do Ticker", "Sobre"])
    general = _FakeNotebook(["Fundamentos", "VWAP"])
    ticker = _FakeNotebook(["Documentos"])
    presenter = FlowScopePresenter(view)
    return _RestoreHost(main, general, ticker, presenter, erro)


class TestRestoreTabsGate:
    def test_release_ocorre_apos_a_restauracao_inicial(self):
        view = MagicMock()
        host = _hosts_restore(view)
        host.iniciar_gate()
        host.eventos.clear()

        host._restore_tabs("Análise Geral", "VWAP")

        assert host.eventos == ["tab", "remover"]
        assert host._inicializando is False
        assert host.escudo_visivel is False
        view.restore_all_buttons.assert_called_once()
        view.exit_busy.assert_called_once()

    def test_falha_na_restauracao_libera_gate_e_registra(self, caplog):
        view = MagicMock()
        host = _hosts_restore(view, erro=True)
        host.iniciar_gate()

        with caplog.at_level(logging.ERROR, logger="flowscope"):
            host._restore_tabs("Análise Geral", "VWAP")

        assert host._inicializando is False
        assert host.escudo_visivel is False
        view.restore_all_buttons.assert_called_once()
        view.exit_busy.assert_called_once()
        assert "restaurar" in caplog.text.lower()


class _HandlerHost(ActionsMixin, CsvMixin):
    pass


class TestGateAtalhos:
    def test_load_data_ignorado_durante_inicializacao(self):
        host = _HandlerHost()
        host._controller = MagicMock()
        host._inicializando = True

        host._on_load_data()
        host._controller.on_load_data.assert_not_called()

        host._inicializando = False
        host._on_load_data()
        host._controller.on_load_data.assert_called_once()

    def test_copy_data_ignorado_durante_inicializacao(self):
        host = _HandlerHost()
        host._texto_para_copiar = MagicMock(return_value="")
        host._presenter = MagicMock()
        host._inicializando = True

        host._copy_data()
        host._texto_para_copiar.assert_not_called()

        host._inicializando = False
        host._copy_data()
        host._texto_para_copiar.assert_called_once()


class _GateUIHost(tk.Tk, StartupGateMixin):
    pass


@needs_display
class TestEscudoUI:
    """Testes de UI restritos à presença/cobertura do overlay."""

    def test_escudo_aparece_e_some(self):
        host = _GateUIHost()
        try:
            host._presenter = MagicMock()

            host.colocar_escudo()
            host.update()
            assert host._escudo is not None
            assert host._escudo.winfo_manager() == "place"
            assert host._escudo.cget("cursor") == "watch"

            mensagens = [
                w
                for w in host._escudo.winfo_children()
                if isinstance(w, tk.Label)
                and w.cget("text") == MENSAGEM_INICIALIZACAO
            ]
            assert len(mensagens) == 1
            assert mensagens[0].winfo_manager() == "place"

            host.remover_escudo()
            host.update()
            assert getattr(host, "_escudo", None) is None
            assert mensagens[0].winfo_exists() == 0
        finally:
            host.destroy()

    def test_escudo_cobre_barra_superior_de_data(self):
        host = _GateUIHost()
        try:
            host.geometry("400x300")
            host._presenter = MagicMock()
            barra = tk.Frame(host)
            barra.pack(side=tk.TOP, fill=tk.X)
            rotulo = tk.Label(barra, text="Data de referência:")
            rotulo.pack(side=tk.LEFT)
            entrada = DateEntry(barra)
            entrada.pack(side=tk.LEFT)
            host.update()

            host.colocar_escudo()
            host.update()

            for widget in (rotulo, entrada):
                x = widget.winfo_rootx() + widget.winfo_width() // 2
                y = widget.winfo_rooty() + widget.winfo_height() // 2
                assert host.winfo_containing(x, y) is host._escudo
        finally:
            host.destroy()

    def test_janela_construida_mantem_gate_ativo_antes_do_mainloop(self, monkeypatch):
        from flowscope.presentation.gui import app as app_mod

        monkeypatch.setattr(
            app_mod, "load_preferences", lambda: dict(app_mod.DEFAULT_CONFIG)
        )
        janela = app_mod.FlowScopeGUI()
        try:
            assert janela._inicializando is True
            assert janela._escudo is not None
            assert "disabled" in str(janela._date_entry.cget("state"))
        finally:
            janela.destroy()

    def test_statusbar_permanece_visivel_apos_o_release(self, monkeypatch):
        from flowscope.presentation.gui import app as app_mod

        monkeypatch.setattr(
            app_mod, "load_preferences", lambda: dict(app_mod.DEFAULT_CONFIG)
        )
        janela = app_mod.FlowScopeGUI()
        try:
            for _ in range(50):
                janela.update()
                time.sleep(0.01)
            janela.finalizar_gate()
            janela.update()
            assert janela._escudo is None
            assert janela._status_frame.winfo_ismapped() == 1
        finally:
            janela.destroy()

    def test_escudo_bloqueia_painel_sem_all_buttons(self):
        host = _GateUIHost()
        try:
            host.geometry("300x200")
            host._presenter = MagicMock()
            cliques: list[int] = []
            botao = tk.Button(host, text="Chat AI", command=lambda: cliques.append(1))
            botao.pack()
            host.update()

            host.colocar_escudo()
            host.update()

            x = botao.winfo_rootx() + botao.winfo_width() // 2
            y = botao.winfo_rooty() + botao.winfo_height() // 2
            no_ponto = host.winfo_containing(x, y)
            assert no_ponto is host._escudo
            assert host._escudo.winfo_width() == host.winfo_width()
            assert host._escudo.winfo_height() == host.winfo_height()
            assert cliques == []
        finally:
            host.destroy()
