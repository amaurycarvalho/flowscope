"""Prompt estável e validação estrita da resposta de inferência.

A resposta da LLM é um JSON com uma lista de itens. Itens com tipo ou papel
desconhecidos, sem descrição, sem documento de origem ou sem trecho de
evidência são descartados, preservando apenas os itens auditáveis.
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import date

from flowscope.domain.renda_fixa import (
    FONTE_INFERENCIA,
    InferenciaTitulo,
    PapelTitulo,
    TipoTitulo,
)

#: Orçamento máximo de caracteres do resumo enviado à LLM.
ORCAMENTO_RESUMO = 12000

#: Quantidade máxima de itens aceitos em uma única resposta.
MAX_ITENS = 20

#: Instruções estáveis da inferência, reutilizáveis como prefixo de sistema.
SYSTEM_PROMPT = (
    "Você extrai direitos e obrigações de renda fixa citados em resumos de "
    "Relatórios Gerenciais e Informes Mensais de fundos imobiliários. "
    "Responda somente com JSON válido, sem markdown, no formato exato: "
    '{"itens": [{"tipo": "...", "papel": "obrigacao|direito", '
    '"descricao": "...", "documento": "...", "trecho": "...", '
    '"confianca": 0.0}]}. '
    "Use apenas tipos conhecidos: debenture, debenture_conversivel, "
    "nota_comercial, cri, cra, lci, lca, cdb, letra_financeira ou outro. "
    "Use papel obrigacao quando o fundo emite ou deve o título e direito "
    "quando o fundo o mantém. Inclua em 'trecho' uma passagem literal do "
    "resumo e em 'documento' o documento de origem. Não invente títulos, "
    "emissores ou valores e não use conhecimento externo ao resumo. "
    'Se não houver itens, responda {"itens": []}.'
)

def _normalizar_texto(valor: object) -> str:
    """Remove acentos, caixa e pontuação para comparar rótulos."""
    texto = unicodedata.normalize("NFKD", str(valor or ""))
    sem_acento = "".join(char for char in texto if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", sem_acento.casefold()).strip()


_TIPOS: dict[str, TipoTitulo] = {}
for _tipo in TipoTitulo:
    _TIPOS[_normalizar_texto(_tipo.value)] = _tipo
    _TIPOS[_normalizar_texto(_tipo.rotulo)] = _tipo
_TIPOS.update(
    {
        "debentures": TipoTitulo.DEBENTURE,
        "debenture conversivel": TipoTitulo.DEBENTURE_CONVERSIVEL,
        "notas comerciais": TipoTitulo.NOTA_COMERCIAL,
        "certificado de recebiveis imobiliarios": TipoTitulo.CRI,
        "certificados de recebiveis imobiliarios": TipoTitulo.CRI,
        "certificado de recebiveis do agronegocio": TipoTitulo.CRA,
        "letras financeiras": TipoTitulo.LETRA_FINANCEIRA,
    }
)

_PAPEIS = {
    "obrigacao": PapelTitulo.OBRIGACAO,
    "obrigacoes": PapelTitulo.OBRIGACAO,
    "passivo": PapelTitulo.OBRIGACAO,
    "direito": PapelTitulo.DIREITO,
    "direitos": PapelTitulo.DIREITO,
    "ativo": PapelTitulo.DIREITO,
}


def _texto(valor: object) -> str:
    """Normaliza um campo textual da resposta."""
    return str(valor).strip() if isinstance(valor, (str, int, float)) else ""


def _tipo_de(valor: object) -> TipoTitulo | None:
    """Resolve o tipo conhecido a partir do valor ou rótulo informado."""
    return _TIPOS.get(_normalizar_texto(valor))


def _papel_de(valor: object) -> PapelTitulo | None:
    """Resolve o papel a partir do valor informado."""
    return _PAPEIS.get(_normalizar_texto(valor))


def _confianca_de(valor: object) -> float:
    """Retorna a confiança no intervalo ``[0, 1]``, com padrão zero."""
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return 0.0
    return min(1.0, max(0.0, numero))


def montar_entrada(
    ticker: str,
    documento: str,
    resumo: str,
    data_referencia: date | None = None,
) -> str:
    """Monta a entrada compacta e determinística enviada à LLM."""
    data = data_referencia.isoformat() if data_referencia is not None else ""
    return (
        f"TICKER: {ticker}\n"
        f"DOCUMENTO: {documento}\n"
        f"DATA_REFERENCIA: {data}\n"
        "RESUMO:\n"
        f"{resumo[:ORCAMENTO_RESUMO]}"
    )


def _sem_cercas(texto: str) -> str:
    """Remove cercas de markdown que eventualmente envolvam o JSON."""
    limpo = texto.strip()
    if not limpo.startswith("```"):
        return limpo
    limpo = re.sub(r"^```[a-zA-Z]*\s*", "", limpo)
    return re.sub(r"\s*```$", "", limpo).strip()


def _itens_brutos(resposta: str) -> list:
    """Interpreta o JSON e devolve a lista de itens, ou levanta ``ValueError``."""
    try:
        dados = json.loads(_sem_cercas(resposta))
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("resposta da inferência não é JSON válido") from exc
    if isinstance(dados, list):
        return dados
    if isinstance(dados, dict) and isinstance(dados.get("itens"), list):
        return dados["itens"]
    raise ValueError("resposta da inferência sem a lista 'itens'")


def _item_de(
    bruto: object,
    documento: str,
    data_referencia: date | None,
) -> InferenciaTitulo | None:
    """Valida e converte um item bruto, descartando os inválidos."""
    if not isinstance(bruto, dict):
        return None
    tipo = _tipo_de(bruto.get("tipo"))
    papel = _papel_de(bruto.get("papel"))
    descricao = _texto(bruto.get("descricao"))
    origem = _texto(bruto.get("documento")) or documento
    trecho = _texto(bruto.get("trecho")) or _texto(bruto.get("evidencia"))
    if tipo is None or papel is None or not descricao or not origem or not trecho:
        return None
    return InferenciaTitulo(
        tipo=tipo,
        papel=papel,
        descricao=descricao,
        documento=origem,
        trecho=trecho,
        confianca=_confianca_de(bruto.get("confianca")),
        data_referencia=data_referencia,
        fonte=FONTE_INFERENCIA,
        identificacao=_texto(bruto.get("identificacao")),
    )


def interpretar_resposta(
    resposta: str,
    documento: str,
    data_referencia: date | None = None,
) -> list[InferenciaTitulo]:
    """Valida a resposta e devolve somente os itens auditáveis, até o limite."""
    itens: list[InferenciaTitulo] = []
    for bruto in _itens_brutos(resposta)[:MAX_ITENS]:
        item = _item_de(bruto, documento, data_referencia)
        if item is not None:
            itens.append(item)
    return itens
