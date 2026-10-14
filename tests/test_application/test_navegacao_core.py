"""Testes do núcleo de navegação compartilhado (`NavegacaoCore`)."""

import pytest

from flowscope.application.chat.arvore import (
    ArvoreConhecimento,
    ErroNavegacao,
    no_folha,
    no_interno,
    normalizar_caminho,
    ramo_fundamentos,
)
from flowscope.application.navegacao import cursor
from flowscope.application.navegacao.core import (
    OPERACOES,
    TAMANHO_PAGINA_LISTAR,
    NavegacaoCore,
)


def _arvore() -> ArvoreConhecimento:
    raiz = no_interno("/", "raiz")
    raiz.filho(
        ramo_fundamentos(
            tickers=["PETR4", "VALE3"],
            campos={"PL": "preço/lucro"},
            valores={"PETR4": "[PETR4] PL=3.2", "VALE3": "[VALE3] PL=5.0"},
        )
    )
    raiz.filho(
        no_folha(
            "/doc/texto",
            "texto",
            carregar=lambda: "conteudo pesado",
            campo_pesado="texto",
        )
    )
    return ArvoreConhecimento(raiz, assinatura="sig")


def _arbore_grande(total: int) -> ArvoreConhecimento:
    raiz = no_interno("/", "raiz")
    ramo = no_interno("/ramo", "ramo")
    for indice in range(total):
        ramo.filho(
            no_folha(f"/ramo/{indice:03d}", f"n{indice:03d}", conteudo="x")
        )
    raiz.filho(ramo)
    return ArvoreConhecimento(raiz)


def _core(arvore: ArvoreConhecimento | None = None) -> NavegacaoCore:
    return NavegacaoCore(arvore or _arvore())


class TestCatalogo:
    def test_operacoes_canonicas(self) -> None:
        assert OPERACOES == frozenset(
            {
                "listar",
                "obter",
                "contar",
                "existe",
                "buscar",
                "buscar_semantico",
                "manifesto",
            }
        )

    def test_sem_reset_nem_lote(self) -> None:
        assert "resetar_navegacao" not in OPERACOES
        assert "batch" not in OPERACOES


class TestOperacoes:
    def test_listar(self) -> None:
        dados = _core().executar("listar", {"caminho": "/fundamentos"}).dados
        assert [item["nome"] for item in dados["itens"]] == [
            "campos",
            "tickers",
            "valores",
        ]

    def test_obter(self) -> None:
        resultado = _core().executar(
            "obter", {"caminho": "/fundamentos/valores/PETR4"}
        )
        assert resultado.dados == "[PETR4] PL=3.2"

    def test_contar(self) -> None:
        assert _core().executar("contar", {"caminho": "/fundamentos/tickers/*"}).dados == 2

    def test_existe(self) -> None:
        assert (
            _core().executar("existe", {"caminho": "/fundamentos/tickers/PETR4"}).dados
            is True
        )

    def test_buscar(self) -> None:
        dados = _core().executar(
            "buscar", {"caminho": "/fundamentos", "regex": "PETR4"}
        ).dados
        assert dados["resultados"]

    def test_buscar_semantico_sem_indice(self) -> None:
        dados = _core().executar(
            "buscar_semantico", {"caminho": "/fundamentos", "consulta": "lucro"}
        ).dados
        assert dados["motivo"] == "indice_indisponivel"

    def test_manifesto(self) -> None:
        dados = _core().executar("manifesto", {}).dados
        assert "listar" in dados


class TestOrdenacaoDeterministica:
    def test_ordem_estavel_entre_chamadas(self) -> None:
        core = _core()
        primeira = core.executar("listar", {"caminho": "/fundamentos"}).dados
        segunda = core.executar("listar", {"caminho": "/fundamentos"}).dados
        assert primeira == segunda

    def test_busca_ordenada_por_caminho(self) -> None:
        dados = _core().executar(
            "buscar", {"caminho": "/fundamentos", "regex": "PETR4"}
        ).dados
        caminhos = [item["caminho"] for item in dados["resultados"]]
        assert caminhos == sorted(caminhos)


