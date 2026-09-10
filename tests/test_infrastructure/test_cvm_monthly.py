import io
import json
import zipfile
from datetime import date, timedelta
from decimal import Decimal

import pytest

from flowscope.domain.b3 import B3Fund
from flowscope.domain.cvm import FundIdentity, normalizar_cnpj
from flowscope.domain.fii.analysis import PatrimonioFii
from flowscope.infrastructure.conditional_cache import (
    RevalidationResult,
    RevalidationStatus,
)
from flowscope.infrastructure.cvm.downloader import (
    CvmMonthlyDownloader,
    hash_sha256,
)
from flowscope.infrastructure.cvm.identity import resolver_identidade
from flowscope.infrastructure.cvm.patrimonio import CvmMonthlyPatrimonioSource
from flowscope.infrastructure.cvm.repository import CvmMonthlyReportRepository
from flowscope.infrastructure.cvm.schema import (
    CvmSchemaError,
    mapear_linha,
    resolver_coluna,
    tem_coluna_identidade,
    validar_schema,
)
from flowscope.infrastructure.fii.cvm import (
    FONTE_CVM,
    CvmFiiAdapter,
    parse_informe_mensal,
)

REFERENCIA = date(2026, 9, 4)
CNPJ = "28737771000185"
CNPJ_FORMATADO = "28.737.771/0001-85"

CSV_ATUAL = (
    "CNPJ_Fundo_Classe;Nome_Fundo_Classe;Tipo_Fundo_Classe;Data_Referencia;"
    "VL_PATRIM_LIQ;QT_COTA;NR_COTST;Versao;Data_Recebimento\n"
    "28.737.771/0001-85;ALIANZA;FII;2026-06-30;2900000000,00;144000000;90000;1;2026-07-10\n"
    "28.737.771/0001-85;ALIANZA;FII;2026-07-31;2942000000,00;144355726;100000;1;2026-08-10\n"
    "28.737.771/0001-85;ALIANZA;FII;2026-07-31;2943000000,00;144355726;100000;2;2026-08-20\n"
    "99.999.999/0001-91;OUTRO;FII;2026-07-31;1000,00;1000;10;1;2026-08-10\n"
)

CSV_LEGADO = (
    "CNPJ_FUNDO;DT_COMPTC;VL_PATRIM_LIQ;QUANT_COTA;NR_COTST\n"
    "28737771000185;30/06/2026;2900000000,00;144000000;90000\n"
    "28737771000185;31/07/2026;2942000000,00;144355726;100000\n"
)

CSV_COMPLEMENTO = (
    "CNPJ_Fundo_Classe;Data_Referencia;Versao;Data_Informacao_Numero_Cotistas;"
    "Total_Numero_Cotistas;Patrimonio_Liquido;Cotas_Emitidas;"
    "Valor_Patrimonial_Cotas\n"
    "28.737.771/0001-85;2026-07-01;1;2026-07-31;206111;1773014664.80;"
    "164444501;10.781842\n"
)

CSV_GERAL = (
    "CNPJ_Fundo_Classe;Data_Referencia;Versao;Quantidade_Cotas_Emitidas\n"
    "28.737.771/0001-85;2026-07-01;1;164444501\n"
)


