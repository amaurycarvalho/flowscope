"""Testes do diálogo de configuração de LLM."""

import json
import os
import threading
import time
import tkinter as tk
from unittest.mock import MagicMock

import pytest

from flowscope.domain.llm import (
    LLMCommunicationError,
    LLMConfigurationError,
    LLMProviderError,
    LLMResposta,
    LLMServiceUnavailableError,
    LLMUnavailableError,
)
from flowscope.infrastructure.llm.config_adapter import InfrastructureLLMConfig
from flowscope.presentation.gui.llm.config_dialog import (
    LLMConfigDialog,
    assinatura_conexao,
    deve_ativar,
)
from flowscope.presentation.gui.llm.config_form import LLMConfigForm

pytestmark = pytest.mark.llm

needs_display = pytest.mark.skipif(
    not os.environ.get("DISPLAY"),
    reason="Test requires a display (no DISPLAY env var)",
)


def _dialog(parent, *, config_port=None, **kwargs):
    """Cria o diálogo com a porta de configuração de LLM já injetada."""
    return LLMConfigDialog(
        parent, config_port=config_port or InfrastructureLLMConfig(), **kwargs
    )


def _aguardar(root: tk.Tk, dialog: LLMConfigDialog, timeout: float = 3.0) -> None:
    inicio = time.time()
    while dialog._testando and time.time() - inicio < timeout:
        root.update()
        time.sleep(0.01)
    root.update()


def _config_salva(tmp_path, **chat):
    caminho = tmp_path / "config.json"
    caminho.write_text(
        json.dumps({"llm": {"chat": chat}}), encoding="utf-8"
    )
    return caminho


class TestCargaESalvamentoForm:
    """Carga, presets e salvamento do modelo puro, sem Tk."""

    def test_abertura_carrega_config(self, tmp_path):
        caminho = _config_salva(
            tmp_path,
            provider="deepseek",
            api_url="https://api.deepseek.com/v1",
            model="deepseek-chat",
            api_key="sk-9",
            rpm=7,
        )
        form = LLMConfigForm(InfrastructureLLMConfig(), caminho)
        form.carregar_inicial()
        assert form.provider == "deepseek"
        assert form.api_url == "https://api.deepseek.com/v1"
        assert form.model == "deepseek-chat"
        assert form.api_key == "sk-9"
        assert form.rpm == "7"

    def test_salvar_sem_teste_grava_sem_ativar(self, tmp_path):
        caminho = tmp_path / "config.json"
        port = InfrastructureLLMConfig()
        form = LLMConfigForm(port, caminho)
        form.provider = "openai"
        form.api_url = "https://api.openai.com/v1"
        form.model = "gpt-4o-mini"
        form.api_key = "sk-2"
        form.rpm = "9"
        config = form.coletar_config()
        port.save_llm_config(config, caminho, ativar=deve_ativar(config, None))
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        chat = dados["llm"]["chat"]
        assert chat["provider"] == "none"
        assert chat["active"] == []
        assert chat["providers"]["openai"]["api_key"] == "sk-2"
        assert chat["providers"]["openai"]["rpm"] == 9

    def test_reabertura_mostra_config_salva(self, tmp_path):
        caminho = tmp_path / "config.json"
        port = InfrastructureLLMConfig()
        form = LLMConfigForm(port, caminho)
        form.provider = "deepseek"
        form.api_url = "https://api.deepseek.com/v1"
        form.model = "deepseek-chat"
        form.api_key = "sk-9"
        form.rpm = "8"
        port.save_llm_config(form.coletar_config(), caminho, ativar=True)
        reaberto = LLMConfigForm(port, caminho)
        reaberto.carregar_inicial()
        assert reaberto.provider == "deepseek"
        assert reaberto.api_url == "https://api.deepseek.com/v1"
        assert reaberto.model == "deepseek-chat"
        assert reaberto.api_key == "sk-9"
        assert reaberto.rpm == "8"

    def test_preset_preenche_modelo_e_url(self, tmp_path):
        form = LLMConfigForm(InfrastructureLLMConfig(), tmp_path / "c.json")
        form.trocar_provider("deepseek")
        assert form.model == "deepseek-chat"
        assert form.api_url == "https://api.deepseek.com/v1"

    def test_preset_custom_fica_em_branco(self, tmp_path):
        form = LLMConfigForm(InfrastructureLLMConfig(), tmp_path / "c.json")
        form.trocar_provider("custom")
        assert form.model == ""
        assert form.api_url == ""


