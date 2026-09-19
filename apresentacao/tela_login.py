import tkinter as tk

from apresentacao.tela_chat import TelaChat
from dominio.servico_sessao import (
    LOGIN,
    REGISTRO,
    RESPOSTA_LOGIN,
    RESPOSTA_REGISTRO,
)


class TelaLogin:

    def __init__(self, servico_sessao):
        self.servico_sessao = servico_sessao

        self.janela = tk.Tk()
        self.janela.title("Login - Cliente de Chat")
        self.janela.geometry("420x320")
        self.janela.protocol("WM_DELETE_WINDOW", self.fechar)

        self.criar_interface()

    def criar_interface(self):
        tk.Label(self.janela, text="Cliente de Chat").pack(pady=20)

        formulario = tk.Frame(self.janela)
        formulario.pack(pady=10)

        tk.Label(formulario, text="Nome:").grid(
            row=0, column=0, padx=5, pady=5, sticky="e"
        )
        self.nome = tk.Entry(formulario, width=28)
        self.nome.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(formulario, text="Senha:").grid(
            row=1, column=0, padx=5, pady=5, sticky="e"
        )
        self.senha = tk.Entry(formulario, width=28, show="*")
        self.senha.grid(row=1, column=1, padx=5, pady=5)

        botoes = tk.Frame(self.janela)
        botoes.pack(pady=10)

        tk.Button(
            botoes,
            text="Entrar",
            command=self.login
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            botoes,
            text="Registrar",
            command=self.registrar
        ).pack(side=tk.LEFT, padx=5)

        self.status = tk.Label(
            self.janela,
            text="Aguardando ação.",
            wraplength=360
        )
        self.status.pack(pady=15)

    def login(self):
        self._enviar_autenticacao(LOGIN)

    def registrar(self):
        self._enviar_autenticacao(REGISTRO)

    def _enviar_autenticacao(self, tipo):
        usuario = self.nome.get().strip()
        senha = self.senha.get()

        if not usuario or not senha:
            self.status.config(text="Informe nome e senha.")
            return

        try:
            if tipo == LOGIN:
                self.servico_sessao.login(usuario, senha)
            else:
                self.servico_sessao.registrar(usuario, senha)
            self.status.config(text="Aguardando resposta do servidor...")
        except Exception as erro:
            self.status.config(
                text=f"Não foi possível enviar a solicitação: {erro}"
            )

    def processar_evento(self, evento):
        self.janela.after(0, self._exibir_resposta, evento)

    def _exibir_resposta(self, evento):
        tipo = evento.get("evento", evento.get("tipo"))
        sucesso = evento.get("sucesso") is True
        mensagem = evento.get("mensagem")

        if tipo == RESPOSTA_REGISTRO and sucesso:
            self.status.config(text="Registro realizado. Entrando na conta...")
            self.servico_sessao.login(
                self.nome.get().strip(),
                self.senha.get()
            )
        elif tipo == RESPOSTA_REGISTRO:
            self.status.config(text=mensagem or "Nome em uso.")
        elif tipo == RESPOSTA_LOGIN and sucesso:
            self.abrir_chat()
        elif tipo == RESPOSTA_LOGIN:
            self.status.config(text=mensagem or "Credenciais inválidas.")
        else:
            self.status.config(text=mensagem or f"Evento recebido: {tipo}")

    def fechar(self):
        self.servico_sessao.fechar()
        self.janela.destroy()

    def abrir_chat(self):
        usuario = self.nome.get().strip()
        tela_chat = TelaChat(self.servico_sessao, usuario, self.janela)
        self.servico_sessao.definir_callback(tela_chat.processar_evento)

    def iniciar(self):
        self.janela.mainloop()
