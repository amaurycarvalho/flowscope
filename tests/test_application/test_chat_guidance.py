"""Testes da fonte do ramo ``/guidance`` da árvore de conhecimento."""

from datetime import date
from decimal import Decimal
from pathlib import Path

from flowscope.application.chat.arvore import ArvoreConhecimento, no_interno
from flowscope.application.chat.guidance import FonteGuidance
from flowscope.application.documentos.document_guidance import (
    EntradaGuidanceArvore,
)
from flowscope.domain.fii import Guidance


def _entrada(
    *,
    ticker: str = "HGBS11",
    ano: int = 2026,
    mes: int = 8,
    chave: str = "chave-1",
    caminho_pdf: str | None = None,
) -> EntradaGuidanceArvore:
    data = date(ano, mes, 1)
    guidance = Guidance(
        valor_min=Decimal("0.85"),
        valor_max=Decimal("0.85"),
        periodo="2026",
        data_relatorio=data,
    )
    return EntradaGuidanceArvore(
        ticker=ticker,
        ano=ano,
        mes=mes,
        chave=chave,
        data_relatorio=data,
        caminho_pdf=caminho_pdf,
        guidance=guidance,
    )


class _ServiceFake:
    """Serviço de guidance que devolve entradas pré-configuradas por ticker."""

    def __init__(self, mapa: dict) -> None:
        self._mapa = mapa
        self.consultas: list[str] = []

    def entradas_arvore(self, ticker: str) -> list:
        self.consultas.append(ticker)
        return list(self._mapa.get(ticker, []))


def _arvore(fonte: FonteGuidance) -> ArvoreConhecimento:
    raiz = no_interno("/", "/")
    no = fonte.construir()
    assert no is not None
    raiz.filho(no)
    return ArvoreConhecimento(raiz)


def _padrao(texto: str):
    from flowscope.application.chat.seguranca_regex import compilar

    return compilar(texto)


class TestFonteGuidance:
    def test_navegacao_expoe_anos_meses_e_folha(self):
        service = _ServiceFake(
            {"HGBS11": [_entrada(caminho_pdf="/cache/rg/10.pdf")]}
        )
        arvore = _arvore(FonteGuidance(["HGBS11"], service))

        assert arvore.existe("/guidance/HGBS11")
        assert [no.nome for no in arvore.listar("/guidance/HGBS11")] == [
            "indice",
            "2026",
        ]
        assert [
            no.nome for no in arvore.listar("/guidance/HGBS11/2026")
        ] == ["08"]
        folhas = arvore.listar("/guidance/HGBS11/2026/08")
        assert len(folhas) == 1
        assert folhas[0].nome.startswith("Guidance R$")
        conteudo = arvore.obter(folhas[0].caminho)
        assert conteudo.startswith("Guidance R$")
        assert "Relatório Gerencial — ago/26 (10.pdf)" in conteudo

    def test_ticker_sem_guidance_e_omitido(self):
        service = _ServiceFake({"HGBS11": [_entrada()]})
        fonte = FonteGuidance(["HGBS11", "SEM"], service)

        raiz = fonte.construir()

        assert raiz is not None
        nomes = [no.nome for no in raiz.filhos]
        assert nomes == ["HGBS11"]
        assert service.consultas == ["HGBS11", "SEM"]

    def test_sem_nenhuma_entrada_nao_monta_ramo(self):
        fonte = FonteGuidance(["SEM"], _ServiceFake({}))
        assert fonte.construir() is None

    def test_leitura_sem_efeitos_colaterais(self):
        service = _ServiceFake({"HGBS11": [_entrada()]})
        fonte = FonteGuidance(["HGBS11"], service)
        fonte.construir()
        assert service.consultas == ["HGBS11"]

    def test_rotulo_do_rg_e_pesquisavel_e_listavel(self):
        service = _ServiceFake(
            {"HGBS11": [_entrada(caminho_pdf="/cache/rg/1323324.pdf")]}
        )
        arvore = _arvore(FonteGuidance(["HGBS11"], service))

        folhas = arvore.listar("/guidance/HGBS11/2026/08")
        assert "1323324.pdf" in folhas[0].metadado
        resultado = arvore.buscar("/guidance", _padrao("1323324"), em=["relatorio"])
        assert [item["caminho"] for item in resultado["resultados"]] == [
            folhas[0].caminho
        ]

    def test_indice_cronologico_decrescente(self):
        julho = _entrada(ano=2026, mes=7, chave="c-jul", caminho_pdf="/rg/7.pdf")
        agosto = _entrada(ano=2026, mes=8, chave="c-ago", caminho_pdf="/rg/8.pdf")
        service = _ServiceFake({"HGBS11": [julho, agosto]})
        arvore = _arvore(FonteGuidance(["HGBS11"], service))

        linhas = arvore.obter("/guidance/HGBS11/indice").splitlines()
        assert linhas[0].startswith("ago/26")
        assert any(linha.startswith("jul/26") for linha in linhas)
        assert "Relatório Gerencial — ago/26 (8.pdf)" in linhas[0]

    def test_periodo_pesquisavel(self):
        service = _ServiceFake({"HGBS11": [_entrada(ano=2026, mes=7)]})
        arvore = _arvore(FonteGuidance(["HGBS11"], service))

        resultado = arvore.buscar("/guidance", _padrao("2026/07"), em=["periodo"])
        assert [item["trecho"] for item in resultado["resultados"]] == ["2026/07"]

    def test_falha_de_leitura_nao_quebra(self):
        class _Falha:
            def entradas_arvore(self, ticker):
                raise RuntimeError("ledger ilegível")

        assert FonteGuidance(["HGBS11"], _Falha()).construir() is None

    def test_documento_do_catalogo_da_nome_ao_rotulo(self):
        from flowscope.domain.documents import (
            AnoDocumentos,
            CatalogoTicker,
            CategoriaDocumentos,
            DocumentoArquivo,
            MesDocumentos,
        )

        entrada = _entrada(caminho_pdf="/cache/rg/10.pdf")
        service = _ServiceFake({"HGBS11": [entrada]})
        arquivo = DocumentoArquivo(
            ticker="HGBS11",
            ano=2026,
            mes=8,
            categoria="Relatorio",
            nome="relatorio-gerencial.pdf",
            tipo="pdf",
            caminho=Path("/cache/rg/10.pdf"),
        )
        catalogo = CatalogoTicker(
            "HGBS11",
            (
                AnoDocumentos(
                    2026,
                    (
                        MesDocumentos(
                            8,
                            (
                                CategoriaDocumentos(
                                    "Relatorio", (arquivo,)
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )

        class _CatalogoFake:
            def catalogo(self, ticker):
                return catalogo

        arvore = _arvore(
            FonteGuidance(["HGBS11"], service, _CatalogoFake())
        )
        folhas = arvore.listar("/guidance/HGBS11/2026/08")
        assert "relatorio-gerencial.pdf" in arvore.obter(folhas[0].caminho)
