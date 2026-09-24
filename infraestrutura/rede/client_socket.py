import socket

from infraestrutura.rede.protocolo import serializar
from infraestrutura.rede.sessao_canal import SessaoCanal


class ClienteSocket:

    def __init__(self, host="127.0.0.1", porta=8000):
        self.host = host
        self.porta = porta
        self.socket = None
        self.arquivo = None
        self.sessao_segura = SessaoCanal()
        self.conectado = False

    def conectar(self):
        if self.conectado:
            return

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((self.host, self.porta))
            self.arquivo = self.socket.makefile("rwb")
            self.sessao_segura.iniciar_cliente(self.arquivo)
        except Exception:
            if self.arquivo:
                self.arquivo.close()
            self.socket.close()
            self.socket = None
            self.arquivo = None
            raise

        self.conectado = True

    def enviar(self, evento):
        if not self.conectado:
            raise ConnectionError("Cliente não está conectado.")
        try:
            self.sessao_segura.enviar(self.arquivo, serializar(evento))
        except OSError as erro:
            self.conectado = False
            raise ConnectionError("Não foi possível enviar a mensagem.") from erro

    def receber(self):
        if not self.conectado:
            raise ConnectionError("Cliente não está conectado.")

        try:
            return self.sessao_segura.receber(self.arquivo)
        except (ConnectionError, OSError):
            self.conectado = False
            raise

    def fechar(self):
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            finally:
                if self.arquivo:
                    self.arquivo.close()
                self.socket.close()

        self.socket = None
        self.arquivo = None
        self.conectado = False