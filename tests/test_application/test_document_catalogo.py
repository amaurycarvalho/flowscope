"""Testes puros do read-model e da chave estável do catálogo de documentos."""

from pathlib import Path

from flowscope.application.documentos.catalogo import (
    ConsultarCatalogoUseCase,
    chave_documento,
    montar_catalogo,
)
from flowscope.domain.documents import CatalogoTicker, DocumentoArquivo


def _arquivo(
    nome: str,
    ano: int = 2026,
    mes: int = 2,
    categoria: str = "Aviso aos Acionistas",
) -> DocumentoArquivo:
    return DocumentoArquivo(
        ticker="ALZR11",
        ano=ano,
        mes=mes,
        categoria=categoria,
        nome=nome,
        tipo="pdf",
        caminho=Path("/cache") / nome,
    )


class TestChaveDocumento:
    def test_relativa_a_base(self, tmp_path):
        caminho = tmp_path / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf"
        assert chave_documento(caminho, tmp_path) == "bdr/ALZR11/2026/02/10.pdf"

    def test_fora_da_base_usa_o_nome(self, tmp_path):
        caminho = Path("/outro/lugar/10.pdf")
        assert chave_documento(caminho, tmp_path) == "10.pdf"

    def test_estavel_entre_chamadas(self, tmp_path):
        caminho = tmp_path / "bdr" / "ALZR11" / "2026" / "02" / "10.pdf"
        assert chave_documento(caminho, tmp_path) == chave_documento(caminho, tmp_path)


class TestMontarCatalogo:
    def test_agrupa_ano_mes_categoria(self):
        catalogo = montar_catalogo(
            "ALZR11",
            [
                _arquivo("10.pdf", categoria="Aviso aos Acionistas"),
                _arquivo("20.pdf", categoria="Assembleia"),
            ],
        )
        assert catalogo.ticker == "ALZR11"
        categorias = catalogo.anos[0].meses[0].categorias
        assert [categoria.nome for categoria in categorias] == [
            "Assembleia",
            "Aviso aos Acionistas",
        ]

    def test_ordena_anos_meses_e_arquivos_decrescentes(self):
        catalogo = montar_catalogo(
            "ALZR11",
            [
                _arquivo("5.pdf", ano=2025, mes=11),
                _arquivo("9.pdf", ano=2026, mes=2),
                _arquivo("10.pdf", ano=2026, mes=2),
            ],
        )
        assert [ano.ano for ano in catalogo.anos] == [2026, 2025]
        assert [mes.mes for mes in catalogo.anos[0].meses] == [2]
        avisos = catalogo.anos[0].meses[0].categorias[0]
        assert [arquivo.nome for arquivo in avisos.arquivos] == ["10.pdf", "9.pdf"]

    def test_sem_arquivos_fica_vazio(self):
        assert montar_catalogo("ALZR11", []).vazio is True


class TestConsultarCatalogoUseCase:
    def test_delega_ao_repositorio(self):
        class _Repositorio:
            def __init__(self):
                self.chamadas: list[str] = []

            def catalogo(self, ticker: str) -> CatalogoTicker:
                self.chamadas.append(ticker)
                return CatalogoTicker(ticker.upper())

        repositorio = _Repositorio()
        caso = ConsultarCatalogoUseCase(repositorio)
        assert caso.executar("alzr11").ticker == "ALZR11"
        assert repositorio.chamadas == ["alzr11"]
