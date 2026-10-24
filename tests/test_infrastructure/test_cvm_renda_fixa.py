"""Testes dos parsers e do join dos datasets CVM de renda fixa."""

from datetime import date
from decimal import Decimal

import pytest

from flowscope.domain.renda_fixa import PapelTitulo, TipoTitulo, TituloAgregado
from flowscope.infrastructure.cvm.renda_fixa_fii import (
    parse_fii_ativo,
    parse_fii_ativo_passivo,
)
from flowscope.infrastructure.cvm.renda_fixa_fre import parse_fre
from flowscope.infrastructure.cvm.renda_fixa_join import enriquecer, indice_securit
from flowscope.infrastructure.cvm.renda_fixa_securit import parse_securit_csvs

CNPJ_PETR = "33000167000101"
CNPJ_SECURITIZADORA = "09346601000125"
CNPJ_FII = "11444777000161"


def _csv(cabecalho: list[str], linhas: list[list[str]]) -> bytes:
    return (";".join(cabecalho) + "\n" + "\n".join(
        ";".join(linha) for linha in linhas
    ) + "\n").encode("latin1")


def _fre(linhas: list[list[str]]) -> bytes:
    cabecalho = [
        "CNPJ_Companhia",
        "Valor_Mobiliario",
        "Identificacao_Valor_Mobiliario",
        "Data_Emissao",
        "Data_Vencimento",
        "Quantidade",
        "Valor",
        "Saldo_Devedor",
        "Serie",
        "Indexador",
        "Taxa",
        "Caracteristicas_Divida",
        "Restricao_Circulacao",
        "Condicao_Alteracao_Direitos",
        "Data_Referencia",
        "Versao",
    ]
    return _csv(cabecalho, linhas)


def _linha_fre(
    valor_mobiliario: str = "Debêntures",
    identificacao: str = "PETR27",
    referencia: str = "2026-06-30",
    versao: str = "1",
    valor: str = "1000,00",
) -> list[str]:
    return [
        CNPJ_PETR,
        valor_mobiliario,
        identificacao,
        "2020-01-01",
        "2030-01-01",
        "1000",
        valor,
        "900,00",
        "1",
        "IPCA",
        "5,5",
        "Quirografária",
        "Livre",
        "Assembleia",
        referencia,
        versao,
    ]


class TestFre:
    def test_extrai_debentures_com_versao_mais_recente(self):
        conteudo = _fre(
            [
                _linha_fre(versao="1", referencia="2026-03-31", valor="900,00"),
                _linha_fre(versao="2", referencia="2026-06-30", valor="1000,00"),
            ]
        )
        titulos = parse_fre(conteudo, CNPJ_PETR, "fre.csv", "hash")
        assert len(titulos) == 1
        titulo = titulos[0]
        assert titulo.tipo is TipoTitulo.DEBENTURE
        assert titulo.papel is PapelTitulo.OBRIGACAO
        assert titulo.valor == Decimal("1000.00")
        assert titulo.data_referencia == date(2026, 6, 30)
        assert titulo.arquivo == "fre.csv"
        assert titulo.hash_fonte == "hash"

    def test_cri_e_cra_com_devedor_e_fora_do_escopo(self):
        conteudo = _fre(
            [
                _linha_fre(
                    valor_mobiliario="Certificados de Recebíveis Imobiliários",
                    identificacao="CRI1",
                ),
                _linha_fre(
                    valor_mobiliario="Certificado de Recebíveis do Agronegócio",
                    identificacao="CRA1",
                ),
                _linha_fre(valor_mobiliario="Ações", identificacao="ACAO"),
                _linha_fre(valor_mobiliario="Bônus de Subscrição", identificacao="BONUS"),
            ]
        )
        titulos = parse_fre(conteudo, CNPJ_PETR)
        assert {item.tipo for item in titulos} == {TipoTitulo.CRI, TipoTitulo.CRA}
        assert all(item.cnpj_devedor == CNPJ_PETR for item in titulos)


