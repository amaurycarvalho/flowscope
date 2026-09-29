"""Testes da fonte de notícias como contexto adicional do chat.

A fonte opera em duas camadas: um índice compacto de todos os itens (1ª) e a
leitura do resumo/texto integral sob demanda pelas chaves (2ª). O catálogo é
somente-leitura do cache local, sem qualquer consulta à B3.
"""

import re
from datetime import date
from types import SimpleNamespace

from flowscope.application.chat import (
    ConsultarChatUseCase,
    ContextoChat,
    FonteContexto,
    MontarContextoChat,
)
from flowscope.domain.structured import CensuraPublica, NoticiaB3
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
    classificar_tipo,
    data_noticia,
    html_do_item,
    item_de_censura,
    item_de_noticia,
)
from flowscope.infrastructure.b3.noticias_catalogo import NoticiasCatalog
from flowscope.infrastructure.b3.noticias_index import (
    NoticiaMeta,
    NoticiasIndexStore,
)
from flowscope.infrastructure.document_summaries import JsonDocumentSummaryStore
from flowscope.infrastructure.document_texts import JsonDocumentTextStore
from flowscope.application.document_preview import texto_preview
from flowscope.application.chat.noticias import TITULO_FONTE, FonteNoticias

_REFERENCIA = date(2026, 9, 25)

_TITULO = "PETROBRAS (PETR4) - Suspensão de negociação - 20/09/26"

_CHAVE = re.compile(r"\(chave: (n[0-9a-f]+)\)")


def _noticia(titulo=_TITULO, url="https://x/1"):
    return NoticiaB3(
        titulo=titulo,
        data_publicacao="2026-09-20 10:00:00",
        url=url,
        agencia="18",
    )


