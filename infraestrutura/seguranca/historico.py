import hashlib

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


ITERACOES = 600_000


def derivar_chave_historico(senha, salt):
    if not isinstance(senha, str) or not senha:
        raise ValueError("A senha é necessária para abrir o histórico local.")
    return PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERACOES,
    ).derive(senha.encode("utf-8"))


def fingerprint_mensagem(chave, remetente, destinatario, timestamp, texto):
    dados = "\x00".join((remetente, destinatario, timestamp, texto)).encode("utf-8")
    return hashlib.pbkdf2_hmac("sha256", dados, chave, 1)