import json
import subprocess
from pathlib import Path

MODOS_PRODUCAO = {"narracao_roteiro", "narracao_livre", "gameplay"}

EXTENSOES_VIDEO = {".mp4", ".mov", ".mkv", ".avi", ".webm"}

EXTENSOES_AUDIO = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}


def verificar_ffprobe():
    """Verifica se o FFprobe está instalado e acessível."""

    try:
        resultado = subprocess.run(
            ["ffprobe", "-version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )

        return resultado.returncode == 0

    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def analisar_arquivo(caminho):
    """Obtém informações técnicas de um arquivo de mídia."""

    caminho = Path(caminho)

    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    comando = [
        "ffprobe",
        "-v",
        "error",
        "-show_streams",
        "-show_format",
        "-of",
        "json",
        str(caminho),
    ]

    resultado = subprocess.run(
        comando, check=False, capture_output=True, text=True, timeout=30
    )

    if resultado.returncode != 0:
        raise RuntimeError(
            f"Não foi possível analisar {caminho.name}: {resultado.stderr.strip()}"
        )

    dados = json.loads(resultado.stdout)

    streams = dados.get("streams", [])

    video = next((s for s in streams if s.get("codec_type") == "video"), None)

    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)

    return {
        "arquivo": caminho.name,
        "duracao": float(dados.get("format", {}).get("duration", 0)),
        "tem_video": video is not None,
        "tem_audio": audio is not None,
        "largura": video.get("width") if video else None,
        "altura": video.get("height") if video else None,
        "codec_video": video.get("codec_name") if video else None,
        "codec_audio": audio.get("codec_name") if audio else None,
    }


def validar_producao(modo, gameplay, narracao=None, roteiro=None):
    """
    Valida os arquivos e as condições de produção.

    Modos:
    - narracao_roteiro
    - narracao_livre
    - gameplay
    """

    erros = []
    avisos = []
    arquivos = {}

    if modo not in MODOS_PRODUCAO:
        erros.append(f"Modo de produção inválido: {modo}")

    if not verificar_ffprobe():
        erros.append("FFprobe não encontrado. Verifique a instalação do FFmpeg.")

        return {
            "aprovado": False,
            "erros": erros,
            "avisos": avisos,
            "arquivos": arquivos,
        }

    # Verificar gameplay
    try:
        caminho_gameplay = Path(gameplay)

        if caminho_gameplay.suffix.lower() not in EXTENSOES_VIDEO:
            erros.append("Formato de gameplay n\u00e3o suportado.")
        else:
            info = analisar_arquivo(caminho_gameplay)

            if not info["tem_video"]:
                erros.append("O arquivo selecionado n\u00e3o possui v\u00eddeo.")

            elif info["duracao"] <= 0:
                erros.append(
                    "A gameplay n\u00e3o possui dura\u00e7\u00e3o v\u00e1lida."
                )

            elif (
                not info["largura"]
                or not info["altura"]
                or info["largura"] <= 0
                or info["altura"] <= 0
            ):
                erros.append("A gameplay possui resolu\u00e7\u00e3o inv\u00e1lida.")

            arquivos["gameplay"] = info

            if not info["tem_audio"]:
                avisos.append("A gameplay n\u00e3o possui \u00e1udio original.")

    except (
        OSError,
        subprocess.TimeoutExpired,
        RuntimeError,
        ValueError,
        TypeError,
    ) as erro:
        erros.append(f"Erro na gameplay: {erro}")

    # Verificar narra\u00e7\u00e3o
    if modo in {"narracao_roteiro", "narracao_livre"}:
        if not narracao:
            erros.append("Este modo exige um arquivo de narração.")

        else:
            try:
                caminho_audio = Path(narracao)

                if caminho_audio.suffix.lower() not in EXTENSOES_AUDIO:
                    erros.append("Formato de narração não suportado.")
                else:
                    info = analisar_arquivo(caminho_audio)

                    if not info["tem_audio"]:
                        erros.append("O arquivo de narração não possui áudio.")

                    elif info["duracao"] <= 0:
                        erros.append("A narração não possui duração válida.")

                    arquivos["narracao"] = info

            except (
                OSError,
                subprocess.TimeoutExpired,
                RuntimeError,
                ValueError,
                TypeError,
            ) as erro:
                erros.append(f"Erro na narração: {erro}")

    # Verificar roteiro
    if modo == "narracao_roteiro":
        if not roteiro:
            erros.append("O modo com roteiro exige um arquivo de texto.")

        else:
            caminho_roteiro = Path(roteiro)

            if not caminho_roteiro.exists():
                erros.append("Arquivo de roteiro não encontrado.")

            elif caminho_roteiro.suffix.lower() != ".txt":
                erros.append("O roteiro precisa estar no formato TXT.")

            else:
                try:
                    conteudo = caminho_roteiro.read_text(encoding="utf-8-sig").strip()

                    if not conteudo:
                        erros.append("O roteiro está vazio.")

                    else:
                        arquivos["roteiro"] = {
                            "arquivo": caminho_roteiro.name,
                            "caracteres": len(conteudo),
                        }

                except UnicodeDecodeError:
                    erros.append("Não foi possível ler o roteiro em UTF-8.")

    return {
        "aprovado": len(erros) == 0,
        "modo": modo,
        "erros": erros,
        "avisos": avisos,
        "arquivos": arquivos,
    }


def exibir_resultado(resultado):
    """Exibe o resultado da validação no terminal."""

    print("\n========== VALIDAÇÃO PJG ==========")

    print(f"Modo: {resultado.get('modo', 'Não identificado')}")

    if resultado["aprovado"]:
        print("\nSTATUS: APROVADO")
    else:
        print("\nSTATUS: REPROVADO")

    for erro in resultado["erros"]:
        print(f"[ERRO] {erro}")

    for aviso in resultado["avisos"]:
        print(f"[AVISO] {aviso}")

    print("\nArquivos analisados:")

    for nome, dados in resultado["arquivos"].items():
        print(f"\n{nome.upper()}:")
        for chave, valor in dados.items():
            print(f"  {chave}: {valor}")

    print("\n===================================")
