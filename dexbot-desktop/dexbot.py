import json
import math
import os
import random
import re
import unicodedata
import ipaddress
import socket
import urllib.parse
import urllib.request
import urllib.error
from html.parser import HTMLParser
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "dexbot_dados.json")
MODEL_FILE = os.path.join(BASE_DIR, "dexbot_modelo.json")
BASE_CONHECIMENTO = os.path.join(BASE_DIR, "dexbot_conhecimento.json")
HISTORY_FILE = os.path.join(BASE_DIR, "dexbot_conversa.json")
OLLAMA_MODEL = "qwen2.5-coder:1.5b"
OLLAMA_CHAT_URL = "http://127.0.0.1:11434/api/chat"
EXTENSOES_TEXTO = {".txt", ".md", ".py", ".html", ".css", ".js", ".json", ".csv", ".xml", ".yml", ".yaml", ".ini", ".log"}

class ExtratorTexto(HTMLParser):
    def __init__(self):
        super().__init__()
        self.partes = []
        self.ignorar = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript", "svg"}:
            self.ignorar += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript", "svg"} and self.ignorar:
            self.ignorar -= 1

    def handle_data(self, data):
        if not self.ignorar:
            texto = data.strip()
            if texto:
                self.partes.append(texto)

def endereco_publico(url):
    try:
        partes = urllib.parse.urlparse(url)
        if partes.scheme != "https" or not partes.hostname:
            return False
        host = partes.hostname
        if host in {"localhost"} or host.endswith(".local"):
            return False
        for info in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM):
            ip = ipaddress.ip_address(info[4][0])
            if not ip.is_global:
                return False
        return True
    except Exception:
        return False

EXEMPLOS_INICIAIS = [
    ["oi", "Olá! Eu sou a Dexbot. Como posso ajudar?"],
    ["ola", "Olá! Eu sou a Dexbot. Como posso ajudar?"],
    ["bom dia", "Bom dia! O que vamos aprender hoje?"],
    ["boa tarde", "Boa tarde! O que vamos fazer hoje?"],
    ["boa noite", "Boa noite! Estou pronta para conversar."],
    ["quem e voce", "Sou a Dexbot, uma IA local em desenvolvimento."],
    ["o que e dexbot", "Sou a Dexbot, uma IA local em desenvolvimento."],
    ["qual e seu nome", "Meu nome é Dexbot."],
    ["quem criou voce", "Fui criada pelo Henry, com um sistema próprio de aprendizado."],
    ["quem e meu criador", "Meu criador é o Henry."],
    ["o que voce faz", "Converso e aprendo com exemplos que você me ensina."],
    ["quais sao suas funcoes", "Nesta versão eu reconheço padrões de texto e aprendo perguntas e respostas."],
    ["voce aprende", "Sim! Use /ensinar para adicionar exemplos e treinar minha rede neural."],
    ["como voce aprende", "Você me ensina pares de perguntas e respostas. Eu treino uma pequena rede neural com esses exemplos."],
    ["obrigado", "Por nada! Pode continuar."],
    ["obrigada", "Por nada! Pode continuar."],
    ["tchau", "Até mais! Estarei aqui quando você voltar."],
    ["ate logo", "Até mais! Estarei aqui quando você voltar."],
    ["me ajude", "Use /ajuda para ver os comandos disponíveis."],
    ["como voce esta", "Estou funcionando localmente e pronta para aprender."]
]

def normalizar(texto):
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^\w\s]", " ", texto, flags=re.UNICODE)
    return re.sub(r"\s+", " ", texto)

def vetorizar(texto, vocabulario):
    palavras = normalizar(texto).split()
    tokens = list(palavras)
    tokens += [palavras[i] + "_" + palavras[i + 1] for i in range(len(palavras) - 1)]
    contagem = Counter(tokens)
    return [float(contagem.get(p, 0)) for p in vocabulario]

def softmax(valores):
    maior = max(valores)
    exps = [math.exp(max(-40, min(40, v - maior))) for v in valores]
    total = sum(exps) or 1.0
    return [v / total for v in exps]

