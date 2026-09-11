"""Formatadores e rótulos de exibição da tabela fundamentalista.

Reúne a conversão de valores de domínio (``Decimal``, ``date``, enums) em
textos amigáveis exibidos nas células, além dos mapas de rótulos usados nas
colunas de identidade, classe e tendência.
"""

from datetime import date
from decimal import Decimal
from enum import Enum

from flowscope.domain.fii import (
    ClasseCotistas,
    ClassePatrimonio,
    SubTipoAcao,
    SubTipoFii,
    TipoAtivo,
)

NA = "N/A"

#: Rótulos descritivos compartilhados pelas tendências do FFO e do dividendo.
_ROTULOS_TENDENCIA = {
    "FORTE_ALTA": "Forte Alta",
    "ALTA": "Leve Alta",
    "ESTAVEL": "Estável",
    "QUEDA": "Leve Queda",
    "FORTE_QUEDA": "Forte Queda",
}

_CLASSE_COTISTAS = {
    ClasseCotistas.MICRO: "Micro",
    ClasseCotistas.MUITO_PEQUENO: "Muito pequeno",
    ClasseCotistas.PEQUENO: "Pequeno",
    ClasseCotistas.MEDIO: "Médio",
    ClasseCotistas.GRANDE: "Grande",
    ClasseCotistas.MUITO_GRANDE: "Muito grande",
    ClasseCotistas.GIGANTE: "Gigante",
}

_CLASSE_PATRIMONIO = {
    ClassePatrimonio.MICRO: "Micro",
    ClassePatrimonio.PEQUENO: "Pequeno",
    ClassePatrimonio.MEDIO: "Médio",
    ClassePatrimonio.GRANDE: "Grande",
    ClassePatrimonio.MUITO_GRANDE: "Muito grande",
    ClassePatrimonio.GIGANTE: "Gigante",
}

_TIPOS = {
    TipoAtivo.ACAO: "Ação",
    TipoAtivo.FII: "FII",
    TipoAtivo.ETF: "ETF",
    TipoAtivo.BDR: "BDR",
    TipoAtivo.DESCONHECIDO: "Desconhecido",
}

_SUB_TIPO_ACAO = {
    SubTipoAcao.ORDINARIA: "Ordinária",
    SubTipoAcao.PREFERENCIAL: "Preferencial",
    SubTipoAcao.ETF: "ETF",
}

_SUB_TIPO_FII = {
    SubTipoFii.TIJOLO: "Tijolo",
    SubTipoFii.PAPEL: "Papel",
    SubTipoFii.HIBRIDO: "Híbrido",
    SubTipoFii.FIAGRO: "Fiagro",
    SubTipoFii.FIINFRA: "Fiinfra",
    SubTipoFii.DESCONHECIDO: "Desconhecido",
}


def rotulo_tipo(tipo: TipoAtivo | None) -> str:
    """Retorna o rótulo amigável de um tipo de ativo."""
    if tipo is None:
        return NA
    return _TIPOS.get(tipo, tipo.name)


def rotulo_sub_tipo(sub_tipo: Enum | None) -> str:
    """Retorna o rótulo amigável de um sub-tipo de ativo."""
    if sub_tipo is None:
        return NA
    if isinstance(sub_tipo, SubTipoFii):
        return _SUB_TIPO_FII.get(sub_tipo, sub_tipo.name)
    if isinstance(sub_tipo, SubTipoAcao):
        return _SUB_TIPO_ACAO.get(sub_tipo, sub_tipo.name)
    return sub_tipo.name


def formatar_data(data: date | None) -> str:
    """Formata uma data no padrão DD/MM/AAAA, ou ``N/A``."""
    if data is None:
        return NA
    return data.strftime("%d/%m/%Y")


def _com_virgula(valor: Decimal, casas: int) -> str:
    """Formata um decimal com vírgula e a quantidade de casas informada."""
    quantizado = valor.quantize(Decimal(1).scaleb(-casas))
    return f"{quantizado:.{casas}f}".replace(".", ",")


def formatar_valor(valor: Decimal | None) -> str:
    """Formata um valor monetário curto com vírgula e 2 casas, ou ``N/A``."""
    if valor is None:
        return NA
    return _com_virgula(valor, 2)


def formatar_percentual(valor: Decimal | None, casas: int = 2) -> str:
    """Formata um percentual decimal como ``8,16%``, ou ``N/A``."""
    if valor is None:
        return NA
    return f"{_com_virgula(valor * Decimal(100), casas)}%"


def formatar_preco_tipico(valor: Decimal | None) -> str:
    """Formata o Preço Típico com separador de milhar e 2 casas, ou ``N/A``."""
    if valor is None:
        return NA
    return _agrupar(valor, 2)


def formatar_ratio(valor: Decimal | None, casas: int = 2) -> str:
    """Formata uma razão como ``12,25x``, ou ``N/A``."""
    if valor is None:
        return NA
    return f"{_com_virgula(valor, casas)}x"


def formatar_inteiro(valor: int | None) -> str:
    """Formata um inteiro com separador de milhar brasileiro, ou ``N/A``."""
    if valor is None:
        return NA
    return f"{valor:,}".replace(",", ".")


def formatar_cnpj(valor: str | None) -> str:
    """Formata um CNPJ como ``99.999.999/9999-99``, ou ``N/A``."""
    if not valor:
        return NA
    digitos = "".join(caractere for caractere in valor if caractere.isdigit())
    if len(digitos) != 14:
        return valor.strip()
    return (
        f"{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/"
        f"{digitos[8:12]}-{digitos[12:]}"
    )


def formatar_patrimonio(valor: Decimal | None) -> str:
    """Formata o patrimônio líquido de forma legível (mi/bi), ou ``N/A``."""
    if valor is None:
        return NA
    if valor >= Decimal(1000000000):
        return f"R$ {_com_virgula(valor / Decimal(1000000000), 2)} bi"
    if valor >= Decimal(1000000):
        return f"R$ {_com_virgula(valor / Decimal(1000000), 2)} mi"
    return f"R$ {_agrupar(valor, 2)}"


def _agrupar(valor: Decimal, casas: int) -> str:
    """Formata um decimal com separador de milhar e vírgula decimal."""
    quantizado = valor.quantize(Decimal(1).scaleb(-casas))
    texto = f"{quantizado:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def rotulo_classe_cotistas(classe: ClasseCotistas | None) -> str:
    """Retorna o rótulo amigável da classe por número de cotistas."""
    if classe is None:
        return NA
    return _CLASSE_COTISTAS.get(classe, classe.name)


def rotulo_classe_patrimonio(classe: ClassePatrimonio | None) -> str:
    """Retorna o rótulo amigável da classe por tamanho patrimonial."""
    if classe is None:
        return NA
    return _CLASSE_PATRIMONIO.get(classe, classe.name)


def rotulo_tendencia(tendencia: Enum | None) -> str:
    """Retorna o rótulo descritivo de uma tendência (FFO ou dividendo)."""
    if tendencia is None:
        return NA
    return _ROTULOS_TENDENCIA.get(tendencia.value, tendencia.value)
