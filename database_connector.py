import os
from dotenv import load_dotenv
from sqlalchemy import create_engine,NullPool
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import URL

load_dotenv()

DATABASE_URL=URL.create(
    drivername="postgresql+psycopg",
    username=os.environ.get("USER"),
    password=os.environ.get("DATABASE_PASSWORD"),
    host=os.environ.get("HOST"),
    port=6543,
    database="postgres"
)

db_url=DATABASE_URL
engine=create_engine(db_url,poolclass=NullPool,connect_args={"prepare_threshold": None})

session=sessionmaker(autoflush=False,bind=engine)

def get_db():
    db=session()
    try:
        print ("database connected successfully")
        yield db
    finally:
        print ("database connection closed")
        db.close()