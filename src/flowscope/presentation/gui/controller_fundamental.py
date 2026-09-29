"""Mixin de análise fundamentalista em background do controlador."""

from datetime import date

from flowscope.application.fundamental_analysis import FundamentalAnalysisUseCase
from flowscope.presentation.gui.background.events import Erro, Progresso, Resultado
from flowscope.presentation.gui.fundamental_job import (
    GRUPO,
    POLITICA,
    executar_fundamental,
)


class FundamentalMixin:
    """Mixin que dispara a análise fundamentalista em background."""

    def _iniciar_analise_fundamental(
        self: "FundamentalMixin",
        tickers: list[str],
        ref_date: date,
        result: dict,
        force: bool = False,
    ) -> None:
        """Dispara a análise fundamentalista em background, se configurada."""
        if self._fundamental_repo is None:
            return
        daily = {
            ticker: dados.get("daily_data", [])
            for ticker, dados in result.items()
            if isinstance(dados, dict)
        }
        mercado = None
        if self._fundamental_mercado_factory is not None:
            mercado = self._fundamental_mercado_factory(daily)
        caso = FundamentalAnalysisUseCase(
            repository=self._fundamental_repo,
            mercado=mercado,
            fundamental_provider=self._fundamental_provider,
            ffo_provider=self._fundamental_ffo_provider,
            historico_dividendos=self._fundamental_dividend_provider,
            acionistas_provider=self._fundamental_acionistas_provider,
            free_float_provider=self._fundamental_acionistas_provider,
            short_interest_provider=self._fundamental_short_interest_provider,
            indexadores_provider=self._fundamental_indexadores_provider,
            historico_store=self._fundamental_history_store,
            resolver_fiagro=self._fundamental_resolver_fiagro,
            bdr_provider=self._fundamental_bdr_provider,
            guidance_store=self._fundamental_guidance_store,
        )
        self._presenter.on_progress(0, len(tickers), "• Fundamentos...")
        if self._background is None:
            return
        self._background.submit(
            lambda ctx: executar_fundamental(
                ctx, caso, tickers, ref_date, force
            ),
            grupo=GRUPO,
            politica=POLITICA,
            cancelavel=True,
            ao_progresso=self._ao_progresso_fundamental,
            ao_resultado=self._ao_resultado_fundamental,
            ao_erro=self._ao_erro_fundamental,
        )

    def on_atualizar_fundamentos(self: "FundamentalMixin") -> None:
        """Força a recomputação dos fundamentos da data, ignorando o cache."""
        if self._fundamental_repo is None:
            return
        if self._background is not None and self._background.tem_ativo(GRUPO):
            return
        tickers = self._presenter.get_current_tickers()
        if not tickers:
            return
        ref_date = self._presenter.get_reference_date()
        current = getattr(self._presenter._gui, "_current_data", {}) or {}
        self._iniciar_analise_fundamental(tickers, ref_date, current, force=True)

    def _ao_progresso_fundamental(self: "FundamentalMixin", evento: Progresso) -> None:
        """Repassa o progresso do job ao presenter."""
        self._presenter.on_fundamental_progress(
            evento.detalhe, evento.atual, evento.total
        )

    def _ao_resultado_fundamental(self: "FundamentalMixin", evento: Resultado) -> None:
        """Aplica o resultado do job no presenter."""
        self._presenter.on_fundamental_result(evento.valor, evento.falhou)

    def _ao_erro_fundamental(self: "FundamentalMixin", evento: Erro) -> None:
        """Reporta a falha catastrófica do job ao presenter."""
        self._presenter.on_fundamental_error()
