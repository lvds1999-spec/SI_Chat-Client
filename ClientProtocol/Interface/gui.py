import tkinter as tk
from tkinter import messagebox


class GUI:

    def __init__(self, cliente_socket):

        self.cliente_socket = cliente_socket

        self.janela = tk.Tk()

        self.janela.title("Chat")
        self.janela.geometry("500x400")

        self.criar_interface()

    def criar_interface(self):

        titulo = tk.Label(
            self.janela,
            text="Cliente de Chat"
        )

        titulo.pack(pady=20)

        self.status = tk.Label(
            self.janela,
            text="Desconectado"
        )

        self.status.pack()

        botao_conectar = tk.Button(
            self.janela,
            text="Conectar",
            command=self.conectar
        )

        botao_conectar.pack(pady=20)

    def conectar(self):

        try:

            if self.cliente_socket.conectado:
                self.status.config(
                    text="Conectado"
                )
                return

            self.cliente_socket.conectar()

            self.status.config(
                text="Conectado"
            )

            messagebox.showinfo(
                "Conexão",
                "Conectado ao servidor."
            )

        except Exception as erro:

            messagebox.showerror(
                "Erro",
                f"Não foi possível conectar:\n{erro}"
            )

    def iniciar(self):

        self.janela.mainloop()