import tkinter as tk
from tkinter import messagebox

from apresentacao.tela_contatos import TelaContatos
from apresentacao.tela_conversa import TelaConversa
from dominio.servico_conversas import ServicoConversas
from infraestrutura.dados.banco_local import BancoLocal
from infraestrutura.rede.protocolo import (
    DIGITANDO_FIM,
    DIGITANDO_INICIO,
    LISTA_CONTATOS,
    MENSAGEM,
    MUDANCA_PRESENCA,
    PRESENCA,
    RESPOSTA_ADICIONAR_CONTATO,
    RESPOSTA_LOGOUT,
    RESPOSTA_REMOVER_CONTATO,
)


class TelaPrincipal:

    def __init__(self, servico_sessao, usuario, janela, ao_sair, senha=None):
        self.servico_sessao = servico_sessao
        self.usuario = usuario
        self.janela = janela
        self.ao_sair = ao_sair
        self.ativa = True
        self.digitando_enviado = False
        self.contato_selecionado = None
        self.contatos = {}
        self.deslogando = False
        self.banco_local = BancoLocal(usuario, senha=senha)

        self.janela.title(f"Chat - {usuario}")
        self.janela.geometry("760x500")
        self.janela.protocol("WM_DELETE_WINDOW", self.fechar)
        self.criar_interface()

    def criar_interface(self):
        for widget in self.janela.winfo_children():
            widget.destroy()

        principal = tk.Frame(self.janela)
        principal.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        coluna = tk.Frame(principal, width=220)
        coluna.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))
        coluna.pack_propagate(False)

        cadastro = tk.Frame(coluna)
        cadastro.pack(fill=tk.X, pady=(0, 8))
        self.novo_contato = tk.Entry(cadastro)
        self.novo_contato.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Button(cadastro, text="Adicionar", command=self.adicionar_contato).pack(
            side=tk.RIGHT, padx=(5, 0)
        )

        self.tela_contatos = TelaContatos(
            coluna,
            self.usuario,
            self.selecionar_contato
        )
        self.tela_contatos.pack(fill=tk.BOTH, expand=True)
        self._recarregar_contatos()
        tk.Button(
            coluna,
            text="Excluir selecionado",
            command=self.remover_contato
        ).pack(fill=tk.X, pady=(8, 0))
        tk.Button(
            coluna,
            text="Sair da conta",
            command=self.sair
        ).pack(fill=tk.X, pady=(8, 0))

        self.servico_conversas = ServicoConversas(
            self.servico_sessao, self.usuario, self.banco_local
        )
        self.tela_conversa = TelaConversa(
            principal,
            self.servico_conversas,
            self.usuario,
            self.banco_local,
            self.informar_digitacao
        )
        self.tela_conversa.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def adicionar_contato(self):
        contato = self.novo_contato.get().strip()
        if not contato or contato == self.usuario:
            self.tela_conversa.definir_status("Informe um contato válido.")
            return
        if contato in self.tela_contatos.contatos:
            self.tela_conversa.definir_status("Esse contato já foi adicionado.")
            return
        self.servico_sessao.adicionar_contato(contato)
        self.tela_conversa.definir_status("Validando contato no servidor...")
        self.novo_contato.delete(0, tk.END)

    def remover_contato(self):
        contato = self.contato_selecionado
        if not contato:
            self.tela_conversa.definir_status("Selecione um contato para excluir.")
            return
        if messagebox.askyesno("Excluir contato", f"Deseja excluir {contato}?"):
            self.servico_sessao.remover_contato(contato)
            self.tela_conversa.definir_status("Excluindo contato...")

    def selecionar_contato(self, contato, online):
        self.contato_selecionado = contato
        self.tela_conversa.selecionar(contato, online)

    def _recarregar_contatos(self):
        self.tela_contatos.atualizar(self.banco_local.listar_contatos())

    def informar_digitacao(self, digitando, destinatario):
        if digitando and not self.digitando_enviado:
            self.servico_sessao.enviar_evento({
                "evento": DIGITANDO_INICIO,
                "destinatario": destinatario
            })
            self.digitando_enviado = True
        elif not digitando and self.digitando_enviado:
            self.servico_sessao.enviar_evento({
                "evento": DIGITANDO_FIM,
                "destinatario": destinatario
            })
            self.digitando_enviado = False

    def processar_evento(self, evento):
        if not self.ativa or not self.janela.winfo_exists():
            return
        self.janela.after(0, self._processar_evento, evento)

    def _processar_evento(self, evento):
        if not self.ativa:
            return
        tipo = evento.get("evento")

        if tipo in ("erro_conexao", "estado_conexao", "erro"):
            if tipo == "estado_conexao" and evento.get("estado") == "reconectando":
                mensagem = "Desconectado. Tentando reconectar..."
            elif tipo == "estado_conexao" and evento.get("estado") == "conectado":
                mensagem = "Conectado ao servidor."
            else:
                mensagem = evento.get("mensagem", "Desconectado do servidor.")
            self.tela_conversa.definir_status(mensagem)
        elif tipo == LISTA_CONTATOS:
            self.banco_local.upsert_contatos(evento.get("contatos", []))
            self._recarregar_contatos()
        elif tipo in (PRESENCA, MUDANCA_PRESENCA, "mudanca_presenca"):
            usuario = evento.get("usuario", evento.get("nome"))
            online = evento.get("online", False)
            self.banco_local.atualizar_presenca(
                usuario, online
            )
            self.tela_contatos.atualizar_presenca(
                usuario,
                online
            )
            self.tela_conversa.atualizar_presenca(usuario, online)
        elif tipo == RESPOSTA_ADICIONAR_CONTATO:
            if evento.get("sucesso"):
                contato = evento.get("contato") or evento.get("usuario")
                if isinstance(contato, dict):
                    self.banco_local.adicionar_contato(contato)
                    contato = contato.get("usuario", contato.get("nome"))
                else:
                    self.banco_local.adicionar_contato(contato)
                self._recarregar_contatos()
            self.tela_conversa.definir_status(evento.get("mensagem", ""))
        elif tipo == RESPOSTA_REMOVER_CONTATO:
            if evento.get("sucesso"):
                contato = evento.get("contato") or evento.get("usuario")
                if isinstance(contato, dict):
                    contato = contato.get("usuario", contato.get("nome"))
                self.banco_local.remover_contato(contato)
                self._recarregar_contatos()
                if self.contato_selecionado == contato:
                    self.contato_selecionado = None
            self.tela_conversa.definir_status(evento.get("mensagem", ""))
        elif tipo == RESPOSTA_LOGOUT:
            self.concluir_logout()
        elif tipo == MENSAGEM:
            remetente = evento.get("remetente")
            self.banco_local.adicionar_contato({"usuario": remetente, "online": True})
            self._recarregar_contatos()
            self.tela_conversa.adicionar_mensagem(evento, recebida=True)
            if self.contato_selecionado != remetente:
                self.tela_conversa.definir_status(
                    f"Nova mensagem de {remetente}."
                )
        elif tipo == DIGITANDO_INICIO:
            self.tela_conversa.exibir_digitando(evento.get("remetente"))
        elif tipo == DIGITANDO_FIM:
            self.tela_conversa.remover_digitando(evento.get("remetente"))
        elif tipo == "aviso_digitando":
            remetente = evento.get("remetente")
            if evento.get("digitando"):
                self.tela_conversa.exibir_digitando(remetente)
            else:
                self.tela_conversa.remover_digitando(remetente)

    def fechar(self):
        self.ativa = False
        self.servico_sessao.fechar()
        self.banco_local.fechar()
        self.janela.destroy()

    def sair(self):
        if self.deslogando:
            return
        self.deslogando = True
        self.tela_conversa.definir_status("Encerrando sessão...")
        self.servico_sessao.logout()

    def concluir_logout(self):
        self.ativa = False
        self.servico_sessao.concluir_logout()
        self.banco_local.fechar()
        self.ao_sair()
