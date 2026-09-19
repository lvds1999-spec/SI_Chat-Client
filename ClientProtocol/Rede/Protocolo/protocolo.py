import json


REGISTRO = "registro"
RESPOSTA_REGISTRO = "resposta_registro"

LOGIN = "login"
RESPOSTA_LOGIN = "resposta_login"

LISTA_CONTATOS = "lista_contatos"

MENSAGEM = "mensagem"
ENTREGA_MENSAGEM = "entrega_mensagem"

DIGITANDO_INICIO = "digitando_inicio"
DIGITANDO_FIM = "digitando_fim"
AVISO_DIGITANDO = "aviso_digitando"

PRESENCA = "presenca"

FILA_OFFLINE = "fila_offline"


def serializar(evento):
    """
    Converte um dicionário Python para JSON.

    Cada evento termina com \\n para que o receptor
    saiba onde termina uma mensagem.
    """

    texto = json.dumps(
        evento,
        ensure_ascii=False
    )

    return (texto + "\n").encode("utf-8")


def desserializar(linha):
    """
    Converte uma mensagem JSON recebida
    para um dicionário Python.
    """

    return json.loads(linha.decode("utf-8"))