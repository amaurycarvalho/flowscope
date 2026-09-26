"""Testes das entidades de domínio do catálogo de documentos."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from flowscope.domain.documents import (
    AnoDocumentos,
    CatalogoTicker,
    CategoriaDocumentos,
    DocumentoArquivo,
    MesDocumentos,
)


def _arquivo(nome: str = "10.pdf") -> DocumentoArquivo:
    return DocumentoArquivo(
        ticker="ALZR11",
        ano=2026,
        mes=2,
        categoria="Aviso aos Acionistas",
        nome=nome,
        tipo="pdf",
        caminho=Path("/cache") / nome,
    )


class TestDocumentoArquivo:
    def test_igualdade_estrutural(self):
        assert _arquivo() == _arquivo()

    def test_imutavel(self):
        arquivo = _arquivo()
        with pytest.raises(FrozenInstanceError):
            arquivo.nome = "outro.pdf"

    def test_resumos_opcionais_por_padrao(self):
        arquivo = _arquivo()
        assert arquivo.short_summary is None
        assert arquivo.long_summary is None


class TestCatalogoTicker:
    def test_vazio_sem_anos(self):
        assert CatalogoTicker("ALZR11").vazio is True

    def test_nao_vazio_com_anos(self):
        arquivo = _arquivo()
        catalogo = CatalogoTicker(
            "ALZR11",
            (
                AnoDocumentos(
                    2026,
                    (
                        MesDocumentos(
                            2,
                            (CategoriaDocumentos("Aviso aos Acionistas", (arquivo,)),),
                        ),
                    ),
                ),
            ),
        )
        assert catalogo.vazio is False
