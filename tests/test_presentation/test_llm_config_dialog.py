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
    LLMUnavailableError,
)
from flowscope.presentation.gui.llm import config_dialog
from flowscope.presentation.gui.llm.config_dialog import LLMConfigDialog

pytestmark = pytest.mark.llm

needs_display = pytest.mark.skipif(
    not os.environ.get("DISPLAY"),
    reason="Test requires a display (no DISPLAY env var)",
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


class TestCargaESalvamento:
    @needs_display
    def test_abertura_carrega_config(self, tmp_path):
        caminho = _config_salva(
            tmp_path,
            provider="deepseek",
            api_url="https://api.deepseek.com/v1",
            model="deepseek-chat",
            api_key="sk-9",
            rpm=7,
        )
        root = tk.Tk()
        try:
            dialog = LLMConfigDialog(root, config_path=caminho)
            assert dialog._provider_var.get() == "deepseek"
            assert dialog._api_url_var.get() == "https://api.deepseek.com/v1"
            assert dialog._model_var.get() == "deepseek-chat"
            assert dialog._api_key_var.get() == "sk-9"
            assert dialog._rpm_var.get() == "7"
        finally:
            root.destroy()

    @needs_display
    def test_salvar_persiste_config(self, tmp_path):
        caminho = tmp_path / "config.json"
        root = tk.Tk()
        try:
            dialog = LLMConfigDialog(root, config_path=caminho)
            dialog._provider_var.set("openai")
            dialog._api_url_var.set("https://api.openai.com/v1")
            dialog._model_var.set("gpt-4o-mini")
            dialog._api_key_var.set("sk-2")
            dialog._rpm_var.set("9")
            dialog._salvar()
            dados = json.loads(caminho.read_text(encoding="utf-8"))
            assert dados["llm"]["chat"]["provider"] == "openai"
            assert dados["llm"]["chat"]["api_key"] == "sk-2"
            assert dados["llm"]["chat"]["rpm"] == 9
        finally:
            root.destroy()

    @needs_display
    def test_salvar_fecha_dialogo(self, tmp_path):
        caminho = tmp_path / "config.json"
        root = tk.Tk()
        try:
            dialog = LLMConfigDialog(root, config_path=caminho)
            dialog._salvar()
            assert dialog.winfo_exists() == 0
        finally:
            root.destroy()

    @needs_display
    def test_reabertura_mostra_config_salva(self, tmp_path):
        caminho = tmp_path / "config.json"
        root = tk.Tk()
        try:
            dialog = LLMConfigDialog(root, config_path=caminho)
            dialog._provider_var.set("deepseek")
            dialog._api_url_var.set("https://api.deepseek.com/v1")
            dialog._model_var.set("deepseek-chat")
            dialog._api_key_var.set("sk-9")
            dialog._rpm_var.set("8")
            dialog._salvar()
            reaberto = LLMConfigDialog(root, config_path=caminho)
            try:
                assert reaberto._provider_var.get() == "deepseek"
                assert reaberto._api_url_var.get() == "https://api.deepseek.com/v1"
                assert reaberto._model_var.get() == "deepseek-chat"
                assert reaberto._api_key_var.get() == "sk-9"
                assert reaberto._rpm_var.get() == "8"
            finally:
                reaberto.destroy()
        finally:
            root.destroy()

    @needs_display
    def test_chave_mascarada(self, tmp_path):
        root = tk.Tk()
        try:
            dialog = LLMConfigDialog(root, config_path=tmp_path / "c.json")
            assert dialog._api_key_entry.cget("show") == "*"
        finally:
            root.destroy()

    @needs_display
    def test_preset_preenche_modelo_e_url(self, tmp_path):
        root = tk.Tk()
        try:
            dialog = LLMConfigDialog(root, config_path=tmp_path / "c.json")
            dialog._provider_var.set("deepseek")
            dialog._on_preset_change()
            assert dialog._model_var.get() == "deepseek-chat"
            assert dialog._api_url_var.get() == "https://api.deepseek.com/v1"
        finally:
            root.destroy()

    @needs_display
    def test_preset_custom_fica_em_branco(self, tmp_path):
        root = tk.Tk()
        try:
            dialog = LLMConfigDialog(root, config_path=tmp_path / "c.json")
            dialog._provider_var.set("custom")
            dialog._on_preset_change()
            assert dialog._model_var.get() == ""
            assert dialog._api_url_var.get() == ""
        finally:
            root.destroy()


class TestTestarConexao:
    def _dialogo(self, tmp_path):
        root = tk.Tk()
        return root, LLMConfigDialog(root, config_path=tmp_path / "c.json")

    @needs_display
    def test_sucesso(self, tmp_path, monkeypatch):
        provedor = MagicMock()
        provedor.complete.return_value = "olá mundo"
        monkeypatch.setattr(
            config_dialog, "create_llm_provider", lambda _c: provedor
        )
        root, dialog = self._dialogo(tmp_path)
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
        "erro",
        [
            LLMUnavailableError("LLM indisponível"),
            LLMCommunicationError("falha de rede"),
            LLMProviderError("não autorizado"),
            LLMConfigurationError("configuração incompleta"),
        ],
    )
    def test_falhas_exibem_motivo(self, tmp_path, monkeypatch, erro):
        def _falha(_config):
            raise erro

        monkeypatch.setattr(config_dialog, "create_llm_provider", _falha)
        root, dialog = self._dialogo(tmp_path)
        try:
            dialog._on_testar()
            _aguardar(root, dialog)
            assert str(erro) in dialog._status_var.get()
        finally:
            root.destroy()

    @needs_display
    def test_falha_registra_log_sem_chave(self, tmp_path, monkeypatch, caplog):
        def _falha(_config):
            raise LLMCommunicationError("timeout de rede")

        monkeypatch.setattr(config_dialog, "create_llm_provider", _falha)
        root, dialog = self._dialogo(tmp_path)
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
        provedor.complete.return_value = "ok"

        def _lento(_config):
            chamadas.append(1)
            liberar.wait(3)
            return provedor

        monkeypatch.setattr(config_dialog, "create_llm_provider", _lento)
        root, dialog = self._dialogo(tmp_path)
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


