from infraestrutura.rede.client_socket import ClienteSocket
from infraestrutura.rede.thread_recepcao import ThreadRecepcao
from infraestrutura.rede.protocolo import (
    LOGIN,
    REGISTRO,
    RESPOSTA_LOGIN,
    RESPOSTA_REGISTRO,
    criar_login,
    criar_registro,
    criar_adicionar_contato,
)


class ServicoSessao:

    def __init__(self, host="127.0.0.1", porta=8000):
        self.cliente_socket = ClienteSocket(host, porta)
        self.thread_recepcao = None

    def conectar(self, callback):
        self.cliente_socket.conectar()
        self.thread_recepcao = ThreadRecepcao(self.cliente_socket, callback)
        self.thread_recepcao.start()

    def registrar(self, usuario, senha):
        self.cliente_socket.enviar(criar_registro(usuario, senha))

    def login(self, usuario, senha):
        self.cliente_socket.enviar(criar_login(usuario, senha))

    def adicionar_contato(self, contato):
        self.cliente_socket.enviar(criar_adicionar_contato(contato))

    def definir_callback(self, callback):
        if self.thread_recepcao:
            self.thread_recepcao.definir_callback(callback)

    def enviar_evento(self, evento):
        self.cliente_socket.enviar(evento)

    def fechar(self):
        if self.thread_recepcao:
            self.thread_recepcao.parar()
        self.cliente_socket.fechar()