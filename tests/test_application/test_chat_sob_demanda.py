"""Testes do contexto inicial sob demanda (janela de entrada limitada)."""

from flowscope.application.chat import (
    ConsultarChatUseCase,
    ContextoChat,
    ContextoDocumental,
    MontarContextoChat,
)
from flowscope.application.chat.consultar import (
    RECURSO_CONHECIMENTO,
    RECURSO_FUNDAMENTOS,
    RECURSO_RESUMOS,
)
from flowscope.application.chat.contexto import MANIFESTO_RECURSOS
from flowscope.domain.llm import LLMResposta


class _FakeLLM:
    """Porta de completion de teste com respostas roteirizadas."""

    def __init__(self, respostas: list) -> None:
        self.respostas = list(respostas)
        self.chamadas: list[tuple] = []

    def complete(
        self, messages: list[dict], system_prompt: str | None = None
    ) -> LLMResposta:
        self.chamadas.append((messages, system_prompt))
        resposta = self.respostas.pop(0)
        if isinstance(resposta, LLMResposta):
            return resposta
        return LLMResposta(texto=resposta)


class _CascataFake:
    """Cascata de documentos de teste."""

    def __init__(self, resumos: str = "RESUMOS") -> None:
        self.resumos = resumos

    def montar_resumos(self, ticker, watchlist):
        return self.resumos, []

    def resolver_alvos(self, chaves):
        return []

    def preparar_texto(self, alvos):
        return ""


def _montador(input_limitado: bool, confirmar_recursos=None) -> MontarContextoChat:
    return MontarContextoChat(
        cascata=_CascataFake(),
        conhecimento="CONHECIMENTO",
        confirmar=lambda quantidade, nomes: True,
        input_limitado=input_limitado,
        confirmar_recursos=confirmar_recursos,
    )


class TestMontagemSobDemanda:
    def test_flag_ativo_omite_blocos_e_usa_manifesto(self):
        contexto = _montador(True).montar("p", {"PETR4": None}, ["PETR4"])
        assert contexto.input_limitado is True
        assert contexto.bloco_estavel == MANIFESTO_RECURSOS
        assert "CONHECIMENTO" not in contexto.bloco_estavel
        assert "RESUMOS" not in contexto.bloco_estavel
        assert set(contexto.recursos) == {
            RECURSO_CONHECIMENTO,
            RECURSO_FUNDAMENTOS,
            RECURSO_RESUMOS,
        }
        assert contexto.recursos[RECURSO_CONHECIMENTO] == "CONHECIMENTO"
        assert "RESUMOS" in contexto.recursos[RECURSO_RESUMOS]

    def test_flag_desligado_preserva_bloco(self):
        contexto = _montador(False).montar("p", {"PETR4": None}, ["PETR4"])
        assert contexto.input_limitado is False
        assert "CONHECIMENTO" in contexto.bloco_estavel
        assert "RESUMOS" in contexto.bloco_estavel
        assert contexto.recursos == {}
        assert contexto.confirmar_recursos is None

    def test_assinatura_estavel_com_flag_apesar_dos_dados(self):
        montador = _montador(True)
        primeiro = montador.montar("p", {"PETR4": None}, ["PETR4"])
        segundo = montador.montar("p", {"VALE3": None}, ["VALE3"])
        assert primeiro.assinatura == segundo.assinatura

    def test_assinatura_muda_entre_flag_ligado_e_desligado(self):
        ligado = _montador(True).montar("p", {"PETR4": None}, ["PETR4"])
        desligado = _montador(False).montar("p", {"PETR4": None}, ["PETR4"])
        assert ligado.assinatura != desligado.assinatura


def _contexto(recursos, confirmar_recursos=None, documentos=None) -> ContextoChat:
    return ContextoChat(
        bloco_estavel=MANIFESTO_RECURSOS,
        input_limitado=True,
        recursos=dict(recursos),
        confirmar_recursos=confirmar_recursos,
        documentos=documentos,
    )


