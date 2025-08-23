# /medfabric/db/database.py
from sqlalchemy import create_engine
from sqlalchemy import URL
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.orm import scoped_session


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
URL_OBJECT = URL.create(
    "postgresql+psycopg",
    username="dev",
    password="ibmehust2025",
    host="localhost",
    port=5432,
    database="medfabric",
)

# ------------------------
# 3. Engine (lazy by default in 2.0)
# ------------------------
engine = create_engine(URL_OBJECT, echo=True)  # echo=True logs SQL

# ------------------------
# 4. Session factory
# ------------------------
session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Session = scoped_session(session_factory)


# ------------------------
# 5. Example usage
# ------------------------
def get_db():
    db = Session()  # scoped_session creates or reuses current Session
    try:
        yield db  # give the session to FastAPI route handler
        db.commit()  # if no exception, commit transaction
    except:
        db.rollback()  # if any exception in the route, rollback transaction
        raise  # re-raise so FastAPI still sees the error
    finally:
        Session.remove()  # cleanup: close & discard this Session
