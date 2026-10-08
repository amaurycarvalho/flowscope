"""Widget de chat com I.A. da aba de topo "Chat AI".

O painel mantém a sessão em memória, exibe a conversa em um campo
somente-leitura copiável e submete cada pergunta a um ``BackgroundManager``
local que monta a árvore de conhecimento e consome a porta ``LLMPort``. O
manager publica o desfecho na thread do Tk, inclusive o pedido de autorização
de custo do turno de navegação pelo evento ``Confirmacao``.

O contexto cobre sempre a watchlist completa: não há seletor de escopo e a LLM
infere o ticker referido navegando a árvore.
"""

import logging
import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk

from PIL import Image, ImageTk

from flowscope import __release_date__, __version__
from flowscope.application.chat import (
    ArvoreConhecimento,
    MontarArvore,
    ParNavegacao,
    RespostaChat,
)
from flowscope.application.chat.conhecimento import (
    FonteConhecimento,
    estrutura_conhecimento,
)
from flowscope.application.chat.documentos import FonteDocumentos
from flowscope.application.chat.fundamentos import FonteFundamentos
from flowscope.application.chat.noticias import FonteNoticias
from flowscope.application.documentos.catalogo import CatalogoDocumentos
from flowscope.application.llm_config_port import LLMConfigPort
from flowscope.domain.chat import ChatMessage, ChatSession
from flowscope.domain.llm import LLMPort, LLMUnavailableError
from flowscope.presentation.gui.app_tabs import TAB_CONTENT
from flowscope.presentation.gui.background.events import Confirmacao
from flowscope.presentation.gui.chat.envio import EnvioMixin
from flowscope.presentation.gui.chat.tokens import ContadorTokens
from flowscope.presentation.gui.llm.mensagens import mensagem_erro_llm
from flowscope.presentation.gui.llm.model_selector import SeletorModelo
from flowscope.presentation.gui.widgets.about_panel import (
    APRESENTACAO,
    LICENCA,
    REPOSITORIO_URL,
)
from flowscope.presentation.gui.widgets.readonly_text import ReadonlyText
from flowscope.presentation.shortcuts import _resolve_icon_path

logger = logging.getLogger("flowscope")

#: Orientação exibida quando nenhum provedor de LLM está configurado.
ORIENTACAO_NAO_CONFIGURADO = (
    "O chat com I.A. ainda não está configurado. Defina um provedor no "
    "botão de configuração para começar a conversar."
)

#: Rótulo do cabeçalho da aba única de chat.
TITULO_CHAT = "Chat AI — watchlist completa"

#: Rótulos das mensagens exibidas na conversa.
_ROTULOS = {"user": "Você", "assistant": "Assistente"}


