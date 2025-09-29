# markdown_to_html/gui.py
from __future__ import annotations

import os
import platform
import subprocess
import webbrowser
import traceback
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from .main import infer_output_path, build_from_file


# ---------- Light palette ----------
PALETTE = {
    "BG": "#F7F7FB",
    "FG": "#111827",
    "MUTED": "#6B7280",
    "CARD": "white",
    "BORDER": "#E5E7EB",
    "SEPARATOR": "#E5E7EB",
    "ACCENT": "#4F46E5",
    "ACCENT_ACTIVE": "#4338CA",
    "ACCENT_DISABLED": "#A5B4FC",
    "SUCCESS": "#065F46",
    "ERROR": "#991B1B",
}


class Tooltip:
    """Tooltip mínima para ttk (sem libs externas)."""
    def __init__(self, widget: tk.Widget, text: str, delay_ms: int = 450) -> None:
        self.widget = widget
        self.text = text
        self.delay = delay_ms
        self._id: str | None = None
        self._tip: tk.Toplevel | None = None
        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._hide)

    def _schedule(self, _=None):
        self._unschedule()
        self._id = self.widget.after(self.delay, self._show)

    def _unschedule(self):
        if self._id:
            self.widget.after_cancel(self._id)
            self._id = None

    def _show(self):
        if self._tip:
            return
        x = self.widget.winfo_rootx() + 16
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        self._tip = tk.Toplevel(self.widget)
        self._tip.overrideredirect(True)
        self._tip.attributes("-topmost", True)
        frm = ttk.Frame(self._tip, padding=8, style="Tip.TFrame")
        frm.pack()
        ttk.Label(frm, text=self.text, style="Tip.TLabel").pack()
        self._tip.geometry(f"+{x}+{y}")

    def _hide(self, _=None):
        self._unschedule()
        if self._tip:
            self._tip.destroy()
            self._tip = None


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Markdown → HTML")
        self.geometry("780x400")
        self.minsize(720, 360)
        self._init_dpi_awareness()
        self._apply_theme()

        # state
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.mode = tk.StringVar(value="full")
        self.force = tk.BooleanVar(value=False)
        self.encoding = tk.StringVar(value="utf-8")
        self.open_after = tk.BooleanVar(value=True)

        # sugere output ao digitar input
        self.input_path.trace_add("write", self._auto_suggest_output)

        self._build_ui()
        self._bind_shortcuts()

    # ---------- platform niceties ----------
    def _init_dpi_awareness(self) -> None:
        if platform.system() == "Windows":
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(1)  # SYSTEM_AWARE
            except Exception:
                pass

    # ---------- theme ----------
    def _apply_theme(self) -> None:
        p = PALETTE
        self.configure(bg=p["BG"])
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        base_font = ("Segoe UI", 10)
        title_font = ("Segoe UI Semibold", 20)

        style.configure(".", background=p["BG"], foreground=p["FG"], font=base_font)
        style.configure("Title.TLabel", font=title_font, background=p["BG"], foreground=p["FG"])
        style.configure("Sub.TLabel", font=("Segoe UI", 10), foreground=p["MUTED"], background=p["BG"])
        style.configure("Card.TFrame", background=p["CARD"], borderwidth=1, relief="solid")
        style.configure("TEntry", padding=8)
        style.configure("TCombobox", padding=6)
        style.configure("TCheckbutton", background=p["CARD"])
        style.configure("TRadiobutton", background=p["CARD"])
        style.configure("TSeparator", background=p["SEPARATOR"])

        # Accent button
        style.configure("Accent.TButton", padding=(14, 10), background=p["ACCENT"], foreground="white", borderwidth=0)
        style.map("Accent.TButton",
                  background=[("active", p["ACCENT_ACTIVE"]), ("disabled", p["ACCENT_DISABLED"])],
                  foreground=[("disabled", "white")])

        # Link button (flat)
        style.configure("Link.TButton", relief="flat", padding=0, background=p["BG"], foreground=p["ACCENT"])
        style.map("Link.TButton", foreground=[("active", p["ACCENT_ACTIVE"])])

        # Segmented (radio-style) buttons
        style.configure("Segment.TButton", padding=(12, 8), background=p["CARD"], borderwidth=1, relief="solid")
        style.map("Segment.TButton",
                  background=[("active", p["BORDER"])])
        style.configure("Segment.Active.TButton", padding=(12, 8), background=p["ACCENT"], foreground="white", borderwidth=1, relief="solid")
        style.map("Segment.Active.TButton",
                  background=[("active", p["ACCENT_ACTIVE"])])

        # Status + tooltip
        style.configure("Status.TLabel", foreground=p["MUTED"], background=p["BG"])
        style.configure("StatusOK.TLabel", foreground=p["SUCCESS"], background=p["BG"])
        style.configure("StatusERR.TLabel", foreground=p["ERROR"], background=p["BG"])
        style.configure("Tip.TFrame", background="black")
        style.configure("Tip.TLabel", background="black", foreground="white", font=("Segoe UI", 9))

    # ---------- UI ----------
    def _build_ui(self) -> None:
        p = PALETTE
        root = ttk.Frame(self, padding=18)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)

        # header
        header = ttk.Frame(root)
        header.grid(row=0, column=0, sticky="we")
        header.columnconfigure(0, weight=1)

        title_row = ttk.Frame(header)
        title_row.grid(row=0, column=0, sticky="we")
        title_row.columnconfigure(1, weight=1)

        ttk.Label(title_row, text="📄→🌐", font=("Segoe UI Emoji", 22)).grid(row=0, column=0, sticky="w", padx=(0, 10))
        ttk.Label(title_row, text="Markdown → HTML", style="Title.TLabel").grid(row=0, column=1, sticky="w")

        ttk.Label(header,
                  text="Selecione um .md, escolha o destino e converta. Você pode gerar página completa ou apenas o body.",
                  style="Sub.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 12))
        ttk.Separator(root).grid(row=1, column=0, sticky="we", pady=(0, 12))

        # card
        card = ttk.Frame(root, style="Card.TFrame", padding=16)
        card.grid(row=2, column=0, sticky="nwe")
        card.columnconfigure(0, weight=1)
        pad = {"padx": 6, "pady": 8}

        # Input
        ttk.Label(card, text="Arquivo Markdown (.md / .markdown):").grid(row=0, column=0, sticky="w", **pad)
        row_in = ttk.Frame(card); row_in.grid(row=1, column=0, sticky="we", **pad); row_in.columnconfigure(0, weight=1)
        ent_in = ttk.Entry(row_in, textvariable=self.input_path)
        ent_in.grid(row=0, column=0, sticky="we")
        btn_in = ttk.Button(row_in, text="📂 Selecionar", command=self.browse_input)
        btn_in.grid(row=0, column=1, padx=(8, 0))
        Tooltip(btn_in, "Escolher arquivo .md")

        # Output
        ttk.Label(card, text="Arquivo de saída (.html):").grid(row=2, column=0, sticky="w", **pad)
        row_out = ttk.Frame(card); row_out.grid(row=3, column=0, sticky="we", **pad); row_out.columnconfigure(0, weight=1)
        ent_out = ttk.Entry(row_out, textvariable=self.output_path)
        ent_out.grid(row=0, column=0, sticky="we")
        btn_out = ttk.Button(row_out, text="💾 Salvar como", command=self.browse_output)
        btn_out.grid(row=0, column=1, padx=(8, 0))
        Tooltip(btn_out, "Definir arquivo de saída .html")

        # Segmented control: modo
        seg = ttk.Frame(card); seg.grid(row=4, column=0, sticky="w", **pad)
        ttk.Label(seg, text="Modo:").grid(row=0, column=0, sticky="w", padx=(0, 8))

        self.btn_full = ttk.Button(seg, text="Página completa", command=lambda: self._set_mode("full"),
                                   style="Segment.Active.TButton")
        self.btn_body = ttk.Button(seg, text="Apenas body", command=lambda: self._set_mode("body"),
                                   style="Segment.TButton")
        self.btn_full.grid(row=0, column=1, sticky="w")
        self.btn_body.grid(row=0, column=2, sticky="w", padx=(2, 0))
        Tooltip(self.btn_full, "Gera <!DOCTYPE html> + <html><head><title>…</title><body>…")
        Tooltip(self.btn_body, "Gera apenas o conteúdo do <body>")

        # Extras
        extras = ttk.Frame(card); extras.grid(row=5, column=0, sticky="we", **pad)
        ttk.Checkbutton(extras, text="Sobrescrever se existir", variable=self.force).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(extras, text="Abrir no navegador após converter", variable=self.open_after)\
            .grid(row=0, column=1, sticky="w", padx=(12, 0))
        ttk.Label(extras, text="Encoding:").grid(row=0, column=2, sticky="e", padx=(18, 6))
        ttk.Combobox(extras, textvariable=self.encoding, values=["utf-8", "latin-1"], width=12, state="readonly")\
            .grid(row=0, column=3, sticky="w")

        # actions + status
        actions = ttk.Frame(root)
        actions.grid(row=3, column=0, sticky="we", pady=(14, 0))
        actions.columnconfigure(0, weight=1)

        self.status = ttk.Label(actions, text="Pronto", style="Status.TLabel")
        self.status.grid(row=0, column=0, sticky="w")

        self.progress = ttk.Progressbar(actions, mode="determinate", length=200)
        self.progress.grid(row=0, column=1, sticky="e", padx=(0, 10))

        right = ttk.Frame(actions); right.grid(row=0, column=2, sticky="e")
        self.btn_open_folder = ttk.Button(right, text="📁 Abrir pasta", command=self._open_output_folder)
        self.btn_open_folder.grid(row=0, column=0, padx=(0, 8))
        self.btn_convert = ttk.Button(right, text="🔄 Converter", style="Accent.TButton", command=self.convert)
        self.btn_convert.grid(row=0, column=1)

        ttk.Separator(root).grid(row=4, column=0, sticky="we", pady=(12, 6))

    # ---------- helpers ----------
    def _bind_shortcuts(self) -> None:
        self.bind("<Control-o>", lambda e: self.browse_input())
        self.bind("<Control-s>", lambda e: self.browse_output())
        self.bind("<Return>", lambda e: self.convert())

    def _set_mode(self, value: str) -> None:
        self.mode.set(value)
        # visual do segmented
        if value == "full":
            self.btn_full.configure(style="Segment.Active.TButton")
            self.btn_body.configure(style="Segment.TButton")
        else:
            self.btn_body.configure(style="Segment.Active.TButton")
            self.btn_full.configure(style="Segment.TButton")

    def _auto_suggest_output(self, *_):
        # sugere output quando input muda e output está vazio
        raw = self.input_path.get().strip()
        if raw and not self.output_path.get().strip():
            try:
                self.output_path.set(str(infer_output_path(Path(raw))))
            except Exception:
                pass

    # ---------- handlers ----------
    def browse_input(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecione o arquivo Markdown",
            filetypes=[("Markdown", "*.md *.markdown"), ("Todos", "*.*")],
        )
        if not path:
            return
        self.input_path.set(path)
        if not self.output_path.get().strip():
            self.output_path.set(str(infer_output_path(Path(path))))

    def browse_output(self) -> None:
        initial = self.output_path.get().strip()
        initdir = str(Path(initial).parent) if initial else None
        path = filedialog.asksaveasfilename(
            title="Salvar como",
            defaultextension=".html",
            filetypes=[("HTML", "*.html")],
            initialdir=initdir,
            initialfile=Path(initial).name if initial else None,
        )
        if path:
            self.output_path.set(path)

    def _open_output_folder(self) -> None:
        out = self.output_path.get().strip()
        if not out:
            messagebox.showinfo("Abrir pasta", "Nenhum arquivo de saída definido ainda.")
            return
        folder = str(Path(out).parent)
        try:
            if platform.system() == "Windows":
                os.startfile(folder)  # type: ignore[attr-defined]
            elif platform.system() == "Darwin":
                subprocess.run(["open", folder], check=False)
            else:
                subprocess.run(["xdg-open", folder], check=False)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{e}")

    def _set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self.btn_convert.config(state=state)
        self.btn_open_folder.config(state=state)

    def _pulse_progress(self, to: int) -> None:
        cur = int(self.progress["value"])
        step = 4 if to - cur > 4 else 1
        for v in range(cur, to + 1, step):
            self.progress["value"] = v
            self.update_idletasks()

    def _set_status(self, text: str, kind: str = "info") -> None:
        if kind == "ok":
            self.status.configure(text=text, style="StatusOK.TLabel")
        elif kind == "err":
            self.status.configure(text=text, style="StatusERR.TLabel")
        else:
            self.status.configure(text=text, style="Status.TLabel")

    def convert(self) -> None:
        try:
            inp = Path(self.input_path.get().strip())
            if not inp.exists() or not inp.is_file():
                messagebox.showerror("Erro", f"Arquivo de entrada não encontrado:\n{inp}")
                self._set_status("Arquivo de entrada não encontrado", "err")
                return

            out = self.output_path.get().strip() or str(infer_output_path(inp))
            out_path = Path(out)
            if out_path.exists() and not self.force.get():
                messagebox.showwarning(
                    "Saída já existe",
                    f"O arquivo já existe:\n{out_path}\n\nMarque 'Sobrescrever' para substituir.",
                )
                self._set_status("Saída já existe (sem overwrite)", "err")
                return

            self._set_busy(True)
            self._set_status("Convertendo…")
            self._pulse_progress(to=35)

            html = build_from_file(inp, mode=self.mode.get())

            self._pulse_progress(to=75)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(html, encoding=self.encoding.get())

            self._pulse_progress(to=100)
            self._set_status(f"OK: salvo em {out_path}", "ok")
            messagebox.showinfo("Sucesso", f"HTML gerado com sucesso:\n{out_path}")

            if self.open_after.get():
                try:
                    webbrowser.open_new_tab(out_path.as_uri())
                except Exception:
                    pass

        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Erro", f"Falha ao converter:\n{e}")
            self._set_status("Falha ao converter", "err")
        finally:
            self.after(450, lambda: self.progress.config(value=0))
            self._set_busy(False)


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
