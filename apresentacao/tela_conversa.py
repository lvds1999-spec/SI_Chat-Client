import tkinter as tk


class TelaConversa(tk.Frame):

    TEMPO_LIMITE_DIGITANDO_MS = 2000

    def __init__(self, parent, servico_conversas, usuario, banco_local, ao_digitando=None):
        super().__init__(parent)
        self.servico_conversas = servico_conversas
        self.usuario = usuario
        self.banco_local = banco_local
        self.destinatario = None
        self.ao_digitando = ao_digitando
        self.mensagens = {}
        self._digitando_local = False
        self._fim_digitando_job = None
        self._digitando_remoto = None
        self._limpar_digitando_job = None

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
        self._encerrar_digitacao_local()
        self._limpar_digitando_remoto()
        self.destinatario = contato
        self._atualizar_titulo(online)
        self.mensagens[contato] = self.banco_local.listar_mensagens(
            contato, self.usuario
        )
        self._renderizar()

    def atualizar_presenca(self, usuario, online):
        if usuario == self.destinatario:
            self._atualizar_titulo(online)

    def _atualizar_titulo(self, online):
        if self.destinatario:
            estado = "online" if online else "offline"
            self.titulo.config(text=f"{self.destinatario} - {estado}")

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

    def exibir_digitando(self, usuario):
        if usuario != self.destinatario:
            return
        self._cancelar_limpeza_digitando()
        self._digitando_remoto = usuario
        self.status.config(text=f"{usuario} está digitando...")
        self._limpar_digitando_job = self.after(
            self.TEMPO_LIMITE_DIGITANDO_MS,
            self._limpar_digitando_remoto,
        )

    def remover_digitando(self, usuario=None):
        if usuario is None or usuario == self._digitando_remoto:
            self._limpar_digitando_remoto()

    def enviar(self, _evento=None):
        if not self.destinatario:
            return "break"
        texto = self.campo.get().strip()
        if not texto:
            return "break"
        mensagem = self.servico_conversas.enviar_mensagem(self.destinatario, texto)
        self.adicionar_mensagem(mensagem, persistir=False)
        self.campo.delete(0, tk.END)
        self._encerrar_digitacao_local()
        return "break"

    def _tecla(self, _evento=None):
        if not self.ao_digitando or not self.destinatario:
            return
        if self.campo.get():
            if not self._digitando_local:
                self._digitando_local = True
                self.ao_digitando(True, self.destinatario)
            self._agendar_fim_digitando()
        else:
            self._encerrar_digitacao_local()

    def _agendar_fim_digitando(self):
        if self._fim_digitando_job:
            self.after_cancel(self._fim_digitando_job)
        self._fim_digitando_job = self.after(
            self.TEMPO_LIMITE_DIGITANDO_MS,
            self._encerrar_digitacao_local,
        )

    def _encerrar_digitacao_local(self):
        if self._fim_digitando_job:
            self.after_cancel(self._fim_digitando_job)
            self._fim_digitando_job = None
        if self._digitando_local and self.ao_digitando and self.destinatario:
            self.ao_digitando(False, self.destinatario)
        self._digitando_local = False

    def _cancelar_limpeza_digitando(self):
        if self._limpar_digitando_job:
            self.after_cancel(self._limpar_digitando_job)
            self._limpar_digitando_job = None

    def _limpar_digitando_remoto(self):
        self._cancelar_limpeza_digitando()
        if self._digitando_remoto:
            self._digitando_remoto = None
            self.status.config(text="")

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
