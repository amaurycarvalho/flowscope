"""Testes do catálogo de notícias em cache (somente leitura local)."""

from datetime import date

from flowscope.domain.structured import (
    CensuraPublica,
    CondicaoExcepcional,
    NoticiaB3,
    ProgramaAquisicao,
)
from flowscope.infrastructure.b3.noticias_aquisicao import (
    ESCOPO_NOTICIAS,
    SECAO_CENSURAS,
    SECAO_CONDICOES,
    SECAO_GERAL,
    SECAO_PROGRAMAS,
    ItemNoticia,
    NoticiasCache,
    chave_item,
    chave_noticia,
    data_noticia,
    html_do_item,
    item_de_censura,
    item_de_condicao,
    item_de_noticia,
    item_de_programa,
)
from flowscope.infrastructure.b3.noticias_catalogo import (
    TITULO_NOTICIAS,
    NoticiasCatalog,
)
from flowscope.infrastructure.b3.noticias_index import (
    NoticiaMeta,
    NoticiasIndexStore,
)
from flowscope.infrastructure.document_summaries import JsonDocumentSummaryStore

_REFERENCIA = date(2026, 9, 25)


def _noticia(titulo="PETROBRAS (PETR4) - Suspensão de negociação", url="https://x/1"):
    return NoticiaB3(
        titulo=titulo,
        data_publicacao="2026-09-20 10:00:00",
        url=url,
        agencia="18",
    )


def _registrar(tmp_path, item: ItemNoticia) -> str:
    """Grava o HTML do item e o registra no índice; devolve o caminho relativo."""
    cache = NoticiasCache(tmp_path)
    data = data_noticia(item.data_publicacao, _REFERENCIA)
    chave = chave_item(item)
    cache.gravar(chave, data, html_do_item(item))
    caminho = cache.caminho(chave, data)
    NoticiasIndexStore(cache_dir=tmp_path).registrar(
        caminho,
        NoticiaMeta(
            secao=item.secao,
            titulo=item.titulo,
            data_publicacao=item.data_publicacao,
            categoria=item.categoria,
            url=item.url,
        ),
    )
    return f"noticias/{data.year:04d}/{data.month:02d}/{chave}.html"


def _catalogado(tmp_path, noticia: NoticiaB3) -> str:
    return _registrar(tmp_path, item_de_noticia(noticia))


class TestNoticiasCatalog:
    def test_retorna_apenas_noticias_indexadas(self, tmp_path):
        com_cache = _noticia(titulo="Com cache - Suspensão de negociação")
        sem_cache = _noticia(
            titulo="Sem cache - Suspensão de negociação", url="https://x/2"
        )
        _catalogado(tmp_path, com_cache)
        catalogo = NoticiasCatalog(cache_dir=tmp_path)
        arquivos = catalogo.arquivos()
        assert [arquivo.nome for arquivo in arquivos] == [
            "Com cache - Suspensão de negociação"
        ]

    def test_html_sem_indice_e_ignorado(self, tmp_path):
        noticia = _noticia()
        data = data_noticia(noticia.data_publicacao, _REFERENCIA)
        NoticiasCache(tmp_path).gravar(
            chave_noticia(noticia), data, b"<html>corpo</html>"
        )
        assert NoticiasCatalog(cache_dir=tmp_path).arquivos() == []

    def test_indice_sem_html_e_ignorado(self, tmp_path):
        noticia = _noticia()
        data = data_noticia(noticia.data_publicacao, _REFERENCIA)
        cache = NoticiasCache(tmp_path)
        NoticiasIndexStore(cache_dir=tmp_path).registrar(
            cache.caminho(chave_noticia(noticia), data),
            NoticiaMeta(
                secao=SECAO_GERAL,
                titulo=noticia.titulo,
                data_publicacao=noticia.data_publicacao,
                categoria="18",
                url=noticia.url,
            ),
        )
        assert NoticiasCatalog(cache_dir=tmp_path).arquivos() == []

    def test_preserva_metadados_da_noticia(self, tmp_path):
        noticia = _noticia()
        _catalogado(tmp_path, noticia)
        arquivo = NoticiasCatalog(cache_dir=tmp_path).arquivos()[0]
        assert arquivo.ticker == ESCOPO_NOTICIAS
        assert arquivo.url == noticia.url
        assert arquivo.data_publicacao == noticia.data_publicacao
        assert arquivo.categoria == "Negociação"

    def test_enriquece_resumos(self, tmp_path):
        noticia = _noticia()
        relativo = _catalogado(tmp_path, noticia)
        JsonDocumentSummaryStore(cache_dir=tmp_path).salvar(
            ESCOPO_NOTICIAS, relativo, "curto", "longo"
        )
        catalogo = NoticiasCatalog(cache_dir=tmp_path)
        arquivo = catalogo.arquivos()[0]
        assert arquivo.short_summary == "curto"
        assert arquivo.long_summary == "longo"
        assert catalogo.chave(arquivo) == relativo

    def test_cache_frio_retorna_vazio(self, tmp_path):
        catalogo = NoticiasCatalog(cache_dir=tmp_path)
        assert catalogo.arquivos() == []
        assert catalogo.secoes().vazio is True

    def test_indice_corrompido_retorna_vazio(self, tmp_path):
        indice = NoticiasIndexStore(cache_dir=tmp_path).path
        indice.parent.mkdir(parents=True, exist_ok=True)
        indice.write_text("{ nao é json", encoding="utf-8")
        assert NoticiasCatalog(cache_dir=tmp_path).secoes().vazio is True

    def test_catalogo_agrupa_por_ano_e_mes(self, tmp_path):
        noticia = _noticia()
        _catalogado(tmp_path, noticia)
        catalogo = NoticiasCatalog(cache_dir=tmp_path).secoes()
        assert catalogo.titulo == TITULO_NOTICIAS
        assert catalogo.vazio is False
        secao = next(s for s in catalogo.secoes if s.catalogo.anos)
        assert secao.nome == SECAO_GERAL
        ano = secao.catalogo.anos[0]
        assert ano.ano == 2026
        assert ano.meses[0].mes == 9
        assert ano.meses[0].categorias[0].nome == "Negociação"
        assert len(ano.meses[0].categorias[0].arquivos) == 1

    def test_titulo_sem_tipo_usa_outros(self, tmp_path):
        noticia = _noticia(
            titulo="EMISSOR - Comunicado sem evento típico", url="https://x/2"
        )
        _catalogado(tmp_path, noticia)
        arquivo = NoticiasCatalog(cache_dir=tmp_path).arquivos()[0]
        assert arquivo.categoria == "Outros"


