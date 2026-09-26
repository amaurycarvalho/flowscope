"""Testes da aquisição e do cache do corpo das notícias do Plantão B3."""

from datetime import date, timedelta

import pytest
import requests
import responses

from flowscope.application.cancellation import (
    CancellationToken,
    OperacaoCancelada,
)
from flowscope.domain.structured import (
    CensuraPublica,
    CondicaoExcepcional,
    NoticiaB3,
    ProgramaAquisicao,
)
from flowscope.infrastructure.b3.noticias_aquisicao import (
    _LOTE_INDICE,
    DIAS_LOTE,
    DIAS_PERIODO,
    ESCOPO_NOTICIAS,
    SECAO_CENSURAS,
    SECAO_CONDICOES,
    SECAO_GERAL,
    SECAO_PROGRAMAS,
    NoticiasCache,
    baixar_noticia,
    chave_item,
    chave_noticia,
    data_noticia,
    item_de_censura,
    itens_de_janela,
    janelas_geral,
    listar_itens,
    listar_periodo,
)
from flowscope.infrastructure.b3.noticias_carga import AquisicaoNoticias
from flowscope.infrastructure.b3.noticias_catalogo import NoticiasCatalog
from flowscope.infrastructure.b3.noticias_index import NoticiasIndexStore
from flowscope.domain.noticias import (
    TERMOS_EXCEPCIONAIS,
    TIPO_OUTROS,
    TIPOS_NOTICIA,
    classificar_tipo,
    noticia_excepcional,
)
from flowscope.infrastructure.cache import CacheManager

_REFERENCIA = date(2026, 9, 25)
_URL = "https://sistemasweb.b3.com.br/PlantaoNoticias/Noticias/Detail?idNoticia=1"
_TITULO_EXCEPCIONAL = "PETROBRAS (PETR4) - Suspensão de negociação - 20/09/26"
_TITULO_ROTINEIRO = "PETROBRAS (PETR4) - Outros Comunicados ao Mercado - 20/09/26"


class _RepositorioFake:
    def __init__(self, noticias=None, erro=False):
        self._noticias = list(noticias or [])
        self._erro = erro
        self.janelas: list[tuple] = []

    def listar_noticias(
        self, agencia="18", data_inicio=None, data_fim=None, palavra=None
    ):
        self.janelas.append((data_inicio, data_fim, palavra))
        if self._erro:
            raise requests.ConnectionError("offline")
        return list(self._noticias)


def _noticia(
    titulo=_TITULO_EXCEPCIONAL,
    data_publicacao="2026-09-20 10:00:00",
    url=_URL,
    agencia="18",
) -> NoticiaB3:
    return NoticiaB3(
        titulo=titulo,
        data_publicacao=data_publicacao,
        url=url,
        agencia=agencia,
    )


def _aquisicao(tmp_path, repositorio, baixar):
    return AquisicaoNoticias(
        repository=repositorio,
        cache=CacheManager(cache_dir=tmp_path),
        baixar=baixar,
    )


class TestChaveNoticia:
    def test_url_produz_chave_estavel(self):
        assert chave_noticia(_noticia()) == chave_noticia(_noticia())
        assert chave_noticia(_noticia()) != chave_noticia(_noticia(url="https://x/2"))

    def test_sem_url_usa_data_agencia_titulo(self):
        noticia = _noticia(url=None)
        outra = _noticia(url=None)
        assert chave_noticia(noticia) == chave_noticia(outra)
        assert chave_noticia(noticia) != chave_noticia(
            _noticia(url=None, titulo="Outro titulo")
        )


class TestDataNoticia:
    def test_iso_com_horario(self):
        assert data_noticia("2026-09-20 10:00:00", _REFERENCIA) == date(2026, 9, 20)

    def test_formato_brasileiro(self):
        assert data_noticia("20/09/2026", _REFERENCIA) == date(2026, 9, 20)

    def test_invalida_usa_fallback(self):
        assert data_noticia("", _REFERENCIA) == _REFERENCIA
        assert data_noticia("sem data", _REFERENCIA) == _REFERENCIA


