class RepositorioHistorico:
    """Persistencia local das mensagens de uma conta."""

    def __init__(self, conexao):
        self.conexao = conexao

    def criar_tabela(self):
        self.conexao.execute(
            """
            CREATE TABLE IF NOT EXISTS mensagens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                remetente TEXT NOT NULL,
                destinatario TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                texto TEXT NOT NULL,
                UNIQUE (remetente, destinatario, timestamp, texto)
            )
            """
        )

    def salvar(self, mensagem):
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

    def listar(self, contato, usuario):
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