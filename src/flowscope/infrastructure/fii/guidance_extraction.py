"""Extração determinística do guidance de distribuição de Relatórios Gerenciais.

Normaliza o texto, descarta menções não relacionadas (glossário e ``forward
guidance``) e extrai valor (único, faixa, banda ou múltiplos por cota) e período
de validade por expressões regulares. É o caminho usado quando a LLM não está
disponível ou falha. A leitura de PDF é tolerante: um arquivo ilegível resulta
em texto vazio e ausência de guidance, preservando o cache.
"""

import logging
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from flowscope.domain.fii.guidance import Guidance
from flowscope.infrastructure.b3.bdr.text import extrair_texto

logger = logging.getLogger("flowscope")

#: Número monetário curto aceito (ex.: ``0,85``, ``0.10``, ``1.234``).
_NUM = r"\d{1,3}(?:[.,]\d{2,3})?"

_MENCAO = re.compile(r"guidance", re.IGNORECASE)
_FORWARD = re.compile(r"\bforward\s+guidance\b", re.IGNORECASE)
_GLOSSARIO = re.compile(
    r"guidance\s*[:]\s*(proje[çc][ãa]o|defini[çc][ãa]o|previs[ãa]o|estimativa)",
    re.IGNORECASE,
)

#: Padrões de período de validade reconhecidos, preservados como no relatório.
_PERIODOS = (
    re.compile(r"\b\d{1,2}[ST]\d{2}\b", re.IGNORECASE),
    re.compile(r"\bpr[óo]ximos?\s+\d+\s+meses\b", re.IGNORECASE),
    re.compile(r"\brestante\s+do\s+ano(?:\s+de\s+\d{4})?\b", re.IGNORECASE),
    re.compile(r"\bat[ée]\s+o\s+fim\s+do\s+ano(?:\s+de\s+\d{4})?\b", re.IGNORECASE),
    re.compile(r"\b[a-zç]{3}/\d{2}\s+a\s+[a-zç]{3}/\d{2}\b", re.IGNORECASE),
    re.compile(r"\bnext\s+\d+\s+months\b", re.IGNORECASE),
    re.compile(r"\bsegundo\s+semestre\s+de\s+\d{4}\b", re.IGNORECASE),
)

_MONEY = re.compile(rf"R\$\s*({_NUM})", re.IGNORECASE)
_RANGE = re.compile(
    rf"R\$\s*({_NUM})\s*(?:a|e|to|at[ée])\s*(?:R\$\s*)?({_NUM})",
    re.IGNORECASE,
)
_BANDA_SUP = re.compile(rf"banda\s+superior\s*:?\s*R\$\s*({_NUM})", re.IGNORECASE)
_BANDA_INF = re.compile(rf"banda\s+inferior\s*:?\s*R\$\s*({_NUM})", re.IGNORECASE)
_COTA = re.compile(r"\bcotas?\b|\bunits?\b", re.IGNORECASE)

_ESPACOS = re.compile(r"\s+")
_RUN_LETRAS = re.compile(r"(?<!\S)([A-Za-zÀ-ÿ])(?: ([A-Za-zÀ-ÿ])){2,}(?!\S)")

_LARGURA_ANTES = 80
_LARGURA_DEPOIS = 260
_RAIO_VALOR = 60


def normalizar_texto(texto: str | None) -> str:
    """Colapsa espaços e junta sequências de letras separadas por espaços."""
    if not texto:
        return ""
    colapsado = _ESPACOS.sub(" ", texto).strip()
    return _RUN_LETRAS.sub(lambda m: "".join(m.group(0).split(" ")), colapsado)


def extrair_guidance(
    texto: str | None,
    data_relatorio: date,
    caminho_pdf: str | None = None,
) -> Guidance | None:
    """Extrai o guidance de distribuição do texto, ou ``None`` quando ausente."""
    normalizado = normalizar_texto(texto)
    if not normalizado:
        return None
    for posicao in _mencoes_validas(normalizado):
        inicio = max(0, posicao - _LARGURA_ANTES)
        fim = min(len(normalizado), posicao + _LARGURA_DEPOIS)
        guidance = _extrair_da_janela(
            normalizado[inicio:fim], data_relatorio, caminho_pdf
        )
        if guidance is not None:
            return guidance
    return None


def extrair_guidance_de_pdf(
    caminho: Path, data_relatorio: date
) -> Guidance | None:
    """Lê o PDF com tolerância a falhas e extrai o guidance, se houver."""
    try:
        dados = Path(caminho).read_bytes()
    except OSError:
        logger.warning("Falha ao ler PDF de guidance: %s", caminho, exc_info=True)
        return None
    return extrair_guidance(extrair_texto(dados), data_relatorio, str(caminho))


