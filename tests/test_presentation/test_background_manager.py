"""Testes headless do gerenciador de jobs em background.

Cobrem o contrato base, as políticas de agendamento, o cancelamento por job, o
pump e o watchdog sem depender de ``DISPLAY`` nem de ``tk.Tk``.
"""

import threading
from pathlib import Path

import flowscope
from flowscope.presentation.gui.background import (
    BackgroundManager,
    EstadoJob,
    JobContext,
    JobHandle,
    Politica,
)
from tests.architecture import guardrail

_PACOTE_BACKGROUND = (
    Path(flowscope.__file__).resolve().parent
    / "presentation"
    / "gui"
    / "background"
)


class _AgendadorFake:
    """Agendador que registra callbacks para execução controlada pelo teste."""

    def __init__(self) -> None:
        self.pendentes = []

    def __call__(self, ms: int, callback) -> object:
        self.pendentes.append(callback)
        return callback

    def executar_proximo(self) -> None:
        """Executa o próximo callback agendado."""
        callback = self.pendentes.pop(0)
        callback()

    def esgotar(self) -> None:
        """Executa todos os callbacks agendados até a fila esvaziar."""
        while self.pendentes:
            self.executar_proximo()


class _Relogio:
    """Relógio controlável para os testes do watchdog."""

    def __init__(self, inicio: float = 0.0) -> None:
        self.agora = inicio

    def __call__(self) -> float:
        return self.agora

    def avancar(self, segundos: float) -> None:
        """Avança o relógio em ``segundos``."""
        self.agora += segundos


class TestContratoBase:
    def test_contexto_nao_expoe_widgets(self):
        handle = JobHandle(id=1, grupo="g", politica=Politica.PARALLEL)
        eventos = []
        contexto = JobContext(handle, eventos.append)

        assert contexto.handle is handle
        assert contexto.token is handle.token
        assert contexto.cancelled is False
        assert not any(
            type(getattr(contexto, nome, None)).__module__.startswith("tkinter")
            for nome in dir(contexto)
        )

    def test_contexto_publica_eventos_tipados(self):
        handle = JobHandle(id=1, grupo="g", politica=Politica.PARALLEL)
        eventos = []
        contexto = JobContext(handle, eventos.append)

        contexto.progress("baixando", 1, 3)
        contexto.resultado([1, 2])
        contexto.erro(RuntimeError("boom"))

        assert [type(e).__name__ for e in eventos] == [
            "Progresso",
            "Resultado",
            "Erro",
        ]

    def test_pacote_background_nao_importa_infrastructure(self):
        for caminho in sorted(_PACOTE_BACKGROUND.glob("*.py")):
            camadas = guardrail.imported_layers(caminho.read_text(encoding="utf-8"))
            assert "infrastructure" not in camadas, caminho

    def test_guardrail_de_fronteiras_permanece_verde(self):
        violacoes = {
            v
            for v in guardrail.find_violations(Path(flowscope.__file__).parent)
            if v[0].startswith("presentation/gui/background/")
        }
        assert violacoes == set()


class TestPoliticaParallel:
    def test_dois_jobs_independentes_coexistem(self):
        manager = BackgroundManager()
        liberar = threading.Event()
        prontos = threading.Barrier(2, timeout=2)

        def trabalho(ctx):
            prontos.wait()
            liberar.wait(2)

        h1 = manager.submit(trabalho, grupo="g", politica=Politica.PARALLEL)
        h2 = manager.submit(trabalho, grupo="g", politica=Politica.PARALLEL)

        assert len(manager.jobs_ativos) == 2
        assert h1.estado is EstadoJob.EXECUTANDO
        assert h2.estado is EstadoJob.EXECUTANDO
        assert not h1.token.is_set
        assert not h2.token.is_set

        liberar.set()
        h1.thread.join(2)
        h2.thread.join(2)
        manager.drenar()
        assert manager.jobs_ativos == ()


class TestPoliticaLatestWins:
    def test_substitui_job_anterior_e_novo_token_limpo(self):
        manager = BackgroundManager()
        liberar = threading.Event()
        terminados = []
        manager.ao_terminar(terminados.append)

        def trabalho(ctx):
            liberar.wait(2)

        h1 = manager.submit(trabalho, grupo="g", politica=Politica.LATEST_WINS)
        h2 = manager.submit(trabalho, grupo="g", politica=Politica.LATEST_WINS)

        assert h1.estado is EstadoJob.CANCELADO
        assert h1.token.is_set is True
        assert h2.estado is EstadoJob.EXECUTANDO
        assert h2.token.is_set is False
        assert manager.jobs_ativos == (h2,)
        assert terminados == [h1]

        liberar.set()
        h1.thread.join(2)
        h2.thread.join(2)
        manager.drenar()

    def test_chave_identica_descarta_sem_cancelar_ativo(self):
        manager = BackgroundManager()
        liberar = threading.Event()

        def trabalho(ctx):
            liberar.wait(2)

        h1 = manager.submit(
            trabalho, grupo="g", politica=Politica.LATEST_WINS, chave="k"
        )
        h2 = manager.submit(
            trabalho, grupo="g", politica=Politica.LATEST_WINS, chave="k"
        )

        assert h2.estado is EstadoJob.DESCARTADO
        assert h1.estado is EstadoJob.EXECUTANDO
        assert h1.token.is_set is False
        assert manager.jobs_ativos == (h1,)

        liberar.set()
        h1.thread.join(2)
        manager.drenar()