def _securit_csvs() -> dict[str, bytes]:
    return {
        "inf_mensal_cri_geral_2026.csv": _csv(
            [
                "CNPJ_Emissora",
                "Nome_Emissor",
                "Codigo_Identificacao_Certificado",
                "Codigo_CETIP",
                "Codigo_ISIN",
                "Serie",
                "Data_Emissao",
                "Data_Vencimento",
                "Situacao",
                "Data_Referencia",
                "Versao",
            ],
            [
                [
                    CNPJ_SECURITIZADORA,
                    "SECURITIZADORA",
                    "CRI-CERT",
                    "18K0669354",
                    "BRCRI123",
                    "1",
                    "2024-01-01",
                    "2030-01-01",
                    "Adimplente",
                    "2026-06-30",
                    "1",
                ]
            ],
        ),
        "inf_mensal_cri_classe_2026.csv": _csv(
            ["Codigo_CETIP", "Garantias", "Coobrigacao", "Subordinacao"],
            [["18K0669354", "Alienação fiduciária", "Não", "Sim"]],
        ),
        "inf_mensal_cri_cedente_devedor_2026.csv": _csv(
            ["Codigo_CETIP", "Tipo", "CNPJ_Devedor", "Nome_Devedor"],
            [["18K0669354", "Devedor", CNPJ_PETR, "PETROBRAS"]],
        ),
        "inf_mensal_cri_creditos_2026.csv": _csv(
            ["Codigo_CETIP", "Contingencias", "Impacto", "Desempenho"],
            [["18K0669354", "Nenhuma", "Baixo", "Estável"]],
        ),
        "inf_mensal_cri_ativo_passivo_2026.csv": _csv(
            ["Codigo_CETIP", "Indice_LTV", "Data_LTV"],
            [["18K0669354", "75,5", "2026-06-30"]],
        ),
        "inf_mensal_cri_carteira_2026.csv": _csv(
            ["Codigo_CETIP", "Lastro", "Sobrecolateralizacao"],
            [["18K0669354", "CRI lastro", "10"]],
        ),
    }


class TestSecurit:
    def test_normaliza_campos_e_ltv(self):
        titulos = parse_securit_csvs(_securit_csvs(), TipoTitulo.CRI)
        assert len(titulos) == 1
        titulo = titulos[0]
        assert titulo.emissor_legal == "SECURITIZADORA"
        assert titulo.cnpj_devedor == CNPJ_PETR
        assert titulo.devedor == "PETROBRAS"
        assert titulo.garantias == "Alienação fiduciária"
        assert titulo.ltv == Decimal("75.5")
        assert titulo.data_ltv == date(2026, 6, 30)
        assert titulo.situacao == "Adimplente"

    def test_linha_invalida_nao_gera_titulo(self):
        csvs = {
            "inf_mensal_cri_geral_2026.csv": _csv(
                ["CNPJ_Emissora", "Codigo_Identificacao_Certificado"],
                [["invalido", "X"]],
            )
        }
        assert parse_securit_csvs(csvs, TipoTitulo.CRI) == []

    def test_join_por_codigo_e_por_devedor(self):
        securit = parse_securit_csvs(_securit_csvs(), TipoTitulo.CRI)
        indice = indice_securit(securit)
        por_codigo = parse_fre(
            _fre([_linha_fre(
                valor_mobiliario="Certificados de Recebíveis Imobiliários",
                identificacao="18K0669354",
            )]),
            CNPJ_PETR,
        )[0]
        enriquecido = enriquecer(por_codigo, indice)
        assert enriquecido.ltv == Decimal("75.5")
        sem_codigo = parse_fre(
            _fre([_linha_fre(
                valor_mobiliario="Certificados de Recebíveis Imobiliários",
                identificacao="OUTRO",
            )]),
            CNPJ_PETR,
        )[0]
        por_devedor = enriquecer(sem_codigo, indice)
        assert por_devedor.garantias == "Alienação fiduciária"

    def test_join_sem_correspondencia_nao_inventa_ltv(self):
        titulo = parse_fre(
            _fre([_linha_fre(
                valor_mobiliario="Certificados de Recebíveis Imobiliários",
                identificacao="OUTRO",
            )]),
            CNPJ_PETR,
        )[0]
        enriquecido = enriquecer(titulo, {})
        assert enriquecido.ltv is None

    def test_cra_e_debenture_nao_recebem_ltv(self):
        securit = parse_securit_csvs(_securit_csvs(), TipoTitulo.CRI)
        indice = indice_securit(securit)
        debenture = parse_fre(_fre([_linha_fre()]), CNPJ_PETR)[0]
        assert enriquecer(debenture, indice).ltv is None

    def test_filtro_por_codigo_materializa_apenas_o_titulo(self):
        titulos = parse_securit_csvs(
            _securit_csvs(),
            TipoTitulo.CRI,
            codigos_alvo={"18K0669354"},
        )
        assert len(titulos) == 1
        assert titulos[0].identificacao == "CRI-CERT"

    def test_filtro_sem_correspondencia_nao_materializa_nada(self):
        assert (
            parse_securit_csvs(
                _securit_csvs(),
                TipoTitulo.CRI,
                codigos_alvo={"NAOEXISTE"},
            )
            == []
        )

    def test_filtro_respeita_cancelamento(self):
        def cancelar() -> None:
            raise RuntimeError("cancelado")

        with pytest.raises(RuntimeError, match="cancelado"):
            parse_securit_csvs(
                _securit_csvs(),
                TipoTitulo.CRI,
                codigos_alvo={"18K0669354"},
                cancelar=cancelar,
            )


