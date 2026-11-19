import feedparser
import requests
import trafilatura
from bs4 import BeautifulSoup

from database.database import SessionLocal
from database.models import Pauta
from intelligence.analise import analisar_noticia
from intelligence.fontes import obter_fontes

TEMAS_MONITORADOS = {
    "GTA VI": ["gta vi", "gta 6", "grand theft auto 6"],
    "Games": ["videogame", "games", "playstation", "xbox", "nintendo"],
}


def extrair_conteudo_completo(url: str, resumo: str) -> str:
    if not url:
        return resumo

    try:
        resposta = requests.get(
            url, headers={"User-Agent": "Mozilla/5.0 PJG News Reader"}, timeout=(5, 8)
        )

        resposta.raise_for_status()

        conteudo = trafilatura.extract(
            resposta.text,
            url=url,
            include_comments=False,
            include_tables=False,
            favor_precision=True,
        )

        if conteudo and len(conteudo) > len(resumo):
            return conteudo

    except requests.RequestException as erro:
        print(f"Erro ao acessar matéria: {erro}")

    except Exception as erro:  # noqa: BLE001
        print(f"Erro na extração: {erro}")

    return resumo


def pesquisar_noticias():
    resultados = []

    for fonte in obter_fontes():
        try:
            feed = feedparser.parse(fonte["url"])

            for noticia in feed.entries:
                titulo = noticia.get("title", "")

                resumo = BeautifulSoup(
                    noticia.get("summary", ""), "html.parser"
                ).get_text(" ", strip=True)

                texto = f"{titulo} {resumo}".lower()

                temas = [
                    tema
                    for tema, palavras in TEMAS_MONITORADOS.items()
                    if any(palavra in texto for palavra in palavras)
                ]

                if not temas:
                    continue

                url = noticia.get("link", "")

                if fonte["nome"] == "GameSpot":
                    conteudo = resumo
                else:
                    conteudo = extrair_conteudo_completo(url, resumo)

                analise = analisar_noticia(titulo, conteudo, fonte["nome"])

                resultados.append({**analise, "url": url, "temas": temas})

        except Exception as erro:  # noqa: BLE001
            print(f"Erro em {fonte['nome']}: {erro}")

    return resultados


def salvar_noticias(noticias):
    salvas = 0
    sessao = SessionLocal()

    try:
        for noticia in noticias:
            url = noticia.get("url", "")

            if not url:
                continue

            existente = sessao.query(Pauta).filter_by(url=url).first()

            if existente:
                existente.titulo = noticia["titulo"]
                existente.assunto = noticia["conteudo"]
                existente.classificacao = noticia["classificacao"]
                existente.relevancia = noticia["relevancia"]
                continue

            pauta = Pauta(
                titulo=noticia["titulo"],
                assunto=noticia["conteudo"],
                fonte=noticia["fonte"],
                url=url,
                classificacao=noticia["classificacao"],
                relevancia=noticia["relevancia"],
            )

            sessao.add(pauta)
            salvas += 1

        sessao.commit()
        return salvas

    except Exception:
        sessao.rollback()
        raise

    finally:
        sessao.close()
