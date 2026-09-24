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
import queue
import threading
import tkinter as tk
from collections.abc import Callable, Iterable
from tkinter import messagebox, ttk

from flowscope.application.chat import (
    ConsultarChatUseCase,
    ContextoChat,
    ContextoDocumental,
    FonteContexto,
)
from flowscope.domain.chat import ChatMessage, ChatSession
from flowscope.domain.llm import LLMError, LLMPort, LLMUnavailableError
from flowscope.presentation.gui.chat.conhecimento import montar_bloco_conhecimento
from flowscope.presentation.gui.chat.documentos import (
    FAIXA_AUTOMATICA,
    CascataDocumentos,
    faixa_confirmacao,
)
from flowscope.presentation.gui.chat.fundamentos import montar_contexto_fundamentos
from flowscope.presentation.gui.llm.mensagens import mensagem_erro_llm
from flowscope.presentation.gui.widgets.readonly_text import ReadonlyText

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


class ChatPanel(tk.Frame):
    """Painel de chat da watchlist completa, com sessão em memória."""

    def __init__(
        self: "ChatPanel",
        parent: tk.Misc,
        *,
        fundamental_data_provider: Callable[[], dict] | None = None,
        watchlist_provider: Callable[[], list[str]] | None = None,
        llm_factory: Callable[[], LLMPort] | None = None,
        llm_available: Callable[[], bool] | None = None,
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
            llm_factory=llm_factory, confirmar=self._confirmar_no_tk
        )
        self._config_callback = config_callback
        self._status_callback = status_callback
        self._fontes_adicionais = list(fontes_adicionais or [])
        self._confirmation_timeout = confirmation_timeout
        self._fila: queue.Queue = queue.Queue()
        self._processando = False
        self._disponivel = True
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

    # ── Estado de configuração ───────────────────────────────────────

    def avaliar_estado(self: "ChatPanel") -> None:
        """Reavalia a disponibilidade da LLM e ajusta os controles."""
        self._disponivel = bool(self._llm_available())
        self._aplicar_estado()

    def _aplicar_estado(self: "ChatPanel") -> None:
        """Habilita ou desabilita a entrada conforme a configuração."""
        if self._disponivel:
            self._mostrar_configuracao(False)
            self._send_btn.config(state=tk.NORMAL)
            self._entrada.config(state=tk.NORMAL)
        else:
            self._mostrar_configuracao(True)
            self._send_btn.config(state=tk.DISABLED)
            self._entrada.config(state=tk.DISABLED)

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

    def _on_return(self: "ChatPanel", event: tk.Event) -> str:
        """Envia a pergunta ao pressionar Enter sem Shift."""
        if event.state & 0x1:
            return ""
        self._enviar()
        return "break"

    def _enviar(self: "ChatPanel") -> None:
        """Registra a pergunta e inicia a consulta em thread de trabalho."""
        if self._processando or not self._disponivel:
            return
        pergunta = self._texto_entrada()
        if not pergunta:
            return
        self._texto_entrada_set("")
        self._registrar("user", pergunta)
        self._processando = True
        self._send_btn.config(state=tk.DISABLED)
        self._status("Consultando a I.A.…", "")
        snapshot_f = dict(self._fundamental_data_provider() or {})
        snapshot_w = list(self._watchlist_provider() or [])
        threading.Thread(
            target=self._executar,
            args=(pergunta, snapshot_f, snapshot_w),
            daemon=True,
        ).start()
        self.after(20, lambda: self._poll(None))

    def _executar(
        self: "ChatPanel", pergunta: str, fundamentos: dict, watchlist: list[str]
    ) -> None:
        """Monta o contexto e consulta a LLM em thread de trabalho."""
        try:
            contexto = self._montar_contexto(pergunta, fundamentos, watchlist)
            usecase = ConsultarChatUseCase(self._criar_llm())
            resposta = usecase.consultar(pergunta, contexto)
        except LLMUnavailableError as exc:
            self._fila.put(("indisponivel", exc))
        except LLMError as exc:
            self._fila.put(("erro", exc))
        except Exception as exc:
            self._fila.put(("erro", exc))
        else:
            self._fila.put(("ok", resposta))

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

    def _preparar_texto(self: "ChatPanel", chaves: list[str]) -> str:
        """Resolve as chaves e lê o texto integral dos documentos-alvo."""
        alvos = self._cascata.resolver_alvos(chaves)
        return self._cascata.preparar_texto(alvos)

    def _confirmar_leitura(self: "ChatPanel", chaves: list[str]) -> bool:
        """Resolve as chaves e aplica o gate de confirmação no contexto do Tk."""
        alvos = self._cascata.resolver_alvos(chaves)
        return self._cascata.confirmar_leitura(alvos)

    def _confirmar_no_tk(self: "ChatPanel", quantidade: int, nomes: list[str]) -> bool:
        """Pede confirmação na thread do Tk e aguarda a resposta na thread de trabalho."""
        evento = threading.Event()
        caixa: dict = {}
        self._fila.put(("confirmar", quantidade, nomes, evento, caixa))
        evento.wait(self._confirmation_timeout)
        return bool(caixa.get("ok", False))

    def _poll(self: "ChatPanel", _event: object) -> None:
        """Consome a fila de resultados na thread do Tk."""
        try:
            mensagem = self._fila.get_nowait()
        except queue.Empty:
            self.after(20, lambda: self._poll(None))
            return
        if mensagem[0] == "confirmar":
            self._atender_confirmacao(mensagem)
            self.after(10, lambda: self._poll(None))
            return
        self._concluir(mensagem)

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
        tipo = mensagem[0]
        self._processando = False
        if self._disponivel:
            self._send_btn.config(state=tk.NORMAL)
        if tipo == "ok":
            resposta = mensagem[1]
            self._registrar("assistant", resposta.texto, resposta.fontes)
            self._status("Pronto.", "")
        elif tipo == "indisponivel":
            self._on_indisponivel(mensagem[1])
        else:
            self._on_falha(mensagem[1])

    def _on_indisponivel(self: "ChatPanel", exc: BaseException) -> None:
        """Marca o painel como não configurado e exibe a orientação."""
        self._registrar("assistant", mensagem_erro_llm(exc))
        self._disponivel = False
        self._aplicar_estado()
        self._status(mensagem_erro_llm(exc), "⚠")

    def _on_falha(self: "ChatPanel", exc: BaseException) -> None:
        """Exibe e registra uma falha da LLM durante o chat."""
        mensagem = mensagem_erro_llm(exc)
        self._registrar("assistant", mensagem)
        logger.error(
            "Falha no chat: %s: %s", type(exc).__name__, exc, exc_info=exc
        )
        self._status(mensagem, "⚠")

    # ── Sessão, cópia e utilidades ───────────────────────────────────

    def _registrar(
        self: "ChatPanel", role: str, texto: str, fontes: list[str] | None = None
    ) -> None:
        """Acrescenta a mensagem à sessão e ao campo somente-leitura."""
        self._sessao.add_message(
            ChatMessage(role=role, content=texto, sources=list(fontes or []))
        )
        bloco = f"{_ROTULOS.get(role, role)}: {texto}"
        if fontes:
            bloco += "\nFontes: " + ", ".join(fontes)
        self._respostas.insert(tk.END, bloco + "\n\n")
        self._respostas.see(tk.END)

    def limpar(self: "ChatPanel") -> None:
        """Reinicia a sessão e limpa a área de mensagens."""
        self._sessao.clear()
        self._respostas.delete("1.0", tk.END)

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
