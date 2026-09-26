import os
import tkinter as tk
from datetime import date
from decimal import Decimal
from tkinter import ttk
from unittest.mock import MagicMock

import pytest

from flowscope.domain.fii import (
    AnaliseFundamental,
    FiiSnapshot,
    MargensFii,
    ResultadoMargem,
    TendenciaDividendo,
    TendenciaFfo,
    UltimoDividendo,
    analisar_snapshot,
    classificar_ticker,
)
from flowscope.presentation.gui.app_status import StatusMixin
from flowscope.presentation.gui.app_tab_layout import TabsLayoutMixin
from flowscope.presentation.gui.app_tabs import TAB_CONTENT
from flowscope.presentation.gui.charts.fundamental_table import (
    FundamentalTablePanel,
)

NA = "N/A"


def _margens_hgbs11() -> MargensFii:
    return MargensFii(
        ffo_receita_12m=ResultadoMargem(Decimal("0.873")),
        ffo_receita_3m=ResultadoMargem(Decimal("0.855")),
        dividendos_receita_12m=ResultadoMargem(Decimal("1.157")),
        dividendos_receita_3m=ResultadoMargem(Decimal("0.768")),
        dividendos_ffo_12m=ResultadoMargem(Decimal("1.326")),
        dividendos_ffo_3m=ResultadoMargem(Decimal("0.899")),
        ffo_trend=TendenciaFfo.ESTAVEL,
    )


def _analise_hgbs11() -> AnaliseFundamental:
    metricas = analisar_snapshot(
        FiiSnapshot(
            ticker="HGBS11",
            reference_date=date(2026, 9, 4),
            price=Decimal("18.74"),
            shares_outstanding=Decimal(144355726),
            net_asset_value=Decimal(2942000000),
            ffo_12m=Decimal(220777000),
            ffo_3m=Decimal(63802000),
            dividends_12m=Decimal(213080000),
        )
    )
    return AnaliseFundamental(
        ticker="HGBS11",
        nome="CSHG Renda Urbana",
        classificacao=classificar_ticker("HGBS11"),
        ultimo_dividendo=UltimoDividendo(
            data_com=date(2026, 7, 10),
            valor=Decimal("0.55"),
            valor_anterior=Decimal("0.50"),
            tendencia=TendenciaDividendo.FORTE_ALTA,
        ),
        dividendos_12m_por_cota=Decimal("1.05"),
        metricas=metricas,
        margens=_margens_hgbs11(),
        cotas=Decimal(144355726),
    )


def _analise_acao() -> AnaliseFundamental:
    return AnaliseFundamental(
        ticker="PETR4",
        nome="Petrobras PN",
        classificacao=classificar_ticker("PETR4"),
        ultimo_dividendo=UltimoDividendo(
            data_com=None,
            valor=None,
            valor_anterior=None,
            tendencia=TendenciaDividendo.N_A,
        ),
        dividendos_12m_por_cota=None,
        metricas=None,
    )


needs_display = pytest.mark.skipif(
    not os.environ.get("DISPLAY"),
    reason="Test requires a display (no DISPLAY env var)",
)


