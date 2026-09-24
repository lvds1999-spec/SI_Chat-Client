import re
import sqlite3
from pathlib import Path


class BancoLocal:
    """Armazena o estado persistente de um usuario neste cliente."""

    def __init__(self, usuario, diretorio_base=None):
        nome_diretorio = re.sub(r"[^A-Za-z0-9_.-]", "_", usuario)
        base = diretorio_base or Path(__file__).resolve().parents[2] / "dados_locais"
        caminho = Path(base) / nome_diretorio / "historico.db"
        caminho.parent.mkdir(parents=True, exist_ok=True)
        self.conexao = sqlite3.connect(caminho)
        self.conexao.row_factory = sqlite3.Row
        self._criar_tabelas()

    def _criar_tabelas(self):
        self.conexao.executescript(
            """
            CREATE TABLE IF NOT EXISTS contatos (
                id TEXT PRIMARY KEY,
                usuario TEXT NOT NULL UNIQUE,
                apelido TEXT,
                favorito INTEGER NOT NULL DEFAULT 0,
                online INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS mensagens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                remetente TEXT NOT NULL,
                destinatario TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                texto TEXT NOT NULL,
                UNIQUE (remetente, destinatario, timestamp, texto)
            );
            """
        )
        self.conexao.commit()

    def upsert_contatos(self, contatos):
        for contato in contatos:
            if not isinstance(contato, dict):
                contato = {"usuario": str(contato).strip()}
            usuario = contato.get("usuario", contato.get("nome"))
            if not usuario:
                continue
            contato_id = contato.get("id", usuario)
            self.conexao.execute(
                """
                INSERT INTO contatos (id, usuario, online)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    usuario = excluded.usuario,
                    online = excluded.online
                """,
                (str(contato_id), usuario, int(bool(contato.get("online", False))))
            )
        self.conexao.commit()

    def listar_contatos(self):
        return [dict(row) for row in self.conexao.execute(
            "SELECT id, usuario, apelido, favorito, online FROM contatos"
        )]

    def atualizar_presenca(self, usuario, online):
        self.conexao.execute(
            "UPDATE contatos SET online = ? WHERE usuario = ?",
            (int(bool(online)), usuario)
        )
        self.conexao.commit()

    def remover_contato(self, usuario):
        self.conexao.execute("DELETE FROM contatos WHERE usuario = ?", (usuario,))
        self.conexao.commit()

    def salvar_mensagem(self, mensagem):
        self.conexao.execute(
            """
            INSERT OR IGNORE INTO mensagens
                (remetente, destinatario, timestamp, texto)
            VALUES (?, ?, ?, ?)
            """,
            (
                mensagem.get("remetente", ""),
                mensagem.get("destinatario", ""),
                mensagem.get("timestamp", ""),
                mensagem.get("texto", "")
            )
        )
        self.conexao.commit()

    def listar_mensagens(self, contato, usuario):
        return [dict(row) for row in self.conexao.execute(
            """
            SELECT remetente, destinatario, timestamp, texto
            FROM mensagens
            WHERE (remetente = ? AND destinatario = ?)
               OR (remetente = ? AND destinatario = ?)
            ORDER BY id
            """,
            (usuario, contato, contato, usuario)
        )]

    def fechar(self):
        self.conexao.close()