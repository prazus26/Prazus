
from database import Base
import model

print("Modelos carregados:")

for tabela in Base.metadata.sorted_tables:
    print(f"- {tabela.name}")

print("\nTotal de tabelas:", len(Base.metadata.tables))