class TestDiasGeral:
    def test_primeiro_dia_sempre_presente(self):
        janelas = janelas_geral(_REFERENCIA)
        assert janelas[0] == (_REFERENCIA, _REFERENCIA)

    def test_cobre_um_ano_dia_a_dia(self):
        janelas = janelas_geral(_REFERENCIA)
        limite = _REFERENCIA - timedelta(days=DIAS_PERIODO - 1)
        assert janelas[-1][0] == limite
        assert janelas[0][1] == _REFERENCIA
        assert all(inicio == fim for inicio, fim in janelas)
        # dias contíguos, do mais recente ao mais antigo, sem sobreposição
        for atual, seguinte in zip(janelas, janelas[1:]):
            assert seguinte[1] == atual[0] - timedelta(days=1)

    def test_marcador_completo_pula_lotes_antigos(self):
        completo = janelas_geral(_REFERENCIA)
        limite = _REFERENCIA - timedelta(days=DIAS_PERIODO - 1)
        janelas = janelas_geral(_REFERENCIA, mais_antiga=limite, referencia=_REFERENCIA)
        assert janelas == [completo[0]]

    def test_marcador_parcial_retoma_de_onde_parou(self):
        completo = janelas_geral(_REFERENCIA)
        corte = completo[3][0]
        janelas = janelas_geral(_REFERENCIA, mais_antiga=corte, referencia=_REFERENCIA)
        assert janelas[0] == completo[0]
        assert janelas[1][1] == corte - timedelta(days=1)
        assert janelas[-1] == completo[-1]

    def test_referencia_anterior_preenche_a_lacuna(self):
        # referência saltou 2 meses: precisa cobrir a lacuna desde a anterior
        anterior = _REFERENCIA - timedelta(days=60)
        janelas = janelas_geral(_REFERENCIA, mais_antiga=anterior, referencia=anterior)
        assert all((fim - inicio).days <= DIAS_LOTE - 1 for inicio, fim in janelas)
        cobertos: set[date] = set()
        for inicio, fim in janelas:
            dia = inicio
            while dia <= fim:
                cobertos.add(dia)
                dia += timedelta(days=1)
        assert anterior + timedelta(days=1) in cobertos
        assert _REFERENCIA in cobertos


class TestListarPeriodo:
    def test_le_um_ano_dia_a_dia(self):
        repositorio = _RepositorioFake([_noticia()])
        noticias = listar_periodo(repositorio, _REFERENCIA)
        assert len(noticias) == 1
        assert len(repositorio.janelas) == len(janelas_geral(_REFERENCIA))
        inicio, fim, palavra = repositorio.janelas[0]
        assert inicio == _REFERENCIA
        assert fim == _REFERENCIA
        assert palavra is None
        assert all(inicio == fim for inicio, fim, _ in repositorio.janelas)

    def test_deduplica_noticia_repetida_entre_janelas(self):
        repositorio = _RepositorioFake([_noticia()])
        assert len(listar_periodo(repositorio, _REFERENCIA)) == 1

    def test_mantem_apenas_casos_excepcionais(self):
        excepcional = _noticia(titulo=_TITULO_EXCEPCIONAL, url="https://x/ok")
        rotineira = _noticia(titulo=_TITULO_ROTINEIRO, url="https://x/rotina")
        repositorio = _RepositorioFake([excepcional, rotineira])
        noticias = listar_periodo(repositorio, _REFERENCIA)
        assert [noticia.titulo for noticia in noticias] == [_TITULO_EXCEPCIONAL]

    def test_falha_de_rede_retorna_lista_vazia(self):
        repositorio = _RepositorioFake(erro=True)
        assert listar_periodo(repositorio, _REFERENCIA) == []

    def test_falha_em_um_lote_nao_interrompe_os_demais(self):
        lote_falho = janelas_geral(_REFERENCIA)[1][0]

        class _RepositorioParcial(_RepositorioFake):
            def listar_noticias(
                self, agencia="18", data_inicio=None, data_fim=None, palavra=None
            ):
                self.janelas.append((data_inicio, data_fim, palavra))
                if data_inicio == lote_falho:
                    raise RuntimeError("offline")
                return list(self._noticias)

        repositorio = _RepositorioParcial([_noticia()])
        assert len(listar_periodo(repositorio, _REFERENCIA)) == 1
        assert lote_falho in {inicio for inicio, _, _ in repositorio.janelas}


