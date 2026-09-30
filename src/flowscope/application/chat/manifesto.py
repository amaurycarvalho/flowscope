"""Manifesto estável da árvore de conhecimento (prefixo cacheável).

O manifesto reúne a persona, a descrição da árvore, os metadados curtos, o
protocolo de navegação e as listas de chaves. É renderizado de forma
determinística e byte-a-byte estável enquanto a assinatura do estado não muda,
respeitando um teto de tokens com degradação para "só chaves".
"""

from __future__ import annotations

import hashlib
import os
from collections.abc import Callable, Iterable
from pathlib import Path

from flowscope.application.chat.arvore import ArvoreConhecimento, ErroNavegacao

#: Teto rígido do manifesto, em tokens.
TETO_TOKENS = 4000

#: Razão grosseira de caracteres por token usada na ausência de contador.
CARACTERES_POR_TOKEN = 4

#: Persona e regras herdadas do prompt de sistema.
PERSONA = (
    "Você é o assistente do FlowScope, uma ferramenta de análise quantitativa de "
    "fluxo de ordens. Responda apenas com base no contexto navegado. Cite as "
    "fontes (tickers, chaves de notícia, caminhos). Identifique o ticker referido "
    "na pergunta; quando for ambíguo, peça esclarecimento. Declare quando a "
    "resposta vier de navegação anterior e não do estado corrente."
)

#: Mapa dos caminhos canônicos, para a LLM saber como navegar cada ramo.
MAPA_ARVORE = (
    "## Mapa da árvore\n"
    "- /flowscope/meta/<chave>, /flowscope/abas/<aba>/subabas/<sub>, "
    "/flowscope/indicadores/<indicador>\n"
    "- /fundamentos/tickers, /fundamentos/campos, /fundamentos/valores/<ticker>\n"
    "- /documentos/tickers, /documentos/<ticker>/curto, /documentos/<ticker>/longo, "
    "/documentos/<ticker>/texto\n"
    "- /noticias/grupos, /noticias/<grupo>/indice, /noticias/<grupo>/<chave>/titulo, "
    "/noticias/<grupo>/<chave>/resumo, /noticias/<grupo>/<chave>/texto"
)

#: Descrição da árvore e das operações de navegação.
PROTOCOLO = (
    "### Operações\n"
    "- listar(caminho) -> filhos imediatos (nome + metadado curto)\n"
    "- obter(caminho) -> conteúdo do nó\n"
    "- contar(caminho) -> nº de nós na subárvore\n"
    "- existe(caminho) -> booleano\n"
    "- buscar(caminho, regex, em=[...], max) -> nós cujos campos casam\n"
    "- buscar_semantico(caminho, consulta, max) -> nós por similaridade\n"
    "- resetar_navegacao() -> descarta o histórico de navegação\n\n"
    "### Formato de resposta (JSON estrito)\n"
    '{"resposta": "<texto ou null>", "solicitacoes": ['
    '{"op": "contar", "caminho": "/documentos/PETR4/*"}]}\n'
    "Se `solicitacoes` estiver vazio, `resposta` é final.\n\n"
    "### Limites\n"
    "- Até 8 operações por turno.\n"
    "- Busca regex: timeout de 100 ms, máx. 50 resultados, padrões "
    "catastróficos bloqueados.\n"
    "- Recomendado: usar contar/existe antes de listar em ramos grandes."
)

#: Ramos cujos filhos viram listas de chaves no manifesto.
_RAMOS_CHAVES = {
    "tickers": "/fundamentos/tickers",
    "campos": "/fundamentos/campos",
    "abas": "/flowscope/abas",
    "indicadores": "/flowscope/indicadores",
    "grupos_noticias": "/noticias/grupos",
}


