"""Testes do loop de navegação do chat."""

import json
import logging

from flowscope.application.chat import (
    ConsultarChatUseCase,
    ParNavegacao,
)
from flowscope.application.chat.arvore import (
    ArvoreConhecimento,
    no_interno,
    ramo_fundamentos,
)
from flowscope.domain.chat import ChatMessage, FonteChat
from flowscope.domain.llm import LLMResposta, LLMUsage


class _FakeLLM:
    """Porta de completion com respostas roteirizadas."""

    def __init__(self, respostas: list) -> None:
        self.respostas = list(respostas)
        self.chamadas: list[tuple] = []

    def complete(self, messages: list[dict], system_prompt: str | None = None) -> LLMResposta:
        self.chamadas.append((messages, system_prompt))
        resposta = self.respostas.pop(0)
        if isinstance(resposta, LLMResposta):
            return resposta
        return LLMResposta(texto=resposta)


def _arvore() -> ArvoreConhecimento:
    raiz = no_interno("/", "/")
    raiz.filho(
        ramo_fundamentos(
            tickers=["PETR4", "VALE3"],
            valores={"PETR4": "[PETR4] PL=3.2", "VALE3": "[VALE3] PL=5.0"},
        )
    )
    return ArvoreConhecimento(raiz, assinatura="sig")


def _resposta(json_texto: str) -> str:
    return json_texto


class TestLoop:
    def test_resposta_no_primeiro_ciclo(self) -> None:
        llm = _FakeLLM(['{"resposta": "pronta", "solicitacoes": []}'])
        resposta = ConsultarChatUseCase(llm).consultar("pergunta?", _arvore())
        assert resposta.texto == "pronta"
        assert len(llm.chamadas) == 1

    def test_navegacao_antes_de_responder(self) -> None:
        llm = _FakeLLM([
            '{"resposta": null, "solicitacoes": [{"op": "obter", "caminho": "/fundamentos/valores/PETR4"}]}',
            '{"resposta": "PL 3.2", "solicitacoes": []}',
        ])
        resposta = ConsultarChatUseCase(llm).consultar("PL da PETR4?", _arvore())
        assert resposta.texto == "PL 3.2"
        assert len(llm.chamadas) == 2
        assert resolved_block(llm.chamadas[0][0]) is None
        assert "RESULTADO_NAVEGACAO" in llm.chamadas[1][0][-1]["content"]

    def test_prefixo_estavel_entre_ciclos(self) -> None:
        llm = _FakeLLM([
            '{"resposta": null, "solicitacoes": [{"op": "existe", "caminho": "/fundamentos"}]}',
            '{"resposta": null, "solicitacoes": [{"op": "contar", "caminho": "/fundamentos"}]}',
            '{"resposta": "ok", "solicitacoes": []}',
        ])
        ConsultarChatUseCase(llm).consultar("p", _arvore())
        prefixos = {chamada[1] for chamada in llm.chamadas}
        assert len(prefixos) == 1

    def test_erro_de_protocolo_continua(self) -> None:
        llm = _FakeLLM([
            '{"resposta": null, "solicitacoes": [{"op": "teleportar", "caminho": "/x"}]}',
            '{"resposta": "segui", "solicitacoes": []}',
        ])
        resposta = ConsultarChatUseCase(llm).consultar("p", _arvore())
        assert resposta.texto == "segui"
        assert "erro" in llm.chamadas[1][0][-1]["content"]

    def test_reuso_de_navegacao(self) -> None:
        llm = _FakeLLM(['{"resposta": "resposta da nova pergunta", "solicitacoes": []}'])
        par = ParNavegacao("assistant antigo", "[RESULTADO_NAVEGACAO] {}")
        ConsultarChatUseCase(llm).consultar("nova", _arvore(), navegacao=[par])
        conteudo = [m["content"] for m in llm.chamadas[0][0]]
        assert "assistant antigo" in conteudo

    def test_historico_selecionado(self) -> None:
        llm = _FakeLLM(['{"resposta": "ok", "solicitacoes": []}'])
        historico = [ChatMessage(role="user", content="anterior")]
        ConsultarChatUseCase(llm).consultar("p", _arvore(), historico=historico)
        assert llm.chamadas[0][0][0]["content"] == "anterior"