class TestItensDeJanela:
    def test_converte_e_filtra_excepcionais(self):
        excepcional = _noticia(titulo=_TITULO_EXCEPCIONAL, url="https://x/ok")
        rotineira = _noticia(titulo=_TITULO_ROTINEIRO, url="https://x/rotina")
        repositorio = _RepositorioFake([excepcional, rotineira])
        itens = itens_de_janela(repositorio, _REFERENCIA, _REFERENCIA)
        assert [item.titulo for item in itens] == [_TITULO_EXCEPCIONAL]
        assert itens[0].secao == SECAO_GERAL

    def test_falha_retorna_none(self):
        repositorio = _RepositorioFake(erro=True)
        assert itens_de_janela(repositorio, _REFERENCIA, _REFERENCIA) is None


class TestNoticiaExcepcional:
    @pytest.mark.parametrize(
        "titulo",
        [
            "PETROBRAS (PETR4) - Suspensão de negociação - 20/09/26",
            "FII BLUE (BLUE) - Suspensao de negociacao",
            "EMISSOR - Incorporação - 20/09/26",
            "EMISSOR - Recuperação judicial - 20/09/26",
            "EMISSOR - Início de negociação - 20/09/26",
            "EMISSOR - Aquisição de participação acionária - 20/09/26",
            "EMISSOR - Alienação de participação acionária - 20/09/26",
            "EMISSOR - Mudança de auditor - 20/09/26",
            "EMISSOR - Transação entre partes relacionadas - 20/09/26",
            "EMISSOR - Esclarecimentos de questionamentos CVM/B3",
            "EMISSOR - OPA - Edital de oferta pública de ações",
            "EMISSOR - Modificação de oferta - 20/09/26",
            "EMISSOR - Cancelamento de registro - 20/09/26",
            "EMISSOR - Conversão de categoria - 20/09/26",
            "EMISSOR - Cia em Liquidação: Quadro de Credores",
            "EMISSOR - Direito de preferência - 20/09/26",
        ],
    )
    def test_titulo_excepcional(self, titulo):
        assert noticia_excepcional(titulo) is True

    @pytest.mark.parametrize(
        "titulo",
        [
            "Informe Anual",
            "Relatório Gerencial",
            "Outros Comunicados ao Mercado",
            "Dados diários",
            "Fato relevante",
            "Aviso aos acionistas",
            "Regulamento",
            "Edital de Convocacao de AGE",
            "Demonstrações Financeiras",
            "ATA AGE",
            "PETROBRAS anuncia dividendos",
            "EMISSOR - Alterações para o pregão - 20/09/26",
            "EMISSOR - Emissores em situação especial",
            "EMISSOR - Liberação de negociação das cotas",
            "AVISO AOS ACIONISTAS: SUBSCRIÇÃO PRIVADA",
            "EMISSOR - Formulário de liberação",
            "EMISSOR - Anúncio de início distribuição pública",
            "",
        ],
    )
    def test_titulo_rotineiro(self, titulo):
        assert noticia_excepcional(titulo) is False

    def test_sigla_opa_nao_casa_substring(self):
        # "administracao para" não deve casar com a sigla "OPA".
        assert not noticia_excepcional(
            "EMISSOR - Proposta da Administracao para AGE"
        )
        assert noticia_excepcional("EMISSOR - OPA - Edital de oferta")
        assert "Suspensão de negociação" in TERMOS_EXCEPCIONAIS


