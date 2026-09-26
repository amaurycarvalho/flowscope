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

        assert contexto.conhecimento == "CONHECIMENTO"
        assert contexto.documentos is not None
        assert contexto.documentos.resumos == "RESUMOS"
        assert contexto.fontes_adicionais == [FonteContexto("Notícias", "conteudo")]
        assert "[PETR4]" in contexto.fundamentos
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