class TestPoliticaSerialize:
    def test_nao_paraleliza_e_respeita_fifo(self):
        manager = BackgroundManager()
        liberar = threading.Event()
        ordem = []

        def trabalho(nome):
            def executar(ctx):
                ordem.append(("inicio", nome))
                liberar.wait(2)
                ordem.append(("fim", nome))

            return executar

        h1 = manager.submit(
            trabalho("a"), grupo="g", politica=Politica.SERIALIZE
        )
        h2 = manager.submit(
            trabalho("b"), grupo="g", politica=Politica.SERIALIZE
        )

        assert h1.estado is EstadoJob.EXECUTANDO
        assert h2.estado is EstadoJob.PENDENTE
        assert manager.jobs_ativos == (h1,)

        liberar.set()
        h1.thread.join(2)
        manager.drenar()

        assert h2.estado is EstadoJob.EXECUTANDO
        h2.thread.join(2)
        manager.drenar()

        assert ordem == [
            ("inicio", "a"),
            ("fim", "a"),
            ("inicio", "b"),
            ("fim", "b"),
        ]

    def test_chave_duplicada_e_descartada(self):
        manager = BackgroundManager()
        liberar = threading.Event()

        def trabalho(ctx):
            liberar.wait(2)

        h1 = manager.submit(
            trabalho, grupo="g", politica=Politica.SERIALIZE, chave="k"
        )
        h2 = manager.submit(
            trabalho, grupo="g", politica=Politica.SERIALIZE, chave="k"
        )
        h3 = manager.submit(
            trabalho, grupo="g", politica=Politica.SERIALIZE, chave="outra"
        )
        h4 = manager.submit(
            trabalho, grupo="g", politica=Politica.SERIALIZE, chave="outra"
        )

        assert h1.estado is EstadoJob.EXECUTANDO
        assert h2.estado is EstadoJob.DESCARTADO
        assert h3.estado is EstadoJob.PENDENTE
        assert h4.estado is EstadoJob.DESCARTADO

        liberar.set()
        h1.thread.join(2)
        manager.drenar()
        h3.thread.join(2)
        manager.drenar()


class TestConfirmacao:
    def test_handshake_despachado_na_thread_do_agendamento(self):
        agendador = _AgendadorFake()
        manager = BackgroundManager(agendador)
        principal = threading.current_thread()
        vistos = []
        recebido = []

        def trabalho(ctx):
            recebido.append(ctx.confirmar(4, ["a", "b"], timeout=2))

        def ao_evento(evento):
            vistos.append(
                (threading.current_thread(), evento.quantidade, evento.nomes)
            )
            evento.caixa["ok"] = True
            evento.evento.set()

        handle = manager.submit(trabalho, grupo="g", ao_evento=ao_evento)
        agendador.esgotar()
        handle.thread.join(2)
        manager.drenar()

        assert recebido == [True]
        assert vistos == [(principal, 4, ["a", "b"])]

    def test_cancelamento_libera_worker_bloqueado_na_confirmacao(self):
        manager = BackgroundManager()
        iniciado = threading.Event()
        recebido = []

        def trabalho(ctx):
            iniciado.set()
            recebido.append(ctx.confirmar(4, ["a"], timeout=5))

        handle = manager.submit(trabalho, grupo="g", ao_evento=lambda evento: None)
        assert iniciado.wait(2)

        manager.cancel(handle.id)
        handle.thread.join(2)

        assert recebido == [False]


