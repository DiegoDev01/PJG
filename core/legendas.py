from pathlib import Path


def transcrever_audio(
    caminho_audio, modelo="small", idioma="pt", dispositivo="cpu", compute_type="int8"
):
    """
    Transcreve um áudio usando Faster-Whisper.
    Retorna os segmentos e as palavras com seus timestamps.
    """

    caminho_audio = Path(caminho_audio)

    if not caminho_audio.exists():
        raise FileNotFoundError(f"Áudio não encontrado: {caminho_audio}")

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise RuntimeError(
            "Faster-Whisper não está instalado. Execute: pip install faster-whisper"
        )

    print(f"\nCarregando modelo Whisper: {modelo}")

    whisper = WhisperModel(modelo, device=dispositivo, compute_type=compute_type)

    print("Iniciando transcrição...")

    segmentos, informacoes = whisper.transcribe(
        str(caminho_audio), language=idioma, word_timestamps=True, vad_filter=False
    )

    resultado = {
        "idioma": informacoes.language,
        "duracao": informacoes.duration,
        "palavras": [],
        "texto_completo": "",
    }

    textos = []

    for segmento in segmentos:
        textos.append(segmento.text.strip())

        if not segmento.words:
            continue

        for palavra in segmento.words:
            if palavra.start is None or palavra.end is None:
                continue

            texto = palavra.word.strip()

            if not texto:
                continue

            resultado["palavras"].append(
                {
                    "texto": texto,
                    "inicio": float(palavra.start),
                    "fim": float(palavra.end),
                }
            )

    resultado["texto_completo"] = " ".join(textos)

    if not resultado["palavras"]:
        raise RuntimeError("Nenhuma palavra foi identificada na transcrição.")

    print(
        f"Transcrição concluída: {len(resultado['palavras'])} palavras identificadas."
    )

    return resultado


def formatar_tempo_ass(segundos):
    """Converte segundos para o formato de tempo ASS."""

    segundos = max(0, segundos)

    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segundos_inteiros = int(segundos % 60)

    centesimos = round((segundos - int(segundos)) * 100)

    if centesimos >= 100:
        segundos_inteiros += 1
        centesimos = 0

    if segundos_inteiros >= 60:
        minutos += 1
        segundos_inteiros = 0

    if minutos >= 60:
        horas += 1
        minutos = 0

    return f"{horas}:{minutos:02d}:{segundos_inteiros:02d}.{centesimos:02d}"


def agrupar_palavras(palavras, max_palavras=3):
    """
    Agrupa palavras em pequenos blocos para legendas dinâmicas.
    Respeita pontuação e limite de palavras.
    """

    blocos = []
    atual = []

    for palavra in palavras:
        atual.append(palavra)

        texto = palavra["texto"]

        terminou_frase = texto.endswith((".", "!", "?", ":", ";"))

        if len(atual) >= max_palavras or terminou_frase:
            blocos.append(atual)
            atual = []

    if atual:
        blocos.append(atual)

    return blocos


def gerar_legendas_ass(
    transcricao, caminho_saida, fonte="Montserrat ExtraBold", tamanho=84, max_palavras=3
):
    """
    Gera arquivo ASS vertical 1080x1920.
    Legendas amarelas, contorno preto e centralizadas.
    """

    caminho_saida = Path(caminho_saida)
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    palavras = transcricao.get("palavras", [])

    if not palavras:
        raise ValueError("A transcrição não contém palavras.")

    blocos = agrupar_palavras(palavras, max_palavras=max_palavras)

    cabecalho = f"""[Script Info]
Title: Legendas PJG
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{fonte},{tamanho},&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,1,5,1,5,60,60,600,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    linhas = [cabecalho]

    for bloco in blocos:
        inicio = bloco[0]["inicio"]
        fim = bloco[-1]["fim"]

        texto = " ".join(palavra["texto"] for palavra in bloco)

        texto = texto.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")

        # Centralização na região inferior do vídeo.
        texto_ass = f"{{\\an5\\pos(540,1320)}}{texto}"

        linha = (
            f"Dialogue: 0,"
            f"{formatar_tempo_ass(inicio)},"
            f"{formatar_tempo_ass(fim)},"
            f"Default,,0,0,0,,{texto_ass}\n"
        )

        linhas.append(linha)

    with open(caminho_saida, "w", encoding="utf-8-sig") as arquivo:
        arquivo.writelines(linhas)

    return {
        "sucesso": True,
        "arquivo": str(caminho_saida),
        "quantidade_palavras": len(palavras),
        "quantidade_legendas": len(blocos),
    }
