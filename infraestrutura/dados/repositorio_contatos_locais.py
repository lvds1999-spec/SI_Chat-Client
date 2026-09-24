class RepositorioContatosLocais:
    """Persistencia local dos contatos e de sua presenca."""

    def __init__(self, conexao):
        self.conexao = conexao

    def criar_tabela(self):
        self.conexao.execute(
            """
            CREATE TABLE IF NOT EXISTS contatos (
                id TEXT PRIMARY KEY,
                usuario TEXT NOT NULL UNIQUE,
                apelido TEXT,
                favorito INTEGER NOT NULL DEFAULT 0,
                online INTEGER NOT NULL DEFAULT 0
            )
            """
        )

    def upsert(self, contatos):
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

    def listar(self):
        return [dict(row) for row in self.conexao.execute(
            "SELECT id, usuario, apelido, favorito, online FROM contatos"
        )]

    def atualizar_presenca(self, usuario, online):
        self.conexao.execute(
            "UPDATE contatos SET online = ? WHERE usuario = ?",
            (int(bool(online)), usuario)
        )
        self.conexao.commit()

    def remover(self, usuario):
        self.conexao.execute("DELETE FROM contatos WHERE usuario = ?", (usuario,))
        self.conexao.commit()