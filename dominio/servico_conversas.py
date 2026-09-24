from datetime import datetime

from infraestrutura.rede.protocolo import criar_mensagem


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
        self.servico_sessao.enviar_evento(evento)
        return evento
