"""Montagem do índice compacto de notícias para o contexto do chat.

A primeira camada do contexto é um índice de todos os itens em cache — seção,
data, tipo, título e uma chave curta — cobrindo as quatro categorias e
intercalando os itens mais recentes de cada uma para caber no orçamento. Esta
montagem é regra de aplicação; a apresentação apenas formata o bloco final.
"""

import hashlib
import re
from dataclasses import dataclass
from datetime import date
from itertools import zip_longest
from pathlib import Path

from flowscope.domain.noticias import (
    SECOES_ORDEM,
    NoticiaArquivo,
    normalizar_texto,
)

#: Instrução de como pedir o conteúdo integral das notícias indexadas.
INSTRUCAO_CHAVES = (
    "As notícias abaixo estão indexadas (seção, data, tipo, título e chave). "
    'Para ler o conteúdo integral de uma delas, inclua a sua chave no campo '
    '"documentos" da resposta.'
)

#: Teto de caracteres do índice compacto de notícias no contexto do chat.
TETO_INDICE = 32000

#: Limite de envio automático do índice filtrado, em tokens estimados.
LIMITE_ENVIO_NOTICIAS = 600

#: Caracteres por token na estimativa grosseira do índice.
CARACTERES_POR_TOKEN = 4

#: Padrão de ticker de renda variável (código B3 com 4 letras e dígitos).
_PADRAO_TICKER = re.compile(r"\b[A-Z]{4}\d{1,2}\b", re.IGNORECASE)

#: Comprimento mínimo de uma palavra-chave extraída da pergunta.
_MIN_PALAVRA = 4

#: Palavras comuns da pergunta que não devem filtrar títulos sozinhas.
_STOPWORDS = frozenset({
    "aqui", "assim", "ainda", "algum", "alguma", "antes", "aquela", "aquele",
    "aquilo", "como", "coisa", "depois", "desde", "essa", "esse", "esta",
    "este", "estao", "existe", "fazer", "foram", "isso", "pela", "pelo",
    "podem", "porque", "quais", "qual", "quando", "quanto", "sobre", "temos",
    "tinha", "todo", "todos", "tudo", "vamos", "voce",
})


def estimar_tokens(texto: str) -> int:
    """Estima os tokens de um texto pela razão grosseira de caracteres."""
    return len(texto) // CARACTERES_POR_TOKEN


def termos_da_pergunta(pergunta: str) -> list[str]:
    """Extrai tickers e palavras-chave normalizados da pergunta.

    Os tickers reusam o padrão de renda variável já usado na extração
    estruturada; as palavras-chave são os termos normalizados com comprimento
    mínimo, descartando palavras comuns.
    """
    termos: set[str] = set()
    for bruto in _PADRAO_TICKER.findall(pergunta or ""):
        normalizado = normalizar_texto(bruto)
        if normalizado:
            termos.add(normalizado)
    for palavra in re.findall(r"[a-z0-9]+", normalizar_texto(pergunta or "")):
        if len(palavra) >= _MIN_PALAVRA and palavra not in _STOPWORDS:
            termos.add(palavra)
    return sorted(termos)


def filtrar_por_pergunta(
    escopos: list["NoticiaEscopo"], pergunta: str
) -> list["NoticiaEscopo"]:
    """Filtra os escopos determinísticamente pelos termos da pergunta.

    Cada termo casa com fronteira de palavra contra o título e os metadados
    normalizados do item. Sem termos extraídos, nada é filtrado; sem casamento,
    a lista devolvida é vazia.
    """
    termos = termos_da_pergunta(pergunta)
    if not termos:
        return list(escopos)
    padroes = [
        re.compile(r"\b" + re.escape(termo) + r"\b") for termo in termos
    ]
    filtrados: list[NoticiaEscopo] = []
    for escopo in escopos:
        alvo = normalizar_texto(
            f"{escopo.nome} {escopo.categoria} {escopo.secao}"
        )
        if any(padrao.search(alvo) for padrao in padroes):
            filtrados.append(escopo)
    return filtrados


