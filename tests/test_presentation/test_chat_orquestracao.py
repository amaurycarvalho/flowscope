"""Testes headless da orquestração de envio/cancelamento do painel de chat.

Exercitam o ciclo do job de envio (submissão, política ``latest_wins``,
cancelamento cooperativo e descarte do desfecho tardio) com o
:class:`BackgroundManager` real e um agendador fake — sem instanciar Tk. O host
registra mensagens e estados de controle no lugar dos widgets.
"""

import threading
import time

from flowscope.application.chat import ArvoreConhecimento
from flowscope.application.chat.arvore import no_interno
from flowscope.domain.chat import ChatMessage, ChatSession
from flowscope.domain.llm import LLMCommunicationError, LLMResposta
from flowscope.presentation.gui.background.context import JobContext
from flowscope.presentation.gui.background.events import Erro, Outcome
from flowscope.presentation.gui.background.job import JobHandle, Politica
from flowscope.presentation.gui.background.manager import BackgroundManager
from flowscope.presentation.gui.chat.envio import MENSAGEM_CANCELADO, EnvioMixin
from flowscope.presentation.gui.llm.mensagens import mensagem_erro_llm


class _AgendadorFake:
    """Agendador que retém os callbacks do pump para execução controlada."""

    def __init__(self) -> None:
        self.pendentes: list = []

    def __call__(self, ms: int, callback):
        self.pendentes.append(callback)
        return callback

    def executar(self) -> None:
        if self.pendentes:
            self.pendentes.pop(0)()


class _LLMBloqueante:
    """Porta de completion que bloqueia até ser liberada."""

    def __init__(self, liberar: threading.Event, resposta) -> None:
        self.liberar = liberar
        self.resposta = resposta
        self.chamadas = 0

    def complete(self, messages, system_prompt=None) -> LLMResposta:
        self.chamadas += 1
        resultado = self.resposta
        self.liberar.wait(3)
        if isinstance(resultado, BaseException):
            raise resultado
        return LLMResposta(texto=resultado)


def _arvore() -> ArvoreConhecimento:
    return ArvoreConhecimento(no_interno("/", "/"), assinatura="a")


class _Host(EnvioMixin):
    """Host headless do ``EnvioMixin`` com widgets substituídos por registros."""

    def __init__(self, llm, agendador: _AgendadorFake) -> None:
        self._background = BackgroundManager(agendador)
        self._background.ao_iniciar(lambda _handle: self._on_job_iniciado())
        self._background.ao_terminar(lambda _handle: self._on_job_terminado())
        self._ctx_atual = None
        self._enviando = False
        self._heartbeat_intervalo = 30.0
        self._disponivel = True
        self._llm = llm
        self._assinatura = None
        self._navegacao = []
        self._sessao = ChatSession()
        self._fundamental_data_provider = dict
        self._watchlist_provider = list
        self._confirmation_timeout = 5.0
        self._texto = ""
        self._status_msgs: list[str] = []
        self._conteudo: list[str] = []

    def _texto_entrada(self) -> str:
        return self._texto

    def _texto_entrada_set(self, texto: str) -> None:
        self._texto = texto

    def _criar_llm(self):
        return self._llm

    def montar_arvore(self, fundamentos, watchlist):
        return _arvore()

    def _registrar(self, role, texto, fontes=None, enviar_ao_modelo=True) -> None:
        self._sessao.add_message(
            ChatMessage(
                role=role,
                content=texto,
                sources=list(fontes or []),
                enviar_ao_modelo=enviar_ao_modelo,
            )
        )
        self._conteudo.append(texto)
        self._atualizar_controles()

    def conteudo_sessao(self) -> str:
        return "\n".join(self._conteudo)

    def _concluir_ok(self, resposta) -> None:
        self._registrar("assistant", resposta.texto, resposta.fontes)
        self._status("Pronto.", "")

    def _concluir_erro(self, dados, exc) -> None:
        self._registrar(
            "assistant", mensagem_erro_llm(exc), enviar_ao_modelo=False
        )
        self._status(mensagem_erro_llm(exc), "⚠")

    def _atualizar_controles(self) -> None:
        return None

    def _status(self, msg: str, icon: str) -> None:
        self._status_msgs.append(msg)

    def _atender_confirmacao(self, confirmacao) -> None:
        confirmacao.caixa["ok"] = True
        confirmacao.evento.set()


