"""Testes do cache JSON das inferências de direitos e obrigações."""

import json
from datetime import date

from flowscope.domain.renda_fixa import (
    CarteiraInferencias,
    InferenciaTitulo,
    PapelTitulo,
    TipoTitulo,
)
from flowscope.infrastructure.cvm.renda_fixa_inferencias_cache import (
    RepositorioInferenciasJson,
)


def _item(descricao: str = "CRI da emissora Alfa") -> InferenciaTitulo:
    return InferenciaTitulo(
        tipo=TipoTitulo.CRI,
        papel=PapelTitulo.DIREITO,
        descricao=descricao,
        documento="relatorio.pdf",
        chave_documento="documentos-relevantes/ALZR11/2026/02/10.pdf",
        hash_resumo="hash",
        trecho="O fundo mantém CRI.",
        confianca=0.8,
        data_referencia=date(2026, 2, 1),
    )


class TestRoundTrip:
    def test_grava_no_subdiretorio_e_reconstroi(self, tmp_path):
        repositorio = RepositorioInferenciasJson(cache_dir=tmp_path)
        repositorio.gravar(
            CarteiraInferencias(
                ticker="ALZR11",
                parser_version="v1",
                adquirido_em="2026-10-01T00:00:00+00:00",
                itens=(_item(),),
            )
        )

        caminho = (
            tmp_path / "direitos-obrigacoes" / "inferencias" / "ALZR11.json"
        )
        assert caminho.exists()
        lida = repositorio.ler("ALZR11")
        assert lida is not None
        assert lida.parser_version == "v1"
        assert lida.itens == (_item(),)

    def test_payload_inclui_adquirido_e_atualizado(self, tmp_path):
        repositorio = RepositorioInferenciasJson(cache_dir=tmp_path)
        repositorio.gravar(
            CarteiraInferencias(
                ticker="ALZR11", adquirido_em="agora", itens=(_item(),)
            )
        )
        dados = json.loads(repositorio.caminho("ALZR11").read_text("utf-8"))
        assert dados["adquirido_em"] == "agora"
        assert dados["atualizado_em"] == "agora"


class TestTolerancia:
    def test_ausente_ou_corrompido_retorna_none(self, tmp_path):
        repositorio = RepositorioInferenciasJson(cache_dir=tmp_path)
        assert repositorio.ler("ALZR11") is None
        caminho = repositorio.caminho("ALZR11")
        caminho.parent.mkdir(parents=True)
        caminho.write_text("{nao e json", encoding="utf-8")
        assert repositorio.ler("ALZR11") is None

    def test_item_invalido_e_descartado(self, tmp_path):
        repositorio = RepositorioInferenciasJson(cache_dir=tmp_path)
        caminho = repositorio.caminho("ALZR11")
        caminho.parent.mkdir(parents=True)
        caminho.write_text(
            json.dumps(
                {
                    "ticker": "ALZR11",
                    "parser_version": "v1",
                    "itens": [
                        {"tipo": "desconhecido", "papel": "direito"},
                        {"tipo": "cri", "papel": "direito", "descricao": "x"},
                    ],
                }
            ),
            encoding="utf-8",
        )
        lida = repositorio.ler("ALZR11")
        assert lida is not None
        assert lida.itens == ()

    def test_ticker_invalido_e_recusado(self, tmp_path):
        repositorio = RepositorioInferenciasJson(cache_dir=tmp_path)
        try:
            repositorio.caminho("../nome")
        except ValueError:
            return
        raise AssertionError("ticker inválido deveria ser recusado")
