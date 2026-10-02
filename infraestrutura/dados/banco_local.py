import re
import secrets
import sqlite3
from pathlib import Path

from infraestrutura.dados.repositorio_contatos_locais import (
    RepositorioContatosLocais,
)
from infraestrutura.dados.repositorio_historico import RepositorioHistorico
from infraestrutura.seguranca.historico import derivar_chave_historico


class BancoLocal:
    """Armazena o estado persistente de um usuario neste cliente."""

    def __init__(self, usuario, diretorio_base=None, senha=None):
        nome_diretorio = re.sub(r"[^A-Za-z0-9_.-]", "_", usuario)
        base = diretorio_base or Path(__file__).resolve().parents[2] / "dados_locais"
        caminho = Path(base) / nome_diretorio / "historico.db"
        caminho.parent.mkdir(parents=True, exist_ok=True)
        self.conexao = sqlite3.connect(caminho)
        self.conexao.row_factory = sqlite3.Row
        self.chave_historico = self._obter_chave_historico(senha)
        self.repositorio_contatos = RepositorioContatosLocais(self.conexao)
        self.repositorio_historico = RepositorioHistorico(
            self.conexao,
            self.chave_historico,
        )
        self._criar_tabelas()

    def _obter_chave_historico(self, senha):
        self.conexao.execute(
            """
            CREATE TABLE IF NOT EXISTS historico_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                salt BLOB NOT NULL
            )
            """
        )
        registro = self.conexao.execute(
            "SELECT salt FROM historico_config WHERE id = 1"
        ).fetchone()
        if registro is None:
            salt = secrets.token_bytes(16)
            self.conexao.execute(
                "INSERT INTO historico_config (id, salt) VALUES (1, ?)",
                (salt,),
            )
            self.conexao.commit()
        else:
            salt = bytes(registro[0])
        return derivar_chave_historico(senha, salt)

    def _criar_tabelas(self):
        self.repositorio_contatos.criar_tabela()
        self.repositorio_historico.criar_tabela()
        self.conexao.commit()

    def upsert_contatos(self, contatos):
        self.repositorio_contatos.upsert(contatos)

    def adicionar_contato(self, contato):
        if not isinstance(contato, dict):
            contato = {"usuario": str(contato).strip()}
        self.repositorio_contatos.adicionar(contato)

    def listar_contatos(self):
        return self.repositorio_contatos.listar()

    def atualizar_presenca(self, usuario, online):
        self.repositorio_contatos.atualizar_presenca(usuario, online)

    def remover_contato(self, usuario):
        self.repositorio_contatos.remover(usuario)

    def salvar_mensagem(self, mensagem):
        return self.repositorio_historico.salvar(mensagem)

    def listar_mensagens(self, contato, usuario):
        return self.repositorio_historico.listar(contato, usuario)

    def enfileirar_mensagem(self, mensagem):
        self.repositorio_historico.enfileirar(mensagem)

    def listar_mensagens_pendentes(self, usuario):
        return self.repositorio_historico.listar_pendentes(usuario)

    def remover_mensagem_pendente(self, mensagem):
        self.repositorio_historico.remover_pendente(mensagem)

    def fechar(self):
        self.conexao.close()