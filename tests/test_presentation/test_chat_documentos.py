"""Testes da cascata de documentos do chat."""

import logging
from pathlib import Path

import pytest

from flowscope.application.documentos.catalogo import chave_documento
from flowscope.infrastructure.document_catalog import DocumentCatalog
from flowscope.presentation.gui.chat.documentos import (
    FAIXA_AUTOMATICA,
    FAIXA_LISTAR,
    FAIXA_QUANTIDADE,
    CascataDocumentos,
    DocumentoEscopo,
    faixa_confirmacao,
)


class _FakeLLM:
    """Porta de completion de teste que devolve um par curto/longo."""

    def __init__(self, resposta: str) -> None:
        self._resposta = resposta
        self.chamadas = 0

    def complete(self, messages: list[dict], system_prompt: str | None = None) -> str:
        self.chamadas += 1
        return self._resposta


def _documento(tmp_path, ticker="PETR4", nome="1.html") -> tuple:
    """Cria um informe mensal HTML em cache e devolve catálogo e arquivo."""
    pasta = tmp_path / "informe-mensal" / ticker / "2026" / "07"
    pasta.mkdir(parents=True)
    arquivo = pasta / nome
    arquivo.write_text(
        "<html><body><p>conteudo integral do informe</p></body></html>",
        encoding="utf-8",
    )
    return DocumentCatalog(cache_dir=tmp_path), arquivo


def _escopo(indice: int) -> DocumentoEscopo:
    """Cria um documento de escopo fictício para os testes de gate."""
    return DocumentoEscopo(
        ticker="PETR4",
        nome=f"{indice}.pdf",
        categoria="Fato Relevante",
        ano=2026,
        mes=7,
        chave=f"documentos-relevantes/PETR4/2026/07/fato-relevante/{indice}.pdf",
        caminho=Path(f"/tmp/{indice}.pdf"),
    )


class TestLeitorResumos:
    def test_resumos_do_escopo(self, tmp_path):
        catalogo, arquivo = _documento(tmp_path)
        chave = chave_documento(arquivo, tmp_path)
        catalogo.summary_store.salvar("PETR4", chave, "curto", "longo")
        cascata = CascataDocumentos(catalog=catalogo)

        texto, alvos = cascata.montar_resumos("PETR4", [])
        assert "curto" in texto
        assert "longo" in texto
        assert chave in texto
        assert [a.chave for a in alvos] == [chave]

    def test_listar_escopo_watchlist(self, tmp_path):
        catalogo, _ = _documento(tmp_path)
        cascata = CascataDocumentos(catalog=catalogo)
        documentos = cascata.listar(None, ["PETR4"])
        assert len(documentos) == 1
        assert documentos[0].ticker == "PETR4"


class TestLeitorTextoIntegral:
    def test_texto_integral_do_cache(self, tmp_path):
        catalogo, arquivo = _documento(tmp_path)
        chave = chave_documento(arquivo, tmp_path)
        catalogo.text_store.salvar("PETR4", chave, "texto integral cacheado")
        cascata = CascataDocumentos(catalog=catalogo)

        alvos = cascata.resolver_alvos([chave])
        assert [a.chave for a in alvos] == [chave]
        assert cascata.preparar_texto(alvos) == "texto integral cacheado"

    def test_chave_desconhecida_ignorada(self, tmp_path):
        catalogo, _ = _documento(tmp_path)
        cascata = CascataDocumentos(catalog=catalogo)
        assert cascata.resolver_alvos(["inexistente"]) == []


class TestPreparacaoSobDemanda:
    def test_cache_frio_prepara_texto_e_resumo(self, tmp_path):
        catalogo, arquivo = _documento(tmp_path)
        chave = chave_documento(arquivo, tmp_path)
        llm = _FakeLLM("CURTO: resumo curto\nLONGO: resumo longo")
        cascata = CascataDocumentos(
            catalog=catalogo, llm_factory=lambda: llm
        )

        texto, alvos = cascata.montar_resumos("PETR4", [])
        assert "resumo curto" in texto
        assert "resumo longo" in texto
        assert llm.chamadas == 1
        assert catalogo.text_store.obter("PETR4", chave) is not None
        resumo = catalogo.summary_store.obter("PETR4", chave)
        assert resumo is not None
        assert resumo.long_summary == "resumo longo"
        assert [a.chave for a in alvos] == [chave]


class TestGateConfirmacao:
    @pytest.mark.parametrize(
        ("quantidade", "faixa"),
        [
            (0, FAIXA_AUTOMATICA),
            (3, FAIXA_AUTOMATICA),
            (4, FAIXA_LISTAR),
            (7, FAIXA_LISTAR),
            (8, FAIXA_QUANTIDADE),
            (20, FAIXA_QUANTIDADE),
        ],
    )
    def test_faixas(self, quantidade, faixa):
        assert faixa_confirmacao(quantidade) == faixa

    def test_ate_tres_prossegue_sem_callback(self):
        chamadas: list = []
        cascata = CascataDocumentos(
            confirmar=lambda quantidade, nomes: chamadas.append(quantidade) or True
        )
        assert cascata.confirmar_leitura([_escopo(i) for i in range(3)]) is True
        assert chamadas == []

    def test_quatro_a_sete_lista_nomes(self):
        chamadas: list = []

        def confirmar(quantidade: int, nomes: list[str]) -> bool:
            chamadas.append((quantidade, nomes))
            return True

        cascata = CascataDocumentos(confirmar=confirmar)
        assert cascata.confirmar_leitura([_escopo(i) for i in range(5)]) is True
        quantidade, nomes = chamadas[0]
        assert quantidade == 5
        assert nomes == ["0.pdf", "1.pdf", "2.pdf", "3.pdf", "4.pdf"]

    def test_oito_ou_mais_informa_quantidade(self):
        chamadas: list = []

        def confirmar(quantidade: int, nomes: list[str]) -> bool:
            chamadas.append((quantidade, nomes))
            return False

        cascata = CascataDocumentos(confirmar=confirmar)
        assert cascata.confirmar_leitura([_escopo(i) for i in range(9)]) is False
        assert chamadas == [(9, [])]


class TestOrcamento:
    def test_teto_por_documento_e_global(self, caplog):
        cascata = CascataDocumentos(teto_documento=5, teto_global=8)
        with caplog.at_level(logging.WARNING, logger="flowscope"):
            texto = cascata._aplicar_orcamento(["123456789", "abcdef"])
        assert texto == "12345\n\nabc"
        assert any("truncado" in r.getMessage() for r in caplog.records)

    def test_sem_excesso_nao_trunca(self, caplog):
        cascata = CascataDocumentos(teto_documento=100, teto_global=100)
        with caplog.at_level(logging.WARNING, logger="flowscope"):
            texto = cascata._aplicar_orcamento(["abc", "def"])
        assert texto == "abc\n\ndef"
        assert caplog.records == []

    def test_teto_global_esgotado(self, caplog):
        cascata = CascataDocumentos(teto_documento=100, teto_global=4)
        with caplog.at_level(logging.WARNING, logger="flowscope"):
            texto = cascata._aplicar_orcamento(["abcd", "efgh"])
        assert texto == "abcd"
        assert any("truncado" in r.getMessage() for r in caplog.records)
