def classificar_noticia(texto: str) -> str:
    texto = texto.lower()

    rumores = [
        "rumor",
        "vazamento",
        "leak",
        "supostamente",
        "não confirmado",
        "informação não confirmada",
    ]

    especulacoes = [
        "pode",
        "poderá",
        "talvez",
        "especula-se",
        "teoria",
        "possivelmente",
        "poderia",
    ]

    promocoes = [
        "desconto",
        "oferta",
        "promoção",
        "por menos de",
        "black friday",
        "cupom",
        "economize",
        "menor preço",
        "preço especial",
    ]

    if any(palavra in texto for palavra in rumores):
        return "rumor"

    if any(palavra in texto for palavra in especulacoes):
        return "especulacao"

    if any(palavra in texto for palavra in promocoes):
        return "promocao"

    return "noticia"