class TestClassificarTipo:
    @pytest.mark.parametrize(
        ("titulo", "tipo"),
        [
            ("EMISSOR - Suspensão de negociação - 20/09/26", "Negociação"),
            ("EMISSOR - Reabertura de negociação", "Negociação"),
            ("EMISSOR - Cancelamento de listagem", "Listagem e Registro"),
            ("EMISSOR - Deslistagem", "Listagem e Registro"),
            ("EMISSOR - OPA - Edital de oferta", "Ofertas e OPA"),
            ("EMISSOR - Modificação de oferta", "Ofertas e OPA"),
            ("EMISSOR - Aquisição de participação acionária", "Participações"),
            ("EMISSOR - Alienação de participação", "Participações"),
            ("EMISSOR - Incorporação - 20/09/26", "Reorganização Societária"),
            ("EMISSOR - Fusão", "Reorganização Societária"),
            ("EMISSOR - Recuperação judicial", "Recuperação e Liquidação"),
            ("EMISSOR - Liquidação extrajudicial", "Recuperação e Liquidação"),
            ("EMISSOR - Grupamento", "Eventos de Capital"),
            ("EMISSOR - Aumento de capital", "Eventos de Capital"),
            (
                "EMISSOR - Transação entre partes relacionadas",
                "Governança e Auditoria",
            ),
            ("EMISSOR - Mudança de auditor", "Governança e Auditoria"),
            ("EMISSOR - Esclarecimentos CVM/B3", "Esclarecimentos e Oscilações"),
            ("EMISSOR - Oscilação atípica", "Esclarecimentos e Oscilações"),
            ("EMISSOR - Comunicado sem evento típico", TIPO_OUTROS),
        ],
    )
    def test_classifica_titulos_tipicos(self, titulo, tipo):
        assert classificar_tipo(titulo) == tipo

    def test_tipos_cobrem_a_whitelist(self):
        tipos = {tipo for tipo, _termos in TIPOS_NOTICIA}
        assert "Outros" not in tipos
        for termo in TERMOS_EXCEPCIONAIS:
            assert classificar_tipo(f"EMISSOR - {termo} - 20/09/26") in tipos


class TestAquisicao:
    def test_baixa_e_grava_no_cache(self, tmp_path):
        baixados: list[str] = []

        def _baixar(url):
            baixados.append(url)
            return b"<html>corpo</html>"

        repo = _RepositorioFake([_noticia()])
        aquisicao = _aquisicao(tmp_path, repo, _baixar)
        aquisicao.adquirir(_REFERENCIA)

        assert baixados == [_URL]
        caminho = aquisicao.cache.caminho(chave_noticia(_noticia()), date(2026, 9, 20))
        assert caminho.read_bytes() == b"<html>corpo</html>"
        assert caminho.parts[-4] == "noticias"

    def test_reexecucao_nao_rebaixa(self, tmp_path):
        baixados: list[str] = []

        def _baixar(url):
            baixados.append(url)
            return b"<html>corpo</html>"

        repo = _RepositorioFake([_noticia()])
        aquisicao = _aquisicao(tmp_path, repo, _baixar)
        aquisicao.adquirir(_REFERENCIA)
        aquisicao.adquirir(_REFERENCIA)

        assert baixados == [_URL]

    def test_noticia_sem_url_e_ignorada(self, tmp_path):
        baixados: list[str] = []
        repo = _RepositorioFake([_noticia(url=None)])
        aquisicao = _aquisicao(tmp_path, repo, lambda url: baixados.append(url))
        aquisicao.adquirir(_REFERENCIA)
        assert baixados == []
        assert not any((tmp_path / "noticias").rglob("*.html"))

    def test_conteudo_vazio_nao_grava(self, tmp_path):
        repo = _RepositorioFake([_noticia()])
        aquisicao = _aquisicao(tmp_path, repo, lambda url: None)
        aquisicao.adquirir(_REFERENCIA)
        assert not aquisicao.cache.existe(
            chave_noticia(_noticia()), date(2026, 9, 20)
        )

    def test_erro_de_rede_por_item_nao_interrompe(self, tmp_path):
        def _baixar(url):
            raise requests.ConnectionError("offline")

        repo = _RepositorioFake([_noticia(titulo="A - Suspensão de negociação"), _noticia(titulo="B - Suspensão de negociação")])
        aquisicao = _aquisicao(tmp_path, repo, _baixar)
        aquisicao.adquirir(_REFERENCIA)
        assert not any((tmp_path / "noticias").rglob("*.html"))

    def test_deduplica_url_repetida(self, tmp_path):
        baixados: list[str] = []

        def _baixar(url):
            baixados.append(url)
            return b"<html>corpo</html>"

        repo = _RepositorioFake([_noticia(titulo="A - Suspensão de negociação"), _noticia(titulo="B - Suspensão de negociação")])
        aquisicao = _aquisicao(tmp_path, repo, _baixar)
        aquisicao.adquirir(_REFERENCIA)
        assert baixados == [_URL]

    def test_falha_de_listagem_nao_baixa(self, tmp_path):
        baixados: list[str] = []
        repo = _RepositorioFake(erro=True)
        aquisicao = _aquisicao(tmp_path, repo, lambda url: baixados.append(url))
        aquisicao.adquirir(_REFERENCIA)
        assert baixados == []


