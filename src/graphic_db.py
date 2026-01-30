import tkinter as tk
from tkinter import ttk
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model import Base, Word, Deck, MultipleChoiceExercise, WritingExercise, ClozeExercise

DATABASE_URL = "sqlite:///info.db"

# ------------------ SQLAlchemy setup ------------------
engine = create_engine(DATABASE_URL, echo=False)
Base.metadata.bind = engine

# Create all tables if they don't exist
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

# ------------------ Tkinter GUI ------------------
root = tk.Tk()
root.title("Database Explorer")
root.geometry("1000x600")

# Tables to display
tables = ["Word", "Deck", "MultipleChoiceExercise", "WritingExercise", "ClozeExercise"]
selected_table = tk.StringVar()
selected_table.set(tables[0])

# Treeview for table display
tree = ttk.Treeview(root, columns=("col1","col2","col3","col4","col5","col6"), show="headings")
tree.pack(fill=tk.BOTH, expand=True)

# Load table data into the Treeview
def load_table():
    tree.delete(*tree.get_children())
    table = selected_table.get()

    if table == "Word":
        rows = session.query(Word).all()
        for w in rows:
            tree.insert("", tk.END, values=(
                w.id, w.word, w.translation, w.isLearned, w.date_created, w.last_date_reviewed, w.interval
            ))
    elif table == "Deck":
        rows = session.query(Deck).all()
        for d in rows:
            tree.insert("", tk.END, values=(d.id, d.name, d.description, d.date_created))
    elif table == "MultipleChoiceExercise":
        rows = session.query(MultipleChoiceExercise).all()
        for m in rows:
            tree.insert("", tk.END, values=(m.id, m.question, m.correct_answer, m.date_created, m.iSolved))
    elif table == "WritingExercise":
        rows = session.query(WritingExercise).all()
        for w in rows:
            tree.insert("", tk.END, values=(w.id, w.prompt, w.answer, w.date_created, w.isSolved))
    elif table == "ClozeExercise":
        rows = session.query(ClozeExercise).all()
        for c in rows:
            tree.insert("", tk.END, values=(c.id, c.sentence, c.answer, c.isSolved))

# Configure columns dynamically
def configure_columns(*args):
    table = selected_table.get()

    if table == "Word":
        tree["columns"] = ("ID", "Word", "Translation", "Learned", "Created", "Last Reviewed", "Interval")
    elif table == "Deck":
        tree["columns"] = ("ID", "Name", "Description", "Created")
    elif table == "MultipleChoiceExercise":
        tree["columns"] = ("ID", "Question", "Answer", "Created", "Solved")
    elif table == "WritingExercise":
        tree["columns"] = ("ID", "Prompt", "Answer", "Created", "Solved")
    elif table == "ClozeExercise":
        tree["columns"] = ("ID", "Sentence", "Answer", "Solved")

    # Set heading and column widths
    for col in tree["columns"]:
        tree.heading(col, text=col)
        tree.column(col, width=150)

    load_table()

# Dropdown menu to select table
dropdown = ttk.OptionMenu(root, selected_table, tables[0], *tables, command=lambda _: configure_columns())
dropdown.pack(pady=10)

selected_table.trace_add("write", configure_columns)
configure_columns()

root.mainloop()