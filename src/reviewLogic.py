from openai import OpenAI
from api import *
import json
from model import *
from datetime import datetime
import random

def calculate_new_ef_interval(data, word):
    myWord = getWordById(word)
    #print("DATA CALCULATE: ", data)
    weighted_correct = 0.0
    isSentence2 = False
    isSentence3 = False

    if data["step"] == "translation":
        if data["answer"] == myWord.translation:
            weighted_correct += 1.0

    if data["step"] == "sentence1":
        if data["answer"] == myWord.sentence1_translation:
            weighted_correct += 1.0

    if data["step"] == "sentence2":
        if data["answer"] == myWord.sentence2_translation:
            isSentence2 = True
            weighted_correct += 1.0

    if data["step"] == "sentence3":
        isSentence3 = True
        if data["answer"] == myWord.sentence3_translation:
            weighted_correct += 1.0

    if data["step"] == "mcq1":
        mcq1 = find_mcq_exercise_by_word(myWord, data["question"])
        mcq1_correct_answer = get_mcq_correct_answer_by_mcq_answer_id(mcq1, data["answer"])
        if mcq1_correct_answer:
            weighted_correct += 0.6

    if data["step"] == "mcq2":
        mcq2 = find_mcq_exercise_by_word(myWord, data["question"])
        mcq2_correct_answer = get_mcq_correct_answer_by_mcq_answer_id(mcq2, data["answer"])
        if mcq2_correct_answer:
            weighted_correct += 0.6

    if data["step"] == "cloze1":
        cloze1 = find_cloze_exercise_by_word(myWord, data["question"])
        if data["answer"] == cloze1.answer:
            weighted_correct += 1.0

    if data["step"] == "cloze2":
        cloze2 = find_cloze_exercise_by_word(myWord, data["question"])
        if data["answer"] == cloze2.answer:
            weighted_correct += 1.0

    if data["step"] == "writing":
        writing1 = get_writing_exercise_by_word(myWord, data["question"])
        grade = review_writing_exercise(writing1, data["answer"])
        print("GRADEEE: ", grade)
        if grade > 7.0:
            weighted_correct += 1.5
    
    return {"word_id": word, "weighted_correct": weighted_correct, "isSentence2": isSentence2, "isSentence3": isSentence3}
    
def generate_mcq_exercise(word):
    MCQ_ARCHETYPES = [
        "Ask directly for the meaning of the Romanian word in English.",
        "Include a short Romanian sentence using the word and ask what it most likely means in that context.",
        "Ask which option is NOT a correct meaning of the word.",
        "Ask which English option best matches the word’s usage, not its definition.",
        "Test a close nuance by offering near-synonyms and asking for the exact meaning."
    ]

    # Pick a random archetype each call
    archetype_rule = random.choice(MCQ_ARCHETYPES)

    prompt = f"""
    You are generating a Romanian vocabulary multiple choice question.

    Target word: "{word.word}"

    Instruction:
    {archetype_rule}

    Return ONLY valid JSON with this structure:
    {{
        "question": "...",
        "choices": ["...", "...", "...", "..."],
        "correct_index": 0
    }}

    Rules:
    - Exactly 4 choices
    - Only ONE choice is correct
    - Distractors must be plausible but clearly incorrect
    - Avoid paraphrasing standard definition questions
    - Avoid starting questions with "What does" unless explicitly required
    - Vary the task being tested, not just the wording
    - Make the phrasing of the question different each time
    - Avoid always placing the correct answer first
    """

    client = OpenAIApi().get_client()
    existing_questions = [mcq.question.lower() for mcq in word.mcq]

    attempts = 0
    MAX_ATTEMPTS = 5
    while attempts < MAX_ATTEMPTS:
        attempts += 1

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You create diverse vocabulary MCQs for language learners."},
                {"role": "user", "content": prompt}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "mcq_exercise",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string"},
                            "choices": {
                                "type": "array",
                                "items": {"type": "string"},
                                "minItems": 4,
                                "maxItems": 4
                            },
                            "correct_index": {"type": "integer", "minimum": 0, "maximum": 3}
                        },
                        "required": ["question", "choices", "correct_index"],
                        "additionalProperties": False
                    }
                }
            },
            temperature=1.0,  # higher temperature → more randomness
            max_tokens=300
        )

        data = json.loads(response.choices[0].message.content)
        question_text = data["question"].lower()

        # Reject duplicates
        if not any(question_text in q or q in question_text for q in existing_questions):
            break
    else:
        print("⚠️ Could not generate a unique MCQ after retries")

    # Shuffle choices for extra randomness
    choices = data["choices"][:]
    correct_answer = choices[data["correct_index"]]
    random.shuffle(choices)
    new_correct_index = choices.index(correct_answer)

    new_mcq = MultipleChoiceExercise(
        question=data["question"],
        option1=choices[0],
        option2=choices[1],
        option3=choices[2],
        option4=choices[3],
        correct_answer=correct_answer,
        date_created=datetime.now().strftime('%Y-%m-%d')
    )

    add_instance(new_mcq)
    word.mcq.append(new_mcq)
    session.commit()

    print("Generated MCQ:", data)
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
        response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "cloze_exercise",
            "schema": {
                "type": "object",
                "properties": {
                    "sentence": {
                        "description": "Romanian sentence with ___ replacing the target word",
                        "type": "string"
                    },
                    "answer": {
                        "description": "The missing word",
                        "type": "string"
                    }
                },
                "required": ["sentence", "answer"],
                "additionalProperties": False
            }
        }
    },
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
        response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "writing_exercise",
            "schema": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "A vivid Romanian writing prompt that requires using the target word"
                    }
                },
                "required": ["prompt"],
                "additionalProperties": False
            }
        }
    },
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

def review_writing_exercise(writing_exercise, user_reply):
    prompt = f"""
    You are a Romanian teacher and you need to check if the following reply: "{user_reply}" is correct based on the following writing question prompt: "{writing_exercise.prompt}"
    
    Rules:
    - Give me a numerical grade from 0.0 (worst) to 10.0 (perfect).
    - Grade this question based on grammar, spelling, and correct context.
    - Spelling is less impactful to the grade.
    - Proper grammar and correct context are the most important.
    - Please only provide the numerical grade, without any explanation or extra text.
    """

    # Create an OpenAI API client
    client = OpenAIApi().get_client()
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are an expert Romanian language teacher."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.9,
        max_tokens=50,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "grading_writing_exercise",
                "schema": {
                    "type": "object",
                    "properties": {
                        "grade": {
                            "type": "string",
                            "description": "The score of an answer that a language student provided for a romanian writing exercise"
                        }
                    },
                    "required": ["grade"],
                    "additionalProperties": False
                }
            }
        }
    )
    content = response.choices[0].message.content
    data = json.loads(content)
    print("GRADE RESPONSE", data)

    grade = float(data["grade"])

    return grade