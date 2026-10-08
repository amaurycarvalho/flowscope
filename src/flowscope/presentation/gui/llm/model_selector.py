"""Seletor compartilhado de modelo ativo de I.A.

Combina um combobox dos provedores ativos (mais a opção ``None``) com um botão
de configuração de ícone. É usado no cabeçalho da aba "Chat AI" e nas barras das
sub-abas "Documentos" e "Notícias". A troca no combobox persiste o provedor ativo
por meio da porta de configuração e dispara o callback de reavaliação; o botão
abre o diálogo de configuração.
"""

import logging
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import ttk

from PIL import Image, ImageTk

from flowscope.application.llm_config_port import LLMConfigPort
from flowscope.presentation.gui.widgets.tooltip import ToolTip
from flowscope.presentation.shortcuts import _resolve_icon_path

logger = logging.getLogger("flowscope")

#: Rótulo do item que desativa o provedor corrente.
ROTULO_NONE = "None"

#: Arquivo de ícone do botão de configuração.
ICONE = "ai-properties.png"

#: Dica exibida sobre o combobox e o botão.
TOOLTIP_SELETOR = "Seleciona o modelo de I.A. ativo"
TOOLTIP_CONFIG = "Configurar a I.A."


def opcoes_modelo(ativos: list[str], provider: str) -> list[str]:
    """Monta as opções do combobox: ``None`` mais os provedores ativos.

    Inclui o provedor corrente mesmo que ele não conste em ``ativos`` (provedor
    em uso ainda não testado), sem duplicar nem repetir ``None``.
    """
    opcoes = [ROTULO_NONE]
    for nome in [*ativos, provider]:
        if nome and nome != "none" and nome not in opcoes:
            opcoes.append(nome)
    return opcoes


def selecao_modelo(provider: str, opcoes: list[str]) -> str:
    """Retorna o item a selecionar, caindo em ``None`` fora das opções."""
    return provider if provider in opcoes else ROTULO_NONE


class _PortaConfigNula:
    """Porta de configuração vazia, usada quando nenhuma é injetada."""

    def active_providers(
        self: "_PortaConfigNula", path: Path | None = None
    ) -> list[str]:
        return []

    def load_llm_config(self: "_PortaConfigNula", path: Path | None = None) -> dict:
        return {"provider": "none"}

    def set_active_provider(
        self: "_PortaConfigNula", provider: str, path: Path | None = None
    ) -> None:
        return None


class SeletorModelo(tk.Frame):
    """Combobox de provedores ativos com botão de configuração de ícone."""

    def __init__(
        self: "SeletorModelo",
        parent: tk.Misc,
        *,
        config_port: LLMConfigPort | None = None,
        on_config: Callable[[], None],
        on_changed: Callable[[str], None] | None = None,
        config_path: Path | None = None,
        largura: int = 18,
    ) -> None:
        """Monta o combobox e o botão, refletindo a configuração corrente."""
        super().__init__(parent)
        self._port = config_port if config_port is not None else _PortaConfigNula()
        self._config_path = config_path
        self._on_config = on_config
        self._on_changed = on_changed
        self._icon_refs: list[ImageTk.PhotoImage] = []
        self._var = tk.StringVar()
        self._combo = ttk.Combobox(
            self, textvariable=self._var, state="readonly", width=largura
        )
        self._combo.pack(side=tk.LEFT, padx=2)
        self._combo.bind("<<ComboboxSelected>>", self._on_selected)
        ToolTip(self._combo, TOOLTIP_SELETOR)
        self._btn = ttk.Button(
            self, image=self._carregar_icone(), command=self._configurar
        )
        self._btn.pack(side=tk.LEFT, padx=2)
        ToolTip(self._btn, TOOLTIP_CONFIG)
        self.recarregar()

    @property
    def combo(self: "SeletorModelo") -> ttk.Combobox:
        """Retorna o combobox do seletor."""
        return self._combo

    @property
    def botao(self: "SeletorModelo") -> ttk.Button:
        """Retorna o botão de configuração do seletor."""
        return self._btn

    def _carregar_icone(self: "SeletorModelo") -> ImageTk.PhotoImage | None:
        """Carrega o ícone do botão, tolerando ausência do recurso."""
        try:
            caminho = _resolve_icon_path(ICONE)
            imagem = Image.open(caminho).resize((20, 20), Image.LANCZOS)
            photo = ImageTk.PhotoImage(imagem)
        except (OSError, ValueError):
            logger.warning("Ícone de configuração de I.A. indisponível", exc_info=True)
            return None
        self._icon_refs.append(photo)
        return photo

    def recarregar(self: "SeletorModelo") -> None:
        """Repopula o combobox a partir da configuração persistida."""
        ativos = list(self._port.active_providers(self._config_path))
        provider = self._port.load_llm_config(self._config_path).get(
            "provider", "none"
        )
        opcoes = opcoes_modelo(ativos, provider)
        self._combo.configure(values=opcoes)
        self._var.set(selecao_modelo(provider, opcoes))

    def definir_ativo(self: "SeletorModelo", provider: str) -> None:
        """Seleciona o provedor informado, se presente nas opções."""
        valores = list(self._combo.cget("values"))
        self._var.set(provider if provider in valores else ROTULO_NONE)

    def provedor_selecionado(self: "SeletorModelo") -> str:
        """Retorna o provedor selecionado, traduzindo ``None`` para ``none``."""
        escolha = self._var.get()
        return "none" if escolha == ROTULO_NONE else escolha

    def set_enabled(self: "SeletorModelo", habilitado: bool) -> None:
        """Habilita ou desabilita o combobox e o botão de configuração."""
        estado = tk.NORMAL if habilitado else tk.DISABLED
        self._combo.config(state="readonly" if habilitado else tk.DISABLED)
        self._btn.config(state=estado)

    def all_buttons(self: "SeletorModelo") -> list[tk.Widget]:
        """Retorna os controles para o bloqueio global da interface."""
        return [self._combo, self._btn]

    def _on_selected(self: "SeletorModelo", event: tk.Event | None = None) -> None:
        """Grava a escolha e notifica a reavaliação."""
        provider = self.provedor_selecionado()
        self._port.set_active_provider(provider, self._config_path)
        if self._on_changed is not None:
            self._on_changed(provider)

    def _configurar(self: "SeletorModelo") -> None:
        """Abre o diálogo de configuração pelo callback injetado."""
        self._on_config()
