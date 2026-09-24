import base64

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

    def conectar(self, callback):
        self.callback = callback
        self.cliente_socket.conectar()
        self.thread_recepcao = ThreadRecepcao(
            self.cliente_socket,
            self._processar_evento,
            lambda erro: self.callback({
                "evento": "erro_conexao",
                "mensagem": str(erro)
            })
        )
        self.thread_recepcao.start()

    def registrar(self, usuario, senha):
        self.identidade = IdentidadeUsuario(usuario)
        self.cliente_socket.enviar(criar_registro(
            usuario,
            senha,
            self.identidade.algoritmo,
            self.identidade.chave_publica,
        ))

    def login(self, usuario, senha):
        self.identidade = IdentidadeUsuario(usuario)
        self.cliente_socket.enviar(criar_login(
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
        if self.thread_recepcao:
            self.thread_recepcao.parar()
        self.cliente_socket.fechar()

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