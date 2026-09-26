"""Widget de chat com I.A. da aba de topo "Chat AI".

O painel mantém a sessão em memória, exibe a conversa em um campo
somente-leitura copiável e envia cada pergunta para uma thread de trabalho que
monta o contexto e consome a porta ``LLMPort``. A thread publica o desfecho em
uma fila consumida na thread do Tk, inclusive os pedidos de confirmação de
leitura do texto integral.

O contexto cobre sempre a watchlist completa: não há seletor de escopo e a LLM
infere o ticker referido a partir da pergunta. Fontes adicionais de contexto
podem ser registradas para changes futuras (``noticias-b3``, ``llm-chat-rag``).
"""

import logging
import tkinter as tk
from collections.abc import Callable, Iterable
from tkinter import messagebox, ttk

from PIL import Image, ImageTk

from flowscope.application.chat import (
    ContextoChat,
    ContextoDocumental,
    FonteContexto,
)
from flowscope.application.documentos.catalogo import CatalogoDocumentos
from flowscope.domain.chat import ChatMessage, ChatSession
from flowscope.domain.llm import LLMPort, LLMUnavailableError
from flowscope.presentation.gui.chat.conhecimento import montar_bloco_conhecimento
from flowscope.presentation.gui.chat.documentos import (
    FAIXA_AUTOMATICA,
    CascataDocumentos,
    faixa_confirmacao,
)
from flowscope.presentation.gui.chat.envio import EnvioMixin
from flowscope.presentation.gui.chat.fundamentos import montar_contexto_fundamentos
from flowscope.presentation.gui.llm.mensagens import mensagem_erro_llm
from flowscope.presentation.gui.widgets.readonly_text import ReadonlyText
from flowscope.presentation.shortcuts import _resolve_icon_path

logger = logging.getLogger("flowscope")

#: Orientação exibida quando nenhum provedor de LLM está configurado.
ORIENTACAO_NAO_CONFIGURADO = (
    "O chat com I.A. ainda não está configurado. Defina um provedor em "
    "\"Configuração\" para começar a conversar."
)

#: Rótulo do cabeçalho da aba única de chat.
TITULO_CHAT = "Chat AI — watchlist completa"

#: Rótulos das mensagens exibidas na conversa.
_ROTULOS = {"user": "Você", "assistant": "Assistente"}

#: Assinatura do callback que confirma a leitura do texto integral.
ConfirmaAlvos = Callable[[int, list[str]], bool]

#: Assinatura de um provedor de fonte adicional dependente da pergunta.
FonteAdicional = Callable[[str], FonteContexto | None]


def mensagem_confirmacao(quantidade: int, nomes: list[str]) -> str | None:
    """Monta o texto do diálogo de confirmação conforme a faixa de quantidade."""
    if faixa_confirmacao(quantidade) == FAIXA_AUTOMATICA:
        return None
    if quantidade <= 7:
        lista = "\n".join(f"• {nome}" for nome in nomes)
        return (
            "Para responder, será necessário ler o texto integral de "
            f"{quantidade} documentos:\n\n{lista}\n\nDeseja prosseguir?"
        )
    return (
        "Para responder, será necessário ler o texto integral de "
        f"{quantidade} documentos. Deseja prosseguir?"
    )


