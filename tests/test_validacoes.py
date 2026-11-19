from core import validacoes


def criar_gameplay(tmp_path):
    arquivo = tmp_path / "gameplay.mp4"
    arquivo.touch()
    return arquivo


def criar_narracao(tmp_path):
    arquivo = tmp_path / "narracao.wav"
    arquivo.touch()
    return arquivo


def info_video(tem_audio=True):
    return {
        "arquivo": "gameplay.mp4",
        "duracao": 60.0,
        "tem_video": True,
        "tem_audio": tem_audio,
        "largura": 1080,
        "altura": 1920,
        "codec_video": "h264",
        "codec_audio": "aac" if tem_audio else None,
    }


def info_audio():
    return {
        "arquivo": "narracao.wav",
        "duracao": 40.0,
        "tem_video": False,
        "tem_audio": True,
        "largura": None,
        "altura": None,
        "codec_video": None,
        "codec_audio": "pcm_s16le",
    }


def preparar_ffprobe(monkeypatch):
    monkeypatch.setattr(validacoes, "verificar_ffprobe", lambda: True)


def test_ffprobe_indisponivel(monkeypatch, tmp_path):
    monkeypatch.setattr(validacoes, "verificar_ffprobe", lambda: False)

    resultado = validacoes.validar_producao("gameplay", tmp_path / "gameplay.mp4")

    assert resultado["aprovado"] is False
    assert any("FFprobe" in erro for erro in resultado["erros"])


def test_modo_invalido(monkeypatch, tmp_path):
    preparar_ffprobe(monkeypatch)

    gameplay = criar_gameplay(tmp_path)

    monkeypatch.setattr(validacoes, "analisar_arquivo", lambda caminho: info_video())

    resultado = validacoes.validar_producao("modo_invalido", gameplay)

    assert resultado["aprovado"] is False
    assert any("inválido" in erro for erro in resultado["erros"])


def test_gameplay_formato_invalido(monkeypatch, tmp_path):
    preparar_ffprobe(monkeypatch)

    arquivo = tmp_path / "gameplay.txt"
    arquivo.touch()

    resultado = validacoes.validar_producao("gameplay", arquivo)

    assert resultado["aprovado"] is False
    assert "Formato de gameplay não suportado." in resultado["erros"]


def test_gameplay_sem_audio_aprova_com_aviso(monkeypatch, tmp_path):
    preparar_ffprobe(monkeypatch)

    gameplay = criar_gameplay(tmp_path)

    monkeypatch.setattr(
        validacoes, "analisar_arquivo", lambda caminho: info_video(tem_audio=False)
    )

    resultado = validacoes.validar_producao("gameplay", gameplay)

    assert resultado["aprovado"] is True
    assert len(resultado["avisos"]) == 1


def test_narracao_obrigatoria_ausente(monkeypatch, tmp_path):
    preparar_ffprobe(monkeypatch)

    gameplay = criar_gameplay(tmp_path)

    monkeypatch.setattr(validacoes, "analisar_arquivo", lambda caminho: info_video())

    resultado = validacoes.validar_producao("narracao_livre", gameplay)

    assert resultado["aprovado"] is False
    assert any("narração" in erro for erro in resultado["erros"])


def test_narracao_sem_audio(monkeypatch, tmp_path):
    preparar_ffprobe(monkeypatch)

    gameplay = criar_gameplay(tmp_path)
    narracao = criar_narracao(tmp_path)

    def analisar(caminho):
        if caminho.suffix == ".mp4":
            return info_video()

        dados = info_audio()
        dados["tem_audio"] = False
        return dados

    monkeypatch.setattr(validacoes, "analisar_arquivo", analisar)

    resultado = validacoes.validar_producao(
        "narracao_livre", gameplay, narracao=narracao
    )

    assert resultado["aprovado"] is False
    assert any("não possui áudio" in erro for erro in resultado["erros"])


def test_roteiro_inexistente(monkeypatch, tmp_path):
    preparar_ffprobe(monkeypatch)

    gameplay = criar_gameplay(tmp_path)
    narracao = criar_narracao(tmp_path)

    monkeypatch.setattr(
        validacoes,
        "analisar_arquivo",
        lambda caminho: info_video() if caminho.suffix == ".mp4" else info_audio(),
    )

    resultado = validacoes.validar_producao(
        "narracao_roteiro",
        gameplay,
        narracao=narracao,
        roteiro=tmp_path / "inexistente.txt",
    )

    assert resultado["aprovado"] is False
    assert "Arquivo de roteiro não encontrado." in resultado["erros"]


