"""Read-models dos títulos de renda fixa associados a um ticker.

O modelo é independente de infraestrutura: descreve obrigações emitidas e
direitos mantidos, com proveniência, agregados e ausência explícita de fonte.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum

#: Versão do parser/cache de títulos de renda fixa.
PARSER_VERSION = "titulos-renda-fixa-v3"


class TipoTitulo(str, Enum):
    """Tipos de título de renda fixa suportados pela árvore."""

    DEBENTURE = "debenture"
    DEBENTURE_CONVERSIVEL = "debenture_conversivel"
    NOTA_COMERCIAL = "nota_comercial"
    CRI = "cri"
    CRA = "cra"
    LCI = "lci"
    LCA = "lca"
    CDB = "cdb"
    LETRA_FINANCEIRA = "letra_financeira"
    OUTRO = "outro"

    @property
    def rotulo(self: TipoTitulo) -> str:
        """Retorna o rótulo humano do tipo de título."""
        return _ROTULOS_TIPO[self]

    @property
    def segmento(self: TipoTitulo) -> str:
        """Retorna o segmento estável do tipo no caminho canônico."""
        return _SEGMENTOS_TIPO[self]


class PapelTitulo(str, Enum):
    """Papel do título na carteira do ticker."""

    OBRIGACAO = "obrigacao"
    DIREITO = "direito"

    @property
    def segmento(self: PapelTitulo) -> str:
        """Retorna o segmento do papel no caminho canônico."""
        return "obrigacoes" if self is PapelTitulo.OBRIGACAO else "direitos"

    @property
    def rotulo(self: PapelTitulo) -> str:
        """Retorna o rótulo humano do papel."""
        return "Obrigações" if self is PapelTitulo.OBRIGACAO else "Direitos"


_ROTULOS_TIPO = {
    TipoTitulo.DEBENTURE: "Debêntures",
    TipoTitulo.DEBENTURE_CONVERSIVEL: "Debêntures Conversíveis",
    TipoTitulo.NOTA_COMERCIAL: "Nota Comercial",
    TipoTitulo.CRI: "CRI",
    TipoTitulo.CRA: "CRA",
    TipoTitulo.LCI: "LCI",
    TipoTitulo.LCA: "LCA",
    TipoTitulo.CDB: "CDB",
    TipoTitulo.LETRA_FINANCEIRA: "Letras Financeiras",
    TipoTitulo.OUTRO: "Outros",
}

_SEGMENTOS_TIPO = {
    TipoTitulo.DEBENTURE: "debentures",
    TipoTitulo.DEBENTURE_CONVERSIVEL: "debentures-conversiveis",
    TipoTitulo.NOTA_COMERCIAL: "nota-comercial",
    TipoTitulo.CRI: "cri",
    TipoTitulo.CRA: "cra",
    TipoTitulo.LCI: "lci",
    TipoTitulo.LCA: "lca",
    TipoTitulo.CDB: "cdb",
    TipoTitulo.LETRA_FINANCEIRA: "letras-financeiras",
    TipoTitulo.OUTRO: "outros",
}

#: Ordem de exibição dos tipos na árvore.
ORDEM_TIPOS: tuple[TipoTitulo, ...] = (
    TipoTitulo.DEBENTURE,
    TipoTitulo.DEBENTURE_CONVERSIVEL,
    TipoTitulo.NOTA_COMERCIAL,
    TipoTitulo.CRI,
    TipoTitulo.CRA,
    TipoTitulo.LCI,
    TipoTitulo.LCA,
    TipoTitulo.CDB,
    TipoTitulo.LETRA_FINANCEIRA,
    TipoTitulo.OUTRO,
)

#: Tipos sem fonte pública por emissor no lado das obrigações.
TIPOS_SEM_FONTE_OBRIGACAO: tuple[TipoTitulo, ...] = (
    TipoTitulo.CDB,
    TipoTitulo.LCI,
    TipoTitulo.LCA,
)


@dataclass(frozen=True)
class DocumentoRelacionado:
    """Link para um documento relacionado ao título, sem baixar conteúdo."""

    descricao: str
    url: str
    fonte: str = ""
    data: str = ""


@dataclass(frozen=True)
class TituloRendaFixa:
    """Título individual de renda fixa com os dados normalizados da fonte."""

    tipo: TipoTitulo
    papel: PapelTitulo
    id: str = ""
    chave_fonte: str = ""
    rotulo: str = ""
    emissor_legal: str | None = None
    cnpj_emissor: str | None = None
    devedor: str | None = None
    cnpj_devedor: str | None = None
    identificacao: str | None = None
    codigos: tuple[str, ...] = field(default_factory=tuple)
    emissao: str | None = None
    serie: str | None = None
    data_emissao: date | None = None
    data_vencimento: date | None = None
    indexador: str | None = None
    taxa: str | None = None
    quantidade: Decimal | None = None
    valor: Decimal | None = None
    saldo_devedor: Decimal | None = None
    valor_posicao: Decimal | None = None
    garantias: str | None = None
    caracteristicas: str | None = None
    condicao_alteracao: str | None = None
    situacao: str | None = None
    rating: str | None = None
    contingencias: str | None = None
    impacto: str | None = None
    desempenho: str | None = None
    lastro: str | None = None
    coobrigacao: str | None = None
    sobrecolateralizacao: str | None = None
    subordinacao: str | None = None
    ltv: Decimal | None = None
    data_ltv: date | None = None
    fonte: str = ""
    data_referencia: date | None = None
    arquivo: str = ""
    hash_fonte: str = ""
    documentos: tuple[DocumentoRelacionado, ...] = field(default_factory=tuple)

    @property
    def nome_exibicao(self: TituloRendaFixa) -> str:
        """Retorna o rótulo humano do título, derivado dos dados disponíveis."""
        if self.rotulo:
            return self.rotulo
        partes = [self.identificacao, self.serie]
        texto = " — ".join(parte for parte in partes if parte)
        if texto:
            return texto
        return self.emissor_legal or self.tipo.rotulo


@dataclass(frozen=True)
class TituloAgregado:
    """Total publicado por ticker para um tipo, sem granularidade por título."""

    tipo: TipoTitulo
    papel: PapelTitulo
    valor: Decimal | None = None
    fonte: str = ""
    data_referencia: date | None = None
    id: str = "agregado"

    @property
    def rotulo(self: TituloAgregado) -> str:
        """Retorna o rótulo de exibição do agregado."""
        return f"{self.tipo.rotulo} (agregado)"


@dataclass(frozen=True)
class AusenciaFonte:
    """Ausência explícita de título ou total público por emissor."""

    tipo: TipoTitulo
    papel: PapelTitulo
    motivo: str = ""
    id: str = "sem-fonte"

    @property
    def rotulo(self: AusenciaFonte) -> str:
        """Retorna o rótulo de exibição da ausência de fonte."""
        return f"{self.tipo.rotulo} (sem fonte)"


@dataclass(frozen=True)
class FonteTitulos:
    """Metadados de proveniência de uma fonte normalizada."""

    data_referencia: date | None = None
    arquivo: str = ""
    hash: str = ""


@dataclass(frozen=True)
class CarteiraTitulos:
    """Carteira normalizada de obrigações e direitos de um ticker."""

    ticker: str
    cnpj: str = ""
    tipo_ativo: str = ""
    assinatura: str = ""
    parser_version: str = PARSER_VERSION
    adquirido_em: str = ""
    data_referencia: date | None = None
    fontes: dict[str, FonteTitulos] = field(default_factory=dict)
    obrigacoes: tuple[TituloRendaFixa, ...] = ()
    direitos: tuple[TituloRendaFixa, ...] = ()
    agregados: tuple[TituloAgregado, ...] = ()
    ausencias: tuple[AusenciaFonte, ...] = ()

    def itens(self: CarteiraTitulos, papel: PapelTitulo) -> tuple:
        """Retorna os itens de um papel, incluindo agregados e ausências."""
        titulos = self.obrigacoes if papel is PapelTitulo.OBRIGACAO else self.direitos
        agregados = tuple(item for item in self.agregados if item.papel is papel)
        ausencias = tuple(item for item in self.ausencias if item.papel is papel)
        return (*titulos, *agregados, *ausencias)

    @property
    def vazio(self: CarteiraTitulos) -> bool:
        """Indica se a carteira não possui obrigações nem direitos."""
        return not self.obrigacoes and not self.direitos
