# Dexbot

O site é servido pelo Cloudflare Worker. O modelo Ollama e o cérebro Python rodam no PC.

## Arquitetura

- `public/`: arquivos públicos da interface.
- `worker.js`: API intermediária do Cloudflare, que encaminha as mensagens para o PC.
- `wrangler.toml`: configuração do Worker e dos arquivos públicos.
- `dexbot-desktop/dexbot.py`: lógica principal do Dexbot.
- `dexbot-desktop/interface/dexbot_web.py`: API local protegida.
- `dexbot-desktop/iniciar_conexao_publica.bat`: inicia a API local e o túnel HTTPS.

## Publicação automática

O GitHub Actions publica o Worker quando há atualização na branch `main`.

Cadastre estes dois **Actions secrets** no repositório GitHub (Settings → Secrets and variables → Actions):

- `CLOUDFLARE_API_TOKEN`: token de API do Cloudflare com permissão para editar Workers.
- `CLOUDFLARE_ACCOUNT_ID`: ID da conta Cloudflare.

Sem esses dois secrets, o fluxo de publicação não consegue autenticar.

## Conectar o PC ao Worker

No Windows:

1. Deixe o Ollama aberto com o modelo `qwen2.5-coder:1.5b instalado.
2. Execute `dexbot-desktop/iniciar_conexao_publica.bat`.
3. O arquivo privado `dexbot-desktop/.dexbot-token` será aberto no Bloco de Notas.
4. A janela do túnel mostrará uma URL HTTPS terminada em `.trycloudflare.com`.

No ambiente do Worker, configure os secrets:

- `DEXBOT_ORIGIN`: a URL HTTPS mostrada pelo cloudflared, sem caminho adicional.
- `DEXBOT_TOKEN`: o conteúdo de `dexbot-desktop/.dexbot-token`.

Nunca coloque o token no GitHub, no HTML ou no JavaScript do navegador.

O Quick Tunnel gera uma URL temporária. Se ela mudar, atualize `DEXBOT_ORIGIN`. O PC, Ollama, janela da API e túnel precisam permanecer ligados para o chat responder.

## Limitações

- O chat envia texto ao Dexbot.
- A imagem anexada aparece como prévia, mas ainda não é analisada pelo modelo.
- A API local escuta apenas em `127.0.0.1` e exige autenticação.
