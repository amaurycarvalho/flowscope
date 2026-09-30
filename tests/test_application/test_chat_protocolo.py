"""Testes do protocolo JSON de navegação."""

import json

from flowscope.application.chat.arvore import (
    ArvoreConhecimento,
    no_interno,
    ramo_fundamentos,
)
from flowscope.application.chat.protocolo import (
    MARCADOR_RESULTADO,
    ProtocoloNavegacao,
    Solicitacao,
    interpretar,
)


def _arvore() -> ArvoreConhecimento:
    raiz = no_interno("/", "raiz")
    raiz.filho(
        ramo_fundamentos(
            tickers=["PETR4", "VALE3"],
            valores={"PETR4": "[PETR4] PL=3.2", "VALE3": "[VALE3] PL=5.0"},
        )
    )
    return ArvoreConhecimento(raiz)


def _protocolo() -> ProtocoloNavegacao:
    return ProtocoloNavegacao(_arvore())


class TestInterpretar:
    def test_json_cru(self) -> None:
        resposta = interpretar('{"resposta": "oi", "solicitacoes": []}')
        assert resposta.resposta == "oi"
        assert resposta.final is True

    def test_json_cercado(self) -> None:
        texto = '```json\n{"resposta": null, "solicitacoes": [{"op": "existe", "caminho": "/x"}]}\n```'
        resposta = interpretar(texto)
        assert resposta.resposta is None
        assert resposta.solicitacoes[0].op == "existe"

    def test_texto_puro_e_final(self) -> None:
        resposta = interpretar("apenas uma resposta")
        assert resposta.resposta == "apenas uma resposta"
        assert resposta.final is True

    def test_sem_resposta_e_vazio(self) -> None:
        assert interpretar("").resposta is None


class TestExecucao:
    def test_listar(self) -> None:
        resultado = _executar("listar", caminho="/fundamentos")
        assert [item["nome"] for item in resultado["dados"]] == ["tickers", "campos", "valores"]

    def test_obter(self) -> None:
        assert _executar("obter", caminho="/fundamentos/valores/PETR4")["dados"] == "[PETR4] PL=3.2"

    def test_contar(self) -> None:
        assert _executar("contar", caminho="/fundamentos/tickers/*")["dados"] == 2

    def test_existe(self) -> None:
        assert _executar("existe", caminho="/fundamentos/tickers/PETR4")["dados"] is True

    def test_buscar(self) -> None:
        resultado = _executar("buscar", caminho="/fundamentos", regex="PETR4")
        assert resultado["dados"]["resultados"]

    def test_op_desconhecida(self) -> None:
        resultado = _executar("teleportar", caminho="/x")
        assert resultado["erro"]["motivo"] == "op_desconhecida"

    def test_campo_ausente(self) -> None:
        resultado = _executar("obter", caminho="")
        assert resultado["erro"]["motivo"] == "campo_ausente"

    def test_caminho_invalido(self) -> None:
        resultado = _executar("obter", caminho="/nao/existe")
        assert resultado["erro"]["motivo"] == "caminho_invalido"

    def test_regex_bloqueada(self) -> None:
        resultado = _executar("buscar", caminho="/fundamentos", regex="(a+)+")
        assert resultado["erro"]["motivo"] == "regex_bloqueada"

    def test_listar_folha_sugere_obter(self) -> None:
        resultado = _executar("listar", caminho="/fundamentos/valores/PETR4")
        assert resultado["erro"]["motivo"] == "nao_interno"
        assert "obter" in resultado["erro"]["dica"]

    def test_obter_interno_sugere_listar(self) -> None:
        resultado = _executar("obter", caminho="/fundamentos")
        assert resultado["erro"]["motivo"] == "nao_folha"
        assert "listar" in resultado["erro"]["dica"]

    def test_caminho_invalido_sugere_existe(self) -> None:
        resultado = _executar("obter", caminho="/nao/existe")
        assert resultado["erro"]["motivo"] == "caminho_invalido"
        assert "dica" in resultado["erro"]

    def test_em_fora_de_lista_e_recusado(self) -> None:
        resultado = _executar("buscar", caminho="/fundamentos", regex="PETR4", em="valor")
        assert resultado["erro"]["motivo"] == "tipo_invalido"
        assert "lista" in resultado["erro"]["dica"]

    def test_max_nao_inteiro_e_recusado(self) -> None:
        resultado = _executar("buscar", caminho="/fundamentos", regex="PETR4", max="5")
        assert resultado["erro"]["motivo"] == "tipo_invalido"
        assert "inteiro" in resultado["erro"]["dica"]

    def test_curinga_fora_de_contar_e_recusado(self) -> None:
        resultado = _executar("obter", caminho="/fundamentos/*")
        assert resultado["erro"]["motivo"] == "caminho_com_curinga"
        assert "contar" in resultado["erro"]["dica"]

    def test_curinga_em_contar_e_aceito(self) -> None:
        resultado = _executar("contar", caminho="/fundamentos/valores/*")
        assert resultado["dados"] == 2

    def test_regex_invalida_tem_dica_propria(self) -> None:
        resultado = _executar("buscar", caminho="/fundamentos", regex="(")
        assert resultado["erro"]["motivo"] == "regex_invalida"
        assert "sintaxe" in resultado["erro"]["dica"]

    def test_curinga_invalido_em_contar(self) -> None:
        resultado = _executar("contar", caminho="/fundamentos/*/x")
        assert resultado["erro"]["motivo"] == "curinga_invalido"
        assert "final" in resultado["erro"]["dica"]

    def test_campo_inexistente_tem_dica(self) -> None:
        resultado = _executar(
            "buscar", caminho="/fundamentos", regex="PETR4", em=["inexistente"]
        )
        assert resultado["erro"]["motivo"] == "campo_inexistente"
        assert "dica" in resultado["erro"]

    def test_busca_vazia_traz_dica(self) -> None:
        resultado = _executar("buscar", caminho="/fundamentos", regex="ZZZZ")
        assert resultado["dados"]["resultados"] == []
        assert "dica" in resultado["dados"]

    def test_buscar_semantico_caminho_invalido(self) -> None:
        resultado = _executar(
            "buscar_semantico", caminho="/nao/existe", consulta="x"
        )
        assert resultado["erro"]["motivo"] == "caminho_invalido"

    def test_limite_de_operacoes(self) -> None:
        protocolo = ProtocoloNavegacao(_arvore(), max_operacoes=1)
        resultados = protocolo.executar(
            [Solicitacao("existe", {"caminho": "/fundamentos"})] * 2
        )
        assert resultados[-1]["op"] == "limite_operacoes"

    def test_resetar_navegacao(self) -> None:
        resultado = _executar("resetar_navegacao")
        assert resultado["dados"] == "navegacao_descartada"


class TestSerializacao:
    def test_bloco_deterministico_sem_timestamp(self) -> None:
        protocolo = _protocolo()
        solicitacoes = [Solicitacao("existe", {"caminho": "/fundamentos"})]
        a = protocolo.executar_e_serializar(solicitacoes)
        b = protocolo.executar_e_serializar(solicitacoes)
        assert a == b
        assert a.startswith(MARCADOR_RESULTADO)
        corpo = json.loads(a[len(MARCADOR_RESULTADO) :])
        assert corpo["resultados"][0]["dados"] is True


def _executar(op: str, **campos) -> dict:
    protocolo = _protocolo()
    return protocolo.executar([Solicitacao(op, campos)])[0]
