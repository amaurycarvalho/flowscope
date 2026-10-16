"""Testes da orquestração de aquisição de documentos."""

from datetime import date

import pytest
import requests

from flowscope.application.cancellation import (
    CancellationToken,
    OperacaoCancelada,
)
from flowscope.domain.structured import FatoRelevante
from flowscope.infrastructure.b3.documentos_aquisicao import AquisicaoDocumentos
from flowscope.infrastructure.b3.documentos_relevantes import (
    DocumentosRelevantesProvider,
)
from flowscope.infrastructure.b3.informe_mensal_cache import (
    InformeMensalArquivoProvider,
)

_REFERENCIA = date(2026, 7, 29)
_URL_FATO = (
    "https://www.rad.cvm.gov.br/ENETWEB/"
    "frmExibirArquivoIPEExterno.aspx?ID=1510187"
)


def _fato(
    url: str = _URL_FATO,
    data_referencia: str = "2026-07-17T00:00:00-03:00",
) -> FatoRelevante:
    return FatoRelevante(
        code_cvm="9512",
        empresa="PETROBRAS",
        ticker="PETR3",
        data_referencia=data_referencia,
        data_entrega=None,
        categoria="Fato Relevante",
        tipo=None,
        especie=None,
        status="Ativo",
        assunto="Comunicado",
        url_documento=url,
        url_download=None,
    )


class _ClienteFake:
    def __init__(
        self,
        *,
        id_fnet: str | None = None,
        code_cvm: str | None = None,
        documentos_relevantes: list[dict] | None = None,
        fatos: dict | None = None,
        informes: list[dict] | None = None,
        erro_fatos: bool = False,
    ) -> None:
        self._id_fnet = id_fnet
        self._code_cvm = code_cvm
        self._documentos_relevantes = documentos_relevantes or []
        self._fatos = fatos or {}
        self._informes = informes or []
        self._erro_fatos = erro_fatos
        self.chamadas: list[str] = []
        self.janelas: list[tuple[str, date, date]] = []

    def resolver_ticker(self, ticker: str):
        return self._id_fnet

    def resolver_code_cvm(self, ticker: str):
        return self._code_cvm

    def listar_todos_documentos_relevantes(self, id_fnet, data_inicio, data_fim):
        self.janelas.append(("dr", data_inicio, data_fim))
        return list(self._documentos_relevantes)

    def baixar_pdf_documento(self, id_documento: str):
        self.chamadas.append(id_documento)
        return b"%PDF-1.4"

    def listar_fatos_relevantes(
        self, code_cvm, categoria, data_inicio, data_fim, ticker=""
    ):
        self.janelas.append(("mf", data_inicio, data_fim))
        if self._erro_fatos:
            raise requests.ConnectionError("offline")
        return list(self._fatos.get(str(categoria), []))

    def listar_documentos(self, id_fnet, data_inicio, data_fim, tipo, tolerante=True):
        self.janelas.append(("im", data_inicio, data_fim))
        return list(self._informes)

    def buscar_html_documento(self, id_documento: str):
        self.chamadas.append(id_documento)
        return "<html>informe</html>"


def _aquisicao(tmp_path, cliente, baixar_cvm=None):
    documentos = DocumentosRelevantesProvider(
        client=cliente, cache_dir=tmp_path / "dr"
    )
    informes = InformeMensalArquivoProvider(
        client=cliente, cache_dir=tmp_path / "im"
    )
    return (
        AquisicaoDocumentos(
            client=cliente,
            documentos=documentos,
            informes=informes,
            baixar_cvm=baixar_cvm,
        ),
        documentos,
        informes,
    )


class TestDeteccaoDeTipo:
    def test_ticker_nao_resolvido_nao_baixa(self, tmp_path):
        cliente = _ClienteFake()
        aquisicao, documentos, informes = _aquisicao(
            tmp_path, cliente, lambda _p: b"%PDF"
        )
        aquisicao.adquirir("PETR3", _REFERENCIA)
        assert cliente.chamadas == []
        assert documentos.cache.listar("PETR3") == []
        assert informes.cache.listar("PETR3") == []

    def test_ticker_vazio_nao_baixa(self, tmp_path):
        cliente = _ClienteFake(code_cvm="9512")
        aquisicao, _documentos, _informes = _aquisicao(
            tmp_path, cliente, lambda _p: b"%PDF"
        )
        aquisicao.adquirir("  ", _REFERENCIA)
        assert cliente.chamadas == []


