from openai import OpenAI
from api import *
import json
from model import *
from datetime import datetime

def calculate_new_ef_interval(data, word):
    myWord = getWordById(word.id)
    interval = myWord.interval
    if interval == 0:
        interval = 1
    ef = myWord.ef
    weighted_total = 8.7
    weighted_correct = 0.0
    mcq1 = find_mcq_exercise_by_word(myWord, data["answers"][2]["question"])
    mcq2 = find_mcq_exercise_by_word(myWord, data["answers"][3]["question"])
    mcq1_correct_answer = get_mcq_correct_answer_by_mcq_answer_id(mcq1, data["answers"][2]["answer"])
    mcq2_correct_answer = get_mcq_correct_answer_by_mcq_answer_id(mcq2, data["answers"][3]["answer"])

    cloze1 = find_cloze_exercise_by_word(myWord, data["answers"][5]["question"])
    cloze2 = find_cloze_exercise_by_word(myWord, data["answers"][7]["question"])

    writing1 = get_writing_exercise_by_word(myWord, data["answers"][8]["question"])

    if mcq1_correct_answer is None or mcq2_correct_answer is None or cloze1 is None or cloze2 is None or writing1 is None:
        print("Error: Could not find exercises for calculation.")
        return {
            "new_ef": ef,
            "new_interval": interval,
            "score": 0.0
        }
    
    if data["answers"][0]["answer"] == myWord.translation:
        weighted_correct += 1.0

    if data["answers"][1]["answer"] == myWord.sentence1_translation:
        weighted_correct += 1.0

    if data["answers"][2]["answer"] == mcq1_correct_answer:
        weighted_correct += 0.6

    if data["answers"][3]["answer"] == mcq2_correct_answer:
        weighted_correct += 0.6

    if data["answers"][4]["answer"] == myWord.sentence2_translation:
        weighted_correct += 1.0

    if data["answers"][5]["answer"] == cloze1.answer:
        weighted_correct += 1.0

    if data["answers"][6]["answer"] == myWord.sentence3_translation:
        weighted_correct += 1.0

    if data["answers"][7]["answer"] == cloze2.answer:
        weighted_correct += 1.0

    if data["answers"][8]["answer"] == writing1.answer:
        weighted_correct += 1.5
    score = weighted_correct / weighted_total

    if score >= 0.85:
        interval = interval * ef * 1.3
        ef = ef + 0.05
        word.isLearned = 1
    elif score >= 0.70 and score < 0.85:
        interval = interval * ef
    elif score > 0.50 and score < 0.70:
        interval = interval * 1.2
        ef = ef - 0.1
    else:
        ef = ef - 0.2
        interval = 1

    word.interval = interval
    word.ef = ef

    print("Weighted correct:", weighted_correct, "score: ", score, "new ef:", ef, "new interval:", interval)
    outputData = {
        "new_ef": ef,
        "new_interval": interval,
        "score": round(score, 2)
    }
    return outputData
    
def generate_mcq_exercise(word):
    word_name = word.word
    prompt = f"""
        Create a multiple choice question to help learn the Romanian word "{word_name}".

        Return ONLY valid JSON with this structure:
        {{
        "question": "...",
        "choices": ["...", "...", "...", "..."],
        "correct_index": 0
        }}

        Rules:
        - The question should ask for the meaning of the word in English
        - Exactly 4 choices
        - correct_index must be 0-3
    """
    client = OpenAIApi().get_client()
    response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {"role": "system", "content": "You create MCQs for language learning."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.7,
    max_tokens=300
    )

    content = response.choices[0].message.content

    data = json.loads(content)

    new_mcq = MultipleChoiceExercise(
        question=data["question"],
        option1=data["choices"][0],
        option2=data["choices"][1],
        option3=data["choices"][2],
        option4=data["choices"][3],
        correct_answer=data["choices"][data["correct_index"]],
        date_created=datetime.now().strftime('%Y-%m-%d')
    )

    print("Data from OpenAI:", data)

    add_instance(new_mcq)
    word.mcq.append(new_mcq)
    session.commit()

    return new_mcq

def generate_cloze_exercise(word):
    prompt = f"""
Create a Romanian cloze exercise for the word "{word.word}".

Rules:
- Sentence must be in Romanian
- Replace the target word with ___
- Answer must be the missing word
- Return ONLY valid JSON
"""

    client = OpenAIApi().get_client()

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You create cloze exercises for language learners."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.5,
        max_tokens=200
    )

    content = response.choices[0].message.content
    data = json.loads(content)

    print("Data from OpenAI:", data)

    new_cloze = ClozeExercise(
        sentence=data["sentence"],
        answer=data["answer"]
    )

    add_instance(new_cloze)
    word.cloze.append(new_cloze)
    session.commit()

    return new_cloze

def generate_writing_exercise(word):
    prompt = f"""
    Create a Romanian writing exercise for the word "{word.word}".
    Rules:
    - Provide a prompt in Romanian that requires the learner to use the target word
    - Interesting and contextually relevant writing exercise.
    - Return ONLY valid JSON
    """
    
    client = OpenAIApi().get_client()
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You create writing exercises for language learners."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.6,
        max_tokens=250
    )

    content = response.choices[0].message.content
    data = json.loads(content)

    print("Data from OpenAI:", data)
    new_writing = WritingExercise(
        prompt=data["prompt"],
        date_created=datetime.now().strftime('%Y-%m-%d')
    )
    #add_instance(new_writing)
    word.writing.append(new_writing)
    session.commit()

    return new_writing