"""Modelos normalizados da extração de dividendos de BDRs.

Os avisos aos acionistas são listados no Plantão de Notícias da B3, o documento
é resolvido na página de detalhe e baixado da CVM; o texto do PDF é
normalizado em ``DividendoBdr`` e consolidado em ``DadosBdr`` para preencher a
tabela de Fundamentos.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from flowscope.domain.fii.dividends import DividendoConsolidado

#: Fonte registrada nos dividendos extraídos de avisos de BDR.
FONTE_BDR = "BDR"


@dataclass(frozen=True)
class AvisoBdr:
    """Aviso aos acionistas de um BDR listado no Plantão de Notícias da B3."""

    ticker: str
    id_noticia: str
    titulo: str
    data_publicacao: str = ""


@dataclass(frozen=True)
class DividendoBdr:
    """Dividendo extraído do texto de um aviso aos acionistas de BDR."""

    valor: Decimal | None
    data_com: date | None
    data_pagamento: date | None = None
    tipo: str | None = None
    isin: str | None = None
    depositario: str | None = None
    empresa: str | None = None
    nivel_programa: str | None = None
    observacao: str | None = None
    fonte: str = FONTE_BDR

    def para_consolidado(self: "DividendoBdr") -> DividendoConsolidado | None:
        """Retorna o dividendo consolidado, ou ``None`` sem valor/data-com."""
        if self.valor is None or self.data_com is None:
            return None
        return DividendoConsolidado(
            data_base=self.data_com, valor=self.valor, fonte=self.fonte
        )


@dataclass(frozen=True)
class DadosBdr:
    """Dados de dividendos, programa e identidade fiscal dos avisos de um BDR."""

    dividendos: tuple[DividendoConsolidado, ...] = ()
    nome_depositario: str | None = None
    nome_empresa: str | None = None
    isin: str | None = None
    nivel_programa: str | None = None
    observacao: str | None = None
    avisos: tuple[str, ...] = field(default_factory=tuple)
