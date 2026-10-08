import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

import keyboard
import pyperclip

try:
    from deep_translator import GoogleTranslator
except ImportError:  # pragma: no cover
    GoogleTranslator = None


class TranslationPopup(tk.Toplevel):
    def __init__(self, master, text):
        super().__init__(master)
        self.title("Tradução")
        self.geometry("420x170")
        self.minsize(360, 150)
        self.configure(bg="#F5F7FA")
        self.attributes("-topmost", True)
        self.transient(master)
        self.grab_set()

        main = ttk.Frame(self, padding=12)
        main.pack(fill="both", expand=True)

        ttk.Label(
            main,
            text="Tradução para inglês:",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        text_box = tk.Text(main, height=6, wrap="word", font=("Segoe UI", 10), padx=8, pady=6)
        text_box.insert("1.0", text)
        text_box.configure(state="disabled")
        text_box.pack(fill="both", expand=True)

        buttons = ttk.Frame(main)
        buttons.pack(fill="x", pady=(10, 0))

        ttk.Button(buttons, text="Copiar", command=lambda: self.copy_and_close(text)).pack(side="right")
        ttk.Button(buttons, text="Fechar", command=self.destroy).pack(side="right", padx=(0, 8))

    def copy_and_close(self, text):
        try:
            pyperclip.copy(text)
        except Exception:
            pass
        self.destroy()


class MiniTranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mini Tradutor")
        self.root.geometry("280x230")
        self.root.resizable(False, False)
        self.root.configure(bg="#F3F6FA")
        self.root.minsize(260, 200)

        self.enabled = True
        self.shortcut = "ctrl+e"
        self.status_text = tk.StringVar(value="Ativado")
        self.status_color = tk.StringVar(value="#2E7D32")
        self.status_label = None

        self.translator = None
        if GoogleTranslator is not None:
            self.translator = GoogleTranslator(source="auto", target="en")

        self.build_ui()
        self.register_shortcut()

        self.root.protocol("WM_DELETE_WINDOW", self.minimize_window)

    def build_ui(self):
        container = ttk.Frame(self.root, padding=14)
        container.pack(fill="both", expand=True)

        title = ttk.Label(container, text="Mini Tradutor", font=("Segoe UI", 12, "bold"))
        title.pack(pady=(0, 10))

        status_frame = ttk.Frame(container)
        status_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(status_frame, text="Status:", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.status_label = tk.Label(
            status_frame,
            textvariable=self.status_text,
            fg=self.status_color.get(),
            font=("Segoe UI", 10, "bold"),
            padx=8,
            pady=4,
            bd=1,
            relief="solid",
            bg="#FFFFFF",
        )
        self.status_label.pack(side="left", padx=(8, 0))

        buttons = ttk.Frame(container)
        buttons.pack(fill="x", pady=8)

        ttk.Button(buttons, text="Ativar", command=self.activate).pack(fill="x", pady=4)
        ttk.Button(buttons, text="Desativar", command=self.deactivate).pack(fill="x", pady=4)

        ttk.Button(container, text="Minimizar", command=self.minimize_window).pack(fill="x", pady=4)
        ttk.Button(container, text="Fechar", command=self.shutdown).pack(fill="x", pady=4)

    def register_shortcut(self):
        try:
            keyboard.add_hotkey(self.shortcut, self.trigger_translation, suppress=False)
        except Exception as exc:  # pragma: no cover
            messagebox.showerror("Erro de atalho", f"Não foi possível registrar o atalho {self.shortcut}:\n{exc}")

    def activate(self):
        self.enabled = True
        self.update_status("Ativado", "#2E7D32")

    def deactivate(self):
        self.enabled = False
        self.update_status("Desativado", "#C62828")

    def update_status(self, text, color):
        self.status_text.set(text)
        self.status_color.set(color)
        if self.status_label is not None:
            self.status_label.configure(fg=color)

    def trigger_translation(self):
        if not self.enabled:
            return

        thread = threading.Thread(target=self.translate_selected_text, daemon=True)
        thread.start()

    def translate_selected_text(self):
        if self.translator is None:
            self.show_error("Biblioteca ausente", "Instale a dependência 'deep-translator' antes de usar o tradutor.")
            return

        try:
            original_clipboard = pyperclip.paste()
        except Exception:
            original_clipboard = ""

        try:
            time.sleep(0.05)
            keyboard.press_and_release("ctrl+c")
            time.sleep(0.12)
            selected_text = pyperclip.paste().strip()
        except Exception as exc:
            self.show_error("Erro ao capturar texto", f"Não foi possível ler o texto selecionado.\n{exc}")
            return

        if not selected_text:
            self.show_error("Nenhum texto selecionado", "Selecione uma palavra, frase ou parágrafo e pressione Ctrl + E.")
            return

        try:
            translated = self.translator.translate(selected_text)
        except Exception as exc:
            self.show_error(
                "Erro de tradução",
                "Não foi possível traduzir o texto. Verifique a conexão com a internet e tente novamente.\n\nDetalhes: "
                f"{exc}",
            )
            return

        if not translated or not translated.strip():
            self.show_error("Erro de tradução", "A tradução não retornou nenhum texto válido.")
            return

        try:
            pyperclip.copy(translated)
            time.sleep(0.08)
            keyboard.press_and_release("ctrl+v")
            time.sleep(0.12)
        except Exception:
            pass
        finally:
            try:
                pyperclip.copy(original_clipboard)
            except Exception:
                pass

        self.root.after(0, lambda: TranslationPopup(self.root, translated))

    def minimize_window(self):
        self.root.iconify()

    def shutdown(self):
        try:
            keyboard.remove_hotkey(self.shortcut)
        except Exception:
            pass
        self.root.destroy()

    def show_error(self, title, message):
        self.root.after(0, lambda: messagebox.showerror(title, message))


def main():
    root = tk.Tk()
    app = MiniTranslatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
