"""Entidades do domínio regulatório da B3."""

from dataclasses import dataclass


@dataclass(frozen=True)
class CensuraPublica:
    """Censura pública aplicada pela B3 a um emissor."""

    titulo: str
    ticker: str | None
    data: str
    conteudo: str

    def to_text(self: "CensuraPublica") -> str:
        """Produz representação textual densa da censura para indexação."""
        nome = self.titulo
        if self.ticker and f"({self.ticker})" not in self.titulo:
            nome = f"{self.titulo} ({self.ticker})"
        lines = [f"[Censura Pública] {nome}"]
        lines.append(f"Data: {self.data}")
        lines.append(f"Conteúdo: {self.conteudo}")
        return "\n".join(lines)

    def to_dict(self: "CensuraPublica") -> dict:
        """Serializa a censura como um dicionário."""
        return {
            "titulo": self.titulo,
            "ticker": self.ticker,
            "data": self.data,
            "conteudo": self.conteudo,
        }


@dataclass(frozen=True)
class CondicaoExcepcional:
    """Condição excepcional concedida pela B3 a uma companhia."""

    companhia: str
    segmento: str | None
    condicao: str
    data_concessao: str | None
    prazo: str | None

    def to_text(self: "CondicaoExcepcional") -> str:
        """Produz representação textual densa da condição para indexação."""
        identificacao = self.companhia
        if self.segmento:
            identificacao = f"{self.companhia} ({self.segmento})"
        lines = [f"[Condição Excepcional] {identificacao}"]
        lines.append(f"Condição: {self.condicao}")
        if self.data_concessao:
            lines.append(f"Data da concessão: {self.data_concessao}")
        if self.prazo:
            lines.append(f"Prazo: {self.prazo}")
        return "\n".join(lines)

    def to_dict(self: "CondicaoExcepcional") -> dict:
        """Serializa a condição excepcional como um dicionário."""
        return {
            "companhia": self.companhia,
            "segmento": self.segmento,
            "condicao": self.condicao,
            "dataConcessao": self.data_concessao,
            "prazo": self.prazo,
        }


@dataclass(frozen=True)
class ProgramaAquisicao:
    """Programa de aquisição de ações em andamento da B3."""

    empresa: str
    data_aprovacao: str | None
    data_inicio: str | None
    data_fim: str | None
    quantidade: str | None
    intermediarios: str | None

    def to_text(self: "ProgramaAquisicao") -> str:
        """Produz representação textual densa do programa para indexação."""
        lines = [f"[Programa de Aquisição de Ações] {self.empresa}"]
        if self.quantidade:
            lines.append(f"Quantidade: {self.quantidade}")
        if self.data_aprovacao:
            lines.append(f"Data de aprovação: {self.data_aprovacao}")
        if self.data_inicio:
            lines.append(f"Início: {self.data_inicio}")
        if self.data_fim:
            lines.append(f"Término: {self.data_fim}")
        if self.intermediarios:
            lines.append(f"Intermediários: {self.intermediarios}")
        return "\n".join(lines)

    def to_dict(self: "ProgramaAquisicao") -> dict:
        """Serializa o programa de aquisição como um dicionário."""
        return {
            "empresa": self.empresa,
            "dataAprovacao": self.data_aprovacao,
            "dataInicio": self.data_inicio,
            "dataFim": self.data_fim,
            "quantidade": self.quantidade,
            "intermediarios": self.intermediarios,
        }
