"""Montagem das dependências da interface gráfica principal.

Consome o núcleo neutro de composição (:func:`~flowscope.presentation.composicao.montar_nucleo`)
e acrescenta apenas o que é específico da GUI (presenter, background e a ligação
da lista de tickers), mantendo ``app.py`` restrito à composição da janela.

Os adaptadores de documentos e notícias são reexportados deste módulo por
compatibilidade com os imports existentes.
"""

from flowscope.infrastructure.feature_flags import feature_flag
from flowscope.presentation.composicao import (
    AdaptadoresDocumentos,
    AdaptadoresNoticias,
    AdaptadoresRendaFixa,
    montar_adaptadores_documentos,
    montar_adaptadores_noticias,
    montar_adaptadores_renda_fixa,
    montar_nucleo,
    resolvedor_chave_documento,
    resolver_data_referencia_seguro,
)
from flowscope.presentation.gui.background.job import JobHandle
from flowscope.presentation.gui.background.manager import BackgroundManager
from flowscope.presentation.gui.controller import FlowScopeController
from flowscope.presentation.gui.presenter import FlowScopePresenter

__all__ = [
    "AdaptadoresDocumentos",
    "AdaptadoresNoticias",
    "AdaptadoresRendaFixa",
    "WiringMixin",
    "montar_adaptadores_documentos",
    "montar_adaptadores_noticias",
    "montar_adaptadores_renda_fixa",
    "montar_nucleo",
    "resolvedor_chave_documento",
]


class WiringMixin:
    """Constrói o controller e os providers usados pela janela principal."""

    def _wire_ports(self: "WiringMixin") -> None:
        """Injeta as portas de releases, LLM e clipboard usadas pela janela."""
        from flowscope.infrastructure.clipboard_image import ClipboardImageAdapter
        from flowscope.infrastructure.llm.config_adapter import InfrastructureLLMConfig
        from flowscope.infrastructure.releases import obter_ultima_release

        self._release_checker = obter_ultima_release
        self._clipboard = ClipboardImageAdapter()
        self._llm_config = InfrastructureLLMConfig()
        self._reference_date_provider = resolver_data_referencia_seguro

    def _obter_nucleo(self: "WiringMixin") -> object:
        """Devolve o núcleo neutro, montando-o sob demanda uma única vez."""
        nucleo = getattr(self, "_nucleo", None)
        if nucleo is None:
            nucleo = montar_nucleo()
            self._nucleo = nucleo
        return nucleo

    def _wire_documentos(self: "WiringMixin") -> None:
        """Monta os adaptadores de documentos antes da construção das abas."""
        self._documentos_adapters = self._obter_nucleo().documentos

    def _wire_noticias(self: "WiringMixin") -> None:
        """Monta os adaptadores de notícias antes da construção das abas."""
        self._noticias_adapters = self._obter_nucleo().noticias

    def _on_background_iniciado(self: "WiringMixin", handle: "JobHandle") -> None:
        """Reflete o início de um job no estado ocupado do apresentador."""
        self._presenter.enter()
        if handle.cancelavel:
            self._presenter.job_cancelavel_iniciado()

    def _on_background_terminado(self: "WiringMixin", handle: "JobHandle") -> None:
        """Reflete o término de um job, incluindo o desfecho, no apresentador."""
        if handle.cancelavel:
            self._presenter.job_cancelavel_finalizado()
        self._presenter.exit(handle.outcome, handle.falha_reportada)

    def _wire_controller(self: "WiringMixin") -> None:
        """Monta o grafo de dependências e conecta a lista de tickers."""
        nucleo = self._obter_nucleo()
        presenter = FlowScopePresenter(view=self)
        self._presenter = presenter
        background = BackgroundManager(agendar=self.agendar)
        background.ao_iniciar(self._on_background_iniciado)
        background.ao_terminar(self._on_background_terminado)
        presenter.attach_background(background)
        self._background = background

        self._documentos_adapters = nucleo.documentos
        self._noticias_adapters = nucleo.noticias
        self._renda_fixa_adapters = nucleo.renda_fixa
        self._aquisicao_documentos = nucleo.aquisicao_documentos
        self._aquisicao_titulos = (
            nucleo.renda_fixa.aquisicao
            if feature_flag("renda_fixa.atualizar_titulos", True)
            else None
        )
        self._aquisicao_noticias = nucleo.aquisicao_noticias
        self._deduplicar_documentos = nucleo.deduplicar_documentos
        self._deduplicar_noticias = nucleo.deduplicar_noticias
        self._fundamental_history_store = nucleo.history_store
        self._guidance_store = nucleo.guidance_store

        self._controller = FlowScopeController(
            guard=nucleo.guard,
            load_portfolio=nucleo.load_portfolio,
            analyze=nucleo.analyze,
            presenter=presenter,
            logger=nucleo.logger,
            fundamental_repo=nucleo.fundamental_repo,
            fundamental_provider=nucleo.fundamental_provider,
            fundamental_ffo_provider=nucleo.fundamental_ffo_provider,
            fundamental_dividend_provider=nucleo.fundamental_dividend_provider,
            fundamental_acionistas_provider=nucleo.fundamental_acionistas_provider,
            fundamental_indexadores_provider=nucleo.fundamental_indexadores_provider,
            fundamental_history_store=nucleo.history_store,
            fundamental_resolver_fiagro=nucleo.resolver_fiagro,
            fundamental_bdr_provider=nucleo.fundamental_bdr_provider,
            fundamental_guidance_store=nucleo.guidance_store,
            fundamental_short_interest_provider=(
                nucleo.fundamental_short_interest_provider
            ),
            fundamental_mercado_factory=nucleo.mercado_factory,
            background=background,
            calendar=nucleo.calendar.service,
        )
        self._ticker_list.rebind(
            on_change=self._on_ticker_edit,
            on_load=self._controller.on_load_data,
            on_data_needed=self._controller.on_load_data,
            on_file_changed=self._on_watchlist_file_changed,
            on_content_changed=self._on_watchlist_content_changed,
            on_index_click={
                "IBOV": lambda: self._on_index_click("IBOV"),
                "IDIV": lambda: self._on_index_click("IDIV"),
                "IFIX": lambda: self._on_index_click("IFIX"),
            },
        )
        self._fundamental_refresh_btn = self._ticker_list.add_action_button(
            self._on_atualizar_fundamentos,
            icon="edit-redo.png",
            tooltip="Atualizar fundamentos",
        )
        self._ticker_list.set_action_button_visible(
            self._fundamental_refresh_btn, False
        )
