import tkinter as tk


class TelaContatos(tk.Frame):

    def __init__(self, parent, usuario, ao_selecionar):
        super().__init__(parent, width=220)
        self.usuario = usuario
        self.ao_selecionar = ao_selecionar
        self.contatos = {}
        self.contato_selecionado = None
        self.pack_propagate(False)

        tk.Label(self, text=f"Contatos | {usuario}").pack(anchor="w")
        self.lista = tk.Listbox(self, exportselection=False)
        self.lista.pack(fill=tk.BOTH, expand=True, pady=(8, 0))
        self.lista.bind("<<ListboxSelect>>", self._selecionar)

    def atualizar(self, contatos):
        contatos_atualizados = {}
        for contato in contatos:
            if isinstance(contato, dict):
                usuario = contato.get("usuario", contato.get("nome"))
                online = contato.get("online", False)
            else:
                usuario = str(contato).strip()
                online = False
            if usuario and usuario != self.usuario:
                contatos_atualizados[usuario] = bool(online)
        self.contatos = contatos_atualizados
        if self.contato_selecionado not in self.contatos:
            self.contato_selecionado = None
        self._renderizar()

    def atualizar_presenca(self, usuario, online):
        if usuario in self.contatos:
            self.contatos[usuario] = online
            self._renderizar()

    def adicionar(self, usuario, online=False):
        if usuario and usuario != self.usuario:
            self.contatos[usuario] = online
            self._renderizar()

    def remover(self, usuario):
        self.contatos.pop(usuario, None)
        if self.contato_selecionado == usuario:
            self.contato_selecionado = None
        self._renderizar()

    def _renderizar(self):
        selecionado = self.contato_selecionado
        nomes = sorted(self.contatos)
        self.lista.delete(0, tk.END)
        for nome in nomes:
            estado = "online" if self.contatos[nome] else "offline"
            self.lista.insert(tk.END, f"{nome} ({estado})")
        if selecionado in nomes:
            self.lista.selection_set(nomes.index(selecionado))

    def _selecionar(self, _evento=None):
        selecao = self.lista.curselection()
        if not selecao:
            return
        nomes = sorted(self.contatos)
        self.contato_selecionado = nomes[selecao[0]]
        self.ao_selecionar(
            self.contato_selecionado,
            self.contatos[self.contato_selecionado]
        )
