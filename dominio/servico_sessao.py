import base64
import threading
import time

from infraestrutura.rede.client_socket import ClienteSocket
from infraestrutura.rede.thread_recepcao import ThreadRecepcao
from infraestrutura.seguranca.identidade import IdentidadeUsuario
from infraestrutura.rede.protocolo import (
    DESAFIO_LOGIN,
    LOGIN,
    REGISTRO,
    RESPOSTA_LOGIN,
    RESPOSTA_REGISTRO,
    criar_login,
    criar_login_assinatura,
    criar_registro,
    criar_adicionar_contato,
    criar_remover_contato,
    criar_logout,
)


class ServicoSessao:

    def __init__(self, host="127.0.0.1", porta=8000):
        self.cliente_socket = ClienteSocket(host, porta)
        self.thread_recepcao = None
        self.callback = None
        self.identidade = None
        self._credenciais = None
        self._fechando = False
        self._reconexao_em_andamento = False

    def conectar(self, callback):
        self.callback = callback
        self._fechando = False
        try:
            self.cliente_socket.conectar()
        except (ConnectionError, OSError) as erro:
            self._notificar({
                "evento": "erro_conexao",
                "mensagem": str(erro),
            })
            self._iniciar_reconexao()
            return

        self._iniciar_thread_recepcao()
        self._notificar({
            "evento": "estado_conexao",
            "estado": "conectado",
        })

    def _iniciar_thread_recepcao(self):
        self.thread_recepcao = ThreadRecepcao(
            self.cliente_socket,
            self._processar_evento,
            self._tratar_queda,
        )
        self.thread_recepcao.start()

    def registrar(self, usuario, senha):
        self.identidade = IdentidadeUsuario(usuario)
        self._credenciais = (REGISTRO, usuario, senha)
        self._enviar_autenticacao(criar_registro(
            usuario,
            senha,
            self.identidade.algoritmo,
            self.identidade.chave_publica,
        ))

    def login(self, usuario, senha):
        self.identidade = IdentidadeUsuario(usuario)
        self._credenciais = (LOGIN, usuario, senha)
        self._enviar_autenticacao(criar_login(
            usuario,
            senha,
            self.identidade.algoritmo,
            self.identidade.chave_publica,
        ))

    def adicionar_contato(self, contato):
        self.cliente_socket.enviar(criar_adicionar_contato(contato))

    def remover_contato(self, contato):
        self.cliente_socket.enviar(criar_remover_contato(contato))

    def logout(self):
        if self.cliente_socket.conectado:
            self.cliente_socket.enviar(criar_logout())

    def concluir_logout(self):
        self.fechar()

    def definir_callback(self, callback):
        self.callback = callback
        if self.thread_recepcao:
            self.thread_recepcao.definir_callback(self._processar_evento)

    def enviar_evento(self, evento):
        self.cliente_socket.enviar(evento)

    def fechar(self):
        self._fechando = True
        if self.thread_recepcao:
            self.thread_recepcao.parar()
        self.cliente_socket.fechar()

    def _enviar_autenticacao(self, evento):
        try:
            self.cliente_socket.enviar(evento)
        except (ConnectionError, OSError):
            self._tratar_queda(ConnectionError("Não foi possível enviar a autenticação."))
            raise

    def _tratar_queda(self, erro):
        if self._fechando:
            return
        self._notificar({
            "evento": "estado_conexao",
            "estado": "desconectado",
        })
        self._notificar({
            "evento": "erro_conexao",
            "mensagem": str(erro),
        })
        self._iniciar_reconexao()

    def _iniciar_reconexao(self):
        if self._fechando or self._reconexao_em_andamento:
            return
        self._reconexao_em_andamento = True
        threading.Thread(target=self._reconectar, daemon=True).start()

    def _reconectar(self):
        reconectado = False
        try:
            for espera in (1, 2, 4):
                if self._fechando:
                    return
                self._notificar({
                    "evento": "estado_conexao",
                    "estado": "reconectando",
                    "tentativa_em": espera,
                })
                time.sleep(espera)
                try:
                    self.cliente_socket.conectar()
                    self._iniciar_thread_recepcao()
                    self._notificar({
                        "evento": "estado_conexao",
                        "estado": "conectado",
                    })
                    reconectado = True
                    self._reenviar_autenticacao()
                    return
                except (ConnectionError, OSError):
                    self.cliente_socket.fechar()
        finally:
            self._reconexao_em_andamento = False
            if not reconectado and not self._fechando:
                self._notificar({
                    "evento": "estado_conexao",
                    "estado": "desconectado",
                })

    def _reenviar_autenticacao(self):
        if not self._credenciais:
            return
        tipo, usuario, senha = self._credenciais
        if not self.identidade:
            self.identidade = IdentidadeUsuario(usuario)
        if tipo == LOGIN:
            evento = criar_login(
                usuario,
                senha,
                self.identidade.algoritmo,
                self.identidade.chave_publica,
            )
        else:
            evento = criar_registro(
                usuario,
                senha,
                self.identidade.algoritmo,
                self.identidade.chave_publica,
            )
        self.cliente_socket.enviar(evento)

    def _notificar(self, evento):
        if self.callback:
            self.callback(evento)

    def _processar_evento(self, evento):
        if evento.get("evento") == DESAFIO_LOGIN:
            try:
                if not self.identidade:
                    raise ValueError("Identidade de login não encontrada.")
                if evento.get("algoritmo_assinatura") != self.identidade.algoritmo:
                    raise ValueError("Algoritmo de assinatura inesperado.")
                nonce = base64.b64decode(
                    evento["nonce"].encode("ascii"),
                    validate=True,
                )
                assinatura = self.identidade.assinar_nonce(nonce)
                self.cliente_socket.enviar(criar_login_assinatura(assinatura))
            except (KeyError, ValueError, TypeError) as erro:
                self.callback({
                    "evento": RESPOSTA_LOGIN,
                    "sucesso": False,
                    "mensagem": f"Desafio de login inválido: {erro}",
                })
            return

        self.callback(evento)