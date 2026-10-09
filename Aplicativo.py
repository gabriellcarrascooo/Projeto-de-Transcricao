
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

import keyboard
import pyperclip


try:
    import argostranslate.package
    import argostranslate.translate
except ImportError:
    argostranslate = None


class LocalTranslator:
    def __init__(self):
        self.available = argostranslate is not None

    def is_model_installed(self):
        if not self.available:
            return False

        source_language = argostranslate.translate.get_language_from_code("pt")
        target_language = argostranslate.translate.get_language_from_code("en")
        return (
            source_language is not None
            and target_language is not None
            and source_language.get_translation(target_language) is not None
        )

    def install_model(self):
        if not self.available:
            raise RuntimeError(
                "A biblioteca Argos Translate não está instalada. "
                "Instale as dependências de requirements.txt."
            )

        argostranslate.package.update_package_index()
        package = next(
            (
                item
                for item in argostranslate.package.get_available_packages()
                if item.from_code == "pt" and item.to_code == "en"
            ),
            None
        )
        if package is None:
            raise RuntimeError(
                "O modelo de português para inglês não foi encontrado."
            )

        package_path = package.download()
        argostranslate.package.install_from_path(package_path)

    def translate(self, text):
        source_language = argostranslate.translate.get_language_from_code("pt")
        if source_language is None:
            raise RuntimeError("O idioma português não está disponível.")

        target_language = argostranslate.translate.get_language_from_code("en")
        if target_language is None:
            raise RuntimeError("O idioma inglês não está disponível.")

        translation = source_language.get_translation(
            target_language
        )
        if translation is None:
            raise RuntimeError(
                "Instale o modelo de português para inglês antes de traduzir."
            )
        return translation.translate(text)


