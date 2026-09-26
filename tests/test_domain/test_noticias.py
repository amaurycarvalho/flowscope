"""Testes de domínio da fatia de Notícias: classificação e entidades."""

from pathlib import Path

from flowscope.domain.documents import (
    AnoDocumentos,
    CategoriaDocumentos,
    MesDocumentos,
)
from flowscope.domain.documents import CatalogoTicker
from flowscope.domain.noticias import (
    SECOES_ORDEM,
    CatalogoNoticias,
    NoticiaArquivo,
    SecaoNoticias,
    classificar_tipo,
    normalizar_texto,
    noticia_excepcional,
)


def _arquivo(secao: str = "Geral") -> NoticiaArquivo:
    return NoticiaArquivo(
        ticker="NOTICIAS",
        ano=2026,
        mes=9,
        categoria="Negociação",
        nome="titulo",
        tipo="html",
        caminho=Path("/tmp/titulo.html"),
        url="https://x/1",
        data_publicacao="2026-09-20",
        secao=secao,
        data_ordinal=10,
    )


class TestClassificacao:
    def test_normaliza_caixa_acentos_e_espacos(self):
        assert normalizar_texto("  SUSPENSÃO   de Negociação ") == (
            "suspensao de negociacao"
        )

    def test_titulo_excepcional(self):
        assert noticia_excepcional("PETR4 - Suspensão de negociação") is True

    def test_titulo_rotineiro_nao_e_excepcional(self):
        assert noticia_excepcional("PETR4 - Comunicado ao Mercado") is False

    def test_classifica_tipo_tipico(self):
        assert classificar_tipo("PETR4 - Suspensão de negociação") == "Negociação"

    def test_titulo_sem_tipo_cai_em_outros(self):
        assert classificar_tipo("PETR4 - Comunicado sem evento") == "Outros"


class TestEntidades:
    def test_noticia_arquivo_estende_documento(self):
        arquivo = _arquivo()
        assert arquivo.secao == "Geral"
        assert arquivo.data_ordinal == 10
        assert arquivo.url == "https://x/1"

    def test_catalogo_vazio_sem_itens(self):
        catalogo = CatalogoNoticias(
            "Notícias",
            tuple(SecaoNoticias(nome, CatalogoTicker(nome)) for nome in SECOES_ORDEM),
        )
        assert catalogo.vazio is True

    def test_catalogo_nao_vazio_com_itens(self):
        catalogo_ticker = CatalogoTicker(
            "Geral",
            (
                AnoDocumentos(
                    2026,
                    (
                        MesDocumentos(
                            9,
                            (CategoriaDocumentos("Negociação", (_arquivo(),)),),
                        ),
                    ),
                ),
            ),
        )
        catalogo = CatalogoNoticias(
            "Notícias", (SecaoNoticias("Geral", catalogo_ticker),)
        )
        assert catalogo.vazio is False
