import tkinter as tk


class ToolTip:
    def __init__(self, widget: tk.Widget, text: str, delay_ms: int = 400):
        self._widget = widget
        self._text = text
        self._delay_ms = delay_ms
        self._after_id = None
        self._tip_window = None
        widget.bind("<Enter>", self._enter, add=True)
        widget.bind("<Leave>", self._leave, add=True)
        widget.bind("<ButtonPress>", self._leave, add=True)

    def _enter(self, event=None):
        self._after_id = self._widget.after(self._delay_ms, self._show)

    def _leave(self, event=None):
        if self._after_id:
            self._widget.after_cancel(self._after_id)
            self._after_id = None
        self._hide()

    def _show(self):
        x = self._widget.winfo_rootx() + 15
        y = self._widget.winfo_rooty() + 25
        self._tip_window = tk.Toplevel(self._widget)
        self._tip_window.wm_overrideredirect(True)
        self._tip_window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self._tip_window,
            text=self._text,
            background="#ffffcc",
            relief=tk.SOLID,
            borderwidth=1,
            padx=6,
            pady=2,
            font=("TkDefaultFont", 9),
        )
        label.pack()

    def _hide(self):
        if self._tip_window:
            self._tip_window.destroy()
            self._tip_window = None