class TestIndiceNoticias:
    def test_aquisicao_indexa_metadados(self, tmp_path):
        repo = _RepositorioFake([_noticia()])
        aquisicao = _aquisicao(tmp_path, repo, lambda url: b"<html>corpo</html>")
        aquisicao.adquirir(_REFERENCIA)

        itens = NoticiasIndexStore(cache_dir=tmp_path).itens()
        assert len(itens) == 1
        meta = next(iter(itens.values()))
        assert meta.titulo == _TITULO_EXCEPCIONAL
        assert meta.secao == SECAO_GERAL
        assert meta.categoria == "Negociação"
        assert meta.url == _URL

    def test_catalogo_le_o_indice_sem_rede(self, tmp_path):
        repo = _RepositorioFake([_noticia()])
        aquisicao = _aquisicao(tmp_path, repo, lambda url: b"<html>corpo</html>")
        aquisicao.adquirir(_REFERENCIA)

        arquivos = NoticiasCatalog(cache_dir=tmp_path).arquivos()
        assert [arquivo.nome for arquivo in arquivos] == [_TITULO_EXCEPCIONAL]

    def test_reexecucao_reconstroi_indice_ausente(self, tmp_path):
        baixados: list[str] = []

        def _baixar(url):
            baixados.append(url)
            return b"<html>corpo</html>"

        repo = _RepositorioFake([_noticia()])
        aquisicao = _aquisicao(tmp_path, repo, _baixar)
        aquisicao.adquirir(_REFERENCIA)
        NoticiasIndexStore(cache_dir=tmp_path).path.unlink()

        aquisicao.adquirir(_REFERENCIA)
        assert baixados == [_URL]
        assert NoticiasIndexStore(cache_dir=tmp_path).itens()

    def test_segunda_carga_so_refaz_o_primeiro_dia(self, tmp_path):
        repo = _RepositorioFake([_noticia()])
        aquisicao = _aquisicao(tmp_path, repo, lambda url: b"<html>corpo</html>")
        aquisicao.adquirir(_REFERENCIA)
        assert len(repo.janelas) == len(janelas_geral(_REFERENCIA))

        repo.janelas.clear()
        aquisicao.adquirir(_REFERENCIA)
        assert len(repo.janelas) == 1
        assert repo.janelas[0][1] == _REFERENCIA

    def test_carga_geral_agrupa_escritas_do_indice(self, tmp_path, monkeypatch):
        repo = _RepositorioFake([_noticia()])
        aquisicao = _aquisicao(tmp_path, repo, lambda url: b"x")
        gravacoes: list = []
        original = NoticiasIndexStore._gravar

        def _gravar(store, doc):
            gravacoes.append(1)
            return original(store, doc)

        monkeypatch.setattr(NoticiasIndexStore, "_gravar", _gravar)
        aquisicao.adquirir(_REFERENCIA)
        dias = len(janelas_geral(_REFERENCIA))
        assert len(gravacoes) < dias
        assert len(gravacoes) <= dias // _LOTE_INDICE + 2

    def test_marcador_de_lote_processado_persistido(self, tmp_path):
        repo = _RepositorioFake([_noticia()])
        aquisicao = _aquisicao(tmp_path, repo, lambda url: b"<html>corpo</html>")
        aquisicao.adquirir(_REFERENCIA)
        limite = _REFERENCIA - timedelta(days=DIAS_PERIODO - 1)
        assert NoticiasIndexStore(cache_dir=tmp_path).geral_processada() == (
            limite,
            _REFERENCIA,
        )

    def test_lote_com_falha_nao_e_marcado(self, tmp_path):
        lote_falho = janelas_geral(_REFERENCIA)[0][0]

        class _RepositorioFalho(_RepositorioFake):
            def listar_noticias(
                self, agencia="18", data_inicio=None, data_fim=None, palavra=None
            ):
                self.janelas.append((data_inicio, data_fim, palavra))
                if data_inicio == lote_falho:
                    raise requests.ConnectionError("offline")
                return list(self._noticias)

        repo = _RepositorioFalho([_noticia()])
        aquisicao = _aquisicao(tmp_path, repo, lambda url: b"<html>corpo</html>")
        aquisicao.adquirir(_REFERENCIA)
        indice = NoticiasIndexStore(cache_dir=tmp_path)
        assert indice.geral_processada() == (None, None)
        assert indice.itens() == {}


