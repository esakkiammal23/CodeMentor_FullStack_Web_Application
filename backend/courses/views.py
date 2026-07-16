import requests
import os
import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from django.utils import timezone
from django.http import StreamingHttpResponse
from .models import Topic, UserProgress

# ─── Topic definitions: minimum 10 per language ───────────────
TOPICS_DATA = {
    'python': [
        'Introduction to Python',
        'Variables and Data Types',
        'Operators',
        'Control Flow (if/else)',
        'Loops (for/while)',
        'Functions',
        'Lists and Tuples',
        'Dictionaries and Sets',
        'File Handling',
        'Exception Handling',
        'OOP',
        'Modules and Packages',
    ],
    'java': [
        'Introduction to Java',
        'Data Types and Variables',
        'Operators',
        'Control Statements',
        'Arrays',
        'Methods',
        'OOP Concepts',
        'Inheritance',
        'Interfaces',
        'Exception Handling',
        'Collections Framework',
        'Multithreading Basics',
    ],
    'ai': [
        'What is AI?',
        'History of AI',
        'Intelligent Agent',
        'Search Algorithms',
        'Knowledge Representation',
        'Natural Language Processing',
        'Computer Vision',
        'AI Ethics',
        'AI Applications',
        'Reasoning and Planning in AI ',
        'Future of AI',
        'Expert Systems'
    ],
    'ml': [
        'What is ML?',
        'Types of ML',
        'Data Preprocessing',
        'Linear Regression',
        'Logistic Regression',
        'Decision Trees',
        'Random Forest',
        'Support Vector Machines',
        'K-Means Clustering',
        'Neural Networks',
        'Model Evaluation',
        'ML Project Lifecycle',
    ],
}