def _semear_textos(catalogo: NoticiasCatalog, tmp_path) -> None:
    """Grava o texto cacheado de todos os itens do catálogo."""
    store = JsonDocumentTextStore(cache_dir=tmp_path)
    for arquivo in catalogo.arquivos():
        store.salvar(
            ESCOPO_NOTICIAS,
            catalogo.chave(arquivo),
            texto_preview(arquivo.caminho),
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
    catalogo = NoticiasCatalog(cache_dir=tmp_path)
    _semear_textos(catalogo, tmp_path)
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
    catalogo = NoticiasCatalog(cache_dir=tmp_path)
    _semear_textos(catalogo, tmp_path)


def _fonte(tmp_path, noticias, **kwargs):
    return FonteNoticias(
        catalog=_catalogo(tmp_path, noticias),
        reference_date_provider=lambda: _REFERENCIA,
        **kwargs,
    )


def _chave_do_indice(texto: str) -> str:
    """Extrai a primeira chave curta exibida no índice."""
    encontrado = _CHAVE.search(texto)
    assert encontrado is not None, f"chave não encontrada em: {texto!r}"
    return encontrado.group(1)


def _seed_apontador(tmp_path, *, resolvido: bool = False) -> NoticiasCatalog:
    """Grava uma notícia "Geral" cujo corpo é um apontador da CVM RAD."""
    cache = NoticiasCache(tmp_path)
    indice = NoticiasIndexStore(cache_dir=tmp_path)
    noticia = NoticiaB3(
        titulo="VALE (VALE-NM) - Esclarecimentos de questionamentos CVM/B3- 22/09/26",
        data_publicacao="2026-09-22 10:00:00",
        url="https://sistemasweb.b3.com.br/x",
        agencia="18",
    )
    data = data_noticia(noticia.data_publicacao, _REFERENCIA)
    chave = chave_noticia(noticia)
    html = (
        "<html><body><pre id='conteudoDetalhe'>"
        "VALE (VALE-NM) - Esclarecimentos\n\n"
        "https://www.rad.cvm.gov.br/ENETWEB/frmExibirArquivoIPEExterno.aspx"
        "?ID=1570300&flnk\n\n(R) = Reapresentacao</pre></body></html>"
    )
    cache.gravar(chave, data, html.encode("utf-8"))
    caminho = cache.caminho(chave, data)
    indice.registrar(
        caminho,
        NoticiaMeta(
            secao=SECAO_GERAL,
            titulo=noticia.titulo,
            data_publicacao=noticia.data_publicacao,
            categoria=classificar_tipo(noticia.titulo),
            url=noticia.url,
        ),
    )
    if resolvido:
        catalogo = NoticiasCatalog(cache_dir=tmp_path)
        JsonDocumentTextStore(cache_dir=tmp_path).salvar(
            ESCOPO_NOTICIAS,
            catalogo.chave(catalogo.arquivos()[0]),
            "CONTEUDO DO DOCUMENTO DA VALE",
        )
    return NoticiasCatalog(cache_dir=tmp_path)


class TestIndice:
    def test_indice_inclui_secao_data_tipo_e_chave(self, tmp_path):
        fonte = _fonte(tmp_path, [_noticia()])
        resultado = fonte("O que saiu sobre PETR4?")
        assert isinstance(resultado, FonteContexto)
        assert resultado.titulo == TITULO_FONTE
        texto = resultado.texto
        assert _TITULO in texto
        assert "2026-09-20" in texto
        assert "Negociação" in texto
        assert "[Geral]" in texto
        assert "chave: " in texto
        assert "Corpo" not in texto

    def test_indice_cobre_todas_as_secoes(self, tmp_path):
        itens = [
            ItemNoticia(
                secao=SECAO_CENSURAS,
                chave_base="c1",
                titulo="Censura A",
                data_publicacao="2026-01-01",
                categoria="TORD",
                conteudo="x",
            ),
            ItemNoticia(
                secao=SECAO_CONDICOES,
                chave_base="d1",
                titulo="Condicao A",
                data_publicacao="2026-01-01",
                categoria="Segmento",
                conteudo="x",
            ),
            ItemNoticia(
                secao=SECAO_PROGRAMAS,
                chave_base="p1",
                titulo="Programa A",
                data_publicacao="2026-01-01",
                categoria="Empresa",
                conteudo="x",
            ),
            item_de_noticia(_noticia()),
        ]
        for item in itens:
            _registrar_item(tmp_path, item)
        fonte = FonteNoticias(
            catalog=NoticiasCatalog(cache_dir=tmp_path),
            reference_date_provider=lambda: _REFERENCIA,
            teto=900,
        )
        texto = fonte("").texto
        for secao in (SECAO_CENSURAS, SECAO_CONDICOES, SECAO_PROGRAMAS, SECAO_GERAL):
            assert f"[{secao}]" in texto

    def test_cache_frio_retorna_none(self, tmp_path):
        catalogo = NoticiasCatalog(cache_dir=tmp_path)
        fonte = FonteNoticias(
            catalog=catalogo, reference_date_provider=lambda: _REFERENCIA
        )
        assert fonte("pergunta") is None

    def test_respeita_teto_de_caracteres(self, tmp_path):
        noticias = [
            _noticia(
                titulo=f"Notícia {indice} - Suspensão de negociação",
                url=f"https://x/{indice}",
            )
            for indice in range(20)
        ]
        fonte = _fonte(tmp_path, noticias, teto=200)
        assert len(fonte("suspensão").texto) <= 200


class TestRecuperaveis:
    def test_item_sem_resumo_e_sem_texto_e_omitido(self, tmp_path):
        catalogo = NoticiasCatalog(cache_dir=tmp_path)
        fonte = FonteNoticias(
            catalog=catalogo, reference_date_provider=lambda: _REFERENCIA
        )
        assert fonte("PETR4") is None

    def test_item_so_com_resumo_e_recuperavel(self, tmp_path):
        noticia = _noticia()
        catalogo = _catalogo(tmp_path, [noticia])
        chave = f"noticias/2026/09/{chave_noticia(noticia)}.html"
        JsonDocumentSummaryStore(cache_dir=tmp_path).salvar(
            ESCOPO_NOTICIAS, chave, "resumo curto", "resumo longo"
        )
        JsonDocumentTextStore(cache_dir=tmp_path).salvar(
            ESCOPO_NOTICIAS, chave, ""
        )
        fonte = FonteNoticias(
            catalog=catalogo, reference_date_provider=lambda: _REFERENCIA
        )
        assert fonte("PETR4") is not None


class TestFiltroDeterministico:
    def test_filtra_por_ticker(self, tmp_path):
        noticias = [
            _noticia(titulo="PETROBRAS (PETR4) - Suspensão", url="https://x/1"),
            _noticia(titulo="VALE (VALE3) - Suspensão", url="https://x/2"),
        ]
        fonte = _fonte(tmp_path, noticias)
        texto = fonte("O que saiu sobre PETR4?").texto
        assert "PETR4" in texto
        assert "VALE3" not in texto

    def test_filtra_por_palavra_chave(self, tmp_path):
        noticias = [
            _noticia(titulo="Empresa A - Suspensão de negociação", url="https://x/1"),
            _noticia(titulo="Empresa B - Recuperação judicial", url="https://x/2"),
        ]
        fonte = _fonte(tmp_path, noticias)
        texto = fonte("Houve recuperação judicial?").texto
        assert "Recuperação" in texto
        assert "Suspensão" not in texto

    def test_sem_casamento_omite_secao(self, tmp_path):
        fonte = _fonte(tmp_path, [_noticia()])
        assert fonte("Qual o dividendo do FII?") is None

    def test_pergunta_vazia_nao_filtra(self, tmp_path):
        fonte = _fonte(tmp_path, [_noticia()])
        assert fonte("") is not None

    def test_termos_extraidos_da_pergunta(self):
        from flowscope.application.noticias.fonte_chat import termos_da_pergunta

        termos = termos_da_pergunta("O que saiu sobre PETR4 e a suspensão?")
        assert "petr4" in termos
        assert "suspensao" in termos
        assert "sobre" not in termos

    def test_estimar_tokens(self):
        from flowscope.application.noticias.fonte_chat import estimar_tokens

        assert estimar_tokens("a" * 2400) == 600


class TestGateConfirmacao:
    def _fonte_com_noticias(self, tmp_path, limite_envio, confirmar):
        noticias = [
            _noticia(titulo=f"PETROBRAS (PETR4) - Suspensão {i}", url=f"https://x/{i}")
            for i in range(5)
        ]
        return _fonte(
            tmp_path,
            noticias,
            limite_envio=limite_envio,
            confirmar=confirmar,
        )

    def test_abaixo_do_limite_nao_confirma(self, tmp_path):
        chamadas: list = []
        fonte = self._fonte_com_noticias(
            tmp_path, 100000, lambda q, nomes: chamadas.append(q) or True
        )
        assert fonte("PETR4") is not None
        assert chamadas == []

    def test_acima_do_limite_confirma(self, tmp_path):
        chamadas: list = []

        def confirmar(quantidade, nomes):
            chamadas.append((quantidade, nomes))
            return True

        fonte = self._fonte_com_noticias(tmp_path, 1, confirmar)
        assert fonte("PETR4") is not None
        assert chamadas and chamadas[0][0] == 5

    def test_recusa_omite_secao(self, tmp_path):
        fonte = self._fonte_com_noticias(tmp_path, 1, lambda q, nomes: False)
        assert fonte("PETR4") is None


class TestConteudoIntegral:
    def test_le_o_texto_por_chave(self, tmp_path):
        fonte = _fonte(tmp_path, [_noticia()])
        chave = _chave_do_indice(fonte("PETR4").texto)
        alvos = fonte.resolver_alvos([chave])
        assert len(alvos) == 1
        conteudo = fonte.preparar_texto(alvos)
        assert _TITULO in conteudo
        assert "Corpo PETROBRAS" in conteudo

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
        conteudo = fonte.preparar_texto(
            fonte.resolver_alvos([_chave_do_indice(fonte("PETR4").texto)])
        )
        assert "Resumo: resumo longo" in conteudo

    def test_usa_texto_cacheado(self, tmp_path):
        noticia = _noticia()
        catalogo = _catalogo(tmp_path, [noticia])
        chave = f"noticias/2026/09/{chave_noticia(noticia)}.html"
        JsonDocumentTextStore(cache_dir=tmp_path).salvar(
            ESCOPO_NOTICIAS, chave, "texto cacheado resolvido"
        )
        fonte = FonteNoticias(
            catalog=catalogo, reference_date_provider=lambda: _REFERENCIA
        )
        conteudo = fonte.preparar_texto(
            fonte.resolver_alvos([_chave_do_indice(fonte("PETR4").texto)])
        )
        assert "texto cacheado resolvido" in conteudo

    def test_apontador_nao_baixado_e_omitido(self, tmp_path):
        fonte = FonteNoticias(
            catalog=_seed_apontador(tmp_path),
            reference_date_provider=lambda: _REFERENCIA,
        )
        assert fonte("VALE") is None

    def test_documento_resolvido_e_entregue(self, tmp_path):
        fonte = FonteNoticias(
            catalog=_seed_apontador(tmp_path, resolvido=True),
            reference_date_provider=lambda: _REFERENCIA,
        )
        conteudo = fonte.preparar_texto(
            fonte.resolver_alvos([_chave_do_indice(fonte("VALE").texto)])
        )
        assert "CONTEUDO DO DOCUMENTO DA VALE" in conteudo
        assert "rad.cvm.gov.br" not in conteudo


class TestPromptDoChat:
    def test_fonte_vira_secao_do_prompt(self, tmp_path):
        fonte = _fonte(tmp_path, [_noticia()])
        resultado = fonte("O que saiu sobre PETR4?")
        contexto = ContextoChat(fontes_adicionais=[resultado])
        sufixo = ConsultarChatUseCase._montar_sufixo(
            "O que saiu?", contexto.fontes_adicionais, None
        )
        assert f"## {TITULO_FONTE}" in sufixo
        assert _TITULO in sufixo
        assert "## Pergunta" in sufixo


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
        resultado = fonte("TORD")
        assert resultado is not None
        assert SECAO_CENSURAS in resultado.texto
        conteudo = fonte.preparar_texto(
            fonte.resolver_alvos([_chave_do_indice(resultado.texto)])
        )
        assert "Corpo da censura." in conteudo


class _CascataVazia:
    def resolver_alvos(self, chaves):
        return []

    def preparar_texto(self, alvos):
        return ""


class TestEscalonamentoNoPainel:
    @staticmethod
    def _montador(cascata, fontes, confirmar=None):
        return MontarContextoChat(
            cascata=cascata,
            fontes_adicionais=fontes,
            confirmar=confirmar or (lambda quantidade, nomes: True),
        )

    def test_soma_documentos_e_noticias(self, tmp_path):
        fonte = _fonte(tmp_path, [_noticia()])

        class _Cascata:
            def resolver_alvos(self, chaves):
                if "doc1" in chaves:
                    return [SimpleNamespace(chave="doc1", nome="Doc 1")]
                return []

            def preparar_texto(self, alvos):
                return "conteudo do documento"

        montador = self._montador(_Cascata(), [fonte])
        chave = _chave_do_indice(fonte("PETR4").texto)
        texto = montador.preparar_texto(["doc1", chave])
        assert "conteudo do documento" in texto
        assert "Corpo PETROBRAS" in texto

    def test_confirmacao_conta_noticias(self, tmp_path):
        noticias = [
            _noticia(
                titulo=f"N{i} - Suspensão de negociação", url=f"https://x/{i}"
            )
            for i in range(4)
        ]
        fonte = _fonte(tmp_path, noticias)
        chaves = _CHAVE.findall(fonte("suspensão").texto)
        chamadas: list[tuple] = []

        def _confirmar(quantidade, nomes):
            chamadas.append((quantidade, nomes))
            return True

        montador = self._montador(_CascataVazia(), [fonte], confirmar=_confirmar)
        assert montador.confirmar_leitura(chaves) is True
        assert chamadas and chamadas[0][0] == 4
