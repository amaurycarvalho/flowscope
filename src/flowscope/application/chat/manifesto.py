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

#: Teto de caracteres de um metadado para integrar a seção de metadados.
TETO_METADADO = 120

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

#: Cabeçalho do mapa dos caminhos canônicos.
_CABECALHO_MAPA = "## Mapa da árvore"


def _mapa_arvore(arvore: ArvoreConhecimento) -> str:
    """Descreve os caminhos canônicos apenas dos ramos existentes.

    Ramos internos vazios são omitidos da árvore; anunciá-los aqui induziria a
    LLM a navegar caminhos inexistentes e receber ``nao_interno``/
    ``caminho_invalido``.
    """
    linhas = [_CABECALHO_MAPA, "- " + ", ".join(_caminhos_flowscope(arvore))]
    fundamentos = _caminhos_fundamentos(arvore)
    if fundamentos:
        linhas.append("- " + ", ".join(fundamentos))
    for caminho, descricao in _RAMOS_CANONICOS:
        if arvore.existe(caminho):
            linhas.append(f"- {descricao}")
    return "\n".join(linhas)


def _caminhos_flowscope(arvore: ArvoreConhecimento) -> list[str]:
    """Lista os formatos de caminho do ramo ``/flowscope`` presentes."""
    caminhos = ["/flowscope/meta/<chave>"]
    if arvore.existe("/flowscope/abas"):
        caminhos.append("/flowscope/abas/<aba>")
        caminhos.append("/flowscope/abas/<aba>/subabas/<sub>")
    if arvore.existe("/flowscope/indicadores"):
        caminhos.append("/flowscope/indicadores/<indicador>")
    return caminhos


def _caminhos_fundamentos(arvore: ArvoreConhecimento) -> list[str]:
    """Lista os formatos de caminho do ramo ``/fundamentos`` presentes."""
    segmentos = (
        ("/fundamentos/tickers", "/fundamentos/tickers"),
        ("/fundamentos/campos", "/fundamentos/campos"),
        ("/fundamentos/valores", "/fundamentos/valores/<ticker>"),
    )
    return [texto for caminho, texto in segmentos if arvore.existe(caminho)]


#: Ramos canônicos e a descrição dos seus formatos de caminho.
_RAMOS_CANONICOS = (
    (
        "/documentos",
        (
            "/documentos/tickers, /documentos/<ticker>/indice, "
            "/documentos/<ticker>/<chave>/curto, /documentos/<ticker>/<chave>/longo, "
            "/documentos/<ticker>/<chave>/texto"
        ),
    ),
    (
        "/guidance",
        "/guidance/<ticker>/indice, /guidance/<ticker>/<ano>/<mes>/<guidance>",
    ),
    (
        "/direitos-obrigacoes",
        "/direitos-obrigacoes/direitos, /direitos-obrigacoes/obrigacoes",
    ),
    (
        "/noticias",
        (
            "/noticias/grupos, /noticias/<grupo>/indice, "
            "/noticias/<grupo>/<chave>/titulo, /noticias/<grupo>/<chave>/resumo, "
            "/noticias/<grupo>/<chave>/texto"
        ),
    ),
)