# Built-in fallback content so learning works even without Ollama
FALLBACK_CONTENT = {
    'python': {
        'Introduction to Python': """🐍 Introduction to Python

Python is a high-level, beginner-friendly programming language created by Guido van Rossum in 1991. It is known for its simple, readable syntax that feels almost like plain English.

📌 Key Concepts:
- Python is interpreted — code runs line by line, making debugging easy
- It is dynamically typed — no need to declare variable types
- Python is used in web development, data science, AI, automation, and more
- Python uses indentation (spaces) instead of curly braces to define blocks

💻 Example:
print("Hello, World!")
name = "Arjun"
print("Welcome,", name)

🎯 Fun Fact:
Python is named after the British comedy show "Monty Python's Flying Circus" — not the snake!""",

'Variables and Data Types': """📦 Variables and Data Types

A variable is a container that stores data. In Python, you don't need to declare the type — Python figures it out automatically.

📌 Key Concepts:
- int — whole numbers: x = 10
- float — decimal numbers: pi = 3.14
- str — text: name = "Tamil"
- bool — True or False: is_student = True
- You can check type using type() function

💻 Example:
age = 25           # int
height = 5.9       # float
name = "Priya"     # string
is_passed = True   # bool

print(type(age))     # <class 'int'>
print(type(name))    # <class 'str'>

🎯 Tip:
Variable names cannot start with a number. Use snake_case like my_name, not myName.""",

        'Operators': """➕ Operators in Python

Operators are symbols that perform operations on variables and values.

📌 Types of Operators:
- Arithmetic: +, -, *, /, //, %, **
- Comparison: ==, !=, >, <, >=, <=
- Logical: and, or, not
- Assignment: =, +=, -=, *=

💻 Example:
a = 10
b = 3

print(a + b)   # 13
print(a // b)  # 3  (floor division)
print(a ** b)  # 1000 (power)
print(a > b)   # True
print(a == b)  # False

x = 5
x += 3   # same as x = x + 3
print(x) # 8

🎯 Tip:
// gives the quotient,   % gives the remainder of division.""",

        'Control Flow (if/else)': """🔀 Control Flow — if / elif / else

Control flow lets your program make decisions based on conditions.

📌 Key Concepts:
- if block runs when condition is True
- elif checks another condition if the first was False
- else runs when all conditions are False
- Indentation (4 spaces) is mandatory in Python

💻 Example:
marks = 75

if marks >= 90:
    print("Grade A")
elif marks >= 75:
    print("Grade B")
elif marks >= 50:
    print("Grade C")
else:
    print("Fail")

# Output: Grade B

🎯 Tip:
You can write one-line if: print("Pass") if marks >= 50 else print("Fail")""",

'Loops (for/while)': """🔁 Loops in Python

Loops are used to repeat a block of code multiple times.

📌 Key Concepts:
- for loop — iterate over a sequence (list, range, string)
- while loop — repeat as long as condition is True
- break — exit the loop early
- continue — skip current iteration

💻 Example:
# for loop
for i in range(1, 6):
    print(i)   # prints 1 to 5

# while loop
count = 0
while count < 3:
    print("Hello", count)
    count += 1

# break example
for i in range(10):
    if i == 5:
        break
    print(i)   # prints 0 to 4

🎯 Tip:
range(start, stop, step) — range(0, 10, 2) gives 0, 2, 4, 6, 8""",

'Functions': """⚙️ Functions in Python

A function is a reusable block of code that performs a specific task.

📌 Key Concepts:
- Define with def keyword
- Functions can take parameters (inputs)
- Functions can return values using return
- Default parameter values can be set

💻 Example:
def greet(name, language="English"):
    if language == "Tamil":
        return f"Vanakkam, {name}!"
    return f"Hello, {name}!"

print(greet("Karthik"))           # Hello, Karthik!
print(greet("Priya", "Tamil"))    # Vanakkam, Priya!

def add(a, b):
    return a + b

result = add(5, 3)
print(result)   # 8

🎯 Tip:
Functions help avoid repeating code. Write once, use many times!""",

'Lists and Tuples': """📋 Lists and Tuples

Lists and tuples are used to store multiple values in a single variable.

📌 Key Concepts:
- List — mutable (changeable), uses square brackets []
- Tuple — immutable (cannot change), uses parentheses ()
- Both support indexing (starts at 0) and slicing
- Common list methods: append(), remove(), pop(), sort()

💻 Example:
# List
fruits = ["apple", "banana", "mango"]
fruits.append("orange")
fruits[0] = "grape"
print(fruits)       # ['grape', 'banana', 'mango', 'orange']
print(fruits[1])    # banana

# Tuple
colors = ("red", "green", "blue")
print(colors[0])    # red
# colors[0] = "yellow"  ← This will throw an error!

🎯 Tip:
Use tuple when data should not change — like days of week, coordinates.""",

'Dictionaries and Sets': """📖 Dictionaries and Sets

Dictionaries store key-value pairs. Sets store unique values only.

📌 Key Concepts:
- Dictionary — key: value pairs, uses {}
- Access value using key: dict[key]
- Common methods: keys(), values(), items(), get()
- Set — unordered, no duplicates, also uses {}

💻 Example:
# Dictionary
student = {
    "name": "Ravi",
    "age": 20,
    "grade": "A"
}
print(student["name"])        # Ravi
student["city"] = "Chennai"   # add new key
print(student.get("age"))     # 20

# Set
numbers = {1, 2, 3, 2, 1}
print(numbers)   # {1, 2, 3} — duplicates removed

🎯 Tip:
Use dictionary when you need to label your data, like a mini-database.""",

'File Handling': """📁 File Handling in Python

Python can read from and write to files on your computer.

📌 Key Concepts:
- open(filename, mode) — opens a file
- Modes: 'r' read, 'w' write, 'a' append, 'r+' read+write
- Always close files or use with statement
- with open() automatically closes the file

💻 Example:
# Writing to a file
with open("notes.txt", "w") as f:
    f.write("Hello, this is my first file!\\n")
    f.write("Python file handling is easy.")

# Reading from a file
with open("notes.txt", "r") as f:
    content = f.read()
    print(content)

# Reading line by line
with open("notes.txt", "r") as f:
    for line in f:
        print(line.strip())

🎯 Tip:
Always use 'with open()' — it handles closing the file automatically even if an error occurs.""",

'Exception Handling': """⚠️ Exception Handling

Exception handling lets your program deal with errors gracefully instead of crashing.

📌 Key Concepts:
- try — the code that might cause an error
- except — what to do if error occurs
- finally — always runs, error or not
- raise — manually trigger an error
- Common exceptions: ValueError, ZeroDivisionError, FileNotFoundError

💻 Example:
try:
    num = int(input("Enter a number: "))
    result = 100 / num
    print("Result:", result)
except ValueError:
    print("That's not a valid number!")
except ZeroDivisionError:
    print("Cannot divide by zero!")
finally:
    print("Program finished.")

🎯 Tip:
Never leave except: pass — always handle the error meaningfully so you know what went wrong.""",

'OOP Basics': """🏗️ Object Oriented Programming (OOP)

OOP is a way of organising code using objects that have properties and behaviours.

📌 Key Concepts:
- Class — blueprint for creating objects
- Object — instance of a class
- __init__ — constructor, runs when object is created
- self — refers to the current object
- Attributes — variables inside a class
- Methods — functions inside a class

💻 Example:
class Student:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def introduce(self):
        return f"Hi, I am {self.name}, aged {self.age}."

    def is_adult(self):
        return self.age >= 18

s1 = Student("Priya", 20)
s2 = Student("Ravi", 16)

print(s1.introduce())    # Hi, I am Priya, aged 20.
print(s2.is_adult())     # False

🎯 Tip:
Think of a class like a cookie cutter and objects as the cookies made from it.""",

'Modules and Packages': """📦 Modules and Packages

A module is a Python file containing functions and variables you can reuse. A package is a folder of modules.

📌 Key Concepts:
- import module — import entire module
- from module import function — import specific item
- Built-in modules: math, os, random, datetime
- Install external packages using pip

💻 Example:
import math
print(math.sqrt(16))     # 4.0
print(math.pi)           # 3.14159...

import random
print(random.randint(1, 10))   # random number 1-10

from datetime import datetime
now = datetime.now()
print(now.strftime("%d-%m-%Y"))   # today's date

# Install external package:
# pip install requests

🎯 Tip:Python has thousands of free packages at pypi.org — there's a package for almost everything!"""
    },

'java': {
        'Introduction to Java': """☕ Introduction to Java

Java is a powerful, object-oriented programming language created by James Gosling at Sun Microsystems in 1995. It follows "Write Once, Run Anywhere" principle.

📌 Key Concepts:
- Java is compiled to bytecode, then run on JVM (Java Virtual Machine)
- It is strongly typed — you must declare variable types
- Java is platform-independent
- Everything in Java is inside a class

💻 Example:
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
        System.out.println("Welcome to Java!");
    }
}

🎯 Tip:
Java is used to power Android apps, enterprise banking systems, and billions of devices worldwide.""",

'Data Types and Variables': """📦 Data Types and Variables in Java

Java has two types of data types: primitive and non-primitive (reference types).

📌 Primitive Types:
- int — whole numbers: int age = 25;
- double — decimals: double pi = 3.14;
- char — single character: char grade = 'A';
- boolean — true/false: boolean passed = true;
- long, float, short, byte — other numeric types

💻 Example:
public class DataTypes {
    public static void main(String[] args) {
        int age = 20;
        double height = 5.9;
        String name = "Priya";
        boolean isStudent = true;
        char grade = 'A';

        System.out.println("Name: " + name);
        System.out.println("Age: " + age);
        System.out.println("Passed: " + isStudent);
    }
}

🎯 Tip:String is not a primitive type in Java — it is an object. That's why it starts with a capital S.""",
    },

'ai': {'What is AI?': """🤖 What is Artificial Intelligence?

Artificial Intelligence (AI) is the simulation of human intelligence by computer systems. It allows machines to learn, reason, and make decisions.

📌 Key Concepts:
- AI enables computers to perform tasks that normally require human intelligence
- Examples: voice assistants (Siri, Alexa), recommendation systems (Netflix, YouTube), self-driving cars
- AI works by processing large amounts of data and finding patterns
- Main branches: Machine Learning, Deep Learning, NLP, Computer Vision, Robotics

📊 AI vs Normal Programming:
- Normal program: programmer writes exact rules
- AI program: machine learns rules from data

🌍 Real-world Applications:
- Healthcare: disease diagnosis from X-rays
- Finance: fraud detection in transactions
- Education: personalised learning systems
- Transport: route optimisation, autonomous vehicles

🎯 Fun Fact:
The term "Artificial Intelligence" was coined by John McCarthy in 1956 at a conference at Dartmouth College.""",
    },

'ml': {
        'What is ML?': """📊 What is Machine Learning?

Machine Learning (ML) is a subset of AI where systems learn from data and improve their performance without being explicitly programmed for every task.

📌 Key Concepts:
- ML algorithms find patterns in data and make predictions
- The more data you feed, the better the model learns
- ML is behind spam filters, product recommendations, and medical diagnosis

📊 How ML Works:
1. Collect data
2. Prepare and clean data
3. Choose an algorithm
4. Train the model on data
5. Evaluate accuracy
6. Deploy and use

🔍 Simple Example:
Imagine teaching a child to identify cats. You show 1000 cat photos and 1000 non-cat photos. The child learns the pattern. ML works the same way — show data, it learns the pattern.

🎯 Fun Fact:
Netflix's recommendation system saves the company $1 billion per year by keeping users engaged through ML-powered suggestions.""",
    }
}

