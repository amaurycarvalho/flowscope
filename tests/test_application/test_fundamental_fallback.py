from datetime import date
from decimal import Decimal

from flowscope.application.fundamental_fallback import CompositeFundamentalProvider
from flowscope.application.fundamental_ports import (
    CAMPO_DIVIDEND_YIELD,
    CAMPO_NOME,
    CAMPO_P_VP,
    CAMPOS_FUNDAMENTAIS,
    CampoFundamental,
    FundamentalDataProvider,
)

REFERENCIA = date(2026, 9, 4)


class _Fonte:
    def __init__(self, nome, campos=None, falhar=False):
        self.nome = nome
        self._campos = campos or {}
        self._falhar = falhar
        self.chamadas = 0

    def obter(self, ticker, reference_date):
        self.chamadas += 1
        if self._falhar:
            raise RuntimeError(f"fonte {self.nome} indisponível")
        return self._campos


def _todos_os_campos(fonte: str) -> dict[str, CampoFundamental]:
    return {chave: CampoFundamental(Decimal(1), fonte) for chave in CAMPOS_FUNDAMENTAIS}


class TestProtocolo:
    def test_protocolo_runtime_checkable(self):
        assert isinstance(_Fonte("x"), FundamentalDataProvider)


class TestCompositeFundamentalProvider:
    def test_campo_do_primario_nao_consulta_fallback(self):
        primario = _Fonte("FUNDAMENTUS", _todos_os_campos("FUNDAMENTUS"))
        fallback = _Fonte("CVM", {CAMPO_P_VP: CampoFundamental(Decimal("0.99"), "CVM")})
        composto = CompositeFundamentalProvider([primario, fallback])
        campos = composto.obter("HGBS11", REFERENCIA)
        assert campos[CAMPO_P_VP].fonte == "FUNDAMENTUS"
        assert fallback.chamadas == 0

    def test_campo_ausente_e_buscado_no_fallback_com_origem(self):
        primario = _Fonte(
            "FUNDAMENTUS",
            {
                CAMPO_NOME: CampoFundamental("CSHG Renda Urbana", "FUNDAMENTUS"),
                CAMPO_DIVIDEND_YIELD: CampoFundamental(Decimal("0.079"), "FUNDAMENTUS"),
            },
        )
        fallback = _Fonte("CVM", {CAMPO_P_VP: CampoFundamental(Decimal("0.92"), "CVM")})
        composto = CompositeFundamentalProvider([primario, fallback])
        campos = composto.obter("HGBS11", REFERENCIA)
        assert campos[CAMPO_NOME].fonte == "FUNDAMENTUS"
        assert campos[CAMPO_P_VP].valor == Decimal("0.92")
        assert campos[CAMPO_P_VP].fonte == "CVM"

    def test_falha_do_primario_cai_para_fallback(self):
        primario = _Fonte("FUNDAMENTUS", falhar=True)
        fallback = _Fonte("B3", {CAMPO_NOME: CampoFundamental("Fundo X", "B3")})
        composto = CompositeFundamentalProvider([primario, fallback])
        campos = composto.obter("HGBS11", REFERENCIA)
        assert campos[CAMPO_NOME].fonte == "B3"

    def test_ordem_de_prioridade_configuravel(self):
        fonte_a = _Fonte("A", {CAMPO_P_VP: CampoFundamental(Decimal(1), "A")})
        fonte_b = _Fonte("B", {CAMPO_P_VP: CampoFundamental(Decimal(2), "B")})
        assert CompositeFundamentalProvider([fonte_a, fonte_b]).obter(
            "X", REFERENCIA
        )[CAMPO_P_VP].fonte == "A"
        assert CompositeFundamentalProvider([fonte_b, fonte_a]).obter(
            "X", REFERENCIA
        )[CAMPO_P_VP].fonte == "B"

    def test_valor_none_nao_sobrescreve(self):
        primario = _Fonte("A", {CAMPO_P_VP: CampoFundamental(None, "A")})
        fallback = _Fonte("B", {CAMPO_P_VP: CampoFundamental(Decimal(2), "B")})
        campos = CompositeFundamentalProvider([primario, fallback]).obter(
            "X", REFERENCIA
        )
        assert campos[CAMPO_P_VP].fonte == "B"