class TestAcaoMaterialFacts:
    def test_grava_pdf_com_slug_da_categoria(self, tmp_path):
        cliente = _ClienteFake(code_cvm="9512", fatos={"4": [_fato()]})
        baixados = []

        def _baixar(protocolo):
            baixados.append(protocolo)
            return b"%PDF-1.4"

        aquisicao, documentos, _informes = _aquisicao(
            tmp_path, cliente, _baixar
        )
        aquisicao.adquirir("PETR3", _REFERENCIA)

        assert baixados == ["1510187"]
        assert documentos.cache.existe(
            "PETR3", date(2026, 7, 17), "fato-relevante", "1510187"
        )

    def test_data_de_referencia_com_hora_estabiliza_o_caminho(self, tmp_path):
        cliente = _ClienteFake(
            code_cvm="9512",
            fatos={"4": [_fato(data_referencia="17/07/2026 09:15:00")]},
        )
        aquisicao, documentos, _informes = _aquisicao(
            tmp_path, cliente, lambda _p: b"%PDF-1.4"
        )
        aquisicao.adquirir("PETR3", _REFERENCIA)

        assert documentos.cache.existe(
            "PETR3", date(2026, 7, 17), "fato-relevante", "1510187"
        )

    def test_falha_de_download_nao_cria_arquivo(self, tmp_path):
        cliente = _ClienteFake(code_cvm="9512", fatos={"4": [_fato()]})

        def _falha(_protocolo):
            raise requests.ConnectionError("offline")

        aquisicao, documentos, _informes = _aquisicao(
            tmp_path, cliente, _falha
        )
        aquisicao.adquirir("PETR3", _REFERENCIA)

        assert documentos.cache.listar("PETR3") == []

    def test_falha_de_listagem_nao_interrompe(self, tmp_path):
        cliente = _ClienteFake(code_cvm="9512", erro_fatos=True)
        aquisicao, _documentos, _informes = _aquisicao(
            tmp_path, cliente, lambda _p: b"%PDF"
        )
        aquisicao.adquirir("PETR3", _REFERENCIA)

    def test_material_fact_duplicado_nao_grava(self, tmp_path):
        outro_url = _URL_FATO.replace("1510187", "2000000")
        cliente = _ClienteFake(
            code_cvm="9512",
            fatos={"4": [_fato(), _fato(url=outro_url)]},
        )
        conteudo = b"%PDF-1.4\n" + b"x" * 2048
        aquisicao, _documentos, _informes = _aquisicao(
            tmp_path, cliente, lambda _p: conteudo
        )
        aquisicao.adquirir("PETR3", _REFERENCIA)
        assert len(list((tmp_path / "dr").rglob("*.pdf"))) == 1


class TestFii:
    def test_grava_documentos_relevantes_e_informe(self, tmp_path):
        itens = [
            {
                "urlViewerFundosNet": "https://fnet?id=1",
                "category": "2",
                "referenceDate": "2026-07-01T00:00:00-03:00",
            }
        ]
        informes = [
            {
                "urlViewerFundosNet": "https://fnet?id=99",
                "referenceDate": "2026-07-01T00:00:00-03:00",
                "status": "1 (Ativo)",
            }
        ]
        cliente = _ClienteFake(
            id_fnet="20294",
            documentos_relevantes=itens,
            informes=informes,
        )
        aquisicao, documentos, informes_provider = _aquisicao(tmp_path, cliente)
        aquisicao.adquirir("ALZR11", _REFERENCIA)

        assert documentos.cache.existe(
            "ALZR11", date(2026, 7, 1), "assembleia", "1"
        )
        assert informes_provider.cache.existe(
            "ALZR11", date(2026, 7, 1), 99
        )

    def test_fii_sem_documentos_nao_falha(self, tmp_path):
        cliente = _ClienteFake(id_fnet="20294")
        aquisicao, _documentos, _informes = _aquisicao(tmp_path, cliente)
        aquisicao.adquirir("ALZR11", _REFERENCIA)


class TestReusoDeCache:
    def test_cache_hit_nao_baixa_novamente(self, tmp_path):
        cliente = _ClienteFake(code_cvm="9512", fatos={"4": [_fato()]})
        baixados = []

        def _baixar(protocolo):
            baixados.append(protocolo)
            return b"%PDF-1.4"

        aquisicao, _documentos, _informes = _aquisicao(
            tmp_path, cliente, _baixar
        )
        aquisicao.adquirir("PETR3", _REFERENCIA)
        aquisicao.adquirir("PETR3", _REFERENCIA)

        assert baixados == ["1510187"]


