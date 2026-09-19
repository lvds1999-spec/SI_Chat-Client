import threading

from infraestrutura.rede.protocolo import desserializar


class ThreadRecepcao(threading.Thread):

    def __init__(self, cliente_socket, callback):
        super().__init__(daemon=True)
        self.cliente_socket = cliente_socket
        self.callback = callback
        self.executando = True

    def run(self):
        while self.executando:
            try:
                self.callback(desserializar(self.cliente_socket.receber()))
            except ConnectionError:
                self.executando = False
            except Exception as erro:
                print(f"Erro na recepção: {erro}")
                self.executando = False

    def parar(self):
        self.executando = False