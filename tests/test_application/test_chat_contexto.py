"""Testes puros da montagem do contexto do chat."""

from types import SimpleNamespace

from flowscope.application.chat import FonteContexto, MontarContextoChat


class _CascataFake:
    """Cascata de documentos de teste com resumos e alvos configuráveis."""

    def __init__(self, resumos: str = "", alvos=None) -> None:
        self.resumos = resumos
        self.alvos = list(alvos or [])
        self.chamadas_montar: list[tuple] = []

    def montar_resumos(self, ticker, watchlist):
        self.chamadas_montar.append((ticker, list(watchlist)))
        return self.resumos, self.alvos

    def resolver_alvos(self, chaves):
        return list(self.alvos)

    def preparar_texto(self, alvos):
        return "TEXTO DOS DOCUMENTOS"


class TestMontar:
    def test_monta_contexto_completo(self):
        cascata = _CascataFake(resumos="RESUMOS")
        fonte = lambda pergunta: FonteContexto("Notícias", "conteudo")
        montador = MontarContextoChat(
            cascata=cascata,
            fontes_adicionais=[fonte],
            confirmar=lambda quantidade, nomes: True,
            conhecimento="CONHECIMENTO",
        )

        contexto = montador.montar(
            "pergunta", {"PETR4": None}, ["PETR4", "VALE3"]
        )

        assert "CONHECIMENTO" in contexto.bloco_estavel
        assert "RESUMOS" in contexto.bloco_estavel
        assert "[PETR4]" in contexto.bloco_estavel
        assert contexto.documentos is not None
        assert contexto.documentos.resumos == "RESUMOS"
        assert contexto.fontes_adicionais == [FonteContexto("Notícias", "conteudo")]
        assert cascata.chamadas_montar == [(None, ["PETR4", "VALE3"])]

    def test_documental_usa_escalonamento_e_gate_do_montador(self):
        documento = SimpleNamespace(nome="Doc", chave="c1")
        cascata = _CascataFake(resumos="R", alvos=[documento])
        montador = MontarContextoChat(cascata=cascata)
        contexto = montador.montar("pergunta", {}, [])
        assert contexto.documentos.preparar_texto(["c1"]) == (
            "TEXTO DOS DOCUMENTOS"
        )
        assert contexto.documentos.confirmar(["c1"]) is True


class TestBlocoEstavelMemoizado:
    def _montador(self, cascata, **kwargs) -> MontarContextoChat:
        kwargs.setdefault("conhecimento", "CONHECIMENTO")
        return MontarContextoChat(cascata=cascata, **kwargs)

    def test_bloco_deterministico(self):
        montador = self._montador(_CascataFake(resumos="RESUMOS"))
        primeiro = montador.montar_bloco({"PETR4": None}, ["PETR4"])
        segundo = montador.montar_bloco({"PETR4": None}, ["PETR4"])
        assert primeiro == segundo
        assert primeiro[0].encode("utf-8") == segundo[0].encode("utf-8")

    def test_reuso_nao_renderiza_de_novo(self, monkeypatch):
        montador = self._montador(_CascataFake(resumos="RESUMOS"))
        bloco, assinatura = montador.montar_bloco({"PETR4": None}, ["PETR4"])
        renderizacoes: list = []
        original = montador._renderizar_bloco
        monkeypatch.setattr(
            montador,
            "_renderizar_bloco",
            lambda *args: renderizacoes.append(1) or original(*args),
        )

        bloco2, assinatura2 = montador.montar_bloco(
            {"PETR4": None}, ["PETR4"], cache=(assinatura, bloco)
        )

        assert (bloco2, assinatura2) == (bloco, assinatura)
        assert renderizacoes == []

    def test_assinatura_muda_com_fundamentos(self):
        montador = self._montador(_CascataFake(resumos="RESUMOS"))
        _b1, a1 = montador.montar_bloco({"PETR4": None}, ["PETR4"])
        _b2, a2 = montador.montar_bloco({"VALE3": None}, ["VALE3"])
        assert a1 != a2

    def test_assinatura_muda_com_watchlist(self):
        montador = self._montador(_CascataFake(resumos="RESUMOS"))
        dados = {"PETR4": None, "VALE3": None}
        _b1, a1 = montador.montar_bloco(dados, ["PETR4"])
        _b2, a2 = montador.montar_bloco(dados, ["PETR4", "VALE3"])
        assert a1 != a2

    def test_assinatura_muda_com_resumos(self):
        cascata = _CascataFake(resumos="RESUMOS 1")
        montador = self._montador(cascata)
        _b1, a1 = montador.montar_bloco({}, [])
        cascata.resumos = "RESUMOS 2"
        _b2, a2 = montador.montar_bloco({}, [])
        assert a1 != a2

    def test_prefixo_repetido_sinalizado(self):
        montador = self._montador(_CascataFake(resumos="RESUMOS"))
        bloco, assinatura = montador.montar_bloco({"PETR4": None}, ["PETR4"])
        primeiro = montador.montar("p", {"PETR4": None}, ["PETR4"])
        assert primeiro.prefixo_repetido is False
        segundo = montador.montar(
            "p2",
            {"PETR4": None},
            ["PETR4"],
            cache=(assinatura, bloco),
        )
        assert segundo.prefixo_repetido is True