class TestFundamentalTablePanel:
    @needs_display
    def test_painel_expoe_dois_treeviews(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            assert tuple(painel._tree_fixo.cget("columns")) == ("ticker", "nome")
            assert len(painel._tree_rolavel.cget("columns")) == 32
        finally:
            root.destroy()

    @needs_display
    def test_update_popula_os_dois_treeviews(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            painel.update({"HGBS11": _analise_hgbs11(), "PETR4": _analise_acao()})
            fixos = painel._tree_fixo.get_children()
            rolantes = painel._tree_rolavel.get_children()
            assert fixos == rolantes == ("HGBS11", "PETR4")
            valores = painel._tree_fixo.item(fixos[0], "values")
            assert valores[0] == "HGBS11"
            assert valores[1] == "CSHG Renda Urbana"
            rolavel = painel._tree_rolavel.item(fixos[0], "values")
            assert rolavel[17] == "87,3%"
        finally:
            root.destroy()

    @needs_display
    def test_linha_dividida_reconstroi_30_campos(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            painel.update({"HGBS11": _analise_hgbs11()})
            iid = painel._tree_fixo.get_children()[0]
            congelados = tuple(painel._tree_fixo.item(iid, "values"))
            rolantes = tuple(painel._tree_rolavel.item(iid, "values"))
            assert len(congelados) == 2
            assert len(rolantes) == 32
            assert len(congelados + rolantes) == 34
        finally:
            root.destroy()

    @needs_display
    def test_update_vazio_limpa_os_dois_treeviews(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            painel.update({"HGBS11": _analise_hgbs11()})
            painel.reset()
            assert len(painel._tree_fixo.get_children()) == 0
            assert len(painel._tree_rolavel.get_children()) == 0
        finally:
            root.destroy()

    @needs_display
    def test_layout_em_grid_com_barra_compartilhada(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            assert painel._frame_fixo.grid_info()["column"] == 0
            assert painel._divisor.grid_info()["column"] == 1
            assert painel._frame_rolavel.grid_info()["column"] == 2
            assert painel._scrollbar_v.grid_info()["column"] == 3
            assert painel._scrollbar_v.grid_info()["in"] == painel.frame
            assert painel._scrollbar_h.grid_info()["in"] == painel._frame_rolavel
            assert painel.frame.grid_columnconfigure(0)["weight"] == 0
            assert painel.frame.grid_columnconfigure(1)["weight"] == 0
            assert painel.frame.grid_columnconfigure(2)["weight"] == 1
            assert painel._espacador.grid_info()["in"] == painel._frame_fixo
            assert painel._espacador.grid_info()["row"] == 1
        finally:
            root.destroy()

    @needs_display
    def test_divisor_fixo_entre_os_paineis(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            assert isinstance(painel._divisor, ttk.Separator)
            assert str(painel._divisor.cget("orient")) == "vertical"
            assert painel._divisor.grid_info()["column"] == 1
            assert painel._divisor.grid_info()["in"] == painel.frame
        finally:
            root.destroy()

    @needs_display
    def test_get_column_widths_agrega_os_dois_treeviews(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            larguras = painel.get_column_widths()
            assert set(larguras) == set(painel._columns)
            assert len(larguras) == 34
        finally:
            root.destroy()

    @needs_display
    def test_painel_aplica_larguras_iniciais(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root, widths={"ticker": 200})
            assert painel.get_column_widths()["ticker"] == 200
        finally:
            root.destroy()

    @needs_display
    def test_larguras_persistidas_vai_para_treeview_correto(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(
                root, widths={"ticker": 200, "nome": 180, "p": 90}
            )
            assert int(painel._tree_fixo.column("ticker", "width")) == 200
            assert int(painel._tree_fixo.column("nome", "width")) == 180
            assert int(painel._tree_rolavel.column("p", "width")) == 90
        finally:
            root.destroy()

    @needs_display
    def test_painel_usa_largura_padrao_sem_preferencia(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            assert painel.get_column_widths()["ticker"] == 140
        finally:
            root.destroy()

    @needs_display
    def test_painel_notifica_mudanca_de_largura(self):
        root = tk.Tk()
        try:
            registradas = []
            painel = FundamentalTablePanel(
                root, on_widths_changed=registradas.append
            )
            painel._tree_fixo.column("ticker", width=222)
            painel._on_column_resized()
            assert registradas and registradas[-1]["ticker"] == 222
            assert registradas[-1]["p"] == 140
        finally:
            root.destroy()

    @needs_display
    def test_fronteira_ajusta_ao_redimensionar_coluna_congelada(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            painel.frame.pack(fill="both", expand=True)
            root.geometry("900x300")
            root.update()
            painel._tree_fixo.column("ticker", width=200)
            painel._tree_fixo.column("nome", width=210)
            painel._on_column_resized()
            root.update()
            assert painel._frame_fixo.winfo_width() == 410
        finally:
            root.destroy()

    @needs_display
    def test_painel_rolavel_mantem_largura_minima(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            painel.frame.pack(fill="both", expand=True)
            root.geometry("400x300")
            root.update()
            painel._tree_fixo.column("ticker", width=600)
            painel._tree_fixo.column("nome", width=600)
            painel._on_column_resized()
            root.update()
            disponivel = painel.frame.winfo_width()
            assert painel._frame_fixo.winfo_width() <= disponivel - 200
        finally:
            root.destroy()

    @needs_display
    def test_rolagem_vertical_sincroniza_os_paineis(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            painel.frame.pack(fill="both", expand=True)
            root.geometry("900x200")
            root.update()
            painel.update(
                {f"AAA{i:02d}": {"daily_data": []} for i in range(60)}
            )
            root.update()
            painel._tree_rolavel.yview_moveto(0.5)
            root.update()
            assert painel._tree_fixo.yview()[0] == pytest.approx(
                painel._tree_rolavel.yview()[0]
            )
        finally:
            root.destroy()

    @needs_display
    def test_barra_vertical_move_os_dois_paineis(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            painel.frame.pack(fill="both", expand=True)
            root.geometry("900x200")
            root.update()
            painel.update(
                {f"AAA{i:02d}": {"daily_data": []} for i in range(60)}
            )
            root.update()
            painel._on_vscroll("moveto", "0.4")
            root.update()
            assert painel._tree_fixo.yview()[0] == pytest.approx(0.4, abs=0.01)
            assert painel._tree_fixo.yview()[0] == pytest.approx(
                painel._tree_rolavel.yview()[0]
            )
        finally:
            root.destroy()

    @needs_display
    def test_roda_do_mouse_encaminha_rolagem(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            painel.frame.pack(fill="both", expand=True)
            root.geometry("900x200")
            root.update()
            painel.update(
                {f"AAA{i:02d}": {"daily_data": []} for i in range(60)}
            )
            root.update()

            class _Evento:
                num = 5
                delta = 0

            inicio = painel._tree_rolavel.yview()[0]
            assert painel._on_mousewheel(_Evento()) == "break"
            root.update()
            assert painel._tree_rolavel.yview()[0] > inicio
            assert painel._tree_fixo.yview()[0] == pytest.approx(
                painel._tree_rolavel.yview()[0]
            )
        finally:
            root.destroy()

    @needs_display
    def test_selecao_espelhada_entre_os_paineis(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            painel.update(
                {f"AAA{i:02d}": {"daily_data": []} for i in range(5)}
            )
            painel._tree_fixo.selection_set("AAA02")
            root.update()
            assert painel._tree_rolavel.selection() == ("AAA02",)
            painel._tree_rolavel.selection_set("AAA04")
            root.update()
            assert painel._tree_fixo.selection() == ("AAA04",)
        finally:
            root.destroy()

    @needs_display
    def test_selecao_e_unica(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            assert str(painel._tree_fixo.cget("selectmode")) == "browse"
            assert str(painel._tree_rolavel.cget("selectmode")) == "browse"
        finally:
            root.destroy()

    @needs_display
    def test_selecao_notifica_ticker_uma_vez(self):
        root = tk.Tk()
        try:
            registros: list[str] = []
            painel = FundamentalTablePanel(root, on_ticker_selected=registros.append)
            painel.update({f"AAA{i:02d}": {"daily_data": []} for i in range(5)})

            painel._tree_fixo.selection_set("AAA02")
            root.update()
            assert registros == ["AAA02"]

            painel._tree_rolavel.selection_set("AAA04")
            root.update()
            assert registros == ["AAA02", "AAA04"]
        finally:
            root.destroy()

    @needs_display
    def test_select_ticker_e_helpers(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            painel.update({f"AAA{i:02d}": {"daily_data": []} for i in range(3)})

            assert painel.first_ticker() == "AAA00"
            assert painel.has_ticker("AAA01") is True
            assert painel.has_ticker("XXXX99") is False
            assert painel.get_selected_ticker() is None

            painel.select_ticker("AAA01")
            root.update()
            assert painel.get_selected_ticker() == "AAA01"
            assert painel._tree_rolavel.selection() == ("AAA01",)

            painel.select_ticker("XXXX99")
            root.update()
            assert painel.get_selected_ticker() == "AAA01"
        finally:
            root.destroy()

    @needs_display
    def test_painel_alinhamento_das_colunas(self):
        root = tk.Tk()
        try:
            painel = FundamentalTablePanel(root)
            direita = {
                "ultimo_dividendo",
                "dividendo_anterior",
                "dividend_yield",
                "shorts_pct",
                "sir",
                "ffo_receita_12m",
                "ffo_receita_3m",
                "dividendos_receita_12m",
                "dividendos_receita_3m",
                "dividendos_ffo_12m",
                "dividendos_ffo_3m",
                "p",
                "preco_tipico",
                "p_pt",
                "vp",
                "p_vp",
                "p_l",
                "cotas",
                "cotistas",
                "patrimonio",
            }
            for coluna_id in painel._columns:
                tree = (
                    painel._tree_fixo
                    if coluna_id in painel._columns_fixas
                    else painel._tree_rolavel
                )
                esperado = "e" if coluna_id in direita else "w"
                assert str(tree.column(coluna_id, "anchor")) == esperado
        finally:
            root.destroy()


class TestWiringSubAba:
    def test_tab_content_fundamentos_existe(self):
        assert ("Análise Geral", "Fundamentos") in TAB_CONTENT
        titulo, corpo = TAB_CONTENT[("Análise Geral", "Fundamentos")]
        assert "Fundamentos" in titulo
        assert isinstance(corpo, list) and len(corpo) > 0

    def test_orientation_panel_explica_p_l_e_acionistas(self):
        _titulo, corpo = TAB_CONTENT[("Análise Geral", "Fundamentos")]
        texto = " ".join(parte for parte, _estilo in corpo)
        assert "último dividendo" in texto
        assert "acionistas" in texto

    def test_orientation_panel_descreve_colunas_recentes(self):
        _titulo, corpo = TAB_CONTENT[("Análise Geral", "Fundamentos")]
        texto = " ".join(parte for parte, _estilo in corpo)
        assert "Preço Típico" in texto
        assert "P / PT" in texto
        assert "Dividendos/FFO" in texto
        assert "Informações adicionais" in texto
        assert "Dados fiscais" in texto

    def test_orientation_panel_descreve_colunas_short_interest(self):
        _titulo, corpo = TAB_CONTENT[("Análise Geral", "Fundamentos")]
        texto = " ".join(parte for parte, _estilo in corpo)
        assert "Shorts%" in texto
        assert "Volume de Shorts" in texto
        assert "Fechamento Shorts" in texto
        assert "Risco Fechamento" in texto
        assert "acima de 5" in texto

    def test_orientation_panel_orienta_quantidade_de_cotas(self):
        _titulo, corpo = TAB_CONTENT[("Análise Geral", "Fundamentos")]
        texto = " ".join(parte for parte, _estilo in corpo)
        assert "cotas emitidas" in texto
        assert "Nro. Ações" in texto

    def test_orientation_panel_descreve_tipo_e_subtipo_implementados(self):
        _titulo, corpo = TAB_CONTENT[("Análise Geral", "Fundamentos")]
        texto = " ".join(parte for parte, _estilo in corpo)
        assert "tipo (`Papel` para ações, ETFs e BDRs; `FII`)" in texto
        assert "Tijolo:" in texto
        assert "Papel:" in texto
        assert "segmento e gestão" in texto

    def test_orientation_panel_orienta_interpretacao_das_colunas(self):
        _titulo, corpo = TAB_CONTENT[("Análise Geral", "Fundamentos")]
        texto = " ".join(parte for parte, _estilo in corpo)
        assert "desconto" in texto
        assert "prêmio" in texto
        assert "FFO/Receita" in texto
        assert "administrador" in texto
        assert "gestor" in texto

    def test_visibilidade_do_botao_por_sub_aba(self):
        from flowscope.presentation.gui.app_tab_actions import TabActionsMixin

        host = TabActionsMixin()
        host._ticker_list = MagicMock()
        host._fundamental_refresh_btn = MagicMock()

        host._sync_fundamental_refresh_visibility("Análise Geral", "Fundamentos")
        host._ticker_list.set_action_button_visible.assert_called_once_with(
            host._fundamental_refresh_btn, True
        )

        host._ticker_list.set_action_button_visible.reset_mock()
        host._sync_fundamental_refresh_visibility("Análise Geral", "VWAP")
        host._ticker_list.set_action_button_visible.assert_called_once_with(
            host._fundamental_refresh_btn, False
        )

    @needs_display
    def test_sub_aba_fundamentos_aparece_na_analise_geral(self):
        root = tk.Tk()
        try:
            host = TabsLayoutMixin()
            host._general_notebook = ttk.Notebook(root)
            host._copy_chart = lambda _figure: None
            host._on_quadrant_summary = lambda *_args: None
            host._build_general_tabs()
            abas = [
                host._general_notebook.tab(indice, "text")
                for indice in range(host._general_notebook.index("end"))
            ]
            assert "Fundamentos" in abas
            assert abas[0] == "Fundamentos"
            assert hasattr(host, "_fundamental_table")
        finally:
            root.destroy()


class _BusyCursorHost(tk.Tk, StatusMixin):
    """Host mínimo que expõe o mecanismo de cursor do estado ocupado."""

    def disable_all_buttons(self) -> None:
        pass

    def restore_all_buttons(self) -> None:
        pass

    def clear_progress(self) -> None:
        pass

    def set_cancellable(self, cancellable: bool) -> None:
        pass

    def config_copy_button_state(self, state: str) -> None:
        pass


class TestFundamentalTableCursorSync:
    @needs_display
    def test_dois_grids_sincronizados_durante_e_apos_operacao(self):
        from flowscope.presentation.gui.presenter import FlowScopePresenter

        root = _BusyCursorHost()
        try:
            painel = FundamentalTablePanel(root)
            painel.frame.pack(fill=tk.BOTH, expand=True)
            fixo = painel._tree_fixo
            rolavel = painel._tree_rolavel
            fixo.config(cursor="hand2")
            rolavel.config(cursor="xterm")
            root.update()

            presenter = FlowScopePresenter(root)
            presenter.on_operation_started()
            assert str(fixo.cget("cursor")) == "watch"
            assert str(rolavel.cget("cursor")) == "watch"

            sep_x = next(
                x for x in range(fixo.winfo_width())
                if fixo.identify_region(x, 5) == "separator"
            )
            fixo.event_generate("<Motion>", x=sep_x, y=5)
            root.update()
            assert str(fixo.cget("cursor")) == "watch"
            assert str(rolavel.cget("cursor")) == "watch"

            presenter.on_operation_finished()
            assert str(fixo.cget("cursor")) == "hand2"
            assert str(rolavel.cget("cursor")) == "xterm"
        finally:
            root.destroy()

    @needs_display
    def test_cursor_nao_vaza_com_ponteiro_sobre_separador_ao_iniciar(self):
        from flowscope.presentation.gui.presenter import FlowScopePresenter

        root = _BusyCursorHost()
        try:
            painel = FundamentalTablePanel(root)
            painel.frame.pack(fill=tk.BOTH, expand=True)
            fixo = painel._tree_fixo
            rolavel = painel._tree_rolavel
            fixo.config(cursor="hand2")
            root.update()

            sep_x = next(
                x for x in range(rolavel.winfo_width())
                if rolavel.identify_region(x, 5) == "separator"
            )
            rolavel.event_generate("<Motion>", x=sep_x, y=5, warp=True)
            root.update()

            presenter = FlowScopePresenter(root)
            presenter.on_operation_started()
            rolavel.event_generate("<Motion>", x=5, y=40, warp=True)
            root.update()
            presenter.on_operation_finished()

            assert str(rolavel.cget("cursor")) != "watch"
            assert str(fixo.cget("cursor")) == "hand2"
        finally:
            root.destroy()
