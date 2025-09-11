import tkinter
import customtkinter
from difflib import Differ
from deepdiff import DeepDiff
import json
import darkdetect

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Comparador Universal")
        self.geometry("1000x600")

        # Configurar tema inicial
        self.set_initial_theme()

        # Configurar o grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Botão de tema
        self.theme_button = customtkinter.CTkButton(self, text="Mudar Tema", command=self.change_theme)
        self.theme_button.grid(row=0, column=1, padx=10, pady=10, sticky="e")

        # Frame para os inputs
        self.input_frame = customtkinter.CTkFrame(self)
        self.input_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=10, sticky="nsew")
        self.input_frame.grid_columnconfigure(0, weight=1)
        self.input_frame.grid_columnconfigure(1, weight=1)
        self.input_frame.grid_rowconfigure(1, weight=1)

        # Input da Esquerda
        self.original_label = customtkinter.CTkLabel(self.input_frame, text="Texto original")
        self.original_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.original_text = customtkinter.CTkTextbox(self.input_frame, width=400, height=400)
        self.original_text.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        # Input da Direita
        self.altered_label = customtkinter.CTkLabel(self.input_frame, text="Texto alterado")
        self.altered_label.grid(row=0, column=1, padx=10, pady=5, sticky="w")
        self.altered_text = customtkinter.CTkTextbox(self.input_frame, width=400, height=400)
        self.altered_text.grid(row=1, column=1, padx=10, pady=5, sticky="nsew")

        # Botão de Comparação
        self.compare_button = customtkinter.CTkButton(self, text="Encontrar Diferença", command=self.find_difference)
        self.compare_button.grid(row=2, column=0, columnspan=2, padx=20, pady=10)

        # Frame para o resultado
        self.result_frame = customtkinter.CTkFrame(self)
        self.result_frame.grid(row=3, column=0, columnspan=2, padx=20, pady=10, sticky="nsew")
        self.result_frame.grid_columnconfigure(0, weight=1)
        self.result_frame.grid_rowconfigure(0, weight=1)
        
        self.result_text = customtkinter.CTkTextbox(self.result_frame, width=800, height=200)
        self.result_text.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.result_text.configure(state="disabled")

    def set_initial_theme(self):
        theme = darkdetect.theme()
        if theme == "Dark":
            customtkinter.set_appearance_mode("dark")
        else:
            customtkinter.set_appearance_mode("light")

    def change_theme(self):
        if customtkinter.get_appearance_mode() == "Light":
            customtkinter.set_appearance_mode("dark")
        else:
            customtkinter.set_appearance_mode("light")

    def find_difference(self):
        original_content = self.original_text.get("1.0", tkinter.END)
        altered_content = self.altered_text.get("1.0", tkinter.END)

        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", tkinter.END)

        # Tenta a comparação como JSON
        try:
            original_json = json.loads(original_content)
            altered_json = json.loads(altered_content)
            diff = DeepDiff(original_json, altered_json, view='text')
            if diff:
                self.result_text.insert(tkinter.END, "Diferenças encontradas (JSON/Properties):\n\n")
                self.result_text.insert(tkinter.END, diff)
            else:
                self.result_text.insert(tkinter.END, "Nenhuma diferença encontrada.")
        except json.JSONDecodeError:
            # Se não for JSON, compara como texto
            d = Differ()
            diff = list(d.compare(original_content.splitlines(), altered_content.splitlines()))
            
            has_diff = any(line.startswith('+ ') or line.startswith('- ') or line.startswith('? ') for line in diff)

            if has_diff:
                self.result_text.insert(tkinter.END, "Diferenças encontradas (Texto):\n\n")
                for line in diff:
                    self.result_text.insert(tkinter.END, line + "\n")
            else:
                self.result_text.insert(tkinter.END, "Nenhuma diferença encontrada.")

        self.result_text.configure(state="disabled")

if __name__ == "__main__":
    app = App()
    app.mainloop()