from openai import OpenAI
from api import *
import json
from model import *
from datetime import datetime
import random

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
    mcq_types = [
        "direct definition",
        "context-based meaning",
        "false friend confusion",
        "same part of speech distractors",
        "near-synonym vs exact meaning",
    ]
    mcq_type = random.choice(mcq_types)
    if mcq_type == "false friend confusion":
        extra_rule = "Wrong answers must look similar to the Romanian word but have different meanings."

    elif mcq_type == "same part of speech distractors":
        extra_rule = "All choices must be the same part of speech."

    elif mcq_type == "context-based meaning":
        extra_rule = "The question must include a short Romanian sentence using the word."

    elif mcq_type == "near-synonym vs exact meaning":
        extra_rule = "Wrong answers should be close in meaning but not exact."

    else:
        extra_rule = "Use clear but non-obvious distractors."
    word_name = word.word
    prompt = f"""
        Create a Romanian vocabulary multiple choice question.

        Target word: "{word_name}"
        MCQ type: {mcq_type}

        Return ONLY valid JSON with this structure:
        {{
        "question": "...",
        "choices": ["...", "...", "...", "..."],
        "correct_index": 0
        }}

        Rules:
        - Ask for the meaning of the word in English
        - Exactly 4 choices
        - Only ONE choice is correct
        - Wrong answers must be plausible but clearly incorrect
        - Avoid repeating common patterns or phrasing
        - correct_index must be 0-3
        - {extra_rule}
    """
    client = OpenAIApi().get_client()
    response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[
        {"role": "system", "content": "You create MCQs for language learning."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.9,
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
    cloze_types = [
        "everyday conversation",
        "narrative context",
        "formal written Romanian",
        "emotional / opinionated sentence",
        "cause–effect sentence",
        "past tense context",
        "future or hypothetical context"
    ]

    cloze_type = random.choice(cloze_types)
    grammar_constraints = [
        "use a common collocation",
        "use the word in a less obvious context",
        "use the word with a modifier or complement",
        "avoid very short sentences",
        "the sentence must clearly disambiguate the meaning"
    ]

    grammar_rule = random.choice(grammar_constraints)
    prompt = f"""
Create ONE Romanian cloze exercise.

Target word: "{word.word}"
Cloze type: {cloze_type}
Constraint: {grammar_rule}

Rules:
- Sentence must be in Romanian
- The sentence must sound natural to a native speaker
- Replace ONLY the target word with ___
- Answer must be the missing word
- Do NOT place ___ at the beginning or end of the sentence
- The meaning must be clear from context
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
        temperature=0.8,
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
    exercise_types = [
        "narativă (poveste scurtă)",
        "dialog (conversație între două persoane)",
        "opinie personală",
        "descriere (loc, persoană sau situație)",
        "scrisoare informală",
        "jurnal personal",
        "argumentare (pro și contra)",
    ]
    exercise_type = random.choice(exercise_types)
    contexts = [
        "viața de zi cu zi",
        "o situație amuzantă",
        "un conflict minor",
        "o experiență personală",
        "o situație neobișnuită",
        "o întâmplare din trecut",
    ]

    context = random.choice(contexts)
    prompt = f"""
    Write ONE engaging Romanian writing prompt for language learners.
    
    Target word: "{word.word}"

    Exercise type: {exercise_type}
    Context: {context}
    Rules:
    - Provide a prompt in Romanian that requires the learner to use the target word
    - The scenario must be concrete and vivid.
    - Avoid generic or school-like prompts
    - Do NOT explain the task, only give the prompt itself
    - Return ONLY valid JSON
    - Do NOT reuse themes, scenarios, or structures from previous exercises.
    - Avoid generic school-style prompts.
    - Each exercise must feel clearly different from a typical vocabulary task.
    """
    
    client = OpenAIApi().get_client()
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You create writing exercises for language learners."},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.9,
        max_tokens=250
    )

    content = response.choices[0].message.content
    data = json.loads(content)

    print("Data from OpenAI:", data)
    new_writing = WritingExercise(
        prompt=data["prompt"],
        date_created=datetime.now().strftime('%Y-%m-%d')
    )
    add_instance(new_writing)
    word.writing.add(new_writing)
    session.commit()

    return new_writing