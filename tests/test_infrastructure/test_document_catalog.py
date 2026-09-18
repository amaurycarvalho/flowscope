"""Testes do catálogo de documentos em cache."""

from pathlib import Path

from flowscope.infrastructure.document_catalog import (
    CatalogoTicker,
    DocumentCatalog,
)
from flowscope.infrastructure.document_summaries import JsonDocumentSummaryStore


def _touch(caminho: Path, conteudo: bytes = b"x") -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_bytes(conteudo)


def _arquivos(catalogo: CatalogoTicker):
    return [
        arquivo
        for ano in catalogo.anos
        for mes in ano.meses
        for categoria in mes.categorias
        for arquivo in categoria.arquivos
    ]


class TestConsolidacao:
    def test_consolida_multiplas_raizes(self, tmp_path):
        _touch(tmp_path / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
        _touch(tmp_path / "informe-mensal" / "ALZR11" / "2026" / "02" / "20.html")
        _touch(
            tmp_path
            / "documentos-relevantes"
            / "ALZR11"
            / "2026"
            / "02"
            / "assembleia"
            / "30.pdf"
        )
        catalogo = DocumentCatalog(cache_dir=tmp_path).catalogo("ALZR11")
        assert catalogo.ticker == "ALZR11"
        assert {arquivo.categoria for arquivo in _arquivos(catalogo)} == {
            "Aviso aos Acionistas",
            "Informe Mensal",
            "Assembleia",
        }

    def test_raiz_inexistente_sem_erro(self, tmp_path):
        catalogo = DocumentCatalog(cache_dir=tmp_path / "ausente").catalogo(
            "ALZR11"
        )
        assert catalogo.vazio


class TestCategoriaETipo:
    def test_deriva_categoria_da_raiz_e_da_subpasta(self, tmp_path):
        _touch(tmp_path / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
        _touch(tmp_path / "informe-mensal" / "ALZR11" / "2026" / "02" / "20.html")
        _touch(
            tmp_path
            / "documentos-relevantes"
            / "ALZR11"
            / "2026"
            / "02"
            / "relatorio"
            / "30.pdf"
        )
        catalogo = DocumentCatalog(cache_dir=tmp_path).catalogo("ALZR11")
        por_categoria = {arquivo.categoria: arquivo for arquivo in _arquivos(catalogo)}
        assert por_categoria["Aviso aos Acionistas"].tipo == "pdf"
        assert por_categoria["Informe Mensal"].tipo == "html"
        assert por_categoria["Relatorio"].tipo == "pdf"

    def test_ticker_normalizado_para_maiusculo(self, tmp_path):
        _touch(tmp_path / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
        catalogo = DocumentCatalog(cache_dir=tmp_path).catalogo("alzr11")
        assert catalogo.ticker == "ALZR11"
        assert len(_arquivos(catalogo)) == 1


class TestOrdenacao:
    def test_ano_mes_categoria_e_arquivos_decrescentes(self, tmp_path):
        base = tmp_path / "bdr" / "ALZR11"
        _touch(base / "2025" / "11" / "5.pdf")
        _touch(base / "2026" / "02" / "9.pdf")
        _touch(base / "2026" / "02" / "10.pdf")
        _touch(
            tmp_path
            / "documentos-relevantes"
            / "ALZR11"
            / "2026"
            / "02"
            / "assembleia"
            / "1.pdf"
        )
        catalogo = DocumentCatalog(cache_dir=tmp_path).catalogo("ALZR11")

        assert [ano.ano for ano in catalogo.anos] == [2026, 2025]
        assert [mes.mes for mes in catalogo.anos[0].meses] == [2]
        assert [mes.mes for mes in catalogo.anos[1].meses] == [11]
        categorias = catalogo.anos[0].meses[0].categorias
        assert [categoria.nome for categoria in categorias] == [
            "Assembleia",
            "Aviso aos Acionistas",
        ]
        avisos = next(
            categoria
            for categoria in categorias
            if categoria.nome == "Aviso aos Acionistas"
        )
        assert [arquivo.nome for arquivo in avisos.arquivos] == [
            "10.pdf",
            "9.pdf",
        ]

    def test_ticker_sem_documentos_vazio(self, tmp_path):
        catalogo = DocumentCatalog(cache_dir=tmp_path).catalogo("ALZR11")
        assert catalogo.vazio
        assert catalogo.anos == ()


class TestResumos:
    def test_campos_nulos_por_padrao(self, tmp_path):
        _touch(tmp_path / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
        catalogo = DocumentCatalog(cache_dir=tmp_path).catalogo("ALZR11")
        arquivo = _arquivos(catalogo)[0]
        assert arquivo.short_summary is None
        assert arquivo.long_summary is None

    def test_documento_com_resumo_enriquecido(self, tmp_path):
        _touch(tmp_path / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
        store = JsonDocumentSummaryStore(cache_dir=tmp_path)
        store.salvar(
            "ALZR11", "bdr/ALZR11/2026/02/10.pdf", "curto", "longo"
        )
        catalogo = DocumentCatalog(
            cache_dir=tmp_path, summary_store=store
        ).catalogo("ALZR11")
        arquivo = _arquivos(catalogo)[0]
        assert arquivo.short_summary == "curto"
        assert arquivo.long_summary == "longo"

    def test_chave_estavel_entre_varreduras(self, tmp_path):
        _touch(tmp_path / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
        store = JsonDocumentSummaryStore(cache_dir=tmp_path)
        store.salvar(
            "ALZR11", "bdr/ALZR11/2026/02/10.pdf", "curto", "longo"
        )
        catalogo = DocumentCatalog(cache_dir=tmp_path, summary_store=store)
        primeira = _arquivos(catalogo.catalogo("ALZR11"))[0]
        segunda = _arquivos(catalogo.catalogo("ALZR11"))[0]
        assert primeira.short_summary == segunda.short_summary == "curto"

    def test_resumo_de_outro_ticker_nao_vaza(self, tmp_path):
        _touch(tmp_path / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf")
        store = JsonDocumentSummaryStore(cache_dir=tmp_path)
        store.salvar("BOVA11", "bdr/BOVA11/2026/02/10.pdf", "curto", "longo")
        catalogo = DocumentCatalog(
            cache_dir=tmp_path, summary_store=store
        ).catalogo("ALZR11")
        assert _arquivos(catalogo)[0].short_summary is None
