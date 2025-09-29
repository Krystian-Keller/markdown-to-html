import os
from tkinter import Tk
from tkinter import filedialog
from builder import HtmlBuilder  
from director.diretor import Diretor

def menu():
    print("=== Conversor Markdown → HTML ===")

    root = Tk()
    root.withdraw()

    md_file = filedialog.askopenfilename(
        title="Selecione o arquivo Markdown",
        filetypes=[("Markdown files", "*.md")]
    )
    if not md_file:
        print("Nenhum arquivo selecionado!")
        return

    save_dir = filedialog.askdirectory(title="Selecione a pasta de destino")
    if not save_dir:
        save_dir = os.getcwd()  # diretório atual

    nome_arquivo = os.path.basename(md_file)
    saida = os.path.join(save_dir, nome_arquivo.replace(".md", ".html"))

    # builder + diretor
    builder = HtmlBuilder()
    diretor = Diretor(builder)

    diretor.construir(md_file)
    html = builder.get_result()

    with open(saida, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Conversão concluída! Arquivo salvo em: {saida}")


if __name__ == "__main__":
    menu()

