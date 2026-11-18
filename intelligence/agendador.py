import schedule
import time

from intelligence.pesquisa import pesquisar_noticias


def executar_pesquisa():
    print("Iniciando pesquisa automática...")

    noticias = pesquisar_noticias()

    print(f"Pesquisa concluída: {len(noticias)} notícias encontradas.")

    return noticias


def iniciar_agendador(horario="08:00"):
    schedule.every().day.at(horario).do(executar_pesquisa)

    print(f"Pesquisa diária programada para {horario}.")

    while True:
        schedule.run_pending()
        time.sleep(30)