class TranslationPopup(tk.Toplevel):
    def __init__(self, master, text):
        super().__init__(master)

        self.title("Tradução")
        self.geometry("420x190")
        self.minsize(360, 150)
        self.attributes("-topmost", True)

        main = ttk.Frame(self, padding=12)
        main.pack(fill="both", expand=True)

        ttk.Label(
            main,
            text="Tradução para inglês:",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", pady=(0, 8))

        text_box = tk.Text(
            main,
            height=5,
            wrap="word",
            font=("Segoe UI", 10),
            padx=8,
            pady=6
        )
        text_box.insert("1.0", text)
        text_box.configure(state="disabled")
        text_box.pack(fill="both", expand=True)

        buttons = ttk.Frame(main)
        buttons.pack(fill="x", pady=(10, 0))

        ttk.Button(
            buttons,
            text="Copiar",
            command=lambda: self.copy_text(text)
        ).pack(side="right")

        ttk.Button(
            buttons,
            text="Fechar",
            command=self.destroy
        ).pack(side="right", padx=(0, 8))

    def copy_text(self, text):
        try:
            pyperclip.copy(text)
            self.destroy()
        except Exception as exc:
            messagebox.showerror(
                "Erro ao copiar",
                str(exc),
                parent=self
            )


class MiniTranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mini Tradutor")
        self.root.geometry("300x285")
        self.root.resizable(False, False)

        self.enabled = True
        self.shortcut = "alt+z"  # Mantido: ALT + Z
        self.is_translating = False
        self.model_installing = False
        self.closing = False

        self.translator = LocalTranslator()
        self.model_installed = self.translator.is_model_installed()
        self.status_text = tk.StringVar(
            value=(
                "Pronto (offline)"
                if self.model_installed
                else "Instale o modelo"
            )
        )
        self.status_color = (
            "#2E7D32" if self.model_installed else "#B26A00"
        )
        self.status_label = None

        self.build_ui()
        self.register_shortcut()

        # Clicar no X minimiza o aplicativo.
        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.minimize_window
        )

    def build_ui(self):
        container = ttk.Frame(self.root, padding=14)
        container.pack(fill="both", expand=True)

        ttk.Label(
            container,
            text="Mini Tradutor",
            font=("Segoe UI", 12, "bold")
        ).pack(pady=(0, 10))

        ttk.Label(
            container,
            text="Atalho: Alt + Z | Tradução local gratuita"
        ).pack(pady=(0, 8))

        status_frame = ttk.Frame(container)
        status_frame.pack(fill="x", pady=(0, 8))

        ttk.Label(
            status_frame,
            text="Status:",
            font=("Segoe UI", 10, "bold")
        ).pack(side="left")

        self.status_label = tk.Label(
            status_frame,
            textvariable=self.status_text,
            fg=self.status_color,
            font=("Segoe UI", 10, "bold"),
            padx=8,
            pady=4,
            bd=1,
            relief="solid",
            bg="#FFFFFF"
        )
        self.status_label.pack(side="left", padx=(8, 0))

        self.install_button = ttk.Button(
            container,
            text="Instalar modelo português → inglês",
            command=self.install_model
        )
        self.install_button.pack(fill="x", pady=3)
        if self.model_installed:
            self.install_button.configure(
                text="Modelo português → inglês instalado",
                state="disabled"
            )

        buttons = ttk.Frame(container)
        buttons.pack(fill="x", pady=4)

        ttk.Button(
            buttons,
            text="Ativar",
            command=self.activate
        ).pack(fill="x", pady=3)

        ttk.Button(
            buttons,
            text="Desativar",
            command=self.deactivate
        ).pack(fill="x", pady=3)

        ttk.Button(
            container,
            text="Minimizar",
            command=self.minimize_window
        ).pack(fill="x", pady=3)

        ttk.Button(
            container,
            text="Fechar programa",
            command=self.shutdown
        ).pack(fill="x", pady=3)

    def register_shortcut(self):
        try:
            keyboard.add_hotkey(
                self.shortcut,
                self.trigger_translation,
                suppress=True
            )
        except Exception as exc:
            messagebox.showerror(
                "Erro de atalho",
                f"Não foi possível registrar Alt + Z:\n\n{exc}",
                parent=self.root
            )

    def activate(self):
        self.enabled = True
        self.update_status("Ativado", "#2E7D32")

    def deactivate(self):
        self.enabled = False
        self.update_status("Desativado", "#C62828")

    def update_status(self, text, color):
        self.status_text.set(text)
        self.status_color = color

        if self.status_label is not None:
            self.status_label.configure(fg=color)

    def trigger_translation(self):
        # O atalho pode ser executado por outra thread.
        if self.closing:
            return

        self.root.after(0, self.start_translation)

    def start_translation(self):
        if not self.enabled or self.is_translating or self.model_installing:
            return

        if not self.translator.available:
            messagebox.showerror(
                "Biblioteca ausente",
                "Instale as dependências com:\n\n"
                ".venv\\Scripts\\python.exe -m pip install -r requirements.txt",
                parent=self.root
            )
            return

        if not self.translator.is_model_installed():
            messagebox.showinfo(
                "Modelo necessário",
                "Clique em “Instalar modelo português → inglês” uma vez. "
                "O download precisa de internet; depois, a tradução "
                "funciona offline.",
                parent=self.root
            )
            return

        self.is_translating = True

        threading.Thread(
            target=self.translate_selected_text,
            daemon=True
        ).start()

    def install_model(self):
        if self.model_installing or self.is_translating:
            return

        if not self.translator.available:
            messagebox.showerror(
                "Biblioteca ausente",
                "Instale as dependências com:\n\n"
                ".venv\\Scripts\\python.exe -m pip install -r requirements.txt",
                parent=self.root
            )
            return

        if self.translator.is_model_installed():
            return

        self.model_installing = True
        self.install_button.configure(state="disabled")
        self.update_status("Baixando modelo...", "#B26A00")
        threading.Thread(
            target=self.install_translation_model,
            daemon=True
        ).start()

    def install_translation_model(self):
        try:
            self.translator.install_model()
        except Exception as exc:
            self.root.after(0, self.finish_model_installation, str(exc))
        else:
            self.root.after(0, self.finish_model_installation, None)

    def finish_model_installation(self, error):
        self.model_installing = False
        if self.closing:
            return

        if error:
            self.install_button.configure(state="normal")
            self.update_status("Falha na instalação", "#C62828")
            messagebox.showerror(
                "Erro ao instalar modelo",
                "Não foi possível baixar ou instalar o modelo.\n\n"
                "Verifique a conexão com a internet e tente novamente.\n\n"
                f"Detalhes: {error}",
                parent=self.root
            )
            return

        self.install_button.configure(
            text="Modelo português → inglês instalado",
            state="disabled"
        )
        self.model_installed = True
        self.update_status("Pronto (offline)", "#2E7D32")

    def show_error(self, title, message):
        if self.closing:
            return

        self.root.after(
            0,
            lambda: self.show_error_safe(title, message)
        )

    def show_error_safe(self, title, message):
        if not self.closing:
            messagebox.showerror(
                title,
                message,
                parent=self.root
            )

    def show_popup_safe(self, text):
        if not self.closing:
            TranslationPopup(self.root, text)

    def finish_translation(self):
        self.is_translating = False

    def translate_selected_text(self):
        original_clipboard = None
        translated = None

        try:
            # Guarda o conteúdo atual da área de transferência.
            original_clipboard = pyperclip.paste()

            # Limpa temporariamente para verificar se Ctrl+C
            # realmente copiou o texto selecionado.
            pyperclip.copy("")

            # Evita enviar Ctrl+C enquanto Alt ainda está pressionada.
            release_deadline = time.monotonic() + 1.0
            while keyboard.is_pressed("alt") and time.monotonic() < release_deadline:
                time.sleep(0.02)

            keyboard.press_and_release("ctrl+c")

            # Aguarda o aplicativo em foco atualizar a área de transferência.
            copy_deadline = time.monotonic() + 1.5
            selected_text = ""
            while time.monotonic() < copy_deadline:
                selected_text = pyperclip.paste().strip()
                if selected_text:
                    break
                time.sleep(0.05)

            if not selected_text:
                self.show_error(
                    "Nenhum texto selecionado",
                    "Selecione uma palavra, frase ou parágrafo "
                    "e pressione Alt + Z. Se o texto já estiver "
                    "selecionado, verifique se o aplicativo permite copiá-lo."
                )
                return

            # Traduz o texto para inglês.
            translated = self.translator.translate(selected_text)

            if not translated or not translated.strip():
                self.show_error(
                    "Erro de tradução",
                    "A tradução não retornou um texto válido."
                )
                return

            # Restaura a área de transferência original antes
            # de mostrar a tradução.
            if original_clipboard is not None:
                pyperclip.copy(original_clipboard)

            self.root.after(
                0,
                self.show_popup_safe,
                translated.strip()
            )

        except Exception as exc:
            error_details = str(exc)
            self.show_error(
                "Erro de tradução",
                "Não foi possível concluir a tradução.\n\n"
                "Se o modelo local já estiver instalado, a tradução "
                "não precisa de internet.\n\n"
                f"Detalhes: {error_details}"
            )

        finally:
            # Garante que a área de transferência seja restaurada.
            if original_clipboard is not None:
                try:
                    pyperclip.copy(original_clipboard)
                except Exception:
                    pass

            if not self.closing:
                self.root.after(0, self.finish_translation)

    def minimize_window(self):
        self.root.iconify()

    def shutdown(self):
        self.closing = True

        try:
            keyboard.remove_hotkey(self.shortcut)
        except Exception:
            pass

        self.root.destroy()


def main():
    root = tk.Tk()
    app = MiniTranslatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
