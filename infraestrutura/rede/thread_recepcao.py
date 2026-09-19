import threading

from infraestrutura.rede.protocolo import desserializar


class ThreadRecepcao(threading.Thread):

    def __init__(self, cliente_socket, callback):
        super().__init__(daemon=True)
        self.cliente_socket = cliente_socket
        self.callback = callback
        self._parar_evento = threading.Event()

    def run(self):
        while not self._parar_evento.is_set():
            try:
                evento = desserializar(self.cliente_socket.receber())
            except ConnectionError:
                break
            except Exception as erro:
                print(f"Erro na recepção: {erro}")
                continue

            try:
                self.callback(evento)
            except Exception as erro:
                print(f"Erro no processamento do evento: {erro}")

    def parar(self):
        self._parar_evento.set()