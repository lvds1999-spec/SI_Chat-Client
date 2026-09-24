import re
import sqlite3
from pathlib import Path

from infraestrutura.dados.repositorio_contatos_locais import (
    RepositorioContatosLocais,
)
from infraestrutura.dados.repositorio_historico import RepositorioHistorico


class BancoLocal:
    """Armazena o estado persistente de um usuario neste cliente."""

    def __init__(self, usuario, diretorio_base=None):
        nome_diretorio = re.sub(r"[^A-Za-z0-9_.-]", "_", usuario)
        base = diretorio_base or Path(__file__).resolve().parents[2] / "dados_locais"
        caminho = Path(base) / nome_diretorio / "historico.db"
        caminho.parent.mkdir(parents=True, exist_ok=True)
        self.conexao = sqlite3.connect(caminho)
        self.conexao.row_factory = sqlite3.Row
        self.repositorio_contatos = RepositorioContatosLocais(self.conexao)
        self.repositorio_historico = RepositorioHistorico(self.conexao)
        self._criar_tabelas()

    def _criar_tabelas(self):
        self.repositorio_contatos.criar_tabela()
        self.repositorio_historico.criar_tabela()
        self.conexao.commit()

    def upsert_contatos(self, contatos):
        self.repositorio_contatos.upsert(contatos)

    def listar_contatos(self):
        return self.repositorio_contatos.listar()

    def atualizar_presenca(self, usuario, online):
        self.repositorio_contatos.atualizar_presenca(usuario, online)

    def remover_contato(self, usuario):
        self.repositorio_contatos.remover(usuario)

    def salvar_mensagem(self, mensagem):
        self.repositorio_historico.salvar(mensagem)

    def listar_mensagens(self, contato, usuario):
        return self.repositorio_historico.listar(contato, usuario)

    def fechar(self):
        self.conexao.close()