import io
import json
import zipfile
from datetime import date, timedelta
from decimal import Decimal

import pytest

from flowscope.domain.ffo import FFOComponentType
from flowscope.infrastructure.conditional_cache import (
    RevalidationResult,
    RevalidationStatus,
)
from flowscope.infrastructure.cvm.datasets import CvmDatasetDownloader
from flowscope.infrastructure.cvm.dfin import CvmDfinRepository
from flowscope.infrastructure.cvm.quarterly import CvmQuarterlyRepository
from flowscope.infrastructure.cvm.schema import CvmSchemaError

REFERENCIA = date(2026, 9, 4)
CNPJ = "28737771000185"
CNPJ_FORMATADO = "28.737.771/0001-85"

CSV_TRIMESTRAL = (
    "CNPJ_Fundo_Classe;Data_Referencia;Codigo;Descricao;Valor;Versao;Data_Recebimento\n"
    "28.737.771/0001-85;2026-06-30;1.01;Receita de aluguel;1000000,00;1;2026-07-10\n"
    "28.737.771/0001-85;2026-06-30;2.01;Despesas administrativas;-200000,00;1;2026-07-10\n"
    "28.737.771/0001-85;2026-06-30;3.01;Ajuste ao valor justo;500000,00;1;2026-07-10\n"
    "28.737.771/0001-85;2026-06-30;9.01;Outras receitas;10000,00;1;2026-07-10\n"
    "28.737.771/0001-85;2026-06-30;1.01;Receita de aluguel;1100000,00;2;2026-07-20\n"
    "99.999.999/0001-91;2026-06-30;1.01;Receita de aluguel;1,00;1;2026-07-10\n"
)

CSV_SEM_COLUNAS = "Outra;Outra2\n1;2\n"

CSV_DFIN = (
    "CNPJ_Fundo_Classe;Data_Referencia;Lucro_Prejuizo\n"
    "28.737.771/0001-85;2026-03-31;700000,00\n"
    "28.737.771/0001-85;2026-06-30;800000,00\n"
    "99.999.999/0001-91;2026-06-30;1,00\n"
)


