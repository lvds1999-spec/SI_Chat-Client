import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ClientProtocol.Rede.client_socket import ClienteSocket
from ClientProtocol.Rede.thread_recepcao import ThreadRecepcao
from ClientProtocol.Interface.gui import GUI


def main():

    cliente_socket = ClienteSocket(
        host="127.0.0.1",
        porta=8000
    )

    cliente_socket.conectar()

    gui = GUI(cliente_socket)
    thread_recepcao = ThreadRecepcao(
        cliente_socket,
        gui.processar_evento
    )
    thread_recepcao.start()

    try:
        gui.iniciar()
    finally:
        thread_recepcao.parar()
        cliente_socket.fechar()


if __name__ == "__main__":
    main()