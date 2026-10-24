"""Read-models das inferências de direitos e obrigações a partir de resumos.

As inferências são produzidas pela LLM a partir de resumos já persistidos e
mantidas em cache separado do oficial. O modelo preserva a proveniência de cada
item e nunca se confunde com um título de fonte oficial.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date

from flowscope.domain.renda_fixa.models import (
    CarteiraTitulos,
    PapelTitulo,
    TipoTitulo,
)

#: Versão do parser/prompt das inferências de direitos e obrigações.
PARSER_VERSION_INFERENCIA = "direitos-obrigacoes-inferencia-v1"

#: Fonte registrada em cada item inferido.
FONTE_INFERENCIA = "LLM"


@dataclass(frozen=True)
class InferenciaTitulo:
    """Item de renda fixa inferido de um resumo de documento.

    ``chave_documento`` e ``hash_resumo`` identificam a entrada de origem e
    permitem reutilizar ou substituir a inferência de forma idempotente.
    """

    tipo: TipoTitulo
    papel: PapelTitulo
    descricao: str
    documento: str = ""
    chave_documento: str = ""
    hash_resumo: str = ""
    trecho: str = ""
    confianca: float = 0.0
    data_referencia: date | None = None
    fonte: str = FONTE_INFERENCIA
    identificacao: str = ""

    @property
    def inferido(self: InferenciaTitulo) -> bool:
        """Indica que o item foi inferido pela IA, não publicado oficialmente."""
        return True

    @property
    def rotulo(self: InferenciaTitulo) -> str:
        """Retorna o rótulo humano do item inferido."""
        return self.descricao or self.tipo.rotulo

    @property
    def nome_exibicao(self: InferenciaTitulo) -> str:
        """Retorna o nome de exibição do item na árvore."""
        return self.rotulo

    @property
    def id(self: InferenciaTitulo) -> str:
        """Deriva um identificador curto e estável para o caminho da árvore."""
        bruto = (
            f"{self.chave_documento}|{self.tipo.value}|{self.papel.value}|"
            f"{self.descricao}|{self.trecho}"
        )
        return "i" + hashlib.sha1(bruto.encode("utf-8")).hexdigest()[:10]


@dataclass(frozen=True)
class CarteiraInferencias:
    """Conjunto persistido de inferências de um ticker."""

    ticker: str
    parser_version: str = PARSER_VERSION_INFERENCIA
    adquirido_em: str = ""
    itens: tuple[InferenciaTitulo, ...] = field(default_factory=tuple)

    @property
    def vazio(self: CarteiraInferencias) -> bool:
        """Indica se não há itens inferidos no cache."""
        return not self.itens


def _tem_itens(carteira: CarteiraTitulos, papel: PapelTitulo) -> bool:
    """Indica se o papel possui títulos ou agregados oficiais."""
    titulos = carteira.obrigacoes if papel is PapelTitulo.OBRIGACAO else carteira.direitos
    agregados = [item for item in carteira.agregados if item.papel is papel]
    return bool(titulos or agregados)


def cobertura_oficial_completa(carteira: CarteiraTitulos | None) -> bool:
    """Indica se o cache oficial cobre obrigações e direitos do ticker.

    A cobertura é considerada completa quando os dois papéis possuem ao menos
    um título ou agregado e não há ausência explícita de fonte. Cache ausente,
    vazio ou com ``sem-fonte`` é tratado como cobertura parcial.
    """
    if carteira is None or carteira.ausencias:
        return False
    if not carteira.obrigacoes and not carteira.direitos and not carteira.agregados:
        return False
    return _tem_itens(carteira, PapelTitulo.OBRIGACAO) and _tem_itens(
        carteira, PapelTitulo.DIREITO
    )
