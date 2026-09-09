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
