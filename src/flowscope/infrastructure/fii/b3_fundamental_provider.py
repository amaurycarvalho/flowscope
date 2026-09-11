"""Adaptador da camada B3 para a porta ``FundamentalDataProvider``.

Atua como fallback de campos básicos (nome, identidade fiscal, patrimônio por
cota e classificação autorregulação) quando a fonte primária não os fornece,
reutilizando a identidade e o Informe Mensal da B3.
"""

from datetime import date
from decimal import Decimal

from flowscope.application.fundamental_ports import (
    CAMPO_ADMINISTRADOR,
    CAMPO_CLASSIFICACAO_FII,
    CAMPO_CNPJ,
    CAMPO_CNPJ_ADMINISTRADOR,
    CAMPO_DISCRIMINADOR,
    CAMPO_GESTAO,
    CAMPO_NOME,
    CAMPO_SEGMENTO,
    CAMPO_VP_COTA,
    CampoFundamental,
)
from flowscope.domain.b3 import B3InformeMensal
from flowscope.domain.fii.analysis import PatrimonioFii
from flowscope.domain.fii.fundamentus import DISCRIMINADOR_FII
from flowscope.infrastructure.fii.b3_fundamental_repository import (
    B3FundamentalRepository,
)

#: Fonte registrada nos campos produzidos pelo adaptador.
FONTE_B3 = "B3"


class B3FundamentalDataProvider:
    """Fornece campos fundamentalistas básicos a partir da camada B3."""

    def __init__(
        self: "B3FundamentalDataProvider",
        repository: B3FundamentalRepository | None = None,
    ) -> None:
        """Inicializa o adaptador com o repositório fundamentalista B3."""
        self._repository = repository or B3FundamentalRepository()

    def obter(
        self: "B3FundamentalDataProvider", ticker: str, reference_date: date
    ) -> dict[str, CampoFundamental]:
        """Retorna identidade, classificação e VP/Cota quando disponíveis."""
        campos: dict[str, CampoFundamental] = {}
        nome = self._repository.obter_nome(ticker)
        if nome:
            campos[CAMPO_NOME] = CampoFundamental(nome, FONTE_B3)
        informe = self._repository.obter_informe(ticker, reference_date)
        if informe is not None:
            _adicionar_classificacao(campos, informe)
        patrimonio = self._obter_patrimonio(ticker, reference_date)
        _adicionar(campos, CAMPO_VP_COTA, _vp_cota(patrimonio))
        return campos

    def _obter_patrimonio(
        self: "B3FundamentalDataProvider", ticker: str, reference_date: date
    ) -> PatrimonioFii | None:
        """Obtém o patrimônio do repositório, tolerando repositórios mínimos."""
        obter = getattr(self._repository, "obter_patrimonio", None)
        if not callable(obter):
            return None
        return obter(ticker, reference_date)


def _adicionar_classificacao(
    campos: dict[str, CampoFundamental], informe: B3InformeMensal
) -> None:
    """Adiciona identidade fiscal e classificação autorregulação do informe."""
    _adicionar(campos, CAMPO_CNPJ, informe.cnpj)
    _adicionar(campos, CAMPO_ADMINISTRADOR, informe.nome_administrador)
    _adicionar(campos, CAMPO_CNPJ_ADMINISTRADOR, informe.cnpj_administrador)
    campos[CAMPO_DISCRIMINADOR] = CampoFundamental(DISCRIMINADOR_FII, FONTE_B3)
    if informe.classificacao:
        campos[CAMPO_CLASSIFICACAO_FII] = CampoFundamental(
            informe.classificacao, FONTE_B3
        )
    _adicionar(campos, CAMPO_SEGMENTO, informe.segmento_atuacao)
    _adicionar(campos, CAMPO_GESTAO, informe.gestao)


def _vp_cota(patrimonio: PatrimonioFii | None) -> Decimal | None:
    """Retorna o VP/Cota reportado ou derivado de ``NAV / cotas``."""
    if patrimonio is None:
        return None
    if patrimonio.vp_cota is not None:
        return patrimonio.vp_cota
    if patrimonio.shares_outstanding and patrimonio.shares_outstanding > 0:
        return patrimonio.net_asset_value / patrimonio.shares_outstanding
    return None


def _adicionar(
    campos: dict[str, CampoFundamental], chave: str, valor: object
) -> None:
    """Adiciona um campo com a fonte B3 quando o valor existe."""
    if valor is not None:
        campos[chave] = CampoFundamental(valor, FONTE_B3)
