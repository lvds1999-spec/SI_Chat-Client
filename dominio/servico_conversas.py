from datetime import datetime

from infraestrutura.rede.protocolo import MENSAGEM, criar_mensagem


class ServicoConversas:

    def __init__(self, servico_sessao, remetente, banco_local):
        self.servico_sessao = servico_sessao
        self.remetente = remetente
        self.banco_local = banco_local

    def enviar_mensagem(self, destinatario, texto):
        evento = criar_mensagem(
            self.remetente,
            destinatario,
            datetime.now().isoformat(timespec="seconds"),
            texto
        )
        self.banco_local.salvar_mensagem(evento)
        self.banco_local.enfileirar_mensagem(evento)
        try:
            enviado = self.servico_sessao.enviar_mensagem_segura(evento)
        except (ConnectionError, OSError):
            enviado = False
        if enviado:
            evento["status"] = "enviado"
            self.banco_local.atualizar_status(evento, "enviado")
            self.banco_local.remover_mensagem_pendente(evento)
        else:
            evento["status"] = "pendente"
        return evento

    def reenviar_pendentes(self):
        for mensagem in self.banco_local.listar_mensagens_pendentes(self.remetente):
            evento = {"evento": MENSAGEM, **mensagem}
            try:
                enviado = self.servico_sessao.enviar_mensagem_segura(evento)
            except (ConnectionError, OSError):
                break
            if enviado:
                self.banco_local.atualizar_status(evento, "enviado")
                self.banco_local.remover_mensagem_pendente(mensagem)
