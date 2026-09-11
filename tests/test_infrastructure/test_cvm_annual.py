import io
import json
import zipfile
from datetime import date

from flowscope.infrastructure.cvm.annual import (
    SOURCE_SCHEMA_VERSION,
    CvmAnnualRepository,
)
from flowscope.infrastructure.cvm.datasets import CvmDatasetDownloader

REFERENCIA = date(2026, 9, 4)
CNPJ = "36501233000115"

CSV_GERAL = (
    "Tipo_Fundo_Classe;CNPJ_Fundo_Classe;Data_Referencia;Versao;"
    "Nome_Administrador;CNPJ_Administrador\n"
    "Classe;36.501.233/0001-15;2025-12-31;1;BANCO GENIAL S.A.;45.246.410/0001-55\n"
    "Classe;36.501.233/0001-15;2024-12-31;1;ADMIN ANTIGO;11.111.111/0001-11\n"
    "Classe;99.999.999/0001-91;2025-12-31;1;OUTRO;22.222.222/0001-22\n"
)

CSV_COMPLEMENTO = (
    "CNPJ_Fundo_Classe;Data_Referencia;Versao;Nome_Gestor;CNPJ_Gestor;"
    "Nome_Custodiante;CNPJ_Custodiante;Nome_Auditor_Independente;"
    "CNPJ_Auditor_Independente\n"
    "36.501.233/0001-15;2025-12-31;1;CY.CAPITAL GESTORA DE RECURSOS LTDA;"
    "18.596.891/0001-56;BANCO GENIAL;45.246.410/0001-55;AUDITOR X;33.333.333/0001-33\n"
    "36.501.233/0001-15;2027-12-31;1;GESTOR FUTURO;44.444.444/0001-44;;;;\n"
)


def _zip(geral: str = CSV_GERAL, complemento: str = CSV_COMPLEMENTO) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as arquivo:
        arquivo.writestr("inf_anual_fii_geral_2026.csv", geral.encode("latin1"))
        arquivo.writestr(
            "inf_anual_fii_complemento_2026.csv", complemento.encode("latin1")
        )
    return buffer.getvalue()


def _repo(tmp_path, data: bytes = None):
    return CvmAnnualRepository(
        downloader=CvmDatasetDownloader(
            base_url="https://x",
            arquivo=lambda ano: f"inf_anual_fii_{ano}.zip",
            dataset="FII-INF-ANUAL",
            cache_dir=tmp_path,
            fetch=lambda _ano: data if data is not None else _zip(),
            parser_version=SOURCE_SCHEMA_VERSION,
        )
    )


class TestCvmAnnualRepository:
    def test_registro_completo(self, tmp_path):
        report = _repo(tmp_path).get(CNPJ, REFERENCIA, ticker="CYCR11")
        assert report is not None
        assert report.ticker == "CYCR11"
        assert report.reference_date == date(2025, 12, 31)
        assert report.nome_gestor == "CY.CAPITAL GESTORA DE RECURSOS LTDA"
        assert report.cnpj_gestor == "18.596.891/0001-56"
        assert report.nome_administrador == "BANCO GENIAL S.A."
        assert report.cnpj_administrador == "45.246.410/0001-55"
        assert report.nome_custodiante == "BANCO GENIAL"
        assert report.nome_auditor == "AUDITOR X"

    def test_competencia_futura_ignorada(self, tmp_path):
        report = _repo(tmp_path).get(CNPJ, REFERENCIA)
        assert report is not None
        assert report.nome_gestor != "GESTOR FUTURO"

    def test_cnpj_ausente(self, tmp_path):
        assert _repo(tmp_path).get("00000000000000", REFERENCIA) is None

    def test_campos_ausentes(self, tmp_path):
        complemento = (
            "CNPJ_Fundo_Classe;Data_Referencia;Versao;Nome_Gestor;CNPJ_Gestor\n"
            "36.501.233/0001-15;2025-12-31;1;GESTOR SEM CNPJ;\n"
        )
        report = _repo(tmp_path, data=_zip(complemento=complemento)).get(
            CNPJ, REFERENCIA
        )
        assert report is not None
        assert report.nome_gestor == "GESTOR SEM CNPJ"
        assert report.cnpj_gestor is None
        assert report.nome_custodiante is None

    def test_arquivo_reutilizado(self, tmp_path):
        chamadas: list[int] = []

        def fetch(ano: int):
            chamadas.append(ano)
            return _zip()

        repo = CvmAnnualRepository(
            downloader=CvmDatasetDownloader(
                base_url="https://x",
                arquivo=lambda ano: f"inf_anual_fii_{ano}.zip",
                dataset="FII-INF-ANUAL",
                cache_dir=tmp_path,
                fetch=fetch,
            )
        )
        repo.get(CNPJ, REFERENCIA)
        repo.get(CNPJ, REFERENCIA)
        assert chamadas == [2026, 2025]

    def test_metadados_hash_e_versao(self, tmp_path):
        repo = _repo(tmp_path)
        repo.get(CNPJ, REFERENCIA)
        metadata = json.loads(
            (tmp_path / "2026" / "metadata.json").read_text(encoding="utf-8")
        )
        assert metadata["dataset"] == "FII-INF-ANUAL"
        assert metadata["parser_version"] == "cvm-inf-anual-v1"
        assert "sha256" in metadata
