"""Diálogo de configuração de LLM da interface gráfica.

Oferece seleção de preset, API URL, modelo, chave de API mascarada e RPM, além
de persistir o bloco ``llm.chat`` e testar a conexão com o provedor em thread
de trabalho, publicando o desfecho na thread do Tk por fila.
"""

import logging
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from flowscope.domain.llm import LLMError
from flowscope.infrastructure.llm.config import (
    check_llm_deps,
    get_presets,
    load_llm_config,
    save_llm_config,
)
from flowscope.infrastructure.llm.factory import create_llm_provider

logger = logging.getLogger("flowscope")

#: Mensagem exibida quando as dependências opcionais não estão instaladas.
MENSAGEM_DEPS = (
    "Instale flowscope[llm] para habilitar o LLM: pip install flowscope[llm]"
)

#: Mensagem exibida durante o teste de conexão.
MENSAGEM_TESTANDO = "Testando conexão…"

#: Prefixo da mensagem de sucesso do teste de conexão.
MENSAGEM_SUCESSO = "Conexão bem-sucedida: {resposta}"

#: Texto enviado ao provedor no teste de conexão.
TEXTO_TESTE = "hello"


class LLMConfigDialog(tk.Toplevel):
    """Janela de configuração do provedor de LLM."""

    def __init__(
        self: "LLMConfigDialog",
        parent: tk.Misc,
        *,
        config_path: Path | None = None,
    ) -> None:
        """Constrói o diálogo, carrega a configuração salva e aplica as deps."""
        super().__init__(parent)
        self.title("Configuração de I.A.")
        self._config_path = config_path
        self._presets = get_presets()
        self._widgets_config: list[tk.Widget] = []
        self._fila: queue.Queue = queue.Queue()
        self._testando = False
        self._deps_ok = True
        self._provider_var = tk.StringVar()
        self._api_url_var = tk.StringVar()
        self._model_var = tk.StringVar()
        self._api_key_var = tk.StringVar()
        self._rpm_var = tk.StringVar()
        self._status_var = tk.StringVar()
        self._build()
        self._carregar()
        self._aplicar_deps()
        self._aplicar_modal(parent)

    def _aplicar_modal(self: "LLMConfigDialog", parent: tk.Misc) -> None:
        """Torna o diálogo modal, não redimensionável e com foco inicial."""
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.focus_set()

    def _build(self: "LLMConfigDialog") -> None:
        """Constrói os campos, os botões e a área de status."""
        corpo = ttk.Frame(self, padding=10)
        corpo.pack(fill=tk.BOTH, expand=True)
        self._provider_combo = self._add_combo(
            corpo, "Provedor", self._provider_var, list(self._presets)
        )
        self._provider_combo.bind(
            "<<ComboboxSelected>>", self._on_preset_change
        )
        self._api_url_entry = self._add_entry(
            corpo, "API URL", self._api_url_var
        )
        self._model_entry = self._add_entry(corpo, "Modelo", self._model_var)
        self._api_key_entry = self._add_entry(
            corpo, "Chave de API", self._api_key_var, show="*"
        )
        self._rpm_spin = self._add_spin(corpo, "RPM", self._rpm_var)

        botoes = ttk.Frame(corpo)
        botoes.pack(fill=tk.X, pady=(8, 0))
        self._save_btn = ttk.Button(
            botoes, text="Salvar", command=self._salvar
        )
        self._save_btn.pack(side=tk.RIGHT, padx=2)
        self._cancel_btn = ttk.Button(
            botoes, text="Cancelar", command=self.destroy
        )
        self._cancel_btn.pack(side=tk.RIGHT, padx=2)
        self._test_btn = ttk.Button(
            botoes, text="Testar", command=self._on_testar
        )
        self._test_btn.pack(side=tk.LEFT, padx=2)
        self._widgets_config.append(self._save_btn)

        ttk.Label(
            corpo,
            textvariable=self._status_var,
            wraplength=360,
            foreground="gray",
        ).pack(fill=tk.X, pady=(8, 0))

    def _add_entry(
        self: "LLMConfigDialog",
        parent: tk.Widget,
        rotulo: str,
        var: tk.StringVar,
        *,
        show: str | None = None,
    ) -> ttk.Entry:
        """Adiciona uma linha de campo de texto e a registra para bloqueio."""
        linha = ttk.Frame(parent)
        linha.pack(fill=tk.X, pady=2)
        ttk.Label(linha, text=rotulo, width=12).pack(side=tk.LEFT)
        entry = ttk.Entry(linha, textvariable=var, show=show)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._widgets_config.append(entry)
        return entry

    def _add_combo(
        self: "LLMConfigDialog",
        parent: tk.Widget,
        rotulo: str,
        var: tk.StringVar,
        valores: list[str],
    ) -> ttk.Combobox:
        """Adiciona uma linha de combobox somente-leitura."""
        linha = ttk.Frame(parent)
        linha.pack(fill=tk.X, pady=2)
        ttk.Label(linha, text=rotulo, width=12).pack(side=tk.LEFT)
        combo = ttk.Combobox(
            linha, textvariable=var, values=valores, state="readonly"
        )
        combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._widgets_config.append(combo)
        return combo

    def _add_spin(
        self: "LLMConfigDialog",
        parent: tk.Widget,
        rotulo: str,
        var: tk.StringVar,
    ) -> ttk.Spinbox:
        """Adiciona uma linha de seletor numérico de RPM."""
        linha = ttk.Frame(parent)
        linha.pack(fill=tk.X, pady=2)
        ttk.Label(linha, text=rotulo, width=12).pack(side=tk.LEFT)
        spin = ttk.Spinbox(linha, from_=1, to=60, textvariable=var)
        spin.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._widgets_config.append(spin)
        return spin

    def _carregar(self: "LLMConfigDialog") -> None:
        """Preenche os campos com a configuração salva."""
        config = load_llm_config(self._config_path)
        self._provider_var.set(config["provider"])
        self._api_url_var.set(config["api_url"])
        self._model_var.set(config["model"])
        self._api_key_var.set(config["api_key"])
        self._rpm_var.set(str(config["rpm"]))

    def _on_preset_change(
        self: "LLMConfigDialog", event: tk.Event | None = None
    ) -> None:
        """Preenche modelo e API URL conforme o preset selecionado."""
        preset = self._presets.get(self._provider_var.get())
        if preset is None:
            return
        self._model_var.set(preset["model"])
        self._api_url_var.set(preset["api_url"])

    def _rpm(self: "LLMConfigDialog") -> int:
        """Retorna o RPM informado, caindo no padrão 5 quando inválido."""
        try:
            return int(self._rpm_var.get())
        except (TypeError, ValueError):
            return 5

    def _coletar_config(self: "LLMConfigDialog") -> dict:
        """Monta a configuração a partir dos valores atualmente preenchidos."""
        return {
            "provider": self._provider_var.get(),
            "api_url": self._api_url_var.get().strip(),
            "model": self._model_var.get().strip(),
            "api_key": self._api_key_var.get().strip(),
            "rpm": self._rpm(),
        }

    def _salvar(self: "LLMConfigDialog") -> None:
        """Grava o bloco ``llm.chat`` e fecha o diálogo."""
        save_llm_config(self._coletar_config(), self._config_path)
        self.destroy()

    def _on_testar(self: "LLMConfigDialog") -> None:
        """Inicia o teste de conexão, impedindo execuções concorrentes."""
        if self._testando or not self._deps_ok:
            return
        self._testando = True
        self._atualizar_botao_teste()
        self._status_var.set(MENSAGEM_TESTANDO)
        fila: queue.Queue = queue.Queue()
        self._fila = fila
        config = self._coletar_config()
        threading.Thread(
            target=self._executar_teste,
            args=(config, fila),
            daemon=True,
        ).start()
        self.after(0, lambda: self._verificar_teste(fila))

    def _executar_teste(
        self: "LLMConfigDialog", config: dict, fila: queue.Queue
    ) -> None:
        """Executa a completion de teste em thread de trabalho."""
        try:
            provedor = create_llm_provider(config)
            resposta = provedor.complete(
                [{"role": "user", "content": TEXTO_TESTE}]
            )
        except LLMError as exc:
            fila.put(("erro", str(exc), config, exc))
        except Exception as exc:
            fila.put(("erro", str(exc), config, exc))
        else:
            fila.put(("ok", resposta, config, None))

    @staticmethod
    def _registrar_falha(
        config: dict, exc: Exception
    ) -> None:
        """Registra a falha do teste de conexão para análise posterior.

        A chave de API nunca é registrada. O provedor, o modelo e a API URL
        identificam a configuração usada no teste.
        """
        logger.warning(
            "Teste de conexão da LLM falhou "
            "(provider=%s, model=%s, api_url=%s): %s: %s",
            config.get("provider"),
            config.get("model"),
            config.get("api_url"),
            type(exc).__name__,
            exc,
        )

    def _verificar_teste(
        self: "LLMConfigDialog", fila: queue.Queue
    ) -> None:
        """Consome o desfecho do teste na thread do Tk, reabilitando o botão."""
        try:
            estado, mensagem, config, exc = fila.get_nowait()
        except queue.Empty:
            self.after(20, lambda: self._verificar_teste(fila))
            return
        self._testando = False
        self._atualizar_botao_teste()
        if estado == "ok":
            self._status_var.set(MENSAGEM_SUCESSO.format(resposta=mensagem))
        else:
            if exc is not None:
                self._registrar_falha(config, exc)
            self._status_var.set(mensagem)

    def _atualizar_botao_teste(self: "LLMConfigDialog") -> None:
        """Habilita o botão "Testar" somente com deps presentes e ocioso."""
        estado = (
            tk.NORMAL if self._deps_ok and not self._testando else tk.DISABLED
        )
        self._test_btn.config(state=estado)

    def _aplicar_deps(self: "LLMConfigDialog") -> None:
        """Bloqueia a configuração quando as dependências ``[llm]`` faltam."""
        self._deps_ok = check_llm_deps()
        if self._deps_ok:
            return
        for widget in self._widgets_config:
            widget.config(state=tk.DISABLED)
        self._status_var.set(MENSAGEM_DEPS)
        self._atualizar_botao_teste()
