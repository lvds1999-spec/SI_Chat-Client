import threading

from ClientProtocol.Rede.Protocolo.protocolo import desserializar


class ThreadRecepcao(threading.Thread):

    def __init__(self, cliente_socket, callback):
        super().__init__(daemon=True)

        self.cliente_socket = cliente_socket
        self.callback = callback

        self.executando = True

    def run(self):
        """Fica ouvindo o servidor enquanto o cliente estiver conectado."""

        while self.executando:

            try:
                dados = self.cliente_socket.receber()

                evento = desserializar(dados)

                self.callback(evento)

            except ConnectionError as erro:
                print(f"Conexão encerrada: {erro}")
                self.executando = False

            except Exception as erro:
                print(f"Erro na recepção: {erro}")

                self.executando = False

    def parar(self):
        """Solicita a parada da thread."""

        self.executando = False