class TestReusoPorUrl:
    def test_url_registrada_nao_baixa_com_data_diferente(self, tmp_path):
        cliente = _ClienteFake(code_cvm="9512", fatos={"4": [_fato()]})
        baixados: list[str] = []

        def _baixar(protocolo):
            baixados.append(protocolo)
            return b"%PDF-1.4"

        aquisicao, _documentos, _informes = _aquisicao(
            tmp_path, cliente, _baixar
        )
        aquisicao.adquirir("PETR3", _REFERENCIA)
        # mesma URL reapresentada com data de referência em outro mês
        cliente._fatos = {
            "4": [_fato(data_referencia="2026-09-17T00:00:00-03:00")]
        }
        aquisicao.adquirir("PETR3", _REFERENCIA)

        assert baixados == ["1510187"]

    def test_duplicata_registra_url_e_nao_rebaixa(self, tmp_path):
        url_a = _URL_FATO
        url_b = _URL_FATO.replace("1510187", "2000000")
        conteudo = b"%PDF-1.4\n" + b"x" * 2048
        cliente = _ClienteFake(
            code_cvm="9512",
            fatos={"4": [_fato(url=url_a), _fato(url=url_b)]},
        )
        baixados: list[str] = []

        def _baixar(protocolo):
            baixados.append(protocolo)
            return conteudo

        aquisicao, documentos, _informes = _aquisicao(
            tmp_path, cliente, _baixar
        )
        aquisicao.adquirir("PETR3", _REFERENCIA)
        assert baixados == ["1510187", "2000000"]

        urls = documentos.urls("PETR3")
        assert urls.canonico(url_a) is not None
        assert urls.canonico(url_b) == urls.canonico(url_a)

        baixados.clear()
        aquisicao.adquirir("PETR3", _REFERENCIA)
        assert baixados == []

    def test_url_registrada_nao_baixa_para_fii(self, tmp_path):
        item = {
            "urlViewerFundosNet": "https://fnet?id=1",
            "category": "2",
            "referenceDate": "2026-07-01T00:00:00-03:00",
        }
        cliente = _ClienteFake(id_fnet="20294", documentos_relevantes=[item])
        baixados: list[str] = []

        def _baixar(id_documento):
            baixados.append(id_documento)
            return b"%PDF-1.4"

        cliente.baixar_pdf_documento = _baixar  # type: ignore[method-assign]
        aquisicao, _documentos, _informes = _aquisicao(tmp_path, cliente)
        aquisicao.adquirir("ALZR11", _REFERENCIA)
        # mesma URL com data de referência em outro mês
        cliente._documentos_relevantes = [
            {**item, "referenceDate": "2026-09-01T00:00:00-03:00"}
        ]
        aquisicao.adquirir("ALZR11", _REFERENCIA)

        assert baixados == ["1"]


class TestJanelaDe12Meses:
    def test_acao_usa_janela_de_12_meses(self, tmp_path):
        cliente = _ClienteFake(code_cvm="9512", fatos={"4": [_fato()]})
        aquisicao, _documentos, _informes = _aquisicao(
            tmp_path, cliente, lambda _p: b"%PDF"
        )
        aquisicao.adquirir("PETR3", _REFERENCIA)

        assert cliente.janelas
        assert all(
            inicio == date(2025, 7, 29)
            for _tipo, inicio, _fim in cliente.janelas
        )
        assert all(
            fim == _REFERENCIA for _tipo, _inicio, fim in cliente.janelas
        )

    def test_fii_usa_janela_de_12_meses(self, tmp_path):
        itens = [
            {
                "urlViewerFundosNet": "https://fnet?id=1",
                "category": "2",
                "referenceDate": "2026-07-01T00:00:00-03:00",
            }
        ]
        informes = [
            {
                "urlViewerFundosNet": "https://fnet?id=99",
                "referenceDate": "2026-07-01T00:00:00-03:00",
                "status": "1 (Ativo)",
            }
        ]
        cliente = _ClienteFake(
            id_fnet="20294",
            documentos_relevantes=itens,
            informes=informes,
        )
        aquisicao, _documentos, _informes = _aquisicao(tmp_path, cliente)
        aquisicao.adquirir("ALZR11", _REFERENCIA)

        assert {tipo for tipo, _i, _f in cliente.janelas} == {"dr", "im"}
        assert all(
            inicio == date(2025, 7, 29)
            for _tipo, inicio, _fim in cliente.janelas
        )


