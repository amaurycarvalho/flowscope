"""Testes da verificação de nova versão e das ações da aba "Sobre"."""

import webbrowser
from unittest.mock import MagicMock, patch

from flowscope.presentation.gui.app_about_actions import AboutActionsMixin
from flowscope.presentation.gui.widgets.about_panel import REPOSITORIO_URL

_MODULO = "flowscope.presentation.gui.app_about_actions"


class _ThreadImediata:
    """Executa o alvo da thread de forma síncrona, evitando corridas nos testes."""

    def __init__(self, target=None, daemon=None, **kwargs):
        self._target = target

    def start(self):
        self._target()


class _Host(AboutActionsMixin):
    def __init__(self, panel=None):
        self._update_checked = False
        self._about_panel = panel if panel is not None else MagicMock()
        self.status = []

    def _set_status(self, msg, icon=""):
        self.status.append(msg)

    def after(self, _ms, callback):
        callback()


def _executar_verificacao(resultado=None):
    host = _Host()
    with patch(f"{_MODULO}.obter_ultima_release", return_value=resultado):
        with patch(f"{_MODULO}.threading.Thread", _ThreadImediata):
            host._verificar_nova_versao()
    return host


class TestVerificacaoUmaVezPorSessao:
    def test_primeira_verificacao_memoiza(self):
        host = _Host()
        with patch(f"{_MODULO}.obter_ultima_release", return_value=None) as consulta:
            with patch(f"{_MODULO}.threading.Thread", _ThreadImediata):
                host._verificar_nova_versao()
                host._verificar_nova_versao()
        consulta.assert_called_once()
        assert host._update_checked is True


class TestNotificacaoDeNovaVersao:
    def test_versao_mais_nova_notifica(self):
        host = _executar_verificacao(("9.9.9", "http://release"))
        host._about_panel.show_update.assert_called_once()
        args = host._about_panel.show_update.call_args.args
        assert args[0] == "9.9.9"
        assert callable(args[1])

    def test_versao_igual_nao_notifica(self):
        host = _executar_verificacao(("1.2.0", "http://release"))
        host._about_panel.show_update.assert_not_called()

    def test_versao_anterior_nao_notifica(self):
        host = _executar_verificacao(("1.1.0", "http://release"))
        host._about_panel.show_update.assert_not_called()

    def test_resultado_none_nao_notifica(self):
        host = _executar_verificacao(None)
        host._about_panel.show_update.assert_not_called()

    def test_falha_inesperada_nao_propaga(self):
        host = _Host()
        with patch(f"{_MODULO}.obter_ultima_release", side_effect=RuntimeError("boom")):
            with patch(f"{_MODULO}.threading.Thread", _ThreadImediata):
                host._verificar_nova_versao()
        host._about_panel.show_update.assert_not_called()

    def test_botao_da_release_abre_url(self):
        host = _Host()
        with patch(f"{_MODULO}.obter_ultima_release", return_value=("9.9.9", "http://release")):
            with patch(f"{_MODULO}.threading.Thread", _ThreadImediata):
                with patch(f"{_MODULO}.webbrowser.open") as abrir:
                    host._verificar_nova_versao()
                    callback = host._about_panel.show_update.call_args.args[1]
                    callback()
        abrir.assert_called_once_with("http://release")

    def test_sem_painel_nao_falha(self):
        host = _Host()
        host._about_panel = None
        host._notificar_nova_versao("9.9.9", "http://release")


class TestAcoesSobre:
    def test_abrir_repositorio_usa_webbrowser(self):
        host = _Host()
        with patch(f"{_MODULO}.webbrowser.open") as abrir:
            host._abrir_repositorio()
        abrir.assert_called_once_with(REPOSITORIO_URL)

    def test_erro_do_webbrowser_informa_status(self):
        host = _Host()
        with patch(f"{_MODULO}.webbrowser.open", side_effect=webbrowser.Error):
            host._abrir_url("http://x")
        assert host.status == ["Não foi possível abrir o navegador."]

    def test_abrir_log_existente(self, tmp_path):
        host = _Host()
        arquivo = tmp_path / "flowscope.log"
        arquivo.write_text("conteudo")
        with patch(f"{_MODULO}.log_file_path", return_value=arquivo):
            with patch(f"{_MODULO}.abrir_no_aplicativo") as abrir:
                host._abrir_log_flowscope()
        abrir.assert_called_once_with(arquivo)

    def test_abrir_log_ausente_informa_status(self, tmp_path):
        host = _Host()
        inexistente = tmp_path / "nao-existe.log"
        with patch(f"{_MODULO}.log_file_path", return_value=inexistente):
            with patch(f"{_MODULO}.abrir_no_aplicativo") as abrir:
                host._abrir_log_flowscope()
        abrir.assert_not_called()
        assert host.status == [
            "O log da aplicação ainda não está disponível."
        ]

    def test_erro_ao_abrir_log_informa_status(self, tmp_path):
        host = _Host()
        arquivo = tmp_path / "flowscope.log"
        arquivo.write_text("conteudo")
        with patch(f"{_MODULO}.log_file_path", return_value=arquivo):
            with patch(f"{_MODULO}.abrir_no_aplicativo", side_effect=OSError("sem app")):
                host._abrir_log_flowscope()
        assert host.status == ["Não foi possível abrir o log da aplicação."]
