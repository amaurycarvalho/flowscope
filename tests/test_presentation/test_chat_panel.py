"""Testes do painel de chat e dos seus estados de configuração."""

import logging
import os
import time
import tkinter as tk

import pytest

from flowscope.application.chat import FonteContexto
from flowscope.domain.llm import LLMCommunicationError, LLMUnavailableError
from flowscope.infrastructure.document_catalog import DocumentCatalog
from flowscope.presentation.gui.chat import chat_panel as chat_panel_mod
from flowscope.presentation.gui.chat.chat_panel import (
    TITULO_CHAT,
    ChatPanel,
    mensagem_confirmacao,
)
from flowscope.presentation.gui.chat.documentos import CascataDocumentos
from flowscope.presentation.gui.widgets.readonly_text import ReadonlyText

needs_display = pytest.mark.skipif(
    not os.environ.get("DISPLAY"),
    reason="Test requires a display (no DISPLAY env var)",
)


class _FakeLLM:
    """Porta de completion de teste com respostas roteirizadas."""

    def __init__(self, respostas: list) -> None:
        self.respostas = list(respostas)
        self.chamadas: list = []

    def complete(self, messages: list[dict], system_prompt: str | None = None) -> str:
        self.chamadas.append((messages, system_prompt))
        resposta = self.respostas.pop(0)
        if isinstance(resposta, BaseException):
            raise resposta
        return resposta


def _painel(root, tmp_path, **kwargs) -> ChatPanel:
    """Constrói um painel com catálogo temporário e opções sobreponíveis."""
    kwargs.setdefault("cascata", CascataDocumentos(catalog=DocumentCatalog(cache_dir=tmp_path)))
    painel = ChatPanel(root, **kwargs)
    painel.pack(fill=tk.BOTH, expand=True)
    return painel


def _aguardar(root: tk.Tk, painel: ChatPanel, timeout: float = 3.0) -> None:
    """Processa eventos do Tk até o painel concluir a consulta."""
    inicio = time.time()
    while painel._processando and time.time() - inicio < timeout:
        root.update()
        time.sleep(0.01)
    root.update()


class TestConstrucao:
    @needs_display
    def test_chat_sem_escopo(self, tmp_path):
        root = tk.Tk()
        try:
            painel = _painel(root, tmp_path, llm_available=lambda: True)
            assert painel._titulo.cget("text") == TITULO_CHAT
            assert isinstance(painel._respostas, ReadonlyText)
            assert painel._send_btn.cget("text") == "Enviar"
            assert painel._config_btn.cget("text") == "Configuração"
        finally:
            root.destroy()

    @needs_display
    def test_respostas_somente_leitura(self, tmp_path):
        root = tk.Tk()
        try:
            painel = _painel(root, tmp_path, llm_available=lambda: True)
            painel._respostas.insert("1.0", "conteudo")
            painel._respostas.pack()
            painel._respostas.focus_force()
            root.update()
            painel._respostas.event_generate("<KeyPress-a>", when="now")
            root.update()
            assert painel._respostas.get("1.0", "end-1c") == "conteudo"
        finally:
            root.destroy()


class TestEstadoConfiguracao:
    @needs_display
    def test_nao_configurado_desabilita_entrada(self, tmp_path):
        root = tk.Tk()
        try:
            painel = _painel(root, tmp_path, llm_available=lambda: False)
            root.update()
            assert str(painel._entrada.cget("state")) == "disabled"
            assert str(painel._send_btn.cget("state")) == "disabled"
            assert painel._orientacao.winfo_ismapped()
            assert painel._config_btn.winfo_ismapped()
        finally:
            root.destroy()

    @needs_display
    def test_configurado_habilita_entrada(self, tmp_path):
        root = tk.Tk()
        try:
            painel = _painel(root, tmp_path, llm_available=lambda: True)
            root.update()
            assert str(painel._entrada.cget("state")) == "normal"
            assert str(painel._send_btn.cget("state")) == "normal"
            assert not painel._orientacao.winfo_ismapped()
            assert painel._config_btn.winfo_ismapped()
        finally:
            root.destroy()

    @needs_display
    def test_reencontro_salva_reavalia_estado(self, tmp_path):
        root = tk.Tk()
        disponivel = {"ok": False}
        try:
            painel = _painel(root, tmp_path, llm_available=lambda: disponivel["ok"])
            root.update()
            assert str(painel._entrada.cget("state")) == "disabled"
            disponivel["ok"] = True
            painel.avaliar_estado()
            root.update()
            assert str(painel._entrada.cget("state")) == "normal"
        finally:
            root.destroy()

    @needs_display
    def test_botao_configurar_aciona_callback(self, tmp_path):
        root = tk.Tk()
        chamadas: list = []
        try:
            painel = _painel(
                root,
                tmp_path,
                llm_available=lambda: False,
                config_callback=lambda: chamadas.append(True),
            )
            painel._config_btn.invoke()
            assert chamadas == [True]
        finally:
            root.destroy()