def mensagem_confirmacao_custo(tokens: int) -> str:
    """Monta o texto do diálogo de autorização do custo de um turno."""
    return (
        "Para prosseguir, será necessário enviar "
        f"{tokens} tokens adicionais de navegação. Deseja continuar?"
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
        noticias_catalog: object | None = None,
        config_callback: Callable[[], None] | None = None,
        config_port: LLMConfigPort | None = None,
        model_changed_callback: Callable[[], None] | None = None,
        status_callback: Callable[[str, str], None] | None = None,
        tokens_callback: Callable[[str], None] | None = None,
        token_counter_provider: Callable[[], Callable[[str], int] | None] | None = None,
        cache_support_provider: Callable[[], bool] | None = None,
        context_window_provider: Callable[[], int] | None = None,
        confirmation_timeout: float = 300.0,
    ) -> None:
        """Constrói o painel, a sessão e os controles de envio e cópia."""
        super().__init__(parent)
        self._sessao = ChatSession()
        self._fundamental_data_provider = fundamental_data_provider or dict
        self._watchlist_provider = watchlist_provider or list
        self._llm_factory = llm_factory
        self._llm_available = llm_available or (lambda: True)
        self._catalogo = catalogo
        self._noticias_catalog = noticias_catalog
        self._config_callback = config_callback
        self._config_port = config_port
        self._model_changed_callback = model_changed_callback
        self._status_callback = status_callback
        self._tokens_callback = tokens_callback
        self._token_counter_provider = token_counter_provider
        self._cache_support_provider = cache_support_provider
        self._context_window_provider = context_window_provider
        self._confirmation_timeout = confirmation_timeout
        self._fonte_conhecimento = self._montar_fonte_conhecimento()
        self._navegacao: list[ParNavegacao] = []
        self._assinatura: str | None = None
        self._tokens = ContadorTokens()
        self._init_envio()
        self._disponivel = True
        self._icon_refs: list[ImageTk.PhotoImage] = []
        self._build()
        self.avaliar_estado()
        self._publicar_tokens()

    def _montar_fonte_conhecimento(self: "ChatPanel") -> FonteConhecimento:
        """Monta a fonte do ramo ``/flowscope`` a partir do ``TAB_CONTENT``."""
        abas, subabas = estrutura_conhecimento(TAB_CONTENT)
        return FonteConhecimento(
            {
                "apresentacao": APRESENTACAO,
                "licenca": LICENCA,
                "versao": __version__,
                "release_date": __release_date__,
                "repositorio": REPOSITORIO_URL,
            },
            abas=abas,
            subabas=subabas,
        )

    def destroy(self: "ChatPanel") -> None:
        """Cancela os envios em background antes de destruir o painel."""
        background = getattr(self, "_background", None)
        if background is not None:
            background.cancel_all()
        super().destroy()

    # ── Construção da interface ──────────────────────────────────────

    def _build(self: "ChatPanel") -> None:
        """Monta o cabeçalho, a área de mensagens e a barra de entrada."""
        self._build_header()
        self._build_mensagens()
        self._build_entrada()

    def _build_header(self: "ChatPanel") -> None:
        """Monta o cabeçalho com título, seletor de modelo e botões."""
        cabecalho = tk.Frame(self)
        cabecalho.pack(side=tk.TOP, fill=tk.X)
        self._titulo = tk.Label(
            cabecalho, text=TITULO_CHAT, font=("TkDefaultFont", 10, "bold")
        )
        self._titulo.pack(side=tk.LEFT, padx=4, pady=4)
        self._model_selector = SeletorModelo(
            cabecalho,
            config_port=self._config_port,
            on_config=self._on_configurar,
            on_changed=self._on_model_changed,
        )
        self._model_selector.pack(side=tk.RIGHT, padx=4, pady=4)
        self._config_btn = self._model_selector.botao
        self._copy_btn = ttk.Button(
            cabecalho, text="Copiar chat", command=self._copiar_chat
        )
        self._copy_btn.pack(side=tk.RIGHT, padx=4, pady=4)
        self._clear_btn = ttk.Button(
            cabecalho, text="Limpar", command=self._limpar_chat
        )
        self._clear_btn.pack(side=tk.RIGHT, padx=4, pady=4)

    def _on_model_changed(self: "ChatPanel", provider: str | None = None) -> None:
        """Reavalia o estado após a troca de modelo e notifica o host."""
        self.avaliar_estado()
        if self._model_changed_callback is not None:
            self._model_changed_callback()

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
        """Ajusta os botões ao estado de processamento, disponibilidade e conteúdo."""
        processando = self._processando
        self._send_btn.config(
            state=(
                tk.NORMAL
                if self._disponivel and not processando and self._tem_fundamentos()
                else tk.DISABLED
            )
        )
        self._cancel_btn.config(state=tk.NORMAL if processando else tk.DISABLED)
        self._model_selector.set_enabled(not processando)
        estado_texto = (
            tk.NORMAL if self._tem_conteudo() and not processando else tk.DISABLED
        )
        self._clear_btn.config(state=estado_texto)
        self._copy_btn.config(state=estado_texto)

    def _mostrar_configuracao(self: "ChatPanel", visivel: bool) -> None:
        """Exibe ou oculta a orientação de configuração."""
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

    def montar_arvore(self: "ChatPanel", fundamentos: dict, watchlist: list[str]) -> ArvoreConhecimento:
        """Monta a árvore de conhecimento a partir dos snapshots do envio."""
        fontes = [
            self._fonte_conhecimento,
            FonteFundamentos(fundamentos, watchlist=watchlist),
            FonteDocumentos(catalog=self._catalogo),
        ]
        if self._noticias_catalog is not None:
            fontes.append(FonteNoticias(catalog=self._noticias_catalog))
        return MontarArvore(fontes).montar(watchlist=watchlist)

    def _atender_confirmacao(self: "ChatPanel", confirmacao: Confirmacao) -> None:
        """Exibe o diálogo de confirmação do evento e libera a thread de trabalho."""
        confirmacao.caixa["ok"] = self._dialogo_confirmacao(
            confirmacao.quantidade,
            list(confirmacao.nomes),
            confirmacao.motivo,
        )
        confirmacao.evento.set()

    def _dialogo_confirmacao(
        self: "ChatPanel", quantidade: int, nomes: list[str], motivo: str = "custo"
    ) -> bool:
        """Exibe o diálogo de confirmação do custo do turno de navegação."""
        if motivo != "custo":
            return True
        return bool(
            messagebox.askyesno(
                "Confirmar custo de navegação",
                mensagem_confirmacao_custo(quantidade),
                parent=self,
            )
        )

    def _concluir_ok(self: "ChatPanel", resposta: RespostaChat) -> None:
        """Registra a resposta, acumula a navegação e sinaliza o término."""
        self._navegacao = list(resposta.navegacao)
        self._tokens.acumular_navegacao(sum(par.tokens for par in self._navegacao))
        self._publicar_tokens()
        self._registrar("assistant", resposta.texto, resposta.fontes)
        if resposta.alerta_janela:
            self._status("Contexto próximo da janela do modelo.", "⚠")
        else:
            self._status("Pronto.", "")

    def _concluir_erro(self: "ChatPanel", dados: object, exc: BaseException) -> None:
        """Trata a falha do job conforme a origem (LLM indisponível ou erro)."""
        if dados == "indisponivel":
            self._on_indisponivel(exc)
        else:
            self._on_falha(exc)

    def _on_indisponivel(self: "ChatPanel", exc: BaseException) -> None:
        """Marca o painel como não configurado e exibe a orientação."""
        self._registrar("assistant", mensagem_erro_llm(exc), enviar_ao_modelo=False)
        self._disponivel = False
        self._aplicar_estado()
        self._status(mensagem_erro_llm(exc), "⚠")

    def _on_falha(self: "ChatPanel", exc: BaseException) -> None:
        """Exibe e registra uma falha da LLM durante o chat."""
        mensagem = mensagem_erro_llm(exc)
        self._registrar("assistant", mensagem, enviar_ao_modelo=False)
        logger.error("Falha no chat: %s: %s", type(exc).__name__, exc, exc_info=exc)
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
        """Reinicia a sessão, a navegação acumulada e a área de mensagens."""
        self._sessao.clear()
        self._navegacao = []
        self._assinatura = None
        self._respostas.delete("1.0", tk.END)
        self._tokens.zerar()
        self._publicar_tokens()
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
