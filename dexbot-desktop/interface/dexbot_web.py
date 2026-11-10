import json
import sys
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
PROJECT_DIR = HERE.parent
REPO_DIR = PROJECT_DIR.parent
PUBLIC_DIR = REPO_DIR / "public"
sys.path.insert(0, str(PROJECT_DIR))

from dexbot import Dexbot

if not PUBLIC_DIR.is_dir():
    raise FileNotFoundError(f"Pasta do site não encontrada: {PUBLIC_DIR}")

print("[Dexbot Web] Carregando a lógica principal do Dexbot...")
dexbot = Dexbot()
dexbot_lock = threading.Lock()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # A interface estática vem da pasta public do repositório.
        super().__init__(*args, directory=str(PUBLIC_DIR), **kwargs)

    def send_json(self, status, data):
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        route = urlsplit(self.path).path
        if route == "/api/status":
            try:
                from urllib.request import urlopen
                with urlopen("http://127.0.0.1:11434/api/tags", timeout=3) as response:
                    data = json.loads(response.read().decode("utf-8"))
                models = [item.get("name", "") for item in data.get("models", [])]
                model = "qwen2.5-coder:1.5b"
                ready = any(name == model or name.startswith(model + ":") for name in models)
                self.send_json(200, {
                    "ok": ready,
                    "model": model,
                    "memory_items": len(dexbot.conhecimento_cache),
                    "examples": len(dexbot.exemplos)
                })
            except Exception:
                self.send_json(200, {"ok": False, "model": "qwen2.5-coder:1.5b"})
            return
        if route.startswith("/api/"):
            self.send_json(404, {"error": "Rota não encontrada"})
            return
        self.path = route or "/"
        if self.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        if urlsplit(self.path).path != "/api/chat":
            self.send_json(404, {"error": "Rota não encontrada"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 2 or length > 100000:
                self.send_json(400, {"error": "Tamanho da mensagem inválido"})
                return
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            messages = payload.get("messages", [])
            if not isinstance(messages, list) or not messages or len(messages) > 30:
                self.send_json(400, {"error": "Histórico de conversa inválido"})
                return

            pergunta = None
            for item in reversed(messages):
                if isinstance(item, dict) and item.get("role") == "user":
                    conteudo = item.get("content")
                    if isinstance(conteudo, str):
                        pergunta = conteudo.strip()
                    break
            if not pergunta:
                self.send_json(400, {"error": "Escreva uma mensagem antes de enviar."})
                return
            if len(pergunta) > 12000:
                self.send_json(400, {"error": "A mensagem passou do limite de 12.000 caracteres."})
                return

            with dexbot_lock:
                resposta = dexbot.responder(pergunta)
            if not resposta:
                self.send_json(503, {"error": "O Dexbot não conseguiu gerar uma resposta. Confira se o Ollama está aberto."})
                return
            self.send_json(200, {
                "response": resposta,
                "memory_items": len(dexbot.conhecimento_cache)
            })
        except Exception as error:
            self.send_json(500, {"error": "Erro interno: " + str(error)[:300]})

    def log_message(self, fmt, *args):
        print("[Dexbot Web] " + (fmt % args))


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("DEXBOT WEB iniciado sem token!")
    print("Site:", PUBLIC_DIR)
    print("Memória local:", len(dexbot.conhecimento_cache), "trechos")
    print("Exemplos aprendidos:", len(dexbot.exemplos))
    print("Abra: http://127.0.0.1:8765")
    print("O mesmo endereço público do túnel abrirá o site e a API.")
    print("Servidor local vinculado somente a 127.0.0.1.")
    print("Para fechar, pressione Ctrl+C.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDexbot Web encerrado.")
    finally:
        server.server_close()
