from database import models  # noqa: F401
from database.database import Base, engine
from interface.main_window import iniciar_interface


def iniciar_pjg():
    Base.metadata.create_all(bind=engine)
    iniciar_interface()


if __name__ == "__main__":
    iniciar_pjg()
