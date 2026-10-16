import os
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from flowscope.infrastructure.conditional_cache_types import _atomic_write_bytes


class TestAtomicWriteBytes:
    def test_escreve_conteudo(self, tmp_path):
        destino = tmp_path / "dados.json"
        _atomic_write_bytes(destino, b"conteudo")
        assert destino.read_bytes() == b"conteudo"

    def test_sobrescreve_destino_existente(self, tmp_path):
        destino = tmp_path / "dados.json"
        destino.write_bytes(b"antigo")
        _atomic_write_bytes(destino, b"novo")
        assert destino.read_bytes() == b"novo"

    def test_cria_diretorios_pais(self, tmp_path):
        destino = tmp_path / "a" / "b" / "dados.json"
        _atomic_write_bytes(destino, b"x")
        assert destino.read_bytes() == b"x"

    def test_escritas_concorrentes_nao_falham_nem_deixam_parcial(self, tmp_path):
        destino = tmp_path / "concorrente.json"
        payloads = [
            (f"valor-{indice}".encode("utf-8") * 5000) for indice in range(40)
        ]

        def escrever(payload: bytes) -> None:
            _atomic_write_bytes(destino, payload)

        with ThreadPoolExecutor(max_workers=8) as executor:
            list(executor.map(escrever, payloads))

        final = destino.read_bytes()
        assert final in payloads
        assert not list(tmp_path.glob("*.tmp"))

    def test_temporarios_distintos_por_escrita(self, tmp_path):
        destino = tmp_path / "alvo.json"
        temporarios = []
        real_replace = os.replace

        def espiao(origem, alvo):
            temporarios.append(os.fspath(origem))
            return real_replace(origem, alvo)

        with patch(
            "flowscope.infrastructure.conditional_cache_types.os.replace",
            side_effect=espiao,
        ):
            _atomic_write_bytes(destino, b"a")
            _atomic_write_bytes(destino, b"b")

        assert len(temporarios) == 2
        assert temporarios[0] != temporarios[1]
