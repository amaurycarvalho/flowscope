import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest

from flowscope.infrastructure.action_lock import (
    ActionLock,
    OperacaoEmAndamento,
    caminho_lock_global,
)

_SCRIPT_HOLD = textwrap.dedent(
    """
    import sys
    import time
    from pathlib import Path

    from flowscope.infrastructure.action_lock import ActionLock

    lock = ActionLock(Path(sys.argv[1]), intervalo=0.02)
    lock.adquirir()
    print("READY", flush=True)
    time.sleep(float(sys.argv[2]))
    """
)


class TestActionLock:
    def test_adquire_e_libera(self, tmp_path):
        caminho = tmp_path / "acao.lock"
        lock = ActionLock(caminho)
        lock.adquirir()
        assert lock.retido
        lock.liberar()
        assert not lock.retido

    def test_context_manager_libera(self, tmp_path):
        caminho = tmp_path / "acao.lock"
        with ActionLock(caminho) as lock:
            assert lock.retido
        assert not lock.retido

    def test_reentrada_apos_liberacao(self, tmp_path):
        caminho = tmp_path / "acao.lock"
        ActionLock(caminho).adquirir().liberar()
        ActionLock(caminho).adquirir().liberar()

    def test_reentrante_no_mesmo_processo(self, tmp_path):
        caminho = tmp_path / "acao.lock"
        externo = ActionLock(caminho).adquirir()
        interno = ActionLock(caminho).adquirir(esperar=0.1)
        assert interno.retido
        interno.liberar()
        assert externo.retido
        externo.liberar()

    def test_threads_do_mesmo_processo_se_excluem(self, tmp_path):
        import threading

        caminho = tmp_path / "acao.lock"
        externo = ActionLock(caminho).adquirir()
        erros = []

        def tentar():
            try:
                ActionLock(caminho, intervalo=0.02).adquirir(esperar=0.2)
            except OperacaoEmAndamento:
                erros.append(1)

        thread = threading.Thread(target=tentar)
        thread.start()
        thread.join(timeout=5)
        assert erros == [1]
        externo.liberar()

    def test_segundo_processo_nao_adquire_enquanto_retido(self, tmp_path):
        caminho = tmp_path / "acao.lock"
        processo = subprocess.Popen(
            [sys.executable, "-c", _SCRIPT_HOLD, str(caminho), "30"],
            stdout=subprocess.PIPE,
            text=True,
        )
        try:
            linha = processo.stdout.readline().strip()
            assert linha == "READY"
            with pytest.raises(OperacaoEmAndamento):
                ActionLock(caminho, intervalo=0.02).adquirir(esperar=0.3)
        finally:
            processo.terminate()
            processo.wait(timeout=10)

    def test_lock_liberado_ao_encerrar_processo(self, tmp_path):
        caminho = tmp_path / "acao.lock"
        processo = subprocess.Popen(
            [sys.executable, "-c", _SCRIPT_HOLD, str(caminho), "30"],
            stdout=subprocess.PIPE,
            text=True,
        )
        assert processo.stdout.readline().strip() == "READY"
        processo.terminate()
        processo.wait(timeout=10)
        ActionLock(caminho, intervalo=0.02).adquirir(esperar=2.0).liberar()

    def test_espera_adquire_quando_lock_e_soltado(self, tmp_path):
        caminho = tmp_path / "acao.lock"
        processo = subprocess.Popen(
            [sys.executable, "-c", _SCRIPT_HOLD, str(caminho), "1"],
            stdout=subprocess.PIPE,
            text=True,
        )
        assert processo.stdout.readline().strip() == "READY"
        inicio = time.monotonic()
        ActionLock(caminho, intervalo=0.02).adquirir(esperar=10.0).liberar()
        assert time.monotonic() - inicio >= 0.5
        processo.wait(timeout=10)

    def test_caminho_padrao_no_cache(self):
        caminho = caminho_lock_global(Path("/tmp/qualquer"))
        assert caminho.name == "flowscope.acao.lock"
        assert caminho.parent == Path("/tmp/qualquer")