class RedeNeural:
    def __init__(self, entradas, ocultos, saidas):
        rng = random.Random(42)
        self.w1 = [[rng.uniform(-0.15, 0.15) for _ in range(entradas)] for _ in range(ocultos)]
        self.b1 = [0.0] * ocultos
        self.w2 = [[rng.uniform(-0.15, 0.15) for _ in range(ocultos)] for _ in range(saidas)]
        self.b2 = [0.0] * saidas

    def prever(self, x):
        h = []
        for i, pesos in enumerate(self.w1):
            soma = self.b1[i] + sum(p * v for p, v in zip(pesos, x))
            h.append(max(0.0, soma))
        logits = [
            self.b2[i] + sum(p * v for p, v in zip(pesos, h))
            for i, pesos in enumerate(self.w2)
        ]
        return softmax(logits), h

    def treinar(self, dados, epocas=260, taxa=0.045):
        rng = random.Random(7)
        for _ in range(epocas):
            rng.shuffle(dados)
            for x, alvo in dados:
                probs, h = self.prever(x)
                grad_saida = probs[:]
                grad_saida[alvo] -= 1.0

                grad_oculta = [0.0] * len(h)
                for j in range(len(h)):
                    grad_oculta[j] = sum(
                        self.w2[k][j] * grad_saida[k]
                        for k in range(len(grad_saida))
                    )
                    if h[j] <= 0:
                        grad_oculta[j] = 0.0

                for k in range(len(self.w2)):
                    for j in range(len(h)):
                        self.w2[k][j] -= taxa * grad_saida[k] * h[j]
                    self.b2[k] -= taxa * grad_saida[k]

                for j in range(len(self.w1)):
                    for i in range(len(x)):
                        self.w1[j][i] -= taxa * grad_oculta[j] * x[i]
                    self.b1[j] -= taxa * grad_oculta[j]

