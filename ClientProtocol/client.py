import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from apresentacao.tela_login import TelaLogin
from dominio.servico_sessao import ServicoSessao


def main():

    servico_sessao = ServicoSessao(
        host="127.0.0.1",
        porta=8000
    )

    gui = TelaLogin(servico_sessao)
    servico_sessao.conectar(gui.processar_evento)

    try:
        gui.iniciar()
    finally:
        servico_sessao.fechar()


if __name__ == "__main__":
    main()