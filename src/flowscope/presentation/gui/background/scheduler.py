"""Decisão de agendamento entre jobs do mesmo grupo.

O :class:`Scheduler` mantém o job ativo de cada grupo e a fila FIFO das
requisições serializadas, traduzindo a política configurada em uma decisão de
submissão. É puro em relação à interface: não conhece threads nem widgets.
"""

from collections import defaultdict, deque
from enum import Enum

from flowscope.presentation.gui.background.job import JobHandle, Politica


class Decisao(Enum):
    """Decisão do agendador para uma requisição submetida."""

    INICIAR = "iniciar"
    SUBSTITUIR = "substituir"
    ENFILEIRAR = "enfileirar"
    DESCARTAR = "descartar"


class Scheduler:
    """Registro de jobs ativos por grupo e decisão de política."""

    def __init__(self: "Scheduler") -> None:
        """Inicializa o agendador sem grupos ativos nem filas."""
        self._ativos: dict[str, JobHandle] = {}
        self._filas: dict[str, deque[JobHandle]] = defaultdict(deque)

    def decidir(self: "Scheduler", handle: JobHandle) -> Decisao:
        """Decide como tratar uma nova requisição conforme a política."""
        ativo = self._ativos.get(handle.grupo)
        if handle.politica is Politica.PARALLEL:
            return Decisao.INICIAR
        if handle.politica is Politica.LATEST_WINS:
            if ativo is None:
                return Decisao.INICIAR
            if handle.chave is not None and ativo.chave == handle.chave:
                return Decisao.DESCARTAR
            return Decisao.SUBSTITUIR
        if handle.politica is Politica.SERIALIZE:
            if handle.chave is not None and self._tem_chave(handle):
                return Decisao.DESCARTAR
            return Decisao.INICIAR if ativo is None else Decisao.ENFILEIRAR
        return Decisao.INICIAR

    def ativo(self: "Scheduler", grupo: str) -> JobHandle | None:
        """Retorna o job ativo do grupo, se houver."""
        return self._ativos.get(grupo)

    def marcar_ativo(self: "Scheduler", handle: JobHandle) -> None:
        """Registra o job como ativo do seu grupo."""
        self._ativos[handle.grupo] = handle

    def remover(self: "Scheduler", handle: JobHandle) -> None:
        """Remove o job do registro de ativos, se ainda for o ativo do grupo."""
        if self._ativos.get(handle.grupo) is handle:
            del self._ativos[handle.grupo]

    def enfileirar(self: "Scheduler", handle: JobHandle) -> None:
        """Adiciona a requisição ao fim da fila FIFO do grupo."""
        self._filas[handle.grupo].append(handle)

    def retirar_proximo(self: "Scheduler", grupo: str) -> JobHandle | None:
        """Retira e retorna a próxima requisição da fila do grupo."""
        fila = self._filas.get(grupo)
        if fila:
            return fila.popleft()
        return None

    def retirar_pendentes(self: "Scheduler", grupo: str) -> list[JobHandle]:
        """Remove e retorna as requisições enfileiradas do grupo."""
        fila = self._filas.pop(grupo, None)
        return list(fila) if fila else []

    def limpar_pendentes(self: "Scheduler") -> list[JobHandle]:
        """Remove e retorna todas as requisições enfileiradas."""
        pendentes = [item for fila in self._filas.values() for item in fila]
        self._filas.clear()
        return pendentes

    def _tem_chave(self: "Scheduler", handle: JobHandle) -> bool:
        """Indica se a chave já está ativa ou enfileirada no grupo."""
        ativo = self._ativos.get(handle.grupo)
        if ativo is not None and ativo.chave == handle.chave:
            return True
        return any(item.chave == handle.chave for item in self._filas[handle.grupo])