class TestProgressoCancelamento:
    def test_reporta_progresso_por_categoria(self, tmp_path):
        progresso: list[tuple] = []
        repo = _RepositorioFake(
            [
                _noticia(titulo="A - Suspensão de negociação", url="https://x/1"),
                _noticia(titulo="B - Suspensão de negociação", url="https://x/2"),
            ]
        )
        aquisicao = _aquisicao(tmp_path, repo, lambda url: b"<html>x</html>")
        aquisicao.adquirir(_REFERENCIA, progress=lambda *args: progresso.append(args))

        rotulos = [label for _c, _t, label in progresso]
        assert any("Censuras Públicas" in rotulo for rotulo in rotulos)
        assert any("Condições Excepcionais" in rotulo for rotulo in rotulos)
        assert any("Programas de Aquisição de Ações" in rotulo for rotulo in rotulos)
        assert any("Geral" in rotulo for rotulo in rotulos)
        assert progresso[-1][0] == progresso[-1][1]
        assert "Geral" in progresso[-1][2]

    def test_cancelamento_indexa_o_processado(self, tmp_path):
        token = CancellationToken()
        baixados: list[str] = []

        def _baixar(url):
            baixados.append(url)
            if len(baixados) == 2:
                token.request()
            return b"<html>x</html>"

        repo = _RepositorioFake(
            [
                _noticia(titulo="A - Suspensão de negociação", url="https://x/1"),
                _noticia(titulo="B - Suspensão de negociação", url="https://x/2"),
                _noticia(titulo="C - Suspensão de negociação", url="https://x/3"),
            ]
        )
        aquisicao = _aquisicao(tmp_path, repo, _baixar)
        with pytest.raises(OperacaoCancelada):
            aquisicao.adquirir(_REFERENCIA, cancel_token=token)
        assert len(NoticiasIndexStore(cache_dir=tmp_path).itens()) == 2

    def test_cancelamento_interrompe(self, tmp_path):
        baixados: list[str] = []
        token = CancellationToken()
        token.request()
        repo = _RepositorioFake([_noticia()])
        aquisicao = _aquisicao(tmp_path, repo, lambda url: baixados.append(url))
        with pytest.raises(OperacaoCancelada):
            aquisicao.adquirir(_REFERENCIA, cancel_token=token)
        assert baixados == []


