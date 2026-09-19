import socket

from ClientProtocol.Rede.Protocolo.protocolo import serializar


class ClienteSocket:

    def __init__(self, host="127.0.0.1", porta=8000):
        self.host = host
        self.porta = porta

        self.socket = None
        self.conectado = False
        self._buffer_recebimento = b""

    def conectar(self):
        """Conecta o cliente ao servidor."""

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.socket.connect((self.host, self.porta))

        self.conectado = True
        self._buffer_recebimento = b""

        print("Conectado ao servidor.")

    def enviar(self, evento):
        """Envia um evento para o servidor."""

        if not self.conectado:
            raise ConnectionError("Cliente não está conectado.")

        dados = serializar(evento)

        self.socket.sendall(dados)

    def receber(self):
        """
        Recebe dados do servidor.

        Essa função será utilizada pela thread de recepção.
        """

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
        """Fecha a conexão com o servidor."""

        if self.socket:
            self.socket.close()

        self.conectado = False
        self._buffer_recebimento = b""

        print("Conexão encerrada.")