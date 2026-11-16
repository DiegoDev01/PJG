import subprocess
from pathlib import Path


def verificar_ffmpeg():
    """Verifica se o FFmpeg está instalado e acessível."""

    try:
        resultado = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=10
        )

        return resultado.returncode == 0

    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def obter_duracao_audio(caminho):
    """Retorna a duração do áudio em segundos."""

    comando = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(caminho)
    ]

    resultado = subprocess.run(
        comando,
        capture_output=True,
        text=True,
        timeout=30
    )

    if resultado.returncode != 0:
        raise RuntimeError("Não foi possível identificar a duração do áudio.")

    return float(resultado.stdout.strip())


def preparar_narracao(
    entrada,
    saida,
    normalizar=True,
    remover_silencios=False
):
    """
    Prepara a narração para o projeto.

    entrada: arquivo original.
    saida: arquivo WAV de destino.
    normalizar: ajusta o volume.
    remover_silencios: remove pausas longas.
    """

    entrada = Path(entrada)
    saida = Path(saida)

    if not entrada.exists():
        raise FileNotFoundError(
            f"Arquivo de narração não encontrado: {entrada}"
        )

    if not verificar_ffmpeg():
        raise RuntimeError("FFmpeg não encontrado no sistema.")

    if entrada.resolve() == saida.resolve():
        raise ValueError("O arquivo de saída deve ser diferente do original.")

    saida.parent.mkdir(parents=True, exist_ok=True)

    filtros = []

    if remover_silencios:
        filtros.append(
            "silenceremove="
            "stop_periods=-1:"
            "stop_duration=0.35:"
            "stop_threshold=-38dB"
        )

    if normalizar:
        filtros.append(
            "loudnorm=I=-16:TP=-1.5:LRA=11"
        )

    filtros.append(
        "aresample=48000"
    )

    filtros.append(
        "aformat=sample_fmts=s16:channel_layouts=stereo"
    )

    comando = [
        "ffmpeg",
        "-y",
        "-i", str(entrada),
        "-vn",
        "-af", ",".join(filtros),
        "-c:a", "pcm_s16le",
        str(saida)
    ]

    resultado = subprocess.run(
        comando,
        capture_output=True,
        text=True
    )

    if resultado.returncode != 0:
        raise RuntimeError(
            "Falha ao preparar a narração:\n"
            + resultado.stderr[-3000:]
        )

    if not saida.exists() or saida.stat().st_size == 0:
        raise RuntimeError("O arquivo de áudio não foi gerado corretamente.")

    duracao = obter_duracao_audio(saida)

    return {
        "sucesso": True,
        "arquivo": str(saida),
        "duracao": round(duracao, 2),
        "formato": "WAV",
        "frequencia": "48000 Hz",
        "canais": "Estéreo"
    }