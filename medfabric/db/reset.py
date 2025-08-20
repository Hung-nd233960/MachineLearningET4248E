from medfabric.db.database import Base, engine
from medfabric.db.models import *  # import all models so they’re registered

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
