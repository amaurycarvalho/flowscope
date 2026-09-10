"""Entidades de material facts (fatos relevantes e avisos) da B3."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DocumentoMaterialFact:
    """Documento de fatos relevantes listado pelo ``GetMaterialFacts`` da B3."""

    code_cvm: str
    empresa: str
    ticker: str
    data_referencia: str
    data_entrega: str | None
    categoria: str
    tipo: str | None
    especie: str | None
    status: str | None
    assunto: str
    url_documento: str | None
    url_download: str | None

    def _rotulo(self: "DocumentoMaterialFact") -> str:
        """Retorna o rótulo do tipo de documento para o texto indexável."""
        return "Documento"

    def to_text(self: "DocumentoMaterialFact") -> str:
        """Produz representação textual densa do documento para indexação."""
        return _texto_documento(
            self, self._rotulo(), tipo=self.tipo, especie=self.especie
        )

    def to_dict(self: "DocumentoMaterialFact") -> dict:
        """Serializa o documento como um dicionário no formato da API."""
        return {
            "codeCVM": self.code_cvm,
            "companyName": self.empresa,
            "ticker": self.ticker,
            "dataReferencia": self.data_referencia,
            "dataEntrega": self.data_entrega,
            "categoria": self.categoria,
            "tipo": self.tipo,
            "especie": self.especie,
            "status": self.status,
            "assunto": self.assunto,
            "urlDocumento": self.url_documento,
            "urlDownload": self.url_download,
        }


@dataclass(frozen=True)
class FatoRelevante(DocumentoMaterialFact):
    """Fato relevante divulgado por uma companhia listada."""

    def _rotulo(self: "FatoRelevante") -> str:
        """Retorna o rótulo do tipo de documento."""
        return "Fato Relevante"


@dataclass(frozen=True)
class Assembleia(DocumentoMaterialFact):
    """Documento de assembleia de uma companhia listada."""

    tipo_assembleia: str | None = None
    especie_documento: str | None = None

    def _rotulo(self: "Assembleia") -> str:
        """Retorna o rótulo do tipo de documento."""
        return "Assembleia"

    def to_text(self: "Assembleia") -> str:
        """Produz representação textual densa da assembleia para indexação."""
        return _texto_documento(
            self,
            "Assembleia",
            tipo_rotulo="Tipo de assembleia",
            especie_rotulo="Espécie de documento",
            tipo=self.tipo_assembleia or self.tipo,
            especie=self.especie_documento or self.especie,
        )

    def to_dict(self: "Assembleia") -> dict:
        """Serializa a assembleia como um dicionário no formato da API."""
        dados = super().to_dict()
        dados["tipoAssembleia"] = self.tipo_assembleia or self.tipo
        dados["especieDocumento"] = self.especie_documento or self.especie
        return dados


@dataclass(frozen=True)
class AvisoAcionista(DocumentoMaterialFact):
    """Aviso aos acionistas de uma companhia listada."""

    def _rotulo(self: "AvisoAcionista") -> str:
        """Retorna o rótulo do tipo de documento."""
        return "Aviso ao Acionista"


@dataclass(frozen=True)
class AvisoDebenturista(DocumentoMaterialFact):
    """Aviso aos debenturistas de uma companhia listada."""

    def _rotulo(self: "AvisoDebenturista") -> str:
        """Retorna o rótulo do tipo de documento."""
        return "Aviso ao Debenturista"


def _texto_documento(
    doc: DocumentoMaterialFact,
    rotulo: str,
    *,
    tipo_rotulo: str = "Tipo",
    especie_rotulo: str = "Espécie",
    tipo: str | None = None,
    especie: str | None = None,
) -> str:
    """Monta o texto indexável de um documento de material fact."""
    identificacao = " ".join(
        parte for parte in (doc.empresa, doc.ticker) if parte
    )
    cabecalho = f"[{rotulo}] {identificacao}".rstrip()
    if doc.data_referencia:
        cabecalho = f"{cabecalho} — {doc.data_referencia}"
    linhas = [cabecalho]
    detalhes: list[str] = []
    if doc.categoria:
        detalhes.append(f"Categoria: {doc.categoria}")
    if tipo:
        detalhes.append(f"{tipo_rotulo}: {tipo}")
    if especie:
        detalhes.append(f"{especie_rotulo}: {especie}")
    if detalhes:
        linhas.append(" | ".join(detalhes))
    if doc.assunto:
        linhas.append(f"Assunto: {doc.assunto}")
    if doc.status:
        linhas.append(f"Status: {doc.status}")
    return "\n".join(linhas)
