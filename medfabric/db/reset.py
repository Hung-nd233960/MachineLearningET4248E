from medfabric.db.database import Base, engine

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
