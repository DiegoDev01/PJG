from database.database import SessionLocal
from database.models import Pauta


def listar_pautas_pendentes():
    sessao = SessionLocal()

    try:
        return sessao.query(Pauta).filter_by(
            status="aguardando"
        ).order_by(Pauta.relevancia.desc()).all()
    finally:
        sessao.close()


def atualizar_status(pauta_id: int, novo_status: str):
    if novo_status not in ["aprovada", "rejeitada"]:
        raise ValueError("Status inválido.")

    sessao = SessionLocal()

    try:
        pauta = sessao.get(Pauta, pauta_id)

        if pauta is None:
            return False

        pauta.status = novo_status
        sessao.commit()
        return True

    except Exception:
        sessao.rollback()
        raise

    finally:
        sessao.close()