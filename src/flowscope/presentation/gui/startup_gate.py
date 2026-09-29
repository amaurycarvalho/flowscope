"""Gate de inicialização da interface gráfica.

Bloqueia toda a entrada da janela — botões, abas, painéis e atalhos — desde o
fim da construção dos widgets até a restauração inicial de abas/painéis
concluir. O bloqueio combina um escudo transparente sobre o toplevel (que
intercepta cliques em qualquer widget, inclusive abas e painéis sem
``all_buttons()``), o estado ocupado da autoridade única de estado e um flag
consultado pelos atalhos globais.
"""

import tkinter as tk
from typing import Protocol

#: Tempo máximo (ms) para a restauração inicial antes do release de segurança.
TIMEOUT_GATE_MS = 3000


class EscudoView(Protocol):
    """Contrato mínimo da view requerido pelo coordenador do gate."""

    def colocar_escudo(self: "EscudoView") -> None:
        """Coloca o escudo de bloqueio sobre a janela."""
        ...

    def remover_escudo(self: "EscudoView") -> None:
        """Remove o escudo de bloqueio da janela."""
        ...


class StartupGate:
    """Coordena escudo, flag de inicialização e estado ocupado.

    ``iniciar`` entra no estado ocupado (desabilitando controles e aplicando o
    cursor de espera) e coloca o escudo; ``finalizar`` remove o escudo antes de
    sair do estado ocupado, para que a restauração do cursor não capture o
    próprio overlay. Ambas as operações são idempotentes.
    """

    def __init__(
        self: "StartupGate", view: EscudoView, presenter: object
    ) -> None:
        """Inicializa o coordenador com a view do escudo e o apresentador."""
        self._view = view
        self._presenter = presenter
        self._inicializando = False

    @property
    def inicializando(self: "StartupGate") -> bool:
        """Indica se o gate está bloqueando a entrada."""
        return self._inicializando

    def iniciar(self: "StartupGate") -> None:
        """Ativa o bloqueio de inicialização, se ainda não estiver ativo."""
        if self._inicializando:
            return
        self._inicializando = True
        self._presenter.enter()
        self._view.colocar_escudo()

    def finalizar(self: "StartupGate") -> None:
        """Desativa o bloqueio de inicialização, se estiver ativo."""
        if not self._inicializando:
            return
        self._inicializando = False
        self._view.remover_escudo()
        self._presenter.exit()


class StartupGateMixin:
    """Expõe o gate de inicialização e o escudo para a janela principal."""

    @property
    def _inicializando(self: "StartupGateMixin") -> bool:
        """Indica se o gate de inicialização está ativo."""
        gate = getattr(self, "_startup_gate", None)
        return bool(gate is not None and gate.inicializando)

    def _gate(self: "StartupGateMixin") -> StartupGate:
        """Retorna (criando sob demanda) o coordenador do gate."""
        gate = getattr(self, "_startup_gate", None)
        if gate is None:
            gate = StartupGate(view=self, presenter=self._presenter)
            self._startup_gate = gate
        return gate

    def iniciar_gate(self: "StartupGateMixin") -> None:
        """Bloqueia a entrada até a restauração inicial concluir.

        Agenda um release de segurança para o caso de a restauração inicial não
        executar (por exemplo, com o ``after`` cancelado), evitando que a
        interface fique presa.
        """
        gate = self._gate()
        if gate.inicializando:
            return
        gate.iniciar()
        self.after(TIMEOUT_GATE_MS, gate.finalizar)

    def finalizar_gate(self: "StartupGateMixin") -> None:
        """Libera a entrada bloqueada pela inicialização."""
        gate = getattr(self, "_startup_gate", None)
        if gate is not None:
            gate.finalizar()

    def colocar_escudo(self: "StartupGateMixin") -> None:
        """Coloca um frame de bloqueio cobrindo toda a janela."""
        if getattr(self, "_escudo", None) is not None:
            return
        escudo = tk.Frame(self, cursor="watch")
        escudo.place(x=0, y=0, relwidth=1, relheight=1)
        escudo.lift()
        self._escudo = escudo

    def remover_escudo(self: "StartupGateMixin") -> None:
        """Remove o frame de bloqueio da janela."""
        escudo = getattr(self, "_escudo", None)
        if escudo is None:
            return
        escudo.destroy()
        self._escudo = None
