"""Diálogo de configuração de LLM da interface gráfica.

Oferece seleção de preset, API URL, modelo, chave de API mascarada e RPM, além
de persistir o bloco ``llm.chat`` e testar a conexão com o provedor em thread
de trabalho, publicando o desfecho na thread do Tk por fila.
"""

import logging
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import ttk

from flowscope.application.llm_config_port import LLMConfigPort
from flowscope.domain.llm import LLMError
from flowscope.presentation.gui.background.context import JobContext
from flowscope.presentation.gui.background.events import Resultado
from flowscope.presentation.gui.background.job import Politica
from flowscope.presentation.gui.background.manager import BackgroundManager
from flowscope.presentation.gui.llm.config_form import LLMConfigForm
from flowscope.presentation.gui.llm.mensagens import mensagem_erro_llm

logger = logging.getLogger("flowscope")

#: Grupo de exclusão do teste de conexão da LLM.
GRUPO_TESTE = "llm_teste"

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


def _normalizar_campo(valor: object) -> str:
    """Normaliza um campo de conexão para comparação de assinatura."""
    return str(valor or "").strip()


def assinatura_conexao(config: dict) -> str:
    """Monta a identidade de conexão (provedor, URL, modelo e chave).

    O ``rpm`` não integra a assinatura por não afetar a conexão. A URL perde a
    barra final para que variações equivalentes não invalidem o teste.
    """
    provider = _normalizar_campo(config.get("provider"))
    api_url = _normalizar_campo(config.get("api_url")).rstrip("/")
    model = _normalizar_campo(config.get("model"))
    api_key = _normalizar_campo(config.get("api_key"))
    return repr((provider, api_url, model, api_key))


def deve_ativar(config: dict, assinatura_testada: str | None) -> bool:
    """Indica se o salvamento deve ativar o provedor do config informado.

    ``none`` sempre desativa; os demais provedores só são ativados quando o
    salvamento corresponde a um teste de conexão bem-sucedido na sessão.
    """
    provider = _normalizar_campo(config.get("provider")) or "none"
    if provider == "none":
        return True
    return (
        assinatura_testada is not None
        and assinatura_conexao(config) == assinatura_testada
    )


