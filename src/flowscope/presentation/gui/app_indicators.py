"""Formatação de indicadores para exibição em texto na interface."""

import tkinter as tk


def _format_value(value: object, label: str) -> str:
    """Formata um único valor de indicador como linha de texto."""
    if value is None:
        return f"{label}: --"
    if isinstance(value, dict):
        if value:
            last_date = max(value.keys())
            display = value[last_date]
            return f"{label}: {display if display is not None else '--'}"
        return f"{label}: (sem dados)"
    return f"{label}: {value}"


def build_indicator_lines(data: dict, keys: tuple[str, ...]) -> list[str]:
    """Gera a lista de linhas formatadas para os indicadores selecionados."""
    all_inds = data.get("all_indicators", {})
    lines = []
    for key in keys:
        val = all_inds.get(key, {}).get(data.get("_ticker")) if isinstance(all_inds.get(key), dict) else all_inds.get(key)
        label = key.replace("_", " ").title()
        lines.append(_format_value(val, label))
    return lines


def build_full_indicator_lines(data: dict, keys: tuple[str, ...]) -> list[str]:
    """Gera as linhas formatadas para os indicadores fixos da análise completa."""
    all_inds = data.get("all_indicators", {})
    lines = []
    for key in keys:
        val = all_inds.get(key)
        label = key.replace("_", " ").title()
        lines.append(_format_value(val, label))
    return lines


def build_extra_indicator_lines(data: dict) -> list[str]:
    """Gera as linhas extras de VWAP e volume acumulado, quando disponíveis."""
    lines = []
    vwap = data.get("vwap") or {}
    vwap_val = vwap.get("period_vwap")
    if vwap_val is not None:
        lines.append(f"\nVwap Periodo: {vwap_val}")
    mfv = data.get("money_flow_volume")
    if mfv is not None:
        lines.append(f"\nMoney Flow Volume (acum.): {mfv}")
    return lines


def insert_indicators(text_w: tk.Text, lines: list[str]) -> None:
    """Insere as linhas de indicadores no widget de texto informado."""
    if lines:
        text_w.insert(tk.END, "\n".join(lines) + "\n")
