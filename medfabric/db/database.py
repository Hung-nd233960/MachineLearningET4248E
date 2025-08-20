from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# ------------------------
# 1. Define a base class
# ------------------------
class Base(DeclarativeBase):
    pass


# ------------------------
# 2. Database URL
# ------------------------
# Syntax: postgresql+psycopg://username:password@host:port/dbname
# dev: ibmehust2025 ; meduser: ibmehust
DATABASE_URL = "postgresql+psycopg://dev:ibmehust2025@localhost:5432/medfabric"

# ------------------------
# 3. Engine (lazy by default in 2.0)
# ------------------------
engine = create_engine(DATABASE_URL, echo=True)  # echo=True logs SQL

# ------------------------
# 4. Session factory
# ------------------------
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# ------------------------
# 5. Example usage
# ------------------------
def get_session():
    with SessionLocal() as session:
        yield session
