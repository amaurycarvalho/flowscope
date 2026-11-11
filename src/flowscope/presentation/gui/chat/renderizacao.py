"""Renderização textual da conversa do chat.

Centraliza a formatação de cada mensagem e a reconstrução da área de mensagens
a partir da sessão em memória, de modo que o append e a alternância do checkbox
"Exibir fontes" compartilhem a mesma lógica. As marcações de exibição usam uma
tag Tk de negrito, e a cópia em Markdown é derivada das faixas dessa tag.
"""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont

from flowscope.domain.chat import ChatMessage

#: Rótulos das mensagens exibidas na conversa.
ROTULOS = {"user": "Você", "assistant": "Assistente"}

#: Rótulo do bloco de fontes exibido após a resposta.
ROTULO_FONTES = "Fontes consultadas:"

#: Tag Tk usada para exibir as marcações em negrito.
TAG_MARCADOR = "marcador"

#: Segmento de texto: ``(texto, negrito)``.
Segmento = tuple[str, bool]


def bloco(mensagem: ChatMessage, exibir_fontes: bool) -> list[Segmento]:
    """Monta os segmentos de uma mensagem, incluindo as fontes se exibidas."""
    segmentos: list[Segmento] = [
        (f"{ROTULOS.get(mensagem.role, mensagem.role)}:", True),
        (f" {mensagem.content}", False),
    ]
    if mensagem.role != "assistant" or not exibir_fontes or not mensagem.sources:
        return segmentos
    linhas = [
        f"- {fonte.rotulo} ({fonte.caminho})"
        if fonte.rotulo
        else f"- {fonte.caminho}"
        for fonte in mensagem.sources
    ]
    segmentos.extend(
        (("\n\n", False), (ROTULO_FONTES, True), ("\n" + "\n".join(linhas), False))
    )
    return segmentos


def renderizar(
    widget: tk.Text, mensagens: list[ChatMessage], exibir_fontes: bool
) -> None:
    """Reconstrói o widget somente-leitura a partir das mensagens da sessão."""
    _configurar_marcador(widget)
    widget.delete("1.0", "end")
    for indice, mensagem in enumerate(mensagens):
        if indice:
            widget.insert("end", "\n\n")
        _inserir(widget, bloco(mensagem, exibir_fontes))
    if mensagens:
        widget.insert("end", "\n\n")
    widget.see("end")


def markdown(widget: tk.Text) -> str:
    """Retorna o conteúdo exibido no widget convertido para Markdown.

    As faixas da tag de negrito viram ``**...**``; o restante é copiado como
    texto simples.
    """
    texto = widget.get("1.0", "end-1c")
    intervalos = widget.tag_ranges(TAG_MARCADOR)
    if not intervalos:
        return texto
    partes: list[str] = []
    cursor = 0
    for inicio, fim in zip(intervalos[::2], intervalos[1::2]):
        inicio_offset = _deslocamento(widget, inicio)
        fim_offset = _deslocamento(widget, fim)
        partes.append(texto[cursor:inicio_offset])
        partes.append(f"**{texto[inicio_offset:fim_offset]}**")
        cursor = fim_offset
    partes.append(texto[cursor:])
    return "".join(partes)


def _configurar_marcador(widget: tk.Text) -> None:
    """Configura a tag de negrito derivada da fonte padrão do Tk."""
    if TAG_MARCADOR in widget.tag_names():
        return
    fonte = tkfont.nametofont("TkDefaultFont").copy()
    fonte.configure(weight="bold")
    widget.tag_configure(TAG_MARCADOR, font=fonte)
    widget._fonte_marcador = fonte


def _inserir(widget: tk.Text, segmentos: list[Segmento]) -> None:
    """Insere os segmentos aplicando a tag de negrito quando indicado."""
    for texto, negrito in segmentos:
        if negrito:
            widget.insert("end", texto, TAG_MARCADOR)
        else:
            widget.insert("end", texto)


def _deslocamento(widget: tk.Text, indice: str) -> int:
    """Retorna o deslocamento de caracteres de um índice do Tk."""
    contagem = widget.count("1.0", indice, "chars")
    return int(contagem[0]) if contagem else 0
