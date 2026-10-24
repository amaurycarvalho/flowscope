"""Renderização Markdown dos títulos, agregados e ausências de fonte.

A renderização é pura e compartilhada pela sub-aba Documentos e pelo Chat AI.
Nenhum conteúdo é baixado, extraído, resumido ou interpretado por LLM.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from flowscope.domain.renda_fixa import (
    AusenciaFonte,
    DocumentoRelacionado,
    FonteTitulos,
    InferenciaTitulo,
    TituloAgregado,
    TituloRendaFixa,
)

_SEM_INFORMACAO = "não informado"


def _texto(valor: object) -> str:
    """Formata um valor simples, usando o marcador de ausência quando vazio."""
    if valor is None or str(valor).strip() == "":
        return _SEM_INFORMACAO
    return str(valor).strip()


def _data(valor: date | None) -> str:
    """Formata uma data opcional em ISO."""
    return valor.isoformat() if valor is not None else _SEM_INFORMACAO


def _decimal(valor: Decimal | None) -> str:
    """Formata um decimal opcional sem notação científica."""
    if valor is None:
        return _SEM_INFORMACAO
    return format(valor.normalize(), "f")


def _linha(rotulo: str, valor: object) -> str:
    """Monta uma linha de bullet com o rótulo e o valor formatado."""
    return f"- **{rotulo}:** {_texto(valor)}"


def _secao(titulo: str, linhas: list[str]) -> list[str]:
    """Monta uma seção Markdown apenas quando há linhas."""
    if not linhas:
        return []
    return [f"## {titulo}", *linhas, ""]


def _gerais(titulo: TituloRendaFixa) -> list[str]:
    """Monta as linhas de informações gerais."""
    return [
        _linha(rotulo, valor)
        for rotulo, valor in (
            ("Tipo", titulo.tipo.rotulo),
            ("Emissor legal", titulo.emissor_legal),
            ("CNPJ do emissor", titulo.cnpj_emissor),
            ("Devedor econômico", titulo.devedor),
            ("CNPJ do devedor", titulo.cnpj_devedor),
            ("Identificação", titulo.identificacao),
            ("Emissão", titulo.emissao),
            ("Série", titulo.serie),
            ("Data de emissão", _data(titulo.data_emissao)),
            ("Vencimento", _data(titulo.data_vencimento)),
            ("Indexador", titulo.indexador),
            ("Taxa", titulo.taxa),
            ("Quantidade", _decimal(titulo.quantidade)),
            ("Valor", _decimal(titulo.valor)),
            ("Saldo devedor", _decimal(titulo.saldo_devedor)),
            ("Valor da posição", _decimal(titulo.valor_posicao)),
            ("Fonte", titulo.fonte),
            ("Data de referência", _data(titulo.data_referencia)),
        )
        if valor not in (None, "")
    ]


def _adicionais(titulo: TituloRendaFixa) -> list[str]:
    """Monta as linhas de informações adicionais."""
    return [
        _linha(rotulo, valor)
        for rotulo, valor in (
            ("Garantias", titulo.garantias),
            ("Coobrigação", titulo.coobrigacao),
            ("Lastro", titulo.lastro),
            ("Sobrecolateralização", titulo.sobrecolateralizacao),
            ("Subordinação", titulo.subordinacao),
            ("Características", titulo.caracteristicas),
            ("Condição de alteração de direitos", titulo.condicao_alteracao),
            ("Situação", titulo.situacao),
            ("Classificação de risco", titulo.rating),
            ("Contingências", titulo.contingencias),
            ("Impacto de eventos", titulo.impacto),
            ("Desempenho", titulo.desempenho),
        )
        if valor not in (None, "")
    ]


def _ltv(titulo: TituloRendaFixa) -> list[str]:
    """Monta a seção de LTV, declarando explicitamente quando não informado."""
    if titulo.ltv is None:
        return ["## LTV", "- LTV: não informado", ""]
    return [
        "## LTV",
        _linha("Índice", _decimal(titulo.ltv)),
        _linha("Data", _data(titulo.data_ltv)),
        "",
    ]


def _documento(item: DocumentoRelacionado) -> str:
    """Monta uma linha de link para um documento relacionado."""
    descricao = item.descricao or item.url
    if item.url:
        return f"- [{descricao}]({item.url})"
    return f"- {descricao}"


def _documentos(titulo: TituloRendaFixa) -> list[str]:
    """Monta a seção de documentos relacionados."""
    linhas = [_documento(item) for item in titulo.documentos if item.url]
    return _secao("Documentos relacionados", linhas)


def render_geral(titulo: TituloRendaFixa) -> str:
    """Renderiza apenas as informações gerais do título."""
    return "\n".join(
        [f"# {titulo.nome_exibicao}", "", *_secao("Informações gerais", _gerais(titulo))]
    ).strip()


def render_adicionais(titulo: TituloRendaFixa) -> str:
    """Renderiza apenas as informações adicionais do título."""
    return "\n".join(
        [
            f"# {titulo.nome_exibicao}",
            "",
            *_secao("Informações adicionais", _adicionais(titulo)),
        ]
    ).strip()


def render_ltv_titulo(titulo: TituloRendaFixa) -> str:
    """Renderiza apenas a seção de LTV do título."""
    return "\n".join([f"# {titulo.nome_exibicao}", "", *_ltv(titulo)]).strip()


def render_documentos(titulo: TituloRendaFixa) -> str:
    """Renderiza apenas os documentos relacionados do título."""
    linhas = [f"# {titulo.nome_exibicao}", ""]
    linhas.extend(_documentos(titulo))
    if len(linhas) == 2:
        linhas.extend(["## Documentos relacionados", "- Nenhum documento relacionado.", ""])
    return "\n".join(linhas).strip()


def render_titulo(titulo: TituloRendaFixa) -> str:
    """Renderiza o Markdown completo de um título individual."""
    linhas = [f"# {titulo.nome_exibicao}", ""]
    linhas.extend(_secao("Informações gerais", _gerais(titulo)))
    linhas.extend(_secao("Informações adicionais", _adicionais(titulo)))
    linhas.extend(_ltv(titulo))
    linhas.extend(_documentos(titulo))
    return "\n".join(linhas).strip()


def render_agregado(agregado: TituloAgregado) -> str:
    """Renderiza o resumo de um agregado por ticker."""
    return "\n".join(
        [
            f"# {agregado.rotulo}",
            "",
            _linha("Valor total", _decimal(agregado.valor)),
            _linha("Fonte", agregado.fonte),
            _linha("Data de referência", _data(agregado.data_referencia)),
        ]
    )


def render_ausencia(ausencia: AusenciaFonte) -> str:
    """Renderiza a explicação explícita de ausência de fonte."""
    motivo = ausencia.motivo or (
        "Não há título nem total público por emissor para este tipo."
    )
    return "\n".join([f"# {ausencia.tipo.rotulo}", "", motivo])


def _confianca(valor: float) -> str:
    """Formata a confiança como percentual inteiro."""
    return f"{round(max(0.0, min(1.0, valor)) * 100)}%"


def render_inferencia_geral(item: InferenciaTitulo) -> str:
    """Renderiza a identificação e o aviso de que o item foi inferido."""
    return "\n".join(
        [
            f"# {item.nome_exibicao}",
            "",
            "## Informações gerais",
            _linha("Tipo", item.tipo.rotulo),
            _linha("Papel", item.papel.rotulo),
            _linha("Origem", "inferido pela IA"),
            _linha("Confiança", _confianca(item.confianca)),
            _linha("Fonte", item.fonte),
        ]
    )


def render_inferencia_proveniencia(item: InferenciaTitulo) -> str:
    """Renderiza a evidência textual e a proveniência do item inferido."""
    return "\n".join(
        [
            f"# {item.nome_exibicao}",
            "",
            "## Proveniência",
            _linha("Documento de origem", item.documento),
            _linha("Data de referência", _data(item.data_referencia)),
            _linha("Confiança", _confianca(item.confianca)),
            _linha("Origem", "inferido pela IA"),
            "",
            "## Trecho de evidência",
            item.trecho or _SEM_INFORMACAO,
        ]
    )


def render_inferencia_documento(item: InferenciaTitulo) -> str:
    """Renderiza o documento de origem de um item inferido."""
    return "\n".join(
        [
            f"# {item.nome_exibicao}",
            "",
            "## Documento de origem",
            _linha("Documento", item.documento),
            _linha("Chave", item.chave_documento),
            _linha("Data de referência", _data(item.data_referencia)),
        ]
    )


def render_inferencia(item: InferenciaTitulo) -> str:
    """Renderiza o Markdown completo de um item inferido, com proveniência."""
    return "\n\n".join(
        (
            render_inferencia_geral(item),
            render_inferencia_proveniencia(item),
        )
    )


def render_data_referencia(
    data_referencia: date | None,
    fontes: dict[str, FonteTitulos],
    adquirido_em: str = "",
) -> str:
    """Renderiza o nó de data de referência e proveniência das fontes."""
    linhas = ["# Data de referência", ""]
    linhas.append(_linha("Data de referência", _data(data_referencia)))
    if adquirido_em:
        linhas.append(_linha("Última aquisição", adquirido_em))
    if fontes:
        linhas.extend(["", "## Fontes"])
        for nome, fonte in sorted(fontes.items()):
            linhas.append(
                f"- **{nome}:** {_data(fonte.data_referencia)}"
                + (f" ({fonte.arquivo})" if fonte.arquivo else "")
            )
    return "\n".join(linhas)
