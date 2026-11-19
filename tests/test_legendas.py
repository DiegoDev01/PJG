from types import SimpleNamespace

import pytest

from core import legendas


def criar_palavras():
    return [
        {"texto": "Olá", "inicio": 0.0, "fim": 0.5},
        {"texto": "mundo!", "inicio": 0.5, "fim": 1.0},
        {"texto": "Estamos", "inicio": 1.1, "fim": 1.5},
        {"texto": "testando", "inicio": 1.5, "fim": 2.0},
        {"texto": "o", "inicio": 2.0, "fim": 2.1},
        {"texto": "PJG.", "inicio": 2.1, "fim": 2.5},
    ]


def test_audio_inexistente(tmp_path):
    with pytest.raises(FileNotFoundError):
        legendas.transcrever_audio(tmp_path / "inexistente.wav")


def test_transcricao_com_sucesso(monkeypatch, tmp_path):
    audio = tmp_path / "audio.wav"
    audio.touch()

    palavras = [
        SimpleNamespace(word=" Olá", start=0.0, end=0.5),
        SimpleNamespace(word=" mundo!", start=0.5, end=1.0),
        SimpleNamespace(word=" ignorada", start=None, end=1.5),
        SimpleNamespace(word="   ", start=1.5, end=2.0),
    ]

    segmento = SimpleNamespace(text="Olá mundo!", words=palavras)

    informacoes = SimpleNamespace(language="pt", duration=2.0)

    class WhisperFake:
        def __init__(self, *args, **kwargs):
            pass

        def transcribe(self, *args, **kwargs):
            return iter([segmento]), informacoes

    import sys

    monkeypatch.setitem(
        sys.modules, "faster_whisper", SimpleNamespace(WhisperModel=WhisperFake)
    )

    resultado = legendas.transcrever_audio(audio)

    assert resultado["idioma"] == "pt"
    assert resultado["duracao"] == 2.0
    assert resultado["texto_completo"] == "Olá mundo!"
    assert len(resultado["palavras"]) == 2


def test_transcricao_sem_palavras(monkeypatch, tmp_path):
    audio = tmp_path / "audio.wav"
    audio.touch()

    segmento = SimpleNamespace(text="", words=[])

    informacoes = SimpleNamespace(language="pt", duration=1.0)

    class WhisperFake:
        def __init__(self, *args, **kwargs):
            pass

        def transcribe(self, *args, **kwargs):
            return iter([segmento]), informacoes

    import sys

    monkeypatch.setitem(
        sys.modules, "faster_whisper", SimpleNamespace(WhisperModel=WhisperFake)
    )

    with pytest.raises(RuntimeError, match="Nenhuma palavra"):
        legendas.transcrever_audio(audio)


def test_formatar_tempo_ass():
    assert legendas.formatar_tempo_ass(0) == "0:00:00.00"
    assert legendas.formatar_tempo_ass(1.25) == "0:00:01.25"
    assert legendas.formatar_tempo_ass(65.50) == "0:01:05.50"
    assert legendas.formatar_tempo_ass(3661.75) == "1:01:01.75"


def test_formatar_tempo_negativo():
    assert legendas.formatar_tempo_ass(-5) == "0:00:00.00"


def test_agrupar_palavras_por_limite():
    palavras = criar_palavras()

    blocos = legendas.agrupar_palavras(palavras, max_palavras=3)

    assert len(blocos) == 3
    assert len(blocos[0]) == 2
    assert len(blocos[1]) == 3
    assert len(blocos[2]) == 1


def test_agrupar_palavras_por_pontuacao():
    palavras = criar_palavras()

    blocos = legendas.agrupar_palavras(palavras, max_palavras=10)

    assert len(blocos) == 2
    assert blocos[0][-1]["texto"] == "mundo!"
    assert blocos[1][-1]["texto"] == "PJG."


def test_gerar_legendas_ass_com_sucesso(tmp_path):
    palavras = criar_palavras()

    transcricao = {
        "idioma": "pt",
        "duracao": 2.5,
        "palavras": palavras,
        "texto_completo": "Olá mundo! Estamos testando o PJG.",
    }

    saida = tmp_path / "legendas" / "teste.ass"

    resultado = legendas.gerar_legendas_ass(transcricao, saida)

    assert resultado["sucesso"] is True
    assert resultado["quantidade_palavras"] == 6
    assert resultado["quantidade_legendas"] == 3
    assert saida.exists()

    conteudo = saida.read_text(encoding="utf-8-sig")

    assert "[Script Info]" in conteudo
    assert "PlayResX: 1080" in conteudo
    assert "PlayResY: 1920" in conteudo
    assert "Olá mundo!" in conteudo
    assert "Estamos testando o" in conteudo


def test_gerar_legendas_com_textos_especiais(tmp_path):
    transcricao = {"palavras": [{"texto": "{teste}\\", "inicio": 0.0, "fim": 1.0}]}

    saida = tmp_path / "especial.ass"

    legendas.gerar_legendas_ass(transcricao, saida)

    conteudo = saida.read_text(encoding="utf-8-sig")

    assert r"\{teste\}" in conteudo
    assert r"\\" in conteudo


def test_transcricao_vazia_nao_gera_legendas(tmp_path):
    transcricao = {"palavras": []}

    with pytest.raises(ValueError, match="não contém palavras"):
        legendas.gerar_legendas_ass(transcricao, tmp_path / "vazio.ass")