class TestGates:
    def test_limite_de_iteracoes_forca_resumo(self) -> None:
        llm = _FakeLLM([
            '{"resposta": null, "solicitacoes": [{"op": "existe", "caminho": "/fundamentos"}]}',
            "resumo final do navegado",
        ])
        usecase = ConsultarChatUseCase(llm, max_iteracoes=1)
        resposta = usecase.consultar("p", _arvore())
        assert resposta.texto == "resumo final do navegado"

    def test_custo_pede_confirmacao(self) -> None:
        llm = _FakeLLM([
            '{"resposta": null, "solicitacoes": [{"op": "obter", "caminho": "/fundamentos/valores/PETR4"}]}',
            '{"resposta": "final", "solicitacoes": []}',
        ])
        pedidos: list[int] = []
        usecase = ConsultarChatUseCase(llm, teto_turno=1)
        usecase.consultar("p", _arvore(), confirmar=lambda tokens: pedidos.append(tokens) or True)
        assert pedidos and pedidos[0] > 0

    def test_custo_recusado_gera_negativa(self) -> None:
        llm = _FakeLLM([
            '{"resposta": null, "solicitacoes": [{"op": "obter", "caminho": "/fundamentos/valores/PETR4"}]}',
            '{"resposta": "final", "solicitacoes": []}',
        ])
        usecase = ConsultarChatUseCase(llm, teto_turno=1)
        usecase.consultar("p", _arvore(), confirmar=lambda _tokens: False)
        assert "negado" in llm.chamadas[1][0][-1]["content"]

    def test_repeticao_de_pedido_negado(self) -> None:
        pedido = '{"resposta": null, "solicitacoes": [{"op": "obter", "caminho": "/fundamentos/valores/PETR4"}]}'
        llm = _FakeLLM([pedido, pedido, '{"resposta": "final", "solicitacoes": []}'])
        usecase = ConsultarChatUseCase(llm, teto_turno=1)
        usecase.consultar("p", _arvore(), confirmar=lambda _tokens: False)
        # O segundo pedido idêntico é rejeitado sem nova confirmação.
        assert "negado" in llm.chamadas[2][0][-1]["content"]


class TestUso:
    def test_uso_e_reportado(self) -> None:
        llm = _FakeLLM([LLMResposta(texto='{"resposta": "x", "solicitacoes": []}', uso=LLMUsage(entrada=10, saida=2))])
        usos: list = []
        ConsultarChatUseCase(llm).consultar("p", _arvore(), ao_uso=usos.append)
        assert usos and usos[0].entrada == 10

    def test_alerta_de_janela(self) -> None:
        llm = _FakeLLM([LLMResposta(texto='{"resposta": "x", "solicitacoes": []}', uso=LLMUsage(entrada=900))])
        resposta = ConsultarChatUseCase(llm, janela=1000).consultar("p", _arvore())
        assert resposta.alerta_janela is True


def resolved_block(mensagens: list[dict]) -> str | None:
    for mensagem in mensagens:
        if "RESULTADO_NAVEGACAO" in mensagem.get("content", ""):
            return mensagem["content"]
    return None


class TestFoco:
    def test_foco_devolvido_apos_obter(self) -> None:
        llm = _FakeLLM([
            '{"resposta": null, "solicitacoes": [{"op": "obter", "caminho": "/fundamentos/valores/PETR4"}]}',
            '{"resposta": "PL 3.2", "solicitacoes": []}',
        ])
        ConsultarChatUseCase(llm).consultar("PL?", _arvore())
        bloco = resolved_block(llm.chamadas[1][0])
        assert bloco is not None
        assert '"foco": "/fundamentos/valores/PETR4"' in bloco

    def test_foco_ausente_sem_obter(self) -> None:
        llm = _FakeLLM([
            '{"resposta": null, "solicitacoes": [{"op": "existe", "caminho": "/fundamentos"}]}',
            '{"resposta": "ok", "solicitacoes": []}',
        ])
        ConsultarChatUseCase(llm).consultar("p", _arvore())
        bloco = resolved_block(llm.chamadas[1][0])
        assert bloco is not None and "foco" not in bloco

    def test_reset_descarta_navegacao_acumulada(self) -> None:
        llm = _FakeLLM([
            '{"resposta": null, "solicitacoes": [{"op": "resetar_navegacao"}]}',
            '{"resposta": "ok", "solicitacoes": []}',
        ])
        par = ParNavegacao("assistant antigo", "[RESULTADO_NAVEGACAO] {}")
        resposta = ConsultarChatUseCase(llm).consultar("p", _arvore(), navegacao=[par])
        assert not any(p.assistant == "assistant antigo" for p in resposta.navegacao)

    def test_reset_limpa_foco_do_turno(self) -> None:
        llm = _FakeLLM([
            '{"resposta": null, "solicitacoes": [{"op": "obter", "caminho": "/fundamentos/valores/PETR4"}]}',
            '{"resposta": null, "solicitacoes": [{"op": "resetar_navegacao"}]}',
            '{"resposta": "ok", "solicitacoes": []}',
        ])
        ConsultarChatUseCase(llm).consultar("p", _arvore())
        bloco_reset = llm.chamadas[2][0][-1]["content"]
        assert "foco" not in bloco_reset


