from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Banco de dados local do Pela Janela Games
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = BASE_DIR / "database"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DATABASE_DIR / 'pjg.db'}"

# Conexão
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Sessões
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base dos modelos
Base = declarative_base()


def criar_banco():
    """Cria as tabelas registradas no sistema."""
    Base.metadata.create_all(bind=engine)


def obter_sessao():
    """Fornece uma sessão do banco de dados."""
    sessao = SessionLocal()
    try:
        yield sessao
    finally:
        sessao.close()
