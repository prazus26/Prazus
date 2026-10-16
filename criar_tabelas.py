
from sqlalchemy import inspect
from database import engine, Base
from model.usuario import Usuario

Base.metadata.create_all(bind=engine)

inspector = inspect(engine)

if inspector.has_table("usuarios"):
    print("Tabela usuarios criada ou já existente!")
    print(inspector.get_columns("usuarios"))
