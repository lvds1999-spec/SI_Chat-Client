import socket

from infraestrutura.rede.protocolo import serializar


class ClienteSocket:

    def __init__(self, host="127.0.0.1", porta=8000):
        self.host = host
        self.porta = porta
        self.socket = None
        self.conectado = False
        self._buffer_recebimento = b""

    def conectar(self):
        if self.conectado:
            return

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((self.host, self.porta))
        except Exception:
            self.socket.close()
            self.socket = None
            raise

        self._buffer_recebimento = b""
        self.conectado = True

    def enviar(self, evento):
        if not self.conectado:
            raise ConnectionError("Cliente não está conectado.")
        self.socket.sendall(serializar(evento))

    def receber(self):
        if not self.conectado:
            raise ConnectionError("Cliente não está conectado.")

        while b"\n" not in self._buffer_recebimento:
            dados = self.socket.recv(4096)
            if not dados:
                self.conectado = False
                raise ConnectionError("Servidor encerrou a conexão.")
            self._buffer_recebimento += dados

        linha, self._buffer_recebimento = self._buffer_recebimento.split(b"\n", 1)
        return linha + b"\n"

    def fechar(self):
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            finally:
                self.socket.close()

        self.socket = None
        self.conectado = False
        self._buffer_recebimento = b""