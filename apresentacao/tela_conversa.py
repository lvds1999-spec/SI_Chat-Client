import tkinter as tk


class TelaConversa(tk.Frame):

    def __init__(self, parent, servico_conversas, usuario, banco_local, ao_digitando=None):
        super().__init__(parent)
        self.servico_conversas = servico_conversas
        self.usuario = usuario
        self.banco_local = banco_local
        self.destinatario = None
        self.ao_digitando = ao_digitando
        self.mensagens = {}

        self.titulo = tk.Label(self, text="Selecione um contato", anchor="w")
        self.titulo.pack(fill=tk.X)
        self.historico = tk.Text(self, state=tk.DISABLED, wrap=tk.WORD)
        self.historico.pack(fill=tk.BOTH, expand=True, pady=8)
        self.status = tk.Label(self, text="", anchor="w")
        self.status.pack(fill=tk.X)

        envio = tk.Frame(self)
        envio.pack(fill=tk.X)
        self.campo = tk.Entry(envio)
        self.campo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.campo.bind("<KeyRelease>", self._tecla)
        self.campo.bind("<Return>", self.enviar)
        tk.Button(envio, text="Enviar", command=self.enviar).pack(side=tk.RIGHT, padx=(5, 0))

    def selecionar(self, contato, online):
        self.destinatario = contato
        estado = "online" if online else "offline"
        self.titulo.config(text=f"{contato} - {estado}")
        self.mensagens[contato] = self.banco_local.listar_mensagens(
            contato, self.usuario
        )
        self._renderizar()

    def adicionar_mensagem(self, mensagem, recebida=False, persistir=True):
        contato = mensagem.get("remetente") if recebida else mensagem.get("destinatario")
        if not contato:
            return
        if persistir:
            self.banco_local.salvar_mensagem(mensagem)
        self.mensagens.setdefault(contato, []).append(mensagem)
        if contato == self.destinatario:
            self._renderizar()

    def definir_status(self, texto):
        self.status.config(text=texto)

    def enviar(self, _evento=None):
        if not self.destinatario:
            return "break"
        texto = self.campo.get().strip()
        if not texto:
            return "break"
        mensagem = self.servico_conversas.enviar_mensagem(self.destinatario, texto)
        self.adicionar_mensagem(mensagem, persistir=False)
        self.campo.delete(0, tk.END)
        if self.ao_digitando:
            self.ao_digitando(False, self.destinatario)
        return "break"

    def _tecla(self, _evento=None):
        if self.ao_digitando and self.destinatario:
            self.ao_digitando(bool(self.campo.get()), self.destinatario)

    def _renderizar(self):
        self.historico.config(state=tk.NORMAL)
        self.historico.delete("1.0", tk.END)
        for mensagem in self.mensagens.get(self.destinatario, []):
            prefixo = mensagem.get("remetente")
            if prefixo == self.usuario:
                prefixo = "Você"
            self.historico.insert(tk.END, f"{prefixo}: {mensagem.get('texto', '')}\n")
        self.historico.config(state=tk.DISABLED)
        self.historico.see(tk.END)
