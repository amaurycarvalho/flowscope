"""Entidades do domínio de notícias da B3."""

from dataclasses import dataclass


@dataclass(frozen=True)
class NoticiaB3:
    """Notícia publicada no Plantão de Notícias da B3."""

    titulo: str
    data_publicacao: str
    url: str | None
    agencia: str

    def to_text(self: "NoticiaB3") -> str:
        """Produz representação textual densa da notícia para indexação."""
        lines = [f"[Notícia B3] {self.titulo}"]
        lines.append(f"Data de publicação: {self.data_publicacao}")
        lines.append(f"Agência: {self.agencia}")
        return "\n".join(lines)

    def to_dict(self: "NoticiaB3") -> dict:
        """Serializa a notícia como um dicionário."""
        return {
            "titulo": self.titulo,
            "dataPublicacao": self.data_publicacao,
            "url": self.url,
            "agencia": self.agencia,
        }
