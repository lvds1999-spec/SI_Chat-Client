import tkinter as tk

from apresentacao.gui import GUI


class GUI:

    def __init__(self, cliente_socket):

        self.cliente_socket = cliente_socket

        self.janela = tk.Tk()

        self.janela.title("Chat")
        self.janela.geometry("420x320")

        self.criar_interface()

    def criar_interface(self):

        titulo = tk.Label(
            self.janela,
            text="Cliente de Chat"
        )

        titulo.pack(pady=20)

        formulario = tk.Frame(self.janela)
        formulario.pack(pady=10)

        tk.Label(formulario, text="Nome:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.nome = tk.Entry(formulario, width=28)
        self.nome.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(formulario, text="Senha:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
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

    def _enviar_autenticacao(self, tipo, nome=None, senha=None):
        nome = self.nome.get().strip() if nome is None else nome
        senha = self.senha.get() if senha is None else senha

        if not nome or not senha:
            self.status.config(text="Informe nome e senha.")
            return

        if not self.cliente_socket.conectado:
            self.status.config(text="Cliente desconectado.")
            return

        try:
            self.cliente_socket.enviar({
                "tipo": tipo,
                "nome": nome,
                "senha": senha,
            })
            self.status.config(text="Aguardando resposta do servidor...")
        except Exception as erro:
            self.status.config(text=f"Não foi possível enviar a solicitação: {erro}")

    def login(self):
        self._enviar_autenticacao(LOGIN)

    def registrar(self):
        self._enviar_autenticacao(REGISTRO)

    def processar_evento(self, evento):
        """Agenda o tratamento do evento na thread da interface."""

        self.janela.after(0, self._exibir_resposta, evento)

    def _exibir_resposta(self, evento):
        tipo = evento.get("tipo", evento.get("evento"))
        sucesso = evento.get("sucesso")
        mensagem = evento.get("mensagem")
        situacao = evento.get(
            "status",
            evento.get("resultado", evento.get("erro", evento.get("motivo")))
        )

        if tipo == RESPOSTA_REGISTRO:
            if evento.get("nome_em_uso") or situacao == "nome_em_uso":
                self.status.config(text="Nome em uso.")
            elif sucesso is True or situacao in ("sucesso", "ok"):
                self.status.config(text=mensagem or "Registro realizado com sucesso.")
            else:
                self.status.config(text=mensagem or "Não foi possível realizar o registro.")
        elif tipo == RESPOSTA_LOGIN:
            if evento.get("credenciais_validas") is False or situacao == "credenciais_invalidas":
                self.status.config(text="Credenciais inválidas.")
            elif sucesso is True or situacao in ("sucesso", "ok"):
                self.status.config(text=mensagem or "Login realizado com sucesso. Cliente conectado.")
            else:
                self.status.config(text=mensagem or "Não foi possível realizar o login.")

        if tipo == RESPOSTA_REGISTRO and (sucesso is True or situacao in ("sucesso", "ok")):
            self.status.config(text="Registro realizado. Entrando na conta...")
            self._enviar_autenticacao(LOGIN)
        else:
            self.status.config(text=mensagem or f"Evento recebido: {tipo}")

    def iniciar(self):

        self.janela.mainloop()