DEXBOT - IA PROPRIA V1

Roda localmente no Windows, sem APIs, servicos pagos ou bibliotecas externas.

REQUISITOS
- Windows 10 ou 11
- Python 3.10 ou superior

ABRIR
Execute iniciar_dexbot.bat ou rode no CMD: py -3 dexbot.py

COMANDOS
- /ensinar: adiciona uma pergunta e resposta e treina novamente.
- /treinar: treina novamente com todos os exemplos salvos.
- /memoria: mostra quantos exemplos existem.
- /ajuda: mostra os comandos.
- /sair: fecha o programa.

ARQUIVOS LOCAIS
- dexbot_dados.json: exemplos ensinados.
- dexbot_modelo.json: pesos da rede neural treinada.

COMO FUNCIONA
A V1 implementa uma pequena rede neural feed-forward com uma camada oculta, ReLU e softmax, usando apenas a biblioteca padrao do Python. Ela classifica perguntas em respostas ensinadas. E um primeiro experimento de aprendizado supervisionado, nao um modelo de linguagem geral: nao possui conhecimento amplo, nao entende imagens e pode errar com perguntas diferentes das usadas no treinamento. O treinamento ocorre localmente; nenhuma mensagem e enviada para a internet.
