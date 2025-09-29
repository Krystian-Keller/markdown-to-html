# markdown_to_html/gui.py
from __future__ import annotations

from pathlib import Path
import traceback
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from .main import infer_output_path, build_from_file


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Markdown → HTML")
        self.geometry("640x280")
        self.minsize(600, 260)

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.mode = tk.StringVar(value="full")
        self.force = tk.BooleanVar(value=False)
        self.encoding = tk.StringVar(value="utf-8")

        self._build_ui()

    def _build_ui(self) -> None:
        pad = {"padx": 10, "pady": 8}
        frm = ttk.Frame(self); frm.pack(fill="both", expand=True)

        # Input
        ttk.Label(frm, text="Arquivo Markdown (.md / .markdown):").grid(row=0, column=0, sticky="w", **pad)
        row_in = ttk.Frame(frm); row_in.grid(row=1, column=0, sticky="we", **pad); row_in.columnconfigure(0, weight=1)
        ttk.Entry(row_in, textvariable=self.input_path).grid(row=0, column=0, sticky="we", padx=(0, 6))
        ttk.Button(row_in, text="Selecionar…", command=self.browse_input).grid(row=0, column=1)

        # Output
        ttk.Label(frm, text="Arquivo de saída (.html):").grid(row=2, column=0, sticky="w", **pad)
        row_out = ttk.Frame(frm); row_out.grid(row=3, column=0, sticky="we", **pad); row_out.columnconfigure(0, weight=1)
        ttk.Entry(row_out, textvariable=self.output_path).grid(row=0, column=0, sticky="we", padx=(0, 6))
        ttk.Button(row_out, text="Escolher…", command=self.browse_output).grid(row=0, column=1)

        # Options
        opt = ttk.Frame(frm); opt.grid(row=4, column=0, sticky="we", **pad)
        ttk.Label(opt, text="Modo de saída:").grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(opt, text="Página completa", value="full", variable=self.mode).grid(row=0, column=1, sticky="w", padx=(8, 0))
        ttk.Radiobutton(opt, text="Apenas body", value="body", variable=self.mode).grid(row=0, column=2, sticky="w", padx=(8, 0))
        ttk.Checkbutton(opt, text="Sobrescrever se existir", variable=self.force).grid(row=0, column=3, sticky="w", padx=(16, 0))
        ttk.Label(opt, text="Encoding:").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Combobox(opt, textvariable=self.encoding, values=["utf-8","latin-1"], width=12, state="readonly")\
            .grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        # Actions
        action = ttk.Frame(frm); action.grid(row=5, column=0, sticky="we", **pad); action.columnconfigure(0, weight=1)
        self.status = ttk.Label(action, text="", foreground="#555"); self.status.grid(row=0, column=0, sticky="w")
        ttk.Button(action, text="Converter", command=self.convert).grid(row=0, column=1, sticky="e")

    def browse_input(self) -> None:
        path = filedialog.askopenfilename(
            title="Selecione o arquivo Markdown",
            filetypes=[("Markdown", "*.md *.markdown"), ("Todos", "*.*")],
        )
        if not path: return
        self.input_path.set(path)
        if not self.output_path.get().strip():
            self.output_path.set(str(infer_output_path(Path(path))))

    def browse_output(self) -> None:
        initial = self.output_path.get().strip()
        initdir = str(Path(initial).parent) if initial else None
        path = filedialog.asksaveasfilename(
            title="Salvar como", defaultextension=".html", filetypes=[("HTML", "*.html")],
            initialdir=initdir, initialfile=Path(initial).name if initial else None,
        )
        if path: self.output_path.set(path)

    def convert(self) -> None:
        try:
            inp = Path(self.input_path.get().strip())
            if not inp.exists() or not inp.is_file():
                messagebox.showerror("Erro", f"Arquivo de entrada não encontrado:\n{inp}"); return

            out = self.output_path.get().strip() or str(infer_output_path(inp))
            out_path = Path(out)
            if out_path.exists() and not self.force.get():
                messagebox.showwarning("Saída já existe",
                    f"O arquivo já existe:\n{out_path}\n\nMarque 'Sobrescrever' para substituir."); return

            self.status.config(text="Convertendo…"); self.update_idletasks()
            html = build_from_file(inp, mode=self.mode.get())
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(html, encoding=self.encoding.get())

            self.status.config(text=f"OK: salvo em {out_path}")
            messagebox.showinfo("Sucesso", f"HTML gerado com sucesso:\n{out_path}")

        except Exception as e:
            self.status.config(text="Falha na conversão")
            traceback.print_exc()
            messagebox.showerror("Erro", f"Falha ao converter:\n{e}")


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
