"""Testes do housekeeping diário dos arquivos de log."""

import os
from datetime import date, datetime
from unittest.mock import patch

from flowscope.infrastructure.logging.housekeeping import (
    limpar_backups_antigos,
    nome_backup,
    renomear_backup,
    rotacionar_log_obsoleto,
)

HOJE = date(2026, 10, 13)


def _definir_mtime(path, quando: datetime) -> None:
    ts = quando.timestamp()
    os.utime(path, (ts, ts))


class TestNomeBackup:
    def test_formato_datado(self):
        assert nome_backup(date(2026, 10, 12)) == "flowscope-2026-10-12.log"

    def test_handler_converte_para_formato_datado(self):
        assert (
            renomear_backup("/logs/flowscope.log.2026-10-12")
            == "/logs/flowscope-2026-10-12.log"
        )

    def test_handler_preserva_nome_fora_do_padrao(self):
        assert renomear_backup("/logs/outro.log") == "/logs/outro.log"


class TestLimparBackupsAntigos:
    def test_apaga_mais_antigos_que_a_retencao(self, tmp_path):
        antigo = tmp_path / "flowscope-2026-10-01.log"
        antigo.write_text("x")

        limpar_backups_antigos(tmp_path, HOJE, 7)

        assert not antigo.exists()

    def test_limite_exato_e_preservado(self, tmp_path):
        limite = tmp_path / "flowscope-2026-10-06.log"
        limite.write_text("x")

        limpar_backups_antigos(tmp_path, HOJE, 7)

        assert limite.exists()

    def test_retencao_customizada(self, tmp_path):
        fora = tmp_path / "flowscope-2026-10-09.log"
        dentro = tmp_path / "flowscope-2026-10-10.log"
        fora.write_text("x")
        dentro.write_text("x")

        limpar_backups_antigos(tmp_path, HOJE, 3)

        assert not fora.exists()
        assert dentro.exists()

    def test_arquivo_ativo_e_preservado(self, tmp_path):
        ativo = tmp_path / "flowscope.log"
        ativo.write_text("x")

        limpar_backups_antigos(tmp_path, HOJE, 7)

        assert ativo.exists()

    def test_arquivos_fora_do_padrao_sao_ignorados(self, tmp_path):
        legado = tmp_path / "flowscope.log.1"
        formato_antigo = tmp_path / "flowscope.log.2026-10-01"
        outro = tmp_path / "outro.txt"
        legado.write_text("x")
        formato_antigo.write_text("x")
        outro.write_text("x")

        limpar_backups_antigos(tmp_path, HOJE, 7)

        assert legado.exists()
        assert formato_antigo.exists()
        assert outro.exists()

    def test_diretorio_inexistente_nao_falha(self, tmp_path):
        limpar_backups_antigos(tmp_path / "nao-existe", HOJE, 7)

    def test_oserror_ao_remover_e_tolerado(self, tmp_path):
        antigo = tmp_path / "flowscope-2026-10-01.log"
        antigo.write_text("x")

        with patch("pathlib.Path.unlink", side_effect=OSError("em uso")):
            limpar_backups_antigos(tmp_path, HOJE, 7)

        assert antigo.exists()


class TestRotacionarLogObsoleto:
    def test_dia_anterior_e_rotacionado(self, tmp_path):
        ativo = tmp_path / "flowscope.log"
        ativo.write_text("ontem")
        _definir_mtime(ativo, datetime(2026, 10, 12, 23, 0, 0))

        rotacionar_log_obsoleto(ativo, HOJE)

        destino = tmp_path / "flowscope-2026-10-12.log"
        assert destino.read_text() == "ontem"
        assert not ativo.exists()

    def test_mesmo_dia_nao_rotaciona(self, tmp_path):
        ativo = tmp_path / "flowscope.log"
        ativo.write_text("hoje")
        _definir_mtime(ativo, datetime(2026, 10, 13, 8, 0, 0))

        rotacionar_log_obsoleto(ativo, HOJE)

        assert ativo.exists()
        assert not (tmp_path / "flowscope-2026-10-13.log").exists()

    def test_destino_existente_recebe_concatenacao(self, tmp_path):
        ativo = tmp_path / "flowscope.log"
        ativo.write_text("novo\n")
        _definir_mtime(ativo, datetime(2026, 10, 12, 10, 0, 0))
        destino = tmp_path / "flowscope-2026-10-12.log"
        destino.write_text("antigo\n")

        rotacionar_log_obsoleto(ativo, HOJE)

        assert destino.read_text() == "antigo\nnovo\n"
        assert not ativo.exists()

    def test_ausente_nao_faz_nada(self, tmp_path):
        rotacionar_log_obsoleto(tmp_path / "flowscope.log", HOJE)

    def test_oserror_ao_inspecionar_e_tolerado(self, tmp_path):
        ativo = tmp_path / "flowscope.log"
        ativo.write_text("ontem")

        with patch("pathlib.Path.stat", side_effect=OSError("sem permissao")):
            rotacionar_log_obsoleto(ativo, HOJE)

        assert ativo.exists()

    def test_oserror_ao_rotacionar_e_tolerado(self, tmp_path):
        ativo = tmp_path / "flowscope.log"
        ativo.write_text("ontem")
        _definir_mtime(ativo, datetime(2026, 10, 12, 23, 0, 0))

        with patch("pathlib.Path.rename", side_effect=OSError("em uso")):
            rotacionar_log_obsoleto(ativo, HOJE)

        assert ativo.exists()
