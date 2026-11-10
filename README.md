# Dexbot

Interface web publicada pelo Cloudflare Worker. O modelo Ollama e o cérebro Python do Dexbot rodam no PC.

## Arquitetura

- `index.html`, `style.css`, `app.js`: interface.
- `worker.js`: API do Worker, que encaminha chamadas para o PC.
- `wrangler.toml`: configuração de publicação do Worker e dos arquivos estáticos.
- `dexbot-desktop/dexbot.py`: lógica principal, memória e conhecimento.
- `dexbot-desktop/interface/dexbot_web.py`: API local protegida.

## Configuração necessária no Worker

Defina estas variáveis/segredos no ambiente do Cloudflare Worker:

- `DEXBOT_ORIGIN`: URL HTTPS do túnel que aponta para `http://127.0.0.1:8765` (por exemplo, a URL gerada pelo Quick Tunnel do cloudflared).
- `DEXBOT_TOKEN`: conteúdo do arquivo local `dexbot-desktop/.dexbot-token`, criado automaticamente na primeira execução do servidor.

Nunca publique o token no GitHub nem coloque-o no JavaScript do navegador.

## Iniciar no Windows

1. Instale e inicie o Ollama com o modelo `qwen2.5-coder:1.5b`.
2. Execute `dexbot-desktop/interface/iniciar_interface.bat`.
3. Em outro terminal, inicie o túnel:
   `cloudflared tunnel --url http://127.0.0.1:8765`
4. Configure a URL HTTPS exibida como `DEXBOT_ORIGIN` no Worker.
5. Cadastre o conteúdo de `dexbot-desktop/.dexbot-token` como segredo `DEXBOT_TOKEN` no Worker.

O Quick Tunnel gera uma URL temporária; se ela mudar, atualize `DEXBOT_ORIGIN`. O PC, Ollama, servidor Python e túnel precisam permanecer ligados para o chat responder.

## Limitações atuais

- O chat envia texto ao Dexbot.
- Imagens aparecem na interface, mas ainda não são interpretadas pelo modelo.
- O servidor local escuta apenas em `127.0.0.1` e exige autenticação nas rotas da API.