def _girar(agendador: _AgendadorFake, condicao, timeout: float = 3.0) -> bool:
    """Executa ticks do pump até a condição valer, ou o timeout expirar."""
    fim = time.time() + timeout
    while time.time() < fim:
        agendador.executar()
        if condicao():
            return True
        time.sleep(0.005)
    return bool(condicao())


class TestEnvioCancelamento:
    def test_envio_fica_processando_ate_o_termino(self):
        agendador = _AgendadorFake()
        liberar = threading.Event()
        llm = _LLMBloqueante(liberar, '{"resposta": "tardia", "documentos": []}')
        host = _Host(llm, agendador)
        host._texto = "pergunta"

        host._enviar()
        assert _girar(agendador, lambda: llm.chamadas == 1)
        assert host._processando is True

        liberar.set()
        assert _girar(agendador, lambda: not host._processando)
        assert "tardia" in host.conteudo_sessao()

    def test_cancelar_restaura_controles(self):
        agendador = _AgendadorFake()
        liberar = threading.Event()
        llm = _LLMBloqueante(liberar, '{"resposta": "tardia", "documentos": []}')
        host = _Host(llm, agendador)
        host._texto = "pergunta"

        host._enviar()
        assert _girar(agendador, lambda: llm.chamadas == 1)
        host._cancelar_envio()
        assert host._processando is False
        assert MENSAGEM_CANCELADO in host._status_msgs

        liberar.set()

    def test_desfecho_tardio_descartado(self):
        agendador = _AgendadorFake()
        liberar = threading.Event()
        llm = _LLMBloqueante(
            liberar, '{"resposta": "resposta tardia", "documentos": []}'
        )
        host = _Host(llm, agendador)
        host._texto = "pergunta"

        host._enviar()
        assert _girar(agendador, lambda: llm.chamadas == 1)
        job = host._background.jobs_ativos[0]
        host._cancelar_envio()
        liberar.set()
        job.thread.join(2)
        _girar(agendador, lambda: True)

        assert "resposta tardia" not in host.conteudo_sessao()

    def test_falha_tardia_descartada(self):
        agendador = _AgendadorFake()
        liberar = threading.Event()
        llm = _LLMBloqueante(liberar, LLMCommunicationError("falha tardia"))
        host = _Host(llm, agendador)
        host._texto = "pergunta"

        host._enviar()
        assert _girar(agendador, lambda: llm.chamadas == 1)
        job = host._background.jobs_ativos[0]
        host._cancelar_envio()
        liberar.set()
        job.thread.join(2)
        _girar(agendador, lambda: True)

        assert "falha tardia" not in host.conteudo_sessao()

    def test_novo_envio_apos_cancelar(self):
        agendador = _AgendadorFake()
        liberar = threading.Event()
        llm = _LLMBloqueante(liberar, '{"resposta": "primeira", "documentos": []}')
        host = _Host(llm, agendador)

        host._texto = "um"
        host._enviar()
        assert _girar(agendador, lambda: llm.chamadas == 1)
        job = host._background.jobs_ativos[0]
        host._cancelar_envio()
        llm.resposta = '{"resposta": "segunda", "documentos": []}'
        liberar.set()
        job.thread.join(2)
        _girar(agendador, lambda: True)

        host._texto = "dois"
        host._enviar()
        assert _girar(agendador, lambda: "segunda" in host.conteudo_sessao())
        conteudo = host.conteudo_sessao()
        assert "segunda" in conteudo
        assert "primeira" not in conteudo


class TestFalhaFatalDoEnvio:
    def test_falha_llm_publica_erro_fatal(self):
        agendador = _AgendadorFake()
        liberar = threading.Event()
        liberar.set()
        llm = _LLMBloqueante(liberar, LLMCommunicationError("falha"))
        host = _Host(llm, agendador)
        eventos: list = []
        handle = JobHandle(id=1, grupo="chat", politica=Politica.LATEST_WINS)
        ctx = JobContext(handle, eventos.append)

        host._executar(ctx, "pergunta", {}, [], [])

        erros = [evento for evento in eventos if isinstance(evento, Erro)]
        assert erros
        assert erros[0].fatal is True
        assert handle.outcome is Outcome.FALHA
