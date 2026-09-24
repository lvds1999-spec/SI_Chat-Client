import base64
import hashlib
import hmac
import json
import os
import struct
import threading

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


VERSAO = 1
TAMANHO_MAXIMO_ENVELOPE = 2 * 1024 * 1024


class ErroSeguranca(Exception):
    pass


def _b64(dados):
    return base64.b64encode(dados).decode("ascii")


def _de_b64(valor):
    if not isinstance(valor, str):
        raise ErroSeguranca("Campo binario ausente no envelope.")
    try:
        return base64.b64decode(valor.encode("ascii"), validate=True)
    except (ValueError, UnicodeEncodeError) as erro:
        raise ErroSeguranca("Campo binario invalido no envelope.") from erro


def _escrever_linha(arquivo, objeto):
    dados = (json.dumps(objeto, separators=(",", ":")) + "\n").encode("utf-8")
    arquivo.write(dados)
    arquivo.flush()


def _ler_linha(arquivo):
    linha = arquivo.readline()
    if not linha:
        raise ConnectionError("Conexao encerrada durante o handshake.")
    if len(linha) > TAMANHO_MAXIMO_ENVELOPE:
        raise ErroSeguranca("Mensagem maior que o limite permitido.")
    try:
        objeto = json.loads(linha.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as erro:
        raise ErroSeguranca("Mensagem de transporte malformada.") from erro
    if not isinstance(objeto, dict):
        raise ErroSeguranca("Mensagem de transporte invalida.")
    return objeto


class SessaoSegura:

    def __init__(self):
        self._chaves = None
        self._sequencia_envio = 0
        self._sequencia_recebimento = 0
        self._lock = threading.RLock()

    def iniciar_cliente(self, arquivo):
        convite = _ler_linha(arquivo)
        self._validar_tipo(convite, "handshake_servidor")

        privada = X25519PrivateKey.generate()
        nonce_cliente = os.urandom(16)
        publica = privada.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        _escrever_linha(arquivo, {
            "evento": "handshake_cliente",
            "versao": VERSAO,
            "chave_publica": _b64(publica),
            "nonce": _b64(nonce_cliente),
        })

        publica_servidor = _de_b64(convite.get("chave_publica"))
        nonce_servidor = _de_b64(convite.get("nonce"))
        if len(publica_servidor) != 32:
            raise ErroSeguranca("Chave publica DHE invalida.")
        if len(nonce_servidor) != 16 or len(nonce_cliente) != 16:
            raise ErroSeguranca("Nonce de handshake invalido.")

        self._estabelecer(
            privada,
            publica_servidor,
            nonce_servidor,
            nonce_cliente,
        )

    def enviar(self, arquivo, dados):
        with self._lock:
            self._exigir_estabelecida()
            _escrever_linha(arquivo, self._criar_envelope(dados))

    def receber(self, arquivo):
        self._exigir_estabelecida()
        while True:
            envelope = _ler_linha(arquivo)
            with self._lock:
                dados = self._abrir_envelope(envelope)
            evento = json.loads(dados.decode("utf-8"))
            if not isinstance(evento, dict):
                raise ErroSeguranca("Evento cifrado invalido.")
            if evento.get("evento") == "renovacao_servidor":
                self._responder_renovacao(arquivo, evento)
                continue
            return dados

    def _criar_envelope(self, dados):
        nonce = os.urandom(16)
        sequencia = self._sequencia_envio
        cifrado = Cipher(
            algorithms.AES(self._chaves["cliente_cifra"]),
            modes.CTR(nonce),
        ).encryptor().update(dados)
        autenticado = struct.pack(">Q", sequencia) + nonce + cifrado
        tag = hmac.digest(self._chaves["cliente_mac"], autenticado, "sha256")
        self._sequencia_envio += 1
        return {
            "evento": "envelope_seguro",
            "versao": VERSAO,
            "sequencia": sequencia,
            "nonce": _b64(nonce),
            "dados": _b64(cifrado),
            "tag": _b64(tag),
        }

    def _abrir_envelope(self, envelope):
        self._validar_tipo(envelope, "envelope_seguro")
        sequencia = envelope.get("sequencia")
        if sequencia != self._sequencia_recebimento:
            raise ErroSeguranca("Sequencia de transporte invalida.")
        nonce = _de_b64(envelope.get("nonce"))
        cifrado = _de_b64(envelope.get("dados"))
        tag = _de_b64(envelope.get("tag"))
        autenticado = struct.pack(">Q", sequencia) + nonce + cifrado
        esperado = hmac.digest(
            self._chaves["servidor_mac"], autenticado, "sha256"
        )
        if not hmac.compare_digest(esperado, tag):
            raise ErroSeguranca("Autenticacao do envelope falhou.")
        dados = Cipher(
            algorithms.AES(self._chaves["servidor_cifra"]),
            modes.CTR(nonce),
        ).decryptor().update(cifrado)
        self._sequencia_recebimento += 1
        return dados

    def _responder_renovacao(self, arquivo, controle):
        self._validar_tipo(controle, "renovacao_servidor")
        privada = X25519PrivateKey.generate()
        nonce_cliente = os.urandom(16)
        publica = privada.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        self.enviar(arquivo, json.dumps({
            "evento": "renovacao_cliente",
            "versao": VERSAO,
            "chave_publica": _b64(publica),
            "nonce": _b64(nonce_cliente),
        }, separators=(",", ":")).encode("utf-8"))
        self._estabelecer(
            privada,
            _de_b64(controle.get("chave_publica")),
            _de_b64(controle.get("nonce")),
            nonce_cliente,
        )

    def _estabelecer(
        self,
        privada,
        publica_servidor,
        nonce_servidor,
        nonce_cliente,
    ):
        if len(publica_servidor) != 32:
            raise ErroSeguranca("Chave publica DHE invalida.")
        if len(nonce_servidor) != 16 or len(nonce_cliente) != 16:
            raise ErroSeguranca("Nonce de handshake invalido.")
        segredo = privada.exchange(
            X25519PublicKey.from_public_bytes(publica_servidor)
        )
        salt = hashlib.sha256(nonce_servidor + nonce_cliente).digest()
        material = HKDF(
            algorithm=hashes.SHA256(),
            length=128,
            salt=salt,
            info=b"SI_Chat-Server transporte seguro v1",
        ).derive(segredo)
        self._chaves = {
            "servidor_cifra": material[0:32],
            "servidor_mac": material[32:64],
            "cliente_cifra": material[64:96],
            "cliente_mac": material[96:128],
        }
        self._sequencia_envio = 0
        self._sequencia_recebimento = 0

    def _exigir_estabelecida(self):
        if self._chaves is None:
            raise ErroSeguranca("Handshake ainda nao foi concluido.")

    @staticmethod
    def _validar_tipo(objeto, tipo):
        if objeto.get("evento") != tipo or objeto.get("versao") != VERSAO:
            raise ErroSeguranca("Mensagem de handshake invalida.")