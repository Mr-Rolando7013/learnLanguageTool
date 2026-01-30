from sqlalchemy import create_engine, update
from sqlalchemy.orm import sessionmaker
from src.model import *

# 1. Connect to your database
DATABASE_URL = "sqlite:///info.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # 2. Update all words: set last_date_reviewed to None
    session.query(Word).update({Word.last_date_reviewed: None})
    session.query(Word).update({Word.interval: 0})
    
    # 3. Commit the changes
    session.commit()
    print("All words updated: last_date_reviewed set to NULL.")
except Exception as e:
    session.rollback()
    print("Error:", e)
finally:
    session.close()