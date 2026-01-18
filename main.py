from model import *
from flask import Flask, render_template, request, jsonify, url_for, redirect
from datetime import datetime

app = Flask(__name__)

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
    sentence2 = request.form.get('sentence2')
    sentence3 = request.form.get('sentence3')
    now = datetime.now().strftime('%Y-%m-%d')

    if word_text and translation:
        new_word = Word(
            word=word_text,
            dictionary_definition=dictionary_definition,
            translation=translation,
            sentence1=sentence1,
            sentence2=sentence2,
            sentence3=sentence3,
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

@app.route('/review/submit', methods=['POST'])
def submit_review():
    data = request.get_json()

    word_id = data["word_id"]
    answers = data["answers"]
    score = data["score"]

    print(f"Word ID: {word_id}, Answers: {answers}, Score: {score}")

    #calculate_new_ef_interval(data)

    return jsonify({"status:": "ok"})

if __name__ == '__main__':
    app.run(debug=True)
