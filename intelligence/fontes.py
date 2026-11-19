FONTES = {
    "jornalismo": [
        {"nome": "IGN Brasil", "url": "https://br.ign.com/feed.xml", "prioridade": 1},
        {
            "nome": "IGN",
            "url": "https://www.ign.com/rss/v2/articles/feed",
            "prioridade": 1,
        },
        {
            "nome": "GameSpot",
            "url": "https://www.gamespot.com/feeds/mashup/",
            "prioridade": 2,
        },
        {"nome": "Eurogamer", "url": "https://www.eurogamer.net/feed", "prioridade": 2},
    ]
}


def listar_fontes():
    return FONTES


def obter_fontes():
    todas = FONTES["jornalismo"]
    return sorted(todas, key=lambda fonte: fonte["prioridade"])