def _fii_ativo(linhas: list[list[str]]) -> bytes:
    return _csv(
        [
            "CNPJ_Fundo_Classe",
            "Tipo_Ativo",
            "Emissor",
            "CNPJ_Emissor",
            "Emissao",
            "Serie",
            "Codigo_CETIP",
            "Nome_Ativo",
            "Data_Vencimento",
            "Quantidade",
            "Valor",
            "Data_Referencia",
            "Versao",
        ],
        linhas,
    )


class TestFii:
    def test_emissor_sem_codigo_nao_vira_codigo_cetip(self):
        conteudo = _fii_ativo(
            [
                [
                    CNPJ_FII,
                    "CRI/CRA",
                    "CANAL COMPANHIA DE SECURITIZACAO",
                    CNPJ_SECURITIZADORA,
                    "0",
                    "1",
                    "",
                    "CRI CANAL",
                    "2030-01-01",
                    "10",
                    "100,00",
                    "2026-03-31",
                    "1",
                ]
            ]
        )
        direitos = parse_fii_ativo(conteudo, CNPJ_FII)
        assert len(direitos) == 1
        assert direitos[0].codigos == ()

    def test_codigo_embutido_no_emissor_e_extraido(self):
        conteudo = _fii_ativo(
            [
                [
                    CNPJ_FII,
                    "CRI/CRA",
                    "GAIA SECURITIZADORA S.A. - 12E0031967",
                    CNPJ_SECURITIZADORA,
                    "4",
                    "33",
                    "",
                    "CRI GAIA",
                    "2030-01-01",
                    "10",
                    "100,00",
                    "2026-03-31",
                    "1",
                ]
            ]
        )
        direitos = parse_fii_ativo(conteudo, CNPJ_FII)
        assert direitos[0].codigos == ("12E0031967",)

    def test_codigo_que_aparece_na_versao_nova_nao_duplica_posicao(self):
        conteudo = _fii_ativo(
            [
                [
                    CNPJ_FII,
                    "CRI",
                    "GAIA SECURITIZADORA S.A.",
                    CNPJ_SECURITIZADORA,
                    "4",
                    "33",
                    "",
                    "CRI GAIA",
                    "2030-01-01",
                    "10",
                    "100,00",
                    "2025-12-31",
                    "1",
                ],
                [
                    CNPJ_FII,
                    "CRI",
                    "GAIA SECURITIZADORA S.A. - 12E0031967",
                    CNPJ_SECURITIZADORA,
                    "4",
                    "33",
                    "",
                    "CRI GAIA",
                    "2030-01-01",
                    "10",
                    "100,00",
                    "2026-03-31",
                    "1",
                ],
            ]
        )
        direitos = parse_fii_ativo(conteudo, CNPJ_FII)
        assert len(direitos) == 1
        assert direitos[0].codigos == ("12E0031967",)
        assert direitos[0].data_referencia == date(2026, 3, 31)

    def test_carteira_trimestral_por_titulo(self):
        conteudo = _fii_ativo(
            [
                [
                    CNPJ_FII,
                    "CRI",
                    "18K0669354",
                    CNPJ_SECURITIZADORA,
                    "1",
                    "1",
                    "18K0669354",
                    "CRI ALZR",
                    "2030-01-01",
                    "10",
                    "100,00",
                    "2026-03-31",
                    "1",
                ],
                [
                    CNPJ_FII,
                    "LCI",
                    "EMISSOR",
                    CNPJ_SECURITIZADORA,
                    "2",
                    "2",
                    "",
                    "LCI ALZR",
                    "2028-01-01",
                    "5",
                    "50,00",
                    "2026-03-31",
                    "1",
                ],
                [
                    CNPJ_FII,
                    "Ações",
                    "XPTO",
                    "",
                    "",
                    "",
                    "",
                    "Ação",
                    "",
                    "",
                    "",
                    "2026-03-31",
                    "1",
                ],
            ]
        )
        direitos = parse_fii_ativo(conteudo, CNPJ_FII)
        assert {item.tipo for item in direitos} == {
            TipoTitulo.CRI,
            TipoTitulo.LCI,
        }
        assert all(item.papel is PapelTitulo.DIREITO for item in direitos)
        assert all(item.valor is not None for item in direitos)

    def test_agregado_usa_ultima_data_sem_somar_meses(self):
        conteudo = _csv(
            [
                "CNPJ_Fundo_Classe",
                "Data_Referencia",
                "Versao",
                "Debentures",
                "Certificados_Deposito_Valores_Mobiliarios",
            ],
            [
                [CNPJ_FII, "2026-01-31", "1", "100,00", "50,00"],
                [CNPJ_FII, "2026-02-28", "1", "200,00", "80,00"],
            ],
        )
        agregados = parse_fii_ativo_passivo(conteudo, CNPJ_FII)
        valores = {item.tipo: item.valor for item in agregados}
        assert valores[TipoTitulo.DEBENTURE] == Decimal("200.00")
        assert valores[TipoTitulo.CDB] == Decimal("80.00")
        assert all(isinstance(item, TituloAgregado) for item in agregados)

    def test_sem_posicoes_retorna_vazio(self):
        conteudo = _csv(
            ["CNPJ_Fundo_Classe", "Data_Referencia", "Debentures"],
            [[CNPJ_FII, "2026-01-31", "0,00"]],
        )
        assert parse_fii_ativo_passivo(conteudo, CNPJ_FII) == []
        assert parse_fii_ativo(_fii_ativo([]), CNPJ_FII) == []


