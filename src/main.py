from dotenv import load_dotenv
import os
from pathlib import Path

env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(env_path)

from src.model import *
from flask import Flask, render_template, request, jsonify, url_for, redirect
from datetime import datetime
from reviewLogic import *

app = Flask(__name__, template_folder='../templates')

@app.route('/')
def index():
    return render_template('main.html')

@app.route('/decks')
def list_decks():
    decks = getDecks()
    return render_template('myDecks.html', decks=decks)

@app.route('/decks/create', methods=['POST'])
def create_deck():
    new_deck = request.form.get('deck_name')
    if new_deck:
        now = datetime.now().strftime('%Y-%m-%d')
        add_instance(Deck(name=new_deck, description='', date_created=now))
        #return render_template('myDecks.html')
    decks = getDecks()
    return render_template('myDecks.html', decks=decks)

@app.route('/deck_detail/<int:deck_id>')
def deck_detail(deck_id):
    deck = getDeckById(deck_id)
    return render_template('deck_detail.html', deck=deck)

@app.route('/deck_detail/<int:deck_id>/words/remove/<int:word_id>', methods=['POST'])
def remove_word_from_deck(deck_id, word_id):
    deleteWordFromDeck(deck_id, word_id)
    return redirect(url_for('deck_detail', deck_id=deck_id))

@app.route('/deck_detail/<int:deck_id>/words/add', methods=['POST'])
def add_word_to_deck(deck_id):
    deck = getDeckById(deck_id)
    word_text = request.form.get('word')
    dictionary_definition = request.form.get('dictionary_definition')
    translation = request.form.get('translation')
    sentence1 = request.form.get('sentence1')
    sentence1_translation = request.form.get('sentence1_translation')
    sentence2 = request.form.get('sentence2')
    sentence2_translation = request.form.get('sentence2_translation')
    sentence3 = request.form.get('sentence3')
    sentence3_translation = request.form.get('sentence3_translation')
    now = datetime.now().strftime('%Y-%m-%d')

    if word_text and translation:
        new_word = Word(
            word=word_text,
            dictionary_definition=dictionary_definition,
            translation=translation,
            sentence1=sentence1,
            sentence1_translation=sentence1_translation,
            sentence2=sentence2,
            sentence2_translation=sentence2_translation,
            sentence3=sentence3,
            sentence3_translation=sentence3_translation,
            date_created=now
        )
        add_instance(new_word)
        deck.words.append(new_word)
        session.commit()

    return redirect(url_for('deck_detail', deck_id=deck_id))

@app.route('/words/<int:word_id>/edit', methods=['GET', 'POST'])
def edit_word(word_id):
    pass

@app.route('/review')
def review_words():
    decks = getDecks()
    return render_template('listDecks.html', decks=decks)

@app.route("/review/start", methods=["GET"])
def start_review():
    deck_id = request.args.get("deck_id")

    if not deck_id:
        return "No deck selected", 400
    
    deck = getDeckById(deck_id)

    words = [word for word in deck.words if word.isLearned == 0 and word.last_date_reviewed != datetime.now().strftime('%Y-%m-%d')]

    return render_template("reviewDeck.html", words=words, deck=deck)

@app.route('/review/word/mcq/<int:word_id>', methods=['GET'])
def get_mcq(word_id):
    returnData = []
    word = getWordById(word_id)

    # collect unsolved MCQs
    for exercise in word.mcq:
        if exercise.iSolved == 0:
            returnData.append({
                "question": exercise.question,
                "option1": exercise.option1,
                "option2": exercise.option2,
                "option3": exercise.option3,
                "option4": exercise.option4,
                "correct_answer": exercise.correct_answer
            })

    # generate missing MCQs (max 2)
    while len(returnData) < 2:
        mcq = generate_mcq_exercise(word)

        # prevent duplicate association
        if mcq not in word.mcq:
            word.mcq.append(mcq)

        returnData.append({
            "question": mcq.question,
            "option1": mcq.option1,
            "option2": mcq.option2,
            "option3": mcq.option3,
            "option4": mcq.option4,
            "correct_answer": mcq.correct_answer
        })

    session.commit()

    return jsonify(returnData[:2])

@app.route('/review/word/cloze/<int:word_id>', methods=['GET'])
def get_cloze(word_id):
    returnData = []
    word = getWordById(word_id)

    for exercise in word.cloze:
        if exercise.isSolved == 0:
            returnData.append({
                "sentence": exercise.sentence,
                "answer": exercise.answer
            })

    while len(returnData) < 2:
        cloze = generate_cloze_exercise(word)

        if cloze not in word.cloze:
            word.cloze.append(cloze)

        returnData.append({
            "sentence": cloze.sentence,
            "answer": cloze.answer
        })
    session.commit()
    return jsonify(returnData[:2])

@app.route('/review/word/writing/<int:word_id>', methods=['GET'])
def get_writing(word_id):
    word = getWordById(word_id)

    # Try to get the first unsolved writing exercise
    writing = next((w for w in word.writing if w.isSolved == 0), None)

    # If none exists, generate one
    if writing is None:
        writing = generate_writing_exercise(word)
        word.writing.append(writing)
        session.commit()

    # Return as a list for consistency with frontend
    return jsonify([{
        "id": writing.id,
        "prompt": writing.prompt
    }])

@app.route('/review/submit', methods=['POST'])
def submit_review():
    data = request.get_json()

    word_id = data["word_id"]
    answers = data["answers"]
    score = data["score"]

    print(f"Word ID: {word_id}, Answers: {answers}, Score: {score}")
    #TODO
    elf = calculate_new_ef_interval(data, getWordById(word_id))

    #calculate_new_ef_interval(data)

    return jsonify({"status:": "ok"})

if __name__ == '__main__':
    app.run(debug=True)