#: Descrição da árvore e das operações de navegação.
PROTOCOLO = (
    "### Operações\n"
    "- listar(caminho) -> filhos imediatos (nome + metadado curto)\n"
    "- obter(caminho, offset, limite) -> conteúdo do nó; para textos longos, "
    "leia em páginas sucessivas com `offset`/`limite` até `continua` ser "
    "falso\n"
    "- contar(caminho) -> nº de nós na subárvore\n"
    "- existe(caminho) -> booleano\n"
    "- buscar(caminho, regex, em=[...], max) -> nós cujos campos casam "
    "(busca determinística)\n"
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
    "- Recomendado: usar contar/existe antes de listar em ramos grandes; "
    "para grupos grandes use o nó `indice` ou `buscar` em vez de listar tudo.\n"
    "- Se `buscar_semantico` responder `indice_indisponivel`, use "
    "`buscar(caminho, regex, em=[...])` (busca determinística por campos) — "
    "não desista da busca.\n\n"
    "### Como responder\n"
    "- Nunca responda prometendo navegar (\"vou abrir\", \"preciso ler\"): se "
    "faltam dados, emita `solicitacoes` com `resposta: null` e só finalize "
    "quando o conteúdo necessário já estiver no contexto navegado.\n"
    "- Use o `foco` (último caminho obtido) para \"esse documento\"/\"nesse RG\" "
    "e não reabra a análise de um alvo já obtido."
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
        if (
            no.metadado
            and no.metadado != no.nome
            and len(no.metadado) <= TETO_METADADO
            and not no.caminho.startswith("/documentos/")
        ):
            linhas.append(f"- {no.caminho}: {no.metadado}")
    return linhas


def _chaves(arvore: ArvoreConhecimento) -> list[str]:
    """Monta as linhas das listas de chaves, incluindo as sub-abas por aba."""
    linhas: list[str] = []
    for rotulo, caminho in _RAMOS_CHAVES.items():
        nomes = _nomes(arvore, caminho)
        if nomes:
            linhas.append(f"- {rotulo}: {', '.join(nomes)}")
    linhas.extend(_subabas(arvore))
    return linhas


def _subabas(arvore: ArvoreConhecimento) -> list[str]:
    """Lista as sub-abas de cada aba presente na árvore."""
    linhas: list[str] = []
    for aba in _nomes(arvore, "/flowscope/abas"):
        subabas = _nomes(arvore, f"/flowscope/abas/{aba}")
        if subabas:
            linhas.append(f"- subabas {aba}: {', '.join(subabas)}")
    return linhas


#: Ramos de topo cuja presença é anunciada na descrição do manifesto.
_RAIZES_DESCRICAO = (
    "/flowscope",
    "/fundamentos",
    "/documentos",
    "/guidance",
    "/direitos-obrigacoes",
    "/noticias",
)


def _descricao(arvore: ArvoreConhecimento) -> str:
    """Descreve a árvore listando apenas os ramos de topo presentes."""
    presentes = [raiz for raiz in _RAIZES_DESCRICAO if arvore.existe(raiz)]
    return (
        "Você tem acesso a uma árvore navegável montada a partir do estado "
        "local. Ela contém: " + ", ".join(presentes) + "."
    )


def _playbook(arvore: ArvoreConhecimento) -> str:
    """Descreve o playbook por intenção apenas dos ramos presentes.

    Anunciar caminhos de ramos ausentes induziria a LLM a navegar caminhos
    inexistentes; por isso cada linha só entra quando o ramo existe.
    """
    linhas = ["### Playbook por intenção"]
    if arvore.existe("/guidance"):
        linhas.append(
            "- Evolução/histórico de guidance -> /guidance/<ticker>/indice e, "
            "para detalhe, a folha do mês"
        )
        linhas.append(
            "- Relatório Gerencial mensal -> /guidance/<ticker>/indice associa o "
            "RG de cada período; abra o texto integral do documento "
            "correspondente em /documentos/<ticker>/<chave>/texto"
        )
    if arvore.existe("/documentos"):
        linhas.append(
            "- Documento/relatório mais recente -> /documentos/<ticker>/indice"
        )
        linhas.append(
            "- Comentar/analisar um documento (ex.: 'comente o RG', 'o que mais "
            "há de relevante') -> abra o texto integral "
            "/documentos/<ticker>/<chave>/texto do alvo; não responda só com "
            "curto/longo"
        )
        linhas.append(
            "- Ler um documento longo por completo -> abra "
            "/documentos/<ticker>/<chave>/texto em páginas sucessivas via "
            "obter com `offset`/`limite` até `continua` ser falso"
        )
        linhas.append(
            "- Resumo curto de um documento -> abra "
            "/documentos/<ticker>/<chave>/curto de cada chave do índice (o "
            "índice traz só uma prévia, não o resumo completo)"
        )
        linhas.append(
            "- Resumo longo de um documento -> abra "
            "/documentos/<ticker>/<chave>/longo de cada chave do índice"
        )
    if arvore.existe("/flowscope"):
        linhas.append(
            "- Objetivo/funcionalidades do aplicativo -> /flowscope/meta e "
            "/flowscope/abas/<aba>/subabas/<sub>"
        )
    return "\n".join(linhas) if len(linhas) > 1 else ""


def _renderizar(
    arvore: ArvoreConhecimento, metadados: list[str], chaves: list[str]
) -> str:
    """Renderiza o manifesto com as seções determinísticas."""
    partes = [
        "# Árvore de conhecimento do FlowScope",
        PERSONA,
        "## Descrição",
        _descricao(arvore),
        _mapa_arvore(arvore),
    ]
    playbook = _playbook(arvore)
    if playbook:
        partes.append(playbook)
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
