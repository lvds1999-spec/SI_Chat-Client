import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from infraestrutura.seguranca.historico import fingerprint_mensagem


class RepositorioHistorico:
    """Persistencia local das mensagens de uma conta."""

    def __init__(self, conexao, chave):
        self.conexao = conexao
        self.chave = chave

    def criar_tabela(self):
        self._criar_ou_migrar("mensagens")
        self._criar_ou_migrar("mensagens_pendentes")

    def _criar_ou_migrar(self, tabela):
        colunas = [
            linha[1]
            for linha in self.conexao.execute(f"PRAGMA table_info({tabela})")
        ]
        if not colunas:
            self._criar_tabela_cifrada(tabela)
        elif "texto" in colunas:
            self._migrar_tabela(tabela)

    def _criar_tabela_cifrada(self, tabela):
        self.conexao.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {tabela} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                remetente TEXT NOT NULL,
                destinatario TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                texto_cifrado BLOB NOT NULL,
                nonce BLOB NOT NULL,
                fingerprint BLOB NOT NULL UNIQUE
            )
            """
        )

    def _migrar_tabela(self, tabela):
        registros = self.conexao.execute(
            f"SELECT id, remetente, destinatario, timestamp, texto FROM {tabela}"
        ).fetchall()
        nova_tabela = f"{tabela}_cifrada"
        self._criar_tabela_cifrada(nova_tabela)
        for registro in registros:
            self._inserir_cifrado(nova_tabela, dict(registro), registro[0])
        self.conexao.execute(f"DROP TABLE {tabela}")
        self.conexao.execute(f"ALTER TABLE {nova_tabela} RENAME TO {tabela}")

    def salvar(self, mensagem):
        self._inserir_cifrado("mensagens", mensagem)
        self.conexao.commit()

    def listar(self, contato, usuario):
        registros = self.conexao.execute(
            """
            SELECT remetente, destinatario, timestamp, texto_cifrado, nonce
            FROM mensagens
            WHERE (remetente = ? AND destinatario = ?)
               OR (remetente = ? AND destinatario = ?)
            ORDER BY id
            """,
            (usuario, contato, contato, usuario)
        ).fetchall()
        return [self._decifrar(registro) for registro in registros]

    def enfileirar(self, mensagem):
        self._inserir_cifrado("mensagens_pendentes", mensagem)
        self.conexao.commit()

    def listar_pendentes(self, remetente):
        registros = self.conexao.execute(
            """
            SELECT remetente, destinatario, timestamp, texto_cifrado, nonce
            FROM mensagens_pendentes
            WHERE remetente = ?
            ORDER BY id
            """,
            (remetente,)
        ).fetchall()
        return [self._decifrar(registro) for registro in registros]

    def remover_pendente(self, mensagem):
        fingerprint = self._fingerprint(mensagem)
        self.conexao.execute(
            "DELETE FROM mensagens_pendentes WHERE fingerprint = ?",
            (fingerprint,),
        )
        self.conexao.commit()

    def _inserir_cifrado(self, tabela, mensagem, identificador=None):
        remetente = mensagem.get("remetente", "")
        destinatario = mensagem.get("destinatario", "")
        timestamp = mensagem.get("timestamp", "")
        texto = mensagem.get("texto", "")
        nonce = secrets.token_bytes(12)
        cifrado = AESGCM(self.chave).encrypt(
            nonce,
            texto.encode("utf-8"),
            None,
        )
        valores = (
            identificador,
            remetente,
            destinatario,
            timestamp,
            cifrado,
            nonce,
            self._fingerprint(mensagem),
        )
        if identificador is None:
            self.conexao.execute(
                f"""
                INSERT OR IGNORE INTO {tabela}
                    (remetente, destinatario, timestamp, texto_cifrado, nonce, fingerprint)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                valores[1:],
            )
        else:
            self.conexao.execute(
                f"""
                INSERT OR IGNORE INTO {tabela}
                    (id, remetente, destinatario, timestamp, texto_cifrado, nonce, fingerprint)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                valores,
            )

    def _decifrar(self, registro):
        texto = AESGCM(self.chave).decrypt(
            bytes(registro["nonce"]),
            bytes(registro["texto_cifrado"]),
            None,
        ).decode("utf-8")
        return {
            "remetente": registro["remetente"],
            "destinatario": registro["destinatario"],
            "timestamp": registro["timestamp"],
            "texto": texto,
        }

    def _fingerprint(self, mensagem):
        return fingerprint_mensagem(
            self.chave,
            mensagem.get("remetente", ""),
            mensagem.get("destinatario", ""),
            mensagem.get("timestamp", ""),
            mensagem.get("texto", ""),
        )