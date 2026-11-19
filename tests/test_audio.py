import subprocess

import pytest

from core import audio


def criar_audio(tmp_path):
    arquivo = tmp_path / "narracao.mp3"
    arquivo.write_bytes(b"audio de teste")
    return arquivo


def test_verificar_ffmpeg_disponivel(monkeypatch):
    monkeypatch.setattr(
        audio.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, stdout="FFmpeg", stderr=""
        ),
    )

    assert audio.verificar_ffmpeg() is True


@pytest.mark.parametrize(
    "erro", [FileNotFoundError(), subprocess.TimeoutExpired("ffmpeg", 10)]
)
def test_verificar_ffmpeg_indisponivel(monkeypatch, erro):
    def executar(*args, **kwargs):
        raise erro

    monkeypatch.setattr(audio.subprocess, "run", executar)

    assert audio.verificar_ffmpeg() is False


def test_obter_duracao_audio(monkeypatch):
    monkeypatch.setattr(
        audio.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, stdout="42.75", stderr=""
        ),
    )

    assert audio.obter_duracao_audio("audio.wav") == 42.75


def test_obter_duracao_audio_falha(monkeypatch):
    monkeypatch.setattr(
        audio.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 1, stdout="", stderr="erro"
        ),
    )

    with pytest.raises(RuntimeError):
        audio.obter_duracao_audio("audio.wav")


def test_narracao_inexistente(tmp_path):
    with pytest.raises(FileNotFoundError):
        audio.preparar_narracao(tmp_path / "inexistente.mp3", tmp_path / "saida.wav")


def test_ffmpeg_indisponivel(monkeypatch, tmp_path):
    entrada = criar_audio(tmp_path)

    monkeypatch.setattr(audio, "verificar_ffmpeg", lambda: False)

    with pytest.raises(RuntimeError, match="FFmpeg"):
        audio.preparar_narracao(entrada, tmp_path / "saida.wav")


def test_entrada_e_saida_iguais(tmp_path):
    entrada = criar_audio(tmp_path)

    with pytest.raises(ValueError):
        audio.preparar_narracao(entrada, entrada)


def test_preparar_narracao_com_sucesso(monkeypatch, tmp_path):
    entrada = criar_audio(tmp_path)
    saida = tmp_path / "resultado" / "narracao.wav"

    monkeypatch.setattr(audio, "verificar_ffmpeg", lambda: True)

    comandos = []

    def executar(comando, **kwargs):
        comandos.append(comando)

        if comando[0] == "ffmpeg":
            saida.parent.mkdir(parents=True, exist_ok=True)
            saida.write_bytes(b"wav de teste")

        return subprocess.CompletedProcess(comando, 0, stdout="", stderr="")

    monkeypatch.setattr(audio.subprocess, "run", executar)

    monkeypatch.setattr(audio, "obter_duracao_audio", lambda caminho: 35.678)

    resultado = audio.preparar_narracao(
        entrada, saida, normalizar=True, remover_silencios=True
    )

    assert resultado["sucesso"] is True
    assert resultado["duracao"] == 35.68
    assert resultado["formato"] == "WAV"
    assert saida.exists()

    comando = comandos[0]

    assert "silenceremove" in comando[comando.index("-af") + 1]
    assert "loudnorm" in comando[comando.index("-af") + 1]
    assert "aresample=48000" in comando[comando.index("-af") + 1]
    assert "pcm_s16le" in comando


def test_falha_no_processamento(monkeypatch, tmp_path):
    entrada = criar_audio(tmp_path)

    monkeypatch.setattr(audio, "verificar_ffmpeg", lambda: True)

    def executar(*args, **kwargs):
        return subprocess.CompletedProcess(
            args[0], 1, stdout="", stderr="Erro simulado do FFmpeg"
        )

    monkeypatch.setattr(audio.subprocess, "run", executar)

    with pytest.raises(RuntimeError, match="Falha ao preparar"):
        audio.preparar_narracao(entrada, tmp_path / "saida.wav")
