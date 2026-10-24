"""Testes da fonte do ramo ``/direitos-obrigacoes`` da árvore de conhecimento."""

from flowscope.application.chat.arvore import ArvoreConhecimento, no_interno
from flowscope.application.chat.direitos_obrigacoes import (
    FonteDireitosObrigacoes,
)


def _arvore() -> ArvoreConhecimento:
    raiz = no_interno("/", "/")
    raiz.filho(FonteDireitosObrigacoes().construir())
    return ArvoreConhecimento(raiz)


class TestFonteDireitosObrigacoes:
    def test_lista_sub_ramos(self):
        nomes = [no.nome for no in _arvore().listar("/direitos-obrigacoes")]
        assert nomes == ["direitos", "obrigacoes"]

    def test_nos_vazios_sao_navegaveis(self):
        arvore = _arvore()
        assert "Sem dados de Direitos." in arvore.obter(
            "/direitos-obrigacoes/direitos"
        )
        assert "Sem dados de Obrigações." in arvore.obter(
            "/direitos-obrigacoes/obrigacoes"
        )


class _ConsultaFake:
    def __init__(self, carteiras):
        self._carteiras = carteiras

    def executar(self, ticker):
        return self._carteiras.get(ticker)


def _carteira_companhia():
    from datetime import date
    from decimal import Decimal

    from flowscope.domain.renda_fixa import (
        CarteiraTitulos,
        FonteTitulos,
        PapelTitulo,
        TipoTitulo,
        TituloRendaFixa,
    )

    return CarteiraTitulos(
        ticker="PETR4",
        data_referencia=date(2026, 6, 30),
        adquirido_em="2026-09-30T10:00:00+00:00",
        fontes={"fre": FonteTitulos(date(2026, 6, 30), "fre.csv", "abc")},
        obrigacoes=(
            TituloRendaFixa(
                tipo=TipoTitulo.DEBENTURE,
                papel=PapelTitulo.OBRIGACAO,
                id="d1",
                identificacao="PETR27",
                emissor_legal="PETROBRAS",
                fonte="FRE",
                data_referencia=date(2026, 6, 30),
                valor=Decimal("1000"),
                garantias="Quirografária",
            ),
        ),
    )


def _arvore_com(carteiras):
    raiz = no_interno("/", "/")
    raiz.filho(
        FonteDireitosObrigacoes(
            _ConsultaFake(carteiras), watchlist=list(carteiras)
        ).construir()
    )
    return ArvoreConhecimento(raiz)


class TestFonteComCache:
    def test_estrutura_companhia(self):
        arvore = _arvore_com({"PETR4": _carteira_companhia()})
        assert arvore.existe("/direitos-obrigacoes/data-referencia")
        assert arvore.existe(
            "/direitos-obrigacoes/obrigacoes/titulos/debentures/d1/geral"
        )
        assert arvore.existe(
            "/direitos-obrigacoes/obrigacoes/titulos/debentures/d1/ltv"
        )
        assert arvore.existe("/direitos-obrigacoes/obrigacoes/titulos/cdb/sem-fonte")
        assert "PETR27" in arvore.obter(
            "/direitos-obrigacoes/obrigacoes/titulos/debentures/d1/geral"
        )
        assert "Quirografária" in arvore.obter(
            "/direitos-obrigacoes/obrigacoes/titulos/debentures/d1/adicionais"
        )

    def test_ltv_nao_informado(self):
        arvore = _arvore_com({"PETR4": _carteira_companhia()})
        assert "não informado" in arvore.obter(
            "/direitos-obrigacoes/obrigacoes/titulos/debentures/d1/ltv"
        )

    def test_fii_com_agregado(self):
        from datetime import date
        from decimal import Decimal

        from flowscope.domain.renda_fixa import (
            CarteiraTitulos,
            PapelTitulo,
            TipoTitulo,
            TituloAgregado,
        )

        carteira = CarteiraTitulos(
            ticker="ALZR11",
            tipo_ativo="fii",
            data_referencia=date(2026, 6, 30),
            agregados=(
                TituloAgregado(
                    TipoTitulo.CDB,
                    PapelTitulo.DIREITO,
                    valor=Decimal("50"),
                    fonte="FII_INF_MENSAL",
                ),
            ),
        )
        arvore = _arvore_com({"ALZR11": carteira})
        assert arvore.existe(
            "/direitos-obrigacoes/direitos/titulos/cdb/agregado/resumo"
        )

    def test_cache_frio_preserva_ramos(self):
        arvore = _arvore_com({})
        assert arvore.existe("/direitos-obrigacoes/direitos")
        assert arvore.existe("/direitos-obrigacoes/obrigacoes")
        assert "Sem dados" in arvore.obter("/direitos-obrigacoes/direitos")


class _InferenciasFake:
    def __init__(self, itens):
        self._itens = itens

    def ler(self, ticker):
        from flowscope.domain.renda_fixa import CarteiraInferencias

        return CarteiraInferencias(ticker, itens=tuple(self._itens))


def _inferencia_cri(descricao="CRI da emissora Alfa"):
    from datetime import date

    from flowscope.domain.renda_fixa import (
        InferenciaTitulo,
        PapelTitulo,
        TipoTitulo,
    )

    return InferenciaTitulo(
        tipo=TipoTitulo.CRI,
        papel=PapelTitulo.DIREITO,
        descricao=descricao,
        documento="relatorio.pdf",
        trecho="O fundo mantém CRI da emissora Alfa.",
        confianca=0.8,
        data_referencia=date(2026, 2, 1),
    )


class TestFonteComInferencias:
    def _arvore(self, itens, carteiras=None, watchlist=("ALZR11",)):
        raiz = no_interno("/", "/")
        raiz.filho(
            FonteDireitosObrigacoes(
                _ConsultaFake(carteiras or {}),
                watchlist=list(watchlist),
                inferencias=_InferenciasFake(itens),
            ).construir()
        )
        return ArvoreConhecimento(raiz)

    def test_item_inferido_aparece_com_proveniencia(self):
        item = _inferencia_cri()
        arvore = self._arvore([item])

        caminho = (
            "/direitos-obrigacoes/direitos/titulos/cri/"
            f"{item.id}"
        )
        assert arvore.existe(caminho)
        assert "inferido pela IA" in arvore.obter(f"{caminho}/geral")
        assert "relatorio.pdf" in arvore.obter(f"{caminho}/adicionais")
        assert "O fundo mantém CRI" in arvore.obter(f"{caminho}/adicionais")

    def test_conflito_oficial_omite_a_inferencia(self):
        from flowscope.domain.renda_fixa import (
            InferenciaTitulo,
            PapelTitulo,
            TipoTitulo,
        )

        carteira = _carteira_companhia()
        item = InferenciaTitulo(
            tipo=TipoTitulo.DEBENTURE,
            papel=PapelTitulo.OBRIGACAO,
            descricao="Debênture PETR27 emitida pela companhia",
            documento="relatorio.pdf",
            trecho="evidência",
        )

        arvore = self._arvore(
            [item], {"PETR4": carteira}, watchlist=("PETR4",)
        )
        caminho = "/direitos-obrigacoes/obrigacoes/titulos/debentures"
        nomes = [no.nome for no in arvore.listar(caminho)]
        assert nomes == ["PETR27"]
