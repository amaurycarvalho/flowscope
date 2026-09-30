"""Testes da árvore de conhecimento navegável do chat."""

import pytest

from flowscope.application.chat.arvore import (
    ArvoreConhecimento,
    ErroNavegacao,
    no_folha,
    no_interno,
    ramo_flowscope,
    ramo_fundamentos,
)


def _arvore() -> ArvoreConhecimento:
    raiz = no_interno("/", "raiz")
    raiz.filho(
        ramo_flowscope(
            {"versao": "1.0", "licenca": "MIT"},
            abas={"Docs": "documentos relevantes"},
            indicadores={"RSI": "índice de força"},
        )
    )
    raiz.filho(
        ramo_fundamentos(
            tickers=["PETR4", "VALE3"],
            campos={"PL": "preço/lucro"},
            valores={"PETR4": "[PETR4] PL=3.2"},
        )
    )
    return ArvoreConhecimento(raiz, assinatura="sig")


def _arvore_com_pesado() -> ArvoreConhecimento:
    raiz = no_interno("/", "raiz")
    doc = no_interno("/doc", "doc")
    doc.filho(
        no_folha("/doc/PETR4", "PETR4", conteudo="PETR4", campos={"ticker": "PETR4"})
    )
    doc.filho(
        no_folha(
            "/doc/texto",
            "texto",
            carregar=lambda: "conteudo pesado",
            campo_pesado="texto",
        )
    )
    raiz.filho(doc)
    return ArvoreConhecimento(raiz)


class TestNavegacao:
    def test_listar_retorna_filhos_imediatos(self) -> None:
        nomes = [no.nome for no in _arvore().listar("/fundamentos")]
        assert nomes == ["tickers", "campos", "valores"]

    def test_obter_folha_devolve_conteudo(self) -> None:
        assert _arvore().obter("/fundamentos/valores/PETR4") == "[PETR4] PL=3.2"

    def test_obter_interno_falha(self) -> None:
        with pytest.raises(ErroNavegacao) as erro:
            _arvore().obter("/fundamentos")
        assert erro.value.motivo == "nao_folha"

    def test_caminho_invalido(self) -> None:
        with pytest.raises(ErroNavegacao) as erro:
            _arvore().listar("/nao/existe")
        assert erro.value.motivo == "caminho_invalido"

    def test_existe(self) -> None:
        arvore = _arvore()
        assert arvore.existe("/fundamentos/tickers/PETR4") is True
        assert arvore.existe("/fundamentos/tickers/XXXX") is False

    def test_contar_subarvore(self) -> None:
        assert _arvore().contar("/fundamentos/valores") == 2

    def test_contar_coringa_conta_filhos(self) -> None:
        assert _arvore().contar("/fundamentos/valores/*") == 1
        assert _arvore().contar("/fundamentos/tickers/*") == 2

    def test_carregar_sob_demanda(self) -> None:
        raiz = no_interno("/", "raiz")
        chamadas = {"n": 0}

        def carregar() -> str:
            chamadas["n"] += 1
            return "conteudo pesado"

        raiz.filho(no_folha("/x", "x", carregar=carregar))
        arvore = ArvoreConhecimento(raiz)
        assert arvore.obter("/x") == "conteudo pesado"
        assert arvore.obter("/x") == "conteudo pesado"
        assert chamadas["n"] == 1

    def test_no_pendente_omitido(self) -> None:
        arvore = _arvore()
        assert not arvore.existe("/documentos/PETR4/curto")


class TestBusca:
    def test_buscar_por_campo(self) -> None:
        resultado = _arvore().buscar(
            "/fundamentos", _padrao("PETR4")
        )
        caminhos = {item["caminho"] for item in resultado["resultados"]}
        assert "/fundamentos/tickers/PETR4" in caminhos
        assert resultado["truncado"] is False

    def test_buscar_restrito_a_campos(self) -> None:
        resultado = _arvore().buscar(
            "/fundamentos", _padrao("PETR4"), em=["valor"]
        )
        assert caminhos(resultado) == {"/fundamentos/valores/PETR4"}

    def test_buscar_trunca(self) -> None:
        resultado = _arvore().buscar("/fundamentos", _padrao("PETR4"), limite=1)
        assert len(resultado["resultados"]) == 1
        assert resultado["truncado"] is True

    def test_buscar_sem_backend(self) -> None:
        resultado = _arvore().buscar_semantico("/fundamentos", "lucro")
        assert resultado["resultados"] == []
        assert resultado["motivo"] == "indice_indisponivel"
        assert "dica" in resultado

    def test_buscar_semantico_caminho_invalido(self) -> None:
        with pytest.raises(ErroNavegacao) as erro:
            _arvore().buscar_semantico("/nao/existe", "lucro")
        assert erro.value.motivo == "caminho_invalido"

    def test_campo_inexistente_tem_dica(self) -> None:
        with pytest.raises(ErroNavegacao) as erro:
            _arvore().buscar("/fundamentos", _padrao("PETR4"), em=["inexistente"])
        assert erro.value.motivo == "campo_inexistente"
        assert "campos disponíveis" in erro.value.dica

    def test_busca_vazia_traz_dica(self) -> None:
        resultado = _arvore().buscar("/fundamentos", _padrao("ZZZZ"))
        assert resultado["resultados"] == []
        assert "dica" in resultado

    def test_caminho_invalido_sugere_pai(self) -> None:
        with pytest.raises(ErroNavegacao) as erro:
            _arvore().obter("/fundamentos/valores/XPTO")
        assert "/fundamentos/valores" in erro.value.dica

    def test_caminho_invalido_usa_ancestral_existente(self) -> None:
        with pytest.raises(ErroNavegacao) as erro:
            _arvore().obter("/flowscope/abas/Inexistente/subabas/x")
        assert "/flowscope/abas" in erro.value.dica
        assert "Inexistente" not in erro.value.dica

    def test_campo_pesado_nao_e_campo_inexistente(self) -> None:
        arvore = _arvore_com_pesado()
        resultado = arvore.buscar("/doc", _padrao("conteudo"), em=["texto"])
        assert resultado["resultados"] == []
        assert "sob demanda" in resultado["dica"]

    def test_campo_pesado_em_lista_com_campo_valido(self) -> None:
        arvore = _arvore_com_pesado()
        resultado = arvore.buscar("/doc", _padrao("PETR4"), em=["ticker", "texto"])
        assert caminhos(resultado) == {"/doc/PETR4"}

    def test_buscar_semantico_com_backend(self) -> None:
        class Backend:
            def buscar(self, caminho, consulta, max):
                return {"resultados": [{"caminho": caminho, "consulta": consulta}], "truncado": False}

        arvore = ArvoreConhecimento(no_interno("/", "/"), backend_semantico=Backend())
        resultado = arvore.buscar_semantico("/", "lucro")
        assert resultado["resultados"][0]["consulta"] == "lucro"


def _padrao(texto: str):
    from flowscope.application.chat.seguranca_regex import compilar

    return compilar(texto)


def caminhos(resultado: dict) -> set[str]:
    return {item["caminho"] for item in resultado["resultados"]}