def test_roteiro_vazio(monkeypatch, tmp_path):
    preparar_ffprobe(monkeypatch)

    gameplay = criar_gameplay(tmp_path)
    narracao = criar_narracao(tmp_path)

    roteiro = tmp_path / "roteiro.txt"
    roteiro.write_text("", encoding="utf-8")

    monkeypatch.setattr(
        validacoes,
        "analisar_arquivo",
        lambda caminho: info_video() if caminho.suffix == ".mp4" else info_audio(),
    )

    resultado = validacoes.validar_producao(
        "narracao_roteiro", gameplay, narracao=narracao, roteiro=roteiro
    )

    assert resultado["aprovado"] is False
    assert "O roteiro está vazio." in resultado["erros"]


def test_producao_completa_valida(monkeypatch, tmp_path):
    preparar_ffprobe(monkeypatch)

    gameplay = criar_gameplay(tmp_path)
    narracao = criar_narracao(tmp_path)

    roteiro = tmp_path / "roteiro.txt"
    roteiro.write_text("Este é um roteiro de teste do PJG.", encoding="utf-8")

    monkeypatch.setattr(
        validacoes,
        "analisar_arquivo",
        lambda caminho: info_video() if caminho.suffix == ".mp4" else info_audio(),
    )

    resultado = validacoes.validar_producao(
        "narracao_roteiro", gameplay, narracao=narracao, roteiro=roteiro
    )

    assert resultado["aprovado"] is True
    assert resultado["erros"] == []
    assert "gameplay" in resultado["arquivos"]
    assert "narracao" in resultado["arquivos"]
    assert "roteiro" in resultado["arquivos"]


def test_gameplay_inexistente(monkeypatch, tmp_path):
    preparar_ffprobe(monkeypatch)

    gameplay = tmp_path / "inexistente.mp4"

    resultado = validacoes.validar_producao("gameplay", gameplay)

    assert resultado["aprovado"] is False
    assert any("Arquivo não encontrado" in erro for erro in resultado["erros"])


def test_gameplay_sem_video(monkeypatch, tmp_path):
    preparar_ffprobe(monkeypatch)

    gameplay = criar_gameplay(tmp_path)

    monkeypatch.setattr(
        validacoes,
        "analisar_arquivo",
        lambda caminho: {
            **info_video(),
            "tem_video": False,
            "largura": None,
            "altura": None,
            "codec_video": None,
        },
    )

    resultado = validacoes.validar_producao("gameplay", gameplay)

    assert resultado["aprovado"] is False
    assert "O arquivo selecionado não possui vídeo." in resultado["erros"]


def test_gameplay_duracao_invalida(monkeypatch, tmp_path):
    preparar_ffprobe(monkeypatch)

    gameplay = criar_gameplay(tmp_path)

    monkeypatch.setattr(
        validacoes, "analisar_arquivo", lambda caminho: {**info_video(), "duracao": 0.0}
    )

    resultado = validacoes.validar_producao("gameplay", gameplay)

    assert resultado["aprovado"] is False
    assert "A gameplay não possui duração válida." in resultado["erros"]


def test_narracao_duracao_invalida(monkeypatch, tmp_path):
    preparar_ffprobe(monkeypatch)

    gameplay = criar_gameplay(tmp_path)
    narracao = criar_narracao(tmp_path)

    def analisar(caminho):
        if caminho.suffix == ".mp4":
            return info_video()

        return {**info_audio(), "duracao": 0.0}

    monkeypatch.setattr(validacoes, "analisar_arquivo", analisar)

    resultado = validacoes.validar_producao(
        "narracao_livre", gameplay, narracao=narracao
    )

    assert resultado["aprovado"] is False
    assert "A narração não possui duração válida." in resultado["erros"]


def test_gameplay_sem_resolucao_valida(monkeypatch, tmp_path):
    preparar_ffprobe(monkeypatch)

    gameplay = criar_gameplay(tmp_path)

    monkeypatch.setattr(
        validacoes,
        "analisar_arquivo",
        lambda caminho: {**info_video(), "largura": 0, "altura": 0},
    )

    resultado = validacoes.validar_producao("gameplay", gameplay)

    assert resultado["aprovado"] is False
