"""Testes da fonte CVM que seleciona e normaliza os datasets de renda fixa."""

from datetime import date

from flowscope.domain.renda_fixa import TipoTitulo
from flowscope.infrastructure.cvm.renda_fixa_fre import CSV_PREFIXO as CSV_FRE
from flowscope.infrastructure.cvm.renda_fixa_source import CvmTitulosSource

_REFERENCIA = date(2026, 9, 30)
_CNPJ = "33000167000101"
_CNPJ_FII = "11444777000161"


class _DownloaderFake:
    def __init__(self, csvs=None, falha=False, nome="dataset") -> None:
        self._csvs = csvs or {}
        self._falha = falha
        self._nome = nome
        self.anos: list[int] = []
        self.extraidos = 0

    def baixar_ano(self, ano):
        self.anos.append(ano)
        if self._falha:
            raise RuntimeError("fonte indisponível")
        return f"{self._nome}-{ano}".encode()

    def extrair_csvs(self, _data, _ano):
        self.extraidos += 1
        return dict(self._csvs)


def _csv_fre(com_cri: bool = False) -> dict[str, bytes]:
    linhas = f"{_CNPJ};Debêntures;PETR27;2026-06-30;1\n"
    if com_cri:
        linhas += (
            f"{_CNPJ};Certificados de Recebíveis Imobiliários;"
            "CRI1;2026-06-30;1\n"
        )
    conteudo = (
        "CNPJ_Companhia;Valor_Mobiliario;Identificacao_Valor_Mobiliario;"
        "Data_Referencia;Versao\n" + linhas
    ).encode("latin1")
    return {f"{CSV_FRE}_2026.csv": conteudo}


class TestFonteCvm:
    def test_companhia_usa_fre_e_securit(self):
        fre = _DownloaderFake(_csv_fre(com_cri=True), nome="fre")
        cri = _DownloaderFake(falha=True, nome="cri")
        cra = _DownloaderFake(falha=True, nome="cra")
        fii = _DownloaderFake(nome="fii")
        mensal = _DownloaderFake(nome="mensal")
        source = CvmTitulosSource(
            downloader_fre=fre,
            downloader_cri=cri,
            downloader_cra=cra,
            downloader_fii=fii,
            downloader_fii_mensal=mensal,
        )
        resultado = source.obter("PETR4", _CNPJ, "acao", _REFERENCIA)
        assert len(resultado.obrigacoes) == 2
        assert {item.tipo for item in resultado.obrigacoes} == {
            TipoTitulo.DEBENTURE,
            TipoTitulo.CRI,
        }
        assert resultado.falhas == frozenset({"SECURIT_CRI", "SECURIT_CRA"})
        assert fii.anos == []

    def test_sem_cri_cra_nao_baixa_securit(self):
        fre = _DownloaderFake(_csv_fre(), nome="fre")
        cri = _DownloaderFake(nome="cri")
        cra = _DownloaderFake(nome="cra")
        source = CvmTitulosSource(
            downloader_fre=fre,
            downloader_cri=cri,
            downloader_cra=cra,
            downloader_fii=_DownloaderFake(),
            downloader_fii_mensal=_DownloaderFake(),
        )
        resultado = source.obter("PETR4", _CNPJ, "acao", _REFERENCIA)
        assert resultado.obrigacoes
        assert cri.anos == []
        assert cra.anos == []

    def test_fii_usa_informes_e_nao_fre(self):
        fre = _DownloaderFake(_csv_fre(), nome="fre")
        fii = _DownloaderFake(nome="fii")
        mensal = _DownloaderFake(nome="mensal")
        source = CvmTitulosSource(
            downloader_fre=fre,
            downloader_cri=_DownloaderFake(nome="cri"),
            downloader_cra=_DownloaderFake(nome="cra"),
            downloader_fii=fii,
            downloader_fii_mensal=mensal,
        )
        source.obter("ALZR11", _CNPJ_FII, "fii", _REFERENCIA)
        assert fre.anos == []
        assert fii.anos == [2026, 2025]
        assert mensal.anos == [2026, 2025]

    def test_falha_de_um_dataset_nao_interrompe_os_demais(self):
        fre = _DownloaderFake(_csv_fre(com_cri=True), nome="fre")
        cri = _DownloaderFake(falha=True, nome="cri")
        source = CvmTitulosSource(
            downloader_fre=fre,
            downloader_cri=cri,
            downloader_cra=_DownloaderFake(falha=True, nome="cra"),
            downloader_fii=_DownloaderFake(),
            downloader_fii_mensal=_DownloaderFake(),
        )
        resultado = source.obter("PETR4", _CNPJ, "acao", _REFERENCIA)
        assert resultado.obrigacoes
        assert "SECURIT_CRI" in resultado.falhas

    def test_enriquecimento_desligado_nao_baixa_securit(self):
        cri = _DownloaderFake(nome="cri")
        cra = _DownloaderFake(nome="cra")
        source = CvmTitulosSource(
            downloader_fre=_DownloaderFake(
                _csv_fre(com_cri=True), nome="fre"
            ),
            downloader_cri=cri,
            downloader_cra=cra,
            downloader_fii=_DownloaderFake(),
            downloader_fii_mensal=_DownloaderFake(),
            enriquecer_securit=False,
        )
        source.obter("PETR4", _CNPJ, "acao", _REFERENCIA)
        assert cri.anos == []
        assert cra.anos == []

    def test_progresso_por_etapa(self):
        eventos = []
        source = CvmTitulosSource(
            downloader_fre=_DownloaderFake(_csv_fre(), nome="fre"),
            downloader_cri=_DownloaderFake(nome="cri"),
            downloader_cra=_DownloaderFake(nome="cra"),
            downloader_fii=_DownloaderFake(),
            downloader_fii_mensal=_DownloaderFake(),
        )
        source.obter(
            "PETR4",
            _CNPJ,
            "acao",
            _REFERENCIA,
            progress=lambda atual, total, rotulo: eventos.append(
                (atual, total, rotulo)
            ),
        )
        assert any("FRE" in rotulo for _atual, _total, rotulo in eventos)
        assert all(total == 3 for _atual, total, _rotulo in eventos)


