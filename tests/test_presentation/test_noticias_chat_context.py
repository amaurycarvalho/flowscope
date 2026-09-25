"""Testes da fonte de notícias como contexto adicional do chat.

O catálogo é somente-leitura do cache local: os itens são gravados com o HTML e
registrados no índice de metadados, sem qualquer consulta à B3.
"""

from datetime import date

from flowscope.application.chat import ContextoChat, ConsultarChatUseCase, FonteContexto
from flowscope.domain.structured import CensuraPublica, NoticiaB3
from flowscope.infrastructure.b3.noticias_aquisicao import (
    ESCOPO_NOTICIAS,
    SECAO_CENSURAS,
    SECAO_GERAL,
    NoticiasCache,
    chave_item,
    chave_noticia,
    classificar_tipo,
    data_noticia,
    html_do_item,
    item_de_censura,
)
from flowscope.infrastructure.b3.noticias_catalogo import NoticiasCatalog
from flowscope.infrastructure.b3.noticias_index import (
    NoticiaMeta,
    NoticiasIndexStore,
)
from flowscope.infrastructure.document_summaries import JsonDocumentSummaryStore
from flowscope.infrastructure.document_texts import JsonDocumentTextStore
from flowscope.presentation.gui.chat.noticias import TITULO_FONTE, FonteNoticias

_REFERENCIA = date(2026, 9, 25)

_TITULO = "PETROBRAS (PETR4) - Suspensão de negociação - 20/09/26"


def _noticia(titulo=_TITULO, url="https://x/1"):
    return NoticiaB3(
        titulo=titulo,
        data_publicacao="2026-09-20 10:00:00",
        url=url,
        agencia="18",
    )


def _catalogo(tmp_path, noticias):
    """Grava o HTML e o índice das notícias e devolve o catálogo cache-only."""
    cache = NoticiasCache(tmp_path)
    indice = NoticiasIndexStore(cache_dir=tmp_path)
    for noticia in noticias:
        data = data_noticia(noticia.data_publicacao, _REFERENCIA)
        chave = chave_noticia(noticia)
        html = f"<html><body><pre>Corpo {noticia.titulo}</pre></body></html>"
        cache.gravar(chave, data, html.encode("utf-8"))
        indice.registrar(
            cache.caminho(chave, data),
            NoticiaMeta(
                secao=SECAO_GERAL,
                titulo=noticia.titulo,
                data_publicacao=noticia.data_publicacao,
                categoria=classificar_tipo(noticia.titulo),
                url=noticia.url,
            ),
        )
    return NoticiasCatalog(cache_dir=tmp_path)


def _registrar_item(tmp_path, item) -> None:
    cache = NoticiasCache(tmp_path)
    data = data_noticia(item.data_publicacao, _REFERENCIA)
    chave = chave_item(item)
    cache.gravar(chave, data, html_do_item(item))
    NoticiasIndexStore(cache_dir=tmp_path).registrar(
        cache.caminho(chave, data),
        NoticiaMeta(
            secao=item.secao,
            titulo=item.titulo,
            data_publicacao=item.data_publicacao,
            categoria=item.categoria,
            url=item.url,
        ),
    )


def _fonte(tmp_path, noticias, **kwargs):
    return FonteNoticias(
        catalog=_catalogo(tmp_path, noticias),
        reference_date_provider=lambda: _REFERENCIA,
        **kwargs,
    )


class TestFonteNoticias:
    def test_inclui_titulo_data_tipo_e_texto(self, tmp_path):
        fonte = _fonte(tmp_path, [_noticia()])
        resultado = fonte("Qualquer pergunta")
        assert isinstance(resultado, FonteContexto)
        assert resultado.titulo == TITULO_FONTE
        assert _TITULO in resultado.texto
        assert "2026-09-20" in resultado.texto
        assert "Negociação" in resultado.texto
        assert f"Corpo {_TITULO}" in resultado.texto

    def test_prefere_resumo_longo(self, tmp_path):
        noticia = _noticia()
        catalogo = _catalogo(tmp_path, [noticia])
        chave = f"noticias/2026/09/{chave_noticia(noticia)}.html"
        JsonDocumentSummaryStore(cache_dir=tmp_path).salvar(
            ESCOPO_NOTICIAS, chave, "resumo curto", "resumo longo"
        )
        fonte = FonteNoticias(
            catalog=catalogo, reference_date_provider=lambda: _REFERENCIA
        )
        resultado = fonte("pergunta")
        assert "resumo longo" in resultado.texto
        assert "Corpo PETROBRAS" not in resultado.texto

    def test_usa_texto_cacheado_quando_sem_resumo(self, tmp_path):
        noticia = _noticia()
        catalogo = _catalogo(tmp_path, [noticia])
        chave = f"noticias/2026/09/{chave_noticia(noticia)}.html"
        texto_store = JsonDocumentTextStore(cache_dir=tmp_path)
        texto_store.salvar(ESCOPO_NOTICIAS, chave, "texto cacheado")
        fonte = FonteNoticias(
            catalog=catalogo,
            text_store=texto_store,
            reference_date_provider=lambda: _REFERENCIA,
        )
        assert "texto cacheado" in fonte("pergunta").texto

    def test_cache_frio_retorna_none(self, tmp_path):
        catalogo = NoticiasCatalog(cache_dir=tmp_path)
        fonte = FonteNoticias(
            catalog=catalogo, reference_date_provider=lambda: _REFERENCIA
        )
        assert fonte("pergunta") is None

    def test_nao_filtra_por_ticker_na_pergunta(self, tmp_path):
        fonte = _fonte(tmp_path, [_noticia()])
        assert fonte("O que saiu sobre PETR4?").texto == fonte(
            "Como está o mercado?"
        ).texto

    def test_respeita_teto_de_caracteres(self, tmp_path):
        noticias = [
            _noticia(
                titulo=f"Notícia {indice} - Suspensão de negociação",
                url=f"https://x/{indice}",
            )
            for indice in range(20)
        ]
        fonte = _fonte(tmp_path, noticias, teto=200)
        assert len(fonte("pergunta").texto) <= 200


class TestPromptDoChat:
    def test_fonte_vira_secao_do_prompt(self, tmp_path):
        fonte = _fonte(tmp_path, [_noticia()])
        resultado = fonte("O que saiu sobre PETR4?")
        contexto = ContextoChat(fontes_adicionais=[resultado])
        prompt = ConsultarChatUseCase._montar_prompt("O que saiu?", contexto, None)
        assert f"## {TITULO_FONTE}" in prompt
        assert _TITULO in prompt
        assert "## Pergunta" in prompt


class TestSecaoRegulatoriaNoChat:
    def test_censura_entra_no_contexto(self, tmp_path):
        censura = CensuraPublica(
            titulo="FII TORDE EI (TORD)",
            ticker="TORD",
            data="25/02/2026",
            conteudo="Corpo da censura.",
        )
        _registrar_item(tmp_path, item_de_censura(censura))

        catalogo = NoticiasCatalog(cache_dir=tmp_path)
        fonte = FonteNoticias(
            catalog=catalogo, reference_date_provider=lambda: _REFERENCIA
        )
        resultado = fonte("pergunta")
        assert resultado is not None
        assert SECAO_CENSURAS in resultado.texto
        assert "Corpo da censura." in resultado.texto
