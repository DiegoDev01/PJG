from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base


class Pauta(Base):
    __tablename__ = "pautas"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    titulo: Mapped[str] = mapped_column(String(300), nullable=False)
    assunto: Mapped[str] = mapped_column(Text, nullable=False)
    fonte: Mapped[str | None] = mapped_column(String(500))
    url: Mapped[str | None] = mapped_column(String(1000))
    classificacao: Mapped[str] = mapped_column(String(30), default="pendente")
    relevancia: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String(30), default="aguardando")
    data_criacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
