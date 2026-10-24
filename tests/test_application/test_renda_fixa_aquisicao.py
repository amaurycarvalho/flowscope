"""Testes da aquisição, mesclagem e cache dos títulos de renda fixa."""

from datetime import date
from decimal import Decimal

import pytest

from flowscope.application.renda_fixa import (
    AquisicaoTitulos,
    ResultadoFontes,
    carteira_de_dict,
    carteira_para_dict,
)
from flowscope.domain.renda_fixa import (
    CarteiraTitulos,
    DocumentoRelacionado,
    FonteTitulos,
    PapelTitulo,
    TipoTitulo,
    TituloAgregado,
    TituloRendaFixa,
)
from flowscope.infrastructure.cvm.renda_fixa_cache import RepositorioTitulosJson

_REFERENCIA = date(2026, 9, 30)


class _RepositorioFake:
    def __init__(self, anterior: CarteiraTitulos | None = None) -> None:
        self.anterior = anterior
        self.gravacoes: list[CarteiraTitulos] = []

    def ler(self, ticker: str) -> CarteiraTitulos | None:
        return self.anterior

    def gravar(self, carteira: CarteiraTitulos) -> None:
        self.gravacoes.append(carteira)
        self.anterior = carteira


class _FonteFake:
    def __init__(self, resultado: ResultadoFontes | None = None) -> None:
        self.resultado = resultado or ResultadoFontes()
        self.chamadas = 0
        self.anteriores = []

    def obter(
        self,
        ticker,
        cnpj,
        tipo_ativo,
        reference_date,
        progress=None,
        cancelar=None,
        anterior=None,
    ):
        self.chamadas += 1
        self.anteriores.append(anterior)
        if progress is not None:
            progress(1, 1, "Títulos: teste")
        return self.resultado


def _titulo(
    id_: str = "t1",
    tipo: TipoTitulo = TipoTitulo.DEBENTURE,
    papel: PapelTitulo = PapelTitulo.OBRIGACAO,
    fonte: str = "FRE",
    valor: str | None = None,
) -> TituloRendaFixa:
    return TituloRendaFixa(
        tipo=tipo,
        papel=papel,
        id=id_,
        identificacao=id_,
        fonte=fonte,
        data_referencia=_REFERENCIA,
        valor=Decimal(valor) if valor else None,
    )


def _aquisicao(repositorio, fonte, resolver=None, documentos=None):
    return AquisicaoTitulos(
        repositorio,
        fonte,
        resolver or (lambda _ticker, _ref: ("33000167000101", "acao")),
        documentos,
    )


class TestCache:
    def test_primeira_gravacao(self):
        fonte = _FonteFake(ResultadoFontes(obrigacoes=(_titulo(),)))
        repo = _RepositorioFake()
        resultado = _aquisicao(repo, fonte).adquirir("PETR4", _REFERENCIA)
        assert resultado.novos == 1
        assert len(repo.gravacoes) == 1
        assert repo.anterior is not None
        assert repo.anterior.obrigacoes[0].id == "t1"

    def test_reutiliza_sem_reescrever(self):
        fonte = _FonteFake(ResultadoFontes(obrigacoes=(_titulo(),)))
        repo = _RepositorioFake()
        aquisicao = _aquisicao(repo, fonte)
        aquisicao.adquirir("PETR4", _REFERENCIA)
        resultado = aquisicao.adquirir("PETR4", _REFERENCIA)
        assert resultado.reutilizados == 1
        assert len(repo.gravacoes) == 1

    def test_segunda_aquisicao_entrega_cache_anterior_a_fonte(self):
        fonte = _FonteFake(ResultadoFontes(obrigacoes=(_titulo(),)))
        repo = _RepositorioFake()
        aquisicao = _aquisicao(repo, fonte)
        aquisicao.adquirir("PETR4", _REFERENCIA)
        anterior = repo.anterior
        aquisicao.adquirir("PETR4", _REFERENCIA)
        assert fonte.anteriores[0] is None
        assert fonte.anteriores[1] is anterior

    def test_mudanca_substitui_assinatura(self):
        fonte = _FonteFake(ResultadoFontes(obrigacoes=(_titulo(valor="10"),)))
        repo = _RepositorioFake()
        aquisicao = _aquisicao(repo, fonte)
        aquisicao.adquirir("PETR4", _REFERENCIA)
        antes = repo.anterior.assinatura
        fonte.resultado = ResultadoFontes(obrigacoes=(_titulo(valor="20"),))
        resultado = aquisicao.adquirir("PETR4", _REFERENCIA)
        assert resultado.atualizados == 1
        assert repo.anterior.assinatura != antes
        assert len(repo.gravacoes) == 2

    def test_ticker_sem_cnpj_nao_grava(self):
        fonte = _FonteFake()
        repo = _RepositorioFake()
        aquisicao = AquisicaoTitulos(
            repo, fonte, lambda _ticker, _ref: None
        )
        resultado = aquisicao.adquirir("XPTO", _REFERENCIA)
        assert resultado.sem_cnpj
        assert fonte.chamadas == 0
        assert repo.gravacoes == []

    def test_idempotencia_nao_duplica(self):
        fonte = _FonteFake(ResultadoFontes(obrigacoes=(_titulo(),)))
        repo = _RepositorioFake()
        aquisicao = _aquisicao(repo, fonte)
        aquisicao.adquirir("PETR4", _REFERENCIA)
        aquisicao.adquirir("PETR4", _REFERENCIA)
        assert len(repo.anterior.obrigacoes) == 1


