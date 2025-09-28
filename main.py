import os
from tkinter import Tk
from tkinter import filedialog
from builder import HtmlBuilder  #
from diretor import Diretor


# ================= MAIN ==================
def menu():
    print("=== Conversor Markdown → HTML ===")

    # Inicializa o Tkinter (sem mostrar a janela principal)
    root = Tk()
    root.withdraw()

    # Seleciona o arquivo Markdown
    md_file = filedialog.askopenfilename(
        title="Selecione o arquivo Markdown",
        filetypes=[("Markdown files", "*.md")]
    )
    if not md_file:
        print("Nenhum arquivo selecionado!")
        return

    # Seleciona o diretório de saída
    save_dir = filedialog.askdirectory(title="Selecione a pasta de destino")
    if not save_dir:
        save_dir = os.getcwd()  # usa diretório atual por padrão

    nome_arquivo = os.path.basename(md_file)
    saida = os.path.join(save_dir, nome_arquivo.replace(".md", ".html"))

    # Builder + Diretor
    builder = HtmlBuilder()
    diretor = Diretor(builder)

    diretor.construir(md_file)
    html = builder.get_result()

    # escreve saída
    with open(saida, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Conversão concluída! Arquivo salvo em: {saida}")


if __name__ == "__main__":
    menu()
