"""Entidades do domínio de dados estruturados da B3."""

from dataclasses import dataclass
from datetime import date

from flowscope.domain.structured.value_objects import CNPJ, ISIN, ValorProvento


@dataclass
class Entidade:
    """Empresa ou fundo listado responsável pelo documento."""

    nome: str
    cnpj: CNPJ
    nome_administrador: str
    cnpj_administrador: CNPJ
    responsavel: str
    telefone: str


@dataclass
class Provento:
    """Pagamento de rendimento ou amortização declarado no documento."""

    codigo_isin: ISIN
    codigo_negociacao: str
    tipo: str
    data_base: date | None
    valor_por_unidade: ValorProvento
    data_pagamento: date | None
    periodo_referencia: str
    isento_ir: bool
    data_informacao: date | None = None
    ano_referencia: int | None = None
    nota_isencao: str | None = None


@dataclass
class DocumentoProvento:
    """Documento estruturado de provento combinando entidade, provento e metadados."""

    ticker: str
    id_fnet: str
    id_documento: str
    url_documento: str
    data_extracao: str
    entidade: Entidade
    provento: Provento

    def to_dict(self: "DocumentoProvento") -> dict:
        """Serializa o documento como um dicionário."""
        entidade = self.entidade
        provento = self.provento
        return {
            "ticker": self.ticker,
            "idFNET": self.id_fnet,
            "idDocumento": self.id_documento,
            "urlDocumento": self.url_documento,
            "dataExtracao": self.data_extracao,
            "dadosFundos": {
                "nomeFundo": entidade.nome,
                "cnpjFundo": entidade.cnpj.value,
            },
            "dadosAdministrador": {
                "nomeAdministrador": entidade.nome_administrador,
                "cnpjAdministrador": entidade.cnpj_administrador.value,
            },
            "dadosContato": {
                "responsavel": entidade.responsavel,
                "telefone": entidade.telefone,
            },
            "dadosInformacao": {
                "dataInformacao": (
                    provento.data_informacao.isoformat()
                    if provento.data_informacao is not None
                    else (
                        provento.data_base.isoformat()
                        if provento.data_base is not None
                        else None
                    )
                ),
                "anoReferencia": (
                    provento.ano_referencia
                    if provento.ano_referencia is not None
                    else (provento.data_base.year if provento.data_base is not None else None)
                ),
            },
            "dadosProvento": {
                "codigoISIN": provento.codigo_isin.value,
                "codigoNegociacao": provento.codigo_negociacao,
                "tipoProvento": provento.tipo,
                "dataBase": (
                    provento.data_base.isoformat()
                    if provento.data_base is not None
                    else None
                ),
                "valorPorUnidade": str(provento.valor_por_unidade.value),
                "dataPagamento": (
                    provento.data_pagamento.isoformat()
                    if provento.data_pagamento is not None
                    else None
                ),
                "periodoReferencia": provento.periodo_referencia,
                "isentoIR": provento.isento_ir,
                "notaIsencao": provento.nota_isencao,
            },
        }

    def to_text(self: "DocumentoProvento") -> str:
        """Produz representação textual densa do documento para indexação."""
        provento = self.provento
        entidade = self.entidade
        lines = [
            f"Fundo: {entidade.nome}",
            f"CNPJ: {entidade.cnpj.value}",
            f"Ticker: {self.ticker}",
            f"Administrador: {entidade.nome_administrador}",
            f"CNPJ do administrador: {entidade.cnpj_administrador.value}",
            f"Responsável: {entidade.responsavel}",
            f"Telefone: {entidade.telefone}",
            f"Código ISIN: {provento.codigo_isin.value}",
            f"Código de negociação: {provento.codigo_negociacao}",
            f"Tipo de provento: {provento.tipo}",
            f"Data-base: {provento.data_base.isoformat() if provento.data_base else 'não informada'}",
            f"Valor por unidade: R$ {provento.valor_por_unidade.value}",
            f"Data do pagamento: {provento.data_pagamento.isoformat() if provento.data_pagamento else 'não informada'}",
            f"Período de referência: {provento.periodo_referencia}",
            f"Isento de IR: {'Sim' if provento.isento_ir else 'Não'}",
        ]
        if provento.nota_isencao:
            lines.append(f"Nota de isenção: {provento.nota_isencao}")
        return "\n".join(lines)


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