def get_fallback(lang, topic_name):
    lang_data = FALLBACK_CONTENT.get(lang, {})
    if topic_name in lang_data:
        return lang_data[topic_name]
    return f"""📚 {topic_name}

This topic is part of the {lang.upper()} course.

📌 Key Points to Learn:
- This is an important concept in {lang.upper()}
- Understanding this topic helps you build stronger programming skills
- Practice with small examples to master this concept

💡 Study Tip:
Search for "{topic_name} in {lang}" on Google or YouTube for video tutorials and examples.

🎯 Keep going! Every topic you complete brings you closer to your certificate."""


def seed_topics():
    for lang, topics in TOPICS_DATA.items():
        for i, name in enumerate(topics):
            Topic.objects.get_or_create(
                programming_language=lang, name=name,
                defaults={'order': i}
            )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_topics(request):
    seed_topics()
    lang = request.query_params.get('language', 'python')
    topics = Topic.objects.filter(programming_language=lang)
    user_progress = UserProgress.objects.filter(user=request.user, topic__in=topics)
    completed_ids = set(p.topic_id for p in user_progress if p.completed)
    data = [
        {
            'id': t.id,
            'name': t.name,
            'order': t.order,
            'completed': t.id in completed_ids,
        }
        for t in topics
    ]
    return Response({'topics': data, 'language': lang})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def learn_topic(request):
    topic_id = request.data.get('topic_id')
    interface_lang = request.data.get('interface_language', 'english')

    content = None   # ✅ FIX: inside function

    try:
        topic = Topic.objects.get(id=topic_id)
    except Topic.DoesNotExist:
        return Response({'error': 'Topic not found'}, status=404)

    lang_instructions = {
        'english': 'Respond in clear English.',
        'tamil': 'Respond in Tamil language (தமிழ்).',
        'hindi': 'Respond in Hindi language (हिंदी).',
        'tanglish': 'Respond in Tanglish (Tamil words written in English letters mixed with English).',
        'malayalam':'Respond in Malayalam language (മലയാളം).',
    }

    prompt = f"""You are an expert programming teacher AI.
Your job is to teach ONLY this topic:
Topic: "{topic.name}"
Language: {topic.programming_language.upper()}

{lang_instructions.get(interface_lang, lang_instructions['english'])}

STRICT RULES:
- Teach step by step like ChatGPT
- Do NOT go outside this topic
- Keep it simple for beginners
- Use examples
- Use friendly tone

FORMAT:
1. Explanation (simple)
2. Key Points
3. Example
4. Small Practice Task

At the end, ask:
"Do you have any doubts about this topic?"
"""

    try:
        response = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
        "Content-Type": "application/json"
    },
    json={
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": prompt}
        ],
        "temperature": 0.7
    },
    timeout=20
)
        

        # Debug
        print("STATUS:", response.status_code)
        print("RAW:", response.text)

        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content']
        else:
            print("API Error:", response.text)

    except Exception as e:
        print("Error:", str(e))

    # ✅ fallback (correct place)
    if not content:
        content = get_fallback(topic.programming_language, topic.name)

    return Response({
        'topic': topic.name,
        'language': topic.programming_language,
        'content': content,
        'interface_language': interface_lang,
    })
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ask_doubt(request):
    topic_id = request.data.get('topic_id')
    question = request.data.get('question', '').strip()
    interface_lang = request.data.get('interface_language', 'english')

    if not question:
        return Response({'error': 'Please enter a question.'}, status=400)

    try:
        topic = Topic.objects.get(id=topic_id)
    except Topic.DoesNotExist:
        return Response({'error': 'Topic not found'}, status=404)

    lang_instructions = {
        'english': 'Answer in clear simple English.',
        'tamil': 'Answer in Tamil language (தமிழ்).',
        'hindi': 'Answer in Hindi language (हिंदी).',
        'tanglish': 'Answer in Tanglish (Tamil in English letters mixed with English).',
    }
    print("QUESTION:", question)
    answer = None



    try:
        response = requests.post(
    "https://api.groq.com/openai/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
        "Content-Type": "application/json"
    },
    json={
        "model": "llama-3.1-8b-instant",
        "messages": [
            {
                "role": "system",
                "content": f"""
You are a smart AI tutor like ChatGPT.

RULES:
- Answer ONLY the user's doubt
- Be clear and simple
- Keep it SHORT
- Use examples if helpful
- Talk like a friendly teacher

Topic: {topic.name}
Language: {topic.programming_language}

{lang_instructions.get(interface_lang, lang_instructions['english'])}
"""
            },
            {
                "role": "user",
                "content": f"My doubt is: {question}"
            }
        ],
        "temperature": 0.7
    },
    timeout=20
)
        

        if response.status_code == 200:
            answer = response.json()['choices'][0]['message']['content']
        else:
            print("Groq Error:", response.status_code, response.text)

    except Exception as e:
        print("Error:", str(e))

    if not answer:
        answer = f"""
I couldn't fetch AI response. Here's help:

{get_fallback(topic.programming_language, topic.name)}

Your question:
{question}
"""

    return Response({'answer': answer, 'question': question})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_complete(request):
    topic_id = request.data.get('topic_id')
    try:
        topic = Topic.objects.get(id=topic_id)
    except Topic.DoesNotExist:
        return Response({'error': 'Topic not found'}, status=404)

    progress, _ = UserProgress.objects.get_or_create(user=request.user, topic=topic)
    progress.completed = True
    progress.completed_at = timezone.now()
    progress.save()
    return Response({'success': True, 'message': f'"{topic.name}" marked as complete!'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_progress(request):
    lang = request.query_params.get('language', 'python')
    topics = Topic.objects.filter(programming_language=lang)
    total = topics.count()
    completed = UserProgress.objects.filter(
        user=request.user, topic__in=topics, completed=True
    ).count()
    return Response({
        'language': lang,
        'total_topics': total,
        'completed_topics': completed,
        'percentage': round((completed / total * 100) if total > 0 else 0, 1),
        'all_completed': completed == total and total > 0,
    })