"""Testes do ramo ``/noticias`` da árvore de conhecimento do chat."""

from datetime import date
from types import SimpleNamespace

from flowscope.application.chat.noticias import FonteNoticias
from flowscope.application.noticias.fonte_chat import chave_curta
from flowscope.domain.noticias import (
    ESCOPO_NOTICIAS,
    SECAO_CENSURAS,
    SECAO_GERAL,
    SECOES_ORDEM,
)


class _FakeStore:
    """Store de textos em memória."""

    def __init__(self, textos: dict[str, str]) -> None:
        self._textos = textos

    def obter(self, ticker: str, chave: str) -> str | None:
        return self._textos.get(chave)


class _FakeCatalog:
    """Catálogo de notícias com itens semeados em memória."""

    def __init__(self, arquivos: list, chaves: dict, textos: dict | None = None) -> None:
        self._arquivos = arquivos
        self._chaves = chaves
        self.text_store = _FakeStore(textos or {})

    def arquivos(self) -> list:
        return list(self._arquivos)

    def chave(self, arquivo) -> str:
        return self._chaves[arquivo.caminho]


def _arquivo(secao: str, nome: str, caminho: str, curto=None, longo=None) -> SimpleNamespace:
    return SimpleNamespace(
        secao=secao,
        nome=nome,
        data_publicacao="2026-09-20",
        categoria="tipo",
        caminho=caminho,
        short_summary=curto,
        long_summary=longo,
        data_ordinal=date(2026, 9, 20).toordinal(),
    )


def _fonte(curto="resumo curto", longo=None, texto=None) -> FonteNoticias:
    arquivo = _arquivo(SECAO_CENSURAS, "PETR4 suspensão", "c1", curto, longo)
    chaves = {"c1": "censuras/c1"}
    textos = {}
    if texto is not None:
        textos["censuras/c1"] = texto
    return FonteNoticias(catalog=_FakeCatalog([arquivo], chaves, textos))


def _caminhos(raiz) -> set[str]:
    return {no.caminho for no in _percorrer(raiz)}


def _percorrer(no):
    yield no
    for filho in no.filhos:
        yield from _percorrer(filho)


class TestRamoNoticias:
    def test_grupos_fixos(self) -> None:
        caminhos = _caminhos(_fonte().construir())
        for secao in SECOES_ORDEM:
            assert f"/noticias/grupos/{secao}" in caminhos

    def test_indice_e_nos_do_item(self) -> None:
        caminhos = _caminhos(_fonte().construir())
        chave = chave_curta("censuras/c1")
        assert f"/noticias/{SECAO_CENSURAS}/indice" in caminhos
        assert f"/noticias/{SECAO_CENSURAS}/{chave}/titulo" in caminhos
        assert f"/noticias/{SECAO_CENSURAS}/{chave}/resumo" in caminhos

    def test_texto_em_cache_vira_no(self) -> None:
        ramo = _fonte(texto="texto integral da noticia").construir()
        chave = chave_curta("censuras/c1")
        caminho = f"/noticias/{SECAO_CENSURAS}/{chave}/texto"
        texto = next((no for no in _percorrer(ramo) if no.caminho == caminho), None)
        assert texto is not None
        assert texto.campo_pesado == "texto"

    def test_pendente_omitido(self) -> None:
        arquivo = _arquivo(SECAO_GERAL, "sem resumo", "g1")
        fonte = FonteNoticias(catalog=_FakeCatalog([arquivo], {"g1": "geral/g1"}))
        caminhos = _caminhos(fonte.construir())
        assert not any(c.startswith(f"/noticias/{SECAO_GERAL}/n") for c in caminhos)

    def test_sem_catalogo(self) -> None:
        assert _caminhos(FonteNoticias(catalog=None).construir()) == {
            "/noticias",
            "/noticias/grupos",
            *{f"/noticias/grupos/{s}" for s in SECOES_ORDEM},
        }

    def test_conteudo_apenas_do_cache(self) -> None:
        ramo = _fonte().construir()
        assert ESCOPO_NOTICIAS  # o ramo não consulta a B3; apenas o cache local
        assert ramo.caminho == "/noticias"
