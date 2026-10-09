
import subprocess
import sys

bibliotecas = [
    "argostranslate==1.11.0",
    "keyboard==0.13.5",
    "pyperclip==1.11.0"
]

print("Instalando bibliotecas...\n")

try:
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", *bibliotecas
    ])
    print("\nTodas as bibliotecas foram instaladas com sucesso!")

except subprocess.CalledProcessError:
    print("\nOcorreu um erro durante a instalação.")
    print("Verifique sua conexão com a internet e tente novamente.")
