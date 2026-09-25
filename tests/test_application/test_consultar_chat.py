"""Testes do caso de uso do chat (cascata em até duas chamadas)."""

import pytest

from flowscope.application.cancellation import (
    CancellationToken,
    OperacaoCancelada,
)
from flowscope.application.chat import (
    ConsultarChatUseCase,
    ContextoChat,
    ContextoDocumental,
    FonteContexto,
)
from flowscope.application.chat.consultar import (
    SYSTEM_PROMPT,
    interpretar_resposta,
)
from flowscope.domain.chat import ChatMessage
from flowscope.domain.llm import LLMUnavailableError


class _FakeLLM:
    """Porta de completion de teste com respostas roteirizadas."""

    def __init__(self, respostas: list) -> None:
        self.respostas = list(respostas)
        self.chamadas: list[tuple] = []

    def complete(self, messages: list[dict], system_prompt: str | None = None) -> str:
        self.chamadas.append((messages, system_prompt))
        resposta = self.respostas.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta


def _documental(resumos="RESUMOS", preparar=None, confirmar=None) -> ContextoDocumental:
    return ContextoDocumental(
        resumos=resumos,
        preparar_texto=preparar or (lambda chaves: ""),
        confirmar=confirmar or (lambda chaves: True),
    )


class TestCascata:
    def test_resposta_nos_resumos_uma_chamada(self):
        llm = _FakeLLM(['{"resposta": "resposta pronta", "documentos": []}'])
        usecase = ConsultarChatUseCase(llm)
        contexto = ContextoChat(
            conhecimento="K", fundamentos="F", documentos=_documental()
        )
        resposta = usecase.consultar("pergunta", contexto)
        assert resposta.texto == "resposta pronta"
        assert len(llm.chamadas) == 1

    def test_escalada_para_texto_integral_duas_chamadas(self):
        llm = _FakeLLM(
            [
                '{"resposta": "", "documentos": ["bdr/PETR4/2026/07/1.pdf"]}',
                '{"resposta": "resposta final", "documentos": []}',
            ]
        )
        preparados: list[list[str]] = []

        def preparar(chaves: list[str]) -> str:
            preparados.append(chaves)
            return "TEXTO INTEGRAL"

        usecase = ConsultarChatUseCase(llm)
        contexto = ContextoChat(
            documentos=_documental(preparar=preparar),
        )
        resposta = usecase.consultar("pergunta", contexto)
        assert len(llm.chamadas) == 2
        assert resposta.texto == "resposta final"
        assert preparados == [["bdr/PETR4/2026/07/1.pdf"]]
        assert resposta.fontes == ["bdr/PETR4/2026/07/1.pdf"]
        assert "TEXTO INTEGRAL" in llm.chamadas[1][0][0]["content"]

    def test_sem_documentos_no_contexto(self):
        llm = _FakeLLM(['{"resposta": "", "documentos": ["chave"]}'])
        usecase = ConsultarChatUseCase(llm)
        resposta = usecase.consultar("pergunta", ContextoChat(documentos=None))
        assert len(llm.chamadas) == 1
        assert resposta.documentos_solicitados == ["chave"]

    def test_confirmacao_recusada_nao_le_texto(self):
        llm = _FakeLLM(['{"resposta": "", "documentos": ["a"]}'])
        preparados: list[list[str]] = []
        usecase = ConsultarChatUseCase(llm)
        contexto = ContextoChat(
            documentos=_documental(
                preparar=lambda chaves: preparados.append(chaves) or "",
                confirmar=lambda chaves: False,
            )
        )
        resposta = usecase.consultar("pergunta", contexto)
        assert len(llm.chamadas) == 1
        assert preparados == []
        assert "Não encontrei documentos" in resposta.texto

    def test_llm_indisponivel_propaga(self):
        llm = _FakeLLM([LLMUnavailableError("sem provedor")])
        usecase = ConsultarChatUseCase(llm)
        with pytest.raises(LLMUnavailableError):
            usecase.consultar("pergunta", ContextoChat())


class TestCancelamento:
    def test_token_ja_cancelado_nao_chama_llm(self):
        llm = _FakeLLM(['{"resposta": "x", "documentos": []}'])
        token = CancellationToken()
        token.request()
        usecase = ConsultarChatUseCase(llm)
        with pytest.raises(OperacaoCancelada):
            usecase.consultar("pergunta", ContextoChat(), token)
        assert llm.chamadas == []

    def test_cancelamento_entre_chamadas(self):
        llm = _FakeLLM(
            [
                '{"resposta": "", "documentos": ["chave"]}',
                '{"resposta": "final", "documentos": []}',
            ]
        )
        token = CancellationToken()

        def confirmar(_chaves: list[str]) -> bool:
            token.request()
            return True

        usecase = ConsultarChatUseCase(llm)
        contexto = ContextoChat(documentos=_documental(confirmar=confirmar))
        with pytest.raises(OperacaoCancelada):
            usecase.consultar("pergunta", contexto, token)
        assert len(llm.chamadas) == 1


class TestParserTolerante:
    def test_formato_reconhecido(self):
        resposta = interpretar_resposta(
            '{"resposta": "ok", "documentos": ["a", 3, ""]}'
        )
        assert resposta.texto == "ok"
        assert resposta.documentos_solicitados == ["a"]

    def test_formato_json_cercado(self):
        resposta = interpretar_resposta(
            'Segue:\n```json\n{"resposta": "ok", "documentos": []}\n```\n'
        )
        assert resposta.texto == "ok"

    def test_formato_nao_reconhecido(self):
        resposta = interpretar_resposta("apenas um texto solto")
        assert resposta.texto == "apenas um texto solto"
        assert resposta.documentos_solicitados == []

    def test_sem_segunda_rodada_quando_invalido(self):
        llm = _FakeLLM(["texto solto"])
        usecase = ConsultarChatUseCase(llm)
        resposta = usecase.consultar(
            "pergunta", ContextoChat(documentos=_documental())
        )
        assert len(llm.chamadas) == 1
        assert resposta.texto == "texto solto"