def _zip(csvs: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as arquivo:
        for nome, conteudo in csvs.items():
            arquivo.writestr(nome, conteudo.encode("latin1"))
    return buffer.getvalue()


def _downloader(tmp_path, csvs=None, contador=None):
    def fetch(ano: int) -> bytes:
        if contador is not None:
            contador.append(ano)
        return _zip(csvs or {"inf_mensal_fii_2026.csv": CSV_ATUAL})

    return CvmMonthlyDownloader(cache_dir=tmp_path, fetch=fetch)


class TestModelos:
    def test_normalizar_cnpj(self):
        assert normalizar_cnpj(CNPJ_FORMATADO) == CNPJ
        assert normalizar_cnpj(None) == ""

    def test_fund_identity_e_monthly_report(self):
        identidade = FundIdentity(
            ticker="ALZR11",
            cnpj_fundo_classe=CNPJ,
            codigo_cvm="1",
            id_fnet="20294",
            name="Alianza",
        )
        assert identidade.cnpj_fundo_classe == CNPJ
        from flowscope.domain.cvm import MonthlyReport

        report = MonthlyReport(
            ticker="ALZR11",
            cnpj_fundo_classe=CNPJ,
            reference_date=REFERENCIA,
            raw_rows={},
            source_file="x.csv",
            source_hash="abc",
        )
        assert report.is_latest is True


class TestSchema:
    def test_resolve_colunas_atuais(self):
        colunas = CSV_ATUAL.splitlines()[0].split(";")
        assert resolver_coluna(colunas, "cnpj") == "CNPJ_Fundo_Classe"
        assert resolver_coluna(colunas, "cotas") == "QT_COTA"

    def test_resolve_colunas_legadas(self):
        colunas = CSV_LEGADO.splitlines()[0].split(";")
        assert resolver_coluna(colunas, "cnpj") == "CNPJ_FUNDO"
        assert resolver_coluna(colunas, "cotas") == "QUANT_COTA"

    def test_colunas_obrigatorias_ausentes(self):
        with pytest.raises(CvmSchemaError):
            validar_schema({"CNPJ_FUNDO", "VL_PATRIM_LIQ"})

    def test_tem_coluna_identidade(self):
        assert tem_coluna_identidade({"CNPJ_Fundo_Classe", "X"}) is True
        assert tem_coluna_identidade({"Outra"}) is False

    def test_mapear_linha(self):
        colunas = CSV_LEGADO.splitlines()[0].split(";")
        linha = dict(zip(colunas, ["28737771000185", "31/07/2026", "1,00", "2", "3"]))
        canonica = mapear_linha(linha, colunas)
        assert canonica["cnpj"] == "28737771000185"
        assert canonica["cotas"] == "2"
        assert canonica["cotistas"] == "3"


class TestDownloader:
    def test_extrai_todos_os_csvs(self, tmp_path):
        data = _zip(
            {"a.csv": CSV_ATUAL, "b.csv": CSV_LEGADO, "leia.txt": "x"}
        )
        downloader = CvmMonthlyDownloader(cache_dir=tmp_path)
        csvs = downloader.extrair_csvs(data)
        assert set(csvs) == {"a.csv", "b.csv"}

    def test_hash_e_metadados_persistidos(self, tmp_path):
        downloader = _downloader(tmp_path)
        data = downloader.baixar_ano(2026)
        diretorio = tmp_path / "2026"
        assert (diretorio / "inf_mensal_fii_2026.zip").read_bytes() == data
        digest = (diretorio / "SHA256").read_text(encoding="utf-8")
        assert digest == hash_sha256(data)
        metadata = json.loads((diretorio / "metadata.json").read_text(encoding="utf-8"))
        assert metadata["dataset"] == "FII-INF-MENSAL"
        assert metadata["sha256"] == digest

    def test_download_nao_repetido_com_cache(self, tmp_path):
        contador: list[int] = []
        downloader = _downloader(tmp_path, contador=contador)
        downloader.baixar_ano(2026)
        downloader.baixar_ano(2026)
        assert contador == [2026]


class TestRevalidacaoMonthly:
    def _downloader(self, tmp_path, respostas, probe):
        estado = {"i": 0, "chamadas": 0}

        def fetch(ano: int):
            estado["chamadas"] += 1
            resposta = respostas[min(estado["i"], len(respostas) - 1)]
            estado["i"] += 1
            return resposta

        downloader = CvmMonthlyDownloader(
            cache_dir=tmp_path,
            fetch=fetch,
            probe=lambda _ano, validators: probe(validators),
            revalidate_after=timedelta(0),
        )
        return downloader, estado

    def test_fonte_inalterada_nao_rebaixa(self, tmp_path):
        downloader, estado = self._downloader(
            tmp_path, [b"v1"], lambda _v: RevalidationResult(RevalidationStatus.UNCHANGED)
        )
        assert downloader.baixar_ano(2026) == b"v1"
        assert downloader.baixar_ano(2026) == b"v1"
        assert estado["chamadas"] == 1

    def test_fonte_alterada_rebaixa(self, tmp_path):
        downloader, estado = self._downloader(
            tmp_path, [b"v1", b"v2"], lambda _v: RevalidationResult(RevalidationStatus.CHANGED)
        )
        assert downloader.baixar_ano(2026) == b"v1"
        assert downloader.baixar_ano(2026) == b"v2"
        assert estado["chamadas"] == 2

    def test_probe_falha_usa_local(self, tmp_path):
        def probe(_v):
            raise RuntimeError("rede fora")

        downloader, estado = self._downloader(tmp_path, [b"v1"], probe)
        downloader.baixar_ano(2026)
        assert downloader.baixar_ano(2026) == b"v1"
        assert estado["chamadas"] == 1

    def test_metadados_registram_validadores(self, tmp_path):
        downloader = CvmMonthlyDownloader(
            cache_dir=tmp_path,
            fetch=lambda _ano: (
                b"v1",
                {"last_modified": "Wed, 09 Sep 2026 18:00:00 GMT", "etag": '"abc"'},
            ),
        )
        downloader.baixar_ano(2026)
        metadata = json.loads(
            (tmp_path / "2026" / "metadata.json").read_text(encoding="utf-8")
        )
        assert metadata["last_modified"] == "Wed, 09 Sep 2026 18:00:00 GMT"
        assert metadata["etag"] == '"abc"'
        assert "revalidated_at" in metadata


class TestNovoMesAnoCorrente:
    def test_novo_mes_refletido_apos_revalidacao(self, tmp_path):
        junho = (
            "CNPJ_Fundo_Classe;Nome_Fundo_Classe;Tipo_Fundo_Classe;Data_Referencia;"
            "VL_PATRIM_LIQ;QT_COTA;NR_COTST;Versao;Data_Recebimento\n"
            "28.737.771/0001-85;ALIANZA;FII;2026-06-30;2900000000,00;144000000;90000;1;2026-07-10\n"
        )
        julho = (
            "28.737.771/0001-85;ALIANZA;FII;2026-07-31;2942000000,00;144355726;100000;1;2026-08-10\n"
        )
        zip_v1 = _zip({"inf_mensal_fii_2026.csv": junho})
        zip_v2 = _zip({"inf_mensal_fii_2026.csv": junho + julho})
        por_ano = {2026: [zip_v1, zip_v2], 2025: [zip_v1, zip_v1]}
        contadores: dict[int, int] = {}

        def fetch(ano: int) -> bytes:
            indice = contadores.get(ano, 0)
            contadores[ano] = indice + 1
            respostas = por_ano.get(ano, [zip_v1])
            return respostas[min(indice, len(respostas) - 1)]

        downloader = CvmMonthlyDownloader(
            cache_dir=tmp_path,
            fetch=fetch,
            probe=lambda _ano, _v: RevalidationResult(RevalidationStatus.CHANGED),
            revalidate_after=timedelta(0),
        )
        repo = CvmMonthlyReportRepository(downloader=downloader)
        primeiro = repo.get(CNPJ, REFERENCIA)
        assert primeiro.reference_date == date(2026, 6, 30)
        segundo = repo.get(CNPJ, REFERENCIA)
        assert segundo.reference_date == date(2026, 7, 31)


class TestRepository:
    def test_seleciona_competencia_mais_recente(self, tmp_path):
        repo = CvmMonthlyReportRepository(downloader=_downloader(tmp_path))
        report = repo.get(CNPJ, REFERENCIA, ticker="ALZR11")
        assert report is not None
        assert report.reference_date == date(2026, 7, 31)
        assert report.cnpj_fundo_classe == CNPJ

    def test_seleciona_reapresentacao_mais_recente(self, tmp_path):
        repo = CvmMonthlyReportRepository(downloader=_downloader(tmp_path))
        report = repo.get(CNPJ, REFERENCIA, ticker="ALZR11")
        assert report.source_version == "2"
        assert report.raw_rows["patrimonio"] == "2943000000,00"
        assert report.is_latest is True

    def test_fundo_ausente_retorna_none(self, tmp_path):
        repo = CvmMonthlyReportRepository(downloader=_downloader(tmp_path))
        assert repo.get("00000000000000", REFERENCIA) is None

    def test_ignora_competencia_futura(self, tmp_path):
        repo = CvmMonthlyReportRepository(downloader=_downloader(tmp_path))
        report = repo.get(CNPJ, date(2026, 6, 30))
        assert report.reference_date == date(2026, 6, 30)

    def test_schema_legado_reconhecido(self, tmp_path):
        downloader = _downloader(tmp_path, csvs={"inf_mensal_fii_2026.csv": CSV_LEGADO})
        repo = CvmMonthlyReportRepository(downloader=downloader)
        report = repo.get(CNPJ, REFERENCIA)
        assert report is not None
        assert report.raw_rows["cotas"] == "144355726"


class _FundoRepo:
    def __init__(self, fund):
        self._fund = fund

    def find_by_ticker(self, ticker):
        return self._fund


class TestIdentity:
    def test_identidade_resolvida(self):
        fund = B3Fund(
            ticker="ALZR11",
            fnet_id="20294",
            primary_id="870",
            name="Alianza",
            trading_name=CNPJ_FORMATADO,
        )
        identidade = resolver_identidade(
            "ALZR11",
            fund_repository=_FundoRepo(fund),
            code_cvm_resolver=lambda _t: "1234",
        )
        assert identidade is not None
        assert identidade.cnpj_fundo_classe == CNPJ
        assert identidade.id_fnet == "20294"
        assert identidade.codigo_cvm == "1234"

    def test_ticker_sem_cnpj_retorna_none(self):
        fund = B3Fund(
            ticker="XPTO11",
            fnet_id="1",
            primary_id=None,
            name="X",
            trading_name=None,
        )
        assert resolver_identidade("XPTO11", fund_repository=_FundoRepo(fund)) is None

    def test_ticker_sem_fundo_retorna_none(self):
        assert resolver_identidade("XPTO11", fund_repository=_FundoRepo(None)) is None


class TestPatrimonio:
    def test_patrimonio_normalizado(self, tmp_path):
        repo = CvmMonthlyReportRepository(downloader=_downloader(tmp_path))
        source = CvmMonthlyPatrimonioSource(
            repository=repo,
            resolver=lambda _t: FundIdentity(
                ticker="ALZR11", cnpj_fundo_classe=CNPJ
            ),
        )
        patrimonio = source.patrimonio("ALZR11", REFERENCIA)
        assert isinstance(patrimonio, PatrimonioFii)
        assert patrimonio.net_asset_value == Decimal("2943000000.00")
        assert patrimonio.shares_outstanding == Decimal("144355726")
        assert patrimonio.cotistas == 100000
        assert patrimonio.reference_date == date(2026, 7, 31)
        assert patrimonio.fonte == FONTE_CVM

    def test_sem_identidade_retorna_none(self, tmp_path):
        repo = CvmMonthlyReportRepository(downloader=_downloader(tmp_path))
        source = CvmMonthlyPatrimonioSource(repository=repo, resolver=lambda _t: None)
        assert source.patrimonio("ALZR11", REFERENCIA) is None


class TestAdapterDelegacao:
    def test_cvm_fii_adapter_delega_ao_repositorio(self, tmp_path):
        repo = CvmMonthlyReportRepository(downloader=_downloader(tmp_path))
        adapter = CvmFiiAdapter(repository=repo, resolver_cnpj=lambda _t: CNPJ)
        patrimonio = adapter.patrimonio("ALZR11", REFERENCIA)
        assert isinstance(patrimonio, PatrimonioFii)
        assert patrimonio.net_asset_value == Decimal("2943000000.00")

    def test_parse_informe_legado_continua_funcionando(self):
        informes = parse_informe_mensal(CSV_LEGADO)
        assert len(informes) == 2
        assert informes[0].cnpj == CNPJ


class TestIntegracaoRepositorio:
    def _source(self, tmp_path):
        repo = CvmMonthlyReportRepository(downloader=_downloader(tmp_path))
        return CvmMonthlyPatrimonioSource(
            repository=repo,
            resolver=lambda _t: FundIdentity(
                ticker="ALZR11", cnpj_fundo_classe=CNPJ
            ),
        )

    def test_fundamental_repository_usa_fonte_cvm(self, tmp_path):
        from flowscope.infrastructure.fii.fundamental_repository import (
            FundamentalRepository,
        )

        class _ProventosVazio:
            def execute(self, *args, **kwargs):
                return []

        fundamental = FundamentalRepository(
            proventos_use_case=_ProventosVazio(),
            patrimonio_source=self._source(tmp_path),
        )
        patrimonio = fundamental.obter_patrimonio("ALZR11", REFERENCIA)
        assert patrimonio is not None
        assert patrimonio.fonte == FONTE_CVM
        assert patrimonio.net_asset_value == Decimal("2943000000.00")

    def test_b3_fundamental_repository_usa_fonte_cvm(self, tmp_path):
        from flowscope.infrastructure.fii.b3_fundamental_repository import (
            B3FundamentalRepository,
        )

        class _RelatoriosSemInforme:
            def extrair_proventos(self, *args, **kwargs):
                return []

        repositorio = B3FundamentalRepository(
            reports_repository=_RelatoriosSemInforme(),
            patrimonio_source=self._source(tmp_path),
        )
        patrimonio = repositorio.obter_patrimonio("ALZR11", REFERENCIA)
        assert patrimonio is not None
        assert patrimonio.fonte == FONTE_CVM
        assert patrimonio.shares_outstanding == Decimal("144355726")


class TestLayoutComplemento:
    def _downloader(self, tmp_path, csvs):
        def fetch(ano):
            return _zip(csvs)

        return CvmMonthlyDownloader(cache_dir=tmp_path, fetch=fetch)

    def test_complemento_alimenta_patrimonio(self, tmp_path):
        downloader = self._downloader(
            tmp_path,
            {
                "inf_mensal_fii_complemento_2026.csv": CSV_COMPLEMENTO,
                "inf_mensal_fii_geral_2026.csv": CSV_GERAL,
            },
        )
        repo = CvmMonthlyReportRepository(downloader=downloader)
        report = repo.get(CNPJ, REFERENCIA, ticker="ALZR11")
        assert report is not None
        assert report.raw_rows["patrimonio"] == "1773014664.80"
        assert report.raw_rows["cotas"] == "164444501"
        assert report.raw_rows["cotistas"] == "206111"
        assert report.raw_rows["vp_cota"] == "10.781842"

    def test_complemento_normaliza_cotistas_e_vp_cota(self, tmp_path):
        downloader = self._downloader(
            tmp_path, {"inf_mensal_fii_complemento_2026.csv": CSV_COMPLEMENTO}
        )
        source = CvmMonthlyPatrimonioSource(
            repository=CvmMonthlyReportRepository(downloader=downloader),
            resolver=lambda _t: FundIdentity(
                ticker="ALZR11", cnpj_fundo_classe=CNPJ
            ),
        )
        patrimonio = source.patrimonio("ALZR11", REFERENCIA)
        assert patrimonio is not None
        assert patrimonio.cotistas == 206111
        assert patrimonio.net_asset_value == Decimal("1773014664.80")
        assert patrimonio.shares_outstanding == Decimal(164444501)
        assert patrimonio.vp_cota == Decimal("10.781842")
        assert patrimonio.fonte == FONTE_CVM

    def test_geral_sem_patrimonio_e_ignorado(self, tmp_path):
        downloader = self._downloader(
            tmp_path, {"inf_mensal_fii_geral_2026.csv": CSV_GERAL}
        )
        repo = CvmMonthlyReportRepository(downloader=downloader)
        assert repo.get(CNPJ, REFERENCIA) is None