class TestDocumentosB3:
    def test_lista_categoria_48_sem_baixar_pdf(self):
        from datetime import date

        from flowscope.domain.structured import (
            CategoriaMaterialFact,
            DocumentoMaterialFact,
        )
        from flowscope.infrastructure.b3.renda_fixa_documentos import (
            listar_avisos_debenturistas,
        )

        chamadas = []

        class _Cliente:
            def resolver_code_cvm(self, ticker):
                return "9512"

            def listar_fatos_relevantes(self, *args, **kwargs):
                chamadas.append((args, kwargs))
                return [
                    DocumentoMaterialFact(
                        code_cvm="9512",
                        empresa="PETROBRAS",
                        ticker="PETR4",
                        data_referencia="2026-06-30",
                        data_entrega=None,
                        categoria="Aviso aos Debenturistas",
                        tipo=None,
                        especie=None,
                        status="Ativo",
                        assunto="Aviso",
                        url_documento="https://exemplo/aviso",
                        url_download=None,
                    )
                ]

            def baixar_pdf_documento(self, _id):
                raise AssertionError("não deve baixar PDF")

        links = listar_avisos_debenturistas(
            _Cliente(), "PETR4", date(2026, 9, 30)
        )
        assert len(links) == 1
        assert links[0].url == "https://exemplo/aviso"
        assert chamadas[0][0][1] is CategoriaMaterialFact.AVISO_DEBENTURISTAS


class TestDeduplicacaoEntreAnos:
    def test_codigo_que_aparece_depois_nao_duplica_posicao_entre_anos(self):
        from flowscope.infrastructure.cvm.renda_fixa_common import melhor_por_chave
        from flowscope.infrastructure.cvm.renda_fixa_fii import chave_posicao_fii
        from flowscope.domain.renda_fixa import TituloRendaFixa

        antigo = TituloRendaFixa(
            tipo=TipoTitulo.CRI,
            papel=PapelTitulo.DIREITO,
            id="antigo",
            chave_fonte=f"{CNPJ_SECURITIZADORA}|4|33|",
            cnpj_emissor=CNPJ_SECURITIZADORA,
            emissao="4",
            serie="33",
            data_referencia=date(2025, 12, 31),
        )
        novo = TituloRendaFixa(
            tipo=TipoTitulo.CRI,
            papel=PapelTitulo.DIREITO,
            id="novo",
            chave_fonte="12E0031967",
            identificacao="12E0031967",
            codigos=("12E0031967",),
            cnpj_emissor=CNPJ_SECURITIZADORA,
            emissao="4",
            serie="33",
            data_referencia=date(2026, 6, 30),
        )

        selecionados = melhor_por_chave(
            [antigo, novo], chave=chave_posicao_fii
        )

        assert [item.id for item in selecionados] == ["novo"]
