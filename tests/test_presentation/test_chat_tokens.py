"""Testes headless do contador de tokens e do rótulo na barra de status."""

from types import SimpleNamespace

from flowscope.domain.llm import LLMUsage
from flowscope.presentation.gui.app_status import StatusMixin
from flowscope.presentation.gui.app_tab_actions import TabActionsMixin
from flowscope.presentation.gui.app_tabs import CHAT_AI_TAB
from flowscope.presentation.gui.chat.tokens import (
    ContadorTokens,
    formatar_k,
    formatar_tokens,
)


class _LabelFake:
    """Rótulo falso que registra empacotamento e texto."""

    def __init__(self) -> None:
        self.empacotado = False
        self.texto: str | None = None
        self.packs = 0
        self.forgets = 0

    def winfo_ismapped(self) -> bool:
        return self.empacotado

    def pack(self, **_kwargs) -> None:
        self.packs += 1
        self.empacotado = True

    def pack_forget(self) -> None:
        self.forgets += 1
        self.empacotado = False

    def config(self, **kwargs) -> None:
        if "text" in kwargs:
            self.texto = kwargs["text"]


class _HostStatus(StatusMixin):
    def __init__(self) -> None:
        self._tokens_label = _LabelFake()


class TestFormatacao:
    def test_zero(self):
        assert formatar_k(0) == "0.0K"

    def test_abaixo_de_mil(self):
        assert formatar_k(340) == "0.3K"

    def test_acima_de_mil(self):
        assert formatar_k(5540) == "5.5K"

    def test_milhar_exato(self):
        assert formatar_k(1000) == "1.0K"

    def test_arredondamento(self):
        assert formatar_k(9949) == "9.9K"
        assert formatar_k(9999) == "10.0K"

    def test_texto_completo(self):
        assert formatar_tokens(5540, 340) == (
            "Tokens: 5.5K entrada · 0.3K saída"
        )


class TestContadorTokens:
    def test_inicia_zerado(self):
        contador = ContadorTokens()
        assert contador.texto() == "Tokens: 0.0K entrada · 0.0K saída"

    def test_soma_uma_completion(self):
        contador = ContadorTokens()
        contador.acumular(LLMUsage(entrada=120, saida=40))
        assert contador.entrada == 120
        assert contador.saida == 40

    def test_cascata_soma_duas_chamadas(self):
        contador = ContadorTokens()
        contador.acumular(LLMUsage(entrada=100, saida=20))
        contador.acumular(LLMUsage(entrada=200, saida=30))
        assert contador.entrada == 300
        assert contador.saida == 50

    def test_zerar_reinicia(self):
        contador = ContadorTokens()
        contador.acumular(LLMUsage(entrada=100, saida=20))
        contador.zerar()
        assert contador.entrada == 0
        assert contador.saida == 0


class TestRotuloStatus:
    def test_set_tokens_atualiza_texto(self):
        host = _HostStatus()
        host._set_tokens("Tokens: 5.5K entrada · 0.3K saída")
        assert host._tokens_label.texto == "Tokens: 5.5K entrada · 0.3K saída"

    def test_mostrar_tokens_empacota_a_direita(self):
        host = _HostStatus()
        host._mostrar_tokens(True)
        assert host._tokens_label.empacotado is True

    def test_ocultar_tokens_desempacota(self):
        host = _HostStatus()
        host._mostrar_tokens(True)
        host._mostrar_tokens(False)
        assert host._tokens_label.empacotado is False
        assert host._tokens_label.forgets == 1

    def test_visivel_nao_reempacota(self):
        host = _HostStatus()
        host._mostrar_tokens(True)
        host._mostrar_tokens(True)
        assert host._tokens_label.packs == 1


class _HostAbas(TabActionsMixin):
    """Host headless que isola o ramo de abas do ``_on_tab_changed``."""

    def __init__(self, tabs) -> None:
        self._tabs = tabs
        self._prefs: dict = {}
        self._tab_content = {tabs: ("titulo", [])}
        self._current_data = None
        self._orientation_panel = SimpleNamespace(set_content=lambda *a: None)
        self.mostrar: list[bool] = []

    def _current_tabs(self):
        return self._tabs

    def _mostrar_tokens(self, visivel: bool) -> None:
        self.mostrar.append(visivel)

    def _resolve_chart(self, main_tab, sub_tab):
        return None

    def _sync_fundamental_refresh_visibility(self, *args) -> None:
        return None

    def _sync_copy_button_for_tab(self, *args) -> None:
        return None

    def _reavaliar_chat_llm(self) -> None:
        return None


class TestVisibilidadePorAba:
    def test_mostra_na_aba_chat(self):
        host = _HostAbas((CHAT_AI_TAB, CHAT_AI_TAB))
        host._on_tab_changed()
        assert host.mostrar == [True]

    def test_oculta_em_outra_aba(self):
        host = _HostAbas(("Análise Geral", "VWAP"))
        host._on_tab_changed()
        assert host.mostrar == [False]