def _mencoes_validas(texto: str) -> list[int]:
    """Retorna as posições de menções a guidance que não são falsos positivos."""
    forward = [m.span() for m in _FORWARD.finditer(texto)]
    return [
        m.start()
        for m in _MENCAO.finditer(texto)
        if not _dentro_de_forward(m.start(), forward)
        and _GLOSSARIO.match(texto, m.start()) is None
    ]


def _dentro_de_forward(posicao: int, intervalos: list[tuple[int, int]]) -> bool:
    """Indica se a posição cai em algum intervalo de ``forward guidance``."""
    return any(inicio <= posicao < fim for inicio, fim in intervalos)


def _extrair_da_janela(
    janela: str, data_relatorio: date, caminho_pdf: str | None
) -> Guidance | None:
    """Extrai o guidance de uma janela ao redor de uma menção."""
    valores = _extrair_valores(janela)
    if valores is None:
        return None
    valor_min, valor_max = valores
    return Guidance(
        valor_min=valor_min,
        valor_max=valor_max,
        periodo=_extrair_periodo(janela),
        data_relatorio=data_relatorio,
        caminho_pdf=caminho_pdf,
    )


def _extrair_valores(janela: str) -> tuple[Decimal, Decimal] | None:
    """Extrai o par (mínimo, máximo) por cota da janela, ou ``None``."""
    bandas = _extrair_bandas(janela)
    if bandas is not None:
        return bandas
    faixa = _extrair_faixa(janela)
    if faixa is not None:
        return faixa
    candidatos = _valores_candidatos(janela)
    if not candidatos:
        return None
    return (min(candidatos), max(candidatos))


def _extrair_bandas(janela: str) -> tuple[Decimal, Decimal] | None:
    """Extrai mínimo e máximo de uma tabela de bandas superior/inferior."""
    numeros = [
        valor
        for valor in (
            _valor_de(_BANDA_SUP, janela),
            _valor_de(_BANDA_INF, janela),
        )
        if valor is not None
    ]
    if not numeros:
        return None
    return (min(numeros), max(numeros))


def _extrair_faixa(janela: str) -> tuple[Decimal, Decimal] | None:
    """Extrai o par (mínimo, máximo) de uma faixa explícita, ou ``None``."""
    faixa = _RANGE.search(janela)
    if faixa is None:
        return None
    primeiro = _decimal(faixa.group(1))
    segundo = _decimal(faixa.group(2))
    if primeiro is None or segundo is None:
        return None
    return (min(primeiro, segundo), max(primeiro, segundo))


def _valores_candidatos(janela: str) -> list[Decimal]:
    """Coleta valores monetários próximos de cota/unit ou de um período."""
    candidatos: list[Decimal] = []
    for m in _MONEY.finditer(janela):
        if not _proximo_de_referencia(janela, m.start(), m.end()):
            continue
        valor = _decimal(m.group(1))
        if valor is not None:
            candidatos.append(valor)
    return candidatos


def _proximo_de_referencia(janela: str, inicio: int, fim: int) -> bool:
    """Indica se o valor está próximo de ``cota``/``unit`` ou de um período."""
    trecho = janela[max(0, inicio - _RAIO_VALOR): fim + _RAIO_VALOR]
    if _COTA.search(trecho):
        return True
    return any(padrao.search(trecho) for padrao in _PERIODOS)


def _extrair_periodo(janela: str) -> str:
    """Retorna o primeiro período de validade reconhecido na janela."""
    melhor: re.Match | None = None
    for padrao in _PERIODOS:
        encontrado = padrao.search(janela)
        if encontrado is not None and (
            melhor is None or encontrado.start() < melhor.start()
        ):
            melhor = encontrado
    return melhor.group(0).strip() if melhor is not None else ""


def _valor_de(padrao: re.Pattern, janela: str) -> Decimal | None:
    """Extrai o primeiro valor monetário casado por ``padrao``."""
    encontrado = padrao.search(janela)
    return _decimal(encontrado.group(1)) if encontrado is not None else None


def _decimal(valor: str) -> Decimal | None:
    """Retorna o ``Decimal`` de um número com vírgula ou ponto."""
    try:
        if "," in valor:
            return Decimal(valor.replace(".", "").replace(",", "."))
        return Decimal(valor)
    except InvalidOperation:
        return None