def _zip(conteudo: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as arquivo:
        arquivo.writestr("inf_trimestral_fii_2026.csv", conteudo.encode("latin1"))
    return buffer.getvalue()


class TestQuarterly:
    def _repo(self, tmp_path, conteudo=CSV_TRIMESTRAL):
        downloader = CvmDatasetDownloader(
            base_url="https://x",
            arquivo=lambda ano: f"inf_trimestral_fii_{ano}.zip",
            dataset="FII-INF-TRIMESTRAL",
            cache_dir=tmp_path,
            fetch=lambda ano: _zip(conteudo),
        )
        return CvmQuarterlyRepository(downloader=downloader)

    def test_componentes_classificados(self, tmp_path):
        componentes = self._repo(tmp_path).get_components(CNPJ, REFERENCIA)
        por_codigo = {c.code: c for c in componentes}
        assert por_codigo["1.01"].classification is FFOComponentType.RECURRING
        assert por_codigo["2.01"].classification is FFOComponentType.RECURRING
        assert por_codigo["3.01"].classification is FFOComponentType.FAIR_VALUE
        assert por_codigo["9.01"].classification is FFOComponentType.UNKNOWN

    def test_codigo_original_preservado(self, tmp_path):
        componentes = self._repo(tmp_path).get_components(CNPJ, REFERENCIA)
        assert "1.01" in {c.code for c in componentes}
        assert all(c.provenance is not None for c in componentes)

    def test_reapresentacao_mais_recente(self, tmp_path):
        componentes = self._repo(tmp_path).get_components(CNPJ, REFERENCIA)
        aluguel = [c for c in componentes if c.code == "1.01"][0]
        assert aluguel.value == Decimal("1100000.00")

    def test_ignora_outro_cnpj(self, tmp_path):
        componentes = self._repo(tmp_path).get_components(CNPJ, REFERENCIA)
        assert all(c.provenance.cnpj == CNPJ for c in componentes)

    def test_schema_ausente_levanta(self, tmp_path):
        repo = self._repo(tmp_path, conteudo=CSV_SEM_COLUNAS)
        # CSV sem a coluna de identidade é ignorado (não é a tabela principal)
        assert repo.get_components(CNPJ, REFERENCIA) == []

    def test_schema_incompleto_levanta(self, tmp_path):
        conteudo = (
            "CNPJ_Fundo_Classe;Data_Referencia\n"
            "28.737.771/0001-85;2026-06-30\n"
        )
        repo = self._repo(tmp_path, conteudo=conteudo)
        with pytest.raises(CvmSchemaError):
            repo.get_components(CNPJ, REFERENCIA)


class TestDfin:
    def _repo(self, tmp_path, conteudo=CSV_DFIN):
        downloader = CvmDatasetDownloader(
            base_url="https://x",
            arquivo=lambda ano: f"dfin_fii_{ano}.csv",
            dataset="FII-DFIN",
            cache_dir=tmp_path,
            fetch=lambda ano: conteudo.encode("latin1"),
            zipado=False,
        )
        return CvmDfinRepository(downloader=downloader)

    def test_resultado_mais_recente(self, tmp_path):
        repo = self._repo(tmp_path)
        assert repo.get_reported(CNPJ, REFERENCIA) == Decimal("800000.00")

    def test_respeita_competencia(self, tmp_path):
        repo = self._repo(tmp_path)
        assert repo.get_reported(CNPJ, date(2026, 4, 1)) == Decimal("700000.00")

    def test_cnpj_ausente_retorna_none(self, tmp_path):
        repo = self._repo(tmp_path)
        assert repo.get_reported("00000000000000", REFERENCIA) is None


class TestDatasetDownloader:
    def test_hash_e_metadados(self, tmp_path):
        data = _zip(CSV_TRIMESTRAL)
        downloader = CvmDatasetDownloader(
            base_url="https://x",
            arquivo=lambda ano: f"inf_trimestral_fii_{ano}.zip",
            dataset="FII-INF-TRIMESTRAL",
            cache_dir=tmp_path,
            fetch=lambda ano: data,
        )
        downloader.baixar_ano(2026)
        diretorio = tmp_path / "2026"
        assert (diretorio / "SHA256").exists()
        metadata = json.loads((diretorio / "metadata.json").read_text(encoding="utf-8"))
        assert metadata["dataset"] == "FII-INF-TRIMESTRAL"

    def test_download_unico(self, tmp_path):
        chamadas: list[int] = []
        downloader = CvmDatasetDownloader(
            base_url="https://x",
            arquivo=lambda ano: f"dfin_fii_{ano}.csv",
            dataset="FII-DFIN",
            cache_dir=tmp_path,
            fetch=lambda ano: chamadas.append(ano) or b"x",
            zipado=False,
        )
        downloader.baixar_ano(2026)
        downloader.baixar_ano(2026)
        assert chamadas == [2026]


class TestRevalidacaoDataset:
    def _downloader(self, tmp_path, respostas, probe):
        estado = {"i": 0, "chamadas": 0}

        def fetch(ano: int):
            estado["chamadas"] += 1
            resposta = respostas[min(estado["i"], len(respostas) - 1)]
            estado["i"] += 1
            return resposta

        downloader = CvmDatasetDownloader(
            base_url="https://x",
            arquivo=lambda ano: f"inf_trimestral_fii_{ano}.zip",
            dataset="FII-INF-TRIMESTRAL",
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
        downloader = CvmDatasetDownloader(
            base_url="https://x",
            arquivo=lambda ano: f"inf_trimestral_fii_{ano}.zip",
            dataset="FII-INF-TRIMESTRAL",
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
