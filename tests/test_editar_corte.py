import pytest

from scripts.editar_corte import alinhar_com_roteiro


def criar_palavras():
    return [
        {"word": "Hoje", "start": 0.0, "end": 0.4},
        {"word": "vamos", "start": 0.4, "end": 0.8},
        {"word": "jogar", "start": 0.8, "end": 1.2},
        {"word": "GTA", "start": 1.2, "end": 1.8},
    ]


def test_alinhamento_com_textos_iguais():
    palavras = criar_palavras()

    resultado = alinhar_com_roteiro(palavras, "Hoje vamos jogar GTA")

    assert len(resultado) == 4
    assert [p["word"] for p in resultado] == ["Hoje", "vamos", "jogar", "GTA"]


def test_corrigir_palavras_reconhecidas():
    palavras = [
        {"word": "oje", "start": 0.0, "end": 0.4},
        {"word": "vamo", "start": 0.4, "end": 0.8},
        {"word": "jogar", "start": 0.8, "end": 1.2},
    ]

    resultado = alinhar_com_roteiro(palavras, "Hoje vamos jogar")

    assert [p["word"] for p in resultado] == ["Hoje", "vamos", "jogar"]


def test_preservar_palavras_extras_do_whisper():
    palavras = [
        {"word": "Hoje", "start": 0.0, "end": 0.3},
        {"word": "nós", "start": 0.3, "end": 0.5},
        {"word": "vamos", "start": 0.0, "end": 1.0},
    ]

    resultado = alinhar_com_roteiro(palavras, "Hoje vamos")

    assert [p["word"] for p in resultado] == ["Hoje", "nós", "vamos"]


def test_roteiro_vazio_retorna_transcricao_original():
    palavras = criar_palavras()

    resultado = alinhar_com_roteiro(palavras, "")

    assert resultado == palavras


def test_transcricao_vazia_retorna_lista_vazia():
    resultado = alinhar_com_roteiro([], "Hoje vamos jogar GTA")

    assert resultado == []


def test_substituicao_de_uma_palavra_por_varias():
    palavras = [
        {"word": "vamo", "start": 0.0, "end": 1.0},
    ]

    resultado = alinhar_com_roteiro(palavras, "vamos todos jogar")

    assert len(resultado) == 3

    assert resultado[0]["word"] == "vamos"
    assert resultado[1]["word"] == "todos"
    assert resultado[2]["word"] == "jogar"

    assert resultado[0]["start"] == pytest.approx(0.0)
    assert resultado[0]["end"] == pytest.approx(1 / 3)

    assert resultado[1]["start"] == pytest.approx(1 / 3)
    assert resultado[1]["end"] == pytest.approx(2 / 3)

    assert resultado[2]["start"] == pytest.approx(2 / 3)
    assert resultado[2]["end"] == pytest.approx(1.0)
