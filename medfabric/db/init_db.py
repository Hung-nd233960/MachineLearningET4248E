from medfabric.db.database import Base, engine
from medfabric.db import models  # 👈 ensures models are registered with Base

print(engine.url)


def init_db():
    print("Creating all tables...")
    print("Discovered tables:", Base.metadata.tables.keys())  # 👈 debug line
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully.")


if __name__ == "__main__":
    init_db()
