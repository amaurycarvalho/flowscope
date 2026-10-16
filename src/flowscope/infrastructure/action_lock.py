"""Lock global de ação, cross-process, baseado em bloqueio de arquivo.

Serializa as fases de escrita no cache local entre processos (CLI, GUI e
servidor MCP) usando o bloqueio de arquivo do sistema operacional (``fcntl`` no
POSIX, ``msvcrt`` no Windows). Como o bloqueio pertence ao descritor de arquivo,
o sistema operacional o libera automaticamente quando o processo termina, sem
locks órfãos.

Dentro do processo, um :class:`threading.RLock` por caminho garante a exclusão
mútua entre threads (inclusive *reentrância* na mesma thread) e só então o
bloqueio do sistema operacional é tomado. Assim, um comando que já detém o lock
pode reusá-lo (por exemplo, ao gravar ``config.json``) sem bloquear a si mesmo,
enquanto processos distintos permanecem serializados.
"""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from types import TracebackType

if os.name == "nt":  # pragma: no cover - depende do sistema operacional
    import msvcrt
else:
    import fcntl

from flowscope.infrastructure.cache import CacheManager

#: Nome do arquivo de lock dentro do diretório de cache.
NOME_ARQUIVO_LOCK = "flowscope.acao.lock"

#: Intervalo entre tentativas de aquisição, em segundos.
_INTERVALO_PADRAO = 0.1

#: Protege os registros de RLocks, contagens e descritores.
_REGISTRO = threading.Lock()

#: RLock por caminho resolvido (exclusão mútua entre threads do processo).
_LOCKS: dict[str, threading.RLock] = {}

#: Profundidade de aquisições por caminho no processo.
_CONTAGEM: dict[str, int] = {}

#: Descritor de arquivo que detém o lock do SO por caminho.
_HANDLES: dict[str, int] = {}


class OperacaoEmAndamento(RuntimeError):
    """O lock global de ação já está retido por outro processo."""

    def __init__(self: OperacaoEmAndamento, caminho: Path) -> None:
        """Registra o caminho do lock disputado."""
        super().__init__(
            "Outra operação de escrita já está em andamento "
            f"(lock: {caminho})"
        )
        self.caminho = caminho


def caminho_lock_global(cache_dir: Path | None = None) -> Path:
    """Resolve o caminho padrão do arquivo do lock global de ação."""
    base = Path(cache_dir) if cache_dir is not None else CacheManager().get_cache_dir()
    return base / NOME_ARQUIVO_LOCK


def _rlock_de(chave: str) -> threading.RLock:
    """Devolve (criando quando preciso) o RLock do caminho."""
    with _REGISTRO:
        rlock = _LOCKS.get(chave)
        if rlock is None:
            rlock = threading.RLock()
            _LOCKS[chave] = rlock
        return rlock


class ActionLock:
    """Lock exclusivo global de ação baseado em arquivo.

    O lock é adquirido de forma bloqueante por até ``esperar`` segundos; quando
    o tempo se esgota, levanta :class:`OperacaoEmAndamento`. Usar como *context
    manager* garante a liberação. A aquisição é reentrante na mesma thread e
    exclusiva entre threads e processos.
    """

    def __init__(
        self: ActionLock,
        caminho: Path | None = None,
        intervalo: float = _INTERVALO_PADRAO,
    ) -> None:
        """Guarda o caminho do arquivo de lock e o intervalo entre tentativas."""
        self._caminho = Path(caminho) if caminho is not None else caminho_lock_global()
        self._intervalo = intervalo
        self._chave: str | None = None
        self._rlock: threading.RLock | None = None

    @property
    def caminho(self: ActionLock) -> Path:
        """Caminho do arquivo de lock."""
        return self._caminho

    @property
    def retido(self: ActionLock) -> bool:
        """Indica se este objeto detém o lock no momento."""
        return self._chave is not None

    def adquirir(self: ActionLock, esperar: float = 0.0) -> ActionLock:
        """Adquire o lock, esperando até ``esperar`` segundos antes de desistir."""
        self._caminho.parent.mkdir(parents=True, exist_ok=True)
        chave = str(self._caminho.resolve())
        prazo = time.monotonic() + max(esperar, 0.0)
        rlock = _rlock_de(chave)
        if not rlock.acquire(timeout=max(esperar, 0.0)):
            raise OperacaoEmAndamento(self._caminho)
        try:
            if _CONTAGEM.get(chave, 0) == 0:
                self._bloquear_os(chave, prazo)
            _CONTAGEM[chave] = _CONTAGEM.get(chave, 0) + 1
        except BaseException:
            rlock.release()
            raise
        self._rlock = rlock
        self._chave = chave
        return self

    def _bloquear_os(self: ActionLock, chave: str, prazo: float) -> None:
        """Toma o bloqueio do sistema operacional, registrando o descritor."""
        handle = os.open(self._caminho, os.O_RDWR | os.O_CREAT, 0o644)
        while True:
            if self._travar(handle):
                _HANDLES[chave] = handle
                return
            if time.monotonic() >= prazo:
                os.close(handle)
                raise OperacaoEmAndamento(self._caminho)
            time.sleep(self._intervalo)

    def liberar(self: ActionLock) -> None:
        """Libera uma aquisição; o lock do SO cai quando a profundidade zera."""
        chave = self._chave
        if chave is None:
            return
        self._chave = None
        contagem = _CONTAGEM.get(chave, 0) - 1
        if contagem > 0:
            _CONTAGEM[chave] = contagem
        else:
            _CONTAGEM.pop(chave, None)
            handle = _HANDLES.pop(chave, None)
            if handle is not None:
                try:
                    self._destravar(handle)
                finally:
                    os.close(handle)
        if self._rlock is not None:
            self._rlock.release()
            self._rlock = None

    @staticmethod
    def _travar(handle: int) -> bool:
        """Tenta travar o descritor de forma não bloqueante."""
        try:
            if os.name == "nt":  # pragma: no cover - depende do SO
                os.lseek(handle, 0, os.SEEK_SET)
                msvcrt.locking(handle, msvcrt.LK_NBLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except OSError:
            return False

    @staticmethod
    def _destravar(handle: int) -> None:
        """Destrava o descritor, tolerando sistemas que já o liberaram."""
        try:
            if os.name == "nt":  # pragma: no cover - depende do SO
                os.lseek(handle, 0, os.SEEK_SET)
                msvcrt.locking(handle, msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)
        except OSError:
            pass

    def __enter__(self: ActionLock) -> ActionLock:  # noqa: PYI034
        """Adquire o lock, esperando zero segundos."""
        return self.adquirir()

    def __exit__(
        self: ActionLock,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Libera o lock ao sair do bloco."""
        self.liberar()
