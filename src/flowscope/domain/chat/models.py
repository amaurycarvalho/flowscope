"""Entidades de conversa em memória usadas pela aba de chat com I.A.

As mensagens existem apenas durante a sessão da interface: não há persistência
de histórico. A aba "Chat AI" mantém a sua própria :class:`ChatSession`.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone


def _agora() -> datetime:
    """Retorna o instante atual em UTC para o carimbo da mensagem."""
    return datetime.now(timezone.utc)


@dataclass
class ChatMessage:
    """Mensagem de uma conversa, do usuário ou do assistente."""

    role: str
    content: str
    sources: list[dict] = field(default_factory=list)
    timestamp: datetime = field(default_factory=_agora)


@dataclass
class ChatSession:
    """Conversa em memória, sem persistência, da aba "Chat AI"."""

    messages: list[ChatMessage] = field(default_factory=list)

    def add_message(self: "ChatSession", msg: ChatMessage) -> None:
        """Acrescenta uma mensagem ao final da conversa."""
        self.messages.append(msg)

    def clear(self: "ChatSession") -> None:
        """Descarta todas as mensagens da conversa."""
        self.messages.clear()
