from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from flowscope.domain.structured import (
    CATEGORIAS_RELEVANTES,
    CNPJ,
    DocumentoProvento,
    DocumentoRelevante,
    Entidade,
    ISIN,
    Provento,
    ValorProvento,
    nome_categoria,
    nome_por_slug,
    slug_categoria,
)


def _entidade() -> Entidade:
    return Entidade(
        nome="ALIANZA TRUST RENDA IMOBILIÁRIA - FII",
        cnpj=CNPJ("28.737.771/0001-85"),
        nome_administrador="BTG PACTUAL SERVIÇOS FINANCEIROS S/A DTVM",
        cnpj_administrador=CNPJ("59.281.253/0001-23"),
        responsavel="Leandro Pereira",
        telefone="(11) 3383-3102",
    )


def _provento() -> Provento:
    return Provento(
        codigo_isin=ISIN("BRALZRCTF006"),
        codigo_negociacao="ALZR11",
        tipo="Rendimento",
        data_base=date(2026, 6, 18),
        valor_por_unidade=ValorProvento(Decimal("0.08355")),
        data_pagamento=date(2026, 6, 25),
        periodo_referencia="Maio-2026",
        isento_ir=True,
        data_informacao=date(2026, 6, 18),
        ano_referencia=2026,
        nota_isencao=(
            "A Administradora declara que o Fundo de Investimento Imobiliário se "
            "enquadra no inciso III do art. 3º da Lei 11.033/2004."
        ),
    )


class TestCNPJ:
    def test_valido(self):
        cnpj = CNPJ("28.737.771/0001-85")
        assert cnpj.value == "28.737.771/0001-85"

    def test_invalido_lanca_value_error(self):
        with pytest.raises(ValueError):
            CNPJ("123")

    def test_igualdade_por_valor(self):
        assert CNPJ("28.737.771/0001-85") == CNPJ("28.737.771/0001-85")
        assert CNPJ("28.737.771/0001-85") != CNPJ("59.281.253/0001-23")


class TestISIN:
    def test_valido(self):
        isin = ISIN("BRALZRCTF006")
        assert isin.value == "BRALZRCTF006"

    def test_normaliza_minusculas(self):
        assert ISIN("bralzrctf006").value == "BRALZRCTF006"

    def test_curto_demais_lanca_value_error(self):
        with pytest.raises(ValueError):
            ISIN("BR12345")

    def test_prefixo_invalido_lanca_value_error(self):
        with pytest.raises(ValueError):
            ISIN("USALZRCTF006")


class TestValorProvento:
    def test_aceita_string_monetaria_brasileira(self):
        valor = ValorProvento("R$ 0,08355")
        assert valor.value == Decimal("0.08355")

    def test_string_com_milhar_e_virgula(self):
        valor = ValorProvento("R$ 1.234,56")
        assert valor.value == Decimal("1234.56")

    def test_aceita_decimal(self):
        valor = ValorProvento(Decimal("1.50"))
        assert valor.value == Decimal("1.50")

    def test_aceita_string_puramente_numerica(self):
        valor = ValorProvento("1.50")
        assert valor.value == Decimal("1.50")

    def test_igualdade_por_valor(self):
        assert ValorProvento("R$ 0,08355") == ValorProvento(Decimal("0.08355"))


class TestEntidade:
    def test_campos_acessiveis(self):
        entidade = _entidade()
        assert entidade.nome.startswith("ALIANZA")
        assert entidade.cnpj.value == "28.737.771/0001-85"
        assert entidade.nome_administrador == "BTG PACTUAL SERVIÇOS FINANCEIROS S/A DTVM"
        assert entidade.cnpj_administrador.value == "59.281.253/0001-23"
        assert entidade.responsavel == "Leandro Pereira"
        assert entidade.telefone == "(11) 3383-3102"


class TestProvento:
    def test_tipo_rendimento_com_decimal(self):
        provento = _provento()
        assert provento.tipo == "Rendimento"
        assert provento.valor_por_unidade.value == Decimal("0.08355")

    def test_tipo_amortizacao(self):
        provento = Provento(
            codigo_isin=ISIN("BRALZRCTF006"),
            codigo_negociacao="ALZR11",
            tipo="Amortização",
            data_base=date(2026, 6, 18),
            valor_por_unidade=ValorProvento(Decimal("1.50")),
            data_pagamento=date(2026, 6, 25),
            periodo_referencia="Junho-2026",
            isento_ir=False,
        )
        assert provento.tipo == "Amortização"
        assert provento.valor_por_unidade.value == Decimal("1.50")


