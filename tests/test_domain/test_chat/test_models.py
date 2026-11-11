"""Testes das entidades ``ChatMessage`` e ``ChatSession``."""

from datetime import datetime

from flowscope.domain.chat import ChatMessage, ChatSession, FonteChat


class TestChatMessage:
    def test_mensagem_usuario_sem_fontes(self):
        msg = ChatMessage(role="user", content="Qual foi o último rendimento?")
        assert msg.role == "user"
        assert msg.content == "Qual foi o último rendimento?"
        assert msg.sources == []
        assert isinstance(msg.timestamp, datetime)
        assert msg.enviar_ao_modelo is True

    def test_mensagem_fora_do_historico(self):
        msg = ChatMessage(role="assistant", content="falha", enviar_ao_modelo=False)
        assert msg.enviar_ao_modelo is False

    def test_mensagem_assistente_com_fontes(self):
        fontes = [
            FonteChat(
                caminho="/documentos/PETR4/abc/texto", rotulo="Fato Relevante 15/07"
            )
        ]
        msg = ChatMessage(
            role="assistant", content="O último rendimento foi...", sources=fontes
        )
        assert msg.sources == fontes

    def test_sem_fontes_nao_compartilha_lista(self):
        primeira = ChatMessage(role="user", content="a")
        segunda = ChatMessage(role="user", content="b")
        primeira.sources.append(FonteChat(caminho="/x"))
        assert segunda.sources == []


class TestFonteChat:
    def test_caminho_obrigatorio(self):
        assert FonteChat(caminho="/x").caminho == "/x"

    def test_rotulo_opcional(self):
        assert FonteChat(caminho="/x").rotulo is None
        assert FonteChat(caminho="/x", rotulo="Rótulo").rotulo == "Rótulo"


class TestChatSession:
    def test_nova_sessao_vazia(self):
        assert ChatSession().messages == []

    def test_adicionar_e_limpar_mensagens(self):
        sessao = ChatSession()
        for indice in range(3):
            sessao.add_message(ChatMessage(role="user", content=str(indice)))
        assert len(sessao.messages) == 3
        sessao.clear()
        assert sessao.messages == []