class TestMesclagem:
    def test_falha_de_direitos_preserva_cache_anterior(self):
        anterior = CarteiraTitulos(
            ticker="PETR4",
            obrigacoes=(_titulo("old"),),
            direitos=(
                _titulo(
                    "right",
                    TipoTitulo.CRI,
                    PapelTitulo.DIREITO,
                    "FII_INF_TRIMESTRAL",
                ),
            ),
        )
        repo = _RepositorioFake(anterior)
        fonte = _FonteFake(
            ResultadoFontes(
                obrigacoes=(_titulo("new"),),
                falhas=frozenset({"FII_INF_TRIMESTRAL"}),
            )
        )
        _aquisicao(repo, fonte).adquirir("PETR4", _REFERENCIA)
        ids = {item.id for item in repo.anterior.direitos}
        assert ids == {"right"}
        assert {item.id for item in repo.anterior.obrigacoes} == {"new"}

    def test_falha_do_securit_preserva_enriquecimento(self):
        anterior_title = TituloRendaFixa(
            tipo=TipoTitulo.CRI,
            papel=PapelTitulo.OBRIGACAO,
            id="cri",
            ltv=Decimal("80"),
            garantias="Fidejussória",
        )
        anterior = CarteiraTitulos(
            ticker="PETR4", obrigacoes=(anterior_title,)
        )
        fonte = _FonteFake(
            ResultadoFontes(
                obrigacoes=(_titulo("cri", TipoTitulo.CRI),),
                falhas=frozenset({"SECURIT_CRI"}),
            )
        )
        repo = _RepositorioFake(anterior)
        _aquisicao(repo, fonte).adquirir("PETR4", _REFERENCIA)
        assert repo.anterior.obrigacoes[0].ltv == Decimal("80")
        assert repo.anterior.obrigacoes[0].garantias == "Fidejussória"

    def test_agregados_sao_mesclados(self):
        anterior = CarteiraTitulos(
            ticker="ALZR11",
            agregados=(
                TituloAgregado(
                    TipoTitulo.CDB,
                    PapelTitulo.DIREITO,
                    valor=Decimal("10"),
                    fonte="FII_INF_MENSAL",
                ),
            ),
        )
        fonte = _FonteFake(ResultadoFontes(falhas=frozenset({"FII_INF_MENSAL"})))
        repo = _RepositorioFake(anterior)
        _aquisicao(
            repo,
            fonte,
            resolver=lambda _ticker, _ref: ("11444777000161", "fii"),
        ).adquirir("ALZR11", _REFERENCIA)
        assert repo.anterior.agregados[0].valor == Decimal("10")


class TestDocumentosRelacionados:
    def test_links_sao_anexados_aos_titulos(self):
        link = DocumentoRelacionado(
            descricao="Aviso", url="https://exemplo/aviso", fonte="B3"
        )
        fonte = _FonteFake(ResultadoFontes(obrigacoes=(_titulo(),)))
        repo = _RepositorioFake()
        _aquisicao(
            repo,
            fonte,
            documentos=lambda _ticker, _ref, _cnpj: [link],
        ).adquirir("PETR4", _REFERENCIA)
        assert repo.anterior.obrigacoes[0].documentos == (link,)


class TestRepositorioJson:
    def test_round_trip(self, tmp_path):
        carteira = CarteiraTitulos(
            ticker="PETR4",
            cnpj="33000167000101",
            tipo_ativo="acao",
            assinatura="sig",
            adquirido_em="2026-09-30T00:00:00+00:00",
            data_referencia=_REFERENCIA,
            fontes={"fre": FonteTitulos(_REFERENCIA, "fre.csv", "abc")},
            obrigacoes=(_titulo(),),
        )
        repo = RepositorioTitulosJson(tmp_path)
        repo.gravar(carteira)
        lida = repo.ler("PETR4")
        assert lida == carteira
        assert carteira_de_dict(carteira_para_dict(carteira)) == carteira

    def test_ticker_invalido(self, tmp_path):
        with pytest.raises(ValueError):
            RepositorioTitulosJson(tmp_path).caminho("../x")

    def test_cache_corrompido_retorna_none(self, tmp_path):
        repo = RepositorioTitulosJson(tmp_path)
        caminho = repo.caminho("PETR4")
        caminho.parent.mkdir(parents=True)
        caminho.write_text("{invalido", encoding="utf-8")
        assert repo.ler("PETR4") is None
