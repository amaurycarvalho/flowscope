"""Testes da política pura e do serviço de deduplicação por hash."""

from pathlib import Path

from flowscope.application.deduplicacao import (
    TAMANHO_MINIMO_CONTEUDO,
    DeduplicacaoConteudo,
    conteudo_hashavel,
    eh_duplicata,
)


class _RegistroFake:
    """Duplo de teste da porta ``HashRegistry``."""

    def __init__(self, mapa: dict[str, str] | None = None) -> None:
        self.mapa = dict(mapa or {})
        self.removidos: list[str] = []

    def canonico(self, digest: str) -> str | None:
        return self.mapa.get(digest)

    def registrados(self) -> dict[str, str]:
        return dict(self.mapa)

    def registrar(self, digest: str, relativo: str) -> None:
        self.mapa[digest] = relativo

    def remover(self, digest: str) -> None:
        self.mapa.pop(digest, None)
        self.removidos.append(digest)

    def remover_relativo(self, relativo: str) -> None:
        self.mapa = {
            digest: valor
            for digest, valor in self.mapa.items()
            if valor != relativo
        }


def _hash(conteudo: bytes) -> str:
    return f"h{len(conteudo)}"


class TestConteudoHashavel:
    def test_vazio_nao_e_hashavel(self):
        assert conteudo_hashavel(b"") is False

    def test_apenas_espacos_nao_e_hashavel(self):
        assert conteudo_hashavel(b"   \n\t" * 100) is False

    def test_abaixo_do_piso_nao_e_hashavel(self):
        assert conteudo_hashavel(b"x" * (TAMANHO_MINIMO_CONTEUDO - 1)) is False

    def test_no_piso_e_hashavel(self):
        assert conteudo_hashavel(b"x" * TAMANHO_MINIMO_CONTEUDO) is True

    def test_piso_configuravel(self):
        assert conteudo_hashavel(b"xxxx", minimo=4) is True
        assert conteudo_hashavel(b"xxxx", minimo=5) is False


class TestEhDuplicata:
    def test_sem_canonico_nao_duplica(self):
        assert eh_duplicata("h", None, False, "a/b.pdf") is False

    def test_canonico_igual_nao_duplica(self):
        assert eh_duplicata("h", "a/b.pdf", True, "a/b.pdf") is False

    def test_canonico_distinto_existente_duplica(self):
        assert eh_duplicata("h", "a/antigo.pdf", True, "a/novo.pdf") is True

    def test_canonico_inexistente_nao_duplica(self):
        assert eh_duplicata("h", "a/sumido.pdf", False, "a/novo.pdf") is False


class TestDeduplicacaoConteudo:
    def _servico(self, tmp_path: Path, registro: _RegistroFake):
        return DeduplicacaoConteudo(registro, _hash, tmp_path)

    def test_conteudo_guardado_nao_avalia(self, tmp_path):
        servico = self._servico(tmp_path, _RegistroFake())
        avaliacao = servico.avaliar(b"curto", tmp_path / "a.pdf")
        assert avaliacao.digest is None
        assert avaliacao.duplicata is False

    def test_conteudo_novo(self, tmp_path):
        servico = self._servico(tmp_path, _RegistroFake())
        conteudo = b"x" * TAMANHO_MINIMO_CONTEUDO
        avaliacao = servico.avaliar(conteudo, tmp_path / "a.pdf")
        assert avaliacao.digest == _hash(conteudo)
        assert avaliacao.duplicata is False

    def test_duplicata_com_canonico_no_disco(self, tmp_path):
        conteudo = b"x" * TAMANHO_MINIMO_CONTEUDO
        digest = _hash(conteudo)
        canonico = tmp_path / "antigo.pdf"
        canonico.write_bytes(conteudo)
        servico = self._servico(tmp_path, _RegistroFake({digest: "antigo.pdf"}))
        avaliacao = servico.avaliar(conteudo, tmp_path / "novo.pdf")
        assert avaliacao.duplicata is True

    def test_canonico_ausente_nao_duplica(self, tmp_path):
        conteudo = b"x" * TAMANHO_MINIMO_CONTEUDO
        digest = _hash(conteudo)
        servico = self._servico(tmp_path, _RegistroFake({digest: "sumido.pdf"}))
        avaliacao = servico.avaliar(conteudo, tmp_path / "novo.pdf")
        assert avaliacao.duplicata is False

    def test_processar_grava_e_registra(self, tmp_path):
        servico = self._servico(tmp_path, _RegistroFake())
        conteudo = b"x" * TAMANHO_MINIMO_CONTEUDO
        gravados: list[bytes] = []
        resultado = servico.processar(
            conteudo, tmp_path / "a" / "b.pdf", gravados.append
        )
        assert resultado is True
        assert gravados == [conteudo]
        assert servico._registry.canonico(_hash(conteudo)) == "a/b.pdf"

    def test_processar_descarta_duplicata(self, tmp_path):
        conteudo = b"x" * TAMANHO_MINIMO_CONTEUDO
        digest = _hash(conteudo)
        (tmp_path / "antigo.pdf").write_bytes(conteudo)
        servico = self._servico(tmp_path, _RegistroFake({digest: "antigo.pdf"}))
        gravados: list[bytes] = []
        resultado = servico.processar(
            conteudo, tmp_path / "novo.pdf", gravados.append
        )
        assert resultado is False
        assert gravados == []