def _censura():
    return CensuraPublica(
        titulo="FII TORDE EI (TORD)",
        ticker="TORD",
        data="25/02/2026",
        conteudo="Corpo da censura.",
    )


def _condicao():
    return CondicaoExcepcional(
        companhia="Bradsaúde S.A.",
        segmento="Novo Mercado",
        condicao="Percentual mínimo abaixo do requerido",
        data_concessao="19/05/2026",
        prazo="30/10/2027",
    )


def _programa():
    return ProgramaAquisicao(
        empresa="3TENTOS (NM)",
        data_aprovacao="13/08/2026",
        data_inicio="13/08/2026",
        data_fim="13/02/2028",
        quantidade="5.000.000 (ON)",
        intermediarios="Bradesco",
    )


class TestSecoesRegulatorias:
    def test_catalogo_traz_as_tres_categorias_regulatorias(self, tmp_path):
        for item in (
            item_de_censura(_censura()),
            item_de_condicao(_condicao()),
            item_de_programa(_programa()),
        ):
            _registrar(tmp_path, item)
        catalogo = NoticiasCatalog(cache_dir=tmp_path).secoes()

        assert catalogo.vazio is False
        assert catalogo.secoes[-1].nome == SECAO_GERAL
        assert catalogo.secoes[-1].catalogo.anos == ()
        nomes = [secao.nome for secao in catalogo.secoes if secao.catalogo.anos]
        assert nomes == [SECAO_CENSURAS, SECAO_CONDICOES, SECAO_PROGRAMAS]

    def test_categoria_do_terceiro_nivel_por_fonte(self, tmp_path):
        for item in (
            item_de_censura(_censura()),
            item_de_condicao(_condicao()),
            item_de_programa(_programa()),
        ):
            _registrar(tmp_path, item)
        catalogo = NoticiasCatalog(cache_dir=tmp_path).secoes()

        def _categoria(nome):
            secao = next(s for s in catalogo.secoes if s.nome == nome)
            return secao.catalogo.anos[0].meses[0].categorias[0].nome

        assert _categoria(SECAO_CENSURAS) == "TORD"
        assert _categoria(SECAO_CONDICOES) == "Novo Mercado"
        assert _categoria(SECAO_PROGRAMAS) == "3TENTOS (NM)"

    def test_arquivo_regulatorio_sem_url(self, tmp_path):
        _registrar(tmp_path, item_de_censura(_censura()))
        arquivo = NoticiasCatalog(cache_dir=tmp_path).arquivos()[0]
        assert arquivo.secao == SECAO_CENSURAS
        assert arquivo.url is None
        assert arquivo.ticker == ESCOPO_NOTICIAS
        assert arquivo.caminho.is_file()