class TestCursor:
    def test_continuacao_ate_o_fim(self) -> None:
        core = _core(_arbore_grande(205))
        vistos: list[str] = []
        resposta = core.executar("listar", {"caminho": "/ramo"}).dados
        paginas = 1
        while "nextCursor" in resposta:
            assert len(resposta["itens"]) == TAMANHO_PAGINA_LISTAR
            vistos.extend(item["caminho"] for item in resposta["itens"])
            resposta = core.executar(
                "listar", {"caminho": "/ramo", "cursor": resposta["nextCursor"]}
            ).dados
            paginas += 1
        vistos.extend(item["caminho"] for item in resposta["itens"])
        assert paginas == 3
        assert len(vistos) == 205
        assert "nextCursor" not in resposta

    def test_fim_omite_cursor(self) -> None:
        dados = _core().executar("listar", {"caminho": "/fundamentos"}).dados
        assert "nextCursor" not in dados

    def test_buscar_cursor(self) -> None:
        core = _core()
        primeira = core.executar(
            "buscar", {"caminho": "/fundamentos", "regex": "PL", "max": 1}
        ).dados
        assert len(primeira["resultados"]) == 1
        assert "nextCursor" in primeira
        segunda = core.executar(
            "buscar",
            {
                "caminho": "/fundamentos",
                "regex": "PL",
                "max": 1,
                "cursor": primeira["nextCursor"],
            },
        ).dados
        assert segunda["resultados"] != primeira["resultados"]

    def test_cursor_malformado(self) -> None:
        resultado = _core().executar(
            "listar", {"caminho": "/fundamentos", "cursor": "!!!nao-base64!!!"}
        )
        assert resultado.erro is not None
        assert resultado.erro["motivo"] == "cursor_invalido"

    def test_cursor_versao_desconhecida(self) -> None:
        token = cursor.codificar("listar", "/fundamentos", 0)
        resultado = _core().executar(
            "listar", {"caminho": "/fundamentos", "cursor": token + "x"}
        )
        assert resultado.erro is not None
        assert resultado.erro["motivo"] == "cursor_invalido"

    def test_cursor_de_outra_operacao(self) -> None:
        token = cursor.codificar("buscar", "/fundamentos", 0)
        resultado = _core().executar(
            "listar", {"caminho": "/fundamentos", "cursor": token}
        )
        assert resultado.erro["motivo"] == "cursor_invalido"

    def test_cursor_de_outro_caminho(self) -> None:
        token = cursor.codificar("listar", "/outro", 0)
        resultado = _core().executar(
            "listar", {"caminho": "/fundamentos", "cursor": token}
        )
        assert resultado.erro["motivo"] == "cursor_invalido"

    def test_round_trip(self) -> None:
        token = cursor.codificar("listar", "/a/b", 7)
        assert cursor.decodificar(token, "listar", "/a/b") == 7


class TestTraversal:
    def test_normalizar_recusa_ponto_ponto(self) -> None:
        with pytest.raises(ErroNavegacao) as erro:
            normalizar_caminho("/a/../b")
        assert erro.value.motivo == "caminho_invalido"

    def test_normalizar_recusa_ponto(self) -> None:
        with pytest.raises(ErroNavegacao):
            normalizar_caminho("/a/./b")

    def test_core_recusa_traversal(self) -> None:
        resultado = _core().executar("listar", {"caminho": "/fundamentos/../x"})
        assert resultado.erro is not None
        assert resultado.erro["motivo"] == "caminho_invalido"
        assert resultado.falha_interna is False

    def test_normalizar_barras_redundantes(self) -> None:
        assert normalizar_caminho("//a//b/") == "/a/b"


class TestFalhaInterna:
    def test_excecao_inesperada_vira_erro_interno(self, monkeypatch) -> None:
        core = _core()
        arvore = core.arvore

        def explodir(_caminho):
            raise RuntimeError("boom")

        monkeypatch.setattr(arvore, "listar", explodir)
        resultado = core.executar("listar", {"caminho": "/fundamentos"})
        assert resultado.erro is not None
        assert resultado.erro["motivo"] == "erro_interno"
        assert resultado.falha_interna is True

    def test_nucleo_continua_apos_falha(self, monkeypatch) -> None:
        core = _core()
        arvore = core.arvore
        original = arvore.listar

        def explodir(_caminho):
            raise RuntimeError("boom")

        monkeypatch.setattr(arvore, "listar", explodir)
        core.executar("listar", {"caminho": "/fundamentos"})
        monkeypatch.setattr(arvore, "listar", original)
        assert core.executar("listar", {"caminho": "/fundamentos"}).erro is None


class TestValidacao:
    def test_op_desconhecida(self) -> None:
        resultado = _core().executar("resetar_navegacao", {})
        assert resultado.erro["motivo"] == "op_desconhecida"
        assert "listar" in resultado.erro["dica"]

    def test_campo_ausente(self) -> None:
        resultado = _core().executar("obter", {"caminho": ""})
        assert resultado.erro["motivo"] == "campo_ausente"

    def test_max_acima_do_limite_nao_e_erro_do_nucleo(self) -> None:
        resultado = _core().executar(
            "buscar", {"caminho": "/fundamentos", "regex": "PL", "max": 500}
        )
        assert resultado.erro is None

    def test_obter_limite_acima_do_teto_e_limitado(self) -> None:
        dados = _core().executar(
            "obter", {"caminho": "/doc/texto", "limite": 50000}
        ).dados
        assert dados["limite"] == 12000

    def test_offst_alem_do_fim(self) -> None:
        dados = _core().executar(
            "obter", {"caminho": "/doc/texto", "offset": 9999}
        ).dados
        assert dados["texto"] == ""
        assert dados["continua"] is False
