import base64
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from flowscope.domain.fii.dividends import (
    TendenciaDividendo,
    calcular_ultimo_dividendo_consolidado,
)
from flowscope.infrastructure.b3.bdr import (
    BdrClient,
    BdrDividendProvider,
    PdfCache,
    decodificar_pdf,
    extrair_texto,
    filtrar_avisos,
    itens_de_noticias,
    janelas_mensais,
    listar_avisos,
    parse_dividendo,
    resolver_url_documento,
)

_FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "b3"
REFERENCIA = date(2026, 10, 1)


def _fixture(nome: str) -> str:
    return (_FIXTURES / nome).read_text(encoding="utf-8")


def _pdf_bytes() -> bytes:
    return base64.b64decode(_fixture("bdr_aviso_exxo.pdf.b64"))


class TestListagemAvisos:
    def test_filtra_raiz_e_termo(self):
        itens = json.loads(_fixture("bdr_noticias_exxo.json"))
        avisos = filtrar_avisos(itens, "EXXO34")
        assert [aviso.id_noticia for aviso in avisos] == ["3480343"]
        assert "Aviso aos Acionistas" in avisos[0].titulo

    def test_formato_real_nwsmsg_e_desembrulhado(self):
        itens = json.loads(_fixture("bdr_noticias_exxo.json"))
        assert itens_de_noticias(itens)[0]["id"] == 3480343
        assert itens_de_noticias(itens)[0]["headline"].startswith("EXXON MOBIL")

    def test_item_de_outra_empresa_nao_e_aviso(self):
        itens = [
            {
                "idNoticia": 1,
                "titulo": "DEXXOS PAR (DEXP-N1) - Fato Relevante",
            }
        ]
        assert filtrar_avisos(itens, "EXXO34") == []

    def test_janelas_mensais_cobrem_12_meses_sem_sobreposicao(self):
        janelas = janelas_mensais(REFERENCIA)
        assert len(janelas) == 12
        assert janelas[0] == (date(2026, 10, 1), date(2026, 10, 1))
        assert janelas[1] == (date(2026, 9, 1), date(2026, 9, 30))
        assert janelas[-1] == (date(2025, 11, 1), date(2025, 11, 30))

    def test_janela_sem_avisos_nao_quebra(self):
        avisos = listar_avisos(
            lambda *_args: [], "EXXO34", REFERENCIA, meses=3
        )
        assert avisos == []

    def test_falha_de_uma_janela_nao_interrompe(self):
        chamadas = {"n": 0}

        def coletar(*_args):
            chamadas["n"] += 1
            if chamadas["n"] == 1:
                raise ConnectionError("fora do ar")
            return [
                {
                    "idNoticia": 123456,
                    "titulo": "EXXON MOBIL (EXXO) - Aviso aos Acionistas",
                }
            ]

        avisos = listar_avisos(coletar, "EXXO34", REFERENCIA, meses=3)
        assert [aviso.id_noticia for aviso in avisos] == ["123456"]


class TestDocumento:
    def test_resolve_url_do_documento(self):
        url = resolver_url_documento(_fixture("bdr_detail_exxo.html"))
        assert url is not None
        assert "frmExibirArquivoIPEExterno" in url

    def test_sem_documento_retorna_none(self):
        assert resolver_url_documento("<html><body>nada</body></html>") is None

    def test_decodifica_pdf_base64(self):
        conteudo = base64.b64encode(_pdf_bytes()).decode("ascii")
        dados = decodificar_pdf({"d": conteudo})
        assert dados is not None
        assert dados.startswith(b"%PDF")

    def test_conteudo_nao_pdf_e_rejeitado(self):
        conteudo = base64.b64encode(b"<html>erro</html>").decode("ascii")
        assert decodificar_pdf({"d": conteudo}) is None

    def test_payload_sem_campo_e_rejeitado(self):
        assert decodificar_pdf({"outro": "x"}) is None


class TestCachePdf:
    def test_arvore_por_ticker_ano_mes(self, tmp_path):
        cache = PdfCache(tmp_path)
        caminho = cache.caminho("EXXO34", date(2026, 2, 10), "123456")
        assert caminho == tmp_path / "EXXO34" / "2026" / "02" / "123456.pdf"

    def test_grava_e_le(self, tmp_path):
        cache = PdfCache(tmp_path)
        cache.gravar("EXXO34", date(2026, 2, 10), "123456", b"%PDF-1.4")
        assert cache.existe("EXXO34", date(2026, 2, 10), "123456")
        assert cache.ler("EXXO34", date(2026, 2, 10), "123456") == b"%PDF-1.4"

class TestExtracaoTexto:
    def test_extrai_texto_do_pdf(self):
        texto = extrair_texto(_pdf_bytes())
        assert "0,455484428" in texto
        assert "10/02/2026" in texto

    def test_pdf_invalido_retorna_vazio(self):
        assert extrair_texto(b"nao e pdf") == ""