class LLMConfigDialog(tk.Toplevel):
    """Janela de configuração do provedor de LLM."""

    def __init__(
        self: "LLMConfigDialog",
        parent: tk.Misc,
        *,
        config_port: LLMConfigPort,
        config_path: Path | None = None,
        on_saved: Callable[[], None] | None = None,
        background: BackgroundManager | None = None,
    ) -> None:
        """Constrói o diálogo, carrega a configuração salva e aplica as deps."""
        super().__init__(parent)
        self.title("Configuração de I.A.")
        self._port = config_port
        self._config_path = config_path
        self._on_saved = on_saved
        self._form = LLMConfigForm(config_port, config_path)
        self._widgets_config: list[tk.Widget] = []
        self._background = (
            background if background is not None else BackgroundManager(self.after)
        )
        self._testando = False
        self._deps_ok = True
        self._assinatura_testada: str | None = None
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

    def destroy(self: "LLMConfigDialog") -> None:
        """Cancela os testes em background antes de destruir o diálogo."""
        background = getattr(self, "_background", None)
        if background is not None:
            background.cancel_all()
        super().destroy()

    def _build(self: "LLMConfigDialog") -> None:
        """Constrói os campos, os botões e a área de status."""
        corpo = ttk.Frame(self, padding=10)
        corpo.pack(fill=tk.BOTH, expand=True)
        self._provider_combo = self._add_combo(
            corpo, "Provedor", self._provider_var, self._form.presets
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
        """Preenche os campos com a configuração salva do provedor ativo."""
        self._form.carregar_inicial()
        self._refletir_modelo()

    def _sincronizar_modelo(self: "LLMConfigDialog") -> None:
        """Copia os valores dos ``StringVar`` para o modelo puro."""
        self._form.provider = self._provider_var.get()
        self._form.api_url = self._api_url_var.get()
        self._form.model = self._model_var.get()
        self._form.api_key = self._api_key_var.get()
        self._form.rpm = self._rpm_var.get()

    def _refletir_modelo(self: "LLMConfigDialog") -> None:
        """Copia os valores do modelo puro para os ``StringVar``."""
        self._provider_var.set(self._form.provider)
        self._api_url_var.set(self._form.api_url)
        self._model_var.set(self._form.model)
        self._api_key_var.set(self._form.api_key)
        self._rpm_var.set(self._form.rpm)

    def _on_preset_change(
        self: "LLMConfigDialog", event: tk.Event | None = None
    ) -> None:
        """Restaura a configuração do provedor selecionado ao trocar o preset."""
        self._sincronizar_modelo()
        self._form.trocar_provider(self._provider_var.get())
        self._refletir_modelo()

    def _coletar_config(self: "LLMConfigDialog") -> dict:
        """Monta a configuração a partir dos valores atualmente preenchidos."""
        self._sincronizar_modelo()
        return self._form.coletar_config()

    def _salvar(self: "LLMConfigDialog") -> None:
        """Grava o bloco ``llm.chat``, ativando só se o salvo foi testado."""
        config = self._coletar_config()
        ativar = deve_ativar(config, self._assinatura_testada)
        self._port.save_llm_config(config, self._config_path, ativar=ativar)
        if self._on_saved is not None:
            self._on_saved()
        self.destroy()

    def _on_testar(self: "LLMConfigDialog") -> None:
        """Inicia o teste de conexão, impedindo execuções concorrentes."""
        if self._testando or not self._deps_ok:
            return
        self._testando = True
        self._atualizar_botao_teste()
        self._status_var.set(MENSAGEM_TESTANDO)
        config = self._coletar_config()
        self._background.submit(
            lambda ctx: self._executar_teste(ctx, config),
            grupo=GRUPO_TESTE,
            politica=Politica.PARALLEL,
            ao_resultado=self._aplicar_resultado_teste,
        )

    def _executar_teste(
        self: "LLMConfigDialog", ctx: JobContext, config: dict
    ) -> None:
        """Executa a completion de teste fora da thread do Tk."""
        try:
            provedor = self._port.create_provider(config)
            resposta = provedor.complete(
                [{"role": "user", "content": TEXTO_TESTE}]
            )
        except LLMError as exc:
            ctx.resultado(valor=("erro", str(exc), config, exc))
        except Exception as exc:
            ctx.resultado(valor=("erro", str(exc), config, exc))
        else:
            ctx.resultado(valor=("ok", resposta.texto, config, None))

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

    def _aplicar_resultado_teste(
        self: "LLMConfigDialog", evento: Resultado
    ) -> None:
        """Aplica o desfecho do teste na thread do Tk, reabilitando o botão."""
        estado, mensagem, config, exc = evento.valor
        self._testando = False
        self._atualizar_botao_teste()
        if estado == "ok":
            self._assinatura_testada = assinatura_conexao(config)
            self._status_var.set(MENSAGEM_SUCESSO.format(resposta=mensagem))
        else:
            if exc is not None:
                self._registrar_falha(config, exc)
            self._status_var.set(
                mensagem_erro_llm(exc) if exc is not None else mensagem
            )

    def _atualizar_botao_teste(self: "LLMConfigDialog") -> None:
        """Habilita o botão "Testar" somente com deps presentes e ocioso."""
        estado = (
            tk.NORMAL if self._deps_ok and not self._testando else tk.DISABLED
        )
        self._test_btn.config(state=estado)

    def _aplicar_deps(self: "LLMConfigDialog") -> None:
        """Bloqueia a configuração quando as dependências ``[llm]`` faltam."""
        self._deps_ok = self._port.check_llm_deps()
        if self._deps_ok:
            return
        for widget in self._widgets_config:
            widget.config(state=tk.DISABLED)
        self._status_var.set(MENSAGEM_DEPS)
        self._atualizar_botao_teste()
