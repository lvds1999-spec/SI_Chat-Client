import base64
import hashlib
import json
import os
import threading

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


VERSAO = 1
TIPO_HANDSHAKE = "handshake_contato"
TIPO_MENSAGEM = "mensagem_cifrada"


def _b64(dados):
    return base64.b64encode(dados).decode("ascii")


def _de_b64(valor):
    if not isinstance(valor, str):
        raise ValueError("Campo binário ausente no pacote E2E.")
    return base64.b64decode(valor.encode("ascii"), validate=True)


def _chave_publica_bytes(chave_publica):
    return _de_b64(chave_publica)


def _assinar(identidade, dados):
    return identidade.chave.sign(dados)


def _verificar(chave_publica, assinatura, dados):
    from cryptography.hazmat.primitives.asymmetric import ed25519

    chave = ed25519.Ed25519PublicKey.from_public_bytes(
        _chave_publica_bytes(chave_publica)
    )
    chave.verify(_de_b64(assinatura), dados)


class SessaoContato:
    """Sessão E2E independente do canal seguro com o servidor."""

    def __init__(self, usuario, contato, identidade, chave_publica_contato):
        self.usuario = usuario
        self.contato = contato
        self.identidade = identidade
        self.chave_publica_contato = chave_publica_contato
        self._privada = None
        self._nonce_local = None
        self._chave = None
        self._lock = threading.RLock()

    @property
    def estabelecida(self):
        return self._chave is not None

    def criar_convite(self):
        with self._lock:
            self._privada = X25519PrivateKey.generate()
            self._nonce_local = os.urandom(32)
            publica = self._publica_dhe(self._privada)
            dados_assinados = self._dados_assinados(
                self._nonce_local,
                publica,
            )
            return self._pacote_handshake(
                "convite",
                self._nonce_local,
                publica,
                _assinar(self.identidade, dados_assinados),
            )

    def aceitar_convite(self, pacote):
        with self._lock:
            pacote = self._normalizar_pacote(pacote)
            self._validar_pacote(pacote, "convite")
            if pacote.get("chave_publica_assinatura") != self.chave_publica_contato:
                raise ValueError("Chave pública do contato não corresponde.")
            nonce_remoto = _de_b64(pacote["nonce"])
            publica_remota = _de_b64(pacote["chave_dhe"])
            _verificar(
                self.chave_publica_contato,
                pacote["assinatura"],
                self._dados_assinados(nonce_remoto, publica_remota),
            )
            self._privada = X25519PrivateKey.generate()
            self._nonce_local = os.urandom(32)
            publica = self._publica_dhe(self._privada)
            dados_assinados = self._dados_assinados(
                nonce_remoto,
                publica_remota,
                self._nonce_local,
                publica,
            )
            self._estabelecer(
                publica_remota,
                nonce_remoto,
                self._nonce_local,
            )
            return self._pacote_handshake(
                "resposta",
                self._nonce_local,
                publica,
                _assinar(self.identidade, dados_assinados),
                nonce_remoto,
                publica_remota,
            )

    def concluir_convite(self, pacote):
        with self._lock:
            pacote = self._normalizar_pacote(pacote)
            self._validar_pacote(pacote, "resposta")
            if pacote.get("chave_publica_assinatura") != self.chave_publica_contato:
                raise ValueError("Chave pública do contato não corresponde.")
            nonce_remoto = _de_b64(pacote["nonce"])
            publica_remota = _de_b64(pacote["chave_dhe"])
            nonce_convite = _de_b64(pacote["nonce_convite"])
            publica_convite = _de_b64(pacote["chave_dhe_convite"])
            if nonce_convite != self._nonce_local:
                raise ValueError("Nonce do convite não corresponde.")
            if publica_convite != self._publica_dhe(self._privada):
                raise ValueError("Chave DHE do convite não corresponde.")
            _verificar(
                self.chave_publica_contato,
                pacote["assinatura"],
                self._dados_assinados(
                    nonce_convite,
                    publica_convite,
                    nonce_remoto,
                    publica_remota,
                ),
            )
            self._estabelecer(
                publica_remota,
                nonce_convite,
                nonce_remoto,
            )

    def cifrar_mensagem(self, texto):
        with self._lock:
            self._exigir_estabelecida()
            nonce = os.urandom(12)
            cifrador = Cipher(
                algorithms.AES(self._chave),
                modes.GCM(nonce),
            ).encryptor()
            cifrado = cifrador.update(texto.encode("utf-8")) + cifrador.finalize()
            return json.dumps({
                "versao": VERSAO,
                "tipo": TIPO_MENSAGEM,
                "remetente": self.usuario,
                "destinatario": self.contato,
                "nonce": _b64(nonce),
                "dados": _b64(cifrado),
                "tag": _b64(cifrador.tag),
            }, separators=(",", ":"))

    def decifrar_mensagem(self, pacote):
        with self._lock:
            self._exigir_estabelecida()
            if isinstance(pacote, str):
                pacote = json.loads(pacote)
            if pacote.get("tipo") != TIPO_MENSAGEM:
                raise ValueError("Pacote de mensagem E2E inválido.")
            decifrador = Cipher(
                algorithms.AES(self._chave),
                modes.GCM(_de_b64(pacote["nonce"]), _de_b64(pacote["tag"])),
            ).decryptor()
            texto = decifrador.update(_de_b64(pacote["dados"]))
            texto += decifrador.finalize()
            return texto.decode("utf-8")

    def _estabelecer(self, publica_remota, nonce_a, nonce_b):
        segredo = self._privada.exchange(
            X25519PublicKey.from_public_bytes(publica_remota)
        )
        salt = hashlib.sha256(nonce_a + nonce_b).digest()
        self._chave = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            info=b"SI_Chat-Client contato E2E v1",
        ).derive(segredo)

    def _pacote_handshake(
        self,
        etapa,
        nonce,
        publica,
        assinatura,
        nonce_convite=None,
        publica_convite=None,
    ):
        pacote = {
            "versao": VERSAO,
            "tipo": TIPO_HANDSHAKE,
            "etapa": etapa,
            "nonce": _b64(nonce),
            "chave_dhe": _b64(publica),
            "assinatura": _b64(assinatura),
            "chave_publica_assinatura": self.identidade.chave_publica,
        }
        if nonce_convite is not None:
            pacote["nonce_convite"] = _b64(nonce_convite)
        if publica_convite is not None:
            pacote["chave_dhe_convite"] = _b64(publica_convite)
        return json.dumps(pacote, separators=(",", ":"))

    @staticmethod
    def _publica_dhe(privada):
        return privada.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )

    @staticmethod
    def _dados_assinados(*partes):
        return b"|".join(partes)

    @staticmethod
    def _validar_pacote(pacote, etapa):
        if (
            pacote.get("versao") != VERSAO
            or pacote.get("tipo") != TIPO_HANDSHAKE
            or pacote.get("etapa") != etapa
        ):
            raise ValueError("Pacote de handshake E2E inválido.")

    @staticmethod
    def _normalizar_pacote(pacote):
        if isinstance(pacote, str):
            pacote = json.loads(pacote)
        if not isinstance(pacote, dict):
            raise ValueError("Pacote E2E inválido.")
        return pacote

    def _exigir_estabelecida(self):
        if self._chave is None:
            raise ValueError("Handshake E2E ainda não foi concluído.")