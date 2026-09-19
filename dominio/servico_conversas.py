from datetime import datetime

from infraestrutura.rede.protocolo import criar_mensagem


class ServicoConversas:

    def __init__(self, servico_sessao, remetente):
        self.servico_sessao = servico_sessao
        self.remetente = remetente

    def enviar_mensagem(self, destinatario, texto):
        evento = criar_mensagem(
            self.remetente,
            destinatario,
            datetime.now().isoformat(timespec="seconds"),
            texto
        )
        self.servico_sessao.enviar_evento(evento)
        return evento