def assinatura_estado(
    caminhos: Iterable[Path], watchlist: Iterable[str]
) -> str:
    """Deriva a assinatura do estado a partir de arquivos e watchlist.

    Usa o caminho e o mtime de cada arquivo, além da watchlist, de forma
    determinística e independente da ordem de entrada.
    """
    digest = hashlib.sha256()
    for caminho in sorted({str(c) for c in caminhos}):
        digest.update(caminho.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(str(_mtime(caminho)).encode("ascii"))
        digest.update(b"\x00")
    for ticker in watchlist:
        digest.update(str(ticker).encode("utf-8"))
        digest.update(b"\x00")
    return digest.hexdigest()


def _mtime(caminho: str) -> int:
    """Devolve o mtime em nanossegundos, tolerando arquivo ausente."""
    try:
        return os.stat(caminho).st_mtime_ns
    except OSError:
        return 0


def estimar_tokens(texto: str) -> int:
    """Estima os tokens pela razão grosseira de caracteres."""
    return len(texto) // CARACTERES_POR_TOKEN


def _nomes(arvore: ArvoreConhecimento, caminho: str) -> list[str]:
    """Lista os nomes dos filhos de um ramo, tolerando ramo ausente ou folha."""
    try:
        return sorted(no.nome for no in arvore.listar(caminho))
    except ErroNavegacao:
        return []


def _metadados(arvore: ArvoreConhecimento) -> list[str]:
    """Coleta os metadados curtos dos ramos, omitindo os redundantes.

    Um metadado igual ao nome do nó não acrescenta informação e apenas infla o
    manifesto (ex.: um nó de campo cujo metadado é o próprio nome).
    """
    linhas: list[str] = []
    for caminho in sorted(arvore._indice):
        no = arvore._indice[caminho]
        if no.metadado and no.metadado != no.nome:
            linhas.append(f"- {no.caminho}: {no.metadado}")
    return linhas


def _chaves(arvore: ArvoreConhecimento) -> list[str]:
    """Monta as linhas das listas de chaves."""
    linhas: list[str] = []
    for rotulo, caminho in _RAMOS_CHAVES.items():
        nomes = _nomes(arvore, caminho)
        if nomes:
            linhas.append(f"- {rotulo}: {', '.join(nomes)}")
    return linhas


def _renderizar(
    arvore: ArvoreConhecimento, metadados: list[str], chaves: list[str]
) -> str:
    """Renderiza o manifesto com as seções determinísticas."""
    partes = [
        "# Árvore de conhecimento do FlowScope",
        PERSONA,
        "## Descrição",
        (
            "Você tem acesso a uma árvore navegável montada a partir do estado "
            "local. Ela contém: /flowscope, /fundamentos, /documentos, /noticias."
        ),
        MAPA_ARVORE,
    ]
    if chaves:
        partes.extend(["## Listas de chaves", *chaves])
    if metadados:
        partes.extend(["## Metadados", *metadados])
    partes.extend(["## Protocolo de navegação", PROTOCOLO])
    return "\n".join(partes)


def montar_manifesto(
    arvore: ArvoreConhecimento,
    persona: str = PERSONA,
    teto_tokens: int = TETO_TOKENS,
    contar_tokens: Callable[[str], int] | None = None,
) -> str:
    """Monta o manifesto, degradando para "só chaves" se exceder o teto."""
    medir = contar_tokens or estimar_tokens
    chaves = _chaves(arvore)
    completo = _renderizar_com_persona(arvore, _metadados(arvore), chaves, persona)
    if medir(completo) <= teto_tokens:
        return completo
    sob_chaves = _renderizar_com_persona(arvore, [], chaves, persona)
    if medir(sob_chaves) <= teto_tokens:
        return sob_chaves
    return _truncar(sob_chaves, teto_tokens)


def _renderizar_com_persona(
    arvore: ArvoreConhecimento,
    metadados: list[str],
    chaves: list[str],
    persona: str,
) -> str:
    """Renderiza o manifesto substituindo a persona."""
    texto = _renderizar(arvore, metadados, chaves)
    return texto.replace(PERSONA, persona, 1)


def _truncar(texto: str, teto_tokens: int) -> str:
    """Corta o manifesto no teto de tokens como último recurso."""
    return texto[: teto_tokens * CARACTERES_POR_TOKEN]
