# markdown_to_html/gui.py
from __future__ import annotations

import json
import os
import platform
import subprocess
import traceback
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from .main import infer_output_path, build_from_file

# ------------------------------------------------------------
# Config & helpers
# ------------------------------------------------------------
APP_NAME = "Markdown → HTML"
HIST_FILE = Path.home() / ".markdown_to_html_history.json"
MAX_RECENTS = 8

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

def open_folder(path: Path) -> None:
    try:
        if platform.system() == "Windows":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif platform.system() == "Darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{e}")

def load_recents() -> list[str]:
    try:
        data = json.loads(HIST_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [s for s in data if isinstance(s, str)]
    except Exception:
        pass
    return []

def save_recents(items: list[str]) -> None:
    try:
        HIST_FILE.write_text(json.dumps(items[:MAX_RECENTS], ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        # não falha a UI por causa do histórico
        pass


# ------------------------------------------------------------
# Tooltip simples
# ------------------------------------------------------------
class Tooltip:
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


# ------------------------------------------------------------
# App
# ------------------------------------------------------------
class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_NAME)
        self.geometry("900x560")
        self.minsize(820, 520)

        # DPI tweak (Windows)
        if platform.system() == "Windows":
            try:
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                pass

        # state
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.mode = tk.StringVar(value="full")     # full | body
        self.force = tk.BooleanVar(value=False)
        self.encoding = tk.StringVar(value="utf-8")
        self.open_after = tk.BooleanVar(value=True)
        self.recents: list[str] = load_recents()
        self.current_html: str = ""                # para preview/copy
        self._apply_theme()
        self._build_ui()
        self._bind_shortcuts()
        self._setup_drag_and_drop()  # best-effort
        # auto-suggest output
        self.input_path.trace_add("write", self._auto_suggest_output)

    # -------------------- theme --------------------
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
        style.configure("Tip.TFrame", background="black")
        style.configure("Tip.TLabel", background="black", foreground="white", font=("Segoe UI", 9))

        # buttons
        style.configure("Accent.TButton", padding=(14, 10), background=p["ACCENT"], foreground="white", borderwidth=0)
        style.map("Accent.TButton",
                  background=[("active", p["ACCENT_ACTIVE"]), ("disabled", p["ACCENT_DISABLED"])],
                  foreground=[("disabled", "white")])

        style.configure("Link.TButton", relief="flat", padding=0, background=p["BG"], foreground=p["ACCENT"])
        style.map("Link.TButton", foreground=[("active", p["ACCENT_ACTIVE"])])

        # segmented control
        style.configure("Segment.TButton", padding=(12, 8), background=p["CARD"], borderwidth=1, relief="solid")
        style.map("Segment.TButton", background=[("active", p["BORDER"])])
        style.configure("Segment.Active.TButton", padding=(12, 8), background=p["ACCENT"],
                        foreground="white", borderwidth=1, relief="solid")
        style.map("Segment.Active.TButton", background=[("active", p["ACCENT_ACTIVE"])])

        # status colors
        style.configure("Status.TLabel", foreground=p["MUTED"], background=p["BG"])
        style.configure("StatusOK.TLabel", foreground=p["SUCCESS"], background=p["BG"])
        style.configure("StatusERR.TLabel", foreground=p["ERROR"], background=p["BG"])

    # -------------------- UI --------------------
    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(3, weight=1)

        # header
        header = ttk.Frame(root)
        header.grid(row=0, column=0, sticky="we")
        header.columnconfigure(0, weight=1)

        hrow = ttk.Frame(header)
        hrow.grid(row=0, column=0, sticky="we")
        hrow.columnconfigure(1, weight=1)
        ttk.Label(hrow, text="📄→🌐", font=("Segoe UI Emoji", 22)).grid(row=0, column=0, padx=(0, 10))
        ttk.Label(hrow, text=APP_NAME, style="Title.TLabel").grid(row=0, column=1, sticky="w")

        about_btn = ttk.Button(hrow, text="❓ Sobre", style="Link.TButton", command=self._about)
        about_btn.grid(row=0, column=2, sticky="e")
        Tooltip(about_btn, "Informações sobre o app")

        ttk.Label(header, text="Converta Markdown em HTML. Gera página completa ou apenas o body.",
                  style="Sub.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 10))
        ttk.Separator(root).grid(row=1, column=0, sticky="we", pady=(0, 10))

        # notebook com duas abas: Conversão / Preview
        notebook = ttk.Notebook(root)
        notebook.grid(row=2, column=0, sticky="nsew")
        root.rowconfigure(2, weight=1)

        # ---- Tab 1: Conversão (form) ----
        tab_form = ttk.Frame(notebook)
        notebook.add(tab_form, text="Conversão")

        # card
        card = ttk.Frame(tab_form, style="Card.TFrame", padding=16)
        card.pack(fill="x", expand=False, pady=(4, 12))
        card.columnconfigure(0, weight=1)

        pad = {"padx": 6, "pady": 8}

        # Recentes + Input
        row_recent = ttk.Frame(card); row_recent.grid(row=0, column=0, sticky="we", **pad)
        row_recent.columnconfigure(1, weight=1)
        ttk.Label(row_recent, text="Recentes:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.recent_combo = ttk.Combobox(row_recent, values=self.recents, state="readonly")
        self.recent_combo.grid(row=0, column=1, sticky="we")
        ttk.Button(row_recent, text="Abrir", command=self._use_recent).grid(row=0, column=2, padx=(8, 0))
        Tooltip(self.recent_combo, "Selecione um arquivo recente")
        Tooltip(row_recent, "Histórico salvo em ~/.markdown_to_html_history.json")

        ttk.Label(card, text="Arquivo Markdown (.md / .markdown):").grid(row=1, column=0, sticky="w", **pad)
        row_in = ttk.Frame(card); row_in.grid(row=2, column=0, sticky="we", **pad); row_in.columnconfigure(0, weight=1)
        self.ent_in = ttk.Entry(row_in, textvariable=self.input_path)
        self.ent_in.grid(row=0, column=0, sticky="we")
        btn_in = ttk.Button(row_in, text="📂 Selecionar", command=self.browse_input)
        btn_in.grid(row=0, column=1, padx=(8, 0))
        Tooltip(btn_in, "Escolher arquivo .md (arraste e solte também é suportado se disponível)")

        ttk.Label(card, text="Arquivo de saída (.html):").grid(row=3, column=0, sticky="w", **pad)
        row_out = ttk.Frame(card); row_out.grid(row=4, column=0, sticky="we", **pad); row_out.columnconfigure(0, weight=1)
        self.ent_out = ttk.Entry(row_out, textvariable=self.output_path)
        self.ent_out.grid(row=0, column=0, sticky="we")
        btn_out = ttk.Button(row_out, text="💾 Salvar como", command=self.browse_output)
        btn_out.grid(row=0, column=1, padx=(8, 0))
        Tooltip(btn_out, "Definir arquivo de saída .html")

        # segmented control: modo
        seg = ttk.Frame(card); seg.grid(row=5, column=0, sticky="w", **pad)
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
        extras = ttk.Frame(card); extras.grid(row=6, column=0, sticky="we", **pad)
        ttk.Checkbutton(extras, text="Sobrescrever se existir", variable=self.force).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(extras, text="Abrir no navegador após converter", variable=self.open_after)\
            .grid(row=0, column=1, sticky="w", padx=(12, 0))
        ttk.Label(extras, text="Encoding:").grid(row=0, column=2, sticky="e", padx=(18, 6))
        ttk.Combobox(extras, textvariable=self.encoding, values=["utf-8", "latin-1"],
                     width=12, state="readonly").grid(row=0, column=3, sticky="w")

        # actions
        action = ttk.Frame(tab_form)
        action.pack(fill="x", expand=False)
        action.columnconfigure(0, weight=1)
        self.status = ttk.Label(action, text="Pronto", style="Status.TLabel")
        self.status.grid(row=0, column=0, sticky="w")
        self.progress = ttk.Progressbar(action, mode="determinate", length=220)
        self.progress.grid(row=0, column=1, sticky="e", padx=(0, 10))
        btns = ttk.Frame(action); btns.grid(row=0, column=2, sticky="e")
        self.btn_open_folder = ttk.Button(btns, text="📁 Abrir pasta", command=self._open_output_folder)
        self.btn_open_folder.grid(row=0, column=0, padx=(0, 8))
        self.btn_convert = ttk.Button(btns, text="🔄 Converter", style="Accent.TButton", command=self.convert)
        self.btn_convert.grid(row=0, column=1)

        ttk.Separator(tab_form).pack(fill="x", pady=(12, 4))

        # ---- Tab 2: Preview ----
        tab_prev = ttk.Frame(notebook)
        notebook.add(tab_prev, text="Preview (HTML)")

        prev_top = ttk.Frame(tab_prev)
        prev_top.pack(fill="x", pady=(8, 6))
        ttk.Label(prev_top, text="Prévia do HTML gerado (texto):", style="Sub.TLabel").pack(side="left")
        ttk.Button(prev_top, text="📋 Copiar HTML", command=self._copy_html, style="Link.TButton").pack(side="right")
        Tooltip(prev_top, "Mostra o HTML como texto. Use 'Abrir no navegador' para ver renderizado.")

        self.prev_text = tk.Text(tab_prev, wrap="word", height=20, padx=10, pady=10)
        self.prev_text.pack(fill="both", expand=True)
        self.prev_text.configure(state="disabled")

        ttk.Separator(root).grid(row=3, column=0, sticky="we", pady=(10, 0))

        # status final (rodapé poderia ir aqui se preferir)

    # -------------------- dnd (best-effort) --------------------
    def _setup_drag_and_drop(self) -> None:
        """
        Implementa drag&drop de arquivos de forma 'best-effort':
        - Tenta usar a API tkdnd (se presente no Tcl/Tk do sistema).
        - Se não existir, a funcionalidade apenas não é habilitada (sem erro).
        """
        try:
            # Alguns builds trazem tkdnd embutido. Se não houver, ignoramos.
            self.drop_target_register = self.__class__.drop_target_register  # type: ignore
            self.dnd_bind = self.__class__.dnd_bind  # type: ignore
        except Exception:
            # Tk sem tkdnd expõe nada — seguimos sem DnD.
            return

        try:
            self.drop_target_register("DND_Files")  # type: ignore
            self.dnd_bind("<<Drop>>", self._on_drop_files)  # type: ignore
        except Exception:
            pass

    def _on_drop_files(self, event) -> None:
        data = getattr(event, "data", "")
        # Em alguns Tk, os paths vêm entre chaves {C:/...}. Vamos limpar:
        paths = [p.strip("{}") for p in data.split() if p.strip()]
        if not paths:
            return
        p = Path(paths[0])
        if p.suffix.lower() in (".md", ".markdown"):
            self.input_path.set(str(p))
            if not self.output_path.get().strip():
                self.output_path.set(str(infer_output_path(p)))

    # -------------------- shortcuts --------------------
    def _bind_shortcuts(self) -> None:
        self.bind("<Control-o>", lambda e: self.browse_input())
        self.bind("<Control-s>", lambda e: self.browse_output())
        self.bind("<Control-Return>", lambda e: self.convert())
        self.bind("<Return>", lambda e: self.convert())

    # -------------------- micro-helpers UI --------------------
    def _set_mode(self, value: str) -> None:
        self.mode.set(value)
        if value == "full":
            self.btn_full.configure(style="Segment.Active.TButton")
            self.btn_body.configure(style="Segment.TButton")
        else:
            self.btn_body.configure(style="Segment.Active.TButton")
            self.btn_full.configure(style="Segment.TButton")

    def _set_status(self, text: str, kind: str = "info") -> None:
        if kind == "ok":
            self.status.configure(text=text, style="StatusOK.TLabel")
        elif kind == "err":
            self.status.configure(text=text, style="StatusERR.TLabel")
        else:
            self.status.configure(text=text, style="Status.TLabel")

    def _pulse_progress(self, to: int) -> None:
        cur = int(self.progress["value"])
        step = 4 if to - cur > 4 else 1
        for v in range(cur, to + 1, step):
            self.progress["value"] = v
            self.update_idletasks()

    def _auto_suggest_output(self, *_):
        raw = self.input_path.get().strip()
        if raw and not self.output_path.get().strip():
            try:
                self.output_path.set(str(infer_output_path(Path(raw))))
            except Exception:
                pass

    def _use_recent(self) -> None:
        sel = self.recent_combo.get().strip()
        if not sel:
            return
        p = Path(sel)
        self.input_path.set(str(p))
        if not self.output_path.get().strip():
            self.output_path.set(str(infer_output_path(p)))

        # -------------------- handlers --------------------
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
        from pathlib import Path as _P
        folder = _P(out).parent
        try:
            if platform.system() == "Windows":
                os.startfile(str(folder))  # type: ignore[attr-defined]
            elif platform.system() == "Darwin":
                subprocess.run(["open", str(folder)], check=False)
            else:
                subprocess.run(["xdg-open", str(folder)], check=False)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a pasta:\n{e}")

    def _copy_html(self) -> None:
        if not getattr(self, "current_html", ""):
            messagebox.showinfo("Copiar HTML", "Não há HTML gerado ainda.")
            return
        self.clipboard_clear()
        self.clipboard_append(self.current_html)
        self._set_status("HTML copiado para a área de transferência", "ok")

    def _about(self) -> None:
        messagebox.showinfo(
            "Sobre",
            "Markdown → HTML\n\n"
            "Trabalho de POO II (Builder Pattern)\n"
            "• Conversor simples Markdown → HTML\n"
            "• GUI em Tkinter (modo claro)\n\n"
            "Atalhos: Ctrl+O (abrir), Ctrl+S (salvar), Enter/Ctrl+Enter (converter)"
        )


    # -------------------- core action --------------------
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

            # UI busy
            self.btn_convert.config(state="disabled")
            self.btn_open_folder.config(state="disabled")
            self._set_status("Convertendo…")
            self._pulse_progress(30)

            html = build_from_file(inp, mode=self.mode.get())
            self.current_html = html

            self._pulse_progress(70)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(html, encoding=self.encoding.get())

            # atualizar preview
            self.prev_text.configure(state="normal")
            self.prev_text.delete("1.0", "end")
            self.prev_text.insert("1.0", html)
            self.prev_text.configure(state="disabled")

            # histórico
            self._update_recents(str(inp))

            self._pulse_progress(100)
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
            self.btn_convert.config(state="normal")
            self.btn_open_folder.config(state="normal")

    def _update_recents(self, new_item: str) -> None:
        new_item = str(Path(new_item))  # normaliza
        items = [i for i in self.recents if i != new_item]
        items.insert(0, new_item)
        self.recents = items[:MAX_RECENTS]
        self.recent_combo["values"] = self.recents
        save_recents(self.recents)


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