class TestParserDividendo:
    def test_extrai_valor_data_com_e_identidade(self):
        texto = extrair_texto(_pdf_bytes())
        dividendo = parse_dividendo(texto)
        assert dividendo is not None
        assert dividendo.valor == Decimal("0.455484428")
        assert dividendo.data_com == date(2026, 2, 10)
        assert dividendo.data_pagamento == date(2026, 2, 26)
        assert dividendo.tipo == "Dividendos"
        assert dividendo.isin == "BREXXOBDR006"
        assert dividendo.depositario == "Banco B3 S.A."
        assert dividendo.empresa == "Exxon Mobil Corporation"

    def test_extrai_do_texto_real_da_cvm(self):
        texto = (
            "O  Banco B3 S.A. , na qualidade de depositário e emissor do Programa "
            "de BDR Nível I Não Patrocinado da Exxon Mobil Corporation , código "
            "ISIN BREXXOBDR006, informa que foi aprovado em 30/01/2026 o pagamento "
            "do(a) Dividendos no valor de USD 1,030000000 , que considerando a taxa "
            "de conversão (USD / R$) de 5,2301, corresponde a um valor prévio de R$ "
            "0,455484428 por BDR. O evento será pago no dia 16/03/2026, aos "
            "titulares de BDRs em 10/02/2026. Obs.: O valor informado acima já "
            "está deduzido de 30% de IR, 0,38% de IOF e 3% referente a tarifa "
            "cobrada pelo Banco B3."
        )
        dividendo = parse_dividendo(texto)
        assert dividendo is not None
        assert dividendo.valor == Decimal("0.455484428")
        assert dividendo.data_com == date(2026, 2, 10)
        assert dividendo.data_pagamento == date(2026, 3, 16)
        assert dividendo.depositario == "Banco B3 S.A."
        assert dividendo.empresa == "Exxon Mobil Corporation"
        assert dividendo.isin == "BREXXOBDR006"
        assert dividendo.nivel_programa == "Nível I Não Patrocinado"
        assert dividendo.observacao == (
            "O valor informado acima já está deduzido de 30% de IR, 0,38% "
            "de IOF e 3% referente a tarifa cobrada pelo Banco B3"
        )

    def test_aviso_sem_valor_e_ignorado(self):
        assert parse_dividendo("Aviso sem valor reconhecivel") is None

    def test_texto_vazio_e_ignorado(self):
        assert parse_dividendo("") is None


class _ClienteFake:
    def __init__(self, itens, pdfs):
        self._itens = itens
        self._pdfs = pdfs
        self.chamadas_pdf: list[str] = []

    def coletar_noticias(self, agencia, palavra, inicio, fim):
        return list(self._itens)

    def obter_pdf_de_aviso(self, id_noticia, data_noticia):
        self.chamadas_pdf.append(id_noticia)
        return self._pdfs.get(id_noticia)