class TestPromptSistema:
    def test_orienta_regex_quando_sem_indice(self):
        from flowscope.application.chat.consultar import SYSTEM_PROMPT

        assert "regex" in SYSTEM_PROMPT
        assert "semântica" in SYSTEM_PROMPT

    def test_orienta_texto_integral(self):
        from flowscope.application.chat.consultar import SYSTEM_PROMPT

        assert "texto integral" in SYSTEM_PROMPT
        assert "/documentos/<ticker>/<chave>/texto" in SYSTEM_PROMPT
        assert "/curto" in SYSTEM_PROMPT
        assert "/longo" in SYSTEM_PROMPT

    def test_orienta_nao_prometer_navegar(self):
        from flowscope.application.chat.consultar import SYSTEM_PROMPT

        assert "prometendo" in SYSTEM_PROMPT
        assert "foco" in SYSTEM_PROMPT

    def test_orienta_paginacao_de_textos_longos(self):
        from flowscope.application.chat.consultar import SYSTEM_PROMPT

        assert "offset" in SYSTEM_PROMPT
        assert "limite" in SYSTEM_PROMPT
        assert "continua" in SYSTEM_PROMPT


def _consultar(operacoes: list[dict], final: dict | str, **kwargs):
    llm = _FakeLLM(
        [
            json.dumps({"resposta": None, "solicitacoes": operacoes}),
            final if isinstance(final, str) else json.dumps({**final, "solicitacoes": []}),
        ]
    )
    return ConsultarChatUseCase(llm, **kwargs).consultar("p", _arvore())


class TestDerivacaoFontes:
    def test_listar_deriva_filhos(self) -> None:
        resposta = _consultar([{"op": "listar", "caminho": "/fundamentos/valores"}], {"resposta": "ok"})
        assert [fonte.caminho for fonte in resposta.fontes] == [
            "/fundamentos/valores/PETR4",
            "/fundamentos/valores/VALE3",
        ]
        assert all(fonte.rotulo is None for fonte in resposta.fontes)

    def test_obter_deriva_o_caminho(self) -> None:
        resposta = _consultar(
            [{"op": "obter", "caminho": "/fundamentos/valores/PETR4"}],
            {"resposta": "ok"},
        )
        assert [fonte.caminho for fonte in resposta.fontes] == [
            "/fundamentos/valores/PETR4"
        ]

    def test_buscar_deriva_resultados(self) -> None:
        resposta = _consultar(
            [{"op": "buscar", "caminho": "/fundamentos/valores", "regex": "PETR4"}],
            {"resposta": "ok"},
        )
        assert "/fundamentos/valores/PETR4" in [
            fonte.caminho for fonte in resposta.fontes
        ]

    def test_buscar_semantico_deriva_resultados(self) -> None:
        class _Backend:
            def buscar(self, caminho, consulta, max):
                return {
                    "resultados": [{"caminho": "/fundamentos/valores/PETR4"}],
                    "truncado": False,
                }

        raiz = no_interno("/", "/")
        raiz.filho(
            ramo_fundamentos(
                tickers=["PETR4", "VALE3"],
                valores={"PETR4": "[PETR4] PL=3.2", "VALE3": "[VALE3] PL=5.0"},
            )
        )
        arvore = ArvoreConhecimento(raiz, assinatura="sig", backend_semantico=_Backend())
        llm = _FakeLLM(
            [
                json.dumps(
                    {
                        "resposta": None,
                        "solicitacoes": [
                            {
                                "op": "buscar_semantico",
                                "caminho": "/fundamentos/valores",
                                "consulta": "PETR4",
                            }
                        ],
                    }
                ),
                '{"resposta": "ok", "solicitacoes": []}',
            ]
        )
        resposta = ConsultarChatUseCase(llm).consultar("p", arvore)
        assert "/fundamentos/valores/PETR4" in [
            fonte.caminho for fonte in resposta.fontes
        ]

    def test_deduplica_preservando_ordem(self) -> None:
        resposta = _consultar(
            [
                {"op": "obter", "caminho": "/fundamentos/valores/PETR4"},
                {"op": "obter", "caminho": "/fundamentos/valores/VALE3"},
                {"op": "obter", "caminho": "/fundamentos/valores/PETR4"},
            ],
            {"resposta": "ok"},
        )
        assert [fonte.caminho for fonte in resposta.fontes] == [
            "/fundamentos/valores/PETR4",
            "/fundamentos/valores/VALE3",
        ]

    def test_erro_nao_gera_fonte(self) -> None:
        resposta = _consultar(
            [{"op": "obter", "caminho": "/nao/existe"}], {"resposta": "ok"}
        )
        assert resposta.fontes == []

    def test_contar_e_existe_nao_geram_fonte(self) -> None:
        resposta = _consultar(
            [
                {"op": "contar", "caminho": "/fundamentos/valores/*"},
                {"op": "existe", "caminho": "/fundamentos"},
            ],
            {"resposta": "ok"},
        )
        assert resposta.fontes == []


