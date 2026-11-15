import os
import sys
import random
import subprocess
import argparse
import re
from difflib import SequenceMatcher
from faster_whisper import WhisperModel

BASE_DIR = r"D:\PJG"
DIR_GAMEPLAY = os.path.join(BASE_DIR, "01_gameplay_bruta")
DIR_NARRACAO = os.path.join(BASE_DIR, "02_narracao_e_roteiro")
DIR_LEGENDAS = os.path.join(BASE_DIR, "03_legendas_sync")
DIR_PRONTOS = os.path.join(BASE_DIR, "04_cortes_prontos")
FONTE_PATH = os.path.join(BASE_DIR, "05_assets", "fontes", "Montserrat-ExtraBold.ttf")

def cortar_silencios(audio_in, audio_out):
    print("1. Cortando silencios da narracao (ritmo dinamico Shorts)...")
    cmd = [
        "ffmpeg", "-y", "-i", audio_in,
        "-af", "silenceremove=stop_periods=-1:stop_duration=0.35:stop_threshold=-38dB,loudnorm=I=-14:TP=-1.5:LRA=11",
        audio_out
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def obter_duracao(arquivo):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", arquivo]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())

def alinhar_com_roteiro(palavras_whisper, texto_roteiro):
    palavras_oficiais = re.findall(r"\b[\w'-]+\b", texto_roteiro)
    if not palavras_oficiais or not palavras_whisper:
        return palavras_whisper

    w_norm = [w["word"].strip().lower() for w in palavras_whisper]
    r_norm = [p.lower() for p in palavras_oficiais]

    matcher = SequenceMatcher(None, w_norm, r_norm)
    alinhadas = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                item = palavras_whisper[i1 + k].copy()
                item["word"] = palavras_oficiais[j1 + k]
                alinhadas.append(item)
        elif tag == "replace":
            t_inicio = palavras_whisper[i1]["start"]
            t_fim = palavras_whisper[i2 - 1]["end"]
            qtd = j2 - j1
            passo = (t_fim - t_inicio) / max(qtd, 1)
            for k in range(qtd):
                alinhadas.append({
                    "word": palavras_oficiais[j1 + k],
                    "start": t_inicio + k * passo,
                    "end": t_inicio + (k + 1) * passo
                })
        elif tag == "delete":
            for k in range(i1, i2):
                alinhadas.append(palavras_whisper[k])
    return alinhadas

def formatar_tempo_ass(segundos):
    h = int(segundos // 3600)
    m = int((segundos % 3600) // 60)
    s = int(segundos % 60)
    cs = int((segundos - int(segundos)) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def gerar_legenda_ass(palavras, caminho_ass, hook_texto=""):
    print("3. Gerando legendas sincronizadas + Safe Zone Shorts...")
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Legenda,Montserrat ExtraBold,84,&H0000D7FF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,2,5,50,50,580,1
Style: Hook,Montserrat ExtraBold,64,&H00FFFFFF,&H00FFFFFF,&H000000FF,&H80000000,-1,0,0,0,100,100,0,0,3,12,0,5,60,60,1450,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    linhas = []
    if hook_texto:
        linhas.append(f"Dialogue: 1,0:00:00.00,0:00:05.00,Hook,,0,0,0,,{{\\pos(540,480)}}{hook_texto.upper()}")

    bloco = []
    for p in palavras:
        bloco.append(p)
        if len(bloco) >= 3 or p["word"].endswith((".", "!", "?")):
            ini = formatar_tempo_ass(bloco[0]["start"])
            fim = formatar_tempo_ass(bloco[-1]["end"])
            texto = " ".join([x["word"].upper() for x in bloco])
            linhas.append(f"Dialogue: 0,{ini},{fim},Legenda,,0,0,0,,{{\\pos(540,1320)}}{texto}")
            bloco = []
    if bloco:
        ini = formatar_tempo_ass(bloco[0]["start"])
        fim = formatar_tempo_ass(bloco[-1]["end"])
        texto = " ".join([x["word"].upper() for x in bloco])
        linhas.append(f"Dialogue: 0,{ini},{fim},Legenda,,0,0,0,,{{\\pos(540,1320)}}{texto}")

    with open(caminho_ass, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(linhas))

def montar_gameplay_dinamica(gameplay_path, duracao_alvo, temp_video, inicio_manual=None):
    print("4. Montando cortes dinamicos da gameplay (troca a cada 3.5s)...")
    duracao_bruta = obter_duracao(gameplay_path)
    if inicio_manual:
        cmd = [
            "ffmpeg", "-y", "-ss", inicio_manual, "-t", str(duracao_alvo),
            "-i", gameplay_path, "-c:v", "h264_amf", "-c:a", "aac", temp_video
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return

    tempo_acumulado = 0.0
    lista_txt = os.path.join(DIR_LEGENDAS, "concat_list.txt")
    clipes_temp = []
    idx = 0

    try:
        while tempo_acumulado < duracao_alvo:
            dur_clipe = min(3.5, duracao_alvo - tempo_acumulado)
            max_start = max(0, duracao_bruta - dur_clipe - 1)
            start_rand = random.uniform(0, max_start)
            clipe_nome = os.path.join(DIR_LEGENDAS, f"temp_clip_{idx}.mp4")
            clipes_temp.append(clipe_nome)

            cmd_clip = [
                "ffmpeg", "-y", "-ss", f"{start_rand:.2f}", "-t", f"{dur_clipe:.2f}",
                "-i", gameplay_path, "-c:v", "h264_amf", "-b:v", "15M", "-r", "60",
                "-c:a", "aac", "-ar", "44100", clipe_nome
            ]
            subprocess.run(cmd_clip, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            tempo_acumulado += dur_clipe
            idx += 1

        with open(lista_txt, "w", encoding="utf-8") as f:
            for c in clipes_temp:
                f.write(f"file '{c}'\n")

        cmd_concat = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lista_txt, "-c", "copy", temp_video]
        subprocess.run(cmd_concat, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        for c in clipes_temp:
            if os.path.exists(c):
                os.remove(c)
        if os.path.exists(lista_txt):
            os.remove(lista_txt)

def main():
    parser = argparse.ArgumentParser(description="Editor Shorts/TikTok/Reels - GTA 6")
    parser.add_argument("--nome", required=True, help="Nome base dos arquivos (ex: corte01)")
    parser.add_argument("--gameplay", required=True, help="Video na pasta 01_gameplay_bruta (ex: gameplay.mp4)")
    parser.add_argument("--inicio", default=None, help="Opcional: tempo fixo (ex: 00:02:15). Se vazio, faz cortes automaticos a cada 3.5s")
    parser.add_argument("--hook", default="", help="Opcional: titulo chamativo nos primeiros 5s")
    args = parser.parse_args()

    audio_orig = None
    for ext in [".mp3", ".wav", ".m4a"]:
        cand = os.path.join(DIR_NARRACAO, args.nome + ext)
        if os.path.exists(cand):
            audio_orig = cand
            break

    roteiro_path = os.path.join(DIR_NARRACAO, args.nome + ".txt")
    gameplay_path = os.path.join(DIR_GAMEPLAY, args.gameplay)

    if not audio_orig or not os.path.exists(roteiro_path) or not os.path.exists(gameplay_path):
        print("Erro: Verifique se o audio, o .txt do roteiro e a gameplay existem nas pastas.")
        sys.exit(1)

    audio_limpo = os.path.join(DIR_LEGENDAS, f"{args.nome}_limpo.wav")
    cortar_silencios(audio_orig, audio_limpo)
    duracao_final = obter_duracao(audio_limpo)

    if duracao_final > 59.5:
        print(f"AVISO: Sua narracao tem {duracao_final:.1f}s. Para YouTube Shorts, mantenha abaixo de 59s!")

    print("2. Sincronizando voz com roteiro...")
    model = WhisperModel("small", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio_limpo, language="pt", word_timestamps=True)
    palavras_whisper = []
    for seg in segments:
        for w in seg.words:
            palavras_whisper.append({"word": w.word.strip(), "start": w.start, "end": w.end})

    with open(roteiro_path, "r", encoding="utf-8") as f:
        texto_roteiro = f.read()

    palavras_finais = alinhar_com_roteiro(palavras_whisper, texto_roteiro)
    ass_path = os.path.join(DIR_LEGENDAS, f"{args.nome}.ass")
    gerar_legenda_ass(palavras_finais, ass_path, args.hook)

    gameplay_temp = os.path.join(DIR_LEGENDAS, f"{args.nome}_gp_temp.mp4")
    montar_gameplay_dinamica(gameplay_path, duracao_final, gameplay_temp, args.inicio)

    print("5. Renderizando Shorts final na RX 7600 (1080x1920 60fps)...")
    video_saida = os.path.join(DIR_PRONTOS, f"{args.nome}_shorts.mp4")
    ass_escapado = ass_path.replace("\\", "/").replace(":", "\\:")
    font_dir = os.path.dirname(FONTE_PATH).replace("\\", "/").replace(":", "\\:")

    filtro_complexo = (
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=35,eq=brightness=-0.15[bg];"
        f"[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
        f"[bg][fg]overlay=(W-w)/2:(H-h)/2,ass='{ass_escapado}':fontsdir='{font_dir}'[vout];"
        f"[0:a]volume=-22dB[agame];"
        f"[1:a]volume=-3dB[avoz];"
        f"[agame][avoz]amix=inputs=2:duration=shortest:normalize=0[aout]"
    )

    cmd_render = [
        "ffmpeg", "-y",
        "-i", gameplay_temp,
        "-i", audio_limpo,
        "-filter_complex", filtro_complexo,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "h264_amf", "-usage", "transcoding", "-quality", "speed", "-rc", "cqp", "-qp_i", "19", "-qp_p", "19",
        "-r", "60", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        video_saida
    ]
    subprocess.run(cmd_render, check=True)
    if os.path.exists(gameplay_temp):
        os.remove(gameplay_temp)
    print(f"PRONTO! Seu video vertical esta em: {video_saida}")

if __name__ == "__main__":
    main()
