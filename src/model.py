from sqlalchemy import create_engine, Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.orm import relationship
from datetime import datetime


DATABASE_URL = "sqlite:///info.db"

engine = create_engine(DATABASE_URL, echo=False)

Base = declarative_base()


deck_words = Table(
    'deck_words',
    Base.metadata,
    Column('deck_id', Integer, ForeignKey('decks.id'), primary_key=True),
    Column('word_id', Integer, ForeignKey('words.id'), primary_key=True),
)

mcq_exercise_words = Table(
    'mcq_exercise_words',
    Base.metadata,
    Column('word_id', Integer, ForeignKey('words.id'), primary_key=True),
    Column('exercise_id', Integer, ForeignKey('exercises.id'), primary_key=True)
)

writing_exercise_words = Table(
    'writing_exercise_words',
    Base.metadata,
    Column('word_id', Integer, ForeignKey('words.id'), primary_key=True),
    Column('exercise_id', Integer, ForeignKey('writing_exercises.id'), primary_key=True)
)

cloze_exercise_words = Table(
    'cloze_exercise_words',
    Base.metadata,
    Column('word_id', Integer, ForeignKey('words.id'), primary_key=True),
    Column('exercise_id', Integer, ForeignKey('cloze_exercises.id'), primary_key=True)
)

class ClozeExercise(Base):
    __tablename__ = 'cloze_exercises'

    id = Column(Integer, primary_key=True)
    sentence = Column(String, nullable=False)
    answer = Column(String, nullable=False)

    word = relationship(
        "Word",
        secondary="cloze_exercise_words",
        backref="cloze_exercises"
    )

    def __repr__(self):
        return f"<ClozeExercise(id={self.id}, sentence='{self.sentence}', answer='{self.answer}')>"

class WritingExercise(Base):
    __tablename__ = 'writing_exercises'
    
    id = Column(Integer, primary_key=True)
    prompt = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    date_created = Column(String, nullable=False)

    word = relationship(
        "Word",
        secondary="writing_exercise_words",
        backref="writing_exercises"
    )

    def __repr__(self):
        return f"<WritingExercise(id={self.id}, prompt='{self.prompt}', answer='{self.answer}', date_created='{self.date_created}')>"

class MultipleChoiceExercise(Base):
    __tablename__ = 'exercises'
    
    id = Column(Integer, primary_key=True)
    question = Column(String, nullable=False)
    option1 = Column(String, nullable=False)
    option2 = Column(String, nullable=False)
    option3 = Column(String, nullable=False)
    option4 = Column(String, nullable=False)
    correct_answer = Column(String, nullable=False)
    date_created = Column(String, nullable=False)

    word = relationship(
        "Word",
        secondary="mcq_exercise_words",
        backref="mcq_exercises"
    )        

    def __repr__(self):
        return f"<MultipleChoiceExercise(id={self.id}, question='{self.question}', correct_answer='{self.correct_answer}', date_created='{self.date_created}')>"

class Word(Base):
    __tablename__ = 'words'
    
    id = Column(Integer, primary_key=True)
    word = Column(String, unique=True, nullable=False)
    dictionary_definition = Column(String, nullable=False)
    translation = Column(String, nullable=False)
    sentence1 = Column(String, nullable=False)
    sentence2 = Column(String, nullable=True)
    sentence3 = Column(String, nullable=True)
    date_created = Column(String, nullable=False)
    last_date_reviewed = Column(String, nullable=True)
    isLearned = Column(Integer, default=0)
    ef = Column(Integer, default=2.5)
    interval = Column(Integer, default=1)

    decks = relationship(
        "Deck",
        secondary=deck_words,
        back_populates="words"
    )

    mcq = relationship(
        "MultipleChoiceExercise",
        secondary=mcq_exercise_words,
        backref="words"
    )

    writing = relationship(
        "WritingExercise",
        secondary=writing_exercise_words,
        backref="words"
    )

    cloze = relationship(
        "ClozeExercise",
        secondary=cloze_exercise_words,
        backref="words"
    )

    def __repr__(self):
        return f"<Word(id={self.id}, word='{self.word}', translation='{self.translation}', isLearned={self.isLearned})>"
    
class Deck(Base):
    __tablename__ = 'decks'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    date_created = Column(String, nullable=False)

    words = relationship(
        "Word",
        secondary=deck_words,
        back_populates="decks"
    )

    def __repr__(self):
        return f"<Deck(id={self.id}, name='{self.name}', description='{self.description}')>"
    

def create_db():
    Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

def add_instance(instance):
    session.add(instance)
    session.commit()

def getWritingExercises():
    return session.query(WritingExercise).all()

def getMultipleChoiceExercises():
    return session.query(MultipleChoiceExercise).all()

def getWords():
    return session.query(Word).all()

def getDecks():
    return session.query(Deck).all()

def getDeckById(deck_id):
    return session.query(Deck).filter_by(id=deck_id).first()

def deleteWordFromDeck(deckId, wordId):
    deck = getDeckById(deckId)
    word = session.query(Word).filter_by(id=wordId).first()
    if deck and word:
        deck.words.remove(word)
        session.commit()