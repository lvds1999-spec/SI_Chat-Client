import tkinter as tk
from datetime import datetime


class TelaChat:

    def __init__(self, servico_sessao, usuario, janela):
        self.servico_sessao = servico_sessao
        self.usuario = usuario
        self.janela = janela
        self.contatos = {}
        self.conversas = {}
        self.contato_selecionado = None
        self.digitando_enviado = False
        self.ativa = True

        self.janela.title(f"Chat - {usuario}")
        self.janela.geometry("760x500")
        self.janela.protocol("WM_DELETE_WINDOW", self.fechar)
        self.criar_interface()

    def criar_interface(self):
        for widget in self.janela.winfo_children():
            widget.destroy()

        principal = tk.Frame(self.janela)
        principal.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        painel_contatos = tk.Frame(principal, width=220)
        painel_contatos.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))
        painel_contatos.pack_propagate(False)

        tk.Label(
            painel_contatos,
            text=f"Contatos | {self.usuario}"
        ).pack(anchor="w")

        cadastro = tk.Frame(painel_contatos)
        cadastro.pack(fill=tk.X, pady=8)
        self.novo_contato = tk.Entry(cadastro)
        self.novo_contato.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(
            cadastro,
            text="Adicionar",
            command=self.adicionar_contato
        ).pack(side=tk.RIGHT, padx=(5, 0))

        self.lista_contatos = tk.Listbox(painel_contatos, exportselection=False)
        self.lista_contatos.pack(fill=tk.BOTH, expand=True)
        self.lista_contatos.bind("<<ListboxSelect>>", self.selecionar_contato)

        painel_conversa = tk.Frame(principal)
        painel_conversa.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.titulo_conversa = tk.Label(
            painel_conversa,
            text="Selecione um contato"
        )
        self.titulo_conversa.pack(anchor="w")

        self.historico = tk.Text(
            painel_conversa,
            state=tk.DISABLED,
            wrap=tk.WORD
        )
        self.historico.pack(fill=tk.BOTH, expand=True, pady=8)

        self.status_digitacao = tk.Label(
            painel_conversa,
            text="",
            anchor="w"
        )
        self.status_digitacao.pack(fill=tk.X)

        envio = tk.Frame(painel_conversa)
        envio.pack(fill=tk.X, pady=(8, 0))
        self.mensagem = tk.Entry(envio)
        self.mensagem.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.mensagem.bind("<KeyRelease>", self.informar_digitacao)
        self.mensagem.bind("<Return>", self.enviar_mensagem)
        tk.Button(
            envio,
            text="Enviar",
            command=self.enviar_mensagem
        ).pack(side=tk.RIGHT, padx=(5, 0))

    def adicionar_contato(self):
        contato = self.novo_contato.get().strip()
        if not contato or contato == self.usuario:
            self.status_digitacao.config(text="Informe um contato válido.")
            return

        if contato in self.contatos:
            self.status_digitacao.config(text="Esse contato já foi adicionado.")
            return

        try:
            self.servico_sessao.adicionar_contato(contato)
            self.status_digitacao.config(text="Validando contato no servidor...")
        except Exception as erro:
            self.status_digitacao.config(text=f"Não foi possível adicionar: {erro}")
        self.novo_contato.delete(0, tk.END)

    def atualizar_lista_contatos(self):
        selecionado = self.contato_selecionado
        self.lista_contatos.delete(0, tk.END)

        for contato, online in sorted(self.contatos.items()):
            marcador = "online" if online else "offline"
            self.lista_contatos.insert(tk.END, f"{contato} ({marcador})")

        if selecionado in self.contatos:
            indice = list(sorted(self.contatos)).index(selecionado)
            self.lista_contatos.selection_set(indice)

    def selecionar_contato(self, _evento=None):
        selecao = self.lista_contatos.curselection()
        if not selecao:
            return

        self.contato_selecionado = list(sorted(self.contatos))[selecao[0]]
        online = self.contatos[self.contato_selecionado]
        estado = "online" if online else "offline"
        self.titulo_conversa.config(
            text=f"{self.contato_selecionado} - {estado}"
        )
        self.exibir_conversa()

    def exibir_conversa(self):
        self.historico.config(state=tk.NORMAL)
        self.historico.delete("1.0", tk.END)
        for mensagem in self.conversas.get(self.contato_selecionado, []):
            self.historico.insert(tk.END, f"{mensagem}\n")
        self.historico.config(state=tk.DISABLED)
        self.historico.see(tk.END)

    def enviar_mensagem(self, _evento=None):
        if not self.contato_selecionado:
            return "break"

        texto = self.mensagem.get().strip()
        if not texto:
            return "break"

        evento = {
            "evento": "mensagem",
            "destinatario": self.contato_selecionado,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "texto": texto,
        }
        self.servico_sessao.enviar_evento(evento)
        self.conversas.setdefault(self.contato_selecionado, []).append(
            f"Você: {texto}"
        )
        self.mensagem.delete(0, tk.END)
        self.exibir_conversa()
        self.enviar_fim_digitacao()
        return "break"

    def informar_digitacao(self, _evento=None):
        if self.contato_selecionado and self.mensagem.get():
            if not self.digitando_enviado:
                self.servico_sessao.enviar_evento({
                    "evento": "digitando_inicio",
                    "destinatario": self.contato_selecionado,
                })
                self.digitando_enviado = True
        elif self.digitando_enviado:
            self.enviar_fim_digitacao()

    def enviar_fim_digitacao(self):
        if self.contato_selecionado and self.digitando_enviado:
            self.servico_sessao.enviar_evento({
                "evento": "digitando_fim",
                "destinatario": self.contato_selecionado,
            })
        self.digitando_enviado = False

    def processar_evento(self, evento):
        if not self.ativa or not self.janela.winfo_exists():
            return
        self.janela.after(0, self._processar_evento, evento)

    def _processar_evento(self, evento):
        if not self.ativa or not self.janela.winfo_exists():
            return
        tipo = evento.get("evento")

        if tipo == "lista_contatos":
            for contato in evento.get("contatos", []):
                nome = contato.get("usuario")
                if nome and nome != self.usuario:
                    self.contatos[nome] = contato.get("online", False)
                    self.conversas.setdefault(nome, [])
            self.atualizar_lista_contatos()
        elif tipo == "resposta_adicionar_contato":
            contato = evento.get("contato")
            if evento.get("sucesso"):
                self.contatos[contato] = evento.get("online", False)
                self.conversas.setdefault(contato, [])
                self.atualizar_lista_contatos()
                self.status_digitacao.config(
                    text=evento.get("mensagem", "Contato adicionado.")
                )
            else:
                self.status_digitacao.config(
                    text=evento.get("mensagem", "Contato não encontrado no servidor.")
                )
        elif tipo == "presenca":
            usuario = evento.get("usuario")
            if usuario in self.contatos:
                self.contatos[usuario] = evento.get("online", False)
                self.atualizar_lista_contatos()
        elif tipo == "mensagem":
            remetente = evento.get("remetente")
            texto = evento.get("texto", "")
            self.contatos.setdefault(remetente, True)
            self.conversas.setdefault(remetente, []).append(
                f"{remetente}: {texto}"
            )
            self.atualizar_lista_contatos()
            if remetente == self.contato_selecionado:
                self.exibir_conversa()
        elif tipo == "fila_offline":
            for mensagem in evento.get("mensagens", []):
                self._processar_evento(mensagem)
        elif tipo == "aviso_digitando":
            if evento.get("remetente") == self.contato_selecionado:
                texto = "está digitando..." if evento.get("digitando") else ""
                self.status_digitacao.config(text=texto)

    def fechar(self):
        self.ativa = False
        self.servico_sessao.fechar()
        self.janela.destroy()