class TestProgresso:
    def test_acao_reporta_progresso_por_documento(self, tmp_path):
        cliente = _ClienteFake(code_cvm="9512", fatos={"4": [_fato()]})
        aquisicao, _documentos, _informes = _aquisicao(
            tmp_path, cliente, lambda _p: b"%PDF"
        )
        eventos: list[tuple[int, int, str]] = []
        aquisicao.adquirir(
            "PETR3",
            _REFERENCIA,
            progress=lambda current, total, label: eventos.append(
                (current, total, label)
            ),
        )

        assert eventos
        assert eventos[0][0] == 0
        assert eventos[-1][0] == eventos[-1][1] == 1
        assert all(total == 1 for _c, total, _l in eventos)
        assert "PETR3" in eventos[-1][2]

    def test_fii_reporta_total_incluindo_informe(self, tmp_path):
        itens = [
            {
                "urlViewerFundosNet": "https://fnet?id=1",
                "category": "2",
                "referenceDate": "2026-07-01T00:00:00-03:00",
            }
        ]
        informes = [
            {
                "urlViewerFundosNet": "https://fnet?id=99",
                "referenceDate": "2026-07-01T00:00:00-03:00",
                "status": "1 (Ativo)",
            }
        ]
        cliente = _ClienteFake(
            id_fnet="20294",
            documentos_relevantes=itens,
            informes=informes,
        )
        aquisicao, _documentos, _informes = _aquisicao(tmp_path, cliente)
        eventos: list[tuple[int, int]] = []
        aquisicao.adquirir(
            "ALZR11",
            _REFERENCIA,
            progress=lambda current, total, _label: eventos.append(
                (current, total)
            ),
        )

        assert eventos[0] == (0, 2)
        assert eventos[-1] == (2, 2)

    def test_sem_progresso_nao_falha(self, tmp_path):
        cliente = _ClienteFake(code_cvm="9512", fatos={"4": [_fato()]})
        aquisicao, _documentos, _informes = _aquisicao(
            tmp_path, cliente, lambda _p: b"%PDF"
        )
        aquisicao.adquirir("PETR3", _REFERENCIA)


class TestCancelamento:
    def test_cancelamento_interrompe_acao_apos_primeiro_documento(self, tmp_path):
        fatos = {
            "4": [
                _fato(url=_URL_FATO),
                _fato(
                    url=(
                        "https://www.rad.cvm.gov.br/ENETWEB/"
                        "frmExibirArquivoIPEExterno.aspx?ID=222"
                    )
                ),
            ]
        }
        cliente = _ClienteFake(code_cvm="9512", fatos=fatos)
        baixados: list[str] = []

        def _baixar(protocolo):
            baixados.append(protocolo)
            return b"%PDF-1.4"

        aquisicao, _documentos, _informes = _aquisicao(
            tmp_path, cliente, _baixar
        )
        token = CancellationToken()

        def progresso(current: int, _total: int, _label: str) -> None:
            if current >= 1:
                token.request()

        with pytest.raises(OperacaoCancelada):
            aquisicao.adquirir(
                "PETR3",
                _REFERENCIA,
                progress=progresso,
                cancel_token=token,
            )

        assert baixados == ["1510187"]


class TestContagemAdquiridos:
    def test_ticker_nao_resolvido_retorna_vazio(self, tmp_path):
        cliente = _ClienteFake()
        aquisicao, _, _ = _aquisicao(tmp_path, cliente, lambda _p: b"%PDF")

        assert aquisicao.adquirir("PETR3", _REFERENCIA).adquiridos == 0

    def test_sem_documentos_retorna_vazio(self, tmp_path):
        cliente = _ClienteFake(code_cvm="9512", fatos={})
        aquisicao, _, _ = _aquisicao(
            tmp_path, cliente, lambda _p: b"%PDF-1.4"
        )

        assert aquisicao.adquirir("PETR3", _REFERENCIA).adquiridos == 0
        assert aquisicao.adquirir("PETR3", _REFERENCIA).falhas == 0

    def test_material_fact_persistido_conta_como_novo(self, tmp_path):
        cliente = _ClienteFake(code_cvm="9512", fatos={"4": [_fato()]})
        aquisicao, _, _ = _aquisicao(
            tmp_path, cliente, lambda _p: b"%PDF-1.4"
        )

        resultado = aquisicao.adquirir("PETR3", _REFERENCIA)
        assert resultado.novos == 1
        assert resultado.reutilizados == 0
        assert resultado.falhas == 0

    def test_reuso_de_cache_conta_como_reutilizado(self, tmp_path):
        cliente = _ClienteFake(code_cvm="9512", fatos={"4": [_fato()]})
        aquisicao, _, _ = _aquisicao(
            tmp_path, cliente, lambda _p: b"%PDF-1.4"
        )

        aquisicao.adquirir("PETR3", _REFERENCIA)
        resultado = aquisicao.adquirir("PETR3", _REFERENCIA)
        assert resultado.reutilizados == 1
        assert resultado.novos == 0

    def test_download_falho_conta_como_falha(self, tmp_path):
        cliente = _ClienteFake(code_cvm="9512", fatos={"4": [_fato()]})
        aquisicao, _, _ = _aquisicao(tmp_path, cliente, lambda _p: None)

        resultado = aquisicao.adquirir("PETR3", _REFERENCIA)
        assert resultado.falhas == 1
        assert resultado.adquiridos == 0
