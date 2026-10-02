# SI_Chat-Client

## Estrutura

- `apresentacao/`: interface gráfica e coordenação dos fluxos de conversa.
- `dominio/`: serviços da aplicação, incluindo `ServicoSessao` e `ServicoConversas`.
- `infraestrutura/rede/`: socket, transporte seguro com o servidor e sessão E2EE independente por contato.
- `infraestrutura/seguranca/`: identidade do usuário e derivação da chave local do histórico.
- `infraestrutura/dados/`: contatos e histórico persistidos em SQLite local.

A GUI não acessa o socket diretamente. As operações de rede passam por
`dominio/servico_sessao.py`; a persistência local passa pelo banco e repositórios
em `infraestrutura/dados/`.

## Proteção das mensagens

Antes do envio, a mensagem recebe uma camada E2EE: uma chave derivada do handshake com o destinatário cifra o texto com AES-256-GCM. O pacote E2EE segue dentro do canal seguro independente negociado com o servidor, protegido por DHE/HKDF, AES-256-CTR e HMAC-SHA256. O servidor encaminha o pacote E2EE sem acesso à chave entre os usuários.

O histórico fica em `dados_locais/<usuario>/historico.db`. O texto é cifrado com AES-256-GCM antes de ser gravado; a chave de 256 bits é derivada localmente da senha da conta com PBKDF2-HMAC-SHA256 e salt aleatório persistido no banco local. Essa chave nunca é enviada ao servidor.

## Execução

Com o servidor ativo na porta 8000:

```powershell
python ClientProtocol\client.py
```