class TestCopiarChat:
    @needs_display
    def test_copiar_chat(self, tmp_path):
        root = tk.Tk()
        try:
            painel = _painel(root, tmp_path, llm_available=lambda: True)
            painel._registrar("user", "pergunta")
            painel._registrar("assistant", "resposta", ["fonte-1"])
            painel._copiar_chat()
            root.update()
            conteudo = root.clipboard_get()
            assert "pergunta" in conteudo
            assert "resposta" in conteudo
        finally:
            root.destroy()

    @needs_display
    def test_copiar_chat_vazio_nao_falha(self, tmp_path):
        root = tk.Tk()
        try:
            painel = _painel(root, tmp_path, llm_available=lambda: True)
            painel._copiar_chat()
        finally:
            root.destroy()


class TestLimparChat:
    @needs_display
    def test_limpar_confirmado_esvazia_sessao(self, tmp_path, monkeypatch):
        root = tk.Tk()
        try:
            painel = _painel(root, tmp_path, llm_available=lambda: True)
            painel._registrar("user", "pergunta")
            painel._registrar("assistant", "resposta")
            monkeypatch.setattr(
                chat_panel_mod.messagebox, "askyesno", lambda *a, **k: True
            )
            painel._clear_btn.invoke()
            assert painel.conteudo_sessao() == ""
            assert painel._sessao.messages == []
        finally:
            root.destroy()

    @needs_display
    def test_limpar_cancelado_mantem_sessao(self, tmp_path, monkeypatch):
        root = tk.Tk()
        try:
            painel = _painel(root, tmp_path, llm_available=lambda: True)
            painel._registrar("user", "pergunta importante")
            monkeypatch.setattr(
                chat_panel_mod.messagebox, "askyesno", lambda *a, **k: False
            )
            painel._clear_btn.invoke()
            assert "pergunta importante" in painel.conteudo_sessao()
        finally:
            root.destroy()

    @needs_display
    def test_limpar_antes_de_copiar_no_cabecalho(self, tmp_path):
        root = tk.Tk()
        try:
            painel = _painel(root, tmp_path, llm_available=lambda: True)
            assert painel._clear_btn.cget("text") == "Limpar"
            botoes = painel._clear_btn.master.pack_slaves()
            # Empacotados à direita em ordem inversa: "Limpar" é empacotado por
            # último e por isso aparece à esquerda de "Copiar chat".
            assert botoes.index(painel._clear_btn) > botoes.index(painel._copy_btn)
        finally:
            root.destroy()


class TestConfirmacao:
    @pytest.mark.parametrize(
        ("quantidade", "nomes", "esperado"),
        [
            (2, [], None),
            (3, [], None),
            (4, ["a", "b", "c", "d"], "a"),
            (8, [], "8 documentos"),
        ],
    )
    def test_mensagem_por_faixa(self, quantidade, nomes, esperado):
        texto = mensagem_confirmacao(quantidade, nomes)
        if esperado is None:
            assert texto is None
        else:
            assert esperado in texto

    @needs_display
    def test_dialogo_confirmacao(self, tmp_path, monkeypatch):
        root = tk.Tk()
        try:
            painel = _painel(root, tmp_path, llm_available=lambda: True)
            monkeypatch.setattr(
                chat_panel_mod.messagebox, "askyesno", lambda *a, **k: True
            )
            assert painel._dialogo_confirmacao(5, ["a", "b", "c", "d", "e"]) is True
            monkeypatch.setattr(
                chat_panel_mod.messagebox, "askyesno", lambda *a, **k: False
            )
            assert painel._dialogo_confirmacao(9, []) is False
        finally:
            root.destroy()

    @needs_display
    def test_ate_tres_nao_abre_dialogo(self, tmp_path, monkeypatch):
        root = tk.Tk()
        try:
            painel = _painel(root, tmp_path, llm_available=lambda: True)
            chamadas: list = []
            monkeypatch.setattr(
                chat_panel_mod.messagebox,
                "askyesno",
                lambda *a, **k: chamadas.append(True) or True,
            )
            assert painel._dialogo_confirmacao(2, []) is True
            assert chamadas == []
        finally:
            root.destroy()