class TestDocumentoProvento:
    def test_componentes_acessiveis(self):
        doc = DocumentoProvento(
            ticker="ALZR11",
            id_fnet="20294",
            id_documento="1224160",
            url_documento="https://fnet.bmfbovespa.com.br/fnet/publico/exibirDocumento?id=1224160",
            data_extracao="2026-07-29T14:30:00-03:00",
            entidade=_entidade(),
            provento=_provento(),
        )
        assert doc.entidade.nome == _entidade().nome
        assert doc.provento.tipo == "Rendimento"
        assert doc.ticker == "ALZR11"

    def test_to_dict_contem_campos_esperados(self):
        doc = DocumentoProvento(
            ticker="ALZR11",
            id_fnet="20294",
            id_documento="1224160",
            url_documento="https://fnet.bmfbovespa.com.br/fnet/publico/exibirDocumento?id=1224160",
            data_extracao="2026-07-29T14:30:00-03:00",
            entidade=_entidade(),
            provento=_provento(),
        )
        data = doc.to_dict()
        assert data["ticker"] == "ALZR11"
        assert data["idFNET"] == "20294"
        assert data["dadosFundos"]["cnpjFundo"] == "28.737.771/0001-85"
        assert data["dadosProvento"]["tipoProvento"] == "Rendimento"
        assert data["dadosProvento"]["valorPorUnidade"] == "0.08355"
        assert data["dadosProvento"]["isentoIR"] is True
        assert data["dadosInformacao"]["anoReferencia"] == 2026

    def test_to_text_contem_campos_esperados(self):
        doc = DocumentoProvento(
            ticker="ALZR11",
            id_fnet="20294",
            id_documento="1224160",
            url_documento="https://fnet.bmfbovespa.com.br/fnet/publico/exibirDocumento?id=1224160",
            data_extracao="2026-07-29T14:30:00-03:00",
            entidade=_entidade(),
            provento=_provento(),
        )
        texto = doc.to_text()
        assert "ALIANZA" in texto
        assert "28.737.771/0001-85" in texto
        assert "ALZR11" in texto
        assert "Rendimento" in texto
        assert "0.08355" in texto
        assert "2026-06-18" in texto
        assert "Isento de IR: Sim" in texto
        assert "Lei 11.033/2004" in texto


class TestDocumentoRelevante:
    def _documento(self) -> DocumentoRelevante:
        return DocumentoRelevante(
            ticker="ALZR11",
            id_fnet="20294",
            id_documento="1252542",
            categoria="Assembleia",
            descricao="Ata de Assembleia Geral Ordinária",
            data_referencia=date(2026, 7, 17),
            data_entrega="17/07/2026",
            url=(
                "https://fnet.bmfbovespa.com.br/fnet/publico/"
                "visualizarDocumento?id=1252542"
            ),
            tamanho_bytes=245760,
            data_extracao=datetime(2026, 7, 29, 14, 30, tzinfo=timezone.utc),
        )

    def test_metadados_acessiveis(self):
        doc = self._documento()
        assert doc.ticker == "ALZR11"
        assert doc.id_fnet == "20294"
        assert doc.id_documento == "1252542"
        assert doc.categoria == "Assembleia"
        assert doc.descricao == "Ata de Assembleia Geral Ordinária"
        assert doc.data_referencia == date(2026, 7, 17)
        assert doc.data_entrega == "17/07/2026"
        assert doc.tamanho_bytes == 245760
        assert doc.data_extracao == datetime(
            2026, 7, 29, 14, 30, tzinfo=timezone.utc
        )

    def test_sem_texto_extraido(self):
        doc = self._documento()
        assert not hasattr(doc, "texto_extraido")
        assert not hasattr(doc, "to_text")


class TestCategoriasRelevantes:
    def test_codigos_na_ordem(self):
        assert CATEGORIAS_RELEVANTES == (1, 2, 3, 7)

    def test_nome_e_slug_por_codigo(self):
        esperado = {
            1: ("Fato Relevante", "fato-relevante"),
            2: ("Assembleia", "assembleia"),
            3: ("Comunicado ao Mercado", "comunicado"),
            7: ("Relatorio", "relatorio"),
        }
        for codigo, (nome, slug) in esperado.items():
            assert nome_categoria(codigo) == nome
            assert nome_categoria(str(codigo)) == nome
            assert slug_categoria(codigo) == slug
            assert slug_categoria(str(codigo)) == slug

    def test_nome_por_slug(self):
        assert nome_por_slug("fato-relevante") == "Fato Relevante"
        assert nome_por_slug("relatorio") == "Relatorio"
        assert nome_por_slug("desconhecido") is None
