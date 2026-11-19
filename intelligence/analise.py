from intelligence.classificacao import classificar_noticia


def analisar_noticia(titulo: str, conteudo: str, fonte: str) -> dict:
    titulo = titulo.lower()
    conteudo = conteudo.lower()
    texto = f"{titulo} {conteudo}"

    classificacao = classificar_noticia(texto)

    relevancia = 0

    # O assunto principal da notícia
    palavras_principais = ["gta 6", "gta vi", "grand theft auto 6"]

    # Informações relevantes sobre o jogo
    palavras_importantes = [
        "rockstar games",
        "trailer",
        "lançamento",
        "gameplay",
        "mapa",
        "lucia",
        "jason",
        "vice city",
        "história",
        "personagem",
        "missões",
        "mundo aberto",
    ]

    # Pontuação pelo título
    if any(p in titulo for p in palavras_principais):
        relevancia += 5

    # Pontuação pelo conteúdo
    if any(p in conteudo for p in palavras_principais):
        relevancia += 2

    for palavra in palavras_importantes:
        if palavra in texto:
            relevancia += 1

    if fonte.lower() in ["rockstar games", "take-two interactive"]:
        relevancia += 3

    # Promoções não devem ganhar prioridade apenas por mencionar GTA 6
    if classificacao == "promocao":
        relevancia = min(relevancia, 3)

    return {
        "titulo": titulo,
        "conteudo": conteudo,
        "fonte": fonte,
        "classificacao": classificacao,
        "relevancia": min(relevancia, 10),
    }