class _RepositorioFontesFake(_RepositorioFake):
    """Repositório com as fontes regulatórias da RFC-004."""

    def __init__(self, censuras=(), condicoes=(), programas=(), **kwargs):
        super().__init__(**kwargs)
        self._censuras = list(censuras)
        self._condicoes = list(condicoes)
        self._programas = list(programas)

    def listar_censuras(self):
        return list(self._censuras)

    def listar_condicoes_excepcionais(self):
        return list(self._condicoes)

    def listar_programas_aquisicao(self, reference_date=None):
        return list(self._programas)


def _censura() -> CensuraPublica:
    return CensuraPublica(
        titulo="FII TORDE EI (TORD)",
        ticker="TORD",
        data="25/02/2026",
        conteudo="A B3 vem a público censurar a administradora.",
    )


def _programa() -> ProgramaAquisicao:
    return ProgramaAquisicao(
        empresa="3TENTOS (NM)",
        data_aprovacao="13/08/2026",
        data_inicio="13/08/2026",
        data_fim="13/02/2028",
        quantidade="5.000.000 (ON)",
        intermediarios="Bradesco",
    )


class TestListarItens:
    def test_deixa_a_geral_por_ultimo(self):
        repo = _RepositorioFontesFake(
            noticias=[_noticia()],
            censuras=[_censura()],
            condicoes=[
                CondicaoExcepcional(
                    companhia="Bradsaúde S.A.",
                    segmento="Novo Mercado",
                    condicao="Percentual mínimo",
                    data_concessao="19/05/2026",
                    prazo="30/10/2027",
                )
            ],
            programas=[_programa()],
        )
        itens = listar_itens(repo, _REFERENCIA)
        secoes = [item.secao for item in itens]
        assert secoes == [
            SECAO_CENSURAS,
            SECAO_CONDICOES,
            SECAO_PROGRAMAS,
            SECAO_GERAL,
        ]

    def test_fonte_indisponivel_nao_interrompe(self):
        class _RepositorioFalho(_RepositorioFontesFake):
            def listar_censuras(self):
                raise RuntimeError("offline")

        itens = listar_itens(_RepositorioFalho(programas=[_programa()]), _REFERENCIA)
        assert [item.secao for item in itens] == [SECAO_PROGRAMAS]

    def test_repositorio_sem_fontes_retorna_so_geral(self):
        repo = _RepositorioFake([_noticia()])
        itens = listar_itens(repo, _REFERENCIA)
        assert [item.secao for item in itens] == [SECAO_GERAL]


class TestChaveItem:
    def test_censura_estavel_e_distinta(self):
        assert chave_item(item_de_censura(_censura())) == chave_item(
            item_de_censura(_censura())
        )
        outra = CensuraPublica(
            titulo="Outra", ticker="OUT", data="25/02/2026", conteudo="x"
        )
        assert chave_item(item_de_censura(_censura())) != chave_item(
            item_de_censura(outra)
        )


