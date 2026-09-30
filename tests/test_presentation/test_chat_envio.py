"""Testes headless do heartbeat e do estado de envio do chat.

Cobrem o heartbeat que mantém o job vivo durante chamadas longas e a janela de
estado entre registrar a pergunta e submeter o trabalho, sem depender de
``DISPLAY`` nem de ``tk.Tk``.
"""

import threading
import time
from types import SimpleNamespace

from flowscope.domain.llm import LLMUsage
from flowscope.presentation.gui.background import BackgroundManager, EstadoJob
from flowscope.presentation.gui.chat.envio import EnvioMixin
from flowscope.presentation.gui.chat.tokens import ContadorTokens


class _CtxFake:
    def __init__(self) -> None:
        self.progressos = 0

    def progress(self, *args, **kwargs) -> None:
        self.progressos += 1


class _HostHeartbeat(EnvioMixin):
    def __init__(self, intervalo: float) -> None:
        self._heartbeat_intervalo = intervalo


class TestHeartbeat:
    def test_publica_progresso_periodico(self):
        host = _HostHeartbeat(0.01)
        ctx = _CtxFake()
        with host._heartbeat(ctx):
            time.sleep(0.06)
        assert ctx.progressos >= 2

    def test_para_ao_fim_do_bloco(self):
        host = _HostHeartbeat(0.01)
        ctx = _CtxFake()
        with host._heartbeat(ctx):
            time.sleep(0.03)
        total = ctx.progressos
        time.sleep(0.05)
        assert ctx.progressos == total


class TestWatchdogComHeartbeat:
    def test_heartbeat_mantem_job_vivo_alem_do_limite(self):
        manager = BackgroundManager(limite_inatividade_s=0.2)
        host = _HostHeartbeat(0.02)
        liberar = threading.Event()
        iniciado = threading.Event()

        def trabalho(ctx) -> None:
            iniciado.set()
            with host._heartbeat(ctx):
                liberar.wait(2)

        handle = manager.submit(trabalho, grupo="g")
        assert iniciado.wait(2)
        fim = time.time() + 0.6
        while time.time() < fim:
            manager.drenar()
            time.sleep(0.01)
        assert handle.estado is EstadoJob.EXECUTANDO
        assert handle.token.is_set is False

        liberar.set()
        handle.thread.join(2)
        manager.drenar()
        assert handle.estado is EstadoJob.CONCLUIDO


class _BackgroundFake:
    """Manager falso que inicia o job ao submeter, como o real."""

    def __init__(self) -> None:
        self.ativo = False
        self.submits = 0
        self.ao_iniciar_cb = None
        self.ao_terminar_cb = None

    def tem_ativo(self, grupo: str) -> bool:
        return self.ativo

    def ao_iniciar(self, callback) -> None:
        self.ao_iniciar_cb = callback

    def ao_terminar(self, callback) -> None:
        self.ao_terminar_cb = callback

    def submit(self, trabalho, **kwargs) -> None:
        self.submits += 1
        self.ativo = True
        if self.ao_iniciar_cb is not None:
            self.ao_iniciar_cb(None)

    def cancel_group(self, grupo: str) -> None:
        self.ativo = False


class _HostEnvio(EnvioMixin):
    def __init__(self) -> None:
        self._disponivel = True
        self._enviando = False
        self._background = _BackgroundFake()
        self._background.ao_iniciar(lambda _handle: self._on_job_iniciado())
        self._background.ao_terminar(lambda _handle: self._on_job_terminado())
        self._sessao = SimpleNamespace(messages=[])
        self._fundamental_data_provider = dict
        self._watchlist_provider = list
        self.processando_ao_registrar: list[bool] = []
        self.controles = 0

    def _texto_entrada(self) -> str:
        return "pergunta"

    def _texto_entrada_set(self, texto: str) -> None:
        return None

    def _registrar(self, role, texto, *args, **kwargs) -> None:
        self.processando_ao_registrar.append(self._processando)

    def _status(self, *args, **kwargs) -> None:
        return None

    def _atualizar_controles(self) -> None:
        self.controles += 1

    def _atender_confirmacao(self, confirmacao) -> None:
        return None


class _HostTokens(EnvioMixin):
    """Host headless para o acúmulo e a publicação do rótulo de tokens."""

    def __init__(self, *, janela: int = 0, cache: bool = False, contar=None) -> None:
        self._tokens = ContadorTokens()
        self.rotulos: list[str] = []
        self._tokens_callback = self.rotulos.append
        self._context_window_provider = lambda: janela
        self._cache_support_provider = lambda: cache
        self._token_counter_provider = lambda: contar


class _HostSemProviders(EnvioMixin):
    """Host headless sem os provedores de perfil de LLM."""


class TestTokensHeadless:
    def test_publica_rotulo_com_cache_e_percentual(self):
        host = _HostTokens(janela=128000, cache=True)
        host._acumular_uso(
            LLMUsage(entrada=6400, saida=100, entrada_cache=2400)
        )
        assert host.rotulos[-1] == (
            "Tokens: 4.0K entrada / 0.1K saída / 6.4K contexto (5%) "
            "· nav: 0.0K/32K"
        )

    def test_sem_janela_omite_percentual(self):
        host = _HostTokens()
        host._acumular_uso(LLMUsage(entrada=1000, saida=10))
        assert host.rotulos[-1] == (
            "Tokens: 1.0K entrada / 0.0K saída / 1.0K contexto · nav: 0.0K/32K"
        )

    def test_uso_nao_llm_e_ignorado(self):
        host = _HostTokens()
        host._acumular_uso("nao-e-uso")
        assert host.rotulos == []

    def test_accessores_toleram_ausencia_de_providers(self):
        host = _HostSemProviders()
        assert host._contar_tokens() is None
        assert host._cache_suportado() is False
        assert host._janela_contexto() == 0

    def test_accessores_toleram_provider_com_erro(self):
        host = _HostSemProviders()

        def explodir():
            raise RuntimeError("boom")

        host._context_window_provider = explodir
        host._token_counter_provider = explodir
        host._cache_support_provider = explodir
        assert host._contar_tokens() is None
        assert host._cache_suportado() is False
        assert host._janela_contexto() == 0

    def test_contador_e_suporte_resolvidos(self):
        def contar(texto: str) -> int:
            return len(texto)

        host = _HostTokens(janela=1000, cache=True, contar=contar)
        assert host._contar_tokens()("abc") == 3
        assert host._cache_suportado() is True
        assert host._janela_contexto() == 1000


class TestTransicaoEnvio:
    def test_processando_verdadeiro_ao_registrar(self):
        host = _HostEnvio()
        host._enviar()
        assert host.processando_ao_registrar == [True]

    def test_janela_fecha_ao_iniciar_o_job(self):
        host = _HostEnvio()
        host._enviar()
        assert host._background.submits == 1
        assert host._enviando is False
        assert host._processando is True

    def test_processando_considera_enviando(self):
        host = _HostEnvio()
        assert host._processando is False
        host._enviando = True
        assert host._processando is True
