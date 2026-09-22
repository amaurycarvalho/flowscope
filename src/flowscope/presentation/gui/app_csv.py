"""Geração e cópia de dados CSV da interface gráfica do FlowScope."""

import tkinter as tk
from datetime import date

from flowscope.presentation.gui.charts.fundamental_table import montar_csv

CSV_HEADER = "RptDt;TckrSymb;MinPric;MaxPric;TradAvrgPric;LastPric;TradQty;FinInstrmQty;NtlFinVol"


class CsvMixin:
    """Constrói o CSV dos dados carregados e copia para a área de transferência."""

    def _build_raw_csv(self: "CsvMixin") -> str:
        tickers = self._csv_tickers(self._current_main_tab())
        if not tickers:
            self._flash_status("Nenhum ticker disponível para cópia.")
            return ""
        sampling_dates = self._csv_sampling_dates(tickers)
        lines = [CSV_HEADER]
        for ticker in tickers:
            lines.extend(self._csv_ticker_lines(ticker, sampling_dates))
        return "\n".join(lines)

    def _current_main_tab(self: "CsvMixin") -> str:
        try:
            return self._main_notebook.tab(self._main_notebook.select(), "text")
        except tk.TclError:
            return "Análise Geral"

    def _csv_tickers(self: "CsvMixin", main_tab: str) -> list[str]:
        if main_tab == "Análise do Ticker":
            ticker = self._ticker_apresentado()
            return [ticker] if ticker else []
        tickers = self._ticker_list.get_tickers()
        if not tickers:
            ticker = self._get_selected_ticker()
            return [ticker] if ticker else []
        return tickers

    def _csv_sampling_dates(self: "CsvMixin", tickers: list[str]) -> list[date]:
        if self._sampling_dates:
            return list(self._sampling_dates)
        return sorted({
            day["date"]
            for t in tickers
            for day in self._current_data.get(t, {}).get("daily_data", [])
        })

    def _csv_ticker_lines(self: "CsvMixin", ticker: str, sampling_dates: list[date]) -> list[str]:
        daily = self._current_data.get(ticker, {}).get("daily_data", [])
        by_date = {day["date"]: day for day in daily}
        lines = []
        for sd in sampling_dates:
            day = by_date.get(sd)
            if day:
                lines.append(self._csv_day_line(sd, ticker, day))
            else:
                lines.append(self._csv_missing_line(sd, ticker))
        return lines

    def _csv_day_line(self: "CsvMixin", sd: date, ticker: str, day: dict) -> str:
        min_p = str(day["min_price"]).replace(".", ",")
        max_p = str(day["max_price"]).replace(".", ",")
        avg_p = str(day["avg_price"]).replace(".", ",")
        last_p = str(day["last_price"]).replace(".", ",")
        fin_v = str(day["fin_vol"]).replace(".", ",")
        return (
            f"{sd.isoformat()};{ticker};{min_p};{max_p};"
            f"{avg_p};{last_p};{day['trades_qty']};"
            f"{day['fin_instr_qty']};{fin_v}"
        )

    def _csv_missing_line(self: "CsvMixin", sd: date, ticker: str) -> str:
        return f"{sd.isoformat()};{ticker};;;;;;;"

    def _copy_data(self: "CsvMixin") -> None:
        texto = self._texto_para_copiar()
        if not texto:
            return
        with self._presenter.busy():
            try:
                import pyxclip

                pyxclip.copy(texto)
                self._flash_status("Dados copiados!")
            except (OSError, ImportError):
                self._fallback_clipboard_text(texto)

    def _texto_para_copiar(self: "CsvMixin") -> str:
        """Seleciona o conteúdo conforme a sub-aba ativa.

        Na sub-aba "Documentos", copia o texto exibido no campo de
        pré-visualização; nas demais, monta o CSV do contexto atual.
        """
        if self._current_tabs() == ("Análise do Ticker", "Documentos"):
            painel = getattr(self, "_documents_panel", None)
            return painel.texto_atual() if painel is not None else ""
        return self._build_csv_for_current_tab()

    def _build_csv_for_current_tab(self: "CsvMixin") -> str:
        """Monta o CSV do contexto atual: tabela de Fundamentos ou CSV bruto."""
        if self._current_tabs() == ("Análise Geral", "Fundamentos"):
            return self._build_fundamental_csv()
        return self._build_raw_csv()

    def _build_fundamental_csv(self: "CsvMixin") -> str:
        """Monta o CSV da tabela de Fundamentos com os tickers exibidos."""
        tickers = self._ticker_list.get_tickers()
        dados = getattr(self, "_fundamental_data", {})
        filtrados = {ticker: dados[ticker] for ticker in tickers if ticker in dados}
        if not filtrados:
            self._flash_status("Nenhum ticker disponível para cópia.")
            return ""
        return montar_csv(filtrados)

    def _fallback_clipboard_text(self: "CsvMixin", csv_text: str) -> None:
        if not csv_text:
            return
        self.clipboard_clear()
        self.clipboard_append(csv_text)
        self._flash_status("Dados copiados! (fallback)")
