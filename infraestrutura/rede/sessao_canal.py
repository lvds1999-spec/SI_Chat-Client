import time

from infraestrutura.rede.sessao_segura import SessaoSegura


class SessaoCanal(SessaoSegura):
    """Canal seguro com o servidor, renovado pelo protocolo de transporte."""

    INTERVALO_RENOVACAO_SEGUNDOS = 60 * 60
    LIMITE_MENSAGENS = 100

    def __init__(self):
        super().__init__()
        self._inicio_sessao = None

    def iniciar_cliente(self, arquivo):
        super().iniciar_cliente(arquivo)
        self._inicio_sessao = time.monotonic()

    @property
    def mensagens_trocadas(self):
        return self._sequencia_envio + self._sequencia_recebimento

    @property
    def proxima_renovacao_em(self):
        if self._inicio_sessao is None:
            return None
        por_tempo = (
            self.INTERVALO_RENOVACAO_SEGUNDOS
            - (time.monotonic() - self._inicio_sessao)
        )
        por_mensagens = self.LIMITE_MENSAGENS - self.mensagens_trocadas
        return max(0, min(por_tempo, por_mensagens))

    def _estabelecer(self, *argumentos, **kwargs):
        super()._estabelecer(*argumentos, **kwargs)
        self._inicio_sessao = time.monotonic()