class TestAquisicaoFontesRegulatorias:
    def test_item_sem_url_grava_o_proprio_conteudo(self, tmp_path):
        repo = _RepositorioFontesFake(censuras=[_censura()])
        aquisicao = _aquisicao(tmp_path, repo, lambda url: b"nao-deve-baixar")
        aquisicao.adquirir(_REFERENCIA)

        item = item_de_censura(_censura())
        caminho = aquisicao.cache.caminho(chave_item(item), date(2026, 2, 25))
        assert caminho.is_file()
        assert b"censurar" in caminho.read_bytes()

    def test_programa_sem_url_grava_conteudo(self, tmp_path):
        repo = _RepositorioFontesFake(programas=[_programa()])
        aquisicao = _aquisicao(tmp_path, repo, lambda url: b"nao-deve-baixar")
        aquisicao.adquirir(_REFERENCIA)
        assert any((tmp_path / "noticias").rglob("*.html"))

    def test_reexecucao_nao_rebaixa(self, tmp_path):
        baixados: list[str] = []
        repo = _RepositorioFontesFake(censuras=[_censura()])
        aquisicao = _aquisicao(tmp_path, repo, lambda url: baixados.append(url) or b"x")
        aquisicao.adquirir(_REFERENCIA)
        aquisicao.adquirir(_REFERENCIA)
        assert baixados == []

    def test_carga_regulatoria_agrupa_escritas_do_indice(self, tmp_path, monkeypatch):
        censuras = [
            CensuraPublica(
                titulo=f"Censura {indice}",
                ticker=f"T{indice}",
                data="25/02/2026",
                conteudo="x",
            )
            for indice in range(60)
        ]

        class _RepositorioSemGeral(_RepositorioFontesFake):
            def listar_noticias(self, **kwargs):
                raise requests.ConnectionError("sem Geral no teste")

        repo = _RepositorioSemGeral(censuras=censuras)
        aquisicao = _aquisicao(tmp_path, repo, lambda url: b"x")
        gravacoes: list = []
        original = NoticiasIndexStore._gravar

        def _gravar(store, doc):
            gravacoes.append(1)
            return original(store, doc)

        monkeypatch.setattr(NoticiasIndexStore, "_gravar", _gravar)
        aquisicao.adquirir(_REFERENCIA)
        # 60 censuras em lotes de 25 => 3 gravações (25, 50 e a sobra)
        assert len(gravacoes) == 3

    def test_reexecucao_nao_reescreve_html_regulatorio(self, tmp_path, monkeypatch):
        repo = _RepositorioFontesFake(censuras=[_censura()], programas=[_programa()])
        aquisicao = _aquisicao(tmp_path, repo, lambda url: b"nao-deve-baixar")
        original = aquisicao.cache.gravar
        chamadas: list = []

        def _gravar(chave, data, conteudo):
            chamadas.append((chave, data))
            return original(chave, data, conteudo)

        monkeypatch.setattr(aquisicao.cache, "gravar", _gravar)
        aquisicao.adquirir(_REFERENCIA)
        assert len(chamadas) == 2  # censura + programa

        chamadas.clear()
        aquisicao.adquirir(_REFERENCIA)
        assert chamadas == []  # nada é reescrito; cache avaliado por existência


class TestNoticiasCache:
    def test_roundtrip_e_nao_sobrescreve(self, tmp_path):
        cache = NoticiasCache(tmp_path)
        cache.gravar("abc", date(2026, 9, 20), b"primeiro")
        cache.gravar("abc", date(2026, 9, 20), b"segundo")
        assert cache.existe("abc", date(2026, 9, 20))
        assert cache.ler("abc", date(2026, 9, 20)) == b"primeiro"

    def test_ler_ausente_retorna_none(self, tmp_path):
        assert NoticiasCache(tmp_path).ler("inexistente", _REFERENCIA) is None

    def test_escopo_dedicado(self):
        assert ESCOPO_NOTICIAS == "NOTICIAS"


class TestBaixarNoticia:
    @responses.activate
    def test_sucesso_retorna_bytes(self):
        responses.get(_URL, body=b"<html>ok</html>", status=200)
        assert baixar_noticia(_URL) == b"<html>ok</html>"

    @responses.activate
    def test_erro_http_retorna_none(self):
        responses.get(_URL, status=500)
        assert baixar_noticia(_URL) is None

    @responses.activate
    def test_erro_de_conexao_retorna_none(self):
        responses.get(_URL, body=requests.ConnectionError("offline"))
        assert baixar_noticia(_URL) is None
