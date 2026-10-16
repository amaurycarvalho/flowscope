"""Desfecho da aquisição de documentos de um ticker."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ResultadoAquisicao:
    """Contagem de documentos novos, reutilizados do cache e falhos."""

    novos: int = 0
    reutilizados: int = 0
    falhas: int = 0

    @property
    def adquiridos(self: "ResultadoAquisicao") -> int:
        """Total de itens persistidos (novos ou reutilizados do cache)."""
        return self.novos + self.reutilizados

    def __add__(
        self: "ResultadoAquisicao", outro: "ResultadoAquisicao"
    ) -> "ResultadoAquisicao":
        """Combina dois desfechos somando cada contagem."""
        return ResultadoAquisicao(
            novos=self.novos + outro.novos,
            reutilizados=self.reutilizados + outro.reutilizados,
            falhas=self.falhas + outro.falhas,
        )
