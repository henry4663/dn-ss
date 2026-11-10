import json
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

HERE = Path(__file__).resolve().parent
OLLAMA_URL = "http://127.0.0.1:11434"
MODEL = "qwen2.5-coder:1.5b"
SYSTEM_PROMPT = (
    "Você é Dexbot, uma IA local que ajuda principalmente com HTML, CSS, JavaScript e programação. "
    "Responda em português claro. Explique de forma organizada e entregue código completo quando solicitado. "
    "Separe corretamente HTML, CSS e JavaScript. Não invente testes que não executou."
)

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(HERE), **kwargs)

    def send_json(self, status, data):
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/api/status":
            try:
                with urlopen(OLLAMA_URL + "/api/tags", timeout=3) as response:
                    data = json.loads(response.read().decode("utf-8"))
                models = [item.get("name", "") for item in data.get("models", [])]
                ready = any(name == MODEL or name.startswith(MODEL + ":") for name in models)
                self.send_json(200, {"ok": ready, "model": MODEL, "installed": models})
            except Exception:
                self.send_json(200, {"ok": False, "model": MODEL})
            return
        if self.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        if self.path != "/api/chat":
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
            clean = [{"role": "system", "content": SYSTEM_PROMPT}]
            for item in messages:
                role = item.get("role")
                content = item.get("content")
                if role not in ("user", "assistant") or not isinstance(content, str):
                    continue
                clean.append({"role": role, "content": content[:12000]})
            body = json.dumps({
                "model": MODEL,
                "messages": clean,
                "stream": False,
                "keep_alive": "30m",
                "options": {"temperature": 0.25, "num_ctx": 2048, "num_predict": 768, "num_thread": 8, "repeat_penalty": 1.2, "repeat_last_n": 128}
            }).encode("utf-8")
            request = Request(OLLAMA_URL + "/api/chat", data=body, headers={"Content-Type": "application/json"}, method="POST")
            with urlopen(request, timeout=300) as response:
                result = json.loads(response.read().decode("utf-8"))
            self.send_json(200, {"response": result.get("message", {}).get("content", "")})
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:500]
            self.send_json(502, {"error": "Ollama retornou erro: " + detail})
        except URLError:
            self.send_json(503, {"error": "Não consegui conectar ao Ollama. Abra o Ollama no Windows."})
        except Exception as error:
            self.send_json(500, {"error": "Erro interno: " + str(error)})

    def log_message(self, fmt, *args):
        print("[Dexbot Web] " + (fmt % args))

if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("DEXBOT WEB iniciado!")
    print("Abra: http://127.0.0.1:8765")
    print("Somente este PC pode acessar por enquanto.")
    print("Para fechar, pressione Ctrl+C.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDexbot Web encerrado.")
    finally:
        server.server_close()