class TestReusoDoCache:
    def test_datasets_inalterados_reutilizam_o_resultado_sem_reprocessar(self):
        from flowscope.domain.renda_fixa import PARSER_VERSION, CarteiraTitulos

        fre = _DownloaderFake(_csv_fre(), nome="fre")
        cri = _DownloaderFake(nome="cri")
        cra = _DownloaderFake(nome="cra")
        source = CvmTitulosSource(
            downloader_fre=fre,
            downloader_cri=cri,
            downloader_cra=cra,
            downloader_fii=_DownloaderFake(),
            downloader_fii_mensal=_DownloaderFake(),
        )
        primeiro = source.obter("PETR4", _CNPJ, "acao", _REFERENCIA)
        anterior = CarteiraTitulos(
            ticker="PETR4",
            parser_version=PARSER_VERSION,
            fontes=dict(primeiro.fontes),
            obrigacoes=primeiro.obrigacoes,
            direitos=primeiro.direitos,
            agregados=primeiro.agregados,
        )
        extraidos = fre.extraidos

        segundo = source.obter(
            "PETR4", _CNPJ, "acao", _REFERENCIA, anterior=anterior
        )

        assert segundo.obrigacoes == primeiro.obrigacoes
        assert segundo.fontes == primeiro.fontes
        assert fre.extraidos == extraidos
        assert cri.anos == []
        assert cra.anos == []

    def test_dataset_alterado_forca_reprocessamento(self):
        from flowscope.domain.renda_fixa import PARSER_VERSION, CarteiraTitulos

        fre = _DownloaderFake(_csv_fre(), nome="fre")
        source = CvmTitulosSource(
            downloader_fre=fre,
            downloader_cri=_DownloaderFake(nome="cri"),
            downloader_cra=_DownloaderFake(nome="cra"),
            downloader_fii=_DownloaderFake(),
            downloader_fii_mensal=_DownloaderFake(),
        )
        primeiro = source.obter("PETR4", _CNPJ, "acao", _REFERENCIA)
        anterior = CarteiraTitulos(
            ticker="PETR4",
            parser_version=PARSER_VERSION,
            fontes=dict(primeiro.fontes),
            obrigacoes=primeiro.obrigacoes,
        )
        fre._nome = "fre-novo"
        extraidos = fre.extraidos

        source.obter("PETR4", _CNPJ, "acao", _REFERENCIA, anterior=anterior)

        assert fre.extraidos > extraidos