class Dexbot:
    def __init__(self):
        self.exemplos = self.carregar_dados()
        self.vocabulario = []
        self.respostas = []
        self.rede = None
        self.historico = self.carregar_historico()
        self.treinar()

    def carregar_dados(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as arquivo:
                    dados = json.load(arquivo)
                if isinstance(dados, list):
                    return dados
            except (OSError, json.JSONDecodeError):
                print("Dexbot: Não consegui ler os dados antigos. Vou criar uma base nova.")
        return [{"pergunta": p, "resposta": r} for p, r in EXEMPLOS_INICIAIS]

    def salvar_dados(self):
        with open(DATA_FILE, "w", encoding="utf-8") as arquivo:
            json.dump(self.exemplos, arquivo, ensure_ascii=False, indent=2)

    def treinar(self):
        if not self.exemplos:
            print("Dexbot: Ainda não tenho exemplos para treinar.")
            return

        tokens = []
        for item in self.exemplos:
            palavras = normalizar(item["pergunta"]).split()
            tokens.extend(palavras)
            tokens.extend(
                palavras[i] + "_" + palavras[i + 1]
                for i in range(len(palavras) - 1)
            )

        self.vocabulario = sorted(set(tokens))
        self.respostas = sorted(set(item["resposta"] for item in self.exemplos))
        indice_resposta = {r: i for i, r in enumerate(self.respostas)}

        dados_treino = [
            (vetorizar(item["pergunta"], self.vocabulario), indice_resposta[item["resposta"]])
            for item in self.exemplos
        ]

        ocultos = min(32, max(12, len(self.vocabulario) * 2))
        self.rede = RedeNeural(len(self.vocabulario), ocultos, len(self.respostas))
        self.rede.treinar(dados_treino)
        self.salvar_modelo()
        print("Dexbot: Treinamento concluído. Exemplos:", len(self.exemplos))

    def salvar_modelo(self):
        modelo = {
            "vocabulario": self.vocabulario,
            "respostas": self.respostas,
            "w1": self.rede.w1,
            "b1": self.rede.b1,
            "w2": self.rede.w2,
            "b2": self.rede.b2
        }
        with open(MODEL_FILE, "w", encoding="utf-8") as arquivo:
            json.dump(modelo, arquivo, ensure_ascii=False)

    def pesquisar_pasta(self):
        pasta = input("Caminho da pasta que posso estudar: ").strip().strip('"')
        if not pasta or not os.path.isdir(pasta):
            print("Dexbot: Essa pasta não existe ou não pode ser acessada.")
            return

        ignorar = {".git", "node_modules", "__pycache__", ".venv", "venv", "env"}
        documentos = []
        total_bytes = 0
        limite_arquivos = 100
        limite_total = 5 * 1024 * 1024

        for raiz, pastas, arquivos in os.walk(pasta):
            pastas[:] = [p for p in pastas if p not in ignorar and not p.startswith(".")]
            for nome in arquivos:
                caminho = os.path.join(raiz, nome)
                extensao = os.path.splitext(nome)[1].lower()
                if extensao not in EXTENSOES_TEXTO or nome.lower() in {".env", "secrets.txt"}:
                    continue
                try:
                    tamanho = os.path.getsize(caminho)
                    if tamanho > 250000 or total_bytes + tamanho > limite_total:
                        continue
                    with open(caminho, "r", encoding="utf-8", errors="ignore") as arquivo:
                        conteudo = arquivo.read(250000).strip()
                    if not conteudo:
                        continue
                    total_bytes += tamanho
                    blocos = [b.strip() for b in re.split(r"\n\s*\n", conteudo) if len(b.strip()) >= 40]
                    if not blocos:
                        blocos = [conteudo[i:i+1200].strip() for i in range(0, len(conteudo), 1200)]
                    for bloco in blocos:
                        documentos.append({
                            "arquivo": os.path.relpath(caminho, pasta),
                            "trecho": bloco[:1800]
                        })
                    if len(documentos) >= limite_arquivos:
                        break
                except (OSError, UnicodeError):
                    continue
            if len(documentos) >= limite_arquivos or total_bytes >= limite_total:
                break

        if not documentos:
            print("Dexbot: Não encontrei arquivos de texto compatíveis nessa pasta.")
            return

        antigos = []
        if os.path.exists(BASE_CONHECIMENTO):
            try:
                with open(BASE_CONHECIMENTO, "r", encoding="utf-8") as arquivo:
                    antigos = json.load(arquivo)
            except (OSError, json.JSONDecodeError):
                antigos = []
        antigos.extend(documentos)
        with open(BASE_CONHECIMENTO, "w", encoding="utf-8") as arquivo:
            json.dump(antigos, arquivo, ensure_ascii=False, indent=2)
        print("Dexbot: Estudei", len(documentos), "trechos de", len(set(d["arquivo"] for d in documentos)), "arquivos.")
        print("Dexbot: O conteúdo foi salvo localmente para consultas futuras.")

    def barra_progresso(self, bytes_total, etapa):
        kb = bytes_total / 1024
        blocos = min(30, int(kb / 10))
        barra = "#" * blocos + "-" * (30 - blocos)
        print("\r[" + barra + "] " + format(kb, ".1f") + " KB aprendidos | " + etapa[:35].ljust(35), end="", flush=True)

    def pesquisar_web(self, consulta):
        consulta = consulta.strip()
        if not consulta:
            return 0
        url_busca = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": consulta})
        pedido = urllib.request.Request(url_busca, headers={"User-Agent": "DexbotLocal/1.0"})
        try:
            with urllib.request.urlopen(pedido, timeout=15) as resposta:
                html_busca = resposta.read(700000).decode("utf-8", errors="ignore")
        except urllib.error.HTTPError as erro:
            print("\nDexbot: O buscador respondeu HTTP", erro.code, ". Tentando a Wikipédia.")
            estado = [0]
            return self.pesquisar_wikipedia(consulta, estado)
        except Exception as erro:
            print("\nDexbot: Falha de conexão:", erro, ". Tentando a Wikipédia.")
            estado = [0]
            return self.pesquisar_wikipedia(consulta, estado)

        class Links(HTMLParser):
            def __init__(self):
                super().__init__()
                self.links = []
            def handle_starttag(self, tag, attrs):
                if tag == "a":
                    dados = dict(attrs)
                    classe = dados.get("class", "")
                    href = dados.get("href", "")
                    if "result__a" in classe and href:
                        partes = urllib.parse.urlparse(href)
                        destino = urllib.parse.parse_qs(partes.query).get("uddg", [href])[0]
                        destino = urllib.parse.unquote(destino)
                        if destino.startswith("https://"):
                            self.links.append(destino)

        parser_links = Links()
        parser_links.feed(html_busca)
        links = list(dict.fromkeys(parser_links.links))[:5]
        if not links:
            print("\nDexbot: Nenhum resultado seguro foi encontrado.")
            return 0

        aprendidos = []
        total = 0
        for indice, link in enumerate(links, 1):
            if not endereco_publico(link):
                continue
            try:
                pedido = urllib.request.Request(link, headers={"User-Agent": "DexbotLocal/1.0"})
                with urllib.request.urlopen(pedido, timeout=15) as resposta:
                    tipo = resposta.headers.get("Content-Type", "").lower()
                    if "text/html" not in tipo and "text/plain" not in tipo:
                        continue
                    bruto = resposta.read(512000)
                total += len(bruto)
                if "text/html" in tipo:
                    extrator = ExtratorTexto()
                    extrator.feed(bruto.decode("utf-8", errors="ignore"))
                    texto = " ".join(extrator.partes)
                else:
                    texto = bruto.decode("utf-8", errors="ignore")
                texto = re.sub(r"\s+", " ", texto).strip()
                if len(texto) < 100:
                    continue
                for inicio in range(0, min(len(texto), 9000), 1200):
                    trecho = texto[inicio:inicio + 1200].strip()
                    if len(trecho) >= 100:
                        aprendidos.append({"arquivo": link, "trecho": trecho})
                self.barra_progresso(total, "Página " + str(indice) + "/5")
            except Exception:
                continue

        if aprendidos:
            antigos = []
            if os.path.exists(BASE_CONHECIMENTO):
                try:
                    with open(BASE_CONHECIMENTO, "r", encoding="utf-8") as arquivo:
                        antigos = json.load(arquivo)
                except (OSError, json.JSONDecodeError):
                    antigos = []
            self.salvar_conhecimento(aprendidos)
        print()
        print("Dexbot: Pesquisa concluída. Trechos guardados:", len(aprendidos))
        return total

    def modo_treinamento_web(self):
        print("\nMODO DE TREINAMENTO PELA INTERNET")
        print("A pesquisa fica em ciclo: informe assuntos quantas vezes quiser.")
        print("Digite PARAR para voltar ao chat. Depois use /voltar para pesquisar novamente.")
        total = 0
        while True:
            try:
                assunto = input("\nO que devo pesquisar? ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if assunto.lower() in {"parar", "/parar", "sair", "/sair"}:
                break
            if assunto:
                total += self.pesquisar_web(assunto)
                self.barra_progresso(total, "Total acumulado")
                print()
        print("Dexbot: Modo de pesquisa encerrado. Total recebido:", format(total / 1024, ".1f"), "KB.")

    def estudar_web_programacao(self, assunto=None):
        catalogo = {
            "html": [
                "HTML5 estrutura do documento elementos semânticos MDN",
                "HTML formulários validação inputs acessibilidade MDN",
                "HTML imagens áudio vídeo links tabelas MDN",
                "HTML acessibilidade landmarks ARIA boas práticas W3C"
            ],
            "css": [
                "CSS seletores cascata especificidade box model MDN",
                "CSS Flexbox Grid layout responsivo MDN",
                "CSS media queries unidades responsivas acessibilidade MDN",
                "CSS animações transições variáveis custom properties MDN"
            ],
            "javascript": [
                "JavaScript fundamentos variáveis tipos funções escopo MDN",
                "JavaScript DOM eventos manipulação elementos MDN",
                "JavaScript arrays objetos módulos promises async await MDN",
                "JavaScript fetch API HTTP JSON tratamento de erros MDN"
            ],
            "web": [
                "web performance Core Web Vitals web.dev",
                "segurança web XSS CSRF CSP MDN OWASP",
                "HTTP HTTPS cookies localStorage sessionStorage MDN",
                "debug JavaScript DevTools testes navegador MDN"
            ]
        }
        fontes = "site:developer.mozilla.org OR site:whatwg.org OR site:w3.org OR site:web.dev"
        if assunto:
            chave = normalizar(assunto)
            if any(p in chave for p in ("html", "css", "javascript", "js", "web")):
                temas = []
                for categoria, consultas in catalogo.items():
                    if categoria in chave or (categoria == "javascript" and "js" in chave):
                        temas.extend(consultas)
                if not temas:
                    temas = [assunto + " documentação oficial exemplos boas práticas"]
            else:
                temas = [
                    assunto + " documentação oficial MDN",
                    assunto + " exemplos boas práticas acessibilidade desempenho",
                    assunto + " erros comuns compatibilidade navegadores"
                ]
        else:
            temas = [q for grupo in catalogo.values() for q in grupo]

        print("\\nDEXBOT: ESTUDO WEB ESPECIALIZADO")
        print("Vou pesquisar documentação técnica e guardar os trechos no conhecimento local.")
        print("Consultas:", len(temas), "| Fontes priorizadas: MDN, WHATWG, W3C e web.dev")
        total = 0
        for indice, tema in enumerate(temas, 1):
            consulta = tema + " " + fontes
            print("\\n[" + str(indice) + "/" + str(len(temas)) + "] " + tema)
            total += self.pesquisar_web(consulta)
        print("\\nEstudo finalizado. Dados recebidos:", format(total / 1024, ".1f"), "KB.")
        print("Os trechos foram salvos em dexbot_conhecimento.json.")
        print("Observação: isso atualiza a memória pesquisável, não retreina os pesos do Qwen.")

    def pesquisar_wikipedia(self, assunto, total_estado):
        parametros = {
            "action": "query",
            "list": "search",
            "srsearch": assunto,
            "format": "json",
            "srlimit": 3
        }
        url = "https://pt.wikipedia.org/w/api.php?" + urllib.parse.urlencode(parametros)
        pedido = urllib.request.Request(url, headers={"User-Agent": "Dexbot/1.0 (local learning project)"})
        try:
            with urllib.request.urlopen(pedido, timeout=20) as resposta:
                dados = json.loads(resposta.read(500000).decode("utf-8"))
        except Exception as erro:
            print("\nDexbot: Falha ao pesquisar Wikipedia:", erro)
            return 0

        paginas = dados.get("query", {}).get("search", [])
        novos = []
        bytes_total = 0
        for pagina in paginas:
            titulo = pagina.get("title", "")
            parametros = {
                "action": "query",
                "prop": "extracts",
                "explaintext": 1,
                "exsectionformat": "plain",
                "titles": titulo,
                "format": "json",
                "redirects": 1
            }
            url_pagina = "https://pt.wikipedia.org/w/api.php?" + urllib.parse.urlencode(parametros)
            try:
                pedido = urllib.request.Request(url_pagina, headers={"User-Agent": "Dexbot/1.0 (local learning project)"})
                with urllib.request.urlopen(pedido, timeout=20) as resposta:
                    bruto = resposta.read(700000)
                bytes_total += len(bruto)
                conteudo = json.loads(bruto.decode("utf-8"))
                for item in conteudo.get("query", {}).get("pages", {}).values():
                    texto = item.get("extract", "").strip()
                    if len(texto) < 150:
                        continue
                    link = "https://pt.wikipedia.org/wiki/" + urllib.parse.quote(titulo.replace(" ", "_"))
                    for inicio in range(0, min(len(texto), 18000), 1200):
                        trecho = texto[inicio:inicio + 1200].strip()
                        if len(trecho) > 100:
                            novos.append({"arquivo": link, "trecho": trecho, "titulo": titulo})
                self.barra_progresso(total_estado[0] + bytes_total, titulo[:35])
            except Exception:
                continue

        if novos:
            self.salvar_conhecimento(novos)
        total_estado[0] += bytes_total
        return bytes_total

    def salvar_conhecimento(self, novos):
        antigos = []
        if os.path.exists(BASE_CONHECIMENTO):
            try:
                with open(BASE_CONHECIMENTO, "r", encoding="utf-8") as arquivo:
                    antigos = json.load(arquivo)
            except (OSError, json.JSONDecodeError):
                antigos = []
        existentes = {(d.get("arquivo"), d.get("trecho")) for d in antigos}
        for doc in novos:
            chave = (doc.get("arquivo"), doc.get("trecho"))
            if chave not in existentes:
                antigos.append(doc)
                existentes.add(chave)
        with open(BASE_CONHECIMENTO, "w", encoding="utf-8") as arquivo:
            json.dump(antigos, arquivo, ensure_ascii=False, indent=2)

    def modo_treinamento_wiki(self):
        assuntos = [
            "inteligência artificial",
            "aprendizado de máquina",
            "processamento de linguagem natural",
            "redes neurais artificiais",
            "linguagem humana",
            "comunicação",
            "gramática da língua portuguesa",
            "memória (aprendizagem)",
            "ciência da computação",
            "internet",
            "vocabulário da língua portuguesa",
            "sinônimos e antônimos",
            "significado das palavras",
            "ortografia da língua portuguesa",
            "verbos da língua portuguesa",
            "conjugação verbal português",
            "pontuação e acentuação",
            "interpretação de texto",
            "matemática básica",
            "operações matemáticas básicas",
            "ciências naturais",
            "geografia do Brasil",
            "história do Brasil",
            "segurança na internet",
            "programação para iniciantes"
        ]
        print("\nDEXBOT: Iniciando estudo automático na Wikipédia em português.")
        print("Vou pesquisar artigos, guardar trechos no PC e mostrar os KB recebidos.")
        total_estado = [0]
        for indice, assunto in enumerate(assuntos, 1):
            print("\nAssunto", indice, "de", len(assuntos), ":", assunto)
            self.pesquisar_wikipedia(assunto, total_estado)
        self.barra_progresso(total_estado[0], "Estudo inicial salvo")
        print("\nDexbot: Estudo inicial concluído. Total recebido:", format(total_estado[0] / 1024, ".1f"), "KB.")
        print("Dexbot: O conhecimento fica em dexbot_conhecimento.json.")

    def palavras_chave(self, texto):
        ignorar = {
            "que", "qual", "quais", "como", "para", "com", "uma", "sobre",
            "isso", "esse", "essa", "dos", "das", "por", "pelo", "pela",
            "nos", "nas", "tem", "ser", "foi", "sao", "the", "and",
            "quanto", "quanta", "quantos", "quantas", "porque", "porquê",
            "onde", "quando", "entao", "tambem", "mais", "menos", "muito",
            "muita", "muitos", "muitas", "voce", "voces", "ele", "ela",
            "eles", "elas", "meu", "minha", "seu", "sua", "estao", "esta",
            "estar", "seria", "pode", "podem", "fazer", "faz", "era",
            "aos", "de", "do", "da", "em", "no", "na", "um", "uns",
            "as", "os", "e", "ou", "a", "o"
        }
        palavras = normalizar(texto).split()
        resultado = []
        for palavra in palavras:
            if len(palavra) < 3 or palavra in ignorar:
                continue
            # Reduz algumas terminações comuns do português para aproximar
            # palavras relacionadas, sem alterar o texto original exibido.
            for final in ("amentos", "imento", "imentos", "acoes", "acao",
                          "mente", "idades", "idade", "adores", "adora",
                          "ando", "endo", "indo", "ados", "adas", "idos",
                          "idas", "es", "os", "as"):
                if len(palavra) > len(final) + 3 and palavra.endswith(final):
                    palavra = palavra[:-len(final)]
                    break
            resultado.append(palavra)
        return resultado

    def buscar_conhecimento(self, pergunta):
        if not os.path.exists(BASE_CONHECIMENTO):
            return None
        try:
            with open(BASE_CONHECIMENTO, "r", encoding="utf-8") as arquivo:
                documentos = json.load(arquivo)
        except (OSError, json.JSONDecodeError):
            return None

        consulta = set(self.palavras_chave(pergunta))
        # Perguntas vagas como "e quanto?" não devem puxar um artigo aleatório.
        if len(consulta) < 2:
            return None

        melhor = None
        melhor_pontuacao = 0.0
        melhor_frase = ""

        for doc in documentos:
            texto = doc.get("trecho", "")
            palavras_doc = set(self.palavras_chave(texto))
            if not palavras_doc:
                continue

            intersecao = consulta & palavras_doc
            cobertura = len(intersecao) / len(consulta)
            if cobertura < 0.35:
                continue

            frases = re.split(r"(?<=[.!?])\s+", texto)
            frases_boas = []
            for frase in frases:
                termos = set(self.palavras_chave(frase))
                pontos = len(consulta & termos)
                if pontos:
                    frases_boas.append((pontos / max(1, len(termos) ** 0.5), frase.strip()))

            if not frases_boas:
                continue
            frases_boas.sort(key=lambda item: item[0], reverse=True)
            pontuacao = cobertura + frases_boas[0][0] * 0.2
            if pontuacao > melhor_pontuacao:
                melhor_pontuacao = pontuacao
                melhor = doc
                melhor_frase = " ".join(frase for _, frase in frases_boas[:4])

        if melhor and melhor_pontuacao >= 0.45:
            origem = melhor.get("titulo") or melhor.get("arquivo", "base local")
            resposta = melhor_frase[:1000].strip()
            if resposta and resposta[-1] not in ".!?":
                resposta += "..."
            return "Encontrei informações relacionadas em " + origem + ":\n" + resposta
        return None

    def interpretar_exemplo(self, pergunta):
        consulta = set(self.palavras_chave(pergunta))
        if not consulta:
            return None
        melhor_item = None
        melhor_indice = 0.0
        for item in self.exemplos:
            palavras = set(self.palavras_chave(item.get("pergunta", "")))
            if not palavras:
                continue
            semelhanca = len(consulta & palavras) / max(1, len(consulta | palavras))
            if semelhanca > melhor_indice:
                melhor_indice = semelhanca
                melhor_item = item
        if melhor_item and melhor_indice >= 0.34:
            return melhor_item.get("resposta")
        return None

    def carregar_historico(self):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)
            return dados[-8:] if isinstance(dados, list) else []
        except (OSError, json.JSONDecodeError):
            return []

    def salvar_historico(self):
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as arquivo:
                json.dump(self.historico[-20:], arquivo, ensure_ascii=False, indent=2)
        except OSError as erro:
            print("Dexbot: Não consegui salvar a conversa:", erro)

    def responder(self, pergunta):
        # Recupera um trecho da memória local para dar contexto ao modelo.
        contexto = self.buscar_conhecimento(pergunta)
        sistema = (
            "Você é Dexbot, uma assistente especializada em desenvolvimento web. "
            "Sua especialidade inclui HTML5, CSS3, JavaScript moderno, DOM, APIs do navegador, JSON, acessibilidade, responsividade, desempenho, segurança web, depuração, HTTP, Git e publicação de sites. "
            "Responda sempre em português do Brasil, com explicações claras e adequadas a iniciantes. "
            "Quando pedirem código, entregue uma solução funcional, completa e organizada, sem remover recursos existentes. "
            "Prefira tecnologias nativas da web; use bibliotecas ou frameworks somente quando forem pedidos ou realmente necessários. "
            "Use boas práticas atuais e diferencie recursos padronizados de recursos experimentais. "
            "Quando houver acesso à memória local, use-a como referência, mas confira coerência e não trate trechos antigos como verdade absoluta. "
            "Para pesquisar ou recomendar APIs, prefira documentação oficial: MDN Web Docs, WHATWG, W3C, web.dev e documentação oficial dos projetos. "
            "Não invente métodos, propriedades, atributos, APIs, compatibilidade ou resultados de testes. Quando não tiver certeza, diga isso e indique como verificar. "
            "Explique brevemente onde colocar cada arquivo e como executar. "
            "Em projetos com vários arquivos, identifique cada arquivo separadamente e mantenha cada bloco apenas com a linguagem daquele arquivo. "
            "HTML deve conter apenas HTML; CSS deve conter apenas CSS; JavaScript deve conter apenas JavaScript. "
            "Nunca coloque tags HTML como </script> ou </html> dentro de um arquivo .js. Nunca coloque cercas Markdown dentro do código. "
            "Confira se IDs, classes, seletores, nomes de arquivos e funções realmente correspondem entre os arquivos. "
            "Confira se o comportamento pedido foi aplicado ao elemento correto, e não a outro elemento por engano. "
            "Nunca entregue código pela metade nem use reticências para substituir partes necessárias. Não force três arquivos se o pedido precisar de apenas um. "
            "Se o projeto for grande demais para uma resposta, divida em partes numeradas e informe claramente o que falta. "
            "Não diga que executou ou testou o código se não executou. "
            "Se faltar informação essencial, faça uma pergunta curta."
        )
        if contexto:
            sistema += "\n\nTrecho da memória local que pode ajudar (verifique se é relevante):\n" + contexto[:3500]

        mensagens = [{"role": "system", "content": sistema}]
        mensagens.extend(self.historico[-6:])
        mensagens.append({"role": "user", "content": pergunta})

        corpo = {
            "model": OLLAMA_MODEL,
            "messages": mensagens,
            "stream": True,
            "keep_alive": "30m",
            "options": {"temperature": 0.2, "num_ctx": 3072, "num_predict": 1024, "num_thread": 4}
        }
        pedido = urllib.request.Request(
            OLLAMA_CHAT_URL,
            data=json.dumps(corpo).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            partes = []
            with urllib.request.urlopen(pedido, timeout=180) as resposta:
                for linha in resposta:
                    if not linha.strip():
                        continue
                    evento = json.loads(linha.decode("utf-8"))
                    trecho = evento.get("message", {}).get("content", "")
                    if trecho:
                        print(trecho, end="", flush=True)
                        partes.append(trecho)
            texto = "".join(partes).strip()
            if not texto:
                print("Não consegui montar uma resposta agora. Pode tentar novamente?")
                return ""
            self.historico.append({"role": "user", "content": pergunta})
            self.historico.append({"role": "assistant", "content": texto})
            self.historico = self.historico[-6:]
            self.salvar_historico()
            return texto
        except urllib.error.URLError:
            aviso = (
                "Não consegui conectar ao Ollama. Abra o Ollama no Windows e "
                "confirme que o modelo " + OLLAMA_MODEL + " foi instalado. "
                "Depois tente novamente."
            )
            print(aviso)
            return ""
        except Exception as erro:
            print("Tive um erro ao conversar com o modelo local:", erro)
            return ""

    def ensinar(self):
        pergunta = input("Nova pergunta: ").strip()
        resposta = input("Resposta que devo aprender: ").strip()
        if not pergunta or not resposta:
            print("Dexbot: Pergunta e resposta não podem ficar vazias.")
            return
        self.exemplos.append({"pergunta": pergunta, "resposta": resposta})
        self.salvar_dados()
        self.treinar()

    def iniciar(self):
        print("\n" + "=" * 48)
        print("             DEXBOT - IA PROPRIA V1")
        print("=" * 48)
        print("IA conversacional local: Ollama + " + OLLAMA_MODEL)
        print("A conversa fica salva localmente em dexbot_conversa.json.")
        print("Digite /ajuda para ver os comandos.\n")

        while True:
            try:
                mensagem = input("Você: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nDexbot: Encerrando.")
                break

            if not mensagem:
                continue

            comando = mensagem.lower()

            if comando == "/sair":
                print("Dexbot: Até mais!")
                break
            elif comando == "/ajuda":
                print("\nCOMANDOS")
                print("/ensinar  - adicionar pergunta e resposta")
                print("/treinar  - treinar novamente a rede neural")
                print("/memoria  - mostrar quantidade de exemplos")
                print("/limparconversa - apagar o histórico de conversa")
                print("/pesquisar - estudar arquivos de uma pasta escolhida")
                print("/treinarweb - iniciar pesquisa contínua na internet")
                print("/voltar - voltar ao modo de pesquisa contínua")
                print("/wiki - estudar novamente a Wikipédia em português")
                print("/sair - fechar a Dexbot\n")
            elif comando == "/ensinar":
                self.ensinar()
            elif comando == "/treinar":
                self.treinar()
            elif comando == "/memoria":
                print("Dexbot: Tenho", len(self.exemplos), "exemplos de treinamento e", len(self.historico), "mensagens recentes salvas.")
            elif comando == "/limparconversa":
                self.historico = []
                self.salvar_historico()
                print("Dexbot: Histórico da conversa apagado.")
            elif comando == "/pesquisar":
                self.pesquisar_pasta()
            elif comando in {"/treinarweb", "/pesquisarcontinuo", "/voltar"}:
                self.modo_treinamento_web()
            elif comando == "/parar":
                print("Dexbot: Você já está no chat. Use /voltar para retomar a pesquisa.")
            elif comando == "/estudarweb":
                tema = input("Tema (HTML, CSS, JavaScript, web ou assunto específico; Enter para estudar tudo): ").strip()
                self.estudar_web_programacao(tema or None)
            elif comando == "/wiki":
                self.modo_treinamento_wiki()
            else:
                print("Dexbot: ", end="", flush=True)
                self.responder(mensagem)
                print()

if __name__ == "__main__":
    Dexbot().iniciar()