class TestPrompt:
    def test_prompt_de_sistema_tem_instrucoes(self):
        llm = _FakeLLM(['{"resposta": "x", "documentos": []}'])
        ConsultarChatUseCase(llm).consultar("pergunta", ContextoChat())
        _mensagens, system_prompt = llm.chamadas[0]
        assert system_prompt == SYSTEM_PROMPT
        assert "apenas com base no contexto" in system_prompt
        assert "Cite as fontes" in system_prompt
        assert "Identifique o ticker" in system_prompt
        assert "peça esclarecimento" in system_prompt
        assert "admita a limitação" in system_prompt

    def test_prompt_inclui_blocos_de_contexto(self):
        llm = _FakeLLM(['{"resposta": "x", "documentos": []}'])
        contexto = ContextoChat(
            conhecimento="CONHECIMENTO",
            fundamentos="FUNDAMENTOS",
            documentos=_documental(resumos="RESUMOS"),
        )
        ConsultarChatUseCase(llm).consultar("Pergunta?", contexto)
        prompt = llm.chamadas[0][0][0]["content"]
        assert "CONHECIMENTO" in prompt
        assert "FUNDAMENTOS" in prompt
        assert "RESUMOS" in prompt
        assert "Pergunta?" in prompt

    def test_prompt_inclui_fontes_adicionais(self):
        llm = _FakeLLM(['{"resposta": "x", "documentos": []}'])
        contexto = ContextoChat(
            fontes_adicionais=[
                FonteContexto(titulo="Notícias", texto="NOTICIA PETR4"),
                FonteContexto(titulo="RAG", texto="TRECHO RELEVANTE"),
            ]
        )
        ConsultarChatUseCase(llm).consultar("Pergunta?", contexto)
        prompt = llm.chamadas[0][0][0]["content"]
        assert "## Notícias" in prompt
        assert "NOTICIA PETR4" in prompt
        assert "## RAG" in prompt
        assert "TRECHO RELEVANTE" in prompt


class TestHistorico:
    def test_historico_enviado_em_ordem(self):
        llm = _FakeLLM(['{"resposta": "x", "documentos": []}'])
        historico = [
            ChatMessage(role="user", content="pergunta anterior"),
            ChatMessage(role="assistant", content="resposta anterior"),
        ]
        ConsultarChatUseCase(llm).consultar(
            "pergunta atual", ContextoChat(), historico=historico
        )
        mensagens = llm.chamadas[0][0]
        assert mensagens[0] == {"role": "user", "content": "pergunta anterior"}
        assert mensagens[1] == {"role": "assistant", "content": "resposta anterior"}
        assert mensagens[-1]["role"] == "user"
        assert "pergunta atual" in mensagens[-1]["content"]

    def test_ambos_os_niveis_herdam_o_historico(self):
        llm = _FakeLLM(
            [
                '{"resposta": "", "documentos": ["chave"]}',
                '{"resposta": "final", "documentos": []}',
            ]
        )
        historico = [ChatMessage(role="user", content="turno antigo")]
        ConsultarChatUseCase(llm).consultar(
            "pergunta",
            ContextoChat(documentos=_documental()),
            historico=historico,
        )
        assert len(llm.chamadas) == 2
        for mensagens, _sistema in llm.chamadas:
            assert mensagens[0] == {
                "role": "user",
                "content": "turno antigo",
            }

    def test_erros_fora_do_historico(self):
        llm = _FakeLLM(['{"resposta": "x", "documentos": []}'])
        historico = [
            ChatMessage(role="user", content="pergunta anterior"),
            ChatMessage(
                role="assistant",
                content="mensagem de erro",
                enviar_ao_modelo=False,
            ),
        ]
        ConsultarChatUseCase(llm).consultar(
            "pergunta atual", ContextoChat(), historico=historico
        )
        mensagens = llm.chamadas[0][0]
        conteudos = [msg["content"] for msg in mensagens]
        assert "pergunta anterior" in conteudos
        assert not any("mensagem de erro" in c for c in conteudos)

    def test_teto_de_mensagens_descarta_mais_antigas(self):
        llm = _FakeLLM(['{"resposta": "x", "documentos": []}'])
        historico = [
            ChatMessage(role="user", content=f"m{indice}") for indice in range(12)
        ]
        ConsultarChatUseCase(llm).consultar(
            "atual", ContextoChat(), historico=historico
        )
        mensagens = llm.chamadas[0][0]
        assert len(mensagens) == 11
        assert mensagens[0]["content"] == "m2"
        assert mensagens[9]["content"] == "m11"

    def test_teto_de_caracteres_descarta_mais_antigas(self):
        llm = _FakeLLM(['{"resposta": "x", "documentos": []}'])
        historico = [
            ChatMessage(role="user", content="a" * 5000),
            ChatMessage(role="assistant", content="b" * 5000),
        ]
        ConsultarChatUseCase(llm).consultar(
            "atual", ContextoChat(), historico=historico
        )
        mensagens = llm.chamadas[0][0]
        assert len(mensagens) == 2
        assert mensagens[0]["content"] == "b" * 5000

