"""Testes puros da aplicação da fatia de Notícias."""

from datetime import date
from pathlib import Path

from flowscope.application.noticias.catalogo import (
    ConsultarCatalogoNoticiasUseCase,
    montar_secoes,
)
from flowscope.application.noticias.fonte_chat import (
    NoticiaEscopo,
    chave_curta,
    intercalar,
    montar_indice,
)
from flowscope.application.noticias.lote import pendentes_ordenados
from flowscope.domain.noticias import (
    SECAO_CENSURAS,
    SECAO_CONDICOES,
    SECAO_GERAL,
    SECAO_PROGRAMAS,
    NoticiaArquivo,
)
from flowscope.infrastructure.b3.noticias_aquisicao import data_noticia

_REFERENCIA = date(2026, 9, 25)


def _arq_noticia(
    secao: str,
    nome: str,
    data: str = "",
    *,
    ano: int = 2026,
    mes: int = 9,
    categoria: str = "cat",
    resumo: str | None = None,
) -> NoticiaArquivo:
    return NoticiaArquivo(
        ticker="NOTICIAS",
        ano=ano,
        mes=mes,
        categoria=categoria,
        nome=nome,
        tipo="html",
        caminho=Path(f"/tmp/{nome}"),
        long_summary=resumo,
        url="https://x/1",
        data_publicacao=data,
        secao=secao,
        data_ordinal=data_noticia(
            data,
            date(max(ano, 1), mes if 1 <= mes <= 12 else 1, 1),
        ).toordinal(),
    )


class TestOrdenacaoDoLote:
    def test_ordena_por_grupo_e_data_decrescente(self):
        arquivos = [
            _arq_noticia(SECAO_GERAL, "g_old", "2026-01-05"),
            _arq_noticia(SECAO_CENSURAS, "c_old", "2026-02-01"),
            _arq_noticia(SECAO_GERAL, "g_new", "2026-09-20 10:00:00"),
            _arq_noticia(SECAO_CENSURAS, "c_new", "2026-08-01"),
            _arq_noticia(SECAO_PROGRAMAS, "p", "2026-05-05"),
            _arq_noticia(SECAO_CONDICOES, "co", "2026-03-03"),
            _arq_noticia(SECAO_GERAL, "g_resumido", resumo="x"),
        ]
        nomes = [a.nome for a in pendentes_ordenados(arquivos)]
        assert nomes == ["c_new", "c_old", "co", "p", "g_new", "g_old"]

    def test_data_ausente_ou_empatada_tem_ordem_estavel(self):
        arquivos = [
            _arq_noticia(SECAO_GERAL, "sem_data", "", ano=2025, mes=3, categoria="B"),
            _arq_noticia(SECAO_GERAL, "iso_data", "2026-09-20"),
            _arq_noticia(SECAO_GERAL, "iso_data_hora", "2026-09-20 10:00:00"),
            _arq_noticia(SECAO_GERAL, "empate_a", "2026-09-20", categoria="A"),
            _arq_noticia(SECAO_GERAL, "invalida", "not-a-date", ano=2024, mes=1),
        ]
        primeira = [a.nome for a in pendentes_ordenados(arquivos)]
        segunda = [a.nome for a in pendentes_ordenados(arquivos)]
        assert primeira == segunda
        assert primeira == [
            "empate_a",
            "iso_data",
            "iso_data_hora",
            "sem_data",
            "invalida",
        ]


class TestMontarSecoes:
    def test_agrupa_por_secao_na_ordem_fixa(self):
        catalogo = montar_secoes(
            [
                _arq_noticia(SECAO_GERAL, "g", "2026-09-20", categoria="Negociação"),
                _arq_noticia(SECAO_CENSURAS, "c", "2026-02-01", categoria="TORD"),
            ]
        )
        nomes = [secao.nome for secao in catalogo.secoes]
        assert nomes == list(
            (SECAO_CENSURAS, SECAO_CONDICOES, SECAO_PROGRAMAS, SECAO_GERAL)
        )
        assert catalogo.vazio is False

    def test_agrupa_ano_mes_categoria(self):
        catalogo = montar_secoes(
            [_arq_noticia(SECAO_GERAL, "g", categoria="Negociação")]
        )
        secao = next(s for s in catalogo.secoes if s.nome == SECAO_GERAL)
        assert secao.catalogo.anos[0].ano == 2026
        assert secao.catalogo.anos[0].meses[0].mes == 9
        assert secao.catalogo.anos[0].meses[0].categorias[0].nome == "Negociação"


class TestConsultarCatalogoUseCase:
    def test_delega_ao_repositorio(self):
        arquivo = _arq_noticia(SECAO_GERAL, "g")

        class _Repositorio:
            def __init__(self):
                self.chamadas = 0

            def arquivos(self):
                self.chamadas += 1
                return [arquivo]

            def chave(self, item):
                return f"noticias/{item.nome}"

        repositorio = _Repositorio()
        caso = ConsultarCatalogoNoticiasUseCase(repositorio)
        assert caso.arquivos() == [arquivo]
        assert caso.chave(arquivo) == "noticias/g"


class TestMontarIndice:
    def _escopo(self, secao: str, nome: str, ordinal: int) -> NoticiaEscopo:
        return NoticiaEscopo(
            secao=secao,
            nome=nome,
            data_publicacao="2026-09-20",
            categoria="Negociação",
            chave=f"noticias/2026/09/{nome}.html",
            caminho=Path(f"/tmp/{nome}.html"),
            data_ordinal=ordinal,
        )

    def test_indice_inclui_secao_data_tipo_titulo_e_chave(self):
        escopo = self._escopo(SECAO_GERAL, "g", 100)
        texto = montar_indice([escopo])
        assert "[Geral]" in texto
        assert "2026-09-20" in texto
        assert "Negociação" in texto
        assert escopo.chave_curta in texto

    def test_chave_curta_estavel(self):
        assert chave_curta("abc") == chave_curta("abc")
        assert chave_curta("abc").startswith("n")

    def test_intercala_todas_as_secoes(self):
        escopos = [
            self._escopo(SECAO_CENSURAS, "c_old", 100),
            self._escopo(SECAO_CENSURAS, "c_new", 300),
            self._escopo(SECAO_CONDICOES, "co", 200),
            self._escopo(SECAO_PROGRAMAS, "p", 150),
            self._escopo(SECAO_GERAL, "g", 400),
        ]
        primeira_rodada = intercalar(escopos)[:4]
        assert [e.secao for e in primeira_rodada] == [
            SECAO_CENSURAS,
            SECAO_CONDICOES,
            SECAO_PROGRAMAS,
            SECAO_GERAL,
        ]
        # Dentro da seção, o mais recente vem primeiro.
        assert intercalar(escopos)[0].nome == "c_new"
