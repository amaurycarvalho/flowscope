import pytest

from flowscope.domain.structured import (
    Assembleia,
    AvisoAcionista,
    AvisoDebenturista,
    CensuraPublica,
    CondicaoExcepcional,
    DocumentoMaterialFact,
    FatoRelevante,
    NoticiaB3,
    ProgramaAquisicao,
)


def _material_fact(**campos) -> dict:
    base = {
        "code_cvm": "9512",
        "empresa": "PETROLEO BRASILEIRO S.A. PETROBRAS",
        "ticker": "PETR4",
        "data_referencia": "16/04/2026 14:16",
        "data_entrega": "28/04/2026 19:19:42",
        "categoria": "Fatos Relevantes",
        "tipo": None,
        "especie": None,
        "status": "Ativo",
        "assunto": "Tomada de Contas-Votação do Relatório da Administração",
        "url_documento": "https://www.rad.cvm.gov.br/ENETWEB/frmExibirArquivoIPEExterno.aspx?ID=1510187",
        "url_download": "https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx?Tela=ext",
    }
    base.update(campos)
    return base


class TestCensuraPublica:
    def test_instanciacao_com_campos_obrigatorios(self):
        censura = CensuraPublica(
            titulo="FII TORDE EI",
            ticker="TORD",
            data="25/02/2026",
            conteudo="A B3 vem a público censurar a VÓRTIX.",
        )
        assert censura.titulo == "FII TORDE EI"
        assert censura.ticker == "TORD"
        assert censura.data == "25/02/2026"
        assert "VÓRTIX" in censura.conteudo

    def test_ticker_opcional(self):
        censura = CensuraPublica(
            titulo="Censura sem ticker",
            ticker=None,
            data="25/02/2026",
            conteudo="Conteúdo.",
        )
        assert censura.ticker is None

    def test_to_text_contem_ticker_e_conteudo(self):
        censura = CensuraPublica(
            titulo="FII TORDE EI",
            ticker="TORD",
            data="25/02/2026",
            conteudo="A B3 vem a público censurar.",
        )
        texto = censura.to_text()
        assert "TORD" in texto
        assert "25/02/2026" in texto
        assert "censurar" in texto


class TestCondicaoExcepcional:
    def test_instanciacao_com_campos_de_tabela(self):
        condicao = CondicaoExcepcional(
            companhia="Bradsaúde S.A.",
            segmento="Novo Mercado",
            condicao="Percentual Mínimo de Ações em Circulação abaixo do requerido",
            data_concessao="19/05/2026",
            prazo="30/10/2027",
        )
        assert condicao.companhia == "Bradsaúde S.A."
        assert condicao.segmento == "Novo Mercado"
        assert condicao.data_concessao == "19/05/2026"
        assert condicao.prazo == "30/10/2027"

    def test_campos_opcionais_como_none(self):
        condicao = CondicaoExcepcional(
            companhia="Companhia A",
            segmento=None,
            condicao="Condição",
            data_concessao=None,
            prazo=None,
        )
        assert condicao.segmento is None
        assert condicao.data_concessao is None
        assert condicao.prazo is None

    def test_to_text_inclui_dados(self):
        condicao = CondicaoExcepcional(
            companhia="Bradsaúde S.A.",
            segmento="Novo Mercado",
            condicao="Ações em circulação abaixo do requerido",
            data_concessao="19/05/2026",
            prazo="30/10/2027",
        )
        texto = condicao.to_text()
        assert "Bradsaúde" in texto
        assert "Novo Mercado" in texto
        assert "19/05/2026" in texto
        assert "30/10/2027" in texto


class TestProgramaAquisicao:
    def test_to_text_inclui_dados(self):
        programa = ProgramaAquisicao(
            empresa="3TENTOS (NM)",
            data_aprovacao="13/08/2026",
            data_inicio="13/08/2026",
            data_fim="13/02/2028",
            quantidade="5.000.000 (ON)",
            intermediarios="Bradesco",
        )
        texto = programa.to_text()
        assert "3TENTOS (NM)" in texto
        assert "5.000.000 (ON)" in texto
        assert "13/08/2026" in texto

    def test_to_dict(self):
        programa = ProgramaAquisicao(
            empresa="3TENTOS (NM)",
            data_aprovacao=None,
            data_inicio="13/08/2026",
            data_fim="13/02/2028",
            quantidade=None,
            intermediarios=None,
        )
        dicionario = programa.to_dict()
        assert dicionario["empresa"] == "3TENTOS (NM)"
        assert dicionario["dataAprovacao"] is None
        assert dicionario["dataFim"] == "13/02/2028"


class TestNoticiaB3:
    def test_instanciacao(self):
        noticia = NoticiaB3(
            titulo="B3 divulga resultado",
            data_publicacao="2026-07-28",
            url="https://sistemasweb.b3.com.br/noticia/1",
            agencia="18",
        )
        assert noticia.titulo == "B3 divulga resultado"
        assert noticia.data_publicacao == "2026-07-28"
        assert noticia.agencia == "18"

    def test_url_opcional(self):
        noticia = NoticiaB3(
            titulo="Sem link",
            data_publicacao="2026-07-28",
            url=None,
            agencia="18",
        )
        assert noticia.url is None

    def test_to_text_contem_titulo_e_data(self):
        noticia = NoticiaB3(
            titulo="B3 divulga resultado",
            data_publicacao="2026-07-28",
            url="https://x",
            agencia="18",
        )
        texto = noticia.to_text()
        assert "B3 divulga resultado" in texto
        assert "2026-07-28" in texto


class TestDocumentoMaterialFact:
    def test_fato_relevante_eh_subclasse(self):
        assert issubclass(FatoRelevante, DocumentoMaterialFact)
        assert issubclass(Assembleia, DocumentoMaterialFact)
        assert issubclass(AvisoAcionista, DocumentoMaterialFact)
        assert issubclass(AvisoDebenturista, DocumentoMaterialFact)

    def test_fato_relevante_to_text_contextualizado(self):
        fato = FatoRelevante(**_material_fact())
        texto = fato.to_text()
        assert "Fato Relevante" in texto
        assert "PETR4" in texto
        assert "16/04/2026" in texto
        assert "Fatos Relevantes" in texto
        assert "Tomada de Contas" in texto

    def test_assembleia_to_text_inclui_tipo_e_especie(self):
        assembleia = Assembleia(
            **_material_fact(
                categoria="Assembleia",
                tipo="AGO",
                especie="Ata",
                tipo_assembleia="AGO",
                especie_documento="Ata",
            )
        )
        texto = assembleia.to_text()
        assert "Assembleia" in texto
        assert "AGO" in texto
        assert "Ata" in texto

    def test_avisos_to_text_rotulam_tipo(self):
        aviso_acionista = AvisoAcionista(**_material_fact())
        aviso_debenturista = AvisoDebenturista(**_material_fact())
        assert "Aviso ao Acionista" in aviso_acionista.to_text()
        assert "Aviso ao Debenturista" in aviso_debenturista.to_text()

    def test_documento_base_to_text_generico(self):
        documento = DocumentoMaterialFact(**_material_fact())
        assert "Documento" in documento.to_text()
        assert "PETR4" in documento.to_text()

    def test_to_dict_contem_campos_da_api(self):
        fato = FatoRelevante(**_material_fact())
        dados = fato.to_dict()
        assert dados["codeCVM"] == "9512"
        assert dados["companyName"] == "PETROLEO BRASILEIRO S.A. PETROBRAS"
        assert dados["ticker"] == "PETR4"
        assert dados["assunto"] == "Tomada de Contas-Votação do Relatório da Administração"