@dataclass(frozen=True)
class NoticiaEscopo:
    """Notícia em cache com a chave curta usada no escalonamento do chat."""

    secao: str
    nome: str
    data_publicacao: str
    categoria: str
    chave: str
    caminho: Path
    short_summary: str | None = None
    long_summary: str | None = None
    data_ordinal: int = 0

    @property
    def chave_curta(self: "NoticiaEscopo") -> str:
        """Chave curta e estável exibida no índice e pedida pela LLM."""
        return chave_curta(self.chave)


def chave_curta(chave: str) -> str:
    """Deriva uma chave curta e estável a partir da chave relativa do item."""
    return "n" + hashlib.sha1(chave.encode("utf-8")).hexdigest()[:10]


def escopo_de(arquivo: NoticiaArquivo, chave: str) -> NoticiaEscopo:
    """Monta o escopo do chat a partir de um arquivo do catálogo."""
    return NoticiaEscopo(
        secao=arquivo.secao,
        nome=arquivo.nome,
        data_publicacao=arquivo.data_publicacao,
        categoria=arquivo.categoria,
        chave=chave,
        caminho=arquivo.caminho,
        short_summary=arquivo.short_summary,
        long_summary=arquivo.long_summary,
        data_ordinal=arquivo.data_ordinal,
    )


def montar_indice(
    escopos: list[NoticiaEscopo], teto: int = TETO_INDICE
) -> str:
    """Monta o índice compacto respeitando o teto de caracteres."""
    linhas: list[str] = []
    total = len(INSTRUCAO_CHAVES) + 1
    for escopo in intercalar(escopos):
        linha = _linha(escopo)
        if linhas and total + len(linha) + 1 > teto:
            break
        linhas.append(linha)
        total += len(linha) + 1
    return "\n".join([INSTRUCAO_CHAVES, *linhas])[:teto]


def _linha(escopo: NoticiaEscopo) -> str:
    """Formata uma linha do índice com seção, data, tipo, título e chave."""
    return (
        f"[{escopo.secao}] {escopo.data_publicacao} — {escopo.categoria} — "
        f"{escopo.nome} (chave: {escopo.chave_curta})"
    )


def intercalar(escopos: list[NoticiaEscopo]) -> list[NoticiaEscopo]:
    """Ordena por seção (ordem fixa) e intercala, do mais recente ao mais antigo.

    A intercalação garante que todas as categorias apareçam no índice mesmo com
    orçamento curto, em vez de concentrar tudo na primeira seção.
    """
    por_secao = _agrupar_por_secao(escopos)
    filas = [por_secao[secao] for secao in _ordem_secoes(por_secao)]
    return [
        escopo
        for rodada in zip_longest(*filas)
        for escopo in rodada
        if escopo is not None
    ]


def _agrupar_por_secao(
    escopos: list[NoticiaEscopo],
) -> dict[str, list[NoticiaEscopo]]:
    """Agrupa os escopos por seção, ordenando cada grupo do mais recente."""
    por_secao: dict[str, list[NoticiaEscopo]] = {}
    for escopo in escopos:
        por_secao.setdefault(escopo.secao, []).append(escopo)
    for lista in por_secao.values():
        lista.sort(key=_ordem_data, reverse=True)
    return por_secao


def _ordem_data(escopo: NoticiaEscopo) -> date:
    """Interpreta a data de publicação para ordenação, tolerando ausência."""
    if escopo.data_ordinal:
        return date.fromordinal(escopo.data_ordinal)
    return date.min


def _ordem_secoes(por_secao: dict[str, list[NoticiaEscopo]]) -> list[str]:
    """Ordena as seções pela ordem fixa, deixando as desconhecidas ao final."""
    fixas = [secao for secao in SECOES_ORDEM if secao in por_secao]
    extras = [secao for secao in por_secao if secao not in SECOES_ORDEM]
    return fixas + extras
