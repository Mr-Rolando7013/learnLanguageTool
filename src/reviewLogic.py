from openai import OpenAI
from api import *
import json
from model import *
from datetime import datetime



def calculate_new_ef_interval(data, word):
    weighted_total = 8.7
    weighted_correct = 0.0
    if data["translation"] == data["definition"]:
        weighted_correct += 1.0
    
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
    word.multiple_choice_exercise_id.append(new_mcq)
    session.commit()
