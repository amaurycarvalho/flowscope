"""Leitura cache-only dos títulos e abertura de links da pré-visualização."""

from __future__ import annotations

import re
import tkinter as tk

from flowscope.domain.renda_fixa import ArvoreTitulos, montar_arvore
from flowscope.presentation.gui.document_actions import abrir_url

#: URL embutida em uma linha Markdown de documentos relacionados.
_URL = re.compile(r"https?://[^\s)]+")


class DocumentTitulosMixin:
    """Complementa o painel com a leitura dos títulos e links externos."""

    def carregar_titulos(
        self: DocumentTitulosMixin, ticker: str | None
    ) -> ArvoreTitulos | None:
        """Combina títulos oficiais e inferidos do cache local, sem rede."""
        if not ticker:
            return None
        consultar = getattr(self, "_titulos_uc", None)
        oficial = consultar.executar(ticker) if consultar is not None else None
        inferencias = self._inferencias_de(ticker)
        if oficial is None and not inferencias:
            return None
        return montar_arvore(oficial, inferencias)

    def _inferencias_de(
        self: DocumentTitulosMixin, ticker: str
    ) -> tuple:
        """Lê os itens inferidos do ticker, tolerando cache ausente/ilegível."""
        repositorio = getattr(self, "_inferencias", None)
        if repositorio is None:
            return ()
        try:
            cache = repositorio.ler(ticker)
        except Exception:  # cache ilegível não derruba o painel
            return ()
        return cache.itens if cache is not None else ()

    def carregar_inferencia_pendente(
        self: DocumentTitulosMixin, ticker: str | None
    ) -> bool:
        """Consulta fora da thread do Tk se há inferência elegível pendente."""
        callback = getattr(self, "_inferencia_pendente_callback", None)
        if not ticker or callback is None:
            return False
        try:
            return bool(callback(ticker))
        except Exception:  # consulta de cache não deve bloquear o painel
            return False

    def definir_inferencia_pendente(
        self: DocumentTitulosMixin, pendente: bool
    ) -> None:
        """Registra o estado de inferência pendente para o botão do lote."""
        self._inferencia_pendente = bool(pendente)

    def inferencia_pendente(self: DocumentTitulosMixin) -> bool:
        """Indica se a última leitura encontrou inferência pendente elegível."""
        return getattr(self, "_inferencia_pendente", False)

    def _on_preview_double_click(
        self: DocumentTitulosMixin, event: tk.Event
    ) -> str:
        """Abre externamente a URL presente na linha clicada da pré-visualização."""
        try:
            indice = self._preview.index(f"@{event.x},{event.y}")
        except tk.TclError:
            return "break"
        linha = self._preview.get(f"{indice} linestart", f"{indice} lineend")
        encontrada = _URL.search(linha)
        if encontrada is not None:
            abrir_url(encontrada.group(0))
        return "break"