class TestConsulta:
    @needs_display
    def test_envio_com_resposta(self, tmp_path):
        root = tk.Tk()
        llm = _FakeLLM(['{"resposta": "olá do assistente", "documentos": []}'])
        try:
            painel = _painel(
                root,
                tmp_path,
                llm_available=lambda: True,
                llm_factory=lambda: llm,
                watchlist_provider=list,
            )
            painel._texto_entrada_set("Qual o rendimento?")
            painel._enviar()
            _aguardar(root, painel)
            conteudo = painel.conteudo_sessao()
            assert "Qual o rendimento?" in conteudo
            assert "olá do assistente" in conteudo
            assert len(llm.chamadas) == 1
        finally:
            root.destroy()

    @needs_display
    def test_falha_exibe_status_e_registra_log(self, tmp_path, caplog):
        root = tk.Tk()
        llm = _FakeLLM([LLMCommunicationError("timeout de rede")])
        estados: list = []
        try:
            painel = _painel(
                root,
                tmp_path,
                llm_available=lambda: True,
                llm_factory=lambda: llm,
                status_callback=lambda msg, icon: estados.append((msg, icon)),
                watchlist_provider=list,
            )
            painel._texto_entrada_set("pergunta")
            with caplog.at_level(logging.ERROR, logger="flowscope"):
                painel._enviar()
                _aguardar(root, painel)
            assert any(icon == "⚠" for _msg, icon in estados)
            assert any(
                "Falha no chat" in registro.getMessage()
                and "timeout de rede" in registro.getMessage()
                for registro in caplog.records
            )
        finally:
            root.destroy()

    @needs_display
    def test_llm_indisponivel_desabilita(self, tmp_path):
        root = tk.Tk()
        llm = _FakeLLM([LLMUnavailableError("sem provedor")])
        try:
            painel = _painel(
                root,
                tmp_path,
                llm_available=lambda: True,
                llm_factory=lambda: llm,
                watchlist_provider=list,
            )
            painel._texto_entrada_set("pergunta")
            painel._enviar()
            _aguardar(root, painel)
            root.update()
            assert painel._disponivel is False
            assert str(painel._entrada.cget("state")) == "disabled"
        finally:
            root.destroy()


class TestFontesAdicionais:
    @needs_display
    def test_fonte_adicional_incluida_no_prompt(self, tmp_path):
        root = tk.Tk()
        llm = _FakeLLM(['{"resposta": "ok", "documentos": []}'])
        recebidas: list[str] = []

        def fonte(pergunta: str) -> FonteContexto:
            recebidas.append(pergunta)
            return FonteContexto("Notícias recentes", "manchete sobre PETR4")

        try:
            painel = _painel(
                root,
                tmp_path,
                llm_available=lambda: True,
                llm_factory=lambda: llm,
                watchlist_provider=list,
                fontes_adicionais=[fonte],
            )
            painel._texto_entrada_set("E as notícias?")
            painel._enviar()
            _aguardar(root, painel)
            assert recebidas == ["E as notícias?"]
            prompt = llm.chamadas[0][0][0]["content"]
            assert "## Notícias recentes" in prompt
            assert "manchete sobre PETR4" in prompt
        finally:
            root.destroy()

    @needs_display
    def test_fonte_adicional_que_falha_e_omitida(self, tmp_path):
        root = tk.Tk()
        llm = _FakeLLM(['{"resposta": "resposta mesmo assim", "documentos": []}'])

        def fonte_ruim(pergunta: str) -> FonteContexto:
            raise RuntimeError("fonte indisponível")

        try:
            painel = _painel(
                root,
                tmp_path,
                llm_available=lambda: True,
                llm_factory=lambda: llm,
                watchlist_provider=list,
                fontes_adicionais=[fonte_ruim],
            )
            painel._texto_entrada_set("Pergunta")
            painel._enviar()
            _aguardar(root, painel)
            assert "resposta mesmo assim" in painel.conteudo_sessao()
            assert len(llm.chamadas) == 1
        finally:
            root.destroy()
