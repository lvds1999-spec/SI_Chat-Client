import base64
import json
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


class IdentidadeUsuario:

    def __init__(self, usuario, diretorio="dados_locais/chaves"):
        self.usuario = usuario
        self.caminho = Path(diretorio) / f"{usuario}.json"
        self.chave = self._carregar_ou_gerar()

    def _carregar_ou_gerar(self):
        if self.caminho.exists():
            dados = json.loads(self.caminho.read_text(encoding="utf-8"))
            privada = base64.b64decode(dados["chave_privada"])
            return ed25519.Ed25519PrivateKey.from_private_bytes(privada)

        chave = ed25519.Ed25519PrivateKey.generate()
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        privada = chave.private_bytes(
            serialization.Encoding.Raw,
            serialization.PrivateFormat.Raw,
            serialization.NoEncryption(),
        )
        self.caminho.write_text(json.dumps({
            "usuario": self.usuario,
            "algoritmo_assinatura": "ed25519",
            "chave_privada": base64.b64encode(privada).decode("ascii"),
        }, indent=2), encoding="utf-8")
        return chave

    @property
    def algoritmo(self):
        return "ed25519"

    @property
    def chave_publica(self):
        dados = self.chave.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        return base64.b64encode(dados).decode("ascii")

    def assinar_nonce(self, nonce):
        return base64.b64encode(self.chave.sign(nonce)).decode("ascii")