class TestFontesAdicionais:
    def test_omite_fontes_vazias_ausentes_e_com_falha(self):
        def boa(pergunta):
            return FonteContexto("Boa", "conteudo")

        def vazia(pergunta):
            return FonteContexto("Vazia", "")

        def ausente(pergunta):
            return None

        def falha(pergunta):
            raise RuntimeError("boom")

        montador = MontarContextoChat(
            cascata=_CascataFake(),
            fontes_adicionais=[boa, vazia, ausente, falha],
        )
        assert montador.preparar_fontes_adicionais("p") == [
            FonteContexto("Boa", "conteudo")
        ]

    def test_fonte_volatil_nao_afeta_assinatura_nem_bloco(self):
        fonte = lambda pergunta: FonteContexto("RAG", f"trecho {pergunta}")
        montador = MontarContextoChat(
            cascata=_CascataFake(resumos="RESUMOS"),
            fontes_adicionais=[fonte],
            conhecimento="CONHECIMENTO",
        )

        primeiro = montador.montar("pergunta A", {"PETR4": None}, ["PETR4"])
        segundo = montador.montar("pergunta B", {"PETR4": None}, ["PETR4"])

        assert primeiro.assinatura == segundo.assinatura
        assert primeiro.bloco_estavel == segundo.bloco_estavel
        assert primeiro.fontes_adicionais != segundo.fontes_adicionais
        assert "trecho pergunta A" not in primeiro.bloco_estavel


class TestGateConfirmacao:
    def test_ate_tres_nao_chama_callback(self):
        chamadas: list = []
        montador = MontarContextoChat(
            cascata=_CascataFake(alvos=[SimpleNamespace(nome="Doc")]),
            confirmar=lambda quantidade, nomes: chamadas.append(quantidade) or True,
        )
        assert montador.confirmar_leitura(["x"]) is True
        assert chamadas == []

    def test_acima_de_tres_lista_nomes(self):
        documentos = [
            SimpleNamespace(nome=f"{i}.pdf", chave=f"c{i}") for i in range(5)
        ]
        chamadas: list = []
        montador = MontarContextoChat(
            cascata=_CascataFake(alvos=documentos),
            confirmar=lambda quantidade, nomes: chamadas.append(
                (quantidade, nomes)
            )
            or True,
        )
        assert montador.confirmar_leitura(["c0"]) is True
        assert chamadas == [(5, [f"{i}.pdf" for i in range(5)])]

    def test_sem_callback_prossegue(self):
        documentos = [SimpleNamespace(nome=f"{i}.pdf") for i in range(5)]
        montador = MontarContextoChat(cascata=_CascataFake(alvos=documentos))
        assert montador.confirmar_leitura(["x"]) is True
