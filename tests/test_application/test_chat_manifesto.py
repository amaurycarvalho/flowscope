"""Testes do manifesto estável da árvore de conhecimento."""

from pathlib import Path

from flowscope.application.chat.arvore import (
    ArvoreConhecimento,
    no_folha,
    no_interno,
    ramo_fundamentos,
)
from flowscope.application.chat.manifesto import (
    TETO_TOKENS,
    assinatura_estado,
    estimar_tokens,
    montar_manifesto,
)


def _arvore() -> ArvoreConhecimento:
    raiz = no_interno("/", "raiz")
    raiz.filho(
        ramo_fundamentos(
            tickers=["PETR4", "VALE3"],
            campos={"PL": "preço/lucro"},
            valores={"PETR4": "[PETR4] PL=3.2"},
        )
    )
    return ArvoreConhecimento(raiz, assinatura="sig")


class TestManifesto:
    def test_determinismo(self) -> None:
        arvore = _arvore()
        assert montar_manifesto(arvore) == montar_manifesto(arvore)

    def test_inclui_chaves(self) -> None:
        texto = montar_manifesto(_arvore())
        assert "PETR4" in texto and "VALE3" in texto
        assert "listar" in texto and "buscar_semantico" in texto

    def test_inclui_mapa_da_arvore(self) -> None:
        texto = montar_manifesto(_arvore())
        assert "/documentos/<ticker>/curto" in texto
        assert "/noticias/<grupo>/indice" in texto
        assert "/fundamentos/valores/<ticker>" in texto

    def test_metadado_redundante_omitido(self) -> None:
        raiz = no_interno("/", "raiz")
        raiz.filho(no_folha("/x", "x", metadado="x"))
        texto = montar_manifesto(ArvoreConhecimento(raiz))
        assert "## Metadados" not in texto

    def test_estima_tokens(self) -> None:
        assert estimar_tokens("x" * 400) == 100

    def test_teto_respeitado(self) -> None:
        assert estimar_tokens(montar_manifesto(_arvore())) < TETO_TOKENS

    def test_degrada_para_so_chaves(self) -> None:
        raiz = no_interno("/", "raiz")
        raiz.filho(no_folha("/x", "x", metadado="propósito descritivo"))
        arvore = ArvoreConhecimento(raiz)
        sem_degradar = montar_manifesto(arvore)
        assert "## Metadados" in sem_degradar
        degradado = montar_manifesto(arvore, contar_tokens=lambda _t: TETO_TOKENS + 1)
        assert "## Metadados" not in degradado


class TestAssinatura:
    def test_estavel_para_mesma_entrada(self, tmp_path: Path) -> None:
        arquivo = tmp_path / "a.txt"
        arquivo.write_text("x")
        a = assinatura_estado([arquivo], ["PETR4"])
        b = assinatura_estado([arquivo], ["PETR4"])
        assert a == b

    def test_muda_com_watchlist(self, tmp_path: Path) -> None:
        arquivo = tmp_path / "a.txt"
        arquivo.write_text("x")
        assert assinatura_estado([arquivo], ["PETR4"]) != assinatura_estado(
            [arquivo], ["VALE3"]
        )

    def test_muda_com_mtime(self, tmp_path: Path) -> None:
        arquivo = tmp_path / "a.txt"
        arquivo.write_text("x")
        antes = assinatura_estado([arquivo], [])
        import os

        os.utime(arquivo, ns=(1, 2_000_000_000))
        assert assinatura_estado([arquivo], []) != antes

    def test_tolera_arquivo_ausente(self, tmp_path: Path) -> None:
        assert assinatura_estado([tmp_path / "some.txt"], []) == assinatura_estado(
            [tmp_path / "some.txt"], []
        )