class TestDialogoShell:
    """Comportamento do diálogo que só existe com Tk."""

    @needs_display
    def test_salvar_fecha_dialogo(self, tmp_path):
        caminho = tmp_path / "config.json"
        root = tk.Tk()
        try:
            dialog = _dialog(root, config_path=caminho)
            dialog._salvar()
            assert dialog.winfo_exists() == 0
        finally:
            root.destroy()

    @needs_display
    def test_chave_mascarada(self, tmp_path):
        root = tk.Tk()
        try:
            dialog = _dialog(root, config_path=tmp_path / "c.json")
            assert dialog._api_key_entry.cget("show") == "*"
        finally:
            root.destroy()


class TestConfigPorProvedor:
    def _config_dois_provedores(self, tmp_path):
        caminho = tmp_path / "config.json"
        caminho.write_text(
            json.dumps(
                {
                    "llm": {
                        "chat": {
                            "provider": "openai",
                            "providers": {
                                "openai": {
                                    "api_url": "https://api.openai.com/v1",
                                    "model": "gpt-4o-mini",
                                    "api_key": "sk-open",
                                    "rpm": 3,
                                },
                                "deepseek": {
                                    "api_url": "https://api.deepseek.com/v1",
                                    "model": "deepseek-chat",
                                    "api_key": "sk-deep",
                                    "rpm": 7,
                                },
                            },
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        return caminho

    def _form(self, tmp_path):
        form = LLMConfigForm(
            InfrastructureLLMConfig(), self._config_dois_provedores(tmp_path)
        )
        form.carregar_inicial()
        return form

    def test_abertura_carrega_provedor_ativo(self, tmp_path):
        form = self._form(tmp_path)
        assert form.provider == "openai"
        assert form.api_key == "sk-open"
        form.trocar_provider("deepseek")
        assert form.api_key == "sk-deep"

    def test_troca_restaura_provedor_salvo(self, tmp_path):
        form = self._form(tmp_path)
        form.trocar_provider("deepseek")
        assert form.api_url == "https://api.deepseek.com/v1"
        assert form.model == "deepseek-chat"
        assert form.api_key == "sk-deep"
        assert form.rpm == "7"

    def test_troca_para_nao_configurado_limpa_chave(self, tmp_path):
        form = self._form(tmp_path)
        form.trocar_provider("gemini")
        assert form.api_url == (
            "https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        assert form.api_key == ""

    def test_none_limpa_e_volta_restaura(self, tmp_path):
        form = self._form(tmp_path)
        form.trocar_provider("none")
        assert form.api_url == ""
        assert form.model == ""
        assert form.api_key == ""
        assert "none" not in form._working

        form.trocar_provider("deepseek")
        assert form.api_key == "sk-deep"

    def test_edicao_nao_salva_sobrevive_na_sessao(self, tmp_path):
        form = self._form(tmp_path)
        form.trocar_provider("deepseek")
        form.api_key = "sk-nova"
        form.trocar_provider("openai")
        form.trocar_provider("deepseek")
        assert form.api_key == "sk-nova"

    def test_trocar_sem_salvar_nao_grava(self, tmp_path):
        caminho = _config_salva(
            tmp_path,
            provider="deepseek",
            api_url="https://api.deepseek.com/v1",
            model="deepseek-chat",
            api_key="sk-deep",
            rpm=7,
        )
        antes = caminho.read_text(encoding="utf-8")
        form = LLMConfigForm(InfrastructureLLMConfig(), caminho)
        form.carregar_inicial()
        form.trocar_provider("openai")
        form.api_key = "sk-open"
        assert caminho.read_text(encoding="utf-8") == antes


class TestTestarConexao:
    def _dialogo(self, tmp_path, port=None):
        root = tk.Tk()
        return root, _dialog(
            root, config_port=port, config_path=tmp_path / "c.json"
        )

    @needs_display
    def test_sucesso(self, tmp_path, monkeypatch):
        provedor = MagicMock()
        provedor.complete.return_value = LLMResposta(texto="olá mundo")
        port = InfrastructureLLMConfig()
        monkeypatch.setattr(port, "create_provider", lambda _c: provedor)
        root, dialog = self._dialogo(tmp_path, port)
        try:
            dialog._on_testar()
            _aguardar(root, dialog)
            assert "olá mundo" in dialog._status_var.get()
            provedor.complete.assert_called_once_with(
                [{"role": "user", "content": "hello"}]
            )
        finally:
            root.destroy()

    @needs_display
    @pytest.mark.parametrize(
        ("erro", "esperado"),
        [
            (LLMUnavailableError("LLM indisponível"), "LLM indisponível"),
            (
                LLMServiceUnavailableError("Error code: 503"),
                "temporariamente indisponível",
            ),
            (LLMCommunicationError("falha de rede"), "conectar ao serviço de I.A."),
            (LLMProviderError("não autorizado"), "provedor de I.A. retornou um erro"),
            (
                LLMConfigurationError("configuração incompleta"),
                "Configuração de I.A. inválida",
            ),
        ],
    )
    def test_falhas_exibem_motivo(self, tmp_path, monkeypatch, erro, esperado):
        def _falha(_config):
            raise erro

        port = InfrastructureLLMConfig()
        monkeypatch.setattr(port, "create_provider", _falha)
        root, dialog = self._dialogo(tmp_path, port)
        try:
            dialog._on_testar()
            _aguardar(root, dialog)
            assert esperado in dialog._status_var.get()
            assert str(erro) not in dialog._status_var.get() or esperado == str(erro)
        finally:
            root.destroy()

    @needs_display
    def test_falha_registra_log_sem_chave(self, tmp_path, monkeypatch, caplog):
        def _falha(_config):
            raise LLMCommunicationError("timeout de rede")

        port = InfrastructureLLMConfig()
        monkeypatch.setattr(port, "create_provider", _falha)
        root, dialog = self._dialogo(tmp_path, port)
        try:
            dialog._provider_var.set("deepseek")
            dialog._model_var.set("deepseek-chat")
            dialog._api_key_var.set("sk-segredo")
            with caplog.at_level("WARNING", logger="flowscope"):
                dialog._on_testar()
                _aguardar(root, dialog)
            mensagens = [registro.getMessage() for registro in caplog.records]
            assert any(
                "Teste de conexão da LLM falhou" in mensagem
                and "LLMCommunicationError" in mensagem
                and "timeout de rede" in mensagem
                for mensagem in mensagens
            )
            assert any("provider=deepseek" in mensagem for mensagem in mensagens)
            assert all("sk-segredo" not in mensagem for mensagem in mensagens)
        finally:
            root.destroy()

    @needs_display
    def test_bloqueio_durante_teste(self, tmp_path, monkeypatch):
        liberar = threading.Event()
        chamadas: list[int] = []
        provedor = MagicMock()
        provedor.complete.return_value = LLMResposta(texto="ok")

        def _lento(_config):
            chamadas.append(1)
            liberar.wait(3)
            return provedor

        port = InfrastructureLLMConfig()
        monkeypatch.setattr(port, "create_provider", _lento)
        root, dialog = self._dialogo(tmp_path, port)
        try:
            dialog._on_testar()
            for _ in range(100):
                if chamadas:
                    break
                root.update()
                time.sleep(0.01)
            assert chamadas == [1]
            assert dialog._testando is True
            assert str(dialog._test_btn.cget("state")) == "disabled"

            dialog._on_testar()
            assert len(chamadas) == 1

            liberar.set()
            _aguardar(root, dialog)
            assert dialog._testando is False
            assert str(dialog._test_btn.cget("state")) == "normal"
        finally:
            liberar.set()
            root.destroy()


class TestOnSaved:
    @needs_display
    def test_on_saved_invocado_apos_salvar(self, tmp_path):
        chamadas = []
        caminho = tmp_path / "config.json"
        root = tk.Tk()
        try:
            dialog = _dialog(
                root, config_path=caminho,
                on_saved=lambda: chamadas.append(True),
            )
            dialog._salvar()
            assert chamadas == [True]
            assert caminho.exists()
        finally:
            root.destroy()

    @needs_display
    def test_sem_on_saved_nao_falha(self, tmp_path):
        root = tk.Tk()
        try:
            dialog = _dialog(root, config_path=tmp_path / "c.json")
            dialog._salvar()
        finally:
            root.destroy()


class TestAssinaturaConexao:
    def test_normaliza_url_e_ignora_rpm(self):
        a = assinatura_conexao(
            {
                "provider": "openai",
                "api_url": "https://x/v1/",
                "model": "m",
                "api_key": "k",
                "rpm": 5,
            }
        )
        b = assinatura_conexao(
            {
                "provider": "openai",
                "api_url": " https://x/v1 ",
                "model": "m",
                "api_key": "k",
                "rpm": 60,
            }
        )
        assert a == b

    def test_campos_distintos_mudam_assinatura(self):
        base = {
            "provider": "openai",
            "api_url": "https://x/v1",
            "model": "m",
            "api_key": "k",
        }
        for campo, valor in (
            ("provider", "gemini"),
            ("api_url", "https://y/v1"),
            ("model", "m2"),
            ("api_key", "k2"),
        ):
            outro = dict(base)
            outro[campo] = valor
            assert assinatura_conexao(base) != assinatura_conexao(outro)


class TestDeveAtivar:
    def test_none_sempre_ativa(self):
        assert deve_ativar({"provider": "none"}, None) is True
        assert deve_ativar({"provider": "none"}, "qualquer") is True

    def test_ativa_somente_com_teste_correspondente(self):
        config = {
            "provider": "openai",
            "api_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini",
            "api_key": "sk-2",
            "rpm": 9,
        }
        assert deve_ativar(config, assinatura_conexao(config)) is True

    def test_sem_teste_nao_ativa(self):
        config = {"provider": "openai", "api_key": "sk-2"}
        assert deve_ativar(config, None) is False

    def test_teste_divergente_nao_ativa(self):
        config = {"provider": "openai", "model": "m", "api_key": "k"}
        outro = dict(config, model="outro")
        assert deve_ativar(config, assinatura_conexao(outro)) is False


class TestModalidade:
    @needs_display
    def test_nao_redimensionavel(self, tmp_path):
        root = tk.Tk()
        try:
            dialog = _dialog(root, config_path=tmp_path / "c.json")
            assert dialog.resizable() == (0, 0)
        finally:
            root.destroy()

    @needs_display
    def test_modal_com_grab(self, tmp_path):
        root = tk.Tk()
        try:
            dialog = _dialog(root, config_path=tmp_path / "c.json")
            assert dialog.grab_current() == dialog
        finally:
            root.destroy()


class TestDependenciasAusentes:
    @needs_display
    def test_bloqueia_configuracao_e_teste(self, tmp_path, monkeypatch):
        port = InfrastructureLLMConfig()
        monkeypatch.setattr(port, "check_llm_deps", lambda: False)
        root = tk.Tk()
        try:
            dialog = _dialog(
                root, config_port=port, config_path=tmp_path / "c.json"
            )
            assert "pip install flowscope[llm]" in dialog._status_var.get()
            assert str(dialog._test_btn.cget("state")) == "disabled"
            assert str(dialog._api_url_entry.cget("state")) == "disabled"
            assert str(dialog._model_entry.cget("state")) == "disabled"
            assert str(dialog._save_btn.cget("state")) == "disabled"
        finally:
            root.destroy()

    @needs_display
    def test_testar_nao_inicia_sem_deps(self, tmp_path, monkeypatch):
        port = InfrastructureLLMConfig()
        monkeypatch.setattr(port, "check_llm_deps", lambda: False)
        chamadas = []
        monkeypatch.setattr(
            port, "create_provider", lambda _c: chamadas.append(1)
        )
        root = tk.Tk()
        try:
            dialog = _dialog(
                root, config_port=port, config_path=tmp_path / "c.json"
            )
            dialog._on_testar()
            root.update()
            assert chamadas == []
            assert dialog._testando is False
        finally:
            root.destroy()