class ChatPanel(EnvioMixin, tk.Frame):
    """Painel de chat da watchlist completa, com sessão em memória."""

    def __init__(
        self: "ChatPanel",
        parent: tk.Misc,
        *,
        fundamental_data_provider: Callable[[], dict] | None = None,
        watchlist_provider: Callable[[], list[str]] | None = None,
        llm_factory: Callable[[], LLMPort] | None = None,
        llm_available: Callable[[], bool] | None = None,
        catalogo: CatalogoDocumentos | None = None,
        cascata: CascataDocumentos | None = None,
        config_callback: Callable[[], None] | None = None,
        status_callback: Callable[[str, str], None] | None = None,
        fontes_adicionais: Iterable[FonteAdicional] | None = None,
        confirmation_timeout: float = 300.0,
    ) -> None:
        """Constrói o painel, a sessão e os controles de envio e cópia."""
        super().__init__(parent)
        self._sessao = ChatSession()
        self._fundamental_data_provider = fundamental_data_provider or dict
        self._watchlist_provider = watchlist_provider or list
        self._llm_factory = llm_factory
        self._llm_available = llm_available or (lambda: True)
        self._cascata = cascata or CascataDocumentos(
            catalog=catalogo,
            llm_factory=llm_factory,
            confirmar=self._confirmar_no_tk,
        )
        self._config_callback = config_callback
        self._status_callback = status_callback
        self._fontes_adicionais = list(fontes_adicionais or [])
        self._confirmation_timeout = confirmation_timeout
        self._init_envio()
        self._disponivel = True
        self._icon_refs: list[ImageTk.PhotoImage] = []
        self._build()
        self.avaliar_estado()

    # ── Construção da interface ──────────────────────────────────────

    def _build(self: "ChatPanel") -> None:
        """Monta o cabeçalho, a área de mensagens e a barra de entrada."""
        self._build_header()
        self._build_mensagens()
        self._build_entrada()

    def _build_header(self: "ChatPanel") -> None:
        """Monta o cabeçalho com o título e os botões de limpar, cópia e config."""
        cabecalho = tk.Frame(self)
        cabecalho.pack(side=tk.TOP, fill=tk.X)
        self._titulo = tk.Label(
            cabecalho, text=TITULO_CHAT, font=("TkDefaultFont", 10, "bold")
        )
        self._titulo.pack(side=tk.LEFT, padx=4, pady=4)
        self._config_btn = ttk.Button(
            cabecalho, text="Configuração", command=self._on_configurar
        )
        self._config_btn.pack(side=tk.RIGHT, padx=4, pady=4)
        self._copy_btn = ttk.Button(
            cabecalho, text="Copiar chat", command=self._copiar_chat
        )
        self._copy_btn.pack(side=tk.RIGHT, padx=4, pady=4)
        self._clear_btn = ttk.Button(
            cabecalho, text="Limpar", command=self._limpar_chat
        )
        self._clear_btn.pack(side=tk.RIGHT, padx=4, pady=4)

    def _build_mensagens(self: "ChatPanel") -> None:
        """Monta a área rolável de respostas em campo somente-leitura."""
        container = tk.Frame(self)
        container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self._respostas = ReadonlyText(
            container, wrap=tk.WORD, height=12, state=tk.NORMAL
        )
        scroll = ttk.Scrollbar(
            container, orient=tk.VERTICAL, command=self._respostas.yview
        )
        self._respostas.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._respostas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))

    def _build_entrada(self: "ChatPanel") -> None:
        """Monta a orientação, o campo de entrada e os botões inferiores."""
        self._orientacao = tk.Label(
            self, text=ORIENTACAO_NAO_CONFIGURADO, fg="gray", wraplength=480,
            justify=tk.LEFT, anchor=tk.W,
        )
        rodape = tk.Frame(self)
        rodape.pack(side=tk.BOTTOM, fill=tk.X)
        self._entrada = tk.Text(rodape, height=3, wrap=tk.WORD)
        self._entrada.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))
        self._entrada.bind("<Return>", self._on_return)
        self._entrada.bind("<Shift-Return>", lambda _event: None)
        self._send_btn = ttk.Button(rodape, text="Enviar", command=self._enviar)
        self._send_btn.pack(side=tk.RIGHT, padx=4, pady=4)
        self._cancel_btn = ttk.Button(
            rodape,
            image=self._load_icon("process-stop.png", size=(16, 16)),
            command=self._cancelar_envio,
            state=tk.DISABLED,
        )
        self._cancel_btn.pack(side=tk.RIGHT, padx=4, pady=4)

    def _load_icon(
        self: "ChatPanel", filename: str, size: tuple = (20, 20)
    ) -> ImageTk.PhotoImage:
        """Carrega um ícone do recurso e o mantém referenciado para o Tk."""
        path = _resolve_icon_path(filename)
        img = Image.open(path).resize(size, Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        self._icon_refs.append(photo)
        return photo

    # ── Estado de configuração ───────────────────────────────────────

    def avaliar_estado(self: "ChatPanel") -> None:
        """Reavalia a disponibilidade da LLM e ajusta os controles."""
        self._disponivel = bool(self._llm_available())
        self._aplicar_estado()

    def _aplicar_estado(self: "ChatPanel") -> None:
        """Habilita ou desabilita a entrada conforme a configuração."""
        if self._disponivel:
            self._mostrar_configuracao(False)
            self._entrada.config(state=tk.NORMAL)
        else:
            self._mostrar_configuracao(True)
            self._entrada.config(state=tk.DISABLED)
        self._atualizar_controles()

    def _tem_fundamentos(self: "ChatPanel") -> bool:
        """Indica se há dados de fundamentos carregados na sub-aba Fundamentos."""
        return bool(self._fundamental_data_provider() or {})

    def _tem_conteudo(self: "ChatPanel") -> bool:
        """Indica se a conversa já possui conteúdo textual exibido."""
        return bool(self.conteudo_sessao().strip())

    def _atualizar_controles(self: "ChatPanel") -> None:
        """Ajusta os botões ao estado de processamento, disponibilidade e conteúdo.

        "Enviar" exige a LLM configurada e fundamentos carregados. "Limpar" e
        "Copiar chat" exigem conteúdo textual na conversa. Durante o envio, os
        três botões de cabeçalho (Limpar, Copiar chat e Configuração) ficam
        desabilitados e voltam ao normal quando o processamento termina.
        """
        processando = self._processando
        self._send_btn.config(
            state=(
                tk.NORMAL
                if self._disponivel and not processando and self._tem_fundamentos()
                else tk.DISABLED
            )
        )
        self._cancel_btn.config(
            state=tk.NORMAL if processando else tk.DISABLED
        )
        self._config_btn.config(
            state=tk.DISABLED if processando else tk.NORMAL
        )
        estado_texto = (
            tk.NORMAL
            if self._tem_conteudo() and not processando
            else tk.DISABLED
        )
        self._clear_btn.config(state=estado_texto)
        self._copy_btn.config(state=estado_texto)

    def _mostrar_configuracao(self: "ChatPanel", visivel: bool) -> None:
        """Exibe ou oculta a orientação de configuração.

        O botão "Configuração" fica no cabeçalho e permanece sempre visível.
        """
        if visivel:
            self._orientacao.pack(side=tk.BOTTOM, fill=tk.X, padx=4)
        else:
            self._orientacao.pack_forget()

    def _on_configurar(self: "ChatPanel") -> None:
        """Abre o diálogo de configuração fornecido pela llm-core."""
        if self._config_callback is not None:
            self._config_callback()

    # ── Envio e resposta ─────────────────────────────────────────────

    def _criar_llm(self: "ChatPanel") -> LLMPort:
        """Cria a porta de completion a partir da fábrica configurada."""
        if self._llm_factory is None:
            raise LLMUnavailableError("Fábrica de LLM não configurada.")
        return self._llm_factory()

    def _montar_contexto(
        self: "ChatPanel", pergunta: str, fundamentos: dict, watchlist: list[str]
    ) -> ContextoChat:
        """Monta o contexto documental e os blocos estáticos da pergunta.

        O escopo é sempre a watchlist completa; a LLM infere o ticker referido
        a partir da pergunta.
        """
        resumos, _alvos = self._cascata.montar_resumos(None, watchlist)
        documental = ContextoDocumental(
            resumos=resumos,
            preparar_texto=self._preparar_texto,
            confirmar=self._confirmar_leitura,
        )
        return ContextoChat(
            conhecimento=montar_bloco_conhecimento(),
            fundamentos=montar_contexto_fundamentos(fundamentos, None, watchlist),
            documentos=documental,
            fontes_adicionais=self._preparar_fontes_adicionais(pergunta),
        )

    def _preparar_fontes_adicionais(
        self: "ChatPanel", pergunta: str
    ) -> list[FonteContexto]:
        """Coleta as fontes adicionais, omitindo as que falham ou vêm vazias."""
        fontes: list[FonteContexto] = []
        for provider in self._fontes_adicionais:
            try:
                fonte = provider(pergunta)
            except Exception:
                logger.warning(
                    "Fonte adicional de contexto falhou; ignorando.", exc_info=True
                )
                continue
            if fonte is not None and fonte.texto:
                fontes.append(fonte)
        return fontes

    def _fontes_escalaveis(self: "ChatPanel") -> list[object]:
        """Fontes adicionais que resolvem chaves para o conteúdo integral.

        A fonte de notícias expõe ``resolver_alvos``/``preparar_texto``; fontes
        que não implementam o escalonamento (apenas texto) são ignoradas aqui.
        """
        return [
            fonte
            for fonte in self._fontes_adicionais
            if callable(getattr(fonte, "resolver_alvos", None))
            and callable(getattr(fonte, "preparar_texto", None))
        ]

    def _preparar_texto(self: "ChatPanel", chaves: list[str]) -> str:
        """Resolve as chaves nos documentos e nas fontes adicionais escaláveis."""
        restantes = set(chaves)
        partes: list[str] = []
        docs = self._cascata.resolver_alvos(chaves)
        if docs:
            partes.append(self._cascata.preparar_texto(docs))
            restantes -= {doc.chave for doc in docs}
        for fonte in self._fontes_escalaveis():
            alvos = fonte.resolver_alvos(restantes)
            if not alvos:
                continue
            partes.append(fonte.preparar_texto(alvos))
            restantes -= {alvo.chave for alvo in alvos}
        return "\n\n".join(parte for parte in partes if parte)

    def _confirmar_leitura(self: "ChatPanel", chaves: list[str]) -> bool:
        """Aplica o gate de confirmação somando documentos e fontes adicionais."""
        nomes = [doc.nome for doc in self._cascata.resolver_alvos(chaves)]
        for fonte in self._fontes_escalaveis():
            nomes.extend(alvo.nome for alvo in fonte.resolver_alvos(chaves))
        if faixa_confirmacao(len(nomes)) == FAIXA_AUTOMATICA:
            return True
        return bool(
            self._confirmar_no_tk(len(nomes), nomes if len(nomes) <= 7 else [])
        )

    def _atender_confirmacao(self: "ChatPanel", mensagem: tuple) -> None:
        """Exibe o diálogo de confirmação e libera a thread de trabalho."""
        _tipo, quantidade, nomes, evento, caixa = mensagem
        caixa["ok"] = self._dialogo_confirmacao(quantidade, nomes)
        evento.set()

    def _dialogo_confirmacao(self: "ChatPanel", quantidade: int, nomes: list[str]) -> bool:
        """Exibe o diálogo de confirmação de leitura do texto integral."""
        texto = mensagem_confirmacao(quantidade, nomes)
        if texto is None:
            return True
        return bool(
            messagebox.askyesno("Confirmar leitura de documentos", texto, parent=self)
        )

    def _concluir(self: "ChatPanel", mensagem: tuple) -> None:
        """Aplica o desfecho da consulta e reabilita a entrada."""
        _geracao, tipo, payload = mensagem
        self._processando = False
        if tipo == "ok":
            resposta = payload
            self._registrar("assistant", resposta.texto, resposta.fontes)
            self._status("Pronto.", "")
        elif tipo == "indisponivel":
            self._on_indisponivel(payload)
        else:
            self._on_falha(payload)
        self._atualizar_controles()

    def _on_indisponivel(self: "ChatPanel", exc: BaseException) -> None:
        """Marca o painel como não configurado e exibe a orientação."""
        self._registrar(
            "assistant", mensagem_erro_llm(exc), enviar_ao_modelo=False
        )
        self._disponivel = False
        self._aplicar_estado()
        self._status(mensagem_erro_llm(exc), "⚠")

    def _on_falha(self: "ChatPanel", exc: BaseException) -> None:
        """Exibe e registra uma falha da LLM durante o chat."""
        mensagem = mensagem_erro_llm(exc)
        self._registrar("assistant", mensagem, enviar_ao_modelo=False)
        logger.error(
            "Falha no chat: %s: %s", type(exc).__name__, exc, exc_info=exc
        )
        self._status(mensagem, "⚠")

    # ── Sessão, cópia e utilidades ───────────────────────────────────

    def _registrar(
        self: "ChatPanel",
        role: str,
        texto: str,
        fontes: list[str] | None = None,
        enviar_ao_modelo: bool = True,
    ) -> None:
        """Acrescenta a mensagem à sessão e ao campo somente-leitura."""
        self._sessao.add_message(
            ChatMessage(
                role=role,
                content=texto,
                sources=list(fontes or []),
                enviar_ao_modelo=enviar_ao_modelo,
            )
        )
        bloco = f"{_ROTULOS.get(role, role)}: {texto}"
        if fontes:
            bloco += "\nFontes: " + ", ".join(fontes)
        self._respostas.insert(tk.END, bloco + "\n\n")
        self._respostas.see(tk.END)
        self._atualizar_controles()

    def limpar(self: "ChatPanel") -> None:
        """Reinicia a sessão e limpa a área de mensagens."""
        self._sessao.clear()
        self._respostas.delete("1.0", tk.END)
        self._atualizar_controles()

    def _limpar_chat(self: "ChatPanel") -> None:
        """Pede confirmação e reinicia a conversa como se começasse agora."""
        confirmado = messagebox.askyesno(
            "Limpar conversa",
            "Deseja limpar toda a conversa? Esta ação não pode ser desfeita.",
            parent=self,
        )
        if confirmado:
            self.limpar()

    def conteudo_sessao(self: "ChatPanel") -> str:
        """Retorna o texto da sessão exibida no painel."""
        return self._respostas.get("1.0", "end-1c")

    def _copiar_chat(self: "ChatPanel") -> None:
        """Copia o conteúdo da sessão para a área de transferência."""
        texto = self.conteudo_sessao()
        if not texto:
            return
        try:
            import pyxclip

            pyxclip.copy(texto)
        except (OSError, ImportError):
            self.clipboard_clear()
            self.clipboard_append(texto)
        self._status("Chat copiado!", "✓")

    def _texto_entrada(self: "ChatPanel") -> str:
        """Lê o texto da entrada, sem espaços nas extremidades."""
        return self._entrada.get("1.0", "end-1c").strip()

    def _texto_entrada_set(self: "ChatPanel", texto: str) -> None:
        """Substitui o conteúdo da entrada."""
        self._entrada.delete("1.0", tk.END)
        if texto:
            self._entrada.insert("1.0", texto)

    def _status(self: "ChatPanel", msg: str, icon: str) -> None:
        """Repassa uma mensagem para a barra de status, quando houver callback."""
        if self._status_callback is not None:
            self._status_callback(msg, icon)