class TestProvider:
    def _cliente(self):
        return _ClienteFake(
            [
                {
                    "idNoticia": 123456,
                    "titulo": "EXXON MOBIL (EXXO) - Aviso aos Acionistas",
                    "dataPublicacao": "11/09/2026",
                }
            ],
            {"123456": _pdf_bytes()},
        )

    def test_obter_dados_bdr_preenche_identidade_e_dividendos(self, tmp_path):
        provider = BdrDividendProvider(client=self._cliente(), cache_dir=tmp_path)
        dados = provider.obter_dados_bdr("EXXO34", REFERENCIA)
        assert dados is not None
        assert dados.nome_depositario == "Banco B3 S.A."
        assert dados.nome_empresa == "Exxon Mobil Corporation"
        assert dados.isin == "BREXXOBDR006"
        assert len(dados.dividendos) == 1
        assert dados.dividendos[0].data_base == date(2026, 2, 10)

    def test_segunda_leitura_nao_baixa_novamente(self, tmp_path):
        cliente = self._cliente()
        provider = BdrDividendProvider(client=cliente, cache_dir=tmp_path)
        provider.obter_dados_bdr("EXXO34", REFERENCIA)
        provider.obter_dados_bdr("EXXO34", REFERENCIA)
        assert cliente.chamadas_pdf == ["123456"]

    def test_falha_de_download_nao_interrompe(self, tmp_path):
        cliente = _ClienteFake(
            [
                {
                    "idNoticia": 1,
                    "titulo": "EXXON MOBIL (EXXO) - Aviso aos Acionistas",
                }
            ],
            {},
        )
        provider = BdrDividendProvider(client=cliente, cache_dir=tmp_path)
        dados = provider.obter_dados_bdr("EXXO34", REFERENCIA)
        assert dados is not None
        assert dados.dividendos == ()

    def test_obter_dividendos_delega_ao_dados_bdr(self, tmp_path):
        provider = BdrDividendProvider(client=self._cliente(), cache_dir=tmp_path)
        dividendos = provider.obter_dividendos("EXXO34", REFERENCIA)
        assert len(dividendos) == 1
        assert dividendos[0].fonte == "BDR"

    def test_ultimo_anterior_e_tendencia(self, tmp_path):
        textos = {
            b"pdf-1": (
                "valor previo de R$ 0,50 por BDR\n"
                "titulares de BDRs em 10/11/2025"
            ),
            b"pdf-2": (
                "valor previo de R$ 0,45 por BDR\n"
                "titulares de BDRs em 10/08/2025"
            ),
        }
        cliente = _ClienteFake(
            [
                {
                    "idNoticia": 1,
                    "titulo": "EXXON MOBIL (EXXO) - Aviso aos Acionistas",
                    "dataPublicacao": "10/11/2025",
                },
                {
                    "idNoticia": 2,
                    "titulo": "EXXON MOBIL (EXXO) - Aviso aos Acionistas",
                    "dataPublicacao": "10/08/2025",
                },
            ],
            {"1": b"pdf-1", "2": b"pdf-2"},
        )
        provider = BdrDividendProvider(
            client=cliente, cache_dir=tmp_path, extractor=lambda d: textos[d]
        )
        dados = provider.obter_dados_bdr("EXXO34", REFERENCIA)
        ultimo = calcular_ultimo_dividendo_consolidado(
            list(dados.dividendos), REFERENCIA
        )
        assert ultimo.data_com == date(2025, 11, 10)
        assert ultimo.valor == Decimal("0.50")
        assert ultimo.valor_anterior == Decimal("0.45")
        assert ultimo.tendencia is TendenciaDividendo.FORTE_ALTA

    def test_propaga_nivel_do_programa_e_observacao_fiscal(self, tmp_path):
        texto = (
            "O Banco B3 S.A. , na qualidade de depositário e emissor do "
            "Programa de BDR Nível I Não Patrocinado da Exxon Mobil "
            "Corporation , código ISIN BREXXOBDR006, informa o pagamento de "
            "Dividendos, valor prévio de R$ 0,50 por BDR, aos titulares de "
            "BDRs em 10/11/2025. Obs.: O valor informado acima já está "
            "deduzido de 30% de IR, 0,38% de IOF e 3% referente a tarifa "
            "cobrada pelo Banco B3."
        )
        cliente = _ClienteFake(
            [
                {
                    "idNoticia": 1,
                    "titulo": "EXXON MOBIL (EXXO) - Aviso aos Acionistas",
                    "dataPublicacao": "10/11/2025",
                }
            ],
            {"1": b"pdf-1"},
        )
        provider = BdrDividendProvider(
            client=cliente, cache_dir=tmp_path, extractor=lambda _d: texto
        )
        dados = provider.obter_dados_bdr("EXXO34", REFERENCIA)
        assert dados.nivel_programa == "Nível I Não Patrocinado"
        assert dados.observacao == (
            "O valor informado acima já está deduzido de 30% de IR, 0,38% "
            "de IOF e 3% referente a tarifa cobrada pelo Banco B3"
        )


class _SessaoFake:
    def __init__(self, json_payload=None, text=""):
        self._json = json_payload
        self._text = text
        self.chamadas: list[dict] = []

    def get(self, url, **kwargs):
        self.chamadas.append({"metodo": "GET", "url": url, **kwargs})
        return _Resposta(self._json, self._text)

    def post(self, url, **kwargs):
        self.chamadas.append({"metodo": "POST", "url": url, **kwargs})
        return _Resposta(self._json, self._text)


class _Resposta:
    def __init__(self, json_payload, text):
        self._json = json_payload
        self.text = text

    def raise_for_status(self):
        pass

    def json(self):
        return self._json


class TestBdrClient:
    def test_obter_pdf_de_aviso_fluxo_completo(self):
        conteudo = base64.b64encode(_pdf_bytes()).decode("ascii")
        sessao = _SessaoFake(json_payload={"d": conteudo})
        sessao._text = _fixture("bdr_detail_exxo.html")
        cliente = BdrClient(session=sessao)
        dados = cliente.obter_pdf_de_aviso("3480343", date(2026, 9, 11))
        assert dados is not None
        assert dados.startswith(b"%PDF")
        metodos = [chamada["metodo"] for chamada in sessao.chamadas]
        assert metodos == ["GET", "POST"]
        get = sessao.chamadas[0]
        assert get["params"]["agencia"] == "18"
        assert get["params"]["idNoticia"] == "3480343"
        assert get["params"]["dataNoticia"] == "2026-09-11"
        post = sessao.chamadas[1]
        assert "codigoInstituicao" in post["data"]
        assert "1567325" in post["data"]

    def test_post_invalido_retorna_none(self):
        sessao = _SessaoFake(json_payload={"d": "nao-base64"})
        sessao._text = _fixture("bdr_detail_exxo.html")
        cliente = BdrClient(session=sessao)
        assert (
            cliente.obter_pdf_de_aviso("3480343", date(2026, 9, 11)) is None
        )

    def test_id_protocolo_extrai_id_da_url(self):
        from flowscope.infrastructure.b3.bdr import id_protocolo

        url = (
            "https://www.rad.cvm.gov.br/ENETWEB/"
            "frmExibirArquivoIPEExterno.aspx?ID=1567325&flnk"
        )
        assert id_protocolo(url) == "1567325"