class TestCancelamento:
    def _manager_com_jobs(self):
        manager = BackgroundManager()
        liberar = threading.Event()

        def trabalho(ctx):
            liberar.wait(2)

        h1 = manager.submit(trabalho, grupo="a", politica=Politica.PARALLEL)
        h2 = manager.submit(trabalho, grupo="b", politica=Politica.PARALLEL)
        return manager, liberar, h1, h2

    def test_cancelamento_isolado_por_job(self):
        manager, liberar, h1, h2 = self._manager_com_jobs()

        manager.cancel(h1.id)

        assert h1.estado is EstadoJob.CANCELADO
        assert h1.token.is_set is True
        assert h2.estado is EstadoJob.EXECUTANDO
        assert h2.token.is_set is False
        assert manager.jobs_ativos == (h2,)

        liberar.set()
        h1.thread.join(2)
        h2.thread.join(2)
        manager.drenar()

    def test_cancel_group_nao_afeta_outros_grupos(self):
        manager, liberar, h1, h2 = self._manager_com_jobs()

        manager.cancel_group("a")

        assert h1.estado is EstadoJob.CANCELADO
        assert h2.estado is EstadoJob.EXECUTANDO

        liberar.set()
        h1.thread.join(2)
        h2.thread.join(2)
        manager.drenar()

    def test_cancel_all_encerra_todos(self):
        manager, liberar, h1, h2 = self._manager_com_jobs()

        manager.cancel_all()

        assert h1.estado is EstadoJob.CANCELADO
        assert h2.estado is EstadoJob.CANCELADO
        assert manager.jobs_ativos == ()

        liberar.set()
        h1.thread.join(2)
        h2.thread.join(2)

    def test_cancel_all_descarta_fila_serializada(self):
        manager = BackgroundManager()
        liberar = threading.Event()

        def trabalho(ctx):
            liberar.wait(2)

        h1 = manager.submit(trabalho, grupo="g", politica=Politica.SERIALIZE)
        h2 = manager.submit(trabalho, grupo="g", politica=Politica.SERIALIZE)

        manager.cancel_all()

        assert h1.estado is EstadoJob.CANCELADO
        assert h2.estado is EstadoJob.DESCARTADO

        liberar.set()
        h1.thread.join(2)


class TestPump:
    def test_callback_e_chamado_na_thread_do_agendamento(self):
        agendador = _AgendadorFake()
        manager = BackgroundManager(agendador)
        principal = threading.current_thread()
        vistos = []

        def trabalho(ctx):
            ctx.progress("baixando", 1, 1)

        handle = manager.submit(
            trabalho,
            grupo="g",
            ao_progresso=lambda evento: vistos.append(threading.current_thread()),
        )
        handle.thread.join(2)

        agendador.executar_proximo()

        assert vistos == [principal]

    def test_pump_para_sem_agendamento_orfao_apos_ultimo_job(self):
        agendador = _AgendadorFake()
        manager = BackgroundManager(agendador)

        handle = manager.submit(lambda ctx: None, grupo="g")
        assert agendador.pendentes

        handle.thread.join(2)
        agendador.esgotar()

        assert agendador.pendentes == []
        assert manager._pump.agendado is False

    def test_pump_religa_ao_submeter_novo_job(self):
        agendador = _AgendadorFake()
        manager = BackgroundManager(agendador)

        handle = manager.submit(lambda ctx: None, grupo="g")
        handle.thread.join(2)
        agendador.esgotar()

        handle2 = manager.submit(lambda ctx: None, grupo="g")
        assert agendador.pendentes
        handle2.thread.join(2)
        agendador.esgotar()
        assert agendador.pendentes == []


class TestCicloDeVida:
    def test_falha_termina_e_balanceia(self):
        manager = BackgroundManager()
        iniciados = []
        terminados = []
        manager.ao_iniciar(iniciados.append)
        manager.ao_terminar(terminados.append)

        def trabalho(ctx):
            raise RuntimeError("boom")

        handle = manager.submit(trabalho, grupo="g", cancelavel=True)
        handle.thread.join(2)
        manager.drenar()

        assert iniciados == [handle]
        assert terminados == [handle]
        assert handle.estado is EstadoJob.CONCLUIDO
        assert manager.jobs_ativos == ()

    def test_cancelamento_termina_e_balanceia(self):
        manager = BackgroundManager()
        terminados = []
        manager.ao_terminar(terminados.append)
        liberar = threading.Event()

        handle = manager.submit(
            lambda ctx: liberar.wait(2), grupo="g", cancelavel=True
        )
        manager.cancel(handle.id)

        assert terminados == [handle]
        assert handle.estado is EstadoJob.CANCELADO

        liberar.set()
        handle.thread.join(2)


class TestWatchdog:
    def test_job_morto_sem_termino_e_encerrado(self):
        manager = BackgroundManager()
        handle = JobHandle(id=99, grupo="g", politica=Politica.PARALLEL)
        thread = threading.Thread(target=lambda: None)
        thread.start()
        thread.join()
        handle.thread = thread
        handle.estado = EstadoJob.EXECUTANDO
        handle.ultima_atividade = manager._relogio()
        manager._jobs[handle.id] = handle
        terminados = []
        manager.ao_terminar(terminados.append)

        manager.drenar()

        assert handle.estado is EstadoJob.CONCLUIDO
        assert terminados == [handle]

    def test_job_sem_progresso_e_encerrado_por_inatividade(self):
        relogio = _Relogio()
        manager = BackgroundManager(limite_inatividade_s=120.0, relogio=relogio)
        liberar = threading.Event()

        handle = manager.submit(
            lambda ctx: liberar.wait(2), grupo="g"
        )
        relogio.avancar(120.1)

        manager.drenar()

        assert handle.estado is EstadoJob.CANCELADO
        assert handle.token.is_set is True
        assert manager.jobs_ativos == ()

        liberar.set()
        handle.thread.join(2)
