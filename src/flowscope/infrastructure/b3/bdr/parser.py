"""Parser do texto de avisos aos acionistas de BDR.

Extrai, quando presentes, o valor do dividendo por BDR em reais, a data-com, a
data de pagamento e o tipo do evento (dividendo ou juros sobre capital próprio),
além do código ISIN, do nome do depositário e do nome da empresa. Avisos cujo
texto não permita extrair valor e data-com são descartados.
"""

import re
from datetime import date
from decimal import Decimal

from flowscope.domain.bdr import DividendoBdr
from flowscope.infrastructure.fii.fundamentus.normalizers import (
    para_data,
    para_decimal,
)

_VALOR_POR_BDR = re.compile(
    r"R\$\s*([\d.]+,\d+)\s*(?:por|/)\s*BDR", re.IGNORECASE
)
_DATA_COM = (
    re.compile(r"titulares de BDRs? em\s+(\d{2}/\d{2}/\d{4})", re.IGNORECASE),
    re.compile(
        r"entitled BDR Shareholders on\s+(\d{2}/\d{2}/\d{4})", re.IGNORECASE
    ),
)
_DATA_PAGAMENTO = (
    re.compile(
        r"data de pagamento\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})", re.IGNORECASE
    ),
    re.compile(r"pago no dia\s+(\d{2}/\d{2}/\d{4})", re.IGNORECASE),
    re.compile(
        r"payment will be completed on\s+(\d{2}/\d{2}/\d{4})", re.IGNORECASE
    ),
)
_ISIN = re.compile(r"\b([A-Z]{2}[A-Z0-9]{9}\d)\b")
_TIPO_JCP = re.compile(r"juros sobre capital", re.IGNORECASE)
_TIPO_DIVIDENDO = re.compile(r"dividendo", re.IGNORECASE)

#: Nível do programa de BDR informado no aviso (PT e EN).
_NIVEL_PROGRAMA = (
    re.compile(r"Programa de BDR\s+(Nível\s+[^,]+?)\s+da", re.IGNORECASE),
    re.compile(
        r"(Unsponsored\s+Level\s+[^,]+?)\s+BDR Program", re.IGNORECASE
    ),
)
#: Observação fiscal do aviso (dedução de IR/IOF/tarifa).
_OBSERVACAO = (
    re.compile(r"Obs\.:\s*(.+?)\.(?:\s|$)", re.IGNORECASE),
    re.compile(r"PS:\s*(.+?)\.(?:\s|$)", re.IGNORECASE),
)

#: Padrões rotulados (``Depositário: X``), aplicados no texto original.
_DEPOSITARIO_ROTULO = (
    re.compile(r"deposit[aá]rio\s*[:\-]\s*([^\n:]+)", re.IGNORECASE),
)
#: Padrões em prosa usados nos avisos reais da CVM.
_DEPOSITARIO_REAL = (
    re.compile(
        r"(?:O|A|Os|As)\s+([A-ZÀ-Ú][^,]{1,60}?)\s*,\s*"
        r"na qualidade de deposit[aá]rio",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:The|The bank)\s+([A-ZÀ-Ú][^,]{1,60}?)\s*,\s*as Depositary",
        re.IGNORECASE,
    ),
)
_EMPRESA_ROTULO = (
    re.compile(r"empresa\s*[:\-]\s*([^\n:]+)", re.IGNORECASE),
)
_EMPRESA_REAL = (
    re.compile(
        r"\bda\s+([A-ZÀ-Ú][^,]{1,60}?)\s*,\s*c[óo]digo\s+ISIN",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bof\s+([A-ZÀ-Ú][^,]{1,60}?)\s*\(Company\)", re.IGNORECASE
    ),
)

_TIPO_DIVIDENDOS = "Dividendos"
_TIPO_JCP_TEXTO = "Juros sobre Capital Próprio"


def parse_dividendo(texto: str) -> DividendoBdr | None:
    """Extrai um dividendo do texto do aviso, ou ``None`` sem valor/data-com."""
    if not texto:
        return None
    plano = _achatar(texto)
    valor = _valor_por_bdr(plano)
    data_com = _primeira_data(_DATA_COM, plano)
    if valor is None or data_com is None:
        return None
    return DividendoBdr(
        valor=valor,
        data_com=data_com,
        data_pagamento=_primeira_data(_DATA_PAGAMENTO, plano),
        tipo=_tipo(plano),
        isin=_primeiro_texto(_ISIN, plano),
        depositario=_depositario(texto, plano),
        empresa=_empresa(texto, plano),
        nivel_programa=_primeiro_texto_grupos(_NIVEL_PROGRAMA, plano),
        observacao=_primeiro_texto_grupos(_OBSERVACAO, plano),
    )


def _achatar(texto: str) -> str:
    """Colapsa espaços e quebras de linha para simplificar as expressões."""
    return re.sub(r"\s+", " ", texto).strip()


def _valor_por_bdr(texto: str) -> Decimal | None:
    """Extrai o valor por BDR do texto."""
    match = _VALOR_POR_BDR.search(texto)
    if match is None:
        return None
    return para_decimal(match.group(1))


def _primeira_data(
    padroes: tuple[re.Pattern[str], ...], texto: str
) -> date | None:
    """Retorna a primeira data capturada por qualquer um dos padrões."""
    for padrao in padroes:
        match = padrao.search(texto)
        if match is not None:
            data = para_data(match.group(1))
            if data is not None:
                return data
    return None


def _primeiro_texto(padrao: re.Pattern[str], texto: str) -> str | None:
    """Retorna o primeiro grupo textual capturado pelo padrão."""
    match = padrao.search(texto)
    if match is None:
        return None
    valor = match.group(1).strip()
    return valor or None


def _primeiro_texto_grupos(
    padroes: tuple[re.Pattern[str], ...], texto: str
) -> str | None:
    """Retorna o primeiro grupo textual capturado por qualquer padrão."""
    for padrao in padroes:
        valor = _primeiro_texto(padrao, texto)
        if valor:
            return valor
    return None


def _depositario(texto: str, plano: str) -> str | None:
    """Extrai o depositário do rótulo ou da prosa do aviso."""
    return _primeiro_texto_grupos(_DEPOSITARIO_ROTULO, texto) or (
        _primeiro_texto_grupos(_DEPOSITARIO_REAL, plano)
    )


def _empresa(texto: str, plano: str) -> str | None:
    """Extrai a empresa do rótulo ou da prosa do aviso."""
    return _primeiro_texto_grupos(_EMPRESA_ROTULO, texto) or (
        _primeiro_texto_grupos(_EMPRESA_REAL, plano)
    )


def _tipo(texto: str) -> str | None:
    """Detecta o tipo do evento no texto."""
    if _TIPO_JCP.search(texto):
        return _TIPO_JCP_TEXTO
    if _TIPO_DIVIDENDO.search(texto):
        return _TIPO_DIVIDENDOS
    return None
