# SI_Chat-Client

## Estrutura

- `apresentacao/`: interface gráfica; depende apenas de `ServicoSessao`.
- `dominio/`: serviços da aplicação, incluindo `ServicoSessao`.
- `infraestrutura/rede/`: socket, recepção e protocolo compartilhado com o servidor.

A GUI não acessa o socket diretamente. Toda operação de sessão passa por
`dominio/servico_sessao.py`.

## Execução

Com o servidor ativo na porta 8000:

```powershell
python ClientProtocol\client.py
```