class TestMergeFontes:
    def test_rotulo_declarado_associa_a_derivada(self) -> None:
        resposta = _consultar(
            [{"op": "obter", "caminho": "/fundamentos/valores/PETR4"}],
            {
                "resposta": "ok",
                "fontes": [
                    {
                        "caminho": "/fundamentos/valores/PETR4",
                        "rotulo": "PL da PETR4",
                    }
                ],
            },
        )
        assert resposta.fontes == [
            FonteChat(caminho="/fundamentos/valores/PETR4", rotulo="PL da PETR4")
        ]

    def test_declarado_valido_nao_derivado_e_incluido(self) -> None:
        resposta = _consultar(
            [{"op": "obter", "caminho": "/fundamentos/valores/PETR4"}],
            {
                "resposta": "ok",
                "fontes": [
                    {"caminho": "/fundamentos/tickers/VALE3", "rotulo": "VALE3"}
                ],
            },
        )
        assert resposta.fontes == [
            FonteChat(caminho="/fundamentos/valores/PETR4"),
            FonteChat(caminho="/fundamentos/tickers/VALE3", rotulo="VALE3"),
        ]

    def test_declarado_inexistente_e_descartado(self, caplog) -> None:
        with caplog.at_level(logging.WARNING, logger="flowscope"):
            resposta = _consultar(
                [{"op": "obter", "caminho": "/fundamentos/valores/PETR4"}],
                {"resposta": "ok", "fontes": ["/nao/existe"]},
            )
        assert [fonte.caminho for fonte in resposta.fontes] == [
            "/fundamentos/valores/PETR4"
        ]
        assert any("inexistente" in registro.message for registro in caplog.records)

    def test_declaracao_repetida_nao_duplica(self) -> None:
        llm = _FakeLLM(
            [
                json.dumps(
                    {
                        "resposta": "ok",
                        "solicitacoes": [],
                        "fontes": [
                            "/fundamentos/tickers/PETR4",
                            "/fundamentos/tickers/PETR4",
                        ],
                    }
                )
            ]
        )
        resposta = ConsultarChatUseCase(llm).consultar("p", _arvore())
        assert resposta.fontes == [FonteChat(caminho="/fundamentos/tickers/PETR4")]

    def test_sem_declaradas_usa_apenas_derivadas(self) -> None:
        resposta = _consultar(
            [{"op": "obter", "caminho": "/fundamentos/valores/PETR4"}],
            {"resposta": "ok"},
        )
        assert resposta.fontes == [FonteChat(caminho="/fundamentos/valores/PETR4")]


class TestFallbackFontes:
    def test_sem_fontes_derivadas_nem_declaradas(self) -> None:
        resposta = _consultar([], {"resposta": "ok"})
        assert resposta.fontes == []

    def test_texto_puro_usa_fontes_derivadas(self) -> None:
        llm = _FakeLLM(
            [
                '{"resposta": null, "solicitacoes": [{"op": "obter", "caminho": "/fundamentos/valores/PETR4"}]}',
                "resposta em texto puro",
            ]
        )
        resposta = ConsultarChatUseCase(llm).consultar("p", _arvore())
        assert resposta.texto == "resposta em texto puro"
        assert resposta.fontes == [FonteChat(caminho="/fundamentos/valores/PETR4")]

    def test_resumo_final_usa_fontes_derivadas(self) -> None:
        llm = _FakeLLM(
            [
                '{"resposta": null, "solicitacoes": [{"op": "obter", "caminho": "/fundamentos/valores/PETR4"}]}',
                "resumo final do navegado",
            ]
        )
        resposta = ConsultarChatUseCase(llm, max_iteracoes=1).consultar("p", _arvore())
        assert resposta.fontes == [FonteChat(caminho="/fundamentos/valores/PETR4")]


class TestContratoFontes:
    def test_orienta_estruturadamente_nos_dois_pontos(self) -> None:
        from flowscope.application.chat.consultar import INSTRUCAO_FORMATO, SYSTEM_PROMPT
        from flowscope.application.chat.manifesto import PERSONA, PROTOCOLO

        for texto in (SYSTEM_PROMPT, INSTRUCAO_FORMATO, PERSONA, PROTOCOLO):
            assert "fontes" in texto
            assert "No corpo" in texto or "no corpo" in texto
            assert "Cite as fontes" not in texto