class TestModalidade:
    @needs_display
    def test_nao_redimensionavel(self, tmp_path):
        root = tk.Tk()
        try:
            dialog = LLMConfigDialog(root, config_path=tmp_path / "c.json")
            assert dialog.resizable() == (0, 0)
        finally:
            root.destroy()

    @needs_display
    def test_modal_com_grab(self, tmp_path):
        root = tk.Tk()
        try:
            dialog = LLMConfigDialog(root, config_path=tmp_path / "c.json")
            assert dialog.grab_current() == dialog
        finally:
            root.destroy()


class TestDependenciasAusentes:
    @needs_display
    def test_bloqueia_configuracao_e_teste(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_dialog, "check_llm_deps", lambda: False)
        root = tk.Tk()
        try:
            dialog = LLMConfigDialog(root, config_path=tmp_path / "c.json")
            assert "pip install flowscope[llm]" in dialog._status_var.get()
            assert str(dialog._test_btn.cget("state")) == "disabled"
            assert str(dialog._api_url_entry.cget("state")) == "disabled"
            assert str(dialog._model_entry.cget("state")) == "disabled"
            assert str(dialog._save_btn.cget("state")) == "disabled"
        finally:
            root.destroy()

    @needs_display
    def test_testar_nao_inicia_sem_deps(self, tmp_path, monkeypatch):
        monkeypatch.setattr(config_dialog, "check_llm_deps", lambda: False)
        chamadas = []
        monkeypatch.setattr(
            config_dialog,
            "create_llm_provider",
            lambda _c: chamadas.append(1),
        )
        root = tk.Tk()
        try:
            dialog = LLMConfigDialog(root, config_path=tmp_path / "c.json")
            dialog._on_testar()
            root.update()
            assert chamadas == []
            assert dialog._testando is False
        finally:
            root.destroy()