class TestRecursosSobDemanda:
    def test_instrucao_cita_chaves_reservadas(self):
        llm = _FakeLLM(['{"resposta": "x", "documentos": []}'])
        contexto = _contexto(
            {RECURSO_CONHECIMENTO: "K", RECURSO_RESUMOS: "R"}
        )
        ConsultarChatUseCase(llm).consultar("p", contexto)
        system = llm.chamadas[0][1]
        assert "conhecimento" in system
        assert "resumos" in system
        assert MANIFESTO_RECURSOS in system

    def test_recurso_servido_em_duas_chamadas(self):
        llm = _FakeLLM(
            [
                '{"resposta": "", "documentos": ["conhecimento"]}',
                '{"resposta": "final", "documentos": []}',
            ]
        )
        contexto = _contexto({RECURSO_CONHECIMENTO: "CONTEUDO-K"})
        resposta = ConsultarChatUseCase(llm).consultar("p", contexto)
        assert len(llm.chamadas) == 2
        assert resposta.texto == "final"
        sufixo = llm.chamadas[1][0][-1]["content"]
        assert "## Recursos iniciais" in sufixo
        assert "CONTEUDO-K" in sufixo

    def test_recursos_nao_solicitados_nao_sao_enviados(self):
        llm = _FakeLLM(['{"resposta": "pronto", "documentos": []}'])
        contexto = _contexto({RECURSO_CONHECIMENTO: "CONTEUDO-K"})
        ConsultarChatUseCase(llm).consultar("p", contexto)
        assert len(llm.chamadas) == 1
        assert "CONTEUDO-K" not in llm.chamadas[0][0][-1]["content"]
        assert "CONTEUDO-K" not in llm.chamadas[0][1]

    def test_gate_recursos_confirmado(self):
        chamadas: list[list[str]] = []
        llm = _FakeLLM(
            [
                '{"resposta": "", "documentos": ["conhecimento"]}',
                '{"resposta": "final", "documentos": []}',
            ]
        )
        contexto = _contexto(
            {RECURSO_CONHECIMENTO: "K"},
            confirmar_recursos=lambda chaves: chamadas.append(chaves) or True,
        )
        ConsultarChatUseCase(llm).consultar("p", contexto)
        assert chamadas == [["conhecimento"]]
        assert len(llm.chamadas) == 2

    def test_gate_recursos_recusado_segue_sem_os_recursos(self):
        llm = _FakeLLM(['{"resposta": "", "documentos": ["conhecimento"]}'])
        contexto = _contexto(
            {RECURSO_CONHECIMENTO: "K"},
            confirmar_recursos=lambda chaves: False,
        )
        resposta = ConsultarChatUseCase(llm).consultar("p", contexto)
        assert len(llm.chamadas) == 1
        assert "Não encontrei documentos" in resposta.texto

    def test_recurso_e_documento_na_mesma_escalada(self):
        llm = _FakeLLM(
            [
                '{"resposta": "", "documentos": ["conhecimento", "doc-1"]}',
                '{"resposta": "final", "documentos": []}',
            ]
        )
        documentos = ContextoDocumental(
            resumos="",
            preparar_texto=lambda chaves: "TXT-DOC",
            confirmar=lambda chaves: True,
        )
        contexto = _contexto({RECURSO_CONHECIMENTO: "K"}, documentos=documentos)
        resposta = ConsultarChatUseCase(llm).consultar("p", contexto)
        assert len(llm.chamadas) == 2
        sufixo = llm.chamadas[1][0][-1]["content"]
        assert "K" in sufixo
        assert "TXT-DOC" in sufixo
        assert resposta.fontes == ["doc-1"]


class TestOrcamentoTresChamadas:
    def test_resumos_e_depois_documentos(self):
        llm = _FakeLLM(
            [
                '{"resposta": "", "documentos": ["resumos"]}',
                '{"resposta": "", "documentos": ["doc-1"]}',
                '{"resposta": "final", "documentos": []}',
            ]
        )
        preparados: list[list[str]] = []
        documentos = ContextoDocumental(
            resumos="R",
            preparar_texto=lambda chaves: preparados.append(chaves) or "TEXTO DOC",
            confirmar=lambda chaves: True,
        )
        contexto = _contexto({RECURSO_RESUMOS: "RESUMOS TXT"}, documentos=documentos)
        resposta = ConsultarChatUseCase(llm).consultar("p", contexto)
        assert len(llm.chamadas) == 3
        assert preparados == [["doc-1"]]
        assert "TEXTO DOC" in llm.chamadas[2][0][-1]["content"]
        assert resposta.texto == "final"
        assert resposta.fontes == ["doc-1"]

    def test_prefixo_compartilhado_nas_tres_chamadas(self):
        llm = _FakeLLM(
            [
                '{"resposta": "", "documentos": ["resumos"]}',
                '{"resposta": "", "documentos": ["doc-1"]}',
                '{"resposta": "final", "documentos": []}',
            ]
        )
        documentos = ContextoDocumental(
            resumos="R",
            preparar_texto=lambda chaves: "TEXTO DOC",
            confirmar=lambda chaves: True,
        )
        contexto = _contexto({RECURSO_RESUMOS: "RESUMOS TXT"}, documentos=documentos)
        ConsultarChatUseCase(llm).consultar("p", contexto)
        prefixos = [system for _mensagens, system in llm.chamadas]
        assert prefixos[0] == prefixos[1] == prefixos[2]

    def test_resposta_conclusiva_encerra_a_cascata(self):
        llm = _FakeLLM(['{"resposta": "pronto", "documentos": []}'])
        contexto = _contexto({RECURSO_RESUMOS: "R"})
        ConsultarChatUseCase(llm).consultar("p", contexto)
        assert len(llm.chamadas) == 1

    def test_flag_desligado_mantem_duas_chamadas(self):
        llm = _FakeLLM(
            [
                '{"resposta": "", "documentos": ["doc-1"]}',
                '{"resposta": "final", "documentos": []}',
            ]
        )
        documentos = ContextoDocumental(
            resumos="R",
            preparar_texto=lambda chaves: "TEXTO DOC",
            confirmar=lambda chaves: True,
        )
        contexto = ContextoChat(bloco_estavel="ESTAVEL", documentos=documentos)
        ConsultarChatUseCase(llm).consultar("p", contexto)
        assert len(llm.chamadas) == 2
        assert llm.chamadas[0][1] == llm.chamadas[1][1]
