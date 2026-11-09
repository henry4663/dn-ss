import json
import math
import os
import random
import re
import unicodedata
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "dexbot_dados.json")
MODEL_FILE = os.path.join(BASE_DIR, "dexbot_modelo.json")
BASE_CONHECIMENTO = os.path.join(BASE_DIR, "dexbot_conhecimento.json")
EXTENSOES_TEXTO = {".txt", ".md", ".py", ".html", ".css", ".js", ".json", ".csv", ".xml", ".yml", ".yaml", ".ini", ".log"}

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

    def buscar_conhecimento(self, pergunta):
        if not os.path.exists(BASE_CONHECIMENTO):
            return None
        try:
            with open(BASE_CONHECIMENTO, "r", encoding="utf-8") as arquivo:
                documentos = json.load(arquivo)
        except (OSError, json.JSONDecodeError):
            return None

        palavras = set(normalizar(pergunta).split())
        palavras = {p for p in palavras if len(p) > 2 and p not in {
            "que", "qual", "quais", "como", "para", "com", "uma", "sobre",
            "isso", "esse", "essa", "dos", "das", "por", "the", "and"
        }}
        if not palavras:
            return None

        melhor = None
        maior_pontuacao = 0
        for doc in documentos:
            texto = doc.get("trecho", "")
            tokens = set(normalizar(texto).split())
            pontuacao = len(palavras & tokens)
            if pontuacao > maior_pontuacao:
                maior_pontuacao = pontuacao
                melhor = doc
        if melhor and maior_pontuacao >= 2:
            trecho = melhor["trecho"]
            if len(trecho) > 900:
                trecho = trecho[:900] + "..."
            return "Encontrei isso em " + melhor["arquivo"] + ":\n" + trecho
        return None

    def responder(self, pergunta):
        conhecimento = self.buscar_conhecimento(pergunta)
        if conhecimento:
            return conhecimento
        if not self.rede:
            return "Ainda não tenho dados suficientes. Use /ensinar."

        entrada = vetorizar(pergunta, self.vocabulario)
        if not any(entrada):
            return "Não reconheci essas palavras. Você pode me ensinar com /ensinar."

        probabilidades, _ = self.rede.prever(entrada)
        melhor = max(range(len(probabilidades)), key=probabilidades.__getitem__)
        confianca = probabilidades[melhor]

        if confianca < 0.48:
            return "Ainda não aprendi a responder isso. Você pode me ensinar com /ensinar."

        return self.respostas[melhor]

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
        print("Rede neural criada em Python puro. Sem API e sem internet.")
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
                print("/pesquisar - estudar arquivos de uma pasta escolhida")
                print("/sair     - fechar a Dexbot\n")
            elif comando == "/ensinar":
                self.ensinar()
            elif comando == "/treinar":
                self.treinar()
            elif comando == "/memoria":
                print("Dexbot: Tenho", len(self.exemplos), "exemplos de treinamento.")
            elif comando == "/pesquisar":
                self.pesquisar_pasta()
            else:
                print("Dexbot:", self.responder(mensagem))

if __name__ == "__main__":
    Dexbot().iniciar()
