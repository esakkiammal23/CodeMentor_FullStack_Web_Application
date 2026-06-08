import random
import subprocess
import tempfile
import os
import re
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from courses.models import Topic, UserProgress
from .models import TopicTestAttempt, CourseTestAttempt, LeaderboardEntry

User = get_user_model()

# ═══════════════════════════════════════════════════════════════
# HELPER — generate generic questions when no specific ones exist
# ═══════════════════════════════════════════════════════════════

def generic_questions(topic_name, prog_lang, count=12):
    base = [
        {"question": f"What is the main purpose of {topic_name} in {prog_lang.upper()}?",
         "options": ["A) To complicate code","B) To organise and structure code better","C) To slow execution","D) To add syntax errors"],
         "correct": "B) To organise and structure code better",
         "explanation": f"{topic_name} helps organise and structure {prog_lang.upper()} code."},
        {"question": f"Which keyword or concept is central to {topic_name}?",
         "options": ["A) print","B) return","C) The core concept of the topic","D) import"],
         "correct": "C) The core concept of the topic",
         "explanation": f"The core concept drives the functionality of {topic_name}."},
        {"question": f"When do you use {topic_name} in {prog_lang.upper()}?",
         "options": ["A) Never","B) Only for beginners","C) When the situation requires it","D) Only in advanced programs"],
         "correct": "C) When the situation requires it",
         "explanation": f"{topic_name} is used whenever its specific functionality is needed."},
        {"question": f"Which of these best describes {topic_name}?",
         "options": ["A) A data type","B) A fundamental programming concept","C) A compiler","D) A hardware component"],
         "correct": "B) A fundamental programming concept",
         "explanation": f"{topic_name} is a fundamental programming concept."},
        {"question": f"What is a benefit of understanding {topic_name}?",
         "options": ["A) Slower code","B) More errors","C) Better code quality","D) None"],
         "correct": "C) Better code quality",
         "explanation": f"Understanding {topic_name} improves code quality."},
        {"question": f"Is {topic_name} unique to {prog_lang.upper()}?",
         "options": ["A) Yes, only in this language","B) No, most languages have similar concepts","C) It doesn't exist","D) Only in Python"],
         "correct": "B) No, most languages have similar concepts",
         "explanation": "Most programming concepts exist across multiple languages."},
        {"question": f"Which statement about {topic_name} is TRUE?",
         "options": ["A) It is optional to learn","B) It is a core building block of {prog_lang.upper()}","C) Only experts use it","D) It has no real use"],
         "correct": "B) It is a core building block of {prog_lang.upper()}",
         "explanation": f"{topic_name} is a core building block."},
        {"question": f"What should you do after learning {topic_name}?",
         "options": ["A) Skip practice","B) Practice with small examples","C) Move on immediately","D) Ignore it"],
         "correct": "B) Practice with small examples",
         "explanation": "Practice solidifies understanding of any topic."},
        {"question": f"How does {topic_name} relate to other topics in {prog_lang.upper()}?",
         "options": ["A) Completely isolated","B) Builds on earlier concepts","C) Replaces all other topics","D) Not related"],
         "correct": "B) Builds on earlier concepts",
         "explanation": "Topics in programming build on each other."},
        {"question": f"Which resource helps learn {topic_name} better?",
         "options": ["A) Ignoring it","B) Reading without practice","C) Writing code examples","D) Memorising theory only"],
         "correct": "C) Writing code examples",
         "explanation": "Writing code is the best way to learn programming concepts."},
        {"question": f"What is the first step to master {topic_name}?",
         "options": ["A) Skip to advanced topics","B) Understand the basic definition","C) Use it in production","D) Ask someone else to do it"],
         "correct": "B) Understand the basic definition",
         "explanation": "Start with the basic definition before diving deeper."},
        {"question": f"What makes {topic_name} important in {prog_lang.upper()}?",
         "options": ["A) It makes code longer","B) It solves real programming problems","C) It is just theory","D) It is rarely used"],
         "correct": "B) It solves real programming problems",
         "explanation": f"{topic_name} solves real programming problems."},
    ]
    qs = [dict(q) for q in base[:count]]
    random.shuffle(qs)
    for i, q in enumerate(qs):
        q['id'] = i + 1
    return qs


# ═══════════════════════════════════════════════════════════════
# TOPIC QUESTION BANK
# Structure: TOPIC_Q[lang][topic_name][iface_lang] = list of 12+ dicts
# Fallback chain: requested lang → english → generic
# ═══════════════════════════════════════════════════════════════

def _shuffle_pick(pool, n=10):
    qs = [dict(q) for q in pool]
    random.shuffle(qs)
    for i, q in enumerate(qs[:n]):
        q['id'] = i + 1
    return qs[:n]


TOPIC_Q = {

# ─────────────────── PYTHON ────────────────────────────────────
'python': {

'Introduction to Python': {
'english': [
  {"question":"Who created Python?","options":["A) James Gosling","B) Guido van Rossum","C) Dennis Ritchie","D) Bjarne Stroustrup"],"correct":"B) Guido van Rossum","explanation":"Python was created by Guido van Rossum in 1991."},
  {"question":"Python is which type of language?","options":["A) Compiled only","B) Interpreted","C) Assembly","D) Machine code"],"correct":"B) Interpreted","explanation":"Python runs line-by-line via an interpreter."},
  {"question":"What does Python use instead of curly braces?","options":["A) Parentheses","B) Square brackets","C) Indentation","D) Semicolons"],"correct":"C) Indentation","explanation":"Python uses spaces/tabs for code blocks."},
  {"question":"Which year was Python first released?","options":["A) 1985","B) 1991","C) 2000","D) 2008"],"correct":"B) 1991","explanation":"Python 1.0 released in 1991."},
  {"question":"Python is mainly known for?","options":["A) Complex syntax","B) Simple readable syntax","C) Low-level programming","D) Hardware control"],"correct":"B) Simple readable syntax","explanation":"Python emphasises readability."},
  {"question":"Which command runs a Python file?","options":["A) run file.py","B) execute file.py","C) python file.py","D) start file.py"],"correct":"C) python file.py","explanation":"python filename.py runs a Python script."},
  {"question":"Python is named after?","options":["A) A snake","B) Monty Python comedy show","C) A scientist","D) A mountain"],"correct":"B) Monty Python comedy show","explanation":"Named after Monty Python's Flying Circus."},
  {"question":"Which is NOT a use of Python?","options":["A) Web development","B) Data science","C) OS kernel development","D) Automation"],"correct":"C) OS kernel development","explanation":"OS kernels use C/C++, not Python."},
  {"question":"Python's print() function is used to?","options":["A) Store values","B) Display output","C) Take input","D) Define variables"],"correct":"B) Display output","explanation":"print() shows output on screen."},
  {"question":"Which extension do Python files use?","options":["A) .java","B) .txt","C) .py","D) .python"],"correct":"C) .py","explanation":"Python files end with .py."},
  {"question":"Python uses which type of typing?","options":["A) Static","B) Dynamic","C) Manual","D) Strict"],"correct":"B) Dynamic","explanation":"Python determines types at runtime."},
  {"question":"Which Python version is current standard?","options":["A) Python 1","B) Python 2","C) Python 3","D) Python 4"],"correct":"C) Python 3","explanation":"Python 3 is the current standard."},
],
'tamil': [
  {"question":"Python-ஐ உருவாக்கியவர் யார்?","options":["A) James Gosling","B) Guido van Rossum","C) Dennis Ritchie","D) Bjarne Stroustrup"],"correct":"B) Guido van Rossum","explanation":"Python-ஐ Guido van Rossum 1991-ல் உருவாக்கினார்."},
  {"question":"Python எந்த வகையான மொழி?","options":["A) Compiled","B) Interpreted","C) Assembly","D) Machine"],"correct":"B) Interpreted","explanation":"Python interpreter மூலம் line-by-line run ஆகும்."},
  {"question":"Python curly braces பதிலாக என்ன?","options":["A) Parentheses","B) Square brackets","C) Indentation","D) Semicolons"],"correct":"C) Indentation","explanation":"Python indentation மூலம் blocks define செய்யும்."},
  {"question":"Python முதல் எந்த ஆண்டு வெளியானது?","options":["A) 1985","B) 1991","C) 2000","D) 2008"],"correct":"B) 1991","explanation":"Python 1.0, 1991-ல் வெளியானது."},
  {"question":"Python எதற்காக பிரபலமானது?","options":["A) Complex syntax","B) Simple readable syntax","C) Low-level programming","D) Hardware control"],"correct":"B) Simple readable syntax","explanation":"Python எளிதான syntax-க்காக பிரபலம்."},
  {"question":"Python file run செய்ய எந்த command?","options":["A) run file.py","B) execute file.py","C) python file.py","D) start file.py"],"correct":"C) python file.py","explanation":"python filename.py Python script run செய்யும்."},
  {"question":"Python பெயர் எதிலிருந்து வந்தது?","options":["A) பாம்பு","B) Monty Python comedy show","C) விஞ்ஞானி","D) மலை"],"correct":"B) Monty Python comedy show","explanation":"Monty Python's Flying Circus-ல் இருந்து பெயர் வந்தது."},
  {"question":"Python பயன்படாத இடம்?","options":["A) Web development","B) Data science","C) OS kernel","D) Automation"],"correct":"C) OS kernel","explanation":"OS kernels-க்கு C/C++ பயன்படுகிறது."},
  {"question":"print() function என்ன செய்கிறது?","options":["A) Values சேமிக்கும்","B) Output காட்டும்","C) Input எடுக்கும்","D) Variables define செய்யும்"],"correct":"B) Output காட்டும்","explanation":"print() screen-ல் output காட்டும்."},
  {"question":"Python files எந்த extension?","options":["A) .java","B) .txt","C) .py","D) .python"],"correct":"C) .py","explanation":"Python files .py extension-உடன் முடியும்."},
  {"question":"Python எந்த வகை typing?","options":["A) Static","B) Dynamic","C) Manual","D) Strict"],"correct":"B) Dynamic","explanation":"Python runtime-ல் types கண்டுபிடிக்கும்."},
  {"question":"தற்போதைய Python version?","options":["A) Python 1","B) Python 2","C) Python 3","D) Python 4"],"correct":"C) Python 3","explanation":"Python 3 தற்போதைய standard."},
],
'tanglish': [
  {"question":"Python-a create pannathu yaar?","options":["A) James Gosling","B) Guido van Rossum","C) Dennis Ritchie","D) Bjarne Stroustrup"],"correct":"B) Guido van Rossum","explanation":"Python-a Guido van Rossum 1991-la create pannaar."},
  {"question":"Python ethu type language?","options":["A) Compiled","B) Interpreted","C) Assembly","D) Machine"],"correct":"B) Interpreted","explanation":"Python interpreter use panni line-by-line run aagum."},
  {"question":"Python curly braces pakkam ethu use pannum?","options":["A) Parentheses","B) Square brackets","C) Indentation","D) Semicolons"],"correct":"C) Indentation","explanation":"Python indentation use panni blocks define pannum."},
  {"question":"Python mudhalla ethu varusham release?","options":["A) 1985","B) 1991","C) 2000","D) 2008"],"correct":"B) 1991","explanation":"Python 1.0, 1991-la release aacchu."},
  {"question":"Python endhatharku famous?","options":["A) Complex syntax","B) Simple readable syntax","C) Low-level programming","D) Hardware control"],"correct":"B) Simple readable syntax","explanation":"Python simple syntax-ku famous."},
  {"question":"Python file run panna ethu command?","options":["A) run file.py","B) execute file.py","C) python file.py","D) start file.py"],"correct":"C) python file.py","explanation":"python filename.py Python script run pannum."},
  {"question":"Python peru engirundhu vandhuthu?","options":["A) Pambu","B) Monty Python comedy show","C) Scientist","D) Malai"],"correct":"B) Monty Python comedy show","explanation":"Monty Python's Flying Circus-la irundhu peru vandhuthu."},
  {"question":"Python use illaadhadu ethu?","options":["A) Web development","B) Data science","C) OS kernel","D) Automation"],"correct":"C) OS kernel","explanation":"OS kernels-ku C/C++ use aagum."},
  {"question":"print() function enna pannum?","options":["A) Values store pannum","B) Output kaattum","C) Input edukum","D) Variables define pannum"],"correct":"B) Output kaattum","explanation":"print() screen-la output kaattum."},
  {"question":"Python files ethu extension?","options":["A) .java","B) .txt","C) .py","D) .python"],"correct":"C) .py","explanation":"Python files .py-la mudiym."},
  {"question":"Python ethu type typing?","options":["A) Static","B) Dynamic","C) Manual","D) Strict"],"correct":"B) Dynamic","explanation":"Python runtime-la types kandupidikkum."},
  {"question":"Ippo irukka Python version ethu?","options":["A) Python 1","B) Python 2","C) Python 3","D) Python 4"],"correct":"C) Python 3","explanation":"Python 3 current standard."},
],
'hindi': [
  {"question":"Python किसने बनाया?","options":["A) James Gosling","B) Guido van Rossum","C) Dennis Ritchie","D) Bjarne Stroustrup"],"correct":"B) Guido van Rossum","explanation":"Python को Guido van Rossum ने 1991 में बनाया।"},
  {"question":"Python किस प्रकार की भाषा है?","options":["A) Compiled","B) Interpreted","C) Assembly","D) Machine"],"correct":"B) Interpreted","explanation":"Python interpreter के ज़रिए line-by-line चलती है।"},
  {"question":"Python curly braces की जगह क्या उपयोग करता है?","options":["A) Parentheses","B) Square brackets","C) Indentation","D) Semicolons"],"correct":"C) Indentation","explanation":"Python indentation से blocks define करता है।"},
  {"question":"Python पहली बार कब आई?","options":["A) 1985","B) 1991","C) 2000","D) 2008"],"correct":"B) 1991","explanation":"Python 1.0, 1991 में आई।"},
  {"question":"Python किसलिए प्रसिद्ध है?","options":["A) Complex syntax","B) Simple readable syntax","C) Low-level programming","D) Hardware control"],"correct":"B) Simple readable syntax","explanation":"Python की syntax सरल है।"},
  {"question":"Python file चलाने का command?","options":["A) run file.py","B) execute file.py","C) python file.py","D) start file.py"],"correct":"C) python file.py","explanation":"python filename.py से Python script चलती है।"},
  {"question":"Python का नाम कहाँ से आया?","options":["A) साँप से","B) Monty Python comedy show से","C) वैज्ञानिक से","D) पहाड़ से"],"correct":"B) Monty Python comedy show से","explanation":"Monty Python's Flying Circus से नाम आया।"},
  {"question":"Python का उपयोग नहीं होता?","options":["A) Web development","B) Data science","C) OS kernel","D) Automation"],"correct":"C) OS kernel","explanation":"OS kernel के लिए C/C++ उपयोग होता है।"},
  {"question":"print() function क्या करता है?","options":["A) Values store करता है","B) Output दिखाता है","C) Input लेता है","D) Variables बनाता है"],"correct":"B) Output दिखाता है","explanation":"print() screen पर output दिखाता है।"},
  {"question":"Python files किस extension का उपयोग करती हैं?","options":["A) .java","B) .txt","C) .py","D) .python"],"correct":"C) .py","explanation":"Python files .py से समाप्त होती हैं।"},
  {"question":"Python किस प्रकार की typing उपयोग करता है?","options":["A) Static","B) Dynamic","C) Manual","D) Strict"],"correct":"B) Dynamic","explanation":"Python runtime पर types पहचानता है।"},
  {"question":"वर्तमान Python version?","options":["A) Python 1","B) Python 2","C) Python 3","D) Python 4"],"correct":"C) Python 3","explanation":"Python 3 वर्तमान standard है।"},
],
'malayalam': [
  {"question":"Python ആരാണ് ഉണ്ടാക്കിയത്?","options":["A) James Gosling","B) Guido van Rossum","C) Dennis Ritchie","D) Bjarne Stroustrup"],"correct":"B) Guido van Rossum","explanation":"Python 1991-ൽ Guido van Rossum ഉണ്ടാക്കി."},
  {"question":"Python ഏത് തരം ഭാഷ?","options":["A) Compiled","B) Interpreted","C) Assembly","D) Machine"],"correct":"B) Interpreted","explanation":"Python interpreter വഴി line-by-line run ആകുന്നു."},
  {"question":"Python curly braces-നു പകരം?","options":["A) Parentheses","B) Square brackets","C) Indentation","D) Semicolons"],"correct":"C) Indentation","explanation":"Python indentation ഉപയോഗിച്ച് blocks define ചെയ്യുന്നു."},
  {"question":"Python ആദ്യം ഏത് വർഷം?","options":["A) 1985","B) 1991","C) 2000","D) 2008"],"correct":"B) 1991","explanation":"Python 1.0, 1991-ൽ release ആയി."},
  {"question":"Python എന്തിന് പ്രശസ്തം?","options":["A) Complex syntax","B) Simple readable syntax","C) Low-level programming","D) Hardware control"],"correct":"B) Simple readable syntax","explanation":"Python simple syntax-ന് പ്രശസ്തം."},
  {"question":"Python file run ചെയ്യാൻ ഏത് command?","options":["A) run file.py","B) execute file.py","C) python file.py","D) start file.py"],"correct":"C) python file.py","explanation":"python filename.py script run ചെയ്യുന്നു."},
  {"question":"Python-ന്റെ പേര് എവിടെ നിന്ന്?","options":["A) പാമ്പ്","B) Monty Python comedy show","C) ശാസ്ത്രജ്ഞൻ","D) മല"],"correct":"B) Monty Python comedy show","explanation":"Monty Python's Flying Circus-ൽ നിന്ന്."},
  {"question":"Python ഉപയോഗിക്കാത്ത ഇടം?","options":["A) Web development","B) Data science","C) OS kernel","D) Automation"],"correct":"C) OS kernel","explanation":"OS kernel-ന് C/C++ ഉപയോഗിക്കുന്നു."},
  {"question":"print() function എന്ത് ചെയ്യുന്നു?","options":["A) Values store ചെയ്യുന്നു","B) Output കാണിക്കുന്നു","C) Input എടുക്കുന്നു","D) Variables define ചെയ്യുന്നു"],"correct":"B) Output കാണിക്കുന്നു","explanation":"print() screen-ൽ output കാണിക്കുന്നു."},
  {"question":"Python files ഏത് extension?","options":["A) .java","B) .txt","C) .py","D) .python"],"correct":"C) .py","explanation":"Python files .py-ൽ അവസാനിക്കുന്നു."},
  {"question":"Python ഏത് typing ഉപയോഗിക്കുന്നു?","options":["A) Static","B) Dynamic","C) Manual","D) Strict"],"correct":"B) Dynamic","explanation":"Python runtime-ൽ types തിരിച്ചറിയുന്നു."},
  {"question":"ഇന്നത്തെ Python version?","options":["A) Python 1","B) Python 2","C) Python 3","D) Python 4"],"correct":"C) Python 3","explanation":"Python 3 ഇന്നത്തെ standard ആണ്."},
],
},  # end Introduction to Python

'Variables and Data Types': {
'english': [
  {"question":"Which stores whole numbers?","options":["A) float","B) int","C) str","D) bool"],"correct":"B) int","explanation":"int stores whole numbers."},
  {"question":"Type of 3.14?","options":["A) int","B) str","C) float","D) bool"],"correct":"C) float","explanation":"3.14 is a float."},
  {"question":"How to check variable type?","options":["A) typeof()","B) gettype()","C) type()","D) datatype()"],"correct":"C) type()","explanation":"type(x) returns the data type."},
  {"question":"x = 'Hello' — what type?","options":["A) int","B) float","C) bool","D) str"],"correct":"D) str","explanation":"Text in quotes is str."},
  {"question":"bool stores?","options":["A) Numbers","B) Text","C) True/False","D) Lists"],"correct":"C) True/False","explanation":"bool holds True or False."},
  {"question":"x = 10 — type of x?","options":["A) str","B) float","C) int","D) bool"],"correct":"C) int","explanation":"10 is an integer."},
  {"question":"Which is a string?","options":["A) 42","B) True","C) 'hello'","D) 3.14"],"correct":"C) 'hello'","explanation":"Text in quotes is string."},
  {"question":"bool(1) equals?","options":["A) False","B) True","C) 1","D) None"],"correct":"B) True","explanation":"Non-zero is True in Python."},
  {"question":"Convert '5' to integer?","options":["A) integer('5')","B) int('5')","C) num('5')","D) toInt('5')"],"correct":"B) int('5')","explanation":"int() converts string to integer."},
  {"question":"type(True) returns?","options":["A) int","B) str","C) bool","D) float"],"correct":"C) bool","explanation":"True and False are bool type."},
  {"question":"Data type for decimals?","options":["A) int","B) str","C) bool","D) float"],"correct":"D) float","explanation":"float stores decimal numbers."},
  {"question":"x = None means?","options":["A) 0","B) Empty string","C) No value","D) False"],"correct":"C) No value","explanation":"None represents absence of value."},
],
'tamil': [
  {"question":"முழு எண்களை எது சேமிக்கும்?","options":["A) float","B) int","C) str","D) bool"],"correct":"B) int","explanation":"int முழு எண்களை சேமிக்கும்."},
  {"question":"3.14-இன் type என்ன?","options":["A) int","B) str","C) float","D) bool"],"correct":"C) float","explanation":"3.14 float ஆகும்."},
  {"question":"Variable type பார்க்க?","options":["A) typeof()","B) gettype()","C) type()","D) datatype()"],"correct":"C) type()","explanation":"type(x) data type return செய்யும்."},
  {"question":"x = 'Hello' எந்த type?","options":["A) int","B) float","C) bool","D) str"],"correct":"D) str","explanation":"Quotes-ல் உள்ளது str."},
  {"question":"bool என்ன சேமிக்கும்?","options":["A) எண்கள்","B) Text","C) True/False","D) Lists"],"correct":"C) True/False","explanation":"bool True அல்லது False சேமிக்கும்."},
  {"question":"x = 10 — x-இன் type?","options":["A) str","B) float","C) int","D) bool"],"correct":"C) int","explanation":"10 integer."},
  {"question":"String எது?","options":["A) 42","B) True","C) 'hello'","D) 3.14"],"correct":"C) 'hello'","explanation":"Quotes-ல் உள்ளது string."},
  {"question":"bool(1) என்ன?","options":["A) False","B) True","C) 1","D) None"],"correct":"B) True","explanation":"Non-zero Python-ல் True."},
  {"question":"'5'-ஐ integer-ஆக மாற்ற?","options":["A) integer('5')","B) int('5')","C) num('5')","D) toInt('5')"],"correct":"B) int('5')","explanation":"int() string-ஐ integer-ஆக மாற்றும்."},
  {"question":"type(True) என்ன return செய்யும்?","options":["A) int","B) str","C) bool","D) float"],"correct":"C) bool","explanation":"True மற்றும் False bool type."},
  {"question":"தசம எண்களுக்கு எந்த data type?","options":["A) int","B) str","C) bool","D) float"],"correct":"D) float","explanation":"float தசம எண்களை சேமிக்கும்."},
  {"question":"x = None என்றால் என்ன?","options":["A) 0","B) Empty string","C) மதிப்பு இல்லை","D) False"],"correct":"C) மதிப்பு இல்லை","explanation":"None என்பது மதிப்பு இல்லாமை."},
],
'tanglish': [
  {"question":"Whole numbers store panna ethu?","options":["A) float","B) int","C) str","D) bool"],"correct":"B) int","explanation":"int whole numbers store pannum."},
  {"question":"3.14-oda type enna?","options":["A) int","B) str","C) float","D) bool"],"correct":"C) float","explanation":"3.14 float aagum."},
  {"question":"Variable type paakka ethu?","options":["A) typeof()","B) gettype()","C) type()","D) datatype()"],"correct":"C) type()","explanation":"type(x) data type return pannum."},
  {"question":"x = 'Hello' ethu type?","options":["A) int","B) float","C) bool","D) str"],"correct":"D) str","explanation":"Quotes-la irukkathu str."},
  {"question":"bool enna store pannum?","options":["A) Numbers","B) Text","C) True/False","D) Lists"],"correct":"C) True/False","explanation":"bool True or False store pannum."},
  {"question":"x = 10 — x-oda type?","options":["A) str","B) float","C) int","D) bool"],"correct":"C) int","explanation":"10 integer."},
  {"question":"String ethu?","options":["A) 42","B) True","C) 'hello'","D) 3.14"],"correct":"C) 'hello'","explanation":"Quotes-la irukkathu string."},
  {"question":"bool(1) enna?","options":["A) False","B) True","C) 1","D) None"],"correct":"B) True","explanation":"Non-zero Python-la True."},
  {"question":"'5'-a integer-a maarra?","options":["A) integer('5')","B) int('5')","C) num('5')","D) toInt('5')"],"correct":"B) int('5')","explanation":"int() string-a integer-a maarum."},
  {"question":"type(True) enna return pannum?","options":["A) int","B) str","C) bool","D) float"],"correct":"C) bool","explanation":"True-um False-um bool type."},
  {"question":"Decimal numbers-ku ethu data type?","options":["A) int","B) str","C) bool","D) float"],"correct":"D) float","explanation":"float decimal numbers store pannum."},
  {"question":"x = None enna?","options":["A) 0","B) Empty string","C) Madipu illai","D) False"],"correct":"C) Madipu illai","explanation":"None enbathu madipu illamai."},
],
'hindi': [
  {"question":"पूरे numbers कौन store करता है?","options":["A) float","B) int","C) str","D) bool"],"correct":"B) int","explanation":"int पूरे numbers store करता है।"},
  {"question":"3.14 का type?","options":["A) int","B) str","C) float","D) bool"],"correct":"C) float","explanation":"3.14 float है।"},
  {"question":"Variable का type देखने के लिए?","options":["A) typeof()","B) gettype()","C) type()","D) datatype()"],"correct":"C) type()","explanation":"type(x) data type return करता है।"},
  {"question":"x = 'Hello' किस type की है?","options":["A) int","B) float","C) bool","D) str"],"correct":"D) str","explanation":"Quotes में text str होता है।"},
  {"question":"bool क्या store करता है?","options":["A) Numbers","B) Text","C) True/False","D) Lists"],"correct":"C) True/False","explanation":"bool True या False रखता है।"},
  {"question":"x = 10 — type?","options":["A) str","B) float","C) int","D) bool"],"correct":"C) int","explanation":"10 integer है।"},
  {"question":"String कौन सा है?","options":["A) 42","B) True","C) 'hello'","D) 3.14"],"correct":"C) 'hello'","explanation":"Quotes में text string है।"},
  {"question":"bool(1) क्या है?","options":["A) False","B) True","C) 1","D) None"],"correct":"B) True","explanation":"Non-zero Python में True है।"},
  {"question":"'5' को integer में कैसे बदलें?","options":["A) integer('5')","B) int('5')","C) num('5')","D) toInt('5')"],"correct":"B) int('5')","explanation":"int() string को integer में बदलता है।"},
  {"question":"type(True) क्या?","options":["A) int","B) str","C) bool","D) float"],"correct":"C) bool","explanation":"True और False bool type हैं।"},
  {"question":"दशमलव numbers के लिए data type?","options":["A) int","B) str","C) bool","D) float"],"correct":"D) float","explanation":"float दशमलव numbers store करता है।"},
  {"question":"x = None का मतलब?","options":["A) 0","B) खाली string","C) कोई मान नहीं","D) False"],"correct":"C) कोई मान नहीं","explanation":"None का मतलब मान नहीं है।"},
],
'malayalam': [
  {"question":"Whole numbers store ചെയ്യുന്നത്?","options":["A) float","B) int","C) str","D) bool"],"correct":"B) int","explanation":"int whole numbers store ചെയ്യുന്നു."},
  {"question":"3.14-ന്റെ type?","options":["A) int","B) str","C) float","D) bool"],"correct":"C) float","explanation":"3.14 float ആണ്."},
  {"question":"Variable type കാണാൻ?","options":["A) typeof()","B) gettype()","C) type()","D) datatype()"],"correct":"C) type()","explanation":"type(x) data type return ചെയ്യുന്നു."},
  {"question":"x = 'Hello' ഏത് type?","options":["A) int","B) float","C) bool","D) str"],"correct":"D) str","explanation":"Quotes-ലെ text str ആണ്."},
  {"question":"bool എന്ത് store ചെയ്യുന്നു?","options":["A) Numbers","B) Text","C) True/False","D) Lists"],"correct":"C) True/False","explanation":"bool True അല്ലെങ്കിൽ False."},
  {"question":"x = 10 — type?","options":["A) str","B) float","C) int","D) bool"],"correct":"C) int","explanation":"10 integer ആണ്."},
  {"question":"String ഏത്?","options":["A) 42","B) True","C) 'hello'","D) 3.14"],"correct":"C) 'hello'","explanation":"Quotes-ലെ text string ആണ്."},
  {"question":"bool(1) എന്ത്?","options":["A) False","B) True","C) 1","D) None"],"correct":"B) True","explanation":"Non-zero Python-ൽ True ആണ്."},
  {"question":"'5' integer ആക്കാൻ?","options":["A) integer('5')","B) int('5')","C) num('5')","D) toInt('5')"],"correct":"B) int('5')","explanation":"int() string-നെ integer ആക്കുന്നു."},
  {"question":"type(True) എന്ത്?","options":["A) int","B) str","C) bool","D) float"],"correct":"C) bool","explanation":"True-ഉം False-ഉം bool type ആണ്."},
  {"question":"Decimal numbers-ന് data type?","options":["A) int","B) str","C) bool","D) float"],"correct":"D) float","explanation":"float decimal numbers store ചെയ്യുന്നു."},
  {"question":"x = None എന്നാൽ?","options":["A) 0","B) Empty string","C) മൂല്യം ഇല്ല","D) False"],"correct":"C) മൂല്യം ഇല്ല","explanation":"None എന്നാൽ മൂല്യം ഇല്ലെന്നാണ്."},
],
},  # end Variables and Data Types

'Operators': {

'english': [
{"question":"Which operator is used for addition in Python?","options":["A) +","B) -","C) *","D) /"],"correct":"A) +","explanation":"+ operator is used to add two values."},
{"question":"What does the '-' operator do?","options":["A) Multiply","B) Subtract","C) Divide","D) Modulus"],"correct":"B) Subtract","explanation":"- operator subtracts one value from another."},
{"question":"Which operator is used for multiplication?","options":["A) x","B) *","C) %","D) #"],"correct":"B) *","explanation":"* operator multiplies two numbers."},
{"question":"What is the result of 10 % 3?","options":["A) 3","B) 1","C) 0","D) 10"],"correct":"B) 1","explanation":"% gives remainder, 10 divided by 3 leaves 1."},
{"question":"Which operator is used for exponentiation?","options":["A) ^","B) **","C) //","D) %%"],"correct":"B) **","explanation":"** raises power (e.g., 2**3 = 8)."},
{"question":"What does '//' operator do?","options":["A) Float division","B) Floor division","C) Multiplication","D) Modulus"],"correct":"B) Floor division","explanation":"// returns integer quotient."},
{"question":"Which operator compares equality?","options":["A) =","B) ==","C) !=","D) >"],"correct":"B) ==","explanation":"== checks if two values are equal."},
{"question":"What does '!=' mean?","options":["A) Equal","B) Not equal","C) Greater","D) Assign"],"correct":"B) Not equal","explanation":"!= checks inequality."},
{"question":"Which operator is logical AND?","options":["A) &","B) and","C) &&","D) AND"],"correct":"B) and","explanation":"and returns True if both conditions are True."},
{"question":"Which operator is logical OR?","options":["A) or","B) ||","C) OR","D) |"],"correct":"A) or","explanation":"or returns True if one condition is True."},
{"question":"Which operator assigns value?","options":["A) ==","B) =","C) :=","D) !="],"correct":"B) =","explanation":"= is assignment operator."},
{"question":"What is output of 5 > 3?","options":["A) True","B) False","C) 5","D) 3"],"correct":"A) True","explanation":"5 is greater than 3."},
],

'tamil': [
{"question":"Python-ல் addition செய்ய எந்த operator?","options":["A) +","B) -","C) *","D) /"],"correct":"A) +","explanation":"+ இரண்டு values-ஐ சேர்க்கும்."},
{"question":"'-' operator என்ன செய்கிறது?","options":["A) Multiply","B) Subtract","C) Divide","D) Modulus"],"correct":"B) Subtract","explanation":"- ஒன்று value-ல் இருந்து மற்றொன்றை கழிக்கும்."},
{"question":"Multiplication operator எது?","options":["A) x","B) *","C) %","D) #"],"correct":"B) *","explanation":"* multiplication செய்யும்."},
{"question":"10 % 3 result என்ன?","options":["A) 3","B) 1","C) 0","D) 10"],"correct":"B) 1","explanation":"% remainder return செய்யும்."},
{"question":"Power operator எது?","options":["A) ^","B) **","C) //","D) %%"],"correct":"B) **","explanation":"** power (எ.கா 2**3 = 8)."},
{"question":"'//' என்ன செய்கிறது?","options":["A) Float division","B) Floor division","C) Multiply","D) Modulus"],"correct":"B) Floor division","explanation":"// integer result தரும்."},
{"question":"Equality check operator எது?","options":["A) =","B) ==","C) !=","D) >"],"correct":"B) ==","explanation":"== equal check செய்யும்."},
{"question":"'!=' என்ன அர்த்தம்?","options":["A) Equal","B) Not equal","C) Greater","D) Assign"],"correct":"B) Not equal","explanation":"!= unequal check."},
{"question":"Logical AND operator எது?","options":["A) &","B) and","C) &&","D) AND"],"correct":"B) and","explanation":"இரண்டும் true ஆனால் true."},
{"question":"Logical OR operator எது?","options":["A) or","B) ||","C) OR","D) |"],"correct":"A) or","explanation":"ஒரு condition true இருந்தால் true."},
{"question":"Assignment operator எது?","options":["A) ==","B) =","C) :=","D) !="],"correct":"B) =","explanation":"value assign செய்யும்."},
{"question":"5 > 3 output என்ன?","options":["A) True","B) False","C) 5","D) 3"],"correct":"A) True","explanation":"5, 3-ஐ விட பெரியது."},
],

'tanglish': [
{"question":"Addition ku use pannra operator ethu?","options":["A) +","B) -","C) *","D) /"],"correct":"A) +","explanation":"+ rendu values add pannum."},
{"question":"'-' enna pannum?","options":["A) Multiply","B) Subtract","C) Divide","D) Modulus"],"correct":"B) Subtract","explanation":"- values subtract pannum."},
{"question":"Multiplication operator ethu?","options":["A) x","B) *","C) %","D) #"],"correct":"B) *","explanation":"* multiply pannum."},
{"question":"10 % 3 result enna?","options":["A) 3","B) 1","C) 0","D) 10"],"correct":"B) 1","explanation":"% remainder kudukkum."},
{"question":"Power operator ethu?","options":["A) ^","B) **","C) //","D) %%"],"correct":"B) **","explanation":"** power calculate pannum."},
{"question":"'//' enna pannum?","options":["A) Float division","B) Floor division","C) Multiply","D) Modulus"],"correct":"B) Floor division","explanation":"integer result kudukkum."},
{"question":"Equal check operator ethu?","options":["A) =","B) ==","C) !=","D) >"],"correct":"B) ==","explanation":"== equal check pannum."},
{"question":"'!=' meaning enna?","options":["A) Equal","B) Not equal","C) Greater","D) Assign"],"correct":"B) Not equal","explanation":"equal illa nu check pannum."},
{"question":"Logical AND ethu?","options":["A) &","B) and","C) &&","D) AND"],"correct":"B) and","explanation":"rendu true na true."},
{"question":"Logical OR ethu?","options":["A) or","B) ||","C) OR","D) |"],"correct":"A) or","explanation":"oru true irundha podhum."},
{"question":"Assignment operator ethu?","options":["A) ==","B) =","C) :=","D) !="],"correct":"B) =","explanation":"value assign pannum."},
{"question":"5 > 3 output enna?","options":["A) True","B) False","C) 5","D) 3"],"correct":"A) True","explanation":"5 perusa irukku 3 vida."},
],

'hindi': [
{"question":"Python में addition के लिए कौन सा operator है?","options":["A) +","B) -","C) *","D) /"],"correct":"A) +","explanation":"+ जोड़ने के लिए उपयोग होता है।"},
{"question":"'-' operator क्या करता है?","options":["A) Multiply","B) Subtract","C) Divide","D) Modulus"],"correct":"B) Subtract","explanation":"- घटाने के लिए उपयोग होता है।"},
{"question":"Multiplication operator कौन सा है?","options":["A) x","B) *","C) %","D) #"],"correct":"B) *","explanation":"* गुणा करता है।"},
{"question":"10 % 3 का परिणाम क्या है?","options":["A) 3","B) 1","C) 0","D) 10"],"correct":"B) 1","explanation":"% remainder देता है।"},
{"question":"Power operator कौन सा है?","options":["A) ^","B) **","C) //","D) %%"],"correct":"B) **","explanation":"** power के लिए।"},
{"question":"'//' क्या करता है?","options":["A) Float division","B) Floor division","C) Multiply","D) Modulus"],"correct":"B) Floor division","explanation":"integer division देता है।"},
{"question":"Equality operator कौन सा है?","options":["A) =","B) ==","C) !=","D) >"],"correct":"B) ==","explanation":"== बराबरी check करता है।"},
{"question":"'!=' का मतलब?","options":["A) Equal","B) Not equal","C) Greater","D) Assign"],"correct":"B) Not equal","explanation":"बराबर नहीं।"},
{"question":"Logical AND operator?","options":["A) &","B) and","C) &&","D) AND"],"correct":"B) and","explanation":"दोनों true होने पर true।"},
{"question":"Logical OR operator?","options":["A) or","B) ||","C) OR","D) |"],"correct":"A) or","explanation":"एक true हो तो true।"},
{"question":"Assignment operator?","options":["A) ==","B) =","C) :=","D) !="],"correct":"B) =","explanation":"value assign करता है।"},
{"question":"5 > 3 का output?","options":["A) True","B) False","C) 5","D) 3"],"correct":"A) True","explanation":"5, 3 से बड़ा है।"},
],

'malayalam': [
{"question":"Addition operator ഏത്?","options":["A) +","B) -","C) *","D) /"],"correct":"A) +","explanation":"+ value add ചെയ്യുന്നു."},
{"question":"'-' എന്ത് ചെയ്യുന്നു?","options":["A) Multiply","B) Subtract","C) Divide","D) Modulus"],"correct":"B) Subtract","explanation":"- കുറയ്ക്കുന്നു."},
{"question":"Multiplication operator ഏത്?","options":["A) x","B) *","C) %","D) #"],"correct":"B) *","explanation":"* multiply ചെയ്യുന്നു."},
{"question":"10 % 3 result എന്ത്?","options":["A) 3","B) 1","C) 0","D) 10"],"correct":"B) 1","explanation":"% remainder തരുന്നു."},
{"question":"Power operator ഏത്?","options":["A) ^","B) **","C) //","D) %%"],"correct":"B) **","explanation":"** power calculate ചെയ്യുന്നു."},
{"question":"'//' എന്ത് ചെയ്യുന്നു?","options":["A) Float division","B) Floor division","C) Multiply","D) Modulus"],"correct":"B) Floor division","explanation":"integer result തരുന്നു."},
{"question":"Equality operator ഏത്?","options":["A) =","B) ==","C) !=","D) >"],"correct":"B) ==","explanation":"== equal check ചെയ്യുന്നു."},
{"question":"'!=' എന്താണ്?","options":["A) Equal","B) Not equal","C) Greater","D) Assign"],"correct":"B) Not equal","explanation":"equal അല്ല."},
{"question":"Logical AND ഏത്?","options":["A) &","B) and","C) &&","D) AND"],"correct":"B) and","explanation":"രണ്ടും true ആണെങ്കിൽ true."},
{"question":"Logical OR ഏത്?","options":["A) or","B) ||","C) OR","D) |"],"correct":"A) or","explanation":"ഒന്ന് true ആണെങ്കിൽ മതി."},
{"question":"Assignment operator ഏത്?","options":["A) ==","B) =","C) :=","D) !="],"correct":"B) =","explanation":"value assign ചെയ്യുന്നു."},
{"question":"5 > 3 output എന്ത്?","options":["A) True","B) False","C) 5","D) 3"],"correct":"A) True","explanation":"5, 3-നേക്കാൾ വലുതാണ്."},
],

},

'Control Flow (if/else)': {

'english': [
{"question":"Which statement is used for decision making in Python?","options":["A) loop","B) if","C) function","D) class"],"correct":"B) if","explanation":"if statement is used to make decisions."},
{"question":"Which keyword is used for alternative condition?","options":["A) else","B) elif","C) both A and B","D) none"],"correct":"C) both A and B","explanation":"else and elif are used for alternative conditions."},
{"question":"What does 'elif' stand for?","options":["A) else if","B) end if","C) extra if","D) equal if"],"correct":"A) else if","explanation":"elif means else if."},
{"question":"Which loop runs until condition is false?","options":["A) for","B) while","C) do-while","D) loop"],"correct":"B) while","explanation":"while loop runs until condition becomes false."},
{"question":"Which loop is used to iterate over sequence?","options":["A) while","B) do-while","C) for","D) loop"],"correct":"C) for","explanation":"for loop iterates over sequences."},
{"question":"What does 'break' do?","options":["A) skips iteration","B) exits loop","C) repeats loop","D) stops program"],"correct":"B) exits loop","explanation":"break exits the loop immediately."},
{"question":"What does 'continue' do?","options":["A) exits loop","B) skips current iteration","C) stops program","D) repeats loop"],"correct":"B) skips current iteration","explanation":"continue skips current iteration."},
{"question":"What is output of if True: print('Hi')?","options":["A) Hi","B) Error","C) Nothing","D) False"],"correct":"A) Hi","explanation":"Condition is True so it prints Hi."},
{"question":"Which keyword is used to do nothing?","options":["A) pass","B) skip","C) null","D) break"],"correct":"A) pass","explanation":"pass does nothing."},
{"question":"Which loop is infinite?","options":["A) while True","B) for i in range(5)","C) if True","D) None"],"correct":"A) while True","explanation":"while True creates infinite loop."},
{"question":"Which statement checks multiple conditions?","options":["A) if-elif-else","B) for","C) while","D) pass"],"correct":"A) if-elif-else","explanation":"Used for multiple conditions."},
{"question":"What is indentation used for?","options":["A) Decoration","B) Block structure","C) Comments","D) Variables"],"correct":"B) Block structure","explanation":"Indentation defines code blocks."},
],

'tamil': [
{"question":"Decision making-க்கு எந்த statement?","options":["A) loop","B) if","C) function","D) class"],"correct":"B) if","explanation":"if decision எடுக்க பயன்படும்."},
{"question":"Alternative condition-க்கு எந்த keyword?","options":["A) else","B) elif","C) இரண்டும்","D) இல்லை"],"correct":"C) இரண்டும்","explanation":"else மற்றும் elif பயன்படுத்தப்படும்."},
{"question":"'elif' என்ன?","options":["A) else if","B) end if","C) extra if","D) equal if"],"correct":"A) else if","explanation":"elif என்பது else if."},
{"question":"Condition false ஆகும் வரை எந்த loop?","options":["A) for","B) while","C) do-while","D) loop"],"correct":"B) while","explanation":"while condition false ஆகும் வரை ஓடும்."},
{"question":"Sequence iterate செய்ய எந்த loop?","options":["A) while","B) do-while","C) for","D) loop"],"correct":"C) for","explanation":"for sequence-ல் iterate செய்யும்."},
{"question":"'break' என்ன செய்கிறது?","options":["A) skip","B) loop exit","C) repeat","D) stop"],"correct":"B) loop exit","explanation":"break loop-ஐ நிறுத்தும்."},
{"question":"'continue' என்ன செய்கிறது?","options":["A) exit","B) current skip","C) stop","D) repeat"],"correct":"B) current skip","explanation":"current iteration skip செய்யும்."},
{"question":"if True: print('Hi') output?","options":["A) Hi","B) Error","C) Nothing","D) False"],"correct":"A) Hi","explanation":"True ஆக இருப்பதால் print ஆகும்."},
{"question":"எதையும் செய்யாத keyword?","options":["A) pass","B) skip","C) null","D) break"],"correct":"A) pass","explanation":"pass எதையும் செய்யாது."},
{"question":"Infinite loop எது?","options":["A) while True","B) for 5","C) if True","D) none"],"correct":"A) while True","explanation":"while True முடிவில்லாமல் ஓடும்."},
{"question":"Multiple condition check?","options":["A) if-elif-else","B) for","C) while","D) pass"],"correct":"A) if-elif-else","explanation":"பல condition-களை check செய்யும்."},
{"question":"Indentation பயன்பாடு?","options":["A) அலங்காரம்","B) Block structure","C) Comments","D) Variables"],"correct":"B) Block structure","explanation":"code blocks define செய்யும்."},
],

'tanglish': [
{"question":"Decision making ku use pannra statement ethu?","options":["A) loop","B) if","C) function","D) class"],"correct":"B) if","explanation":"if decision eduka use aagum."},
{"question":"Alternative condition ku keyword ethu?","options":["A) else","B) elif","C) both","D) none"],"correct":"C) both","explanation":"else and elif use pannuvanga."},
{"question":"'elif' na enna?","options":["A) else if","B) end if","C) extra if","D) equal if"],"correct":"A) else if","explanation":"elif = else if."},
{"question":"Condition false varaikum run aagum loop?","options":["A) for","B) while","C) do-while","D) loop"],"correct":"B) while","explanation":"while false varaikum run aagum."},
{"question":"Sequence iterate panna loop ethu?","options":["A) while","B) do-while","C) for","D) loop"],"correct":"C) for","explanation":"for loop sequence iterate pannum."},
{"question":"'break' enna pannum?","options":["A) skip","B) exit loop","C) repeat","D) stop"],"correct":"B) exit loop","explanation":"loop ah stop pannum."},
{"question":"'continue' enna pannum?","options":["A) exit","B) skip iteration","C) stop","D) repeat"],"correct":"B) skip iteration","explanation":"current iteration skip pannum."},
{"question":"if True print('Hi') output enna?","options":["A) Hi","B) Error","C) Nothing","D) False"],"correct":"A) Hi","explanation":"True na print aagum."},
{"question":"Onnum pannaadha keyword ethu?","options":["A) pass","B) skip","C) null","D) break"],"correct":"A) pass","explanation":"pass nothing pannum."},
{"question":"Infinite loop ethu?","options":["A) while True","B) for 5","C) if True","D) none"],"correct":"A) while True","explanation":"end illaama run aagum."},
{"question":"Multiple condition check panna?","options":["A) if-elif-else","B) for","C) while","D) pass"],"correct":"A) if-elif-else","explanation":"multiple condition check pannum."},
{"question":"Indentation use enna?","options":["A) decoration","B) block","C) comments","D) variables"],"correct":"B) block","explanation":"code blocks define pannum."},
],

'hindi': [
{"question":"Decision making के लिए कौन सा statement है?","options":["A) loop","B) if","C) function","D) class"],"correct":"B) if","explanation":"if decision लेने के लिए उपयोग होता है।"},
{"question":"Alternative condition के लिए keyword?","options":["A) else","B) elif","C) दोनों","D) कोई नहीं"],"correct":"C) दोनों","explanation":"else और elif दोनों उपयोग होते हैं।"},
{"question":"'elif' का मतलब?","options":["A) else if","B) end if","C) extra if","D) equal if"],"correct":"A) else if","explanation":"elif = else if."},
{"question":"कौन सा loop condition false होने तक चलता है?","options":["A) for","B) while","C) do-while","D) loop"],"correct":"B) while","explanation":"while false तक चलता है।"},
{"question":"Sequence iterate करने के लिए loop?","options":["A) while","B) do-while","C) for","D) loop"],"correct":"C) for","explanation":"for sequence पर चलता है।"},
{"question":"'break' क्या करता है?","options":["A) skip","B) loop exit","C) repeat","D) stop"],"correct":"B) loop exit","explanation":"loop को रोकता है।"},
{"question":"'continue' क्या करता है?","options":["A) exit","B) skip iteration","C) stop","D) repeat"],"correct":"B) skip iteration","explanation":"current iteration skip करता है।"},
{"question":"if True: print('Hi') output?","options":["A) Hi","B) Error","C) Nothing","D) False"],"correct":"A) Hi","explanation":"True होने पर print होता है।"},
{"question":"कुछ न करने वाला keyword?","options":["A) pass","B) skip","C) null","D) break"],"correct":"A) pass","explanation":"pass कुछ नहीं करता।"},
{"question":"Infinite loop कौन सा है?","options":["A) while True","B) for 5","C) if True","D) none"],"correct":"A) while True","explanation":"endless loop।"},
{"question":"Multiple conditions check?","options":["A) if-elif-else","B) for","C) while","D) pass"],"correct":"A) if-elif-else","explanation":"multiple conditions के लिए।"},
{"question":"Indentation का उपयोग?","options":["A) decoration","B) block","C) comments","D) variables"],"correct":"B) block","explanation":"code blocks define करता है।"},
],

'malayalam': [
{"question":"Decision making-ന് ഏത് statement?","options":["A) loop","B) if","C) function","D) class"],"correct":"B) if","explanation":"if decision എടുക്കാൻ ഉപയോഗിക്കുന്നു."},
{"question":"Alternative condition keyword?","options":["A) else","B) elif","C) രണ്ടും","D) ഒന്നുമില്ല"],"correct":"C) രണ്ടും","explanation":"else, elif ഉപയോഗിക്കുന്നു."},
{"question":"'elif' എന്താണ്?","options":["A) else if","B) end if","C) extra if","D) equal if"],"correct":"A) else if","explanation":"elif = else if."},
{"question":"Condition false ആകുന്നതുവരെ ഏത് loop?","options":["A) for","B) while","C) do-while","D) loop"],"correct":"B) while","explanation":"while false വരെ run ചെയ്യും."},
{"question":"Sequence iterate ചെയ്യാൻ loop?","options":["A) while","B) do-while","C) for","D) loop"],"correct":"C) for","explanation":"for sequence iterate ചെയ്യുന്നു."},
{"question":"'break' എന്ത് ചെയ്യുന്നു?","options":["A) skip","B) exit loop","C) repeat","D) stop"],"correct":"B) exit loop","explanation":"loop നിർത്തുന്നു."},
{"question":"'continue' എന്ത് ചെയ്യുന്നു?","options":["A) exit","B) skip iteration","C) stop","D) repeat"],"correct":"B) skip iteration","explanation":"current iteration skip ചെയ്യും."},
{"question":"if True print('Hi') output?","options":["A) Hi","B) Error","C) Nothing","D) False"],"correct":"A) Hi","explanation":"True ആയതിനാൽ print ചെയ്യും."},
{"question":"ഒന്നും ചെയ്യാത്ത keyword?","options":["A) pass","B) skip","C) null","D) break"],"correct":"A) pass","explanation":"pass ഒന്നും ചെയ്യില്ല."},
{"question":"Infinite loop ഏത്?","options":["A) while True","B) for 5","C) if True","D) none"],"correct":"A) while True","explanation":"end ഇല്ലാതെ run ചെയ്യും."},
{"question":"Multiple conditions check?","options":["A) if-elif-else","B) for","C) while","D) pass"],"correct":"A) if-elif-else","explanation":"multiple conditions check ചെയ്യുന്നു."},
{"question":"Indentation എന്തിന്?","options":["A) decoration","B) block","C) comments","D) variables"],"correct":"B) block","explanation":"code blocks define ചെയ്യുന്നു."},
],

},#control flow  over

'Loops (for/while)': {

'english': [
{"question":"Which loop is used to iterate over a sequence?","options":["A) while","B) for","C) do-while","D) loop"],"correct":"B) for","explanation":"for loop is used to iterate over sequences like list, tuple."},
{"question":"Which loop runs based on a condition?","options":["A) for","B) while","C) foreach","D) loop"],"correct":"B) while","explanation":"while loop runs as long as condition is True."},
{"question":"What is the output of for i in range(3): print(i)?","options":["A) 1 2 3","B) 0 1 2","C) 0 1 2 3","D) Error"],"correct":"B) 0 1 2","explanation":"range(3) generates 0,1,2."},
{"question":"What does range(5) generate?","options":["A) 1 to 5","B) 0 to 5","C) 0 to 4","D) 1 to 4"],"correct":"C) 0 to 4","explanation":"range(5) starts from 0 and ends at 4."},
{"question":"Which keyword stops the loop completely?","options":["A) continue","B) pass","C) break","D) stop"],"correct":"C) break","explanation":"break exits the loop."},
{"question":"Which keyword skips current iteration?","options":["A) break","B) continue","C) pass","D) skip"],"correct":"B) continue","explanation":"continue skips current iteration."},
{"question":"Which loop is best when number of iterations is known?","options":["A) while","B) for","C) infinite","D) nested"],"correct":"B) for","explanation":"for loop is used when iterations are known."},
{"question":"What is an infinite loop?","options":["A) Loop with end","B) Loop that never ends","C) Loop with error","D) Loop with break"],"correct":"B) Loop that never ends","explanation":"Infinite loop runs forever."},
{"question":"Which loop can be infinite?","options":["A) for","B) while","C) both","D) none"],"correct":"C) both","explanation":"Both can be infinite if condition never ends."},
{"question":"What does pass do in loop?","options":["A) Stops loop","B) Skips iteration","C) Does nothing","D) Ends program"],"correct":"C) Does nothing","explanation":"pass is placeholder and does nothing."},
{"question":"What is output of for i in range(1,4): print(i)?","options":["A) 1 2 3","B) 0 1 2","C) 1 2 3 4","D) Error"],"correct":"A) 1 2 3","explanation":"range(1,4) gives 1,2,3."},
{"question":"Nested loop means?","options":["A) Loop inside loop","B) Loop outside","C) Single loop","D) No loop"],"correct":"A) Loop inside loop","explanation":"Nested loop is loop inside another loop."},
],

'tamil': [
{"question":"Sequence iterate செய்ய எந்த loop?","options":["A) while","B) for","C) do-while","D) loop"],"correct":"B) for","explanation":"for loop list போன்றவற்றை iterate செய்யும்."},
{"question":"Condition அடிப்படையில் ஓடும் loop?","options":["A) for","B) while","C) foreach","D) loop"],"correct":"B) while","explanation":"while condition True இருக்கும் வரை ஓடும்."},
{"question":"for i in range(3): print(i) output?","options":["A) 1 2 3","B) 0 1 2","C) 0 1 2 3","D) Error"],"correct":"B) 0 1 2","explanation":"range(3) 0,1,2 தரும்."},
{"question":"range(5) என்ன தரும்?","options":["A) 1 to 5","B) 0 to 5","C) 0 to 4","D) 1 to 4"],"correct":"C) 0 to 4","explanation":"0 முதல் 4 வரை தரும்."},
{"question":"Loop-ஐ முழுவதும் நிறுத்துவது?","options":["A) continue","B) pass","C) break","D) stop"],"correct":"C) break","explanation":"break loop-ஐ நிறுத்தும்."},
{"question":"Current iteration skip செய்ய?","options":["A) break","B) continue","C) pass","D) skip"],"correct":"B) continue","explanation":"continue iteration skip செய்யும்."},
{"question":"Iterations தெரிந்தால் எந்த loop?","options":["A) while","B) for","C) infinite","D) nested"],"correct":"B) for","explanation":"for loop iterations தெரிந்தால் பயன்படுத்தப்படும்."},
{"question":"Infinite loop என்றால்?","options":["A) முடிவுள்ள loop","B) முடிவில்லா loop","C) error loop","D) break loop"],"correct":"B) முடிவில்லா loop","explanation":"முடிவில்லாமல் ஓடும்."},
{"question":"Infinite loop ஆகும் loop?","options":["A) for","B) while","C) இரண்டும்","D) இல்லை"],"correct":"C) இரண்டும்","explanation":"இரண்டும் infinite ஆகலாம்."},
{"question":"pass என்ன செய்கிறது?","options":["A) stop","B) skip","C) எதுவும் செய்யாது","D) end"],"correct":"C) எதுவும் செய்யாது","explanation":"pass placeholder."},
{"question":"range(1,4) output?","options":["A) 1 2 3","B) 0 1 2","C) 1 2 3 4","D) error"],"correct":"A) 1 2 3","explanation":"1 முதல் 3 வரை."},
{"question":"Nested loop என்றால்?","options":["A) loop உள்ள loop","B) வெளியே loop","C) single","D) இல்லை"],"correct":"A) loop உள்ள loop","explanation":"ஒரு loop உள்ளே இன்னொரு loop."},
],

'tanglish': [
{"question":"Sequence iterate panna loop ethu?","options":["A) while","B) for","C) do-while","D) loop"],"correct":"B) for","explanation":"for loop sequence iterate pannum."},
{"question":"Condition base la run aagum loop?","options":["A) for","B) while","C) foreach","D) loop"],"correct":"B) while","explanation":"while condition true varaikum run aagum."},
{"question":"for i in range(3) print(i) output enna?","options":["A) 1 2 3","B) 0 1 2","C) 0 1 2 3","D) Error"],"correct":"B) 0 1 2","explanation":"range(3) 0,1,2 kudukkum."},
{"question":"range(5) enna generate pannum?","options":["A) 1 to 5","B) 0 to 5","C) 0 to 4","D) 1 to 4"],"correct":"C) 0 to 4","explanation":"0 la start aagi 4 varaikum."},
{"question":"Loop full ah stop panna keyword ethu?","options":["A) continue","B) pass","C) break","D) stop"],"correct":"C) break","explanation":"break loop ah mudichudum."},
{"question":"Current iteration skip panna?","options":["A) break","B) continue","C) pass","D) skip"],"correct":"B) continue","explanation":"continue skip pannum."},
{"question":"Iterations known na ethu use pannuvom?","options":["A) while","B) for","C) infinite","D) nested"],"correct":"B) for","explanation":"for loop use pannuvom."},
{"question":"Infinite loop na enna?","options":["A) end irukku","B) end illa","C) error","D) break"],"correct":"B) end illa","explanation":"mudiyama run aagum."},
{"question":"Infinite loop aagum loop ethu?","options":["A) for","B) while","C) both","D) none"],"correct":"C) both","explanation":"rendume infinite aagalam."},
{"question":"pass enna pannum?","options":["A) stop","B) skip","C) onnum illa","D) end"],"correct":"C) onnum illa","explanation":"pass nothing pannum."},
{"question":"range(1,4) output enna?","options":["A) 1 2 3","B) 0 1 2","C) 1 2 3 4","D) error"],"correct":"A) 1 2 3","explanation":"1 la start 3 varaikum."},
{"question":"Nested loop na enna?","options":["A) loop inside loop","B) outside","C) single","D) none"],"correct":"A) loop inside loop","explanation":"oru loop kulla inoru loop."},
],

'hindi': [
{"question":"Sequence iterate करने के लिए कौन सा loop?","options":["A) while","B) for","C) do-while","D) loop"],"correct":"B) for","explanation":"for loop sequence iterate करता है।"},
{"question":"Condition के आधार पर कौन सा loop चलता है?","options":["A) for","B) while","C) foreach","D) loop"],"correct":"B) while","explanation":"while condition True तक चलता है।"},
{"question":"for i in range(3): print(i) output?","options":["A) 1 2 3","B) 0 1 2","C) 0 1 2 3","D) Error"],"correct":"B) 0 1 2","explanation":"range(3) 0,1,2 देता है।"},
{"question":"range(5) क्या देता है?","options":["A) 1 to 5","B) 0 to 5","C) 0 to 4","D) 1 to 4"],"correct":"C) 0 to 4","explanation":"0 से 4 तक।"},
{"question":"Loop को पूरी तरह रोकने वाला keyword?","options":["A) continue","B) pass","C) break","D) stop"],"correct":"C) break","explanation":"break loop रोकता है।"},
{"question":"Current iteration skip करने वाला keyword?","options":["A) break","B) continue","C) pass","D) skip"],"correct":"B) continue","explanation":"continue iteration skip करता है।"},
{"question":"Iterations ज्ञात हों तो कौन सा loop?","options":["A) while","B) for","C) infinite","D) nested"],"correct":"B) for","explanation":"for loop उपयोग होता है।"},
{"question":"Infinite loop क्या है?","options":["A) समाप्त होने वाला","B) कभी समाप्त न होने वाला","C) error","D) break"],"correct":"B) कभी समाप्त न होने वाला","explanation":"लगातार चलता रहता है।"},
{"question":"Infinite loop कौन सा हो सकता है?","options":["A) for","B) while","C) दोनों","D) कोई नहीं"],"correct":"C) दोनों","explanation":"दोनों infinite हो सकते हैं।"},
{"question":"pass क्या करता है?","options":["A) stop","B) skip","C) कुछ नहीं","D) end"],"correct":"C) कुछ नहीं","explanation":"pass कुछ नहीं करता।"},
{"question":"range(1,4) output?","options":["A) 1 2 3","B) 0 1 2","C) 1 2 3 4","D) error"],"correct":"A) 1 2 3","explanation":"1 से 3 तक।"},
{"question":"Nested loop क्या है?","options":["A) loop के अंदर loop","B) बाहर loop","C) single","D) none"],"correct":"A) loop के अंदर loop","explanation":"एक loop के अंदर दूसरा loop।"},
],

'malayalam': [
{"question":"Sequence iterate ചെയ്യാൻ ഏത് loop?","options":["A) while","B) for","C) do-while","D) loop"],"correct":"B) for","explanation":"for loop sequence iterate ചെയ്യുന്നു."},
{"question":"Condition അടിസ്ഥാനത്തിൽ run ചെയ്യുന്ന loop?","options":["A) for","B) while","C) foreach","D) loop"],"correct":"B) while","explanation":"while condition true വരെ run ചെയ്യും."},
{"question":"for i in range(3) print(i) output?","options":["A) 1 2 3","B) 0 1 2","C) 0 1 2 3","D) Error"],"correct":"B) 0 1 2","explanation":"range(3) 0,1,2 നൽകുന്നു."},
{"question":"range(5) എന്ത് നൽകുന്നു?","options":["A) 1 to 5","B) 0 to 5","C) 0 to 4","D) 1 to 4"],"correct":"C) 0 to 4","explanation":"0 മുതൽ 4 വരെ."},
{"question":"Loop നിർത്തുന്ന keyword?","options":["A) continue","B) pass","C) break","D) stop"],"correct":"C) break","explanation":"break loop നിർത്തുന്നു."},
{"question":"Current iteration skip ചെയ്യാൻ?","options":["A) break","B) continue","C) pass","D) skip"],"correct":"B) continue","explanation":"continue skip ചെയ്യുന്നു."},
{"question":"Iterations അറിയുമ്പോൾ loop?","options":["A) while","B) for","C) infinite","D) nested"],"correct":"B) for","explanation":"for loop ഉപയോഗിക്കുന്നു."},
{"question":"Infinite loop എന്താണ്?","options":["A) അവസാനിക്കുന്ന","B) അവസാനമില്ലാത്ത","C) error","D) break"],"correct":"B) അവസാനമില്ലാത്ത","explanation":"മുടിയാതെ run ചെയ്യും."},
{"question":"Infinite loop ഏത്?","options":["A) for","B) while","C) രണ്ടും","D) none"],"correct":"C) രണ്ടും","explanation":"രണ്ടും infinite ആകാം."},
{"question":"pass എന്ത് ചെയ്യുന്നു?","options":["A) stop","B) skip","C) ഒന്നുമില്ല","D) end"],"correct":"C) ഒന്നുമില്ല","explanation":"pass ഒന്നും ചെയ്യില്ല."},
{"question":"range(1,4) output?","options":["A) 1 2 3","B) 0 1 2","C) 1 2 3 4","D) error"],"correct":"A) 1 2 3","explanation":"1 മുതൽ 3 വരെ."},
{"question":"Nested loop എന്താണ്?","options":["A) loop ഉള്ളിൽ loop","B) പുറത്തുള്ള","C) single","D) none"],"correct":"A) loop ഉള്ളിൽ loop","explanation":"ഒരു loop-ന്റെ ഉള്ളിൽ മറ്റൊന്ന്."},
],

} ,#loops over

'Functions': {

'english': [
{"question":"What is a function in Python?","options":["A) Loop","B) Block of reusable code","C) Variable","D) Operator"],"correct":"B) Block of reusable code","explanation":"Function is used to reuse code."},
{"question":"Which keyword is used to define a function?","options":["A) func","B) define","C) def","D) function"],"correct":"C) def","explanation":"def keyword is used to define function."},
{"question":"How to call a function named test?","options":["A) call test","B) test()","C) run test","D) execute test"],"correct":"B) test()","explanation":"Function is called using its name with parentheses."},
{"question":"What is return keyword used for?","options":["A) Print output","B) Exit program","C) Return value","D) Loop"],"correct":"C) Return value","explanation":"return sends value back."},
{"question":"What is a parameter?","options":["A) Output","B) Input to function","C) Loop","D) Variable"],"correct":"B) Input to function","explanation":"Parameter is input passed to function."},
{"question":"What is an argument?","options":["A) Function name","B) Value passed","C) Loop","D) Output"],"correct":"B) Value passed","explanation":"Argument is value given to parameter."},
{"question":"Which function has no return value?","options":["A) void","B) none","C) function with no return","D) null"],"correct":"C) function with no return","explanation":"If no return, it returns None."},
{"question":"Default return value of function?","options":["A) 0","B) None","C) False","D) Empty"],"correct":"B) None","explanation":"Python returns None by default."},
{"question":"What are default arguments?","options":["A) Fixed values","B) Predefined values","C) Optional values","D) Loop"],"correct":"B) Predefined values","explanation":"Default values are assigned in function definition."},
{"question":"What is a recursive function?","options":["A) Loop","B) Function calling itself","C) Nested loop","D) Condition"],"correct":"B) Function calling itself","explanation":"Recursion means self-calling."},
{"question":"Lambda function means?","options":["A) Named function","B) Anonymous function","C) Loop","D) Class"],"correct":"B) Anonymous function","explanation":"Lambda is unnamed function."},
{"question":"Which keyword is used for anonymous function?","options":["A) def","B) lambda","C) func","D) anon"],"correct":"B) lambda","explanation":"lambda creates anonymous function."},
],

'tamil': [
{"question":"Function என்றால் என்ன?","options":["A) Loop","B) மீண்டும் பயன்படுத்தக்கூடிய code","C) Variable","D) Operator"],"correct":"B) மீண்டும் பயன்படுத்தக்கூடிய code","explanation":"Function code reuse-க்கு பயன்படும்."},
{"question":"Function define செய்ய எந்த keyword?","options":["A) func","B) define","C) def","D) function"],"correct":"C) def","explanation":"def keyword பயன்படுத்தப்படும்."},
{"question":"test என்ற function call செய்வது?","options":["A) call test","B) test()","C) run test","D) execute test"],"correct":"B) test()","explanation":"Function parentheses உடன் call செய்யப்படும்."},
{"question":"return keyword என்ன செய்கிறது?","options":["A) Print","B) Exit","C) Value return","D) Loop"],"correct":"C) Value return","explanation":"return value திருப்பி தரும்."},
{"question":"Parameter என்றால்?","options":["A) Output","B) Input","C) Loop","D) Variable"],"correct":"B) Input","explanation":"Function-க்கு input ஆகும்."},
{"question":"Argument என்றால்?","options":["A) Name","B) Value","C) Loop","D) Output"],"correct":"B) Value","explanation":"Parameter-க்கு value கொடுப்பது argument."},
{"question":"Return இல்லாத function?","options":["A) void","B) none","C) return இல்லாதது","D) null"],"correct":"C) return இல்லாதது","explanation":"None return ஆகும்."},
{"question":"Default return value?","options":["A) 0","B) None","C) False","D) Empty"],"correct":"B) None","explanation":"Default None."},
{"question":"Default arguments என்றால்?","options":["A) Fixed","B) Predefined","C) Optional","D) Loop"],"correct":"B) Predefined","explanation":"முன்கூட்டியே value கொடுக்கப்படும்."},
{"question":"Recursive function என்றால்?","options":["A) Loop","B) தன்னை தானே அழைக்கும்","C) Nested loop","D) Condition"],"correct":"B) தன்னை தானே அழைக்கும்","explanation":"Self calling."},
{"question":"Lambda function என்றால்?","options":["A) Named","B) Anonymous","C) Loop","D) Class"],"correct":"B) Anonymous","explanation":"பெயரில்லா function."},
{"question":"Anonymous function keyword?","options":["A) def","B) lambda","C) func","D) anon"],"correct":"B) lambda","explanation":"lambda பயன்படுத்தப்படும்."},
],

'tanglish': [
{"question":"Function na enna?","options":["A) Loop","B) reusable code","C) Variable","D) Operator"],"correct":"B) reusable code","explanation":"Function code reuse panna use aagum."},
{"question":"Function define panna keyword ethu?","options":["A) func","B) define","C) def","D) function"],"correct":"C) def","explanation":"def use pannuvom."},
{"question":"test function call epdi?","options":["A) call test","B) test()","C) run test","D) execute test"],"correct":"B) test()","explanation":"() use panni call pannuvom."},
{"question":"return enna pannum?","options":["A) print","B) exit","C) value return","D) loop"],"correct":"C) value return","explanation":"value thiruppi kudukkum."},
{"question":"Parameter na enna?","options":["A) output","B) input","C) loop","D) variable"],"correct":"B) input","explanation":"function ku input."},
{"question":"Argument na enna?","options":["A) name","B) value","C) loop","D) output"],"correct":"B) value","explanation":"parameter ku value."},
{"question":"Return illa function?","options":["A) void","B) none","C) no return","D) null"],"correct":"C) no return","explanation":"None return pannum."},
{"question":"Default return value?","options":["A) 0","B) None","C) False","D) empty"],"correct":"B) None","explanation":"default None."},
{"question":"Default arguments na enna?","options":["A) fixed","B) predefined","C) optional","D) loop"],"correct":"B) predefined","explanation":"already value assign pannirukum."},
{"question":"Recursive function na enna?","options":["A) loop","B) self call","C) nested loop","D) condition"],"correct":"B) self call","explanation":"thanaiye call pannum."},
{"question":"Lambda function na enna?","options":["A) named","B) anonymous","C) loop","D) class"],"correct":"B) anonymous","explanation":"name illa function."},
{"question":"Anonymous function keyword ethu?","options":["A) def","B) lambda","C) func","D) anon"],"correct":"B) lambda","explanation":"lambda use pannuvom."},
],

'hindi': [
{"question":"Function क्या है?","options":["A) Loop","B) Reusable code","C) Variable","D) Operator"],"correct":"B) Reusable code","explanation":"Function code reuse के लिए है।"},
{"question":"Function define करने का keyword?","options":["A) func","B) define","C) def","D) function"],"correct":"C) def","explanation":"def keyword उपयोग होता है।"},
{"question":"test function call कैसे करें?","options":["A) call test","B) test()","C) run test","D) execute test"],"correct":"B) test()","explanation":"() से call करते हैं।"},
{"question":"return क्या करता है?","options":["A) print","B) exit","C) value return","D) loop"],"correct":"C) value return","explanation":"value वापस देता है।"},
{"question":"Parameter क्या है?","options":["A) output","B) input","C) loop","D) variable"],"correct":"B) input","explanation":"function का input।"},
{"question":"Argument क्या है?","options":["A) name","B) value","C) loop","D) output"],"correct":"B) value","explanation":"parameter को दी गई value।"},
{"question":"Return नहीं होने पर क्या होता है?","options":["A) 0","B) None","C) False","D) empty"],"correct":"B) None","explanation":"default None return होता है।"},
{"question":"Default arguments क्या हैं?","options":["A) fixed","B) predefined","C) optional","D) loop"],"correct":"B) predefined","explanation":"पहले से value दी होती है।"},
{"question":"Recursive function क्या है?","options":["A) loop","B) खुद को call करना","C) nested loop","D) condition"],"correct":"B) खुद को call करना","explanation":"self calling।"},
{"question":"Lambda function क्या है?","options":["A) named","B) anonymous","C) loop","D) class"],"correct":"B) anonymous","explanation":"नाम रहित function।"},
{"question":"Anonymous function keyword?","options":["A) def","B) lambda","C) func","D) anon"],"correct":"B) lambda","explanation":"lambda उपयोग होता है।"},
{"question":"Function का default return?","options":["A) 0","B) None","C) False","D) empty"],"correct":"B) None","explanation":"default None होता है।"},
],

'malayalam': [
{"question":"Function എന്താണ്?","options":["A) Loop","B) Reusable code","C) Variable","D) Operator"],"correct":"B) Reusable code","explanation":"Function code reuse ചെയ്യാൻ ഉപയോഗിക്കുന്നു."},
{"question":"Function define ചെയ്യാൻ keyword?","options":["A) func","B) define","C) def","D) function"],"correct":"C) def","explanation":"def ഉപയോഗിക്കുന്നു."},
{"question":"test function call എങ്ങനെ?","options":["A) call test","B) test()","C) run test","D) execute test"],"correct":"B) test()","explanation":"() ഉപയോഗിച്ച് call ചെയ്യുന്നു."},
{"question":"return എന്ത് ചെയ്യുന്നു?","options":["A) print","B) exit","C) value return","D) loop"],"correct":"C) value return","explanation":"value തിരികെ നൽകുന്നു."},
{"question":"Parameter എന്താണ്?","options":["A) output","B) input","C) loop","D) variable"],"correct":"B) input","explanation":"function input."},
{"question":"Argument എന്താണ്?","options":["A) name","B) value","C) loop","D) output"],"correct":"B) value","explanation":"parameter-ന് value നൽകുന്നത്."},
{"question":"Return ഇല്ലെങ്കിൽ?","options":["A) 0","B) None","C) False","D) empty"],"correct":"B) None","explanation":"default None."},
{"question":"Default arguments എന്ത്?","options":["A) fixed","B) predefined","C) optional","D) loop"],"correct":"B) predefined","explanation":"മുൻകൂട്ടി value നൽകിയിരിക്കും."},
{"question":"Recursive function എന്ത്?","options":["A) loop","B) self call","C) nested loop","D) condition"],"correct":"B) self call","explanation":"സ്വയം call ചെയ്യുന്നു."},
{"question":"Lambda function എന്ത്?","options":["A) named","B) anonymous","C) loop","D) class"],"correct":"B) anonymous","explanation":"പേര് ഇല്ലാത്ത function."},
{"question":"Anonymous function keyword?","options":["A) def","B) lambda","C) func","D) anon"],"correct":"B) lambda","explanation":"lambda ഉപയോഗിക്കുന്നു."},
{"question":"Default return value?","options":["A) 0","B) None","C) False","D) empty"],"correct":"B) None","explanation":"default None."},
],}, #function over

'Lists and Tuples in Python': {

'english': [
{"question":"What is a list in Python?","options":["A) Immutable","B) Ordered collection","C) Function","D) Loop"],"correct":"B) Ordered collection","explanation":"List is ordered and mutable."},
{"question":"What is a tuple in Python?","options":["A) Mutable","B) Immutable collection","C) Loop","D) Function"],"correct":"B) Immutable collection","explanation":"Tuple cannot be changed."},
{"question":"Which bracket is used for list?","options":["A) ()","B) {}","C) []","D) <>"],"correct":"C) []","explanation":"List uses square brackets."},
{"question":"Which bracket is used for tuple?","options":["A) ()","B) {}","C) []","D) <>"],"correct":"A) ()","explanation":"Tuple uses parentheses."},
{"question":"Can list store multiple data types?","options":["A) No","B) Yes","C) Only int","D) Only string"],"correct":"B) Yes","explanation":"List can store mixed data types."},
{"question":"Can tuple store multiple data types?","options":["A) No","B) Yes","C) Only int","D) Only string"],"correct":"B) Yes","explanation":"Tuple can store mixed data types."},
{"question":"Which is mutable?","options":["A) Tuple","B) List","C) String","D) Integer"],"correct":"B) List","explanation":"List is mutable."},
{"question":"Which is immutable?","options":["A) List","B) Tuple","C) Dictionary","D) Set"],"correct":"B) Tuple","explanation":"Tuple is immutable."},
{"question":"How to access first element in list L?","options":["A) L(0)","B) L[1]","C) L[0]","D) L.first"],"correct":"C) L[0]","explanation":"Index starts from 0."},
{"question":"How to access first element in tuple T?","options":["A) T(0)","B) T[0]","C) T.first","D) T{0}"],"correct":"B) T[0]","explanation":"Same indexing as list."},
{"question":"Which method is used to add element in list?","options":["A) add()","B) append()","C) insert()","D) Both B and C"],"correct":"D) Both B and C","explanation":"append and insert are used."},
{"question":"Can we modify tuple elements?","options":["A) Yes","B) No","C) Sometimes","D) Only integers"],"correct":"B) No","explanation":"Tuple is immutable."},
],

'tamil': [
{"question":"List என்றால் என்ன?","options":["A) Immutable","B) Ordered collection","C) Function","D) Loop"],"correct":"B) Ordered collection","explanation":"List ordered மற்றும் mutable."},
{"question":"Tuple என்றால் என்ன?","options":["A) Mutable","B) Immutable collection","C) Loop","D) Function"],"correct":"B) Immutable collection","explanation":"Tuple மாற்ற முடியாது."},
{"question":"List க்கு எந்த bracket?","options":["A) ()","B) {}","C) []","D) <>"],"correct":"C) []","explanation":"Square bracket பயன்படுத்தப்படும்."},
{"question":"Tuple க்கு எந்த bracket?","options":["A) ()","B) {}","C) []","D) <>"],"correct":"A) ()","explanation":"Parentheses பயன்படுத்தப்படும்."},
{"question":"List multiple datatype store செய்யுமா?","options":["A) இல்லை","B) ஆம்","C) int மட்டும்","D) string மட்டும்"],"correct":"B) ஆம்","explanation":"பல datatype store செய்யலாம்."},
{"question":"Tuple multiple datatype store செய்யுமா?","options":["A) இல்லை","B) ஆம்","C) int மட்டும்","D) string மட்டும்"],"correct":"B) ஆம்","explanation":"Tuple-லும் mixed datatype இருக்கலாம்."},
{"question":"Mutable எது?","options":["A) Tuple","B) List","C) String","D) Integer"],"correct":"B) List","explanation":"List mutable."},
{"question":"Immutable எது?","options":["A) List","B) Tuple","C) Dictionary","D) Set"],"correct":"B) Tuple","explanation":"Tuple immutable."},
{"question":"List-ல் first element access?","options":["A) L(0)","B) L[1]","C) L[0]","D) L.first"],"correct":"C) L[0]","explanation":"Index 0-ல் தொடங்கும்."},
{"question":"Tuple-ல் first element access?","options":["A) T(0)","B) T[0]","C) T.first","D) T{0}"],"correct":"B) T[0]","explanation":"List போலவே indexing."},
{"question":"List-ல் element add செய்ய method?","options":["A) add()","B) append()","C) insert()","D) B மற்றும் C"],"correct":"D) B மற்றும் C","explanation":"append, insert பயன்படுத்தலாம்."},
{"question":"Tuple modify செய்ய முடியுமா?","options":["A) ஆம்","B) இல்லை","C) சில நேரம்","D) int மட்டும்"],"correct":"B) இல்லை","explanation":"Tuple immutable."},
],

'tanglish': [
{"question":"List na enna?","options":["A) Immutable","B) Ordered collection","C) Function","D) Loop"],"correct":"B) Ordered collection","explanation":"List ordered and mutable."},
{"question":"Tuple na enna?","options":["A) Mutable","B) Immutable","C) Loop","D) Function"],"correct":"B) Immutable","explanation":"Tuple change panna mudiyathu."},
{"question":"List ku use panna bracket?","options":["A) ()","B) {}","C) []","D) <>"],"correct":"C) []","explanation":"Square bracket use pannuvom."},
{"question":"Tuple ku bracket?","options":["A) ()","B) {}","C) []","D) <>"],"correct":"A) ()","explanation":"Parentheses use pannuvom."},
{"question":"List la mixed datatype store panna mudiyuma?","options":["A) illa","B) mudiyum","C) int mattum","D) string mattum"],"correct":"B) mudiyum","explanation":"mixed values store pannalam."},
{"question":"Tuple la mixed datatype store panna mudiyuma?","options":["A) illa","B) mudiyum","C) int mattum","D) string mattum"],"correct":"B) mudiyum","explanation":"tuple la kuda mudiyum."},
{"question":"Mutable edhu?","options":["A) Tuple","B) List","C) String","D) Integer"],"correct":"B) List","explanation":"List mutable."},
{"question":"Immutable edhu?","options":["A) List","B) Tuple","C) Dictionary","D) Set"],"correct":"B) Tuple","explanation":"Tuple immutable."},
{"question":"List la first element epdi access?","options":["A) L(0)","B) L[1]","C) L[0]","D) L.first"],"correct":"C) L[0]","explanation":"Index 0."},
{"question":"Tuple la first element epdi access?","options":["A) T(0)","B) T[0]","C) T.first","D) T{0}"],"correct":"B) T[0]","explanation":"same as list."},
{"question":"List la add panna method?","options":["A) add()","B) append()","C) insert()","D) B and C"],"correct":"D) B and C","explanation":"append, insert use pannuvom."},
{"question":"Tuple modify panna mudiyuma?","options":["A) mudiyum","B) mudiyathu","C) konjam","D) int mattum"],"correct":"B) mudiyathu","explanation":"Tuple immutable."},
],

'hindi': [
{"question":"List क्या है?","options":["A) Immutable","B) Ordered collection","C) Function","D) Loop"],"correct":"B) Ordered collection","explanation":"List ordered और mutable है।"},
{"question":"Tuple क्या है?","options":["A) Mutable","B) Immutable","C) Loop","D) Function"],"correct":"B) Immutable","explanation":"Tuple बदल नहीं सकता।"},
{"question":"List के लिए bracket?","options":["A) ()","B) {}","C) []","D) <>"],"correct":"C) []","explanation":"Square bracket।"},
{"question":"Tuple के लिए bracket?","options":["A) ()","B) {}","C) []","D) <>"],"correct":"A) ()","explanation":"Parentheses।"},
{"question":"List multiple datatype रख सकता है?","options":["A) नहीं","B) हाँ","C) int only","D) string only"],"correct":"B) हाँ","explanation":"Mixed values रख सकता है।"},
{"question":"Tuple multiple datatype रख सकता है?","options":["A) नहीं","B) हाँ","C) int only","D) string only"],"correct":"B) हाँ","explanation":"Tuple भी रख सकता है।"},
{"question":"Mutable कौन है?","options":["A) Tuple","B) List","C) String","D) Integer"],"correct":"B) List","explanation":"List mutable है।"},
{"question":"Immutable कौन है?","options":["A) List","B) Tuple","C) Dictionary","D) Set"],"correct":"B) Tuple","explanation":"Tuple immutable है।"},
{"question":"List का पहला element कैसे access करें?","options":["A) L(0)","B) L[1]","C) L[0]","D) L.first"],"correct":"C) L[0]","explanation":"Index 0 से शुरू।"},
{"question":"Tuple का पहला element कैसे access करें?","options":["A) T(0)","B) T[0]","C) T.first","D) T{0}"],"correct":"B) T[0]","explanation":"List जैसा indexing।"},
{"question":"List में add करने का method?","options":["A) add()","B) append()","C) insert()","D) Both"],"correct":"D) Both","explanation":"append और insert।"},
{"question":"Tuple modify कर सकते हैं?","options":["A) हाँ","B) नहीं","C) कभी-कभी","D) केवल int"],"correct":"B) नहीं","explanation":"Tuple immutable है।"},
],

'malayalam': [
{"question":"List എന്താണ്?","options":["A) Immutable","B) Ordered collection","C) Function","D) Loop"],"correct":"B) Ordered collection","explanation":"List ordered and mutable ആണ്."},
{"question":"Tuple എന്താണ്?","options":["A) Mutable","B) Immutable","C) Loop","D) Function"],"correct":"B) Immutable","explanation":"Tuple മാറ്റാൻ കഴിയില്ല."},
{"question":"List bracket ഏത്?","options":["A) ()","B) {}","C) []","D) <>"],"correct":"C) []","explanation":"Square bracket ഉപയോഗിക്കുന്നു."},
{"question":"Tuple bracket ഏത്?","options":["A) ()","B) {}","C) []","D) <>"],"correct":"A) ()","explanation":"Parentheses ഉപയോഗിക്കുന്നു."},
{"question":"List mixed datatype store ചെയ്യുമോ?","options":["A) ഇല്ല","B) ആണ്","C) int മാത്രം","D) string മാത്രം"],"correct":"B) ആണ്","explanation":"Mixed values store ചെയ്യാം."},
{"question":"Tuple mixed datatype store ചെയ്യുമോ?","options":["A) ഇല്ല","B) ആണ്","C) int മാത്രം","D) string മാത്രം"],"correct":"B) ആണ്","explanation":"Tuple-ലും സാധിക്കും."},
{"question":"Mutable ഏത്?","options":["A) Tuple","B) List","C) String","D) Integer"],"correct":"B) List","explanation":"List mutable ആണ്."},
{"question":"Immutable ഏത്?","options":["A) List","B) Tuple","C) Dictionary","D) Set"],"correct":"B) Tuple","explanation":"Tuple immutable ആണ്."},
{"question":"List first element access?","options":["A) L(0)","B) L[1]","C) L[0]","D) L.first"],"correct":"C) L[0]","explanation":"Index 0."},
{"question":"Tuple first element access?","options":["A) T(0)","B) T[0]","C) T.first","D) T{0}"],"correct":"B) T[0]","explanation":"Same indexing."},
{"question":"List add method?","options":["A) add()","B) append()","C) insert()","D) Both"],"correct":"D) Both","explanation":"append, insert ഉപയോഗിക്കുന്നു."},
{"question":"Tuple modify ചെയ്യാമോ?","options":["A) ആണ്","B) ഇല്ല","C) ചിലപ്പോൾ","D) int മാത്രം"],"correct":"B) ഇല്ല","explanation":"Tuple immutable ആണ്."},
],

},
'Dictionaries and Sets': {

'english': [
{"question":"What is a dictionary in Python?","options":["A) Ordered list","B) Key-value pairs","C) Loop","D) Function"],"correct":"B) Key-value pairs","explanation":"Dictionary stores data as key-value pairs."},
{"question":"What is a set in Python?","options":["A) Ordered collection","B) Unique elements collection","C) Key-value","D) Function"],"correct":"B) Unique elements collection","explanation":"Set stores unique values."},
{"question":"Which bracket is used for dictionary?","options":["A) []","B) ()","C) {}","D) <>"],"correct":"C) {}","explanation":"Curly braces used for dictionary."},
{"question":"Which bracket is used for set?","options":["A) []","B) ()","C) {}","D) <>"],"correct":"C) {}","explanation":"Set also uses curly braces."},
{"question":"Can dictionary have duplicate keys?","options":["A) Yes","B) No","C) Sometimes","D) Only int"],"correct":"B) No","explanation":"Keys must be unique."},
{"question":"Can set have duplicate values?","options":["A) Yes","B) No","C) Sometimes","D) Only string"],"correct":"B) No","explanation":"Set stores only unique values."},
{"question":"How to access value in dictionary d?","options":["A) d(key)","B) d[key]","C) d.value","D) d->key"],"correct":"B) d[key]","explanation":"Use key inside brackets."},
{"question":"Which method adds element in set?","options":["A) append()","B) add()","C) insert()","D) push()"],"correct":"B) add()","explanation":"add() is used for sets."},
{"question":"Which method adds key-value in dictionary?","options":["A) add()","B) append()","C) assign using key","D) insert()"],"correct":"C) assign using key","explanation":"d[key]=value is used."},
{"question":"Are dictionaries mutable?","options":["A) No","B) Yes","C) Sometimes","D) Only string"],"correct":"B) Yes","explanation":"Dictionary can be modified."},
{"question":"Are sets mutable?","options":["A) No","B) Yes","C) Sometimes","D) Only int"],"correct":"B) Yes","explanation":"Set can be modified."},
{"question":"Empty set creation?","options":["A) {}","B) []","C) set()","D) ()"],"correct":"C) set()","explanation":"{} creates empty dictionary."},
],

'tamil': [
{"question":"Dictionary என்றால் என்ன?","options":["A) List","B) Key-value pairs","C) Loop","D) Function"],"correct":"B) Key-value pairs","explanation":"Key மற்றும் value சேர்த்து இருக்கும்."},
{"question":"Set என்றால் என்ன?","options":["A) Ordered","B) Unique elements","C) Key-value","D) Function"],"correct":"B) Unique elements","explanation":"Set unique values மட்டும்."},
{"question":"Dictionary க்கு எந்த bracket?","options":["A) []","B) ()","C) {}","D) <>"],"correct":"C) {}","explanation":"Curly braces பயன்படுத்தப்படும்."},
{"question":"Set க்கு எந்த bracket?","options":["A) []","B) ()","C) {}","D) <>"],"correct":"C) {}","explanation":"Set-க்கும் {} பயன்படுத்தப்படும்."},
{"question":"Dictionary duplicate key இருக்குமா?","options":["A) ஆம்","B) இல்லை","C) சில நேரம்","D) int மட்டும்"],"correct":"B) இல்லை","explanation":"Key unique ஆக வேண்டும்."},
{"question":"Set duplicate value இருக்குமா?","options":["A) ஆம்","B) இல்லை","C) சில நேரம்","D) string மட்டும்"],"correct":"B) இல்லை","explanation":"Unique values மட்டும்."},
{"question":"Dictionary value access?","options":["A) d(key)","B) d[key]","C) d.value","D) d->key"],"correct":"B) d[key]","explanation":"Key மூலம் access."},
{"question":"Set-ல் add செய்ய method?","options":["A) append()","B) add()","C) insert()","D) push()"],"correct":"B) add()","explanation":"add() பயன்படுத்தப்படும்."},
{"question":"Dictionary-ல் value add?","options":["A) add()","B) append()","C) key assign","D) insert()"],"correct":"C) key assign","explanation":"d[key]=value."},
{"question":"Dictionary mutable ஆ?","options":["A) இல்லை","B) ஆம்","C) சில நேரம்","D) string மட்டும்"],"correct":"B) ஆம்","explanation":"Modify செய்யலாம்."},
{"question":"Set mutable ஆ?","options":["A) இல்லை","B) ஆம்","C) சில நேரம்","D) int மட்டும்"],"correct":"B) ஆம்","explanation":"Modify செய்யலாம்."},
{"question":"Empty set எப்படி create?","options":["A) {}","B) []","C) set()","D) ()"],"correct":"C) set()","explanation":"{} dictionary ஆகும்."},
],

'tanglish': [
{"question":"Dictionary na enna?","options":["A) List","B) key-value pairs","C) Loop","D) Function"],"correct":"B) key-value pairs","explanation":"Key value ah store pannum."},
{"question":"Set na enna?","options":["A) ordered","B) unique values","C) key-value","D) function"],"correct":"B) unique values","explanation":"duplicate illa."},
{"question":"Dictionary bracket ethu?","options":["A) []","B) ()","C) {}","D) <>"],"correct":"C) {}","explanation":"curly braces."},
{"question":"Set bracket ethu?","options":["A) []","B) ()","C) {}","D) <>"],"correct":"C) {}","explanation":"same curly braces."},
{"question":"Dictionary la duplicate key varuma?","options":["A) varum","B) varaadhu","C) sometimes","D) int mattum"],"correct":"B) varaadhu","explanation":"keys unique."},
{"question":"Set la duplicate values varuma?","options":["A) varum","B) varaadhu","C) sometimes","D) string mattum"],"correct":"B) varaadhu","explanation":"unique values."},
{"question":"Dictionary value epdi access?","options":["A) d(key)","B) d[key]","C) d.value","D) d->key"],"correct":"B) d[key]","explanation":"key use pannuvom."},
{"question":"Set la add panna method?","options":["A) append()","B) add()","C) insert()","D) push()"],"correct":"B) add()","explanation":"add() use pannuvom."},
{"question":"Dictionary la add epdi?","options":["A) add()","B) append()","C) d[key]=value","D) insert()"],"correct":"C) d[key]=value","explanation":"assign pannuvom."},
{"question":"Dictionary mutable aa?","options":["A) illa","B) aama","C) konjam","D) string mattum"],"correct":"B) aama","explanation":"modify pannalam."},
{"question":"Set mutable aa?","options":["A) illa","B) aama","C) konjam","D) int mattum"],"correct":"B) aama","explanation":"modify pannalam."},
{"question":"Empty set epdi create?","options":["A) {}","B) []","C) set()","D) ()"],"correct":"C) set()","explanation":"{} dictionary aagum."},
],

'hindi': [
{"question":"Dictionary क्या है?","options":["A) List","B) Key-value pairs","C) Loop","D) Function"],"correct":"B) Key-value pairs","explanation":"Key और value में data store होता है।"},
{"question":"Set क्या है?","options":["A) Ordered","B) Unique values","C) Key-value","D) Function"],"correct":"B) Unique values","explanation":"Duplicate नहीं होता।"},
{"question":"Dictionary के लिए bracket?","options":["A) []","B) ()","C) {}","D) <>"],"correct":"C) {}","explanation":"Curly braces।"},
{"question":"Set के लिए bracket?","options":["A) []","B) ()","C) {}","D) <>"],"correct":"C) {}","explanation":"Same curly braces।"},
{"question":"Dictionary में duplicate key?","options":["A) हाँ","B) नहीं","C) कभी-कभी","D) int only"],"correct":"B) नहीं","explanation":"Keys unique होती हैं।"},
{"question":"Set में duplicate values?","options":["A) हाँ","B) नहीं","C) कभी-कभी","D) string only"],"correct":"B) नहीं","explanation":"Unique values।"},
{"question":"Dictionary value access कैसे?","options":["A) d(key)","B) d[key]","C) d.value","D) d->key"],"correct":"B) d[key]","explanation":"Key से access।"},
{"question":"Set में add method?","options":["A) append()","B) add()","C) insert()","D) push()"],"correct":"B) add()","explanation":"add() उपयोग होता है।"},
{"question":"Dictionary में add कैसे?","options":["A) add()","B) append()","C) d[key]=value","D) insert()"],"correct":"C) d[key]=value","explanation":"Assign करते हैं।"},
{"question":"Dictionary mutable है?","options":["A) नहीं","B) हाँ","C) कभी-कभी","D) string only"],"correct":"B) हाँ","explanation":"Modify कर सकते हैं।"},
{"question":"Set mutable है?","options":["A) नहीं","B) हाँ","C) कभी-कभी","D) int only"],"correct":"B) हाँ","explanation":"Modify कर सकते हैं।"},
{"question":"Empty set कैसे बनाएं?","options":["A) {}","B) []","C) set()","D) ()"],"correct":"C) set()","explanation":"{} dictionary बनाता है।"},
],

'malayalam': [
{"question":"Dictionary എന്താണ്?","options":["A) List","B) Key-value pairs","C) Loop","D) Function"],"correct":"B) Key-value pairs","explanation":"Key-value ആയി data സൂക്ഷിക്കുന്നു."},
{"question":"Set എന്താണ്?","options":["A) Ordered","B) Unique values","C) Key-value","D) Function"],"correct":"B) Unique values","explanation":"Duplicate ഇല്ല."},
{"question":"Dictionary bracket ഏത്?","options":["A) []","B) ()","C) {}","D) <>"],"correct":"C) {}","explanation":"Curly braces."},
{"question":"Set bracket ഏത്?","options":["A) []","B) ()","C) {}","D) <>"],"correct":"C) {}","explanation":"Same curly braces."},
{"question":"Dictionary duplicate key ഉണ്ടോ?","options":["A) ഉണ്ട്","B) ഇല്ല","C) ചിലപ്പോൾ","D) int മാത്രം"],"correct":"B) ഇല്ല","explanation":"Keys unique ആണ്."},
{"question":"Set duplicate values ഉണ്ടോ?","options":["A) ഉണ്ട്","B) ഇല്ല","C) ചിലപ്പോൾ","D) string മാത്രം"],"correct":"B) ഇല്ല","explanation":"Unique values മാത്രം."},
{"question":"Dictionary value access?","options":["A) d(key)","B) d[key]","C) d.value","D) d->key"],"correct":"B) d[key]","explanation":"Key ഉപയോഗിച്ച് access ചെയ്യുന്നു."},
{"question":"Set add method?","options":["A) append()","B) add()","C) insert()","D) push()"],"correct":"B) add()","explanation":"add() ഉപയോഗിക്കുന്നു."},
{"question":"Dictionary add എങ്ങനെ?","options":["A) add()","B) append()","C) d[key]=value","D) insert()"],"correct":"C) d[key]=value","explanation":"Assign ചെയ്യുന്നു."},
{"question":"Dictionary mutable ആണോ?","options":["A) ഇല്ല","B) ആണ്","C) ചിലപ്പോൾ","D) string മാത്രം"],"correct":"B) ആണ്","explanation":"Modify ചെയ്യാം."},
{"question":"Set mutable ആണോ?","options":["A) ഇല്ല","B) ആണ്","C) ചിലപ്പോൾ","D) int മാത്രം"],"correct":"B) ആണ്","explanation":"Modify ചെയ്യാം."},
{"question":"Empty set എങ്ങനെ create?","options":["A) {}","B) []","C) set()","D) ()"],"correct":"C) set()","explanation":"{} dictionary ആണ്."},
],



},#dictionaries and sets over

'File Handling': {

'english': [
{"question":"What is file handling in Python?","options":["A) Loop","B) Working with files","C) Function","D) Variable"],"correct":"B) Working with files","explanation":"File handling is used to read/write files."},
{"question":"Which function is used to open a file?","options":["A) file()","B) open()","C) read()","D) write()"],"correct":"B) open()","explanation":"open() is used to open files."},
{"question":"Which mode is used to read a file?","options":["A) w","B) a","C) r","D) x"],"correct":"C) r","explanation":"r mode is for reading."},
{"question":"Which mode is used to write a file?","options":["A) r","B) w","C) a","D) x"],"correct":"B) w","explanation":"w mode is for writing."},
{"question":"Which mode is used to append data?","options":["A) r","B) w","C) a","D) x"],"correct":"C) a","explanation":"a mode adds data at end."},
{"question":"Which method reads entire file?","options":["A) read()","B) readline()","C) readlines()","D) write()"],"correct":"A) read()","explanation":"read() reads full content."},
{"question":"Which method reads one line?","options":["A) read()","B) readline()","C) readlines()","D) write()"],"correct":"B) readline()","explanation":"Reads single line."},
{"question":"Which method reads all lines as list?","options":["A) read()","B) readline()","C) readlines()","D) write()"],"correct":"C) readlines()","explanation":"Returns list of lines."},
{"question":"Which method writes to file?","options":["A) read()","B) write()","C) open()","D) append()"],"correct":"B) write()","explanation":"write() adds content."},
{"question":"Why use close()?","options":["A) Delete file","B) Save memory","C) Close file","D) Read file"],"correct":"C) Close file","explanation":"close() releases file resources."},
{"question":"Which keyword automatically closes file?","options":["A) auto","B) with","C) close","D) file"],"correct":"B) with","explanation":"with handles closing automatically."},
{"question":"What does x mode do?","options":["A) Read","B) Write","C) Create new file","D) Append"],"correct":"C) Create new file","explanation":"x creates file if not exists."},
],

'tamil': [
{"question":"File handling என்றால் என்ன?","options":["A) Loop","B) File வேலை","C) Function","D) Variable"],"correct":"B) File வேலை","explanation":"File read/write செய்ய பயன்படும்."},
{"question":"File open செய்ய function?","options":["A) file()","B) open()","C) read()","D) write()"],"correct":"B) open()","explanation":"open() பயன்படுத்தப்படும்."},
{"question":"Read mode எது?","options":["A) w","B) a","C) r","D) x"],"correct":"C) r","explanation":"r mode read."},
{"question":"Write mode எது?","options":["A) r","B) w","C) a","D) x"],"correct":"B) w","explanation":"w mode write."},
{"question":"Append mode எது?","options":["A) r","B) w","C) a","D) x"],"correct":"C) a","explanation":"a mode data add செய்யும்."},
{"question":"முழு file read செய்ய method?","options":["A) read()","B) readline()","C) readlines()","D) write()"],"correct":"A) read()","explanation":"Full content read செய்யும்."},
{"question":"ஒரு line read செய்ய?","options":["A) read()","B) readline()","C) readlines()","D) write()"],"correct":"B) readline()","explanation":"ஒரு line மட்டும்."},
{"question":"அனைத்து lines list ஆக?","options":["A) read()","B) readline()","C) readlines()","D) write()"],"correct":"C) readlines()","explanation":"List return ஆகும்."},
{"question":"File write செய்ய method?","options":["A) read()","B) write()","C) open()","D) append()"],"correct":"B) write()","explanation":"Content எழுதும்."},
{"question":"close() ஏன்?","options":["A) Delete","B) Memory save","C) Close file","D) Read"],"correct":"C) Close file","explanation":"File close செய்யும்."},
{"question":"Auto close keyword?","options":["A) auto","B) with","C) close","D) file"],"correct":"B) with","explanation":"Auto close செய்யும்."},
{"question":"x mode என்ன?","options":["A) Read","B) Write","C) Create","D) Append"],"correct":"C) Create","explanation":"புதிய file உருவாக்கும்."},
],

'tanglish': [
{"question":"File handling na enna?","options":["A) loop","B) file work","C) function","D) variable"],"correct":"B) file work","explanation":"file read/write panna use."},
{"question":"File open panna function?","options":["A) file()","B) open()","C) read()","D) write()"],"correct":"B) open()","explanation":"open() use pannuvom."},
{"question":"Read mode ethu?","options":["A) w","B) a","C) r","D) x"],"correct":"C) r","explanation":"r read."},
{"question":"Write mode ethu?","options":["A) r","B) w","C) a","D) x"],"correct":"B) w","explanation":"w write."},
{"question":"Append mode ethu?","options":["A) r","B) w","C) a","D) x"],"correct":"C) a","explanation":"a add pannum."},
{"question":"Full file read panna?","options":["A) read()","B) readline()","C) readlines()","D) write()"],"correct":"A) read()","explanation":"full read."},
{"question":"Single line read panna?","options":["A) read()","B) readline()","C) readlines()","D) write()"],"correct":"B) readline()","explanation":"one line."},
{"question":"All lines list aa?","options":["A) read()","B) readline()","C) readlines()","D) write()"],"correct":"C) readlines()","explanation":"list return."},
{"question":"Write panna method?","options":["A) read()","B) write()","C) open()","D) append()"],"correct":"B) write()","explanation":"write use pannuvom."},
{"question":"close() enna pannum?","options":["A) delete","B) memory save","C) close file","D) read"],"correct":"C) close file","explanation":"file close pannum."},
{"question":"Auto close keyword?","options":["A) auto","B) with","C) close","D) file"],"correct":"B) with","explanation":"auto close."},
{"question":"x mode na enna?","options":["A) read","B) write","C) create","D) append"],"correct":"C) create","explanation":"new file create."},
],

'hindi': [
{"question":"File handling क्या है?","options":["A) Loop","B) File work","C) Function","D) Variable"],"correct":"B) File work","explanation":"File read/write के लिए उपयोग होता है।"},
{"question":"File open करने का function?","options":["A) file()","B) open()","C) read()","D) write()"],"correct":"B) open()","explanation":"open() उपयोग होता है।"},
{"question":"Read mode कौन सा?","options":["A) w","B) a","C) r","D) x"],"correct":"C) r","explanation":"r mode read करता है।"},
{"question":"Write mode कौन सा?","options":["A) r","B) w","C) a","D) x"],"correct":"B) w","explanation":"w mode write करता है।"},
{"question":"Append mode कौन सा?","options":["A) r","B) w","C) a","D) x"],"correct":"C) a","explanation":"a data add करता है।"},
{"question":"पूरा file पढ़ने का method?","options":["A) read()","B) readline()","C) readlines()","D) write()"],"correct":"A) read()","explanation":"पूरा content पढ़ता है।"},
{"question":"एक line पढ़ने का method?","options":["A) read()","B) readline()","C) readlines()","D) write()"],"correct":"B) readline()","explanation":"एक line पढ़ता है।"},
{"question":"सभी lines list में?","options":["A) read()","B) readline()","C) readlines()","D) write()"],"correct":"C) readlines()","explanation":"List return करता है।"},
{"question":"File में लिखने का method?","options":["A) read()","B) write()","C) open()","D) append()"],"correct":"B) write()","explanation":"Content लिखता है।"},
{"question":"close() क्यों?","options":["A) Delete","B) Memory save","C) Close file","D) Read"],"correct":"C) Close file","explanation":"File बंद करता है।"},
{"question":"Auto close keyword?","options":["A) auto","B) with","C) close","D) file"],"correct":"B) with","explanation":"Automatically close करता है।"},
{"question":"x mode क्या है?","options":["A) Read","B) Write","C) Create","D) Append"],"correct":"C) Create","explanation":"नई file बनाता है।"},
],

'malayalam': [
{"question":"File handling എന്താണ്?","options":["A) Loop","B) File work","C) Function","D) Variable"],"correct":"B) File work","explanation":"File read/write ചെയ്യാൻ ഉപയോഗിക്കുന്നു."},
{"question":"File open ചെയ്യാൻ function?","options":["A) file()","B) open()","C) read()","D) write()"],"correct":"B) open()","explanation":"open() ഉപയോഗിക്കുന്നു."},
{"question":"Read mode ഏത്?","options":["A) w","B) a","C) r","D) x"],"correct":"C) r","explanation":"r mode read."},
{"question":"Write mode ഏത്?","options":["A) r","B) w","C) a","D) x"],"correct":"B) w","explanation":"w mode write."},
{"question":"Append mode ഏത്?","options":["A) r","B) w","C) a","D) x"],"correct":"C) a","explanation":"a mode add."},
{"question":"Full file read method?","options":["A) read()","B) readline()","C) readlines()","D) write()"],"correct":"A) read()","explanation":"Full content വായിക്കുന്നു."},
{"question":"Single line read method?","options":["A) read()","B) readline()","C) readlines()","D) write()"],"correct":"B) readline()","explanation":"ഒരു line."},
{"question":"All lines list ആയി?","options":["A) read()","B) readline()","C) readlines()","D) write()"],"correct":"C) readlines()","explanation":"List return ചെയ്യും."},
{"question":"Write method?","options":["A) read()","B) write()","C) open()","D) append()"],"correct":"B) write()","explanation":"Content എഴുതുന്നു."},
{"question":"close() എന്ത്?","options":["A) Delete","B) Memory save","C) Close file","D) Read"],"correct":"C) Close file","explanation":"File close ചെയ്യുന്നു."},
{"question":"Auto close keyword?","options":["A) auto","B) with","C) close","D) file"],"correct":"B) with","explanation":"Auto close."},
{"question":"x mode എന്ത്?","options":["A) Read","B) Write","C) Create","D) Append"],"correct":"C) Create","explanation":"New file create."},
],

},#file handling over

'Exception Handling': {

'english': [
{"question":"What is an exception?","options":["A) Loop","B) Error during execution","C) Function","D) Variable"],"correct":"B) Error during execution","explanation":"Exception occurs at runtime."},
{"question":"Which block is used to handle exceptions?","options":["A) try","B) catch","C) handle","D) error"],"correct":"A) try","explanation":"try block is used to test code."},
{"question":"Which block catches the exception?","options":["A) try","B) except","C) finally","D) error"],"correct":"B) except","explanation":"except handles the error."},
{"question":"Which block always executes?","options":["A) try","B) except","C) finally","D) error"],"correct":"C) finally","explanation":"finally always runs."},
{"question":"Which keyword is used to raise exception?","options":["A) throw","B) raise","C) error","D) exception"],"correct":"B) raise","explanation":"raise is used to create exception."},
{"question":"What happens if exception is not handled?","options":["A) Ignored","B) Program crashes","C) Loop runs","D) None"],"correct":"B) Program crashes","explanation":"Unhandled exception stops program."},
{"question":"Can we have multiple except blocks?","options":["A) No","B) Yes","C) Only one","D) Sometimes"],"correct":"B) Yes","explanation":"Multiple exceptions can be handled."},
{"question":"What is finally block used for?","options":["A) Loop","B) Cleanup","C) Error","D) Print"],"correct":"B) Cleanup","explanation":"Used for cleanup operations."},
{"question":"Which is correct syntax?","options":["A) try-except","B) try-catch","C) error-handle","D) catch-finally"],"correct":"A) try-except","explanation":"Python uses try-except."},
{"question":"Can we use try without except?","options":["A) Yes","B) No","C) Only finally","D) Sometimes"],"correct":"C) Only finally","explanation":"try must have except or finally."},
{"question":"Which error occurs when dividing by zero?","options":["A) TypeError","B) ValueError","C) ZeroDivisionError","D) NameError"],"correct":"C) ZeroDivisionError","explanation":"Division by zero error."},
{"question":"Which error occurs for undefined variable?","options":["A) TypeError","B) NameError","C) ValueError","D) IndexError"],"correct":"B) NameError","explanation":"Undefined variable error."},
],

'tamil': [
{"question":"Exception என்றால் என்ன?","options":["A) Loop","B) Runtime error","C) Function","D) Variable"],"correct":"B) Runtime error","explanation":"Execution போது error."},
{"question":"Exception handle செய்ய block?","options":["A) try","B) catch","C) handle","D) error"],"correct":"A) try","explanation":"try block பயன்படுத்தப்படும்."},
{"question":"Exception catch செய்ய?","options":["A) try","B) except","C) finally","D) error"],"correct":"B) except","explanation":"except error handle செய்யும்."},
{"question":"எப்போதும் run ஆகும் block?","options":["A) try","B) except","C) finally","D) error"],"correct":"C) finally","explanation":"finally எப்போதும் run ஆகும்."},
{"question":"Exception raise செய்ய keyword?","options":["A) throw","B) raise","C) error","D) exception"],"correct":"B) raise","explanation":"raise பயன்படுத்தப்படும்."},
{"question":"Exception handle செய்யாவிட்டால்?","options":["A) Ignore","B) Program crash","C) Loop","D) None"],"correct":"B) Program crash","explanation":"Program நிற்கும்."},
{"question":"Multiple except blocks இருக்குமா?","options":["A) இல்லை","B) ஆம்","C) ஒன்று மட்டும்","D) சில நேரம்"],"correct":"B) ஆம்","explanation":"பல exception handle செய்யலாம்."},
{"question":"finally block பயன்பாடு?","options":["A) Loop","B) Cleanup","C) Error","D) Print"],"correct":"B) Cleanup","explanation":"Cleanup operations."},
{"question":"சரியான syntax?","options":["A) try-except","B) try-catch","C) error-handle","D) catch-finally"],"correct":"A) try-except","explanation":"Python-ல் try-except."},
{"question":"try மட்டும் use செய்ய முடியுமா?","options":["A) ஆம்","B) இல்லை","C) finally உடன் மட்டும்","D) சில நேரம்"],"correct":"C) finally உடன் மட்டும்","explanation":"except அல்லது finally வேண்டும்."},
{"question":"Zero divide error?","options":["A) TypeError","B) ValueError","C) ZeroDivisionError","D) NameError"],"correct":"C) ZeroDivisionError","explanation":"0-ஆல் divide செய்தால் வரும்."},
{"question":"Undefined variable error?","options":["A) TypeError","B) NameError","C) ValueError","D) IndexError"],"correct":"B) NameError","explanation":"Variable define செய்யவில்லை."},
],

'tanglish': [
{"question":"Exception na enna?","options":["A) loop","B) runtime error","C) function","D) variable"],"correct":"B) runtime error","explanation":"execution time la error."},
{"question":"Exception handle panna block?","options":["A) try","B) catch","C) handle","D) error"],"correct":"A) try","explanation":"try use pannuvom."},
{"question":"Exception catch panna?","options":["A) try","B) except","C) finally","D) error"],"correct":"B) except","explanation":"except handle pannum."},
{"question":"Always run aagura block?","options":["A) try","B) except","C) finally","D) error"],"correct":"C) finally","explanation":"finally always run."},
{"question":"Exception raise panna keyword?","options":["A) throw","B) raise","C) error","D) exception"],"correct":"B) raise","explanation":"raise use pannuvom."},
{"question":"Handle panna illa na?","options":["A) ignore","B) program crash","C) loop","D) none"],"correct":"B) program crash","explanation":"program stop aagum."},
{"question":"Multiple except use panna mudiyuma?","options":["A) illa","B) mudiyum","C) onnu","D) sometimes"],"correct":"B) mudiyum","explanation":"multiple errors handle pannalam."},
{"question":"finally use enna?","options":["A) loop","B) cleanup","C) error","D) print"],"correct":"B) cleanup","explanation":"cleanup tasks."},
{"question":"Correct syntax?","options":["A) try-except","B) try-catch","C) error-handle","D) catch-finally"],"correct":"A) try-except","explanation":"python la try-except."},
{"question":"try mattum use panna mudiyuma?","options":["A) mudiyum","B) mudiyathu","C) finally oda","D) sometimes"],"correct":"C) finally oda","explanation":"except illa na finally venum."},
{"question":"Zero divide error?","options":["A) TypeError","B) ValueError","C) ZeroDivisionError","D) NameError"],"correct":"C) ZeroDivisionError","explanation":"0 la divide panna."},
{"question":"Undefined variable error?","options":["A) TypeError","B) NameError","C) ValueError","D) IndexError"],"correct":"B) NameError","explanation":"variable define illa."},
],

'hindi': [
{"question":"Exception क्या है?","options":["A) Loop","B) Runtime error","C) Function","D) Variable"],"correct":"B) Runtime error","explanation":"Execution के समय error।"},
{"question":"Exception handle करने का block?","options":["A) try","B) catch","C) handle","D) error"],"correct":"A) try","explanation":"try block उपयोग होता है।"},
{"question":"Exception catch करने का block?","options":["A) try","B) except","C) finally","D) error"],"correct":"B) except","explanation":"except error handle करता है।"},
{"question":"कौन सा block हमेशा चलता है?","options":["A) try","B) except","C) finally","D) error"],"correct":"C) finally","explanation":"finally हमेशा execute होता है।"},
{"question":"Exception raise करने का keyword?","options":["A) throw","B) raise","C) error","D) exception"],"correct":"B) raise","explanation":"raise उपयोग होता है।"},
{"question":"Exception handle नहीं किया तो?","options":["A) ignore","B) program crash","C) loop","D) none"],"correct":"B) program crash","explanation":"Program रुक जाता है।"},
{"question":"Multiple except blocks?","options":["A) नहीं","B) हाँ","C) एक","D) कभी-कभी"],"correct":"B) हाँ","explanation":"Multiple errors handle कर सकते हैं।"},
{"question":"finally block का उपयोग?","options":["A) loop","B) cleanup","C) error","D) print"],"correct":"B) cleanup","explanation":"Cleanup के लिए।"},
{"question":"सही syntax?","options":["A) try-except","B) try-catch","C) error-handle","D) catch-finally"],"correct":"A) try-except","explanation":"Python में try-except।"},
{"question":"try अकेले use कर सकते हैं?","options":["A) हाँ","B) नहीं","C) finally के साथ","D) कभी-कभी"],"correct":"C) finally के साथ","explanation":"except या finally होना चाहिए।"},
{"question":"Zero division error?","options":["A) TypeError","B) ValueError","C) ZeroDivisionError","D) NameError"],"correct":"C) ZeroDivisionError","explanation":"0 से divide करने पर।"},
{"question":"Undefined variable error?","options":["A) TypeError","B) NameError","C) ValueError","D) IndexError"],"correct":"B) NameError","explanation":"Variable define नहीं है।"},
],

'malayalam': [
{"question":"Exception എന്താണ്?","options":["A) Loop","B) Runtime error","C) Function","D) Variable"],"correct":"B) Runtime error","explanation":"Execution സമയത്ത് error."},
{"question":"Exception handle ചെയ്യാൻ block?","options":["A) try","B) catch","C) handle","D) error"],"correct":"A) try","explanation":"try block ഉപയോഗിക്കുന്നു."},
{"question":"Exception catch ചെയ്യാൻ?","options":["A) try","B) except","C) finally","D) error"],"correct":"B) except","explanation":"except handle ചെയ്യുന്നു."},
{"question":"Always run block?","options":["A) try","B) except","C) finally","D) error"],"correct":"C) finally","explanation":"finally എപ്പോഴും run ചെയ്യും."},
{"question":"Exception raise keyword?","options":["A) throw","B) raise","C) error","D) exception"],"correct":"B) raise","explanation":"raise ഉപയോഗിക്കുന്നു."},
{"question":"Handle ചെയ്യാത്താൽ?","options":["A) ignore","B) crash","C) loop","D) none"],"correct":"B) crash","explanation":"Program stop ചെയ്യും."},
{"question":"Multiple except blocks ഉണ്ടോ?","options":["A) ഇല്ല","B) ആണ്","C) ഒന്ന്","D) ചിലപ്പോൾ"],"correct":"B) ആണ്","explanation":"Multiple handle ചെയ്യാം."},
{"question":"finally block ഉപയോഗം?","options":["A) loop","B) cleanup","C) error","D) print"],"correct":"B) cleanup","explanation":"Cleanup വേണ്ടി."},
{"question":"Correct syntax?","options":["A) try-except","B) try-catch","C) error-handle","D) catch-finally"],"correct":"A) try-except","explanation":"Python-ൽ try-except."},
{"question":"try മാത്രം ഉപയോഗിക്കാമോ?","options":["A) ആണ്","B) ഇല്ല","C) finally കൂടെ","D) ചിലപ്പോൾ"],"correct":"C) finally കൂടെ","explanation":"except അല്ലെങ്കിൽ finally വേണം."},
{"question":"Zero divide error?","options":["A) TypeError","B) ValueError","C) ZeroDivisionError","D) NameError"],"correct":"C) ZeroDivisionError","explanation":"0 കൊണ്ട് divide ചെയ്യുമ്പോൾ."},
{"question":"Undefined variable error?","options":["A) TypeError","B) NameError","C) ValueError","D) IndexError"],"correct":"B) NameError","explanation":"Variable define ചെയ്തിട്ടില്ല."},
],

},#exception handling
'OOP': {

'english': [
{"question":"What is a class in Python?","options":["A) Variable","B) Blueprint for objects","C) Function","D) Module"],"correct":"B) Blueprint for objects","explanation":"Class defines structure and behavior of objects."},
{"question":"What is an object?","options":["A) Instance of class","B) Function","C) Loop","D) Module"],"correct":"A) Instance of class","explanation":"Object is an instance created from a class."},
{"question":"Which method is the constructor in Python?","options":["A) __init__","B) __main__","C) __str__","D) __del__"],"correct":"A) __init__","explanation":"__init__ initializes object attributes."},
{"question":"How do you access an object's attribute?","options":["A) object.attribute","B) class.attribute","C) attribute.object","D) object->attribute"],"correct":"A) object.attribute","explanation":"Use dot notation to access attributes."},
{"question":"Which keyword is used for inheritance?","options":["A) extends","B) super","C) class","D) import"],"correct":"B) super","explanation":"super() is used to access parent class methods."},
{"question":"What is encapsulation?","options":["A) Hiding internal details","B) Code repetition","C) Multiple inheritance","D) Looping"],"correct":"A) Hiding internal details","explanation":"Encapsulation protects object data using private/protected attributes."},
{"question":"What is polymorphism?","options":["A) Single class multiple objects","B) Using different types with same interface","C) Hiding data","D) Inheritance"],"correct":"B) Using different types with same interface","explanation":"Polymorphism allows same method name for different classes."},
{"question":"What is abstraction?","options":["A) Hiding complexity","B) Showing all details","C) Using loops","D) Inheriting classes"],"correct":"A) Hiding complexity","explanation":"Abstraction hides internal implementation and shows necessary details."},
{"question":"Which symbol is used for private attributes?","options":["A) __","B) _","C) #","D) $"],"correct":"A) __","explanation":"Double underscore makes attributes private."},
{"question":"What happens when a method is overridden?","options":["A) Parent method is deleted","B) Child method replaces parent","C) Program crashes","D) No effect"],"correct":"B) Child method replaces parent","explanation":"Overriding lets child class provide its own method implementation."},
{"question":"Which is correct syntax for inheritance?","options":["A) class Child(Parent):","B) class Child extends Parent:","C) class Child inherits Parent:","D) class Child -> Parent:"],"correct":"A) class Child(Parent):","explanation":"Python uses class Child(Parent): syntax."},
{"question":"How do you call parent class method inside child?","options":["A) super().method()","B) parent.method()","C) this.method()","D) call.method()"],"correct":"A) super().method()","explanation":"super() calls the parent class method from child."},
],

'tamil': [
{"question":"Python-ல் class என்றால் என்ன?","options":["A) Variable","B) Objects-க்கு blueprint","C) Function","D) Module"],"correct":"B) Objects-க்கு blueprint","explanation":"Class object-களின் structure மற்றும் behavior define செய்கிறது."},
{"question":"Object என்றால் என்ன?","options":["A) Class instance","B) Function","C) Loop","D) Module"],"correct":"A) Class instance","explanation":"Object class-இல் இருந்து உருவாக்கப்பட்ட instance ஆகும்."},
{"question":"Python-ல் constructor method எது?","options":["A) __init__","B) __main__","C) __str__","D) __del__"],"correct":"A) __init__","explanation":"__init__ object attributes-ஐ initialize செய்கிறது."},
{"question":"Object-ன் attribute-ஐ access செய்ய எப்படி?","options":["A) object.attribute","B) class.attribute","C) attribute.object","D) object->attribute"],"correct":"A) object.attribute","explanation":"Dot notation-ஐ பயன்படுத்தி attribute access செய்யலாம்."},
{"question":"Inheritance-க்கு எது பயன்படுத்தப்படுகிறது?","options":["A) extends","B) super","C) class","D) import"],"correct":"B) super","explanation":"super() parent class methods-ஐ access செய்ய பயன்படும்."},
{"question":"Encapsulation என்றால் என்ன?","options":["A) Internal details hide செய்யல்","B) Code repetition","C) Multiple inheritance","D) Looping"],"correct":"A) Internal details hide செய்யல்","explanation":"Private/protected attributes-ஐ பயன்படுத்தி object data-ஐ பாதுகாக்கும்."},
{"question":"Polymorphism என்றால் என்ன?","options":["A) ஒரு class பல objects","B) ஒரே interface-க்கு பல types பயன்படுத்தல்","C) Data hide செய்யல்","D) Inheritance"],"correct":"B) ஒரே interface-க்கு பல types பயன்படுத்தல்","explanation":"Polymorphism பல classes-ல் ஒரே method name-ஐ பயன்படுத்த அனுமதிக்கிறது."},
{"question":"Abstraction என்றால் என்ன?","options":["A) Complexity hide செய்யல்","B) எல்லா details காட்டு","C) Loops பயன்படுத்தல்","D) Classes inherit செய்யல்"],"correct":"A) Complexity hide செய்யல்","explanation":"Abstraction internal implementation-ஐ மறைத்து தேவையான details மட்டுமே காட்டும்."},
{"question":"Private attribute-க்கு எது பயன்படுத்தப்படுகிறது?","options":["A) __","B) _","C) #","D) $"],"correct":"A) __","explanation":"Double underscore attributes-ஐ private ஆக மாற்றும்."},
{"question":"Method override செய்யும்போது என்ன ஆகும்?","options":["A) Parent method delete ஆகும்","B) Child method parent method-ஐ மாற்றும்","C) Program crash ஆகும்","D) எதுவும் இல்லாது"],"correct":"B) Child method parent method-ஐ மாற்றும்","explanation":"Child class தன் implementation-ஐ வழங்கும்."},
{"question":"Inheritance syntax எது சரியானது?","options":["A) class Child(Parent):","B) class Child extends Parent:","C) class Child inherits Parent:","D) class Child -> Parent:"],"correct":"A) class Child(Parent):","explanation":"Python-ல் class Child(Parent): syntax பயன்படுத்தப்படுகிறது."},
{"question":"Parent method-ஐ child-ல் எப்படி call செய்வது?","options":["A) super().method()","B) parent.method()","C) this.method()","D) call.method()"],"correct":"A) super().method()","explanation":"super() parent class-ன் method call செய்ய பயன்படுத்தப்படுகிறது."},
],

'tanglish': [
{"question":"Python-la class enna?","options":["A) Variable","B) Blueprint for objects","C) Function","D) Module"],"correct":"B) Blueprint for objects","explanation":"Class objects structure & behavior define pannum."},
{"question":"Object na enna?","options":["A) Class instance","B) Function","C) Loop","D) Module"],"correct":"A) Class instance","explanation":"Object class-la create panna instance."},
{"question":"Constructor method enna?","options":["A) __init__","B) __main__","C) __str__","D) __del__"],"correct":"A) __init__","explanation":"__init__ object attributes initialize pannum."},
{"question":"Object attribute access panna?","options":["A) object.attribute","B) class.attribute","C) attribute.object","D) object->attribute"],"correct":"A) object.attribute","explanation":"Dot notation use pannitu access pannuvom."},
{"question":"Inheritance-ku keyword enna?","options":["A) extends","B) super","C) class","D) import"],"correct":"B) super","explanation":"super() parent class methods access panna."},
{"question":"Encapsulation enna?","options":["A) Hide internal details","B) Code repetition","C) Multiple inheritance","D) Looping"],"correct":"A) Hide internal details","explanation":"Private/protected attributes use panni protect pannuvom."},
{"question":"Polymorphism enna?","options":["A) Single class multiple objects","B) Different types same interface use pannuvom","C) Hide data","D) Inheritance"],"correct":"B) Different types same interface use pannuvom","explanation":"Same method name different classes-la use pannuvom."},
{"question":"Abstraction enna?","options":["A) Hide complexity","B) Show all details","C) Use loops","D) Inherit classes"],"correct":"A) Hide complexity","explanation":"Internal implementation hide pannitu only necessary details kaattu."},
{"question":"Private attribute symbol enna?","options":["A) __","B) _","C) #","D) $"],"correct":"A) __","explanation":"Double underscore attribute private aagum."},
{"question":"Method override panna enna aagum?","options":["A) Parent method delete","B) Child method parent replace pannum","C) Program crash","D) No effect"],"correct":"B) Child method parent replace pannum","explanation":"Child method override pannum."},
{"question":"Inheritance syntax correct?","options":["A) class Child(Parent):","B) class Child extends Parent:","C) class Child inherits Parent:","D) class Child -> Parent:"],"correct":"A) class Child(Parent):","explanation":"Python-la class Child(Parent): use pannuvom."},
{"question":"Parent method call panna child-la?","options":["A) super().method()","B) parent.method()","C) this.method()","D) call.method()"],"correct":"A) super().method()","explanation":"super() parent method call panna use pannuvom."},
],

'hindi': [
{"question":"Python में class क्या है?","options":["A) Variable","B) Objects का blueprint","C) Function","D) Module"],"correct":"B) Objects का blueprint","explanation":"Class objects की structure और behavior define करती है।"},
{"question":"Object क्या है?","options":["A) Class का instance","B) Function","C) Loop","D) Module"],"correct":"A) Class का instance","explanation":"Object class से बनाया गया instance है।"},
{"question":"Constructor method कौन सा है?","options":["A) __init__","B) __main__","C) __str__","D) __del__"],"correct":"A) __init__","explanation":"__init__ object attributes initialize करता है।"},
{"question":"Object attribute access कैसे करें?","options":["A) object.attribute","B) class.attribute","C) attribute.object","D) object->attribute"],"correct":"A) object.attribute","explanation":"Dot notation से access करते हैं।"},
{"question":"Inheritance के लिए keyword क्या है?","options":["A) extends","B) super","C) class","D) import"],"correct":"B) super","explanation":"super() parent class methods access करने के लिए।"},
{"question":"Encapsulation क्या है?","options":["A) Internal details hide करना","B) Code repetition","C) Multiple inheritance","D) Looping"],"correct":"A) Internal details hide करना","explanation":"Private/protected attributes से data protect होता है।"},
{"question":"Polymorphism क्या है?","options":["A) Single class multiple objects","B) Different types same interface use","C) Hide data","D) Inheritance"],"correct":"B) Different types same interface use","explanation":"Same method name different classes में use कर सकते हैं।"},
{"question":"Abstraction क्या है?","options":["A) Complexity hide करना","B) Show all details","C) Use loops","D) Inherit classes"],"correct":"A) Complexity hide करना","explanation":"Implementation hide करके only necessary details दिखाते हैं।"},
{"question":"Private attribute symbol कौन सा?","options":["A) __","B) _","C) #","D) $"],"correct":"A) __","explanation":"Double underscore से attribute private बनता है।"},
{"question":"Method override होने पर क्या होता है?","options":["A) Parent method delete","B) Child method parent replace करता है","C) Program crash","D) No effect"],"correct":"B) Child method parent replace करता है","explanation":"Child class अपना implementation provide करता है।"},
{"question":"Inheritance syntax correct?","options":["A) class Child(Parent):","B) class Child extends Parent:","C) class Child inherits Parent:","D) class Child -> Parent:"],"correct":"A) class Child(Parent):","explanation":"Python में class Child(Parent): syntax use होता है।"},
{"question":"Parent method call कैसे करें child में?","options":["A) super().method()","B) parent.method()","C) this.method()","D) call.method()"],"correct":"A) super().method()","explanation":"super() parent method call करने के लिए।"},
],

'malayalam': [
{"question":"Python-ൽ class എന്താണ്?","options":["A) Variable","B) Objects-ന് blueprint","C) Function","D) Module"],"correct":"B) Objects-ന് blueprint","explanation":"Class objects-ന്റെ structure & behavior define ചെയ്യുന്നു."},
{"question":"Object എന്താണ്?","options":["A) Class instance","B) Function","C) Loop","D) Module"],"correct":"A) Class instance","explanation":"Object class-ൽ നിന്നും രൂപപ്പെടുത്തിയ instance ആണ്."},
{"question":"Constructor method ഏത്?","options":["A) __init__","B) __main__","C) __str__","D) __del__"],"correct":"A) __init__","explanation":"__init__ object attributes initialize ചെയ്യുന്നു."},
{"question":"Object attribute access എങ്ങനെ?","options":["A) object.attribute","B) class.attribute","C) attribute.object","D) object->attribute"],"correct":"A) object.attribute","explanation":"Dot notation ഉപയോഗിച്ച് access ചെയ്യാം."},
{"question":"Inheritance keyword ഏത്?","options":["A) extends","B) super","C) class","D) import"],"correct":"B) super","explanation":"super() parent class methods access ചെയ്യാൻ."},
{"question":"Encapsulation എന്താണ്?","options":["A) Internal details hide ചെയ്യൽ","B) Code repetition","C) Multiple inheritance","D) Looping"],"correct":"A) Internal details hide ചെയ്യൽ","explanation":"Private/protected attributes ഉപയോഗിച്ച് data protect ചെയ്യുന്നു."},
{"question":"Polymorphism എന്താണ്?","options":["A) Single class multiple objects","B) Different types same interface ഉപയോഗിക്കുക","C) Hide data","D) Inheritance"],"correct":"B) Different types same interface ഉപയോഗിക്കുക","explanation":"Same method name different classes-ൽ ഉപയോഗിക്കാൻ കഴിയും."},
{"question":"Abstraction എന്താണ്?","options":["A) Complexity hide ചെയ്യൽ","B) Show all details","C) Use loops","D) Inherit classes"],"correct":"A) Complexity hide ചെയ്യൽ","explanation":"Implementation hide ചെയ്ത് necessary details മാത്രം കാണിക്കുന്നു."},
{"question":"Private attribute symbol ഏത്?","options":["A) __","B) _","C) #","D) $"],"correct":"A) __","explanation":"Double underscore attribute private ആക്കും."},
{"question":"Method override ആയാൽ എന്ത് സംഭവിക്കും?","options":["A) Parent method delete","B) Child method parent replace ചെയ്യും","C) Program crash","D) No effect"],"correct":"B) Child method parent replace ചെയ്യും","explanation":"Child class തങ്ങളുടെ implementation നൽകും."},
{"question":"Inheritance syntax correct?","options":["A) class Child(Parent):","B) class Child extends Parent:","C) class Child inherits Parent:","D) class Child -> Parent:"],"correct":"A) class Child(Parent):","explanation":"Python-ൽ class Child(Parent): syntax ഉപയോഗിക്കുന്നു."},
{"question":"Parent method child-ൽ call ചെയ്യാൻ?","options":["A) super().method()","B) parent.method()","C) this.method()","D) call.method()"],"correct":"A) super().method()","explanation":"super() parent method call ചെയ്യാൻ ഉപയോഗിക്കുന്നു."},
],

},#oop over
'Modules and Packages': {

'english': [
{"question":"What is a module in Python?","options":["A) File containing Python code","B) Function","C) Loop","D) Variable"],"correct":"A) File containing Python code","explanation":"Module is a .py file with code you can import."},
{"question":"How do you import a module?","options":["A) import module_name","B) include module_name","C) require module_name","D) using module_name"],"correct":"A) import module_name","explanation":"Use import to bring module into your program."},
{"question":"Which keyword imports a specific function from module?","options":["A) import","B) from","C) include","D) require"],"correct":"B) from","explanation":"from module import function is used to import specific items."},
{"question":"What is a package?","options":["A) Directory containing modules","B) Single file","C) Function","D) Variable"],"correct":"A) Directory containing modules","explanation":"Package is a collection of modules organized in directories."},
{"question":"Which file makes a directory a package?","options":["A) __init__.py","B) main.py","C) module.py","D) start.py"],"correct":"A) __init__.py","explanation":"__init__.py marks a directory as a Python package."},
{"question":"How to import a module from a package?","options":["A) import package.module","B) include package.module","C) require package.module","D) using package.module"],"correct":"A) import package.module","explanation":"Use dot notation to import module from package."},
{"question":"Which function shows all functions and variables in a module?","options":["A) dir()","B) help()","C) list()","D) type()"],"correct":"A) dir()","explanation":"dir(module) lists attributes, functions, and classes in the module."},
{"question":"Can you reload a module after editing it?","options":["A) No","B) Yes, using importlib.reload","C) Only in Python 2","D) Only for packages"],"correct":"B) Yes, using importlib.reload","explanation":"importlib.reload(module) reloads a module without restarting program."},
{"question":"How to alias a module during import?","options":["A) import module as alias","B) import module alias","C) from module alias","D) module as alias"],"correct":"A) import module as alias","explanation":"Use as to give a short name to a module."},
{"question":"Can packages contain sub-packages?","options":["A) Yes","B) No","C) Only modules","D) Only functions"],"correct":"A) Yes","explanation":"Packages can have nested sub-packages."},
],

'tamil': [
{"question":"Python-ல் module என்ன?","options":["A) Python code கொண்ட file","B) Function","C) Loop","D) Variable"],"correct":"A) Python code கொண்ட file","explanation":"Module என்பது .py file ஆகும், import செய்யலாம்."},
{"question":"Module import செய்ய எப்படி?","options":["A) import module_name","B) include module_name","C) require module_name","D) using module_name"],"correct":"A) import module_name","explanation":"Import மூலம் module-ஐ bring செய்யலாம்."},
{"question":"Module-இலிருந்து specific function import செய்ய keyword?","options":["A) import","B) from","C) include","D) require"],"correct":"B) from","explanation":"from module import function use செய்யலாம்."},
{"question":"Package என்ன?","options":["A) Modules-களை கொண்ட directory","B) Single file","C) Function","D) Variable"],"correct":"A) Modules-களை கொண்ட directory","explanation":"Package என்பது modules directory ஆகும்."},
{"question":"Directory-ஐ package ஆக்குவது எது?","options":["A) __init__.py","B) main.py","C) module.py","D) start.py"],"correct":"A) __init__.py","explanation":"__init__.py directory-ஐ package ஆக்கும்."},
{"question":"Package-இலிருந்து module import செய்ய எப்படி?","options":["A) import package.module","B) include package.module","C) require package.module","D) using package.module"],"correct":"A) import package.module","explanation":"Dot notation மூலம் import செய்யலாம்."},
{"question":"Module-இலுள்ள function மற்றும் variables காணும் function?","options":["A) dir()","B) help()","C) list()","D) type()"],"correct":"A) dir()","explanation":"dir(module) lists attributes, functions, classes."},
{"question":"Module edit செய்த பிறகு reload செய்ய முடியுமா?","options":["A) இல்லை","B) ஆம், importlib.reload-ஐ பயன்படுத்தி","C) Python 2-ல் மட்டும்","D) Packages-க்கு மட்டும்"],"correct":"B) ஆம், importlib.reload-ஐ பயன்படுத்தி","explanation":"importlib.reload(module) module-ஐ reload செய்யும்."},
{"question":"Module-க்கு alias தர keyword?","options":["A) import module as alias","B) import module alias","C) from module alias","D) module as alias"],"correct":"A) import module as alias","explanation":"as மூலம் short name-ஐ தரலாம்."},
{"question":"Packages-க்கு sub-packages இருக்க முடியுமா?","options":["A) ஆம்","B) இல்லை","C) Modules மட்டும்","D) Functions மட்டும்"],"correct":"A) ஆம்","explanation":"Packages nested sub-packages-ஐ கொண்டிருக்கும்."},
],

'tanglish': [
{"question":"Python-la module enna?","options":["A) Python code file","B) Function","C) Loop","D) Variable"],"correct":"A) Python code file","explanation":"Module is .py file, import pannalaam."},
{"question":"Module import panna eppadi?","options":["A) import module_name","B) include module_name","C) require module_name","D) using module_name"],"correct":"A) import module_name","explanation":"Import use panni module program-la bring pannalaam."},
{"question":"Module-la irukra specific function import panna keyword?","options":["A) import","B) from","C) include","D) require"],"correct":"B) from","explanation":"from module import function use pannuvom."},
{"question":"Package enna?","options":["A) Directory with modules","B) Single file","C) Function","D) Variable"],"correct":"A) Directory with modules","explanation":"Package modules collect pannra directory."},
{"question":"Directory-ai package-aa make panna file?","options":["A) __init__.py","B) main.py","C) module.py","D) start.py"],"correct":"A) __init__.py","explanation":"__init__.py directory-ai package-aa mark pannum."},
{"question":"Package-la irukra module import panna?","options":["A) import package.module","B) include package.module","C) require package.module","D) using package.module"],"correct":"A) import package.module","explanation":"Dot notation use panni import pannuvom."},
{"question":"Module-la functions & variables paaka function?","options":["A) dir()","B) help()","C) list()","D) type()"],"correct":"A) dir()","explanation":"dir(module) lists functions, attributes, classes."},
{"question":"Module edit pannitu reload panna mudiyuma?","options":["A) illa","B) importlib.reload use pannitu","C) Python2-la mattum","D) Packages-kk mattum"],"correct":"B) importlib.reload use pannitu","explanation":"importlib.reload(module) reload pannum."},
{"question":"Module-ku alias provide panna?","options":["A) import module as alias","B) import module alias","C) from module alias","D) module as alias"],"correct":"A) import module as alias","explanation":"as use pannitu short name kudukkalaam."},
{"question":"Package-ku sub-packages irukka mudiyuma?","options":["A) mudiyum","B) mudiyathu","C) modules mattum","D) functions mattum"],"correct":"A) mudiyum","explanation":"Packages nested sub-packages contain pannum."},
],

'hindi': [
{"question":"Python में module क्या है?","options":["A) Python code file","B) Function","C) Loop","D) Variable"],"correct":"A) Python code file","explanation":"Module .py file है, import किया जा सकता है।"},
{"question":"Module import कैसे करें?","options":["A) import module_name","B) include module_name","C) require module_name","D) using module_name"],"correct":"A) import module_name","explanation":"Import से module program में आएगा।"},
{"question":"Module से specific function import करने का keyword?","options":["A) import","B) from","C) include","D) require"],"correct":"B) from","explanation":"from module import function use किया जाता है।"},
{"question":"Package क्या है?","options":["A) Modules वाला directory","B) Single file","C) Function","D) Variable"],"correct":"A) Modules वाला directory","explanation":"Package modules का collection directory है।"},
{"question":"Directory को package बनाने वाला file?","options":["A) __init__.py","B) main.py","C) module.py","D) start.py"],"correct":"A) __init__.py","explanation":"__init__.py directory को package mark करता है।"},
{"question":"Package से module import कैसे करें?","options":["A) import package.module","B) include package.module","C) require package.module","D) using package.module"],"correct":"A) import package.module","explanation":"Dot notation use करके import किया जाता है।"},
{"question":"Module के functions और variables देखने के लिए function?","options":["A) dir()","B) help()","C) list()","D) type()"],"correct":"A) dir()","explanation":"dir(module) lists functions, attributes, classes."},
{"question":"Module edit करने के बाद reload कर सकते हैं?","options":["A) नहीं","B) हाँ, importlib.reload use करके","C) Python2 में ही","D) Packages में ही"],"correct":"B) हाँ, importlib.reload use करके","explanation":"importlib.reload(module) reload करता है।"},
{"question":"Module को alias देने का तरीका?","options":["A) import module as alias","B) import module alias","C) from module alias","D) module as alias"],"correct":"A) import module as alias","explanation":"as keyword से short name दिया जा सकता है।"},
{"question":"Package में sub-packages हो सकते हैं?","options":["A) हाँ","B) नहीं","C) केवल modules","D) केवल functions"],"correct":"A) हाँ","explanation":"Packages nested sub-packages contain कर सकते हैं।"},
],

'malayalam': [
{"question":"Python-ൽ module എന്താണ്?","options":["A) Python code file","B) Function","C) Loop","D) Variable"],"correct":"A) Python code file","explanation":"Module .py file ആണ്, import ചെയ്യാം."},
{"question":"Module import എങ്ങനെ ചെയ്യാം?","options":["A) import module_name","B) include module_name","C) require module_name","D) using module_name"],"correct":"A) import module_name","explanation":"Import ഉപയോഗിച്ച് module program-ൽ bring ചെയ്യാം."},
{"question":"Module-ൽ നിന്ന് specific function import ചെയ്യാൻ keyword?","options":["A) import","B) from","C) include","D) require"],"correct":"B) from","explanation":"from module import function ഉപയോഗിക്കുന്നു."},
{"question":"Package എന്താണ്?","options":["A) Modules ഉള്ള directory","B) Single file","C) Function","D) Variable"],"correct":"A) Modules ഉള്ള directory","explanation":"Package modules-ന്റെ collection directory ആണ്."},
{"question":"Directory package ആകാൻ ഉപയോഗിക്കുന്ന ഫയൽ?","options":["A) __init__.py","B) main.py","C) module.py","D) start.py"],"correct":"A) __init__.py","explanation":"__init__.py directory-നെ package ആക്കുന്നു."},
{"question":"Package-ൽ നിന്ന് module import എങ്ങനെ?","options":["A) import package.module","B) include package.module","C) require package.module","D) using package.module"],"correct":"A) import package.module","explanation":"Dot notation ഉപയോഗിച്ച് import ചെയ്യാം."},
{"question":"Module-ൽ functions & variables കാണാൻ function?","options":["A) dir()","B) help()","C) list()","D) type()"],"correct":"A) dir()","explanation":"dir(module) lists functions, attributes, classes."},
{"question":"Module edit ചെയ്ത് reload ചെയ്യാമോ?","options":["A) ഇല്ല","B) importlib.reload ഉപയോഗിച്ച്","C) Python2-ൽ മാത്രം","D) Packages-ൽ മാത്രം"],"correct":"B) importlib.reload ഉപയോഗിച്ച്","explanation":"importlib.reload(module) reload ചെയ്യും."},
{"question":"Module-യ്ക്ക് alias നൽകാൻ?","options":["A) import module as alias","B) import module alias","C) from module alias","D) module as alias"],"correct":"A) import module as alias","explanation":"as ഉപയോഗിച്ച് short name നൽകാം."},
{"question":"Package-ൽ sub-packages ഉണ്ടാകാമോ?","options":["A) ഉണ്ടാകാം","B) ഇല്ല","C) modules മാത്രം","D) functions മാത്രം"],"correct":"A) ഉണ്ടാകാം","explanation":"Packages nested sub-packages include ചെയ്യാം."},
],

}

},  # end python topics dict

# ─────────────────── JAVA ──────────────────────────────────────
'java': {
'Introduction to Java': {
'english': [
  {"question":"Who created Java?","options":["A) Guido van Rossum","B) James Gosling","C) Dennis Ritchie","D) Bjarne Stroustrup"],"correct":"B) James Gosling","explanation":"Java was created by James Gosling at Sun Microsystems in 1995."},
  {"question":"Java's motto is?","options":["A) Fast and Furious","B) Write Once Run Anywhere","C) Code and Deploy","D) Simple and Slow"],"correct":"B) Write Once Run Anywhere","explanation":"Java bytecode runs on any JVM."},
  {"question":"What does JVM stand for?","options":["A) Java Virtual Memory","B) Java Variable Method","C) Java Virtual Machine","D) Java Version Manager"],"correct":"C) Java Virtual Machine","explanation":"JVM runs Java bytecode on any platform."},
  {"question":"Java file extension?","options":["A) .py","B) .cpp","C) .java","D) .js"],"correct":"C) .java","explanation":"Java source files use .java extension."},
  {"question":"Java entry point method?","options":["A) start()","B) begin()","C) main()","D) run()"],"correct":"C) main()","explanation":"public static void main(String[] args) is the entry point."},
  {"question":"How do you print in Java?","options":["A) print()","B) console.log()","C) echo()","D) System.out.println()"],"correct":"D) System.out.println()","explanation":"System.out.println() prints output in Java."},
  {"question":"Which keyword creates objects in Java?","options":["A) create","B) object","C) make","D) new"],"correct":"D) new","explanation":"new allocates memory and creates object."},
  {"question":"Java is which type of language?","options":["A) Interpreted only","B) Compiled only","C) Both compiled and interpreted","D) Assembly"],"correct":"C) Both compiled and interpreted","explanation":"Java compiles to bytecode, then JVM interprets it."},
  {"question":"What year was Java released?","options":["A) 1991","B) 1995","C) 2000","D) 2005"],"correct":"B) 1995","explanation":"Java was released in 1995 by Sun Microsystems."},
  {"question":"Java is used for?","options":["A) Only web apps","B) Only mobile apps","C) Android, enterprise, web","D) Only desktop apps"],"correct":"C) Android, enterprise, web","explanation":"Java is used broadly across platforms."},
  {"question":"Which company created Java?","options":["A) Google","B) Microsoft","C) Apple","D) Sun Microsystems"],"correct":"D) Sun Microsystems","explanation":"Java was created at Sun Microsystems."},
  {"question":"Java programs are compiled into?","options":["A) Machine code","B) Python code","C) Bytecode","D) Assembly"],"correct":"C) Bytecode","explanation":"Java source is compiled to bytecode (.class files)."},
],
'tamil': [
  {"question":"Java-ஐ உருவாக்கியவர் யார்?","options":["A) Guido van Rossum","B) James Gosling","C) Dennis Ritchie","D) Bjarne Stroustrup"],"correct":"B) James Gosling","explanation":"Java-ஐ James Gosling 1995-ல் உருவாக்கினார்."},
  {"question":"Java-இன் motto என்ன?","options":["A) Fast and Furious","B) Write Once Run Anywhere","C) Code and Deploy","D) Simple and Slow"],"correct":"B) Write Once Run Anywhere","explanation":"Java bytecode எந்த JVM-லும் run ஆகும்."},
  {"question":"JVM என்றால் என்ன?","options":["A) Java Virtual Memory","B) Java Variable Method","C) Java Virtual Machine","D) Java Version Manager"],"correct":"C) Java Virtual Machine","explanation":"JVM Java bytecode-ஐ run செய்யும்."},
  {"question":"Java file extension?","options":["A) .py","B) .cpp","C) .java","D) .js"],"correct":"C) .java","explanation":"Java source files .java extension பயன்படுத்துகின்றன."},
  {"question":"Java entry point method?","options":["A) start()","B) begin()","C) main()","D) run()"],"correct":"C) main()","explanation":"public static void main(String[] args) entry point ஆகும்."},
  {"question":"Java-ல் print செய்ய?","options":["A) print()","B) console.log()","C) echo()","D) System.out.println()"],"correct":"D) System.out.println()","explanation":"System.out.println() Java-ல் output print செய்யும்."},
  {"question":"Java-ல் objects create செய்ய எந்த keyword?","options":["A) create","B) object","C) make","D) new"],"correct":"D) new","explanation":"new memory allocate செய்து object create செய்யும்."},
  {"question":"Java எந்த வகையான மொழி?","options":["A) Interpreted மட்டும்","B) Compiled மட்டும்","C) Compiled மற்றும் Interpreted","D) Assembly"],"correct":"C) Compiled மற்றும் Interpreted","explanation":"Java bytecode-ஆக compile ஆகி JVM interpret செய்யும்."},
  {"question":"Java எந்த ஆண்டு வெளியானது?","options":["A) 1991","B) 1995","C) 2000","D) 2005"],"correct":"B) 1995","explanation":"Java 1995-ல் Sun Microsystems வெளியிட்டது."},
  {"question":"Java எதற்கு பயன்படுகிறது?","options":["A) Web மட்டும்","B) Mobile மட்டும்","C) Android, enterprise, web","D) Desktop மட்டும்"],"correct":"C) Android, enterprise, web","explanation":"Java பல platforms-ல் பயன்படுகிறது."},
  {"question":"Java-ஐ எந்த company உருவாக்கியது?","options":["A) Google","B) Microsoft","C) Apple","D) Sun Microsystems"],"correct":"D) Sun Microsystems","explanation":"Java Sun Microsystems-ல் உருவாக்கப்பட்டது."},
  {"question":"Java programs எதாக compile ஆகின்றன?","options":["A) Machine code","B) Python code","C) Bytecode","D) Assembly"],"correct":"C) Bytecode","explanation":"Java source .class bytecode-ஆக compile ஆகும்."},
],
'tanglish': [
  {"question":"Java-a create pannathu yaar?","options":["A) Guido van Rossum","B) James Gosling","C) Dennis Ritchie","D) Bjarne Stroustrup"],"correct":"B) James Gosling","explanation":"Java-a James Gosling 1995-la create pannaar."},
  {"question":"Java-oda motto enna?","options":["A) Fast and Furious","B) Write Once Run Anywhere","C) Code and Deploy","D) Simple and Slow"],"correct":"B) Write Once Run Anywhere","explanation":"Java bytecode yedha JVM-lum run aagum."},
  {"question":"JVM enna?","options":["A) Java Virtual Memory","B) Java Variable Method","C) Java Virtual Machine","D) Java Version Manager"],"correct":"C) Java Virtual Machine","explanation":"JVM Java bytecode-a run pannum."},
  {"question":"Java file extension?","options":["A) .py","B) .cpp","C) .java","D) .js"],"correct":"C) .java","explanation":"Java source files .java use pannum."},
  {"question":"Java entry point method?","options":["A) start()","B) begin()","C) main()","D) run()"],"correct":"C) main()","explanation":"public static void main(String[] args) entry point aagum."},
  {"question":"Java-la print panna?","options":["A) print()","B) console.log()","C) echo()","D) System.out.println()"],"correct":"D) System.out.println()","explanation":"System.out.println() Java-la output print pannum."},
  {"question":"Java-la objects create panna ethu keyword?","options":["A) create","B) object","C) make","D) new"],"correct":"D) new","explanation":"new memory allocate panni object create pannum."},
  {"question":"Java ethu type language?","options":["A) Interpreted mattum","B) Compiled mattum","C) Compiled-um Interpreted-um","D) Assembly"],"correct":"C) Compiled-um Interpreted-um","explanation":"Java bytecode-a compile aagi JVM interpret pannum."},
  {"question":"Java ethu varusham release aacchu?","options":["A) 1991","B) 1995","C) 2000","D) 2005"],"correct":"B) 1995","explanation":"Java 1995-la Sun Microsystems release pannatu."},
  {"question":"Java endhatharku use aagum?","options":["A) Web mattum","B) Mobile mattum","C) Android, enterprise, web","D) Desktop mattum"],"correct":"C) Android, enterprise, web","explanation":"Java pala platforms-la use aagum."},
  {"question":"Java-a ethu company create pannatu?","options":["A) Google","B) Microsoft","C) Apple","D) Sun Microsystems"],"correct":"D) Sun Microsystems","explanation":"Java Sun Microsystems-la create aacchu."},
  {"question":"Java programs ethaaga compile aagum?","options":["A) Machine code","B) Python code","C) Bytecode","D) Assembly"],"correct":"C) Bytecode","explanation":"Java source .class bytecode-a compile aagum."},
],
'hindi': [
  {"question":"Java किसने बनाया?","options":["A) Guido van Rossum","B) James Gosling","C) Dennis Ritchie","D) Bjarne Stroustrup"],"correct":"B) James Gosling","explanation":"Java को James Gosling ने 1995 में बनाया।"},
  {"question":"Java का motto?","options":["A) Fast and Furious","B) Write Once Run Anywhere","C) Code and Deploy","D) Simple and Slow"],"correct":"B) Write Once Run Anywhere","explanation":"Java bytecode किसी भी JVM पर चलता है।"},
  {"question":"JVM का मतलब?","options":["A) Java Virtual Memory","B) Java Variable Method","C) Java Virtual Machine","D) Java Version Manager"],"correct":"C) Java Virtual Machine","explanation":"JVM Java bytecode चलाता है।"},
  {"question":"Java file extension?","options":["A) .py","B) .cpp","C) .java","D) .js"],"correct":"C) .java","explanation":"Java source files .java उपयोग करती हैं।"},
  {"question":"Java entry point method?","options":["A) start()","B) begin()","C) main()","D) run()"],"correct":"C) main()","explanation":"public static void main(String[] args) entry point है।"},
  {"question":"Java में print कैसे करें?","options":["A) print()","B) console.log()","C) echo()","D) System.out.println()"],"correct":"D) System.out.println()","explanation":"System.out.println() Java में output print करता है।"},
  {"question":"Java में objects बनाने का keyword?","options":["A) create","B) object","C) make","D) new"],"correct":"D) new","explanation":"new memory allocate करके object बनाता है।"},
  {"question":"Java किस प्रकार की भाषा है?","options":["A) सिर्फ Interpreted","B) सिर्फ Compiled","C) Compiled और Interpreted दोनों","D) Assembly"],"correct":"C) Compiled और Interpreted दोनों","explanation":"Java bytecode में compile होती है, JVM interpret करता है।"},
  {"question":"Java कब release हुई?","options":["A) 1991","B) 1995","C) 2000","D) 2005"],"correct":"B) 1995","explanation":"Java 1995 में Sun Microsystems ने release किया।"},
  {"question":"Java किसके लिए उपयोग होती है?","options":["A) सिर्फ web","B) सिर्फ mobile","C) Android, enterprise, web","D) सिर्फ desktop"],"correct":"C) Android, enterprise, web","explanation":"Java कई platforms पर उपयोग होती है।"},
  {"question":"Java किस company ने बनाई?","options":["A) Google","B) Microsoft","C) Apple","D) Sun Microsystems"],"correct":"D) Sun Microsystems","explanation":"Java Sun Microsystems में बनी।"},
  {"question":"Java programs किसमें compile होते हैं?","options":["A) Machine code","B) Python code","C) Bytecode","D) Assembly"],"correct":"C) Bytecode","explanation":"Java source .class bytecode में compile होती है।"},
],
'malayalam': [
  {"question":"Java ആരാണ് ഉണ്ടാക്കിയത്?","options":["A) Guido van Rossum","B) James Gosling","C) Dennis Ritchie","D) Bjarne Stroustrup"],"correct":"B) James Gosling","explanation":"Java James Gosling 1995-ൽ ഉണ്ടാക്കി."},
  {"question":"Java-ന്റെ motto?","options":["A) Fast and Furious","B) Write Once Run Anywhere","C) Code and Deploy","D) Simple and Slow"],"correct":"B) Write Once Run Anywhere","explanation":"Java bytecode ഏത് JVM-ലും run ആകും."},
  {"question":"JVM എന്നാൽ?","options":["A) Java Virtual Memory","B) Java Variable Method","C) Java Virtual Machine","D) Java Version Manager"],"correct":"C) Java Virtual Machine","explanation":"JVM Java bytecode run ചെയ്യുന്നു."},
  {"question":"Java file extension?","options":["A) .py","B) .cpp","C) .java","D) .js"],"correct":"C) .java","explanation":"Java source files .java extension ഉപയോഗിക്കുന്നു."},
  {"question":"Java entry point method?","options":["A) start()","B) begin()","C) main()","D) run()"],"correct":"C) main()","explanation":"public static void main(String[] args) entry point ആണ്."},
  {"question":"Java-ൽ print ചെയ്യാൻ?","options":["A) print()","B) console.log()","C) echo()","D) System.out.println()"],"correct":"D) System.out.println()","explanation":"System.out.println() Java-ൽ output print ചെയ്യുന്നു."},
  {"question":"Java-ൽ objects ഉണ്ടാക്കാൻ ഏത് keyword?","options":["A) create","B) object","C) make","D) new"],"correct":"D) new","explanation":"new memory allocate ചെയ്ത് object ഉണ്ടാക്കുന്നു."},
  {"question":"Java ഏത് തരം ഭാഷ?","options":["A) Interpreted മാത്രം","B) Compiled മാത്രം","C) Compiled-ഉം Interpreted-ഉം","D) Assembly"],"correct":"C) Compiled-ഉം Interpreted-ഉം","explanation":"Java bytecode ആയി compile ആകുന്നു, JVM interpret ചെയ്യുന്നു."},
  {"question":"Java എത്ര വർഷം release ആയി?","options":["A) 1991","B) 1995","C) 2000","D) 2005"],"correct":"B) 1995","explanation":"Java 1995-ൽ Sun Microsystems release ചെയ്തു."},
  {"question":"Java എന്തിന് ഉപയോഗിക്കുന്നു?","options":["A) Web മാത്രം","B) Mobile മാത്രം","C) Android, enterprise, web","D) Desktop മാത്രം"],"correct":"C) Android, enterprise, web","explanation":"Java പല platforms-ൽ ഉപയോഗിക്കുന്നു."},
  {"question":"Java ഏത് company ഉണ്ടാക്കി?","options":["A) Google","B) Microsoft","C) Apple","D) Sun Microsystems"],"correct":"D) Sun Microsystems","explanation":"Java Sun Microsystems-ൽ ഉണ്ടാക്കി."},
  {"question":"Java programs എന്തിൽ compile ആകുന്നു?","options":["A) Machine code","B) Python code","C) Bytecode","D) Assembly"],"correct":"C) Bytecode","explanation":"Java source .class bytecode ആയി compile ആകുന്നു."},
],
}, #intro over

'Data Types and Variables': {

'english': [
{"question":"What is a primitive datatype in Java?","options":["A) Object","B) int, float, char","C) Class","D) Interface"],"correct":"B) int, float, char","explanation":"Primitive datatypes are basic types like int, float, char, boolean, etc."},
{"question":"Which of these is not a primitive datatype?","options":["A) int","B) String","C) boolean","D) double"],"correct":"B) String","explanation":"String is a class, not a primitive datatype."},
{"question":"Default value of int in Java?","options":["A) 0","B) null","C) 1","D) Undefined"],"correct":"A) 0","explanation":"Default value of numeric primitives is 0."},
{"question":"Default value of boolean in Java?","options":["A) true","B) false","C) 0","D) null"],"correct":"B) false","explanation":"Default value of boolean is false."},
{"question":"Which datatype is used for decimal numbers?","options":["A) int","B) float/double","C) char","D) boolean"],"correct":"B) float/double","explanation":"float and double store decimal numbers."},
{"question":"What is a variable in Java?","options":["A) Storage for data","B) Function","C) Loop","D) Class"],"correct":"A) Storage for data","explanation":"Variable stores values in memory."},
{"question":"Which keyword is used to declare a constant?","options":["A) final","B) const","C) static","D) immutable"],"correct":"A) final","explanation":"final makes a variable constant."},
{"question":"Which of these is a valid variable name?","options":["A) 1var","B) var_1","C) var-1","D) @var"],"correct":"B) var_1","explanation":"Variable names cannot start with digits or contain special symbols except _."},
{"question":"Can variable names be same as keywords?","options":["A) Yes","B) No","C) Sometimes","D) Only static"],"correct":"B) No","explanation":"Keywords are reserved and cannot be used as variable names."},
{"question":"What is the size of int datatype in Java?","options":["A) 2 bytes","B) 4 bytes","C) 8 bytes","D) Depends on OS"],"correct":"B) 4 bytes","explanation":"int is 4 bytes in Java."},
],

'tamil': [
{"question":"Java-ல் primitive datatype என்ன?","options":["A) Object","B) int, float, char","C) Class","D) Interface"],"correct":"B) int, float, char","explanation":"Primitive datatype என்பது basic types (int, float, char, boolean) ஆகும்."},
{"question":"Primitive datatype அல்லாதது எது?","options":["A) int","B) String","C) boolean","D) double"],"correct":"B) String","explanation":"String class ஆகும், primitive datatype இல்லை."},
{"question":"int-இன் default value என்ன?","options":["A) 0","B) null","C) 1","D) Undefined"],"correct":"A) 0","explanation":"Numeric primitives-இன் default value 0."},
{"question":"boolean-இன் default value என்ன?","options":["A) true","B) false","C) 0","D) null"],"correct":"B) false","explanation":"boolean-இன் default value false."},
{"question":"Decimal numbers-க்கு எந்த datatype பயன்படுத்தப்படுகிறது?","options":["A) int","B) float/double","C) char","D) boolean"],"correct":"B) float/double","explanation":"float மற்றும் double decimal numbers store செய்யும்."},
{"question":"Java-ல் variable என்ன?","options":["A) Data சேமிக்கும் storage","B) Function","C) Loop","D) Class"],"correct":"A) Data சேமிக்கும் storage","explanation":"Variable memory-ல் values store செய்யும்."},
{"question":"Constant declare செய்ய எந்த keyword?","options":["A) final","B) const","C) static","D) immutable"],"correct":"A) final","explanation":"final மூலம் variable constant ஆகும்."},
{"question":"Valid variable name எது?","options":["A) 1var","B) var_1","C) var-1","D) @var"],"correct":"B) var_1","explanation":"Variable name digits-ல் தொடங்க கூடாது, special symbols _ தவிர இல்லை."},
{"question":"Variable name keyword-க்கு சமமானதாக இருக்க முடியுமா?","options":["A) ஆம்","B) இல்லை","C) சில நேரம்","D) only static"],"correct":"B) இல்லை","explanation":"Keywords reserved, variable names ஆக பயன்படுத்த முடியாது."},
{"question":"int datatype-இன் size என்ன?","options":["A) 2 bytes","B) 4 bytes","C) 8 bytes","D) OS-க்கு உட்பட்டது"],"correct":"B) 4 bytes","explanation":"Java-ல் int 4 bytes."},
],

'tanglish': [
{"question":"Java-la primitive datatype enna?","options":["A) Object","B) int, float, char","C) Class","D) Interface"],"correct":"B) int, float, char","explanation":"Primitive types int, float, char, boolean, etc."},
{"question":"Primitive datatype alla edhu?","options":["A) int","B) String","C) boolean","D) double"],"correct":"B) String","explanation":"String class, primitive alla."},
{"question":"int-oda default value enna?","options":["A) 0","B) null","C) 1","D) Undefined"],"correct":"A) 0","explanation":"Numeric primitives-oda default 0."},
{"question":"boolean-oda default value enna?","options":["A) true","B) false","C) 0","D) null"],"correct":"B) false","explanation":"boolean default false."},
{"question":"Decimal numbers-kku datatype enna?","options":["A) int","B) float/double","C) char","D) boolean"],"correct":"B) float/double","explanation":"float & double decimal store pannum."},
{"question":"Java-la variable enna?","options":["A) Data storage","B) Function","C) Loop","D) Class"],"correct":"A) Data storage","explanation":"Variable memory-la value store pannum."},
{"question":"Constant declare panna keyword?","options":["A) final","B) const","C) static","D) immutable"],"correct":"A) final","explanation":"final constant variable-aakum."},
{"question":"Valid variable name edhu?","options":["A) 1var","B) var_1","C) var-1","D) @var"],"correct":"B) var_1","explanation":"Digits start aagatha, _ use panna mudiyum."},
{"question":"Variable name keyword-oda same aaguma?","options":["A) Yes","B) No","C) Sometimes","D) Only static"],"correct":"B) No","explanation":"Keywords reserved, use panna mudiyathu."},
{"question":"int datatype size enna?","options":["A) 2 bytes","B) 4 bytes","C) 8 bytes","D) Depends on OS"],"correct":"B) 4 bytes","explanation":"Java-la int 4 bytes."},
],

'hindi': [
{"question":"Java में primitive datatype क्या है?","options":["A) Object","B) int, float, char","C) Class","D) Interface"],"correct":"B) int, float, char","explanation":"Primitive types basic types जैसे int, float, char, boolean।"},
{"question":"Primitive datatype नहीं है?","options":["A) int","B) String","C) boolean","D) double"],"correct":"B) String","explanation":"String class है, primitive नहीं।"},
{"question":"int का default value क्या है?","options":["A) 0","B) null","C) 1","D) Undefined"],"correct":"A) 0","explanation":"Numeric primitive default 0।"},
{"question":"boolean का default value?","options":["A) true","B) false","C) 0","D) null"],"correct":"B) false","explanation":"boolean default false।"},
{"question":"Decimal numbers के लिए datatype?","options":["A) int","B) float/double","C) char","D) boolean"],"correct":"B) float/double","explanation":"float और double decimal numbers store करते हैं।"},
{"question":"Java में variable क्या है?","options":["A) Data storage","B) Function","C) Loop","D) Class"],"correct":"A) Data storage","explanation":"Variable memory में value store करता है।"},
{"question":"Constant declare करने का keyword?","options":["A) final","B) const","C) static","D) immutable"],"correct":"A) final","explanation":"final variable को constant बनाता है।"},
{"question":"Valid variable name कौन सा है?","options":["A) 1var","B) var_1","C) var-1","D) @var"],"correct":"B) var_1","explanation":"Variable name digit से शुरू नहीं होना चाहिए, special symbols _ छोड़कर नहीं।"},
{"question":"Variable name keyword के समान हो सकता है?","options":["A) हाँ","B) नहीं","C) कभी-कभी","D) Only static"],"correct":"B) नहीं","explanation":"Keywords reserved हैं।"},
{"question":"int datatype का size?","options":["A) 2 bytes","B) 4 bytes","C) 8 bytes","D) OS पर निर्भर"],"correct":"B) 4 bytes","explanation":"Java में int 4 bytes।"},
],

'malayalam': [
{"question":"Java-ൽ primitive datatype എന്താണ്?","options":["A) Object","B) int, float, char","C) Class","D) Interface"],"correct":"B) int, float, char","explanation":"Primitive types int, float, char, boolean ആണ്."},
{"question":"Primitive datatype അല്ലാത്തത്?","options":["A) int","B) String","C) boolean","D) double"],"correct":"B) String","explanation":"String class ആണ്, primitive അല്ല."},
{"question":"int-ന്റെ default value?","options":["A) 0","B) null","C) 1","D) Undefined"],"correct":"A) 0","explanation":"Numeric primitive-ന്റെ default 0."},
{"question":"boolean-ന്റെ default value?","options":["A) true","B) false","C) 0","D) null"],"correct":"B) false","explanation":"boolean-ന്റെ default false."},
{"question":"Decimal numbers-ന് datatype ഏത്?","options":["A) int","B) float/double","C) char","D) boolean"],"correct":"B) float/double","explanation":"float & double decimal numbers store ചെയ്യുന്നു."},
{"question":"Java-ൽ variable എന്താണ്?","options":["A) Data storage","B) Function","C) Loop","D) Class"],"correct":"A) Data storage","explanation":"Variable memory-ൽ value store ചെയ്യുന്നു."},
{"question":"Constant declare ചെയ്യാൻ keyword?","options":["A) final","B) const","C) static","D) immutable"],"correct":"A) final","explanation":"final variable constant ആക്കുന്നു."},
{"question":"Valid variable name ഏത്?","options":["A) 1var","B) var_1","C) var-1","D) @var"],"correct":"B) var_1","explanation":"Digits-ൽ തുടങ്ങരുത്, _ മാത്രം allowed."},
{"question":"Variable name keyword-ന്റെ പോലെ ആകാമോ?","options":["A) ഇല്ലാ","B) ആണ്","C) ചിലപ്പോൾ","D) Only static"],"correct":"A) ഇല്ലാ","explanation":"Keywords reserved ആണ്."},
{"question":"int datatype size?","options":["A) 2 bytes","B) 4 bytes","C) 8 bytes","D) OS-നനുസരിച്ച്"],"correct":"B) 4 bytes","explanation":"Java-ൽ int 4 bytes."},
],

},#datatype over

'Operators': {

'english': [
{"question":"Which operator is used for addition?","options":["A) +","B) -","C) *","D) /"],"correct":"A) +","explanation":"The + operator is used for addition."},
{"question":"Which operator is used for comparison of equality?","options":["A) =","B) ==","C) !=","D) <"],"correct":"B) ==","explanation":"== checks equality of two values."},
{"question":"Which is the modulus operator?","options":["A) %","B) /","C) *","D) &"],"correct":"A) %","explanation":"% gives remainder after division."},
{"question":"Which operator is used for logical AND?","options":["A) &&","B) ||","C) &","D) |"],"correct":"A) &&","explanation":"&& is logical AND, & is bitwise AND."},
{"question":"Which operator is used for logical OR?","options":["A) &&","B) ||","C) &","D) |"],"correct":"B) ||","explanation":"|| is logical OR."},
{"question":"Increment operator in Java?","options":["A) ++","B) --","C) += ","D) -="],"correct":"A) ++","explanation":"++ increases value by 1."},
{"question":"Decrement operator in Java?","options":["A) ++","B) --","C) += ","D) -="],"correct":"B) --","explanation":"-- decreases value by 1."},
{"question":"Which operator is used for assignment?","options":["A) =","B) ==","C) +","D) &"],"correct":"A) =","explanation":"= assigns a value to a variable."},
{"question":"Which is bitwise OR operator?","options":["A) &&","B) ||","C) |","D) &"],"correct":"C) |","explanation":"| is bitwise OR."},
{"question":"Which is ternary operator?","options":["A) ? :","B) &&","C) ||","D) ="],"correct":"A) ? :","explanation":"Ternary operator ? : used for conditional expressions."},
],

'tamil': [
{"question":"Addition-க்கு operator எது?","options":["A) +","B) -","C) *","D) /"],"correct":"A) +","explanation":"+ addition-க்கு."},
{"question":"Equality compare-க்கு operator எது?","options":["A) =","B) ==","C) !=","D) <"],"correct":"B) ==","explanation":"== value-ஐ compare செய்யும்."},
{"question":"Modulus operator எது?","options":["A) %","B) /","C) *","D) &"],"correct":"A) %","explanation":"% remainder return செய்யும்."},
{"question":"Logical AND operator?","options":["A) &&","B) ||","C) &","D) |"],"correct":"A) &&","explanation":"&& logical AND."},
{"question":"Logical OR operator?","options":["A) &&","B) ||","C) &","D) |"],"correct":"B) ||","explanation":"|| logical OR."},
{"question":"Increment operator?","options":["A) ++","B) --","C) += ","D) -="],"correct":"A) ++","explanation":"++ value increase செய்யும்."},
{"question":"Decrement operator?","options":["A) ++","B) --","C) += ","D) -="],"correct":"B) --","explanation":"-- value decrease."},
{"question":"Assignment operator?","options":["A) =","B) ==","C) +","D) &"],"correct":"A) =","explanation":"= assign செய்யும்."},
{"question":"Bitwise OR operator?","options":["A) &&","B) ||","C) |","D) &"],"correct":"C) |","explanation":"| bitwise OR."},
{"question":"Ternary operator?","options":["A) ? :","B) &&","C) ||","D) ="],"correct":"A) ? :","explanation":"? : conditional expression."},
],

'tanglish': [
{"question":"Addition-kku operator enna?","options":["A) +","B) -","C) *","D) /"],"correct":"A) +","explanation":"+ addition-kku."},
{"question":"Equality check-ku operator enna?","options":["A) =","B) ==","C) !=","D) <"],"correct":"B) ==","explanation":"== value compare pannum."},
{"question":"Modulus operator?","options":["A) %","B) /","C) *","D) &"],"correct":"A) %","explanation":"% remainder kudukkum."},
{"question":"Logical AND operator?","options":["A) &&","B) ||","C) &","D) |"],"correct":"A) &&","explanation":"&& logical AND."},
{"question":"Logical OR operator?","options":["A) &&","B) ||","C) &","D) |"],"correct":"B) ||","explanation":"|| logical OR."},
{"question":"Increment operator?","options":["A) ++","B) --","C) += ","D) -="],"correct":"A) ++","explanation":"++ value increase pannum."},
{"question":"Decrement operator?","options":["A) ++","B) --","C) += ","D) -="],"correct":"B) --","explanation":"-- value decrease."},
{"question":"Assignment operator?","options":["A) =","B) ==","C) +","D) &"],"correct":"A) =","explanation":"= value assign pannum."},
{"question":"Bitwise OR operator?","options":["A) &&","B) ||","C) |","D) &"],"correct":"C) |","explanation":"| bitwise OR."},
{"question":"Ternary operator?","options":["A) ? :","B) &&","C) ||","D) ="],"correct":"A) ? :","explanation":"? : conditional expression."},
],

'hindi': [
{"question":"Addition operator कौन सा है?","options":["A) +","B) -","C) *","D) /"],"correct":"A) +","explanation":"+ addition के लिए।"},
{"question":"Equality check operator?","options":["A) =","B) ==","C) !=","D) <"],"correct":"B) ==","explanation":"== values compare करता है।"},
{"question":"Modulus operator?","options":["A) %","B) /","C) *","D) &"],"correct":"A) %","explanation":"% remainder देता है।"},
{"question":"Logical AND operator?","options":["A) &&","B) ||","C) &","D) |"],"correct":"A) &&","explanation":"&& logical AND।"},
{"question":"Logical OR operator?","options":["A) &&","B) ||","C) &","D) |"],"correct":"B) ||","explanation":"|| logical OR।"},
{"question":"Increment operator?","options":["A) ++","B) --","C) += ","D) -="],"correct":"A) ++","explanation":"++ value बढ़ाता है।"},
{"question":"Decrement operator?","options":["A) ++","B) --","C) += ","D) -="],"correct":"B) --","explanation":"-- value घटाता है।"},
{"question":"Assignment operator?","options":["A) =","B) ==","C) +","D) &"],"correct":"A) =","explanation":"= assign करता है।"},
{"question":"Bitwise OR operator?","options":["A) &&","B) ||","C) |","D) &"],"correct":"C) |","explanation":"| bitwise OR।"},
{"question":"Ternary operator?","options":["A) ? :","B) &&","C) ||","D) ="],"correct":"A) ? :","explanation":"? : conditional expression।"},
],

'malayalam': [
{"question":"Addition operator ഏത്?","options":["A) +","B) -","C) *","D) /"],"correct":"A) +","explanation":"+ addition-ന്."},
{"question":"Equality check operator?","options":["A) =","B) ==","C) !=","D) <"],"correct":"B) ==","explanation":"== values compare ചെയ്യുന്നു."},
{"question":"Modulus operator?","options":["A) %","B) /","C) *","D) &"],"correct":"A) %","explanation":"% remainder return ചെയ്യുന്നു."},
{"question":"Logical AND operator?","options":["A) &&","B) ||","C) &","D) |"],"correct":"A) &&","explanation":"&& logical AND."},
{"question":"Logical OR operator?","options":["A) &&","B) ||","C) &","D) |"],"correct":"B) ||","explanation":"|| logical OR."},
{"question":"Increment operator?","options":["A) ++","B) --","C) += ","D) -="],"correct":"A) ++","explanation":"++ value increase ചെയ്യുന്നു."},
{"question":"Decrement operator?","options":["A) ++","B) --","C) += ","D) -="],"correct":"B) --","explanation":"-- value decrease ചെയ്യുന്നു."},
{"question":"Assignment operator?","options":["A) =","B) ==","C) +","D) &"],"correct":"A) =","explanation":"= assign ചെയ്യുന്നു."},
{"question":"Bitwise OR operator?","options":["A) &&","B) ||","C) |","D) &"],"correct":"C) |","explanation":"| bitwise OR."},
{"question":"Ternary operator?","options":["A) ? :","B) &&","C) ||","D) ="],"correct":"A) ? :","explanation":"? : conditional expression."},
],
},#operators over
'Control Statements': {

'english': [
{"question":"Which statement is used to make a decision?","options":["A) if","B) for","C) while","D) switch"],"correct":"A) if","explanation":"if is used for decision making."},
{"question":"Which loop is entry-controlled?","options":["A) do-while","B) for","C) switch","D) break"],"correct":"B) for","explanation":"for loop checks condition before executing."},
{"question":"Which loop is exit-controlled?","options":["A) for","B) while","C) do-while","D) if"],"correct":"C) do-while","explanation":"do-while executes once before checking condition."},
{"question":"Which statement exits a loop?","options":["A) continue","B) break","C) pass","D) return"],"correct":"B) break","explanation":"break exits the loop."},
{"question":"Which statement skips current iteration?","options":["A) break","B) continue","C) return","D) switch"],"correct":"B) continue","explanation":"continue skips current iteration."},
{"question":"Switch statement works with which type?","options":["A) boolean","B) int, char, String","C) double","D) float"],"correct":"B) int, char, String","explanation":"switch supports int, char, String, enum."},
{"question":"What is the default case in switch?","options":["A) when condition false","B) optional case","C) executes if no match","D) none"],"correct":"C) executes if no match","explanation":"default runs when no case matches."},
{"question":"While loop syntax?","options":["A) while(condition){}","B) while{}","C) while(condition);","D) while:condition{}"],"correct":"A) while(condition){}","explanation":"Proper while loop syntax."},
{"question":"For loop structure?","options":["A) for(init; condition; update){}","B) for{}","C) for(condition){}","D) for(init; condition){}"],"correct":"A) for(init; condition; update){}","explanation":"Correct for loop format."},
{"question":"Do-while loop executes at least?","options":["A) 0 times","B) 1 time","C) 2 times","D) depends"],"correct":"B) 1 time","explanation":"do-while executes body once before condition check."},
],

'tamil': [
{"question":"Decision எடுக்க statement?","options":["A) if","B) for","C) while","D) switch"],"correct":"A) if","explanation":"if decision-making."},
{"question":"Entry-controlled loop?","options":["A) do-while","B) for","C) switch","D) break"],"correct":"B) for","explanation":"for condition check பின் execute."},
{"question":"Exit-controlled loop?","options":["A) for","B) while","C) do-while","D) if"],"correct":"C) do-while","explanation":"do-while executes once பின் check."},
{"question":"Loop exit செய்ய statement?","options":["A) continue","B) break","C) pass","D) return"],"correct":"B) break","explanation":"break loop exit."},
{"question":"Current iteration skip?","options":["A) break","B) continue","C) return","D) switch"],"correct":"B) continue","explanation":"continue skip current iteration."},
{"question":"Switch type support?","options":["A) boolean","B) int, char, String","C) double","D) float"],"correct":"B) int, char, String","explanation":"switch int, char, String, enum."},
{"question":"Default case?","options":["A) condition false","B) optional case","C) executes if no match","D) none"],"correct":"C) executes if no match","explanation":"default no match போது run."},
{"question":"While loop syntax?","options":["A) while(condition){}","B) while{}","C) while(condition);","D) while:condition{}"],"correct":"A) while(condition){}","explanation":"Correct while loop."},
{"question":"For loop structure?","options":["A) for(init; condition; update){}","B) for{}","C) for(condition){}","D) for(init; condition){}"],"correct":"A) for(init; condition; update){}","explanation":"Correct for loop."},
{"question":"Do-while executes at least?","options":["A) 0 times","B) 1 time","C) 2 times","D) depends"],"correct":"B) 1 time","explanation":"do-while once பின் check."},
],

'tanglish': [
{"question":"Decision statement enna?","options":["A) if","B) for","C) while","D) switch"],"correct":"A) if","explanation":"if decision making."},
{"question":"Entry-controlled loop?","options":["A) do-while","B) for","C) switch","D) break"],"correct":"B) for","explanation":"for condition check munnadi."},
{"question":"Exit-controlled loop?","options":["A) for","B) while","C) do-while","D) if"],"correct":"C) do-while","explanation":"do-while executes one time first."},
{"question":"Loop exit panna statement?","options":["A) continue","B) break","C) pass","D) return"],"correct":"B) break","explanation":"break loop exit."},
{"question":"Current iteration skip panna statement?","options":["A) break","B) continue","C) return","D) switch"],"correct":"B) continue","explanation":"continue skip current iteration."},
{"question":"Switch support panna types?","options":["A) boolean","B) int, char, String","C) double","D) float"],"correct":"B) int, char, String","explanation":"switch int, char, String, enum support."},
{"question":"Default case enna?","options":["A) condition false","B) optional case","C) executes if no match","D) none"],"correct":"C) executes if no match","explanation":"default no match la run."},
{"question":"While loop syntax?","options":["A) while(condition){}","B) while{}","C) while(condition);","D) while:condition{}"],"correct":"A) while(condition){}","explanation":"Correct syntax."},
{"question":"For loop structure?","options":["A) for(init; condition; update){}","B) for{}","C) for(condition){}","D) for(init; condition){}"],"correct":"A) for(init; condition; update){}","explanation":"Correct for loop."},
{"question":"Do-while executes minimum?","options":["A) 0 times","B) 1 time","C) 2 times","D) depends"],"correct":"B) 1 time","explanation":"do-while body once execute."},
],

'hindi': [
{"question":"Decision लेने का statement?","options":["A) if","B) for","C) while","D) switch"],"correct":"A) if","explanation":"if decision making."},
{"question":"Entry-controlled loop?","options":["A) do-while","B) for","C) switch","D) break"],"correct":"B) for","explanation":"for पहले condition check करता है।"},
{"question":"Exit-controlled loop?","options":["A) for","B) while","C) do-while","D) if"],"correct":"C) do-while","explanation":"do-while body एक बार execute करता है।"},
{"question":"Loop exit करने वाला statement?","options":["A) continue","B) break","C) pass","D) return"],"correct":"B) break","explanation":"break exits loop."},
{"question":"Current iteration skip करने वाला?","options":["A) break","B) continue","C) return","D) switch"],"correct":"B) continue","explanation":"continue skip करता है।"},
{"question":"Switch support types?","options":["A) boolean","B) int, char, String","C) double","D) float"],"correct":"B) int, char, String","explanation":"switch int, char, String, enum support करता है।"},
{"question":"Default case?","options":["A) condition false","B) optional case","C) executes if no match","D) none"],"correct":"C) executes if no match","explanation":"default तब run होगा जब कोई case match नहीं होगा।"},
{"question":"While loop syntax?","options":["A) while(condition){}","B) while{}","C) while(condition);","D) while:condition{}"],"correct":"A) while(condition){}","explanation":"Correct syntax."},
{"question":"For loop structure?","options":["A) for(init; condition; update){}","B) for{}","C) for(condition){}","D) for(init; condition){}"],"correct":"A) for(init; condition; update){}","explanation":"Correct for loop."},
{"question":"Do-while executes minimum?","options":["A) 0 times","B) 1 time","C) 2 times","D) depends"],"correct":"B) 1 time","explanation":"do-while body कम से कम एक बार execute करता है।"},
],

'malayalam': [
{"question":"Decision statement?","options":["A) if","B) for","C) while","D) switch"],"correct":"A) if","explanation":"if decision making."},
{"question":"Entry-controlled loop?","options":["A) do-while","B) for","C) switch","D) break"],"correct":"B) for","explanation":"for condition check munnadi."},
{"question":"Exit-controlled loop?","options":["A) for","B) while","C) do-while","D) if"],"correct":"C) do-while","explanation":"do-while executes one time."},
{"question":"Loop exit statement?","options":["A) continue","B) break","C) pass","D) return"],"correct":"B) break","explanation":"break loop exit."},
{"question":"Current iteration skip statement?","options":["A) break","B) continue","C) return","D) switch"],"correct":"B) continue","explanation":"continue skip current iteration."},
{"question":"Switch support types?","options":["A) boolean","B) int, char, String","C) double","D) float"],"correct":"B) int, char, String","explanation":"switch int, char, String, enum support."},
{"question":"Default case?","options":["A) condition false","B) optional case","C) executes if no match","D) none"],"correct":"C) executes if no match","explanation":"default no match la run."},
{"question":"While loop syntax?","options":["A) while(condition){}","B) while{}","C) while(condition);","D) while:condition{}"],"correct":"A) while(condition){}","explanation":"Correct syntax."},
{"question":"For loop structure?","options":["A) for(init; condition; update){}","B) for{}","C) for(condition){}","D) for(init; condition){}"],"correct":"A) for(init; condition; update){}","explanation":"Correct for loop."},
{"question":"Do-while executes minimum?","options":["A) 0 times","B) 1 time","C) 2 times","D) depends"],"correct":"B) 1 time","explanation":"do-while executes at least once."},
],

},#loops over
'Arrays': {

'english': [
{"question":"Which index does an array start with in Java?","options":["A) 0","B) 1","C) -1","D) depends"],"correct":"A) 0","explanation":"Java arrays are 0-indexed."},
{"question":"Which is correct way to declare array?","options":["A) int arr[];","B) int arr;","C) array arr[];","D) int arr()"],"correct":"A) int arr[];","explanation":"Correct syntax for array declaration."},
{"question":"How to get array length?","options":["A) arr.length","B) length(arr)","C) arr.size","D) size(arr)"],"correct":"A) arr.length","explanation":"Use .length property."},
{"question":"Default value of int array elements?","options":["A) 0","B) null","C) 1","D) undefined"],"correct":"A) 0","explanation":"int arrays default to 0."},
{"question":"Default value of boolean array?","options":["A) true","B) false","C) null","D) undefined"],"correct":"B) false","explanation":"boolean arrays default to false."},
{"question":"Which loop is used to traverse array?","options":["A) for loop","B) do-while","C) if","D) switch"],"correct":"A) for loop","explanation":"for loop commonly used to traverse arrays."},
{"question":"Can array size change after creation?","options":["A) Yes","B) No","C) Sometimes","D) Only with int arrays"],"correct":"B) No","explanation":"Java arrays have fixed size."},
{"question":"How to initialize array at declaration?","options":["A) int arr[] = {1,2,3};","B) int arr = {1,2,3};","C) int arr();","D) int arr{};"],"correct":"A) int arr[] = {1,2,3};","explanation":"Use curly braces."},
{"question":"Can we have multi-dimensional arrays?","options":["A) Yes","B) No","C) Only 2D","D) Only 1D"],"correct":"A) Yes","explanation":"Java supports multidimensional arrays."},
{"question":"Access last element of array arr?","options":["A) arr[arr.length-1]","B) arr[length]","C) arr[arr.size]","D) arr.last"],"correct":"A) arr[arr.length-1]","explanation":"Indexing starts at 0."},
],

'tamil': [
{"question":"Array index எப்பிடி start ஆகும்?","options":["A) 0","B) 1","C) -1","D) depends"],"correct":"A) 0","explanation":"Java array 0-indexed."},
{"question":"Array declare செய்ய syntax?","options":["A) int arr[];","B) int arr;","C) array arr[];","D) int arr()"],"correct":"A) int arr[];","explanation":"Correct syntax."},
{"question":"Array length பெற?","options":["A) arr.length","B) length(arr)","C) arr.size","D) size(arr)"],"correct":"A) arr.length","explanation":".length property."},
{"question":"int array default value?","options":["A) 0","B) null","C) 1","D) undefined"],"correct":"A) 0","explanation":"int default 0."},
{"question":"boolean array default value?","options":["A) true","B) false","C) null","D) undefined"],"correct":"B) false","explanation":"boolean default false."},
{"question":"Array traverse loop?","options":["A) for loop","B) do-while","C) if","D) switch"],"correct":"A) for loop","explanation":"for loop traverse."},
{"question":"Array size change after creation?","options":["A) ஆம்","B) இல்லை","C) சில நேரம்","D) int array மட்டும்"],"correct":"B) இல்லை","explanation":"Fixed size."},
{"question":"Declaration time initialize?","options":["A) int arr[] = {1,2,3};","B) int arr = {1,2,3};","C) int arr();","D) int arr{};"],"correct":"A) int arr[] = {1,2,3};","explanation":"Use {}."},
{"question":"Multi-dimensional arrays support?","options":["A) ஆம்","B) இல்லை","C) 2D மட்டும்","D) 1D மட்டும்"],"correct":"A) ஆம்","explanation":"Java multidimensional arrays support."},
{"question":"Last element access?","options":["A) arr[arr.length-1]","B) arr[length]","C) arr[arr.size]","D) arr.last"],"correct":"A) arr[arr.length-1]","explanation":"Index 0 based."},
],

'tanglish': [
{"question":"Array index eppadi start?","options":["A) 0","B) 1","C) -1","D) depends"],"correct":"A) 0","explanation":"Java array 0-indexed."},
{"question":"Array declare panna syntax?","options":["A) int arr[];","B) int arr;","C) array arr[];","D) int arr()"],"correct":"A) int arr[];","explanation":"Correct syntax."},
{"question":"Array length eppadi?","options":["A) arr.length","B) length(arr)","C) arr.size","D) size(arr)"],"correct":"A) arr.length","explanation":".length property use."},
{"question":"int array default value?","options":["A) 0","B) null","C) 1","D) undefined"],"correct":"A) 0","explanation":"int array default 0."},
{"question":"boolean array default?","options":["A) true","B) false","C) null","D) undefined"],"correct":"B) false","explanation":"boolean array default false."},
{"question":"Array traverse loop?","options":["A) for loop","B) do-while","C) if","D) switch"],"correct":"A) for loop","explanation":"for loop use."},
{"question":"Array size change after create panna mudiyuma?","options":["A) yes","B) no","C) sometimes","D) only int"],"correct":"B) no","explanation":"Java array fixed size."},
{"question":"Initialize array declaration time?","options":["A) int arr[] = {1,2,3};","B) int arr = {1,2,3};","C) int arr();","D) int arr{};"],"correct":"A) int arr[] = {1,2,3};","explanation":"{} use."},
{"question":"Multi-dimensional arrays support?","options":["A) yes","B) no","C) only 2D","D) only 1D"],"correct":"A) yes","explanation":"Java support multidimensional."},
{"question":"Last element access?","options":["A) arr[arr.length-1]","B) arr[length]","C) arr[arr.size]","D) arr.last"],"correct":"A) arr[arr.length-1]","explanation":"Index starts 0."},
],

'hindi': [
{"question":"Array index कहाँ से start?","options":["A) 0","B) 1","C) -1","D) depends"],"correct":"A) 0","explanation":"Java array 0-indexed."},
{"question":"Array declare करने का syntax?","options":["A) int arr[];","B) int arr;","C) array arr[];","D) int arr()"],"correct":"A) int arr[];","explanation":"Correct syntax."},
{"question":"Array length कैसे पाएँ?","options":["A) arr.length","B) length(arr)","C) arr.size","D) size(arr)"],"correct":"A) arr.length","explanation":".length use."},
{"question":"int array default value?","options":["A) 0","B) null","C) 1","D) undefined"],"correct":"A) 0","explanation":"int array default 0."},
{"question":"boolean array default value?","options":["A) true","B) false","C) null","D) undefined"],"correct":"B) false","explanation":"boolean array default false."},
{"question":"Array traverse करने के लिए loop?","options":["A) for loop","B) do-while","C) if","D) switch"],"correct":"A) for loop","explanation":"for loop use."},
{"question":"Array size change after creation?","options":["A) हाँ","B) नहीं","C) कभी-कभी","D) int array only"],"correct":"B) नहीं","explanation":"Array fixed size."},
{"question":"Array initialize declaration time?","options":["A) int arr[] = {1,2,3};","B) int arr = {1,2,3};","C) int arr();","D) int arr{};"],"correct":"A) int arr[] = {1,2,3};","explanation":"{} use."},
{"question":"Multi-dimensional arrays supported?","options":["A) हाँ","B) नहीं","C) सिर्फ 2D","D) सिर्फ 1D"],"correct":"A) हाँ","explanation":"Java multidimensional support."},
{"question":"Last element access?","options":["A) arr[arr.length-1]","B) arr[length]","C) arr[arr.size]","D) arr.last"],"correct":"A) arr[arr.length-1]","explanation":"Index 0 based."},
],

'malayalam': [
{"question":"Array index evide ninnu start?","options":["A) 0","B) 1","C) -1","D) depends"],"correct":"A) 0","explanation":"0-indexed."},
{"question":"Array declare syntax?","options":["A) int arr[];","B) int arr;","C) array arr[];","D) int arr()"],"correct":"A) int arr[];","explanation":"Correct syntax."},
{"question":"Array length?","options":["A) arr.length","B) length(arr)","C) arr.size","D) size(arr)"],"correct":"A) arr.length","explanation":".length use."},
{"question":"int array default value?","options":["A) 0","B) null","C) 1","D) undefined"],"correct":"A) 0","explanation":"int array default 0."},
{"question":"boolean array default value?","options":["A) true","B) false","C) null","D) undefined"],"correct":"B) false","explanation":"boolean array default false."},
{"question":"Array traverse loop?","options":["A) for loop","B) do-while","C) if","D) switch"],"correct":"A) for loop","explanation":"for loop use."},
{"question":"Array size change after creation?","options":["A) yes","B) no","C) sometimes","D) only int"],"correct":"B) no","explanation":"Fixed size."},
{"question":"Initialize array at declaration?","options":["A) int arr[] = {1,2,3};","B) int arr = {1,2,3};","C) int arr();","D) int arr{};"],"correct":"A) int arr[] = {1,2,3};","explanation":"{} use."},
{"question":"Multi-dimensional arrays support?","options":["A) yes","B) no","C) only 2D","D) only 1D"],"correct":"A) yes","explanation":"Supports multidimensional."},
{"question":"Last element access?","options":["A) arr[arr.length-1]","B) arr[length]","C) arr[arr.size]","D) arr.last"],"correct":"A) arr[arr.length-1]","explanation":"Index starts 0."},
],

},
'Methods': {

'english': [
{"question":"Which keyword is used to define a method?","options":["A) function","B) void","C) method","D) define"],"correct":"B) void","explanation":"void is used when method returns nothing."},
{"question":"Can a method return a value?","options":["A) Yes","B) No","C) Only void","D) Depends"],"correct":"A) Yes","explanation":"Methods can return values using return statement."},
{"question":"Method with no parameters?","options":["A) int add(int a)","B) void display()","C) void add(int a)","D) int display(int a)"],"correct":"B) void display()","explanation":"No parameters inside parentheses."},
{"question":"Method overloading possible?","options":["A) Yes","B) No","C) Only static","D) Only void"],"correct":"A) Yes","explanation":"Same method name with different parameters."},
{"question":"Method overriding possible?","options":["A) Yes","B) No","C) Only private methods","D) Only final methods"],"correct":"A) Yes","explanation":"Child class can override parent method."},
{"question":"Keyword to call method of same class?","options":["A) this","B) super","C) call","D) self"],"correct":"A) this","explanation":"this can call another method of same class."},
{"question":"Return type mismatch causes?","options":["A) Compilation error","B) Runtime error","C) Logical error","D) No error"],"correct":"A) Compilation error","explanation":"Return type must match method signature."},
{"question":"Static method can access instance variables?","options":["A) No","B) Yes","C) Only final","D) Sometimes"],"correct":"A) No","explanation":"Static cannot access instance variables directly."},
{"question":"Method recursion possible?","options":["A) Yes","B) No","C) Only void","D) Only static"],"correct":"A) Yes","explanation":"Method can call itself."},
{"question":"Constructor is a type of method?","options":["A) Yes","B) No","C) Only static","D) Only private"],"correct":"A) Yes","explanation":"Constructor initializes objects."},
],

'tamil': [
{"question":"Method define செய்ய keyword?","options":["A) function","B) void","C) method","D) define"],"correct":"B) void","explanation":"void பயன்படுத்தும்போது return value இல்லை."},
{"question":"Method value return செய்யமுடியுமா?","options":["A) ஆம்","B) இல்லை","C) void மட்டும்","D) depends"],"correct":"A) ஆம்","explanation":"return statement use செய்யலாம்."},
{"question":"Parameters இல்லாத method?","options":["A) int add(int a)","B) void display()","C) void add(int a)","D) int display(int a)"],"correct":"B) void display()","explanation":"Parentheses வெறுமை."},
{"question":"Method overloading செய்யமுடியுமா?","options":["A) ஆம்","B) இல்லை","C) static மட்டும்","D) void மட்டும்"],"correct":"A) ஆம்","explanation":"பேர் தான் method மாறலாம்."},
{"question":"Method overriding செய்யமுடியுமா?","options":["A) ஆம்","B) இல்லை","C) private method மட்டும்","D) final method மட்டும்"],"correct":"A) ஆம்","explanation":"Child class override parent method."},
{"question":"அதே class-ல் method call செய்ய keyword?","options":["A) this","B) super","C) call","D) self"],"correct":"A) this","explanation":"this method call செய்ய."},
{"question":"Return type mismatch error?","options":["A) Compilation error","B) Runtime error","C) Logical error","D) No error"],"correct":"A) Compilation error","explanation":"Return type match செய்ய வேண்டும்."},
{"question":"Static method instance variable access செய்யமுடியுமா?","options":["A) இல்லை","B) ஆம்","C) final மட்டும்","D) சில நேரம்"],"correct":"A) இல்லை","explanation":"Static direct access not allowed."},
{"question":"Recursion possible?","options":["A) ஆம்","B) இல்லை","C) void மட்டும்","D) static மட்டும்"],"correct":"A) ஆம்","explanation":"Method தானே call செய்யலாம்."},
{"question":"Constructor method-ஓ?","options":["A) ஆம்","B) இல்லை","C) static மட்டும்","D) private மட்டும்"],"correct":"A) ஆம்","explanation":"Constructor object initialize செய்ய."},
],

'tanglish': [
{"question":"Method define panna keyword?","options":["A) function","B) void","C) method","D) define"],"correct":"B) void","explanation":"void use panna return value illa."},
{"question":"Method value return panna mudiyuma?","options":["A) yes","B) no","C) only void","D) depends"],"correct":"A) yes","explanation":"return statement use pannalam."},
{"question":"No parameters method?","options":["A) int add(int a)","B) void display()","C) void add(int a)","D) int display(int a)"],"correct":"B) void display()","explanation":"Parentheses empty."},
{"question":"Method overloading possible?","options":["A) yes","B) no","C) only static","D) only void"],"correct":"A) yes","explanation":"Same name, different parameters."},
{"question":"Method overriding possible?","options":["A) yes","B) no","C) only private","D) only final"],"correct":"A) yes","explanation":"Child override parent."},
{"question":"Same class method call panna keyword?","options":["A) this","B) super","C) call","D) self"],"correct":"A) this","explanation":"this use panna."},
{"question":"Return type mismatch?","options":["A) compilation error","B) runtime error","C) logical error","D) no error"],"correct":"A) compilation error","explanation":"Return type match panna vendum."},
{"question":"Static method instance variable access panna mudiyuma?","options":["A) no","B) yes","C) only final","D) sometimes"],"correct":"A) no","explanation":"Static direct access impossible."},
{"question":"Recursion possible?","options":["A) yes","B) no","C) void only","D) static only"],"correct":"A) yes","explanation":"Method self call pannalam."},
{"question":"Constructor method-aha?","options":["A) yes","B) no","C) static only","D) private only"],"correct":"A) yes","explanation":"Constructor object initialize."},
],

'hindi': [
{"question":"Method define करने का keyword?","options":["A) function","B) void","C) method","D) define"],"correct":"B) void","explanation":"void method कोई value return नहीं करता."},
{"question":"Method value return कर सकता है?","options":["A) हाँ","B) नहीं","C) सिर्फ void","D) depends"],"correct":"A) हाँ","explanation":"return statement use होता है।"},
{"question":"No parameters method?","options":["A) int add(int a)","B) void display()","C) void add(int a)","D) int display(int a)"],"correct":"B) void display()","explanation":"Parentheses खाली।"},
{"question":"Method overloading संभव?","options":["A) हाँ","B) नहीं","C) केवल static","D) केवल void"],"correct":"A) हाँ","explanation":"Same नाम, different parameters."},
{"question":"Method overriding संभव?","options":["A) हाँ","B) नहीं","C) केवल private","D) केवल final"],"correct":"A) हाँ","explanation":"Child override कर सकता है।"},
{"question":"Same class method call keyword?","options":["A) this","B) super","C) call","D) self"],"correct":"A) this","explanation":"this use कर सकते हैं।"},
{"question":"Return type mismatch?","options":["A) Compilation error","B) Runtime error","C) Logical error","D) No error"],"correct":"A) Compilation error","explanation":"Return type match करना जरूरी।"},
{"question":"Static method instance variable access कर सकता है?","options":["A) नहीं","B) हाँ","C) सिर्फ final","D) कभी-कभी"],"correct":"A) नहीं","explanation":"Static direct access नहीं कर सकता।"},
{"question":"Recursion possible?","options":["A) हाँ","B) नहीं","C) void only","D) static only"],"correct":"A) हाँ","explanation":"Method खुद को call कर सकता है।"},
{"question":"Constructor method-है?","options":["A) हाँ","B) नहीं","C) static only","D) private only"],"correct":"A) हाँ","explanation":"Constructor object initialize करता है।"},
],

'malayalam': [
{"question":"Method define ചെയ്യാൻ keyword?","options":["A) function","B) void","C) method","D) define"],"correct":"B) void","explanation":"void method value return ചെയ്യില്ല."},
{"question":"Method value return ചെയ്യുമോ?","options":["A) yes","B) no","C) void മാത്രം","D) depends"],"correct":"A) yes","explanation":"return statement ഉപയോഗിക്കുന്നു."},
{"question":"Parameters ഇല്ലാത്ത method?","options":["A) int add(int a)","B) void display()","C) void add(int a)","D) int display(int a)"],"correct":"B) void display()","explanation":"Parentheses empty."},
{"question":"Method overloading support?","options":["A) yes","B) no","C) static മാത്രം","D) void മാത്രം"],"correct":"A) yes","explanation":"Same name different parameters."},
{"question":"Method overriding support?","options":["A) yes","B) no","C) private മാത്രം","D) final മാത്രം"],"correct":"A) yes","explanation":"Child override parent."},
{"question":"Same class method call keyword?","options":["A) this","B) super","C) call","D) self"],"correct":"A) this","explanation":"this use ചെയ്യാം."},
{"question":"Return type mismatch?","options":["A) compilation error","B) runtime error","C) logical error","D) no error"],"correct":"A) compilation error","explanation":"Return type match വേണം."},
{"question":"Static method instance variable access ചെയ്യുമോ?","options":["A) no","B) yes","C) final മാത്രം","D) sometimes"],"correct":"A) no","explanation":"Static direct access not allowed."},
{"question":"Recursion possible?","options":["A) yes","B) no","C) void only","D) static only"],"correct":"A) yes","explanation":"Method self call ചെയ്യാം."},
{"question":"Constructor method-ആണോ?","options":["A) yes","B) no","C) static only","D) private only"],"correct":"A) yes","explanation":"Constructor object initialize ചെയ്യും."},
],

},#methods over,

'OOP Concepts': {

'english': [
{"question":"OOP stands for?","options":["A) Object Oriented Programming","B) Only Programming","C) Open Object Program","D) Object Operation"],"correct":"A) Object Oriented Programming","explanation":"OOP = Object Oriented Programming."},
{"question":"Four main pillars of OOP?","options":["A) Abstraction, Encapsulation, Inheritance, Polymorphism","B) Loop, Array, Function, Class","C) Class, Method, Variable, Object","D) If, Else, Switch, For"],"correct":"A) Abstraction, Encapsulation, Inheritance, Polymorphism","explanation":"Four main principles."},
{"question":"Class is?","options":["A) Blueprint of object","B) Object itself","C) Variable type","D) Function"],"correct":"A) Blueprint of object","explanation":"Class defines structure of object."},
{"question":"Object is?","options":["A) Instance of class","B) Class","C) Method","D) Variable"],"correct":"A) Instance of class","explanation":"Object = instance of class."},
{"question":"Encapsulation is?","options":["A) Wrapping data & methods","B) Hiding class","C) Multiple inheritance","D) Loop control"],"correct":"A) Wrapping data & methods","explanation":"Data and methods wrapped together."},
{"question":"Abstraction is?","options":["A) Showing only necessary details","B) Showing everything","C) Method overloading","D) Object creation"],"correct":"A) Showing only necessary details","explanation":"Hide unnecessary details."},
{"question":"Polymorphism means?","options":["A) Many forms of methods/objects","B) Single method","C) Class only","D) Looping"],"correct":"A) Many forms of methods/objects","explanation":"Same name, different forms."},
{"question":"Constructor is used for?","options":["A) Object initialization","B) Method call","C) Looping","D) Variable declaration"],"correct":"A) Object initialization","explanation":"Constructor initializes object."},
{"question":"Java supports multiple inheritance?","options":["A) No, via interface","B) Yes","C) Only class","D) Sometimes"],"correct":"A) No, via interface","explanation":"Class multiple inheritance not allowed, interface yes."},
{"question":"Which feature allows code reusability?","options":["A) Inheritance","B) Loop","C) Encapsulation","D) Object"],"correct":"A) Inheritance","explanation":"Inheritance allows reuse of code."},
],

'tamil': [
{"question":"OOP full form?","options":["A) Object Oriented Programming","B) Only Programming","C) Open Object Program","D) Object Operation"],"correct":"A) Object Oriented Programming","explanation":"OOP = Object Oriented Programming."},
{"question":"OOP 4 pillars?","options":["A) Abstraction, Encapsulation, Inheritance, Polymorphism","B) Loop, Array, Function, Class","C) Class, Method, Variable, Object","D) If, Else, Switch, For"],"correct":"A) Abstraction, Encapsulation, Inheritance, Polymorphism","explanation":"நான்கு principle."},
{"question":"Class என்றால்?","options":["A) Object-ன் blueprint","B) Object தான்","C) Variable type","D) Function"],"correct":"A) Object-ன் blueprint","explanation":"Class structure define செய்யும்."},
{"question":"Object என்றால்?","options":["A) Class-ன் instance","B) Class","C) Method","D) Variable"],"correct":"A) Class-ன் instance","explanation":"Object = instance of class."},
{"question":"Encapsulation என்பது?","options":["A) Data & methods wrap செய்தல்","B) Class hide","C) Multiple inheritance","D) Loop control"],"correct":"A) Data & methods wrap செய்தல்","explanation":"Data, methods சேர்த்து வைத்தல்."},
{"question":"Abstraction என்பது?","options":["A) தேவையான details மட்டும் காட்டுதல்","B) எல்லாம் காட்டுதல்","C) Method overloading","D) Object creation"],"correct":"A) தேவையான details மட்டும் காட்டுதல்","explanation":"Unnecessary hide செய்யும்."},
{"question":"Polymorphism என்றால்?","options":["A) பல forms method/object-க்கு","B) Single method","C) Class மட்டும்","D) Loop"],"correct":"A) பல forms method/object-க்கு","explanation":"Same name, different forms."},
{"question":"Constructor பயன்பாடு?","options":["A) Object initialize","B) Method call","C) Loop","D) Variable declare"],"correct":"A) Object initialize","explanation":"Constructor object initialize செய்யும்."},
{"question":"Java multiple inheritance support செய்கிறதா?","options":["A) இல்லை, interface மூலம்","B) ஆம்","C) class மட்டும்","D) சில நேரம்"],"correct":"A) இல்லை, interface மூலம்","explanation":"Class multiple inheritance இல்லை, interface மூலம் possible."},
{"question":"Code reuse செய்ய feature?","options":["A) Inheritance","B) Loop","C) Encapsulation","D) Object"],"correct":"A) Inheritance","explanation":"Inheritance code reuse செய்ய உதவும்."},
],

'tanglish': [
{"question":"OOP full form?","options":["A) Object Oriented Programming","B) Only Programming","C) Open Object Program","D) Object Operation"],"correct":"A) Object Oriented Programming","explanation":"OOP = Object Oriented Programming."},
{"question":"4 pillars of OOP?","options":["A) Abstraction, Encapsulation, Inheritance, Polymorphism","B) Loop, Array, Function, Class","C) Class, Method, Variable, Object","D) If, Else, Switch, For"],"correct":"A) Abstraction, Encapsulation, Inheritance, Polymorphism","explanation":"Four main principles."},
{"question":"Class na enna?","options":["A) Blueprint of object","B) Object itself","C) Variable type","D) Function"],"correct":"A) Blueprint of object","explanation":"Class defines structure."},
{"question":"Object na?","options":["A) Instance of class","B) Class","C) Method","D) Variable"],"correct":"A) Instance of class","explanation":"Object = instance of class."},
{"question":"Encapsulation enna?","options":["A) Wrap data & methods","B) Hide class","C) Multiple inheritance","D) Loop control"],"correct":"A) Wrap data & methods","explanation":"Data, methods wrap pannuvom."},
{"question":"Abstraction enna?","options":["A) Show only necessary details","B) Show everything","C) Method overloading","D) Object creation"],"correct":"A) Show only necessary details","explanation":"Hide unnecessary details."},
{"question":"Polymorphism enna?","options":["A) Many forms methods/objects","B) Single method","C) Class only","D) Loop"],"correct":"A) Many forms methods/objects","explanation":"Same name different forms."},
{"question":"Constructor purpose?","options":["A) Object initialization","B) Method call","C) Loop","D) Variable declare"],"correct":"A) Object initialization","explanation":"Constructor object initialize."},
{"question":"Java multiple inheritance?","options":["A) No, via interface","B) Yes","C) Only class","D) Sometimes"],"correct":"A) No, via interface","explanation":"Class multiple inheritance not allowed, interface yes."},
{"question":"Code reuse feature?","options":["A) Inheritance","B) Loop","C) Encapsulation","D) Object"],"correct":"A) Inheritance","explanation":"Inheritance code reuse."},
],
'hindi': [
{"question":"OOP का मतलब क्या है?","options":["A) Object Oriented Programming","B) केवल Programming","C) Open Object Program","D) Object Operation"],"correct":"A) Object Oriented Programming","explanation":"OOP = Object Oriented Programming."},
{"question":"OOP के चार मुख्य स्तंभ कौनसे हैं?","options":["A) Abstraction, Encapsulation, Inheritance, Polymorphism","B) Loop, Array, Function, Class","C) Class, Method, Variable, Object","D) If, Else, Switch, For"],"correct":"A) Abstraction, Encapsulation, Inheritance, Polymorphism","explanation":"चार मुख्य सिद्धांत।"},
{"question":"Class क्या है?","options":["A) Object का Blueprint","B) Object स्वयं","C) Variable type","D) Function"],"correct":"A) Object का Blueprint","explanation":"Class object की संरचना को define करती है।"},
{"question":"Object क्या है?","options":["A) Class का instance","B) Class","C) Method","D) Variable"],"correct":"A) Class का instance","explanation":"Object = class का instance।"},
{"question":"Encapsulation क्या है?","options":["A) Data & Methods को wrap करना","B) Class छिपाना","C) Multiple inheritance","D) Loop control"],"correct":"A) Data & Methods को wrap करना","explanation":"Data और methods को एक साथ wrap किया जाता है।"},
{"question":"Abstraction क्या है?","options":["A) केवल आवश्यक details दिखाना","B) सब कुछ दिखाना","C) Method overloading","D) Object creation"],"correct":"A) केवल आवश्यक details दिखाना","explanation":"अनावश्यक details को छुपाना।"},
{"question":"Polymorphism का मतलब?","options":["A) Methods/Objects के कई रूप","B) Single method","C) केवल Class","D) Looping"],"correct":"A) Methods/Objects के कई रूप","explanation":"एक ही नाम, अलग-अलग रूप।"},
{"question":"Constructor का उपयोग किसके लिए?","options":["A) Object initialization","B) Method call","C) Looping","D) Variable declaration"],"correct":"A) Object initialization","explanation":"Constructor object को initialize करता है।"},
{"question":"Java multiple inheritance support करता है?","options":["A) नहीं, केवल interface के जरिए","B) हाँ","C) केवल class","D) कभी-कभी"],"correct":"A) नहीं, केवल interface के जरिए","explanation":"Class multiple inheritance allow नहीं, interface से हाँ।"},
{"question":"कौनसा feature code reusability allow करता है?","options":["A) Inheritance","B) Loop","C) Encapsulation","D) Object"],"correct":"A) Inheritance","explanation":"Inheritance code reuse करने देता है।"},
],

'malayalam': [
{"question":"OOP എന്നത് എന്തിന് പ്രതിനിധാനം ചെയ്യുന്നു?","options":["A) Object Oriented Programming","B) മാത്രം Programming","C) Open Object Program","D) Object Operation"],"correct":"A) Object Oriented Programming","explanation":"OOP = Object Oriented Programming."},
{"question":"OOP-ന്റെ നാല് പ്രധാന pillars ഏതാണ്?","options":["A) Abstraction, Encapsulation, Inheritance, Polymorphism","B) Loop, Array, Function, Class","C) Class, Method, Variable, Object","D) If, Else, Switch, For"],"correct":"A) Abstraction, Encapsulation, Inheritance, Polymorphism","explanation":"നാല് പ്രധാന സിദ്ധാന്തങ്ങൾ."},
{"question":"Class എന്താണ്?","options":["A) Object-ന്റെ Blueprint","B) Object തന്നെ","C) Variable type","D) Function"],"correct":"A) Object-ന്റെ Blueprint","explanation":"Class object-ന്റെ structure define ചെയ്യുന്നു."},
{"question":"Object എന്താണ്?","options":["A) Class-ന്റെ instance","B) Class","C) Method","D) Variable"],"correct":"A) Class-ന്റെ instance","explanation":"Object = class-ന്റെ instance."},
{"question":"Encapsulation എന്താണ്?","options":["A) Data & Methods wrap ചെയ്യുക","B) Class മറയ്ക്കുക","C) Multiple inheritance","D) Loop control"],"correct":"A) Data & Methods wrap ചെയ്യുക","explanation":"Data and methods ഒപ്പം wrap ചെയ്യുന്നു."},
{"question":"Abstraction എന്താണ്?","options":["A) ആവശ്യമായ details മാത്രം കാണിക്കുക","B) എല്ലാം കാണിക്കുക","C) Method overloading","D) Object creation"],"correct":"A) ആവശ്യമായ details മാത്രം കാണിക്കുക","explanation":"അപ്രയാസമായ details മറയ്ക്കുക."},
{"question":"Polymorphism എന്ത് അർത്ഥം?","options":["A) Methods/Objects-ന്റെ പല രൂപങ്ങൾ","B) Single method","C) Class മാത്രം","D) Looping"],"correct":"A) Methods/Objects-ന്റെ പല രൂപങ്ങൾ","explanation":"ഒരേ പേര്, വ്യത്യസ്ത രൂപങ്ങൾ."},
{"question":"Constructor ഉപയോഗിക്കുന്നത് എന്തിന്?","options":["A) Object initialization","B) Method call","C) Looping","D) Variable declaration"],"correct":"A) Object initialization","explanation":"Constructor object initialize ചെയ്യുന്നു."},
{"question":"Java multiple inheritance support ചെയ്യുന്നുണ്ടോ?","options":["A) ഇല്ല, interface വഴി മാത്രം","B) ഉണ്ട്","C) Class മാത്രം","D) ചിലപ്പോൾ"],"correct":"A) ഇല്ല, interface വഴി മാത്രം","explanation":"Class multiple inheritance allow ചെയ്യുന്നില്ല, interface-ൽ כן."},
{"question":"Code reusability അനുവദിക്കുന്ന feature ഏതാണ്?","options":["A) Inheritance","B) Loop","C) Encapsulation","D) Object"],"correct":"A) Inheritance","explanation":"Inheritance code reuse ചെയ്യാൻ അനുവദിക്കുന്നു."},
]},#oop over

'Inheritance': {

'english': [
{"question":"Inheritance in Java means?","options":["A) Acquiring properties of another class","B) Loop control","C) Variable declaration","D) Function call"],"correct":"A) Acquiring properties of another class","explanation":"Child class gets fields and methods of parent class."},
{"question":"Keyword for inheritance?","options":["A) extends","B) implements","C) inherit","D) super"],"correct":"A) extends","explanation":"Use extends to inherit a class."},
{"question":"Java supports multiple inheritance?","options":["A) No, only via interfaces","B) Yes","C) Sometimes","D) Only for abstract class"],"correct":"A) No, only via interfaces","explanation":"Java avoids multiple class inheritance."},
{"question":"Parent class is also called?","options":["A) Super class","B) Base class","C) Both A & B","D) Child class"],"correct":"C) Both A & B","explanation":"Super class or base class is parent."},
{"question":"Child class is also called?","options":["A) Subclass","B) Derived class","C) Both A & B","D) Parent class"],"correct":"C) Both A & B","explanation":"Subclass or derived class is child."},
{"question":"Constructor inheritance possible?","options":["A) No","B) Yes","C) Sometimes","D) Only final"],"correct":"A) No","explanation":"Constructors are not inherited."},
{"question":"Private members inheritance?","options":["A) Not inherited","B) Fully inherited","C) Partially inherited","D) Only via interface"],"correct":"A) Not inherited","explanation":"Private members not accessible in child."},
{"question":"super keyword use?","options":["A) Access parent class members","B) Loop control","C) Variable reuse","D) Only method call"],"correct":"A) Access parent class members","explanation":"super calls parent members/methods."},
{"question":"Which supports inheritance?","options":["A) Class","B) Interface","C) Abstract class","D) All of these"],"correct":"D) All of these","explanation":"All can participate in inheritance."},
{"question":"Why use inheritance?","options":["A) Code reusability & hierarchy","B) Loop control","C) Variable reuse","D) Only method call"],"correct":"A) Code reusability & hierarchy","explanation":"Reuse code and establish class hierarchy."},
],

'tamil': [
{"question":"Inheritance என்றால்?","options":["A) மற்ற class-இன் properties பெறுதல்","B) Loop control","C) Variable declare","D) Function call"],"correct":"A) மற்ற class-இன் properties பெறுதல்","explanation":"Child class, parent class-இன் fields & methods பெறும்."},
{"question":"Inheritance keyword?","options":["A) extends","B) implements","C) inherit","D) super"],"correct":"A) extends","explanation":"extends keyword பயன்படுத்தப்படுகிறது."},
{"question":"Java multiple inheritance support செய்கிறதா?","options":["A) இல்லை, interfaces மூலமாக தான்","B) ஆம்","C) சில நேரம்","D) abstract class-க்கு மட்டும்"],"correct":"A) இல்லை, interfaces மூலமாக தான்","explanation":"Java multiple class inheritance avoid செய்கிறது."},
{"question":"Parent class-க்கு மற்றொரு பெயர்?","options":["A) Super class","B) Base class","C) இரண்டும்","D) Child class"],"correct":"C) இரண்டும்","explanation":"Super class அல்லது Base class parent class ஆகும்."},
{"question":"Child class-க்கு மற்றொரு பெயர்?","options":["A) Subclass","B) Derived class","C) இரண்டும்","D) Parent class"],"correct":"C) இரண்டும்","explanation":"Subclass அல்லது Derived class child class ஆகும்."},
{"question":"Constructor inheritance சாத்தியம்?","options":["A) இல்லை","B) ஆம்","C) சில நேரம்","D) final மட்டுமே"],"correct":"A) இல்லை","explanation":"Constructor-கள் inherit செய்யப்படாது."},
{"question":"Private members inheritance?","options":["A) இல்லை","B) முழுமையாக inherit செய்யப்படும்","C) பகுதியளவு","D) Interface மூலம் மட்டும்"],"correct":"A) இல்லை","explanation":"Private members child class-இல் கிடையாது."},
{"question":"super keyword பயன்பாடு?","options":["A) Parent class members access செய்ய","B) Loop control","C) Variable reuse","D) Method call மட்டுமே"],"correct":"A) Parent class members access செய்ய","explanation":"super parent members/methods க்கு call செய்கிறது."},
{"question":"Inheritance-க்கு support செய்யும்?","options":["A) Class","B) Interface","C) Abstract class","D) எல்லாம்"],"correct":"D) எல்லாம்","explanation":"எல்லாம் inheritance-ல் கலந்து கொள்ளலாம்."},
{"question":"Inheritance ஏன் பயன்படுத்தப்படுகிறது?","options":["A) Code reusability & hierarchy","B) Loop control","C) Variable reuse","D) Method call மட்டும்"],"correct":"A) Code reusability & hierarchy","explanation":"Code reuse & class hierarchy உருவாக்க."},
],

'tanglish': [
{"question":"Inheritance na enna?","options":["A) vera class-oda properties acquire pannradhu","B) Loop control","C) Variable declare","D) Function call"],"correct":"A) vera class-oda properties acquire pannradhu","explanation":"Child class parent class fields & methods acquire pannum."},
{"question":"Keyword for inheritance?","options":["A) extends","B) implements","C) inherit","D) super"],"correct":"A) extends","explanation":"extends use pannuvom inheritance-kku."},
{"question":"Java multiple inheritance support pannumaa?","options":["A) Illai, interfaces use pannina thaan","B) Aam","C) Sometimes","D) Abstract class-ku mattum"],"correct":"A) Illai, interfaces use pannina thaan","explanation":"Java multiple class inheritance avoid pannum."},
{"question":"Parent class-oda inoru name?","options":["A) Super class","B) Base class","C) Both","D) Child class"],"correct":"C) Both","explanation":"Super class or Base class parent class."},
{"question":"Child class-oda inoru name?","options":["A) Subclass","B) Derived class","C) Both","D) Parent class"],"correct":"C) Both","explanation":"Subclass or Derived class child."},
{"question":"Constructor inheritance possible?","options":["A) Illai","B) Aam","C) Sometimes","D) final mattum"],"correct":"A) Illai","explanation":"Constructors inherit agathu."},
{"question":"Private members inheritance?","options":["A) Illai","B) Fully inherit","C) Partially","D) Interface use panna mattum"],"correct":"A) Illai","explanation":"Private members child class access panna mudiyathu."},
{"question":"super keyword use?","options":["A) Parent class members access panna","B) Loop control","C) Variable reuse","D) Method call mattum"],"correct":"A) Parent class members access panna","explanation":"super parent members/methods kku call pannum."},
{"question":"Inheritance-ku support pannuvathu?","options":["A) Class","B) Interface","C) Abstract class","D) Ellam"],"correct":"D) Ellam","explanation":"Ellam inheritance-il join aagum."},
{"question":"Inheritance use panna reason?","options":["A) Code reuse & hierarchy","B) Loop control","C) Variable reuse","D) Method call mattum"],"correct":"A) Code reuse & hierarchy","explanation":"Code reuse & hierarchy build panna."},
],

'hindi': [
{"question":"Inheritance का मतलब?","options":["A) किसी class की properties लेना","B) Loop control","C) Variable declare","D) Function call"],"correct":"A) किसी class की properties लेना","explanation":"Child class parent class के fields & methods लेता है."},
{"question":"Inheritance keyword?","options":["A) extends","B) implements","C) inherit","D) super"],"correct":"A) extends","explanation":"extends keyword use होता है."},
{"question":"Java में multiple inheritance support करता है?","options":["A) नहीं, interfaces के जरिए","B) हाँ","C) कभी-कभी","D) केवल abstract class"],"correct":"A) नहीं, interfaces के जरिए","explanation":"Java multiple class inheritance avoid करता है."},
{"question":"Parent class को अन्य नाम?","options":["A) Super class","B) Base class","C) दोनों","D) Child class"],"correct":"C) दोनों","explanation":"Super class या Base class parent होता है."},
{"question":"Child class को अन्य नाम?","options":["A) Subclass","B) Derived class","C) दोनों","D) Parent class"],"correct":"C) दोनों","explanation":"Subclass या Derived class child होता है."},
{"question":"Constructor inheritance possible?","options":["A) नहीं","B) हाँ","C) कभी-कभी","D) केवल final"],"correct":"A) नहीं","explanation":"Constructors inherit नहीं होते."},
{"question":"Private members inheritance?","options":["A) नहीं","B) पूरी तरह inherit","C) आंशिक","D) Interface के जरिए"],"correct":"A) नहीं","explanation":"Private members child class में access नहीं होते."},
{"question":"super keyword use?","options":["A) Parent class members access करना","B) Loop control","C) Variable reuse","D) Method call केवल"],"correct":"A) Parent class members access करना","explanation":"super parent members/methods को call करता है."},
{"question":"Inheritance support करता है?","options":["A) Class","B) Interface","C) Abstract class","D) सभी"],"correct":"D) सभी","explanation":"सभी inheritance में participate कर सकते हैं."},
{"question":"Inheritance use क्यों?","options":["A) Code reuse & hierarchy","B) Loop control","C) Variable reuse","D) केवल method call"],"correct":"A) Code reuse & hierarchy","explanation":"Code reuse & class hierarchy बनाए."},
],

'malayalam': [
{"question":"Inheritance എന്നത് എന്ത്?","options":["A) മറ്റൊരു class-ന്റെ properties acquire ചെയ്യുക","B) Loop control","C) Variable declare","D) Function call"],"correct":"A) മറ്റൊരു class-ന്റെ properties acquire ചെയ്യുക","explanation":"Child class parent class fields & methods inherit ചെയ്യും."},
{"question":"Inheritance keyword?","options":["A) extends","B) implements","C) inherit","D) super"],"correct":"A) extends","explanation":"extends keyword use ചെയ്യുന്നു."},
{"question":"Java multiple inheritance support ചെയ്യുന്നുണ്ടോ?","options":["A) ഇല്ല, interfaces വഴി മാത്രം","B) ഉണ്ട്","C) ചിലപ്പോൾ","D) abstract class-க்கு മാത്രം"],"correct":"A) ഇല്ല, interfaces വഴി മാത്രം","explanation":"Java multiple class inheritance avoid ചെയ്യുന്നു."},
{"question":"Parent class-ന് മറ്റൊരു പേര്?","options":["A) Super class","B) Base class","C) രണ്ട് പേരും ശരി","D) Child class"],"correct":"C) രണ്ട് പേരും ശരി","explanation":"Super class അല്ലെങ്കിൽ Base class parent class."},
{"question":"Child class-ന് മറ്റൊരു പേര്?","options":["A) Subclass","B) Derived class","C) രണ്ട് പേരും ശരി","D) Parent class"],"correct":"C) രണ്ട് പേരും ശരി","explanation":"Subclass അല്ലെങ്കിൽ Derived class child class."},
{"question":"Constructor inheritance possible?","options":["A) ഇല്ല","B) ഉണ്ട്","C) ചിലപ്പോൾ","D) final മാത്രം"],"correct":"A) ഇല്ല","explanation":"Constructors inherit ചെയ്യില്ല."},
{"question":"Private members inheritance?","options":["A) ഇല്ല","B) പൂര്‍ണ്ണമായി inherit","C) ഭാഗികമായി","D) Interface വഴിയേ മാത്രം"],"correct":"A) ഇല്ല","explanation":"Private members child class-ൽ access ചെയ്യാനാകില്ല."},
{"question":"super keyword use?","options":["A) Parent class members access ചെയ്യാൻ","B) Loop control","C) Variable reuse","D) Method call മാത്രം"],"correct":"A) Parent class members access ചെയ്യാൻ","explanation":"super parent members/methods call ചെയ്യാൻ."},
{"question":"Inheritance-ന് support ചെയ്യുന്നവ?","options":["A) Class","B) Interface","C) Abstract class","D) എല്ലാം"],"correct":"D) എല്ലാം","explanation":"എല്ലാം inheritance-ൽ join ആകാം."},
{"question":"Inheritance ഉപയോഗിക്കുന്നത് എന്തിന്?","options":["A) Code reuse & hierarchy","B) Loop control","C) Variable reuse","D) Method call മാത്രം"],"correct":"A) Code reuse & hierarchy","explanation":"Code reuse & hierarchy build ചെയ്യാൻ."},
],},#inheritance
'Interfaces':{
'english': [
{"question":"What is an interface in Java?","options":["A) Blueprint of class methods","B) Class object","C) Variable","D) Loop"],"correct":"A) Blueprint of class methods","explanation":"Interface defines abstract methods."},
{"question":"Interface methods are by default?","options":["A) Public and abstract","B) Private","C) Protected","D) Static only"],"correct":"A) Public and abstract","explanation":"All interface methods are public abstract."},
{"question":"Which keyword is used to implement interface?","options":["A) implements","B) extends","C) inherit","D) use"],"correct":"A) implements","explanation":"Class uses implements keyword."},
{"question":"Can interface have variables?","options":["A) Yes, final and static","B) No","C) Only private","D) Only public"],"correct":"A) Yes, final and static","explanation":"Variables are public static final."},
{"question":"Can we create object of interface?","options":["A) No","B) Yes","C) Sometimes","D) Only once"],"correct":"A) No","explanation":"Interface cannot be instantiated."},
{"question":"Does Java support multiple inheritance using interface?","options":["A) Yes","B) No","C) Only class","D) Sometimes"],"correct":"A) Yes","explanation":"Multiple inheritance via interfaces."},
{"question":"Which method can have body in interface (Java 8+)?","options":["A) Default and static","B) Abstract only","C) Private only","D) None"],"correct":"A) Default and static","explanation":"Java 8 introduced default & static methods."},
{"question":"Interface is used for?","options":["A) Abstraction","B) Looping","C) Sorting","D) Printing"],"correct":"A) Abstraction","explanation":"Hides implementation details."},
{"question":"Which keyword is used to declare interface?","options":["A) interface","B) class","C) struct","D) object"],"correct":"A) interface","explanation":"Use 'interface' keyword."},
{"question":"Can a class implement multiple interfaces?","options":["A) Yes","B) No","C) Only one","D) Sometimes"],"correct":"A) Yes","explanation":"Java allows multiple interfaces."}
],

'tamil': [
{"question":"Java-வில் interface என்ன?","options":["A) Method blueprint","B) Class object","C) Variable","D) Loop"],"correct":"A) Method blueprint","explanation":"Abstract methods define செய்கிறது."},
{"question":"Interface methods default?","options":["A) Public abstract","B) Private","C) Protected","D) Static"],"correct":"A) Public abstract","explanation":"Default public abstract."},
{"question":"Implement keyword?","options":["A) implements","B) extends","C) inherit","D) use"],"correct":"A) implements","explanation":"Class implements use செய்கிறது."},
{"question":"Variables?","options":["A) final static","B) No","C) Private","D) Public"],"correct":"A) final static","explanation":"Public static final."},
{"question":"Object create?","options":["A) No","B) Yes","C) Sometimes","D) Once"],"correct":"A) No","explanation":"Instantiate முடியாது."},
{"question":"Multiple inheritance?","options":["A) Yes","B) No","C) Class மட்டும்","D) Sometimes"],"correct":"A) Yes","explanation":"Interface மூலம் possible."},
{"question":"Method body?","options":["A) Default static","B) Abstract","C) Private","D) None"],"correct":"A) Default static","explanation":"Java 8 feature."},
{"question":"Use?","options":["A) Abstraction","B) Loop","C) Sort","D) Print"],"correct":"A) Abstraction","explanation":"Implementation hide."},
{"question":"Declare keyword?","options":["A) interface","B) class","C) struct","D) object"],"correct":"A) interface","explanation":"interface keyword use."},
{"question":"Multiple interfaces?","options":["A) Yes","B) No","C) One","D) Sometimes"],"correct":"A) Yes","explanation":"Multiple implement."}
],

'tanglish': [
{"question":"Interface na?","options":["A) Method blueprint","B) Object","C) Variable","D) Loop"],"correct":"A) Method blueprint","explanation":"Abstract methods."},
{"question":"Default methods?","options":["A) Public abstract","B) Private","C) Protected","D) Static"],"correct":"A) Public abstract","explanation":"Default ah public abstract."},
{"question":"Implement keyword?","options":["A) implements","B) extends","C) inherit","D) use"],"correct":"A) implements","explanation":"Class implement pannum."},
{"question":"Variables?","options":["A) final static","B) No","C) Private","D) Public"],"correct":"A) final static","explanation":"Public static final."},
{"question":"Object create?","options":["A) No","B) Yes","C) Sometimes","D) Once"],"correct":"A) No","explanation":"Create panna mudiyadhu."},
{"question":"Multiple inheritance?","options":["A) Yes","B) No","C) Class","D) Sometimes"],"correct":"A) Yes","explanation":"Interface use pannalaam."},
{"question":"Method body?","options":["A) Default static","B) Abstract","C) Private","D) None"],"correct":"A) Default static","explanation":"Java 8 feature."},
{"question":"Use?","options":["A) Abstraction","B) Loop","C) Sort","D) Print"],"correct":"A) Abstraction","explanation":"Hide logic."},
{"question":"Keyword?","options":["A) interface","B) class","C) struct","D) object"],"correct":"A) interface","explanation":"Declare panna."},
{"question":"Multiple interfaces?","options":["A) Yes","B) No","C) One","D) Sometimes"],"correct":"A) Yes","explanation":"Implement pannalaam."}
],

'hindi': [
{"question":"Java में interface क्या है?","options":["A) Method blueprint","B) Object","C) Variable","D) Loop"],"correct":"A) Method blueprint","explanation":"Abstract methods define करता है।"},
{"question":"Default methods?","options":["A) Public abstract","B) Private","C) Protected","D) Static"],"correct":"A) Public abstract","explanation":"Default public abstract होते हैं।"},
{"question":"Implement keyword?","options":["A) implements","B) extends","C) inherit","D) use"],"correct":"A) implements","explanation":"Class implements use करता है।"},
{"question":"Variables?","options":["A) final static","B) No","C) Private","D) Public"],"correct":"A) final static","explanation":"Public static final होते हैं।"},
{"question":"Object create?","options":["A) No","B) Yes","C) Sometimes","D) Once"],"correct":"A) No","explanation":"Interface का object नहीं बना सकते।"},
{"question":"Multiple inheritance?","options":["A) Yes","B) No","C) Class","D) Sometimes"],"correct":"A) Yes","explanation":"Interface से possible है।"},
{"question":"Method body?","options":["A) Default static","B) Abstract","C) Private","D) None"],"correct":"A) Default static","explanation":"Java 8 feature।"},
{"question":"Use?","options":["A) Abstraction","B) Loop","C) Sort","D) Print"],"correct":"A) Abstraction","explanation":"Implementation hide करता है।"},
{"question":"Keyword?","options":["A) interface","B) class","C) struct","D) object"],"correct":"A) interface","explanation":"Declare करने के लिए।"},
{"question":"Multiple interfaces?","options":["A) Yes","B) No","C) One","D) Sometimes"],"correct":"A) Yes","explanation":"Multiple implement कर सकते हैं।"}
],

'malayalam': [
{"question":"Javaയിൽ interface എന്താണ്?","options":["A) Method blueprint","B) Object","C) Variable","D) Loop"],"correct":"A) Method blueprint","explanation":"Abstract methods define ചെയ്യുന്നു."},
{"question":"Default methods?","options":["A) Public abstract","B) Private","C) Protected","D) Static"],"correct":"A) Public abstract","explanation":"Default public abstract."},
{"question":"Implement keyword?","options":["A) implements","B) extends","C) inherit","D) use"],"correct":"A) implements","explanation":"Class implements ഉപയോഗിക്കുന്നു."},
{"question":"Variables?","options":["A) final static","B) No","C) Private","D) Public"],"correct":"A) final static","explanation":"Public static final."},
{"question":"Object create?","options":["A) No","B) Yes","C) Sometimes","D) Once"],"correct":"A) No","explanation":"Interface instantiate ചെയ്യാൻ പറ്റില്ല."},
{"question":"Multiple inheritance?","options":["A) Yes","B) No","C) Class","D) Sometimes"],"correct":"A) Yes","explanation":"Interface വഴി possible."},
{"question":"Method body?","options":["A) Default static","B) Abstract","C) Private","D) None"],"correct":"A) Default static","explanation":"Java 8 feature."},
{"question":"Use?","options":["A) Abstraction","B) Loop","C) Sort","D) Print"],"correct":"A) Abstraction","explanation":"Implementation hide ചെയ്യുന്നു."},
{"question":"Keyword?","options":["A) interface","B) class","C) struct","D) object"],"correct":"A) interface","explanation":"Declare ചെയ്യാൻ."},
{"question":"Multiple interfaces?","options":["A) Yes","B) No","C) One","D) Sometimes"],"correct":"A) Yes","explanation":"Multiple implement ചെയ്യാം."}
],},
'Exception Handling': {

'english': [
{"question":"What is an exception in Java?","options":["A) Loop","B) Error during execution","C) Variable","D) Function"],"correct":"B) Error during execution","explanation":"An exception is an event that occurs during the execution of a program that disrupts normal flow."},
{"question":"Which keyword is used to handle exceptions?","options":["A) try","B) catch","C) throw","D) final"],"correct":"A) try","explanation":"The try block is used to wrap code that may throw an exception."},
{"question":"Which block catches an exception?","options":["A) try","B) catch","C) finally","D) throw"],"correct":"B) catch","explanation":"catch block handles the exception thrown by try block."},
{"question":"Which block always executes?","options":["A) try","B) catch","C) finally","D) throw"],"correct":"C) finally","explanation":"finally block executes always, whether exception occurs or not."},
{"question":"Which keyword is used to manually throw an exception?","options":["A) throw","B) raise","C) catch","D) handle"],"correct":"A) throw","explanation":"throw keyword is used to explicitly throw an exception."},
{"question":"What happens if an exception is not handled?","options":["A) Program ignores it","B) Program crashes","C) Loop continues","D) Nothing"],"correct":"B) Program crashes","explanation":"Unhandled exceptions terminate the program."},
{"question":"Can multiple catch blocks be used?","options":["A) No","B) Yes","C) Only one","D) Sometimes"],"correct":"B) Yes","explanation":"Multiple catch blocks can handle different types of exceptions."},
{"question":"Which exception occurs for dividing by zero?","options":["A) ArithmeticException","B) NullPointerException","C) IOException","D) ClassNotFoundException"],"correct":"A) ArithmeticException","explanation":"Dividing by zero throws ArithmeticException."},
{"question":"Which exception occurs for invalid array index?","options":["A) ArrayIndexOutOfBoundsException","B) NumberFormatException","C) IOException","D) ClassCastException"],"correct":"A) ArrayIndexOutOfBoundsException","explanation":"Accessing invalid array index throws this exception."},
{"question":"Which exception occurs for null object reference?","options":["A) NullPointerException","B) ArithmeticException","C) IOException","D) ClassNotFoundException"],"correct":"A) NullPointerException","explanation":"Accessing members of a null object throws NullPointerException."},
],

'hindi': [
{"question":"Java में exception क्या है?","options":["A) Loop","B) Execution के दौरान error","C) Variable","D) Function"],"correct":"B) Execution के दौरान error","explanation":"Exception एक घटना है जो program execution को disrupt करती है।"},
{"question":"Exception handle करने के लिए keyword?","options":["A) try","B) catch","C) throw","D) final"],"correct":"A) try","explanation":"try block में वो code होता है जो exception throw कर सकता है।"},
{"question":"कौनसा block exception को catch करता है?","options":["A) try","B) catch","C) finally","D) throw"],"correct":"B) catch","explanation":"catch block try में thrown exception को handle करता है।"},
{"question":"कौनसा block हमेशा execute होता है?","options":["A) try","B) catch","C) finally","D) throw"],"correct":"C) finally","explanation":"finally block हमेशा execute होता है।"},
{"question":"Manually exception throw करने के लिए keyword?","options":["A) throw","B) raise","C) catch","D) handle"],"correct":"A) throw","explanation":"throw keyword exception को explicitly throw करने के लिए।"},
{"question":"अगर exception handle ना किया जाए तो क्या होगा?","options":["A) Program ignore करेगा","B) Program crash होगा","C) Loop continue होगा","D) कुछ नहीं होगा"],"correct":"B) Program crash होगा","explanation":"Unhandled exception program को terminate कर देता है।"},
{"question":"क्या multiple catch blocks use किए जा सकते हैं?","options":["A) नहीं","B) हाँ","C) केवल एक","D) कभी-कभी"],"correct":"B) हाँ","explanation":"Multiple catch blocks अलग-अलग exceptions handle कर सकते हैं।"},
{"question":"Zero से divide करने पर कौनसा exception आता है?","options":["A) ArithmeticException","B) NullPointerException","C) IOException","D) ClassNotFoundException"],"correct":"A) ArithmeticException","explanation":"Zero divide करने पर ArithmeticException आता है।"},
{"question":"Invalid array index access करने पर कौनसा exception आता है?","options":["A) ArrayIndexOutOfBoundsException","B) NumberFormatException","C) IOException","D) ClassCastException"],"correct":"A) ArrayIndexOutOfBoundsException","explanation":"Invalid array index access करने पर यह exception आता है।"},
{"question":"Null object reference access करने पर कौनसा exception आता है?","options":["A) NullPointerException","B) ArithmeticException","C) IOException","D) ClassNotFoundException"],"correct":"A) NullPointerException","explanation":"Null object के member access करने पर NullPointerException आता है।"},
],

'tamil': [
{"question":"Java-ல் exception என்றால் என்ன?","options":["A) Loop","B) Execution பிழை","C) Variable","D) Function"],"correct":"B) Execution பிழை","explanation":"Execution போது program நடத்தை கெட்டுப்போகும் நிகழ்வு."},
{"question":"Exception handle செய்ய keyword?","options":["A) try","B) catch","C) throw","D) final"],"correct":"A) try","explanation":"try block exception throw செய்யக்கூடிய code."},
{"question":"Exception catch செய்ய block?","options":["A) try","B) catch","C) finally","D) throw"],"correct":"B) catch","explanation":"catch block try block-ல் வரும் exception handle செய்யும்."},
{"question":"எப்போதும் இயங்கும் block?","options":["A) try","B) catch","C) finally","D) throw"],"correct":"C) finally","explanation":"finally block எப்போதும் execute ஆகும்."},
{"question":"Manual ஆக exception throw செய்ய keyword?","options":["A) throw","B) raise","C) catch","D) handle"],"correct":"A) throw","explanation":"throw keyword-ஐ use செய்து exception throw செய்யலாம்."},
{"question":"Exception handle செய்யாவிட்டால் என்ன ஆகும்?","options":["A) Program ignore","B) Program crash","C) Loop continue","D) ஒன்றுமில்லை"],"correct":"B) Program crash","explanation":"Unhandled exception program-ஐ நிறுத்தும்."},
{"question":"Multiple catch blocks பயன்படுத்த முடியுமா?","options":["A) இல்லை","B) ஆம்","C) ஒன்று மட்டும்","D) சிலசமயம்"],"correct":"B) ஆம்","explanation":"பல catch blocks வெவ்வேறு exceptions handle செய்யும்."},
{"question":"Zero divide செய்யும் போது exception?","options":["A) ArithmeticException","B) NullPointerException","C) IOException","D) ClassNotFoundException"],"correct":"A) ArithmeticException","explanation":"0-ஆல் divide செய்யும் போது ArithmeticException வரும்."},
{"question":"Invalid array index access செய்யும் போது exception?","options":["A) ArrayIndexOutOfBoundsException","B) NumberFormatException","C) IOException","D) ClassCastException"],"correct":"A) ArrayIndexOutOfBoundsException","explanation":"Array தவறான index access செய்யும் போது வரும்."},
{"question":"Null object reference access செய்யும் போது exception?","options":["A) NullPointerException","B) ArithmeticException","C) IOException","D) ClassNotFoundException"],"correct":"A) NullPointerException","explanation":"Null object member access செய்யும் போது NullPointerException வரும்."},
],

'tanglish': [
{"question":"Java-la exception enna?","options":["A) loop","B) execution error","C) variable","D) function"],"correct":"B) execution error","explanation":"Execution time-la program flow disturb aagum."},
{"question":"Exception handle panna keyword?","options":["A) try","B) catch","C) throw","D) final"],"correct":"A) try","explanation":"try block-la exception varalaam nu code pottu irukom."},
{"question":"Exception catch panna block?","options":["A) try","B) catch","C) finally","D) throw"],"correct":"B) catch","explanation":"catch block try-la throw aana exception handle pannum."},
{"question":"Always run aagura block?","options":["A) try","B) catch","C) finally","D) throw"],"correct":"C) finally","explanation":"finally block elam time run aagum."},
{"question":"Manual-a exception throw panna keyword?","options":["A) throw","B) raise","C) catch","D) handle"],"correct":"A) throw","explanation":"throw keyword use panni exception throw pannuvom."},
{"question":"Handle pannala exception-na enna aagum?","options":["A) program ignore","B) program crash","C) loop continue","D) nothing"],"correct":"B) program crash","explanation":"Unhandled exception program stop aagum."},
{"question":"Multiple catch blocks use panna mudiyuma?","options":["A) illa","B) mudiyum","C) onnu","D) sometimes"],"correct":"B) mudiyum","explanation":"Multiple catch blocks different exceptions handle pannum."},
{"question":"Zero divide panna exception?","options":["A) ArithmeticException","B) NullPointerException","C) IOException","D) ClassNotFoundException"],"correct":"A) ArithmeticException","explanation":"0 divide panna ArithmeticException varum."},
{"question":"Invalid array index access panna exception?","options":["A) ArrayIndexOutOfBoundsException","B) NumberFormatException","C) IOException","D) ClassCastException"],"correct":"A) ArrayIndexOutOfBoundsException","explanation":"Array wrong index access panna varum."},
{"question":"Null object reference access panna exception?","options":["A) NullPointerException","B) ArithmeticException","C) IOException","D) ClassNotFoundException"],"correct":"A) NullPointerException","explanation":"Null object member access panna NullPointerException varum."},
],

'malayalam': [
{"question":"Java-ലുള്ള exception എന്താണ്?","options":["A) Loop","B) Execution സമയത്തിലെ പിഴവ്","C) Variable","D) Function"],"correct":"B) Execution സമയത്തിലെ പിഴവ്","explanation":"Execution-ലെ program flow-നെ block ചെയ്യുന്ന घटना."},
{"question":"Exception handle ചെയ്യാൻ keyword?","options":["A) try","B) catch","C) throw","D) final"],"correct":"A) try","explanation":"try block exception throw ചെയ്യാവുന്ന code wrap ചെയ്യുന്നു."},
{"question":"Exception catch ചെയ്യുന്നത് ഏത് block?","options":["A) try","B) catch","C) finally","D) throw"],"correct":"B) catch","explanation":"catch block try-ൽ thrown exception handle ചെയ്യുന്നു."},
{"question":"എപ്പോഴും run ആകുന്ന block?","options":["A) try","B) catch","C) finally","D) throw"],"correct":"C) finally","explanation":"finally block എപ്പോഴും run ചെയ്യും."},
{"question":"Manual ആയി exception throw ചെയ്യാൻ keyword?","options":["A) throw","B) raise","C) catch","D) handle"],"correct":"A) throw","explanation":"throw keyword ഉപയോഗിച്ച് exception throw ചെയ്യാം."},
{"question":"Exception handle ചെയ്യാതിരിക്കുകയാണെങ്കിൽ?","options":["A) program ignore ചെയ്യും","B) program crash ആയും","C) loop continue ആയും","D) ഒന്നും സംഭവിക്കില്ല"],"correct":"B) program crash ആയും","explanation":"Unhandled exception program stop ചെയ്യും."},
{"question":"Multiple catch blocks ഉപയോഗിക്കാമോ?","options":["A) ഇല്ല","B) ഉണ്ട്","C) ഒന്ന് മാത്രം","D) ചിലപ്പോൾ"],"correct":"B) ഉണ്ട്","explanation":"Multiple catch blocks വ്യത്യസ്ത exceptions handle ചെയ്യും."},
{"question":"Zero divide ചെയ്താൽ exception?","options":["A) ArithmeticException","B) NullPointerException","C) IOException","D) ClassNotFoundException"],"correct":"A) ArithmeticException","explanation":"0 divide ചെയ്താൽ ArithmeticException വരും."},
{"question":"Invalid array index access ചെയ്താൽ exception?","options":["A) ArrayIndexOutOfBoundsException","B) NumberFormatException","C) IOException","D) ClassCastException"],"correct":"A) ArrayIndexOutOfBoundsException","explanation":"Array-ലോ തെറ്റായ index access ചെയ്താൽ വരും."},
{"question":"Null object reference access ചെയ്താൽ exception?","options":["A) NullPointerException","B) ArithmeticException","C) IOException","D) ClassNotFoundException"],"correct":"A) NullPointerException","explanation":"Null object-ന്റെ member access ചെയ്താൽ NullPointerException വരും."},
],},#exception handling

'Collections Framework':{
'english': [
{"question":"What is the Java Collections Framework?","options":["A) A set of classes and interfaces for storing groups of objects","B) A GUI library","C) Networking API","D) File handling API"],"correct":"A) A set of classes and interfaces for storing groups of objects","explanation":"It provides standard data structures and algorithms."},
{"question":"Which interface implements a resizable array in Java?","options":["A) List","B) Set","C) Map","D) Queue"],"correct":"A) List","explanation":"ArrayList implements List interface for resizable arrays."},
{"question":"Which collection does not allow duplicate elements?","options":["A) List","B) Set","C) Map","D) Queue"],"correct":"B) Set","explanation":"Set ensures unique elements only."},
{"question":"Which collection stores key-value pairs?","options":["A) List","B) Set","C) Map","D) Queue"],"correct":"C) Map","explanation":"Map stores data as key-value pairs."},
{"question":"Which collection maintains insertion order?","options":["A) HashSet","B) LinkedHashSet","C) TreeSet","D) PriorityQueue"],"correct":"B) LinkedHashSet","explanation":"LinkedHashSet maintains insertion order."},
{"question":"Which collection is sorted automatically?","options":["A) HashSet","B) TreeSet","C) ArrayList","D) LinkedList"],"correct":"B) TreeSet","explanation":"TreeSet sorts elements in natural order."},
{"question":"Which interface allows duplicate elements and maintains order?","options":["A) List","B) Set","C) Map","D) Queue"],"correct":"A) List","explanation":"List can have duplicates and preserves order."},
{"question":"Which class is synchronized in Java Collections?","options":["A) Vector","B) ArrayList","C) LinkedList","D) HashSet"],"correct":"A) Vector","explanation":"Vector is synchronized, unlike ArrayList."},
{"question":"Which method is used to get the size of a collection?","options":["A) length()","B) size()","C) count()","D) lengthOf()"],"correct":"B) size()","explanation":"size() method returns number of elements in collection."},
{"question":"Which collection allows insertion, deletion, and retrieval in FIFO order?","options":["A) Stack","B) Queue","C) Set","D) Map"],"correct":"B) Queue","explanation":"Queue follows First-In-First-Out order."},
],

'hindi': [
{"question":"Java Collections Framework क्या है?","options":["A) Objects के समूह को store करने के लिए classes और interfaces का set","B) GUI library","C) Networking API","D) File handling API"],"correct":"A) Objects के समूह को store करने के लिए classes और interfaces का set","explanation":"यह standard data structures और algorithms provide करता है।"},
{"question":"Resizable array implement करने वाला interface कौनसा है?","options":["A) List","B) Set","C) Map","D) Queue"],"correct":"A) List","explanation":"ArrayList List interface implement करता है।"},
{"question":"कौनसी collection duplicate elements allow नहीं करती?","options":["A) List","B) Set","C) Map","D) Queue"],"correct":"B) Set","explanation":"Set में केवल unique elements होते हैं।"},
{"question":"कौनसी collection key-value pair store करती है?","options":["A) List","B) Set","C) Map","D) Queue"],"correct":"C) Map","explanation":"Map में key-value pair store होते हैं।"},
{"question":"कौनसी collection insertion order maintain करती है?","options":["A) HashSet","B) LinkedHashSet","C) TreeSet","D) PriorityQueue"],"correct":"B) LinkedHashSet","explanation":"LinkedHashSet insertion order preserve करता है।"},
{"question":"कौनसी collection automatically sort होती है?","options":["A) HashSet","B) TreeSet","C) ArrayList","D) LinkedList"],"correct":"B) TreeSet","explanation":"TreeSet elements को natural order में sort करता है।"},
{"question":"कौनसा interface duplicates allow करता है और order maintain करता है?","options":["A) List","B) Set","C) Map","D) Queue"],"correct":"A) List","explanation":"List duplicates allow करता है और order preserve करता है।"},
{"question":"Java Collections में synchronized class कौनसी है?","options":["A) Vector","B) ArrayList","C) LinkedList","D) HashSet"],"correct":"A) Vector","explanation":"Vector synchronized है, ArrayList नहीं।"},
{"question":"Collection का size पता करने के लिए method?","options":["A) length()","B) size()","C) count()","D) lengthOf()"],"correct":"B) size()","explanation":"size() method elements की संख्या return करता है।"},
{"question":"कौनसी collection FIFO order में elements handle करती है?","options":["A) Stack","B) Queue","C) Set","D) Map"],"correct":"B) Queue","explanation":"Queue First-In-First-Out order follow करती है।"},
],

'tamil': [
{"question":"Java Collections Framework என்ன?","options":["A) Objects-ஐ சேமிக்க classes & interfaces set","B) GUI library","C) Networking API","D) File handling API"],"correct":"A) Objects-ஐ சேமிக்க classes & interfaces set","explanation":"Standard data structures & algorithms supply செய்யும்."},
{"question":"Resizable array implement செய்யும் interface யார்?","options":["A) List","B) Set","C) Map","D) Queue"],"correct":"A) List","explanation":"ArrayList List interface implement செய்கிறது."},
{"question":"Duplicate elements allow செய்யாத collection?","options":["A) List","B) Set","C) Map","D) Queue"],"correct":"B) Set","explanation":"Set unique elements மட்டும் கொண்டுள்ளது."},
{"question":"Key-value pairs சேமிக்கும் collection?","options":["A) List","B) Set","C) Map","D) Queue"],"correct":"C) Map","explanation":"Map key-value pair சேமிக்கும்."},
{"question":"Insertion order maintain செய்யும் collection?","options":["A) HashSet","B) LinkedHashSet","C) TreeSet","D) PriorityQueue"],"correct":"B) LinkedHashSet","explanation":"LinkedHashSet insertion order maintain செய்கிறது."},
{"question":"Automatic-a sort ஆகும் collection?","options":["A) HashSet","B) TreeSet","C) ArrayList","D) LinkedList"],"correct":"B) TreeSet","explanation":"TreeSet elements-ஐ natural order-ல் sort செய்கிறது."},
{"question":"Duplicate elements allow & order maintain செய்யும் interface?","options":["A) List","B) Set","C) Map","D) Queue"],"correct":"A) List","explanation":"List duplicates allow செய்கிறது & order maintain செய்கிறது."},
{"question":"Synchronized class யார்?","options":["A) Vector","B) ArrayList","C) LinkedList","D) HashSet"],"correct":"A) Vector","explanation":"Vector synchronized ஆகும், ArrayList அல்ல."},
{"question":"Collection size method?","options":["A) length()","B) size()","C) count()","D) lengthOf()"],"correct":"B) size()","explanation":"size() elements எண்ணிக்கை return செய்கிறது."},
{"question":"FIFO order follow செய்யும் collection?","options":["A) Stack","B) Queue","C) Set","D) Map"],"correct":"B) Queue","explanation":"Queue First-In-First-Out order follow செய்கிறது."},
],

'tanglish': [
{"question":"Java Collections Framework enna?","options":["A) Objects store panna classes & interfaces set","B) GUI library","C) Networking API","D) File handling API"],"correct":"A) Objects store panna classes & interfaces set","explanation":"Standard data structures & algorithms provide pannum."},
{"question":"Resizable array implement panna interface?","options":["A) List","B) Set","C) Map","D) Queue"],"correct":"A) List","explanation":"ArrayList List interface implement pannum."},
{"question":"Duplicate elements allow pannatha collection?","options":["A) List","B) Set","C) Map","D) Queue"],"correct":"B) Set","explanation":"Set unique elements mattum."},
{"question":"Key-value pair store panna collection?","options":["A) List","B) Set","C) Map","D) Queue"],"correct":"C) Map","explanation":"Map key-value pair store pannum."},
{"question":"Insertion order maintain panna collection?","options":["A) HashSet","B) LinkedHashSet","C) TreeSet","D) PriorityQueue"],"correct":"B) LinkedHashSet","explanation":"LinkedHashSet insertion order maintain pannum."},
{"question":"Automatic sort aagura collection?","options":["A) HashSet","B) TreeSet","C) ArrayList","D) LinkedList"],"correct":"B) TreeSet","explanation":"TreeSet elements natural order-la sort aagum."},
{"question":"Duplicate allow & order maintain panna interface?","options":["A) List","B) Set","C) Map","D) Queue"],"correct":"A) List","explanation":"List duplicates allow pannum & order maintain pannum."},
{"question":"Synchronized class?","options":["A) Vector","B) ArrayList","C) LinkedList","D) HashSet"],"correct":"A) Vector","explanation":"Vector synchronized, ArrayList illa."},
{"question":"Collection size method?","options":["A) length()","B) size()","C) count()","D) lengthOf()"],"correct":"B) size()","explanation":"size() elements count return pannum."},
{"question":"FIFO order follow panna collection?","options":["A) Stack","B) Queue","C) Set","D) Map"],"correct":"B) Queue","explanation":"Queue First-In-First-Out order follow pannum."},
],

'malayalam': [
{"question":"Java Collections Framework എന്താണ്?","options":["A) Objects-നെ store ചെയ്യാനുള്ള classes & interfaces set","B) GUI library","C) Networking API","D) File handling API"],"correct":"A) Objects-നെ store ചെയ്യാനുള്ള classes & interfaces set","explanation":"Standard data structures & algorithms provide ചെയ്യുന്നു."},
{"question":"Resizable array implement ചെയ്യുന്ന interface?","options":["A) List","B) Set","C) Map","D) Queue"],"correct":"A) List","explanation":"ArrayList List interface implement ചെയ്യുന്നു."},
{"question":"Duplicate elements allow ചെയ്യാത്ത collection?","options":["A) List","B) Set","C) Map","D) Queue"],"correct":"B) Set","explanation":"Set-ല് unique elements മാത്രം ഉള്ളൂ."},
{"question":"Key-value pair store ചെയ്യുന്ന collection?","options":["A) List","B) Set","C) Map","D) Queue"],"correct":"C) Map","explanation":"Map key-value pair store ചെയ്യുന്നു."},
{"question":"Insertion order maintain ചെയ്യുന്ന collection?","options":["A) HashSet","B) LinkedHashSet","C) TreeSet","D) PriorityQueue"],"correct":"B) LinkedHashSet","explanation":"LinkedHashSet insertion order maintain ചെയ്യുന്നു."},
{"question":"Automatically sort ചെയ്യുന്ന collection?","options":["A) HashSet","B) TreeSet","C) ArrayList","D) LinkedList"],"correct":"B) TreeSet","explanation":"TreeSet elements natural order-ല് sort ചെയ്യുന്നു."},
{"question":"Duplicate allow & order maintain ചെയ്യുന്ന interface?","options":["A) List","B) Set","C) Map","D) Queue"],"correct":"A) List","explanation":"List duplicates allow ചെയ്യുന്നു & order maintain ചെയ്യുന്നു."},
{"question":"Synchronized class?","options":["A) Vector","B) ArrayList","C) LinkedList","D) HashSet"],"correct":"A) Vector","explanation":"Vector synchronized ആണ്, ArrayList അല്ല."},
{"question":"Collection size method?","options":["A) length()","B) size()","C) count()","D) lengthOf()"],"correct":"B) size()","explanation":"size() elements count return ചെയ്യുന്നു."},
{"question":"FIFO order follow ചെയ്യുന്ന collection?","options":["A) Stack","B) Queue","C) Set","D) Map"],"correct":"B) Queue","explanation":"Queue First-In-First-Out order follow ചെയ്യുന്നു."},
],},#collection frameworks over

'Multithreading Basics':{
'english': [
{"question":"What is multithreading in Java?","options":["A) Running multiple threads concurrently","B) Running single thread","C) Running multiple programs","D) Only memory management"],"correct":"A) Running multiple threads concurrently","explanation":"Multithreading allows multiple threads to run in parallel."},
{"question":"Which class is used to create a thread by extending?","options":["A) Thread","B) Runnable","C) Object","D) Executor"],"correct":"A) Thread","explanation":"By extending Thread class, a new thread can be created."},
{"question":"Which interface is implemented to create a thread?","options":["A) Runnable","B) Callable","C) Serializable","D) Cloneable"],"correct":"A) Runnable","explanation":"Runnable interface provides run() method to define thread logic."},
{"question":"Which method starts a thread?","options":["A) start()","B) run()","C) execute()","D) init()"],"correct":"A) start()","explanation":"start() internally calls run() and begins execution."},
{"question":"Which method is used to pause a thread?","options":["A) sleep()","B) wait()","C) join()","D) notify()"],"correct":"A) sleep()","explanation":"sleep() pauses thread for given time."},
{"question":"What is a daemon thread?","options":["A) Background thread","B) Main thread","C) UI thread","D) Worker thread"],"correct":"A) Background thread","explanation":"Daemon threads run in background and terminate when all non-daemon threads finish."},
{"question":"Which method waits for a thread to finish?","options":["A) join()","B) sleep()","C) yield()","D) start()"],"correct":"A) join()","explanation":"join() makes current thread wait until the thread finishes."},
{"question":"Which method is used to stop a thread safely?","options":["A) interrupt()","B) stop()","C) destroy()","D) exit()"],"correct":"A) interrupt()","explanation":"stop() is deprecated; interrupt() is used for safe termination."},
{"question":"Which is true about thread priority?","options":["A) 1 (min) to 10 (max)","B) 0 to 5","C) -1 to 1","D) 1 to 100"],"correct":"A) 1 (min) to 10 (max)","explanation":"Java thread priority ranges from 1 to 10."},
{"question":"Which method allows a thread to give up CPU voluntarily?","options":["A) yield()","B) sleep()","C) wait()","D) notify()"],"correct":"A) yield()","explanation":"yield() pauses current thread and allows other threads to execute."},
],

'hindi': [
{"question":"Java में multithreading क्या है?","options":["A) Multiple threads का concurrent execution","B) Single thread execution","C) Multiple programs execute करना","D) केवल memory management"],"correct":"A) Multiple threads का concurrent execution","explanation":"Multithreading से कई threads एक साथ चल सकते हैं।"},
{"question":"Thread बनाने के लिए कौनसा class extend करते हैं?","options":["A) Thread","B) Runnable","C) Object","D) Executor"],"correct":"A) Thread","explanation":"Thread class extend करके नया thread बनाया जा सकता है।"},
{"question":"Thread बनाने के लिए कौनसा interface implement करना पड़ता है?","options":["A) Runnable","B) Callable","C) Serializable","D) Cloneable"],"correct":"A) Runnable","explanation":"Runnable interface run() method provide करता है।"},
{"question":"Thread शुरू करने के लिए कौनसा method use होता है?","options":["A) start()","B) run()","C) execute()","D) init()"],"correct":"A) start()","explanation":"start() internally run() call करता है और execution शुरू करता है।"},
{"question":"Thread को pause करने के लिए कौनसा method use होता है?","options":["A) sleep()","B) wait()","C) join()","D) notify()"],"correct":"A) sleep()","explanation":"sleep() thread को दिए गए समय तक रोकता है।"},
{"question":"Daemon thread क्या है?","options":["A) Background thread","B) Main thread","C) UI thread","D) Worker thread"],"correct":"A) Background thread","explanation":"Daemon thread background में चलता है और सभी non-daemon threads के खत्म होने पर terminate होता है।"},
{"question":"कौनसा method thread खत्म होने तक wait करता है?","options":["A) join()","B) sleep()","C) yield()","D) start()"],"correct":"A) join()","explanation":"join() current thread को wait कराता है।"},
{"question":"Thread को safely stop करने के लिए कौनसा method use होता है?","options":["A) interrupt()","B) stop()","C) destroy()","D) exit()"],"correct":"A) interrupt()","explanation":"stop() deprecated है, interrupt() safe termination के लिए use होता है।"},
{"question":"Thread priority के बारे में सही statement क्या है?","options":["A) 1 (min) to 10 (max)","B) 0 to 5","C) -1 to 1","D) 1 to 100"],"correct":"A) 1 (min) to 10 (max)","explanation":"Java में thread priority 1 से 10 तक होती है।"},
{"question":"कौनसा method thread को CPU छोड़ने के लिए allow करता है?","options":["A) yield()","B) sleep()","C) wait()","D) notify()"],"correct":"A) yield()","explanation":"yield() current thread को pause कर other threads को execute करने देता है।"},
],

'tamil': [
{"question":"Java-ல் multithreading என்பது?","options":["A) பல threads concurrent-a run ஆகும்","B) Single thread run","C) Multiple programs run","D) Only memory management"],"correct":"A) பல threads concurrent-a run ஆகும்","explanation":"Multithreading மூலம் பல threads parallel-a run ஆகும்."},
{"question":"Thread உருவாக்க Thread-ஐ extend செய்யும் class?","options":["A) Thread","B) Runnable","C) Object","D) Executor"],"correct":"A) Thread","explanation":"Thread class extend செய்து புதிய thread உருவாக்கலாம்."},
{"question":"Thread உருவாக்க implement செய்யும் interface?","options":["A) Runnable","B) Callable","C) Serializable","D) Cloneable"],"correct":"A) Runnable","explanation":"Runnable interface run() method provide செய்கிறது."},
{"question":"Thread தொடங்க method?","options":["A) start()","B) run()","C) execute()","D) init()"],"correct":"A) start()","explanation":"start() run() call செய்து execution start செய்கிறது."},
{"question":"Thread pause செய்ய method?","options":["A) sleep()","B) wait()","C) join()","D) notify()"],"correct":"A) sleep()","explanation":"sleep() thread-ஐ குறிப்பிட்ட நேரம் நிறுத்தும்."},
{"question":"Daemon thread என்ன?","options":["A) Background thread","B) Main thread","C) UI thread","D) Worker thread"],"correct":"A) Background thread","explanation":"Daemon thread background-ல் run ஆகும், non-daemon threads முடிந்ததும் stop ஆகும்."},
{"question":"Thread முடியும் வரை wait செய்ய method?","options":["A) join()","B) sleep()","C) yield()","D) start()"],"correct":"A) join()","explanation":"join() current thread-ஐ wait செய்கிறது."},
{"question":"Thread safely stop செய்ய method?","options":["A) interrupt()","B) stop()","C) destroy()","D) exit()"],"correct":"A) interrupt()","explanation":"stop() deprecated, interrupt() use பண்ணலாம்."},
{"question":"Thread priority பற்றி உண்மை statement?","options":["A) 1 (min) to 10 (max)","B) 0 to 5","C) -1 to 1","D) 1 to 100"],"correct":"A) 1 (min) to 10 (max)","explanation":"Java threads-க்கு priority 1 முதல் 10 வரை."},
{"question":"Thread voluntary-a CPU விட method?","options":["A) yield()","B) sleep()","C) wait()","D) notify()"],"correct":"A) yield()","explanation":"yield() current thread-ஐ pause செய்து மற்ற threads execute செய்ய அனுமதிக்கும்."},
],

'tanglish': [
{"question":"Java-la multithreading enna?","options":["A) Multiple threads concurrent-a run","B) Single thread run","C) Multiple programs run","D) Only memory management"],"correct":"A) Multiple threads concurrent-a run","explanation":"Multithreading allows multiple threads to run parallel-la."},
{"question":"Thread create panna class extend pannum?","options":["A) Thread","B) Runnable","C) Object","D) Executor"],"correct":"A) Thread","explanation":"Thread class extend pannitu new thread create pannalam."},
{"question":"Thread create panna interface implement pannum?","options":["A) Runnable","B) Callable","C) Serializable","D) Cloneable"],"correct":"A) Runnable","explanation":"Runnable interface run() method provide pannum."},
{"question":"Thread start panna method?","options":["A) start()","B) run()","C) execute()","D) init()"],"correct":"A) start()","explanation":"start() run() call pannum and execution start aagum."},
{"question":"Thread pause panna method?","options":["A) sleep()","B) wait()","C) join()","D) notify()"],"correct":"A) sleep()","explanation":"sleep() thread-ā pause pannum for given time."},
{"question":"Daemon thread enna?","options":["A) Background thread","B) Main thread","C) UI thread","D) Worker thread"],"correct":"A) Background thread","explanation":"Daemon thread background-la run aagum & non-daemon threads mudinjaal stop aagum."},
{"question":"Thread finish aagum vara wait panna method?","options":["A) join()","B) sleep()","C) yield()","D) start()"],"correct":"A) join()","explanation":"join() current thread wait pannum until target thread finish aagum."},
{"question":"Thread safely stop panna method?","options":["A) interrupt()","B) stop()","C) destroy()","D) exit()"],"correct":"A) interrupt()","explanation":"stop() deprecated, interrupt() safe termination-ku."},
{"question":"Thread priority correct range?","options":["A) 1 to 10","B) 0 to 5","C) -1 to 1","D) 1 to 100"],"correct":"A) 1 to 10","explanation":"Java thread priority 1-10 range-la irukum."},
{"question":"Thread voluntary CPU release panna method?","options":["A) yield()","B) sleep()","C) wait()","D) notify()"],"correct":"A) yield()","explanation":"yield() current thread pause pannitu other threads execute pannum."},
],

'malayalam': [
{"question":"Java-യിൽ multithreading എന്താണ്?","options":["A) Multiple threads concurrent run ചെയ്യുന്നു","B) Single thread run","C) Multiple programs run","D) Only memory management"],"correct":"A) Multiple threads concurrent run ചെയ്യുന്നു","explanation":"Multithreading allows multiple threads parallel run ചെയ്യാൻ."},
{"question":"Thread സൃഷ്ടിക്കാൻ ഏത് class extend ചെയ്യുന്നു?","options":["A) Thread","B) Runnable","C) Object","D) Executor"],"correct":"A) Thread","explanation":"Thread class extend ചെയ്തു new thread സൃഷ്ടിക്കാം."},
{"question":"Thread സൃഷ്ടിക്കാൻ ഏത് interface implement ചെയ്യുന്നു?","options":["A) Runnable","B) Callable","C) Serializable","D) Cloneable"],"correct":"A) Runnable","explanation":"Runnable interface run() method provide ചെയ്യുന്നു."},
{"question":"Thread start ചെയ്യാൻ method?","options":["A) start()","B) run()","C) execute()","D) init()"],"correct":"A) start()","explanation":"start() run() call ചെയ്തു execution start ചെയ്യും."},
{"question":"Thread pause ചെയ്യാൻ method?","options":["A) sleep()","B) wait()","C) join()","D) notify()"],"correct":"A) sleep()","explanation":"sleep() thread-നെ given time-ൽ pause ചെയ്യും."},
{"question":"Daemon thread എന്താണ്?","options":["A) Background thread","B) Main thread","C) UI thread","D) Worker thread"],"correct":"A) Background thread","explanation":"Daemon threads background-ൽ run ചെയ്യുന്നു & non-daemon threads finish ആകുമ്പോൾ stop ചെയ്യും."},
{"question":"Thread finish ആകുന്നത് വരെ wait ചെയ്യാൻ method?","options":["A) join()","B) sleep()","C) yield()","D) start()"],"correct":"A) join()","explanation":"join() current thread wait ചെയ്യുന്നു until target thread finish ആകും."},
{"question":"Thread safe-ആ ആയി stop ചെയ്യാൻ method?","options":["A) interrupt()","B) stop()","C) destroy()","D) exit()"],"correct":"A) interrupt()","explanation":"stop() deprecated ആണ്, interrupt() safe termination-കായി ഉപയോഗിക്കുന്നു."},
{"question":"Thread priority range?","options":["A) 1 to 10","B) 0 to 5","C) -1 to 1","D) 1 to 100"],"correct":"A) 1 to 10","explanation":"Java threads-ന്റെ priority 1-10 range-ൽ ആണ്."},
{"question":"Thread voluntary CPU release method?","options":["A) yield()","B) sleep()","C) wait()","D) notify()"],"correct":"A) yield()","explanation":"yield() current thread pause ചെയ്ത് other threads run ചെയ്യാൻ അനുവദിക്കുന്നു."},
],#multi threading over

}
},  # end java topics

# ─────────────────── AI ────────────────────────────────────────
'ai': {
'What is AI?': {
'english': [
  {"question":"What does AI stand for?","options":["A) Automated Interface","B) Artificial Intelligence","C) Automatic Integration","D) Advanced Internet"],"correct":"B) Artificial Intelligence","explanation":"AI = Artificial Intelligence."},
  {"question":"Who coined the term AI?","options":["A) Alan Turing","B) John McCarthy","C) Elon Musk","D) Bill Gates"],"correct":"B) John McCarthy","explanation":"John McCarthy coined AI in 1956."},
  {"question":"AI enables machines to?","options":["A) Only calculate","B) Learn and make decisions","C) Only store data","D) Only display output"],"correct":"B) Learn and make decisions","explanation":"AI lets machines learn, reason, and decide."},
  {"question":"Which is an AI application?","options":["A) Calculator","B) Alarm clock","C) Voice assistant","D) Light bulb"],"correct":"C) Voice assistant","explanation":"Voice assistants use NLP and ML."},
  {"question":"AI stands for simulating?","options":["A) Computer programs","B) Human intelligence","C) Machine hardware","D) Network protocols"],"correct":"B) Human intelligence","explanation":"AI simulates human intelligence in machines."},
  {"question":"Which branch is NOT part of AI?","options":["A) Machine Learning","B) Computer Vision","C) Spreadsheet design","D) NLP"],"correct":"C) Spreadsheet design","explanation":"Spreadsheet design is not an AI branch."},
  {"question":"What is Narrow AI?","options":["A) AI that does everything","B) AI designed for a specific task","C) Robotic hardware","D) A programming language"],"correct":"B) AI designed for a specific task","explanation":"Narrow AI handles one specific type of task."},
  {"question":"What does Deep Learning use?","options":["A) Simple rules","B) Layered neural networks","C) SQL databases","D) Expert systems"],"correct":"B) Layered neural networks","explanation":"Deep Learning uses multiple neural network layers."},
  {"question":"Which AI test measures intelligence?","options":["A) SAT","B) IQ Test","C) Turing Test","D) Benchmark"],"correct":"C) Turing Test","explanation":"The Turing Test measures machine intelligence."},
  {"question":"AI was coined in which year?","options":["A) 1945","B) 1956","C) 1970","D) 1985"],"correct":"B) 1956","explanation":"John McCarthy coined AI in 1956 at Dartmouth."},
  {"question":"Which company made ChatGPT?","options":["A) Google","B) Meta","C) OpenAI","D) Microsoft"],"correct":"C) OpenAI","explanation":"ChatGPT was developed by OpenAI."},
  {"question":"AI uses data to?","options":["A) Delete files","B) Find patterns and make predictions","C) Format disks","D) Only display charts"],"correct":"B) Find patterns and make predictions","explanation":"AI learns from data to find patterns."},
],
'tamil': [
  {"question":"AI-ன் full form என்ன?","options":["A) Automated Interface","B) Artificial Intelligence","C) Automatic Integration","D) Advanced Internet"],"correct":"B) Artificial Intelligence","explanation":"AI = Artificial Intelligence (செயற்கை நுண்ணறிவு)."},
  {"question":"AI என்ற வார்த்தை யார் உருவாக்கினார்?","options":["A) Alan Turing","B) John McCarthy","C) Elon Musk","D) Bill Gates"],"correct":"B) John McCarthy","explanation":"John McCarthy 1956-ல் AI என்ற வார்த்தை உருவாக்கினார்."},
  {"question":"AI machines-ஐ என்ன செய்ய வைக்கிறது?","options":["A) கணக்கிட மட்டும்","B) கற்று முடிவு எடுக்க","C) Data சேமிக்க மட்டும்","D) Output காட்ட மட்டும்"],"correct":"B) கற்று முடிவு எடுக்க","explanation":"AI machines-ஐ கற்க, reason செய்ய, decide செய்ய வைக்கிறது."},
  {"question":"AI application எது?","options":["A) Calculator","B) Alarm clock","C) Voice assistant","D) Light bulb"],"correct":"C) Voice assistant","explanation":"Voice assistants NLP மற்றும் ML பயன்படுத்துகின்றன."},
  {"question":"AI என்ன simulate செய்கிறது?","options":["A) Computer programs","B) Human intelligence","C) Machine hardware","D) Network protocols"],"correct":"B) Human intelligence","explanation":"AI machines-ல் human intelligence simulate செய்கிறது."},
  {"question":"AI-ன் branch இல்லாதது?","options":["A) Machine Learning","B) Computer Vision","C) Spreadsheet design","D) NLP"],"correct":"C) Spreadsheet design","explanation":"Spreadsheet design AI branch இல்லை."},
  {"question":"Narrow AI என்றால் என்ன?","options":["A) எல்லாவற்றையும் செய்யும் AI","B) ஒரு குறிப்பிட்ட task-க்கான AI","C) Robotic hardware","D) Programming language"],"correct":"B) ஒரு குறிப்பிட்ட task-க்கான AI","explanation":"Narrow AI ஒரு specific task handle செய்யும்."},
  {"question":"Deep Learning என்ன பயன்படுத்துகிறது?","options":["A) Simple rules","B) Layered neural networks","C) SQL databases","D) Expert systems"],"correct":"B) Layered neural networks","explanation":"Deep Learning multiple neural network layers பயன்படுத்துகிறது."},
  {"question":"AI intelligence அளவிட எந்த test?","options":["A) SAT","B) IQ Test","C) Turing Test","D) Benchmark"],"correct":"C) Turing Test","explanation":"Turing Test machine intelligence அளவிடுகிறது."},
  {"question":"AI என்ற வார்த்தை எந்த ஆண்டு உருவானது?","options":["A) 1945","B) 1956","C) 1970","D) 1985"],"correct":"B) 1956","explanation":"John McCarthy 1956-ல் Dartmouth-ல் AI உருவாக்கினார்."},
  {"question":"ChatGPT-ஐ உருவாக்கியது?","options":["A) Google","B) Meta","C) OpenAI","D) Microsoft"],"correct":"C) OpenAI","explanation":"ChatGPT-ஐ OpenAI உருவாக்கியது."},
  {"question":"AI data பயன்படுத்தி என்ன செய்கிறது?","options":["A) Files delete செய்யும்","B) Patterns கண்டு predictions செய்யும்","C) Disks format செய்யும்","D) Charts காட்டும்"],"correct":"B) Patterns கண்டு predictions செய்யும்","explanation":"AI data-ல் இருந்து patterns கற்று predictions செய்யும்."},
],
'tanglish': [
  {"question":"AI-oda full form enna?","options":["A) Automated Interface","B) Artificial Intelligence","C) Automatic Integration","D) Advanced Internet"],"correct":"B) Artificial Intelligence","explanation":"AI = Artificial Intelligence."},
  {"question":"AI nu peru vachinathu yaar?","options":["A) Alan Turing","B) John McCarthy","C) Elon Musk","D) Bill Gates"],"correct":"B) John McCarthy","explanation":"John McCarthy 1956-la AI nu peru vachinaaru."},
  {"question":"AI machines-a enna seyyra vaikkum?","options":["A) Calculation mattum","B) Kalluthu decision edukka","C) Data store mattum","D) Output kaattu mattum"],"correct":"B) Kalluthu decision edukka","explanation":"AI machines-a kallukka, reason panna, decide panna vaikkum."},
  {"question":"AI application ethu?","options":["A) Calculator","B) Alarm clock","C) Voice assistant","D) Light bulb"],"correct":"C) Voice assistant","explanation":"Voice assistants NLP-um ML-um use pannum."},
  {"question":"AI enna simulate pannum?","options":["A) Computer programs","B) Human intelligence","C) Machine hardware","D) Network protocols"],"correct":"B) Human intelligence","explanation":"AI machines-la human intelligence simulate pannum."},
  {"question":"AI-oda branch illaadhathu?","options":["A) Machine Learning","B) Computer Vision","C) Spreadsheet design","D) NLP"],"correct":"C) Spreadsheet design","explanation":"Spreadsheet design AI branch illai."},
  {"question":"Narrow AI enna?","options":["A) Ellaamae seyyra AI","B) Oru specific task-ku AI","C) Robotic hardware","D) Programming language"],"correct":"B) Oru specific task-ku AI","explanation":"Narrow AI oru specific task handle pannum."},
  {"question":"Deep Learning enna use pannum?","options":["A) Simple rules","B) Layered neural networks","C) SQL databases","D) Expert systems"],"correct":"B) Layered neural networks","explanation":"Deep Learning multiple neural network layers use pannum."},
  {"question":"AI intelligence measure panna ethu test?","options":["A) SAT","B) IQ Test","C) Turing Test","D) Benchmark"],"correct":"C) Turing Test","explanation":"Turing Test machine intelligence measure pannum."},
  {"question":"AI nu ethu varusham create aacchu?","options":["A) 1945","B) 1956","C) 1970","D) 1985"],"correct":"B) 1956","explanation":"John McCarthy 1956-la Dartmouth-la AI create pannaar."},
  {"question":"ChatGPT-a create pannathu?","options":["A) Google","B) Meta","C) OpenAI","D) Microsoft"],"correct":"C) OpenAI","explanation":"ChatGPT-a OpenAI create pannatu."},
  {"question":"AI data use panni enna pannum?","options":["A) Files delete pannum","B) Patterns kannu predictions pannum","C) Disks format pannum","D) Charts kaattum"],"correct":"B) Patterns kannu predictions pannum","explanation":"AI data-la irundhu patterns kalluthu predictions pannum."},
],
'hindi': [
  {"question":"AI का full form?","options":["A) Automated Interface","B) Artificial Intelligence","C) Automatic Integration","D) Advanced Internet"],"correct":"B) Artificial Intelligence","explanation":"AI = Artificial Intelligence (कृत्रिम बुद्धिमत्ता)."},
  {"question":"AI शब्द किसने बनाया?","options":["A) Alan Turing","B) John McCarthy","C) Elon Musk","D) Bill Gates"],"correct":"B) John McCarthy","explanation":"John McCarthy ने 1956 में AI शब्द बनाया।"},
  {"question":"AI मशीनों को क्या करने में सक्षम बनाता है?","options":["A) सिर्फ गणना","B) सीखना और निर्णय लेना","C) सिर्फ data store","D) सिर्फ output दिखाना"],"correct":"B) सीखना और निर्णय लेना","explanation":"AI मशीनों को सीखने, तर्क और निर्णय लेने में सक्षम बनाता है।"},
  {"question":"AI का उदाहरण?","options":["A) Calculator","B) Alarm clock","C) Voice assistant","D) Light bulb"],"correct":"C) Voice assistant","explanation":"Voice assistants NLP और ML उपयोग करते हैं।"},
  {"question":"AI क्या simulate करता है?","options":["A) Computer programs","B) Human intelligence","C) Machine hardware","D) Network protocols"],"correct":"B) Human intelligence","explanation":"AI मशीनों में human intelligence simulate करता है।"},
  {"question":"AI की branch नहीं है?","options":["A) Machine Learning","B) Computer Vision","C) Spreadsheet design","D) NLP"],"correct":"C) Spreadsheet design","explanation":"Spreadsheet design AI की branch नहीं है।"},
  {"question":"Narrow AI क्या है?","options":["A) सब कुछ करने वाला AI","B) एक specific task के लिए AI","C) Robotic hardware","D) Programming language"],"correct":"B) एक specific task के लिए AI","explanation":"Narrow AI एक specific task handle करता है।"},
  {"question":"Deep Learning क्या उपयोग करता है?","options":["A) Simple rules","B) Layered neural networks","C) SQL databases","D) Expert systems"],"correct":"B) Layered neural networks","explanation":"Deep Learning multiple neural network layers उपयोग करता है।"},
  {"question":"AI intelligence मापने का test?","options":["A) SAT","B) IQ Test","C) Turing Test","D) Benchmark"],"correct":"C) Turing Test","explanation":"Turing Test machine intelligence मापता है।"},
  {"question":"AI शब्द किस वर्ष बना?","options":["A) 1945","B) 1956","C) 1970","D) 1985"],"correct":"B) 1956","explanation":"John McCarthy ने 1956 में Dartmouth में AI बनाया।"},
  {"question":"ChatGPT किसने बनाया?","options":["A) Google","B) Meta","C) OpenAI","D) Microsoft"],"correct":"C) OpenAI","explanation":"ChatGPT OpenAI ने बनाया।"},
  {"question":"AI data से क्या करता है?","options":["A) Files delete करता है","B) Patterns ढूंढ predictions करता है","C) Disks format करता है","D) सिर्फ charts दिखाता है"],"correct":"B) Patterns ढूंढ predictions करता है","explanation":"AI data से patterns सीखकर predictions करता है।"},
],
'malayalam': [
  {"question":"AI-ന്റെ full form?","options":["A) Automated Interface","B) Artificial Intelligence","C) Automatic Integration","D) Advanced Internet"],"correct":"B) Artificial Intelligence","explanation":"AI = Artificial Intelligence (കൃത്രിമ ബുദ്ധി)."},
  {"question":"AI എന്ന പദം ആരാണ് ഉണ്ടാക്കിയത്?","options":["A) Alan Turing","B) John McCarthy","C) Elon Musk","D) Bill Gates"],"correct":"B) John McCarthy","explanation":"John McCarthy 1956-ൽ AI പദം ഉണ്ടാക്കി."},
  {"question":"AI machines-നെ എന്ത് ചെയ്യാൻ സഹായിക്കുന്നു?","options":["A) കണക്കുകൂട്ടൽ മാത്രം","B) പഠിക്കാനും തീരുമാനിക്കാനും","C) Data store ചെയ്യൽ മാത്രം","D) Output കാണിക്കൽ മാത്രം"],"correct":"B) പഠിക്കാനും തീരുമാനിക്കാനും","explanation":"AI machines-നെ പഠിക്കാൻ, reason ചെയ്യാൻ, decide ചെയ്യാൻ സഹായിക്കുന്നു."},
  {"question":"AI application ഏതാണ്?","options":["A) Calculator","B) Alarm clock","C) Voice assistant","D) Light bulb"],"correct":"C) Voice assistant","explanation":"Voice assistants NLP-ഉം ML-ഉം ഉപയോഗിക്കുന്നു."},
  {"question":"AI എന്ത് simulate ചെയ്യുന്നു?","options":["A) Computer programs","B) Human intelligence","C) Machine hardware","D) Network protocols"],"correct":"B) Human intelligence","explanation":"AI machines-ൽ human intelligence simulate ചെയ്യുന്നു."},
  {"question":"AI-ന്റെ branch അല്ലാത്തത്?","options":["A) Machine Learning","B) Computer Vision","C) Spreadsheet design","D) NLP"],"correct":"C) Spreadsheet design","explanation":"Spreadsheet design AI branch അല്ല."},
  {"question":"Narrow AI എന്നാൽ?","options":["A) എല്ലാം ചെയ്യുന്ന AI","B) ഒരു specific task-നായി AI","C) Robotic hardware","D) Programming language"],"correct":"B) ഒരു specific task-നായി AI","explanation":"Narrow AI ഒരു specific task handle ചെയ്യുന്നു."},
  {"question":"Deep Learning എന്ത് ഉപയോഗിക്കുന്നു?","options":["A) Simple rules","B) Layered neural networks","C) SQL databases","D) Expert systems"],"correct":"B) Layered neural networks","explanation":"Deep Learning multiple neural network layers ഉപയോഗിക്കുന്നു."},
  {"question":"AI intelligence അളക്കാൻ ഏത് test?","options":["A) SAT","B) IQ Test","C) Turing Test","D) Benchmark"],"correct":"C) Turing Test","explanation":"Turing Test machine intelligence അളക്കുന്നു."},
  {"question":"AI പദം ഏത് വർഷം ഉണ്ടായി?","options":["A) 1945","B) 1956","C) 1970","D) 1985"],"correct":"B) 1956","explanation":"John McCarthy 1956-ൽ Dartmouth-ൽ AI ഉണ്ടാക്കി."},
  {"question":"ChatGPT ഉണ്ടാക്കിയത്?","options":["A) Google","B) Meta","C) OpenAI","D) Microsoft"],"correct":"C) OpenAI","explanation":"ChatGPT OpenAI ഉണ്ടാക്കി."},
  {"question":"AI data ഉപയോഗിച്ച് എന്ത് ചെയ്യുന്നു?","options":["A) Files delete ചെയ്യുന്നു","B) Patterns കണ്ടെത്തി predictions ചെയ്യുന്നു","C) Disks format ചെയ്യുന്നു","D) Charts കാണിക്കുന്നു"],"correct":"B) Patterns കണ്ടെത്തി predictions ചെയ്യുന്നു","explanation":"AI data-ൽ നിന്ന് patterns പഠിച്ച് predictions ചെയ്യുന്നു."},
],# end What is AI
}, 
'History of AI':
{'english': [
{"question":"Who is known as the father of Artificial Intelligence?","options":["A) Alan Turing","B) John McCarthy","C) Elon Musk","D) Bill Gates"],"correct":"B) John McCarthy","explanation":"John McCarthy coined the term Artificial Intelligence in 1956."},
{"question":"In which conference was AI officially introduced?","options":["A) MIT Conference","B) Harvard Summit","C) Dartmouth Conference","D) Oxford Meeting"],"correct":"C) Dartmouth Conference","explanation":"AI was formally introduced in the Dartmouth Conference in 1956."},
{"question":"Who proposed the Turing Test?","options":["A) John McCarthy","B) Alan Turing","C) Marvin Minsky","D) Charles Babbage"],"correct":"B) Alan Turing","explanation":"Alan Turing proposed the Turing Test in 1950."},
{"question":"What was the first AI program?","options":["A) Logic Theorist","B) Google","C) ChatGPT","D) Windows"],"correct":"A) Logic Theorist","explanation":"Logic Theorist (1955) was one of the first AI programs."},
{"question":"What is AI Winter?","options":["A) Growth of AI","B) Reduction in funding","C) AI invention","D) AI success period"],"correct":"B) Reduction in funding","explanation":"AI Winter refers to the period of reduced funding and interest due to slow progress."},
],

'hindi': [
{"question":"Artificial Intelligence के पिता कौन हैं?","options":["A) Alan Turing","B) John McCarthy","C) Elon Musk","D) Bill Gates"],"correct":"B) John McCarthy","explanation":"John McCarthy ने 1956 में Artificial Intelligence शब्द दिया।"},
{"question":"AI को किस conference में introduce किया गया?","options":["A) MIT Conference","B) Harvard Summit","C) Dartmouth Conference","D) Oxford Meeting"],"correct":"C) Dartmouth Conference","explanation":"AI को 1956 में Dartmouth Conference में introduce किया गया।"},
{"question":"Turing Test किसने propose किया?","options":["A) John McCarthy","B) Alan Turing","C) Marvin Minsky","D) Charles Babbage"],"correct":"B) Alan Turing","explanation":"Alan Turing ने 1950 में Turing Test propose किया।"},
{"question":"पहला AI program कौन सा था?","options":["A) Logic Theorist","B) Google","C) ChatGPT","D) Windows"],"correct":"A) Logic Theorist","explanation":"Logic Theorist (1955) पहला AI program माना जाता है।"},
{"question":"AI Winter क्या है?","options":["A) AI का विकास","B) Funding में कमी","C) AI invention","D) AI success period"],"correct":"B) Funding में कमी","explanation":"AI Winter में funding और interest कम हो जाता है।"},
],

'tamil': [
{"question":"Artificial Intelligence-ன் தந்தை யார்?","options":["A) Alan Turing","B) John McCarthy","C) Elon Musk","D) Bill Gates"],"correct":"B) John McCarthy","explanation":"John McCarthy 1956-ல் AI என்ற சொல்லை உருவாக்கினார்."},
{"question":"AI எங்கு அறிமுகப்படுத்தப்பட்டது?","options":["A) MIT Conference","B) Harvard Summit","C) Dartmouth Conference","D) Oxford Meeting"],"correct":"C) Dartmouth Conference","explanation":"1956 Dartmouth Conference-ல் AI அறிமுகமானது."},
{"question":"Turing Test யார் முன்வைத்தார்?","options":["A) John McCarthy","B) Alan Turing","C) Marvin Minsky","D) Charles Babbage"],"correct":"B) Alan Turing","explanation":"Alan Turing 1950-ல் Turing Test முன்வைத்தார்."},
{"question":"முதல் AI program எது?","options":["A) Logic Theorist","B) Google","C) ChatGPT","D) Windows"],"correct":"A) Logic Theorist","explanation":"Logic Theorist (1955) முதல் AI program."},
{"question":"AI Winter என்றால் என்ன?","options":["A) AI வளர்ச்சி","B) Funding குறைவு","C) AI உருவாக்கம்","D) AI வெற்றி காலம்"],"correct":"B) Funding குறைவு","explanation":"AI Winter என்பது funding குறைந்த காலம்."},
],

'tanglish': [
{"question":"AI-oda father yar?","options":["A) Alan Turing","B) John McCarthy","C) Elon Musk","D) Bill Gates"],"correct":"B) John McCarthy","explanation":"John McCarthy 1956-la Artificial Intelligence term use panninaar."},
{"question":"AI enga introduce aayiduchu?","options":["A) MIT Conference","B) Harvard Summit","C) Dartmouth Conference","D) Oxford Meeting"],"correct":"C) Dartmouth Conference","explanation":"1956 Dartmouth Conference-la AI introduce pannanga."},
{"question":"Turing Test yar propose pannanga?","options":["A) John McCarthy","B) Alan Turing","C) Marvin Minsky","D) Charles Babbage"],"correct":"B) Alan Turing","explanation":"Alan Turing 1950-la Turing Test propose pannaar."},
{"question":"First AI program edhu?","options":["A) Logic Theorist","B) Google","C) ChatGPT","D) Windows"],"correct":"A) Logic Theorist","explanation":"Logic Theorist (1955) first AI program nu solluvaanga."},
{"question":"AI Winter na enna?","options":["A) AI growth","B) Funding kurai","C) AI invention","D) Success period"],"correct":"B) Funding kurai","explanation":"AI Winter-na funding and interest kuraiya irukkum period."},
],

'malayalam': [
{"question":"Artificial Intelligence-ന്റെ പിതാവ് ആരാണ്?","options":["A) Alan Turing","B) John McCarthy","C) Elon Musk","D) Bill Gates"],"correct":"B) John McCarthy","explanation":"John McCarthy 1956-ൽ Artificial Intelligence എന്ന പദം അവതരിപ്പിച്ചു."},
{"question":"AI എവിടെ introduce ചെയ്തു?","options":["A) MIT Conference","B) Harvard Summit","C) Dartmouth Conference","D) Oxford Meeting"],"correct":"C) Dartmouth Conference","explanation":"1956 Dartmouth Conference-ൽ AI അവതരിപ്പിച്ചു."},
{"question":"Turing Test ആരാണ് propose ചെയ്തത്?","options":["A) John McCarthy","B) Alan Turing","C) Marvin Minsky","D) Charles Babbage"],"correct":"B) Alan Turing","explanation":"Alan Turing 1950-ൽ Turing Test propose ചെയ്തു."},
{"question":"ആദ്യ AI program ഏത്?","options":["A) Logic Theorist","B) Google","C) ChatGPT","D) Windows"],"correct":"A) Logic Theorist","explanation":"Logic Theorist (1955) ആദ്യ AI program ആയി കണക്കാക്കുന്നു."},
{"question":"AI Winter എന്താണ്?","options":["A) AI വളർച്ച","B) Funding കുറവ്","C) AI invention","D) Success period"],"correct":"B) Funding കുറവ്","explanation":"AI Winter-ൽ funding & interest കുറയുന്ന കാലഘട്ടമാണ്."},
],},# end history of  AI


'Intelligent Agent':{
'english': [
{"question":"What is an Intelligent Agent?","options":["A) A machine that acts in an environment","B) A programming language","C) A database","D) A network"],"correct":"A) A machine that acts in an environment","explanation":"An intelligent agent perceives environment and takes actions."},
{"question":"What are the main components of an agent?","options":["A) Sensors and Actuators","B) CPU and RAM","C) Input and Output","D) Class and Object"],"correct":"A) Sensors and Actuators","explanation":"Sensors perceive environment, actuators act upon it."},
{"question":"What does a sensor do?","options":["A) Acts on environment","B) Observes environment","C) Stores data","D) Executes code"],"correct":"B) Observes environment","explanation":"Sensors collect information from environment."},
{"question":"What does an actuator do?","options":["A) Observes environment","B) Acts on environment","C) Stores data","D) Calculates"],"correct":"B) Acts on environment","explanation":"Actuators perform actions."},
{"question":"What is a rational agent?","options":["A) Always random","B) Always correct","C) Takes best possible action","D) Works slowly"],"correct":"C) Takes best possible action","explanation":"Rational agent chooses best action based on percepts."},
{"question":"What is an environment in AI?","options":["A) Program","B) Surroundings where agent operates","C) Hardware","D) Software"],"correct":"B) Surroundings where agent operates","explanation":"Environment is where the agent interacts."},
{"question":"Which agent uses condition-action rules?","options":["A) Simple reflex agent","B) Learning agent","C) Utility agent","D) Goal-based agent"],"correct":"A) Simple reflex agent","explanation":"Simple reflex agents act based on current percept."},
{"question":"Which agent uses goals to make decisions?","options":["A) Reflex agent","B) Goal-based agent","C) Random agent","D) Static agent"],"correct":"B) Goal-based agent","explanation":"Goal-based agents act to achieve goals."},
{"question":"Which agent improves performance over time?","options":["A) Learning agent","B) Reflex agent","C) Static agent","D) Manual agent"],"correct":"A) Learning agent","explanation":"Learning agents learn from experience."},
{"question":"PEAS stands for?","options":["A) Performance, Environment, Actuators, Sensors","B) Program, Execution, Action, System","C) Process, Event, Agent, Sensor","D) None"],"correct":"A) Performance, Environment, Actuators, Sensors","explanation":"PEAS is used to define agent environment."},
],

'hindi': [
{"question":"Intelligent Agent क्या है?","options":["A) Environment में कार्य करने वाली मशीन","B) Programming language","C) Database","D) Network"],"correct":"A) Environment में कार्य करने वाली मशीन","explanation":"Agent environment को observe करके action लेता है।"},
{"question":"Agent के मुख्य components क्या हैं?","options":["A) Sensors और Actuators","B) CPU और RAM","C) Input और Output","D) Class और Object"],"correct":"A) Sensors और Actuators","explanation":"Sensors observe करते हैं, actuators action लेते हैं।"},
{"question":"Sensor क्या करता है?","options":["A) Action लेता है","B) Environment observe करता है","C) Data store करता है","D) Code execute करता है"],"correct":"B) Environment observe करता है","explanation":"Sensor environment से information लेता है।"},
{"question":"Actuator क्या करता है?","options":["A) Observe करता है","B) Action लेता है","C) Data store करता है","D) Calculate करता है"],"correct":"B) Action लेता है","explanation":"Actuator action perform करता है।"},
{"question":"Rational agent क्या है?","options":["A) Random काम करता है","B) हमेशा सही होता है","C) Best action लेता है","D) Slow काम करता है"],"correct":"C) Best action लेता है","explanation":"Rational agent best possible decision लेता है।"},
{"question":"AI में environment क्या है?","options":["A) Program","B) Surroundings","C) Hardware","D) Software"],"correct":"B) Surroundings","explanation":"Agent जिस जगह काम करता है वही environment है।"},
{"question":"Condition-action rule वाला agent कौनसा है?","options":["A) Simple reflex agent","B) Learning agent","C) Utility agent","D) Goal-based agent"],"correct":"A) Simple reflex agent","explanation":"Simple reflex agent current condition पर काम करता है।"},
{"question":"Goal use करने वाला agent?","options":["A) Reflex agent","B) Goal-based agent","C) Random agent","D) Static agent"],"correct":"B) Goal-based agent","explanation":"Goal-based agent goal achieve करने के लिए काम करता है।"},
{"question":"Performance improve करने वाला agent?","options":["A) Learning agent","B) Reflex agent","C) Static agent","D) Manual agent"],"correct":"A) Learning agent","explanation":"Learning agent experience से सीखता है।"},
{"question":"PEAS का full form क्या है?","options":["A) Performance, Environment, Actuators, Sensors","B) Program, Execution, Action, System","C) Process, Event, Agent, Sensor","D) None"],"correct":"A) Performance, Environment, Actuators, Sensors","explanation":"PEAS agent environment define करने के लिए use होता है।"},
],

'tamil': [
{"question":"Intelligent Agent என்றால் என்ன?","options":["A) சூழலில் செயல்படும் இயந்திரம்","B) Programming language","C) Database","D) Network"],"correct":"A) சூழலில் செயல்படும் இயந்திரம்","explanation":"Agent environment-ஐ observe செய்து action எடுக்கும்."},
{"question":"Agent-ன் முக்கிய கூறுகள்?","options":["A) Sensors மற்றும் Actuators","B) CPU மற்றும் RAM","C) Input மற்றும் Output","D) Class மற்றும் Object"],"correct":"A) Sensors மற்றும் Actuators","explanation":"Sensors observe செய்கின்றன, actuators action செய்கின்றன."},
{"question":"Sensor என்ன செய்கிறது?","options":["A) Action செய்கிறது","B) Environment observe செய்கிறது","C) Data store செய்கிறது","D) Code run செய்கிறது"],"correct":"B) Environment observe செய்கிறது","explanation":"Sensor environment-இல் இருந்து தகவல் பெறுகிறது."},
{"question":"Actuator என்ன செய்கிறது?","options":["A) Observe செய்கிறது","B) Action செய்கிறது","C) Data store செய்கிறது","D) Calculate செய்கிறது"],"correct":"B) Action செய்கிறது","explanation":"Actuator action செய்கிறது."},
{"question":"Rational agent என்ன?","options":["A) Random","B) Always correct","C) Best action எடுக்கும்","D) Slow"],"correct":"C) Best action எடுக்கும்","explanation":"Rational agent சிறந்த முடிவை எடுக்கும்."},
{"question":"Environment என்றால்?","options":["A) Program","B) சூழல்","C) Hardware","D) Software"],"correct":"B) சூழல்","explanation":"Agent செயல்படும் இடம் environment."},
{"question":"Condition-action rule agent?","options":["A) Simple reflex agent","B) Learning agent","C) Utility agent","D) Goal-based agent"],"correct":"A) Simple reflex agent","explanation":"Current condition-ஐ வைத்து செயல்."},
{"question":"Goal பயன்படுத்தும் agent?","options":["A) Reflex","B) Goal-based","C) Random","D) Static"],"correct":"B) Goal-based","explanation":"Goal அடைய செயல்படும்."},
{"question":"Learning செய்யும் agent?","options":["A) Learning agent","B) Reflex","C) Static","D) Manual"],"correct":"A) Learning agent","explanation":"Experience மூலம் கற்றுக்கொள்கிறது."},
{"question":"PEAS என்றால்?","options":["A) Performance, Environment, Actuators, Sensors","B) Program, Execution, Action, System","C) Process, Event, Agent, Sensor","D) None"],"correct":"A) Performance, Environment, Actuators, Sensors","explanation":"Agent environment define செய்ய பயன்படும்."},
],

'tanglish': [
{"question":"Intelligent Agent enna?","options":["A) Environment-la act pannum machine","B) Programming language","C) Database","D) Network"],"correct":"A) Environment-la act pannum machine","explanation":"Agent environment observe pannitu action edukkum."},
{"question":"Agent main components?","options":["A) Sensors & Actuators","B) CPU & RAM","C) Input & Output","D) Class & Object"],"correct":"A) Sensors & Actuators","explanation":"Sensors observe pannum, actuators act pannum."},
{"question":"Sensor enna pannum?","options":["A) Act pannum","B) Observe pannum","C) Store pannum","D) Execute pannum"],"correct":"B) Observe pannum","explanation":"Environment-la irundhu info edukkum."},
{"question":"Actuator enna pannum?","options":["A) Observe pannum","B) Act pannum","C) Store pannum","D) Calculate pannum"],"correct":"B) Act pannum","explanation":"Action perform pannum."},
{"question":"Rational agent enna?","options":["A) Random","B) Always correct","C) Best action edukkum","D) Slow"],"correct":"C) Best action edukkum","explanation":"Best possible action choose pannum."},
{"question":"Environment enna?","options":["A) Program","B) Surroundings","C) Hardware","D) Software"],"correct":"B) Surroundings","explanation":"Agent operate pannra place."},
{"question":"Condition-action rule agent?","options":["A) Simple reflex","B) Learning","C) Utility","D) Goal-based"],"correct":"A) Simple reflex","explanation":"Current condition base panni act pannum."},
{"question":"Goal use pannra agent?","options":["A) Reflex","B) Goal-based","C) Random","D) Static"],"correct":"B) Goal-based","explanation":"Goal achieve panna work pannum."},
{"question":"Learning improve pannra agent?","options":["A) Learning","B) Reflex","C) Static","D) Manual"],"correct":"A) Learning","explanation":"Experience-la irundhu kathukuvum."},
{"question":"PEAS full form?","options":["A) Performance, Environment, Actuators, Sensors","B) Program, Execution, Action, System","C) Process, Event, Agent, Sensor","D) None"],"correct":"A) Performance, Environment, Actuators, Sensors","explanation":"Agent environment define panna use pannum."},
],

'malayalam': [
{"question":"Intelligent Agent എന്താണ്?","options":["A) Environment-ൽ പ്രവർത്തിക്കുന്ന മെഷീൻ","B) Programming language","C) Database","D) Network"],"correct":"A) Environment-ൽ പ്രവർത്തിക്കുന്ന മെഷീൻ","explanation":"Agent environment observe ചെയ്ത് action എടുക്കുന്നു."},
{"question":"Agent-ന്റെ പ്രധാന ഘടകങ്ങൾ?","options":["A) Sensors & Actuators","B) CPU & RAM","C) Input & Output","D) Class & Object"],"correct":"A) Sensors & Actuators","explanation":"Sensors observe ചെയ്യുന്നു, actuators action ചെയ്യുന്നു."},
{"question":"Sensor എന്ത് ചെയ്യുന്നു?","options":["A) Action","B) Observe","C) Store","D) Execute"],"correct":"B) Observe","explanation":"Environment-ൽ നിന്ന് വിവരം ശേഖരിക്കുന്നു."},
{"question":"Actuator എന്ത് ചെയ്യുന്നു?","options":["A) Observe","B) Action","C) Store","D) Calculate"],"correct":"B) Action","explanation":"Action perform ചെയ്യുന്നു."},
{"question":"Rational agent എന്താണ്?","options":["A) Random","B) Always correct","C) Best action തിരഞ്ഞെടുക്കുന്നു","D) Slow"],"correct":"C) Best action തിരഞ്ഞെടുക്കുന്നു","explanation":"Best possible action തിരഞ്ഞെടുക്കുന്നു."},
{"question":"Environment എന്താണ്?","options":["A) Program","B) Surroundings","C) Hardware","D) Software"],"correct":"B) Surroundings","explanation":"Agent പ്രവർത്തിക്കുന്ന സ്ഥലം."},
{"question":"Condition-action rule ഉപയോഗിക്കുന്ന agent?","options":["A) Simple reflex agent","B) Learning agent","C) Utility agent","D) Goal-based agent"],"correct":"A) Simple reflex agent","explanation":"Current condition അനുസരിച്ച് പ്രവർത്തിക്കുന്നു."},
{"question":"Goal ഉപയോഗിക്കുന്ന agent?","options":["A) Reflex","B) Goal-based","C) Random","D) Static"],"correct":"B) Goal-based","explanation":"Goal achieve ചെയ്യാൻ പ്രവർത്തിക്കുന്നു."},
{"question":"Learning ചെയ്യുന്ന agent?","options":["A) Learning agent","B) Reflex","C) Static","D) Manual"],"correct":"A) Learning agent","explanation":"Experience-ൽ നിന്ന് പഠിക്കുന്നു."},
{"question":"PEAS full form?","options":["A) Performance, Environment, Actuators, Sensors","B) Program, Execution, Action, System","C) Process, Event, Agent, Sensor","D) None"],"correct":"A) Performance, Environment, Actuators, Sensors","explanation":"Agent environment define ചെയ്യാൻ ഉപയോഗിക്കുന്നു."},
],
},
'Search Algorithms':{
   'english': [
{"question":"What is a search algorithm in AI?","options":["A) Finds solution to a problem","B) Stores data","C) Compiles code","D) Runs hardware"],"correct":"A) Finds solution to a problem","explanation":"Search algorithms explore state space to find solutions."},
{"question":"Which search algorithm uses FIFO?","options":["A) DFS","B) BFS","C) A*","D) Greedy"],"correct":"B) BFS","explanation":"Breadth First Search uses queue (FIFO)."},
{"question":"Which search algorithm uses stack (LIFO)?","options":["A) BFS","B) DFS","C) A*","D) UCS"],"correct":"B) DFS","explanation":"Depth First Search uses stack."},
{"question":"Which algorithm guarantees shortest path?","options":["A) DFS","B) BFS","C) Greedy","D) Random"],"correct":"B) BFS","explanation":"BFS finds shortest path in unweighted graph."},
{"question":"What is heuristic function?","options":["A) Exact solution","B) Estimated cost","C) Random guess","D) Final result"],"correct":"B) Estimated cost","explanation":"Heuristic estimates distance to goal."},
{"question":"Which algorithm uses heuristic?","options":["A) BFS","B) DFS","C) A*","D) None"],"correct":"C) A*","explanation":"A* uses heuristic + path cost."},
{"question":"What does A* combine?","options":["A) BFS + DFS","B) Cost + Heuristic","C) Stack + Queue","D) Input + Output"],"correct":"B) Cost + Heuristic","explanation":"A* uses f(n)=g(n)+h(n)."},
{"question":"Which search is uninformed?","options":["A) A*","B) Greedy","C) BFS","D) Heuristic"],"correct":"C) BFS","explanation":"BFS does not use heuristic."},
{"question":"Which search is informed?","options":["A) DFS","B) BFS","C) A*","D) Random"],"correct":"C) A*","explanation":"A* uses heuristic knowledge."},
{"question":"What is state space?","options":["A) Memory","B) All possible states","C) CPU","D) Program"],"correct":"B) All possible states","explanation":"State space is all possible configurations."},
],

'tamil': [
{"question":"AI-ல் search algorithm என்றால் என்ன?","options":["A) பிரச்சனைக்கு தீர்வு கண்டுபிடிக்கும்","B) Data store","C) Code compile","D) Hardware run"],"correct":"A) பிரச்சனைக்கு தீர்வு கண்டுபிடிக்கும்","explanation":"Search algorithm state space-ஐ explore செய்கிறது."},
{"question":"FIFO பயன்படுத்தும் algorithm?","options":["A) DFS","B) BFS","C) A*","D) Greedy"],"correct":"B) BFS","explanation":"BFS queue (FIFO) பயன்படுத்தும்."},
{"question":"Stack (LIFO) பயன்படுத்துவது?","options":["A) BFS","B) DFS","C) A*","D) UCS"],"correct":"B) DFS","explanation":"DFS stack பயன்படுத்தும்."},
{"question":"Shortest path கண்டுபிடிக்கும் algorithm?","options":["A) DFS","B) BFS","C) Greedy","D) Random"],"correct":"B) BFS","explanation":"BFS unweighted graph-ல் shortest path தரும்."},
{"question":"Heuristic function என்றால்?","options":["A) Exact solution","B) Estimated cost","C) Random","D) Final"],"correct":"B) Estimated cost","explanation":"Goal வரை distance estimate செய்கிறது."},
{"question":"Heuristic பயன்படுத்தும் algorithm?","options":["A) BFS","B) DFS","C) A*","D) None"],"correct":"C) A*","explanation":"A* heuristic பயன்படுத்தும்."},
{"question":"A* என்ன combine செய்கிறது?","options":["A) BFS + DFS","B) Cost + Heuristic","C) Stack + Queue","D) Input + Output"],"correct":"B) Cost + Heuristic","explanation":"f(n)=g(n)+h(n)."},
{"question":"Uninformed search எது?","options":["A) A*","B) Greedy","C) BFS","D) Heuristic"],"correct":"C) BFS","explanation":"BFS heuristic இல்லாமல் செய்கிறது."},
{"question":"Informed search எது?","options":["A) DFS","B) BFS","C) A*","D) Random"],"correct":"C) A*","explanation":"A* heuristic பயன்படுத்துகிறது."},
{"question":"State space என்றால்?","options":["A) Memory","B) எல்லா states","C) CPU","D) Program"],"correct":"B) எல்லா states","explanation":"அனைத்து possible configurations."},
],

'tanglish': [
{"question":"Search algorithm na enna?","options":["A) Problem solution find pannum","B) Data store","C) Code compile","D) Hardware run"],"correct":"A) Problem solution find pannum","explanation":"State space explore pannum."},
{"question":"FIFO use pannra algorithm?","options":["A) DFS","B) BFS","C) A*","D) Greedy"],"correct":"B) BFS","explanation":"Queue (FIFO) use pannum."},
{"question":"Stack use pannra algorithm?","options":["A) BFS","B) DFS","C) A*","D) UCS"],"correct":"B) DFS","explanation":"DFS stack use pannum."},
{"question":"Shortest path kudukura algorithm?","options":["A) DFS","B) BFS","C) Greedy","D) Random"],"correct":"B) BFS","explanation":"Unweighted graph-la shortest path."},
{"question":"Heuristic function na?","options":["A) Exact","B) Estimate cost","C) Random","D) Final"],"correct":"B) Estimate cost","explanation":"Goal distance estimate pannum."},
{"question":"Heuristic use pannra algorithm?","options":["A) BFS","B) DFS","C) A*","D) None"],"correct":"C) A*","explanation":"A* heuristic use pannum."},
{"question":"A* enna combine pannum?","options":["A) BFS + DFS","B) Cost + Heuristic","C) Stack + Queue","D) Input + Output"],"correct":"B) Cost + Heuristic","explanation":"f(n)=g(n)+h(n)."},
{"question":"Uninformed search?","options":["A) A*","B) Greedy","C) BFS","D) Heuristic"],"correct":"C) BFS","explanation":"Heuristic illa."},
{"question":"Informed search?","options":["A) DFS","B) BFS","C) A*","D) Random"],"correct":"C) A*","explanation":"Heuristic use pannum."},
{"question":"State space na?","options":["A) Memory","B) All states","C) CPU","D) Program"],"correct":"B) All states","explanation":"All possible states."},
],

'hindi': [
{"question":"Search algorithm क्या है?","options":["A) Solution ढूंढना","B) Data store","C) Compile","D) Hardware"],"correct":"A) Solution ढूंढना","explanation":"State space explore करता है।"},
{"question":"FIFO कौन use करता है?","options":["A) DFS","B) BFS","C) A*","D) Greedy"],"correct":"B) BFS","explanation":"Queue use करता है।"},
{"question":"Stack कौन use करता है?","options":["A) BFS","B) DFS","C) A*","D) UCS"],"correct":"B) DFS","explanation":"DFS stack use करता है।"},
{"question":"Shortest path कौन देता है?","options":["A) DFS","B) BFS","C) Greedy","D) Random"],"correct":"B) BFS","explanation":"Unweighted graph में shortest path देता है।"},
{"question":"Heuristic function क्या है?","options":["A) Exact","B) Estimate","C) Random","D) Final"],"correct":"B) Estimate","explanation":"Goal तक का अनुमान।"},
{"question":"Heuristic कौन use करता है?","options":["A) BFS","B) DFS","C) A*","D) None"],"correct":"C) A*","explanation":"A* heuristic use करता है।"},
{"question":"A* क्या combine करता है?","options":["A) BFS+DFS","B) Cost+Heuristic","C) Stack+Queue","D) Input+Output"],"correct":"B) Cost+Heuristic","explanation":"f(n)=g(n)+h(n)."},
{"question":"Uninformed search कौन सा है?","options":["A) A*","B) Greedy","C) BFS","D) Heuristic"],"correct":"C) BFS","explanation":"Heuristic use नहीं करता।"},
{"question":"Informed search कौन सा है?","options":["A) DFS","B) BFS","C) A*","D) Random"],"correct":"C) A*","explanation":"Heuristic use करता है।"},
{"question":"State space क्या है?","options":["A) Memory","B) सभी states","C) CPU","D) Program"],"correct":"B) सभी states","explanation":"सभी possible स्थितियां।"},
],

'malayalam': [
{"question":"Search algorithm എന്താണ്?","options":["A) Solution കണ്ടെത്തുന്നു","B) Data store","C) Compile","D) Hardware"],"correct":"A) Solution കണ്ടെത്തുന്നു","explanation":"State space explore ചെയ്യുന്നു."},
{"question":"FIFO ഉപയോഗിക്കുന്നത്?","options":["A) DFS","B) BFS","C) A*","D) Greedy"],"correct":"B) BFS","explanation":"Queue (FIFO) ഉപയോഗിക്കുന്നു."},
{"question":"Stack ഉപയോഗിക്കുന്നത്?","options":["A) BFS","B) DFS","C) A*","D) UCS"],"correct":"B) DFS","explanation":"DFS stack ഉപയോഗിക്കുന്നു."},
{"question":"Shortest path നൽകുന്നത്?","options":["A) DFS","B) BFS","C) Greedy","D) Random"],"correct":"B) BFS","explanation":"Unweighted graph-ൽ shortest path."},
{"question":"Heuristic function എന്താണ്?","options":["A) Exact","B) Estimate","C) Random","D) Final"],"correct":"B) Estimate","explanation":"Goal distance estimate ചെയ്യുന്നു."},
{"question":"Heuristic ഉപയോഗിക്കുന്നത്?","options":["A) BFS","B) DFS","C) A*","D) None"],"correct":"C) A*","explanation":"A* heuristic ഉപയോഗിക്കുന്നു."},
{"question":"A* എന്ത് combine ചെയ്യുന്നു?","options":["A) BFS+DFS","B) Cost+Heuristic","C) Stack+Queue","D) Input+Output"],"correct":"B) Cost+Heuristic","explanation":"f(n)=g(n)+h(n)."},
{"question":"Uninformed search ഏത്?","options":["A) A*","B) Greedy","C) BFS","D) Heuristic"],"correct":"C) BFS","explanation":"Heuristic ഇല്ല."},
{"question":"Informed search ഏത്?","options":["A) DFS","B) BFS","C) A*","D) Random"],"correct":"C) A*","explanation":"Heuristic ഉപയോഗിക്കുന്നു."},
{"question":"State space എന്താണ്?","options":["A) Memory","B) All states","C) CPU","D) Program"],"correct":"B) All states","explanation":"All possible states."},
],
},
'Knowledge Representation':
{'english': [
{"question":"What is Knowledge Representation (KR) in AI?","options":["A) Storing knowledge","B) Representing information for reasoning","C) Writing code","D) Data cleaning"],"correct":"B) Representing information for reasoning","explanation":"KR helps machines understand and reason about knowledge."},
{"question":"Which is a type of knowledge in AI?","options":["A) Declarative","B) Procedural","C) Heuristic","D) All"],"correct":"D) All","explanation":"AI uses multiple types of knowledge."},
{"question":"What is Declarative knowledge?","options":["A) How to do things","B) Facts and information","C) Programming","D) Rules"],"correct":"B) Facts and information","explanation":"Declarative knowledge represents facts."},
{"question":"What is Procedural knowledge?","options":["A) Facts","B) Steps to perform tasks","C) Data","D) Objects"],"correct":"B) Steps to perform tasks","explanation":"Procedural knowledge explains how to do things."},
{"question":"Which method uses IF-THEN rules?","options":["A) Semantic network","B) Production rules","C) Frames","D) Logic"],"correct":"B) Production rules","explanation":"Production rules use IF-THEN format."},
{"question":"What is a Semantic Network?","options":["A) Code structure","B) Graph of knowledge","C) Database","D) Algorithm"],"correct":"B) Graph of knowledge","explanation":"It represents relationships using nodes and links."},
{"question":"What are Frames in AI?","options":["A) Data structures for knowledge","B) Programs","C) Hardware","D) Networks"],"correct":"A) Data structures for knowledge","explanation":"Frames store structured knowledge."},
{"question":"Which representation uses symbols and logic?","options":["A) Logical representation","B) Neural network","C) Database","D) Compiler"],"correct":"A) Logical representation","explanation":"Logic uses symbols to represent knowledge."},
{"question":"What is inference in AI?","options":["A) Data storage","B) Drawing conclusions","C) Coding","D) Printing"],"correct":"B) Drawing conclusions","explanation":"Inference derives new knowledge."},
{"question":"What is ontology in AI?","options":["A) Programming","B) Structure of knowledge","C) Hardware","D) Compiler"],"correct":"B) Structure of knowledge","explanation":"Ontology defines relationships between concepts."},
],

'tamil': [
{"question":"AI-ல் Knowledge Representation என்றால்?","options":["A) Data store","B) தகவலை represent செய்து reasoning செய்யுதல்","C) Code எழுதுதல்","D) Data clean"],"correct":"B) தகவலை represent செய்து reasoning செய்யுதல்","explanation":"Machine reasoning செய்ய உதவும்."},
{"question":"AI-ல் knowledge வகைகள்?","options":["A) Declarative","B) Procedural","C) Heuristic","D) அனைத்தும்"],"correct":"D) அனைத்தும்","explanation":"பல வகை knowledge உள்ளது."},
{"question":"Declarative knowledge என்ன?","options":["A) எப்படி செய்வது","B) தகவல் மற்றும் facts","C) Programming","D) Rules"],"correct":"B) தகவல் மற்றும் facts","explanation":"Facts represent செய்கிறது."},
{"question":"Procedural knowledge என்ன?","options":["A) Facts","B) Steps","C) Data","D) Objects"],"correct":"B) Steps","explanation":"எப்படி செய்வது என்பதை கூறும்."},
{"question":"IF-THEN rules பயன்படுத்துவது?","options":["A) Semantic","B) Production rules","C) Frames","D) Logic"],"correct":"B) Production rules","explanation":"IF-THEN format."},
{"question":"Semantic Network என்றால்?","options":["A) Code","B) Graph","C) DB","D) Algorithm"],"correct":"B) Graph","explanation":"Nodes & links பயன்படுத்தும்."},
{"question":"Frames என்ன?","options":["A) Data structure","B) Program","C) Hardware","D) Network"],"correct":"A) Data structure","explanation":"Structured knowledge store செய்கிறது."},
{"question":"Logic representation?","options":["A) Logical","B) Neural","C) DB","D) Compiler"],"correct":"A) Logical","explanation":"Symbols பயன்படுத்தும்."},
{"question":"Inference என்ன?","options":["A) Store","B) Conclusion","C) Code","D) Print"],"correct":"B) Conclusion","explanation":"New knowledge derive செய்கிறது."},
{"question":"Ontology என்ன?","options":["A) Code","B) Knowledge structure","C) Hardware","D) Compiler"],"correct":"B) Knowledge structure","explanation":"Concept relations define செய்கிறது."},
],

'tanglish': [
{"question":"Knowledge Representation na enna?","options":["A) Store","B) Info represent panni reasoning","C) Code","D) Clean"],"correct":"B) Info represent panni reasoning","explanation":"Machine understand panna help pannum."},
{"question":"Knowledge types?","options":["A) Declarative","B) Procedural","C) Heuristic","D) All"],"correct":"D) All","explanation":"Different types irukku."},
{"question":"Declarative knowledge na?","options":["A) How","B) Facts","C) Code","D) Rules"],"correct":"B) Facts","explanation":"Information represent pannum."},
{"question":"Procedural knowledge na?","options":["A) Facts","B) Steps","C) Data","D) Objects"],"correct":"B) Steps","explanation":"How to do nu sollum."},
{"question":"IF-THEN use pannradhu?","options":["A) Semantic","B) Production rules","C) Frames","D) Logic"],"correct":"B) Production rules","explanation":"Rules format."},
{"question":"Semantic network na?","options":["A) Code","B) Graph","C) DB","D) Algo"],"correct":"B) Graph","explanation":"Nodes links use pannum."},
{"question":"Frames na?","options":["A) Data structure","B) Program","C) Hardware","D) Network"],"correct":"A) Data structure","explanation":"Structured info store pannum."},
{"question":"Logic representation?","options":["A) Logical","B) Neural","C) DB","D) Compiler"],"correct":"A) Logical","explanation":"Symbols use pannum."},
{"question":"Inference na?","options":["A) Store","B) Conclusion","C) Code","D) Print"],"correct":"B) Conclusion","explanation":"New info derive pannum."},
{"question":"Ontology na?","options":["A) Code","B) Structure","C) Hardware","D) Compiler"],"correct":"B) Structure","explanation":"Concept relation define pannum."},
],

'hindi': [
{"question":"Knowledge Representation क्या है?","options":["A) Store","B) Info represent करना","C) Code","D) Clean"],"correct":"B) Info represent करना","explanation":"Machine reasoning में मदद करता है।"},
{"question":"Knowledge के प्रकार?","options":["A) Declarative","B) Procedural","C) Heuristic","D) All"],"correct":"D) All","explanation":"कई प्रकार होते हैं।"},
{"question":"Declarative knowledge?","options":["A) How","B) Facts","C) Code","D) Rules"],"correct":"B) Facts","explanation":"Facts represent करता है।"},
{"question":"Procedural knowledge?","options":["A) Facts","B) Steps","C) Data","D) Objects"],"correct":"B) Steps","explanation":"कैसे करना है बताता है।"},
{"question":"IF-THEN rules?","options":["A) Semantic","B) Production","C) Frames","D) Logic"],"correct":"B) Production","explanation":"Rule based format।"},
{"question":"Semantic network?","options":["A) Code","B) Graph","C) DB","D) Algo"],"correct":"B) Graph","explanation":"Nodes और links।"},
{"question":"Frames?","options":["A) Data structure","B) Program","C) Hardware","D) Network"],"correct":"A) Data structure","explanation":"Structured knowledge store करता है।"},
{"question":"Logic representation?","options":["A) Logical","B) Neural","C) DB","D) Compiler"],"correct":"A) Logical","explanation":"Symbols use करता है।"},
{"question":"Inference?","options":["A) Store","B) Conclusion","C) Code","D) Print"],"correct":"B) Conclusion","explanation":"नया ज्ञान निकालता है।"},
{"question":"Ontology?","options":["A) Code","B) Structure","C) Hardware","D) Compiler"],"correct":"B) Structure","explanation":"Concept relation define करता है।"},
],

'malayalam': [
{"question":"Knowledge Representation എന്താണ്?","options":["A) Store","B) Info represent","C) Code","D) Clean"],"correct":"B) Info represent","explanation":"Machine reasoning സഹായിക്കുന്നു."},
{"question":"Knowledge types?","options":["A) Declarative","B) Procedural","C) Heuristic","D) All"],"correct":"D) All","explanation":"പല തരത്തിലുള്ള knowledge ഉണ്ട്."},
{"question":"Declarative knowledge?","options":["A) How","B) Facts","C) Code","D) Rules"],"correct":"B) Facts","explanation":"Facts represent ചെയ്യുന്നു."},
{"question":"Procedural knowledge?","options":["A) Facts","B) Steps","C) Data","D) Objects"],"correct":"B) Steps","explanation":"എങ്ങനെ ചെയ്യണം എന്ന് പറയുന്നു."},
{"question":"IF-THEN rules?","options":["A) Semantic","B) Production","C) Frames","D) Logic"],"correct":"B) Production","explanation":"Rule-based format."},
{"question":"Semantic network?","options":["A) Code","B) Graph","C) DB","D) Algo"],"correct":"B) Graph","explanation":"Nodes & links ഉപയോഗിക്കുന്നു."},
{"question":"Frames?","options":["A) Data structure","B) Program","C) Hardware","D) Network"],"correct":"A) Data structure","explanation":"Structured knowledge store ചെയ്യുന്നു."},
{"question":"Logic representation?","options":["A) Logical","B) Neural","C) DB","D) Compiler"],"correct":"A) Logical","explanation":"Symbols ഉപയോഗിക്കുന്നു."},
{"question":"Inference?","options":["A) Store","B) Conclusion","C) Code","D) Print"],"correct":"B) Conclusion","explanation":"New knowledge derive ചെയ്യുന്നു."},
{"question":"Ontology?","options":["A) Code","B) Structure","C) Hardware","D) Compiler"],"correct":"B) Structure","explanation":"Concept relation define ചെയ്യുന്നു."},
],
},
'Natural Language Processing':{
'english': [
{"question":"What is NLP?","options":["A) Network Language Processing","B) Natural Language Processing","C) Neural Logic Program","D) None"],"correct":"B) Natural Language Processing","explanation":"NLP helps computers understand human language."},
{"question":"Which is an application of NLP?","options":["A) Image processing","B) Speech recognition","C) Hardware design","D) Networking"],"correct":"B) Speech recognition","explanation":"Speech recognition is a key NLP application."},
{"question":"What is tokenization?","options":["A) Splitting text into words","B) Storing data","C) Encrypting data","D) Sorting text"],"correct":"A) Splitting text into words","explanation":"Tokenization breaks text into smaller units."},
{"question":"What is stemming?","options":["A) Adding suffix","B) Reducing word to root form","C) Translating language","D) Removing spaces"],"correct":"B) Reducing word to root form","explanation":"Stemming removes suffixes."},
{"question":"What is lemmatization?","options":["A) Random word","B) Root word extraction","C) Grammar correction","D) Data storage"],"correct":"B) Root word extraction","explanation":"Lemmatization finds meaningful base form."},
{"question":"What is POS tagging?","options":["A) Type of network","B) Assigning parts of speech","C) Storing text","D) Compiling"],"correct":"B) Assigning parts of speech","explanation":"POS tagging labels nouns, verbs, etc."},
{"question":"Which task converts speech to text?","options":["A) Text generation","B) Speech recognition","C) Translation","D) Parsing"],"correct":"B) Speech recognition","explanation":"It converts spoken language to text."},
{"question":"Which task converts text to speech?","options":["A) TTS","B) STT","C) Parsing","D) Tokenization"],"correct":"A) TTS","explanation":"Text-to-Speech converts text into audio."},
{"question":"What is machine translation?","options":["A) Code conversion","B) Language translation","C) Data storage","D) Encryption"],"correct":"B) Language translation","explanation":"It translates one language to another."},
{"question":"What is sentiment analysis?","options":["A) Grammar check","B) Emotion detection","C) Data sorting","D) Encryption"],"correct":"B) Emotion detection","explanation":"It detects positive/negative feelings."},
],

'tamil': [
{"question":"NLP என்றால் என்ன?","options":["A) Network Language Processing","B) Natural Language Processing","C) Neural Logic Program","D) None"],"correct":"B) Natural Language Processing","explanation":"மனித மொழியை கணினி புரிந்து கொள்ள உதவும்."},
{"question":"NLP பயன்பாடு எது?","options":["A) Image processing","B) Speech recognition","C) Hardware design","D) Networking"],"correct":"B) Speech recognition","explanation":"Speech recognition முக்கிய பயன்பாடு."},
{"question":"Tokenization என்றால்?","options":["A) Words-ஆக பிரித்தல்","B) Data store","C) Encrypt","D) Sort"],"correct":"A) Words-ஆக பிரித்தல்","explanation":"Text-ஐ சிறு பகுதிகளாக பிரிக்கும்."},
{"question":"Stemming என்றால்?","options":["A) Add suffix","B) Root form","C) Translate","D) Remove space"],"correct":"B) Root form","explanation":"Suffix-ஐ நீக்கும்."},
{"question":"Lemmatization என்றால்?","options":["A) Random","B) Root word","C) Grammar","D) Store"],"correct":"B) Root word","explanation":"Meaningful base form கண்டறியும்."},
{"question":"POS tagging என்றால்?","options":["A) Network","B) Parts of speech assign","C) Store","D) Compile"],"correct":"B) Parts of speech assign","explanation":"Noun, verb போன்றவை assign செய்கிறது."},
{"question":"Speech to text task?","options":["A) Generation","B) Recognition","C) Translation","D) Parsing"],"correct":"B) Recognition","explanation":"Speech → Text."},
{"question":"Text to speech task?","options":["A) TTS","B) STT","C) Parsing","D) Token"],"correct":"A) TTS","explanation":"Text → Audio."},
{"question":"Machine translation என்றால்?","options":["A) Code","B) Language translate","C) Store","D) Encrypt"],"correct":"B) Language translate","explanation":"ஒரு மொழியை மற்றொன்றாக மாற்றும்."},
{"question":"Sentiment analysis?","options":["A) Grammar","B) Emotion detect","C) Sort","D) Encrypt"],"correct":"B) Emotion detect","explanation":"Positive/negative கண்டறியும்."},
],

'tanglish': [
{"question":"NLP na enna?","options":["A) Network","B) Natural Language Processing","C) Neural","D) None"],"correct":"B) Natural Language Processing","explanation":"Human language-a computer understand panna help pannum."},
{"question":"NLP application?","options":["A) Image","B) Speech recognition","C) Hardware","D) Network"],"correct":"B) Speech recognition","explanation":"Important application."},
{"question":"Tokenization na?","options":["A) Split words","B) Store","C) Encrypt","D) Sort"],"correct":"A) Split words","explanation":"Text-a break pannum."},
{"question":"Stemming na?","options":["A) Add","B) Root form","C) Translate","D) Remove"],"correct":"B) Root form","explanation":"Suffix remove pannum."},
{"question":"Lemmatization na?","options":["A) Random","B) Root word","C) Grammar","D) Store"],"correct":"B) Root word","explanation":"Base form find pannum."},
{"question":"POS tagging na?","options":["A) Network","B) Parts assign","C) Store","D) Compile"],"correct":"B) Parts assign","explanation":"Noun, verb assign pannum."},
{"question":"Speech to text?","options":["A) Gen","B) Recognition","C) Translation","D) Parsing"],"correct":"B) Recognition","explanation":"Speech → Text."},
{"question":"Text to speech?","options":["A) TTS","B) STT","C) Parsing","D) Token"],"correct":"A) TTS","explanation":"Text → Audio."},
{"question":"Machine translation?","options":["A) Code","B) Language","C) Store","D) Encrypt"],"correct":"B) Language","explanation":"One language to another."},
{"question":"Sentiment analysis?","options":["A) Grammar","B) Emotion","C) Sort","D) Encrypt"],"correct":"B) Emotion","explanation":"Feeling detect pannum."},
],

'hindi': [
{"question":"NLP क्या है?","options":["A) Network","B) Natural Language Processing","C) Neural","D) None"],"correct":"B) Natural Language Processing","explanation":"Computer को human language समझने में मदद करता है।"},
{"question":"NLP application?","options":["A) Image","B) Speech recognition","C) Hardware","D) Network"],"correct":"B) Speech recognition","explanation":"महत्वपूर्ण उपयोग।"},
{"question":"Tokenization?","options":["A) Split","B) Store","C) Encrypt","D) Sort"],"correct":"A) Split","explanation":"Text को words में तोड़ता है।"},
{"question":"Stemming?","options":["A) Add","B) Root","C) Translate","D) Remove"],"correct":"B) Root","explanation":"Suffix हटाता है।"},
{"question":"Lemmatization?","options":["A) Random","B) Root word","C) Grammar","D) Store"],"correct":"B) Root word","explanation":"Base form देता है।"},
{"question":"POS tagging?","options":["A) Network","B) Parts assign","C) Store","D) Compile"],"correct":"B) Parts assign","explanation":"Noun, verb आदि assign करता है।"},
{"question":"Speech to text?","options":["A) Gen","B) Recognition","C) Translation","D) Parsing"],"correct":"B) Recognition","explanation":"Speech → Text."},
{"question":"Text to speech?","options":["A) TTS","B) STT","C) Parsing","D) Token"],"correct":"A) TTS","explanation":"Text → Audio."},
{"question":"Machine translation?","options":["A) Code","B) Language","C) Store","D) Encrypt"],"correct":"B) Language","explanation":"Language conversion।"},
{"question":"Sentiment analysis?","options":["A) Grammar","B) Emotion","C) Sort","D) Encrypt"],"correct":"B) Emotion","explanation":"भावनाएं पहचानता है।"},
],

'malayalam': [
{"question":"NLP എന്താണ്?","options":["A) Network","B) Natural Language Processing","C) Neural","D) None"],"correct":"B) Natural Language Processing","explanation":"Human language computer മനസ്സിലാക്കാൻ സഹായിക്കുന്നു."},
{"question":"NLP application?","options":["A) Image","B) Speech recognition","C) Hardware","D) Network"],"correct":"B) Speech recognition","explanation":"പ്രധാന ഉപയോഗം."},
{"question":"Tokenization?","options":["A) Split","B) Store","C) Encrypt","D) Sort"],"correct":"A) Split","explanation":"Text words ആയി വിഭജിക്കുന്നു."},
{"question":"Stemming?","options":["A) Add","B) Root","C) Translate","D) Remove"],"correct":"B) Root","explanation":"Suffix നീക്കം ചെയ്യുന്നു."},
{"question":"Lemmatization?","options":["A) Random","B) Root word","C) Grammar","D) Store"],"correct":"B) Root word","explanation":"Base form കണ്ടെത്തുന്നു."},
{"question":"POS tagging?","options":["A) Network","B) Parts assign","C) Store","D) Compile"],"correct":"B) Parts assign","explanation":"Noun, verb assign ചെയ്യുന്നു."},
{"question":"Speech to text?","options":["A) Gen","B) Recognition","C) Translation","D) Parsing"],"correct":"B) Recognition","explanation":"Speech → Text."},
{"question":"Text to speech?","options":["A) TTS","B) STT","C) Parsing","D) Token"],"correct":"A) TTS","explanation":"Text → Audio."},
{"question":"Machine translation?","options":["A) Code","B) Language","C) Store","D) Encrypt"],"correct":"B) Language","explanation":"Language മാറ്റം."},
{"question":"Sentiment analysis?","options":["A) Grammar","B) Emotion","C) Sort","D) Encrypt"],"correct":"B) Emotion","explanation":"Feelings detect ചെയ്യുന്നു."},
],
},
'Computer Vision':{
'english': [
{"question":"What is Computer Vision?","options":["A) Understanding images and videos","B) Writing code","C) Data storage","D) Networking"],"correct":"A) Understanding images and videos","explanation":"Computer Vision enables machines to interpret visual data."},
{"question":"Which is an application of Computer Vision?","options":["A) Image recognition","B) Text editing","C) Networking","D) Database"],"correct":"A) Image recognition","explanation":"Recognizing objects in images is a key task."},
{"question":"What is image classification?","options":["A) Editing image","B) Assigning label to image","C) Compressing image","D) Drawing image"],"correct":"B) Assigning label to image","explanation":"It categorizes images into classes."},
{"question":"What is object detection?","options":["A) Finding objects in image","B) Editing image","C) Deleting image","D) Storing image"],"correct":"A) Finding objects in image","explanation":"It locates and identifies objects."},
{"question":"What is pixel?","options":["A) Smallest unit of image","B) Large image","C) Program","D) Code"],"correct":"A) Smallest unit of image","explanation":"Images are made of pixels."},
{"question":"What is grayscale image?","options":["A) Color image","B) Black and white image","C) 3D image","D) Video"],"correct":"B) Black and white image","explanation":"Grayscale images have shades of gray."},
{"question":"Which technique detects edges?","options":["A) Edge detection","B) Tokenization","C) Sorting","D) Parsing"],"correct":"A) Edge detection","explanation":"Edge detection finds boundaries in images."},
{"question":"Which model is used in vision tasks?","options":["A) CNN","B) RNN","C) SVM","D) DBMS"],"correct":"A) CNN","explanation":"Convolutional Neural Networks are widely used."},
{"question":"What is feature extraction?","options":["A) Removing data","B) Identifying important parts","C) Adding noise","D) Saving image"],"correct":"B) Identifying important parts","explanation":"Extracts useful patterns from images."},
{"question":"What is face recognition?","options":["A) Editing face","B) Identifying person from image","C) Drawing face","D) Saving image"],"correct":"B) Identifying person from image","explanation":"Used in security and authentication."},
],

'tamil': [
{"question":"Computer Vision என்றால்?","options":["A) Image/video புரிதல்","B) Code எழுதுதல்","C) Data store","D) Network"],"correct":"A) Image/video புரிதல்","explanation":"Visual data-ஐ machine புரிந்து கொள்கிறது."},
{"question":"Computer Vision பயன்பாடு?","options":["A) Image recognition","B) Text edit","C) Network","D) DB"],"correct":"A) Image recognition","explanation":"Objects கண்டறிதல் முக்கியம்."},
{"question":"Image classification என்றால்?","options":["A) Edit","B) Label assign","C) Compress","D) Draw"],"correct":"B) Label assign","explanation":"Image-க்கு category கொடுக்கும்."},
{"question":"Object detection?","options":["A) Object கண்டறிதல்","B) Edit","C) Delete","D) Store"],"correct":"A) Object கண்டறிதல்","explanation":"Location + identity கண்டறியும்."},
{"question":"Pixel என்றால்?","options":["A) சிறிய unit","B) பெரிய image","C) Program","D) Code"],"correct":"A) சிறிய unit","explanation":"Image pixels-ஆல் ஆனது."},
{"question":"Grayscale image?","options":["A) Color","B) Black & white","C) 3D","D) Video"],"correct":"B) Black & white","explanation":"Gray shades மட்டும்."},
{"question":"Edge detection technique?","options":["A) Edge detection","B) Token","C) Sort","D) Parse"],"correct":"A) Edge detection","explanation":"Edges கண்டறியும்."},
{"question":"Vision model?","options":["A) CNN","B) RNN","C) SVM","D) DB"],"correct":"A) CNN","explanation":"CNN image tasks-க்கு பயன்படும்."},
{"question":"Feature extraction?","options":["A) Remove","B) Important parts find","C) Noise add","D) Save"],"correct":"B) Important parts find","explanation":"Useful patterns எடுக்கும்."},
{"question":"Face recognition?","options":["A) Edit","B) Identify person","C) Draw","D) Save"],"correct":"B) Identify person","explanation":"Security பயன்பாடு."},
],

'tanglish': [
{"question":"Computer Vision na enna?","options":["A) Image/video understand","B) Code","C) Store","D) Network"],"correct":"A) Image/video understand","explanation":"Visual data-a machine purinjukudum."},
{"question":"Application?","options":["A) Image recognition","B) Text","C) Network","D) DB"],"correct":"A) Image recognition","explanation":"Object identify pannum."},
{"question":"Image classification na?","options":["A) Edit","B) Label","C) Compress","D) Draw"],"correct":"B) Label","explanation":"Category assign pannum."},
{"question":"Object detection?","options":["A) Object find","B) Edit","C) Delete","D) Store"],"correct":"A) Object find","explanation":"Locate + identify pannum."},
{"question":"Pixel na?","options":["A) Small unit","B) Big image","C) Program","D) Code"],"correct":"A) Small unit","explanation":"Image basic unit."},
{"question":"Grayscale image?","options":["A) Color","B) B/W","C) 3D","D) Video"],"correct":"B) B/W","explanation":"Gray shades."},
{"question":"Edge detection?","options":["A) Edge","B) Token","C) Sort","D) Parse"],"correct":"A) Edge","explanation":"Boundary detect pannum."},
{"question":"Model?","options":["A) CNN","B) RNN","C) SVM","D) DB"],"correct":"A) CNN","explanation":"CNN use pannuvanga."},
{"question":"Feature extraction?","options":["A) Remove","B) Important parts","C) Noise","D) Save"],"correct":"B) Important parts","explanation":"Useful features edukkum."},
{"question":"Face recognition?","options":["A) Edit","B) Identify","C) Draw","D) Save"],"correct":"B) Identify","explanation":"Person identify pannum."},
],

'hindi': [
{"question":"Computer Vision क्या है?","options":["A) Image/video समझना","B) Code","C) Store","D) Network"],"correct":"A) Image/video समझना","explanation":"Machine visual data समझती है।"},
{"question":"Application?","options":["A) Image recognition","B) Text","C) Network","D) DB"],"correct":"A) Image recognition","explanation":"Object पहचानना।"},
{"question":"Image classification?","options":["A) Edit","B) Label","C) Compress","D) Draw"],"correct":"B) Label","explanation":"Image को category देता है।"},
{"question":"Object detection?","options":["A) Object ढूंढना","B) Edit","C) Delete","D) Store"],"correct":"A) Object ढूंढना","explanation":"Location + पहचान।"},
{"question":"Pixel?","options":["A) Small unit","B) Big","C) Program","D) Code"],"correct":"A) Small unit","explanation":"Image का छोटा हिस्सा।"},
{"question":"Grayscale image?","options":["A) Color","B) B/W","C) 3D","D) Video"],"correct":"B) B/W","explanation":"Gray shades।"},
{"question":"Edge detection?","options":["A) Edge","B) Token","C) Sort","D) Parse"],"correct":"A) Edge","explanation":"Edges detect करता है।"},
{"question":"Model?","options":["A) CNN","B) RNN","C) SVM","D) DB"],"correct":"A) CNN","explanation":"Image tasks के लिए।"},
{"question":"Feature extraction?","options":["A) Remove","B) Important parts","C) Noise","D) Save"],"correct":"B) Important parts","explanation":"Useful features निकालता है।"},
{"question":"Face recognition?","options":["A) Edit","B) Identify","C) Draw","D) Save"],"correct":"B) Identify","explanation":"Person पहचानता है।"},
],

'malayalam': [
{"question":"Computer Vision എന്താണ്?","options":["A) Image/video മനസ്സിലാക്കൽ","B) Code","C) Store","D) Network"],"correct":"A) Image/video മനസ്സിലാക്കൽ","explanation":"Machine visual data മനസ്സിലാക്കുന്നു."},
{"question":"Application?","options":["A) Image recognition","B) Text","C) Network","D) DB"],"correct":"A) Image recognition","explanation":"Object തിരിച്ചറിയൽ."},
{"question":"Image classification?","options":["A) Edit","B) Label","C) Compress","D) Draw"],"correct":"B) Label","explanation":"Category നൽകുന്നു."},
{"question":"Object detection?","options":["A) Object കണ്ടെത്തൽ","B) Edit","C) Delete","D) Store"],"correct":"A) Object കണ്ടെത്തൽ","explanation":"Location + identity."},
{"question":"Pixel?","options":["A) Small unit","B) Big","C) Program","D) Code"],"correct":"A) Small unit","explanation":"Image-ന്റെ ചെറിയ ഭാഗം."},
{"question":"Grayscale image?","options":["A) Color","B) B/W","C) 3D","D) Video"],"correct":"B) B/W","explanation":"Gray shades മാത്രം."},
{"question":"Edge detection?","options":["A) Edge","B) Token","C) Sort","D) Parse"],"correct":"A) Edge","explanation":"Edges കണ്ടെത്തുന്നു."},
{"question":"Model?","options":["A) CNN","B) RNN","C) SVM","D) DB"],"correct":"A) CNN","explanation":"Image tasks-ക്ക് ഉപയോഗിക്കുന്നു."},
{"question":"Feature extraction?","options":["A) Remove","B) Important parts","C) Noise","D) Save"],"correct":"B) Important parts","explanation":"Useful features കണ്ടെത്തുന്നു."},
{"question":"Face recognition?","options":["A) Edit","B) Identify","C) Draw","D) Save"],"correct":"B) Identify","explanation":"Person തിരിച്ചറിയുന്നു."},
],  
},
'AI Ethics':{
'english': [
{"question":"What is AI Ethics?","options":["A) Moral principles for AI","B) Programming language","C) Database system","D) Hardware"],"correct":"A) Moral principles for AI","explanation":"AI Ethics deals with responsible use of AI."},
{"question":"What is bias in AI?","options":["A) Fair decision","B) Unfair preference","C) Fast processing","D) Data storage"],"correct":"B) Unfair preference","explanation":"Bias leads to unfair outcomes."},
{"question":"What is transparency in AI?","options":["A) Hidden system","B) Clear understanding","C) Fast output","D) Data hiding"],"correct":"B) Clear understanding","explanation":"Users should understand how AI works."},
{"question":"What is accountability?","options":["A) No responsibility","B) Taking responsibility","C) Data storage","D) Coding"],"correct":"B) Taking responsibility","explanation":"Developers must be responsible for AI actions."},
{"question":"What is privacy in AI?","options":["A) Data sharing","B) Protecting user data","C) Data selling","D) Open access"],"correct":"B) Protecting user data","explanation":"User data should be safe."},
{"question":"What is fairness in AI?","options":["A) Equal treatment","B) Bias","C) Fast output","D) Random result"],"correct":"A) Equal treatment","explanation":"AI should treat all equally."},
{"question":"What is explainability?","options":["A) Complex output","B) Easy to understand","C) Hidden logic","D) Random result"],"correct":"B) Easy to understand","explanation":"AI decisions should be explainable."},
{"question":"What is misuse of AI?","options":["A) Good usage","B) Harmful usage","C) Learning","D) Testing"],"correct":"B) Harmful usage","explanation":"Using AI for harmful purposes."},
{"question":"What is ethical concern in AI?","options":["A) Bias","B) Privacy","C) Security","D) All of the above"],"correct":"D) All of the above","explanation":"All are key ethical concerns."},
{"question":"Why is AI Ethics important?","options":["A) Safe AI use","B) Fast coding","C) Storage","D) Hardware"],"correct":"A) Safe AI use","explanation":"Ensures AI benefits society."},
],

'tamil': [
{"question":"AI Ethics என்றால்?","options":["A) நெறிமுறைகள்","B) Language","C) DB","D) Hardware"],"correct":"A) நெறிமுறைகள்","explanation":"AI-ஐ சரியாக பயன்படுத்தும் விதிமுறைகள்."},
{"question":"Bias என்றால்?","options":["A) Fair","B) Unfair preference","C) Fast","D) Store"],"correct":"B) Unfair preference","explanation":"நியாயமில்லாத முடிவுகள்."},
{"question":"Transparency?","options":["A) Hidden","B) Clear","C) Fast","D) Hide"],"correct":"B) Clear","explanation":"AI எப்படி வேலை செய்கிறது தெரிய வேண்டும்."},
{"question":"Accountability?","options":["A) No responsibility","B) Responsibility","C) Store","D) Code"],"correct":"B) Responsibility","explanation":"Developers பொறுப்பு எடுக்க வேண்டும்."},
{"question":"Privacy?","options":["A) Share","B) Protect data","C) Sell","D) Open"],"correct":"B) Protect data","explanation":"User data பாதுகாப்பு."},
{"question":"Fairness?","options":["A) Equal","B) Bias","C) Fast","D) Random"],"correct":"A) Equal","explanation":"அனைவருக்கும் சமமான முடிவு."},
{"question":"Explainability?","options":["A) Complex","B) Easy","C) Hidden","D) Random"],"correct":"B) Easy","explanation":"AI முடிவு புரிய வேண்டும்."},
{"question":"Misuse?","options":["A) Good","B) Harmful","C) Learn","D) Test"],"correct":"B) Harmful","explanation":"தவறான பயன்பாடு."},
{"question":"Ethical concern?","options":["A) Bias","B) Privacy","C) Security","D) All"],"correct":"D) All","explanation":"அனைத்தும் முக்கியம்."},
{"question":"Importance?","options":["A) Safe AI","B) Fast","C) Store","D) Hardware"],"correct":"A) Safe AI","explanation":"சமூக நலன்."},
],

'tanglish': [
{"question":"AI Ethics na enna?","options":["A) Moral rules","B) Language","C) DB","D) Hardware"],"correct":"A) Moral rules","explanation":"AI use panna correct rules."},
{"question":"Bias na?","options":["A) Fair","B) Unfair","C) Fast","D) Store"],"correct":"B) Unfair","explanation":"Niyayam illa result."},
{"question":"Transparency?","options":["A) Hidden","B) Clear","C) Fast","D) Hide"],"correct":"B) Clear","explanation":"AI epdi work nu puriyanum."},
{"question":"Accountability?","options":["A) No resp","B) Resp","C) Store","D) Code"],"correct":"B) Resp","explanation":"Responsibility edukkanum."},
{"question":"Privacy?","options":["A) Share","B) Protect","C) Sell","D) Open"],"correct":"B) Protect","explanation":"User data safe."},
{"question":"Fairness?","options":["A) Equal","B) Bias","C) Fast","D) Random"],"correct":"A) Equal","explanation":"Ellarum same treatment."},
{"question":"Explainability?","options":["A) Complex","B) Easy","C) Hidden","D) Random"],"correct":"B) Easy","explanation":"AI result puriyanum."},
{"question":"Misuse?","options":["A) Good","B) Harmful","C) Learn","D) Test"],"correct":"B) Harmful","explanation":"Thappu use."},
{"question":"Ethical concern?","options":["A) Bias","B) Privacy","C) Security","D) All"],"correct":"D) All","explanation":"Ellam mukkiyam."},
{"question":"Importance?","options":["A) Safe","B) Fast","C) Store","D) Hardware"],"correct":"A) Safe","explanation":"Safe AI use."},
],

'hindi': [
{"question":"AI Ethics क्या है?","options":["A) नैतिक नियम","B) Language","C) DB","D) Hardware"],"correct":"A) नैतिक नियम","explanation":"AI के सही उपयोग के नियम।"},
{"question":"Bias क्या है?","options":["A) Fair","B) Unfair","C) Fast","D) Store"],"correct":"B) Unfair","explanation":"अन्यायपूर्ण परिणाम।"},
{"question":"Transparency?","options":["A) Hidden","B) Clear","C) Fast","D) Hide"],"correct":"B) Clear","explanation":"AI कैसे काम करता है समझना।"},
{"question":"Accountability?","options":["A) No resp","B) Resp","C) Store","D) Code"],"correct":"B) Resp","explanation":"जिम्मेदारी लेना।"},
{"question":"Privacy?","options":["A) Share","B) Protect","C) Sell","D) Open"],"correct":"B) Protect","explanation":"User data सुरक्षित।"},
{"question":"Fairness?","options":["A) Equal","B) Bias","C) Fast","D) Random"],"correct":"A) Equal","explanation":"सबको समान व्यवहार।"},
{"question":"Explainability?","options":["A) Complex","B) Easy","C) Hidden","D) Random"],"correct":"B) Easy","explanation":"AI निर्णय समझ में आना चाहिए।"},
{"question":"Misuse?","options":["A) Good","B) Harmful","C) Learn","D) Test"],"correct":"B) Harmful","explanation":"गलत उपयोग।"},
{"question":"Ethical concern?","options":["A) Bias","B) Privacy","C) Security","D) All"],"correct":"D) All","explanation":"सभी महत्वपूर्ण हैं।"},
{"question":"Importance?","options":["A) Safe","B) Fast","C) Store","D) Hardware"],"correct":"A) Safe","explanation":"सुरक्षित AI उपयोग।"},
],

'malayalam': [
{"question":"AI Ethics എന്താണ്?","options":["A) നൈതിക നിയമങ്ങൾ","B) Language","C) DB","D) Hardware"],"correct":"A) നൈതിക നിയമങ്ങൾ","explanation":"AI ശരിയായി ഉപയോഗിക്കാൻ നിയമങ്ങൾ."},
{"question":"Bias എന്താണ്?","options":["A) Fair","B) Unfair","C) Fast","D) Store"],"correct":"B) Unfair","explanation":"അന്യായ ഫലങ്ങൾ."},
{"question":"Transparency?","options":["A) Hidden","B) Clear","C) Fast","D) Hide"],"correct":"B) Clear","explanation":"AI എങ്ങനെ പ്രവർത്തിക്കുന്നു മനസ്സിലാക്കണം."},
{"question":"Accountability?","options":["A) No resp","B) Resp","C) Store","D) Code"],"correct":"B) Resp","explanation":"ഉത്തരവാദിത്വം എടുക്കണം."},
{"question":"Privacy?","options":["A) Share","B) Protect","C) Sell","D) Open"],"correct":"B) Protect","explanation":"User data സംരക്ഷണം."},
{"question":"Fairness?","options":["A) Equal","B) Bias","C) Fast","D) Random"],"correct":"A) Equal","explanation":"എല്ലാവർക്കും ഒരുപോലെ."},
{"question":"Explainability?","options":["A) Complex","B) Easy","C) Hidden","D) Random"],"correct":"B) Easy","explanation":"AI തീരുമാനങ്ങൾ മനസ്സിലാക്കണം."},
{"question":"Misuse?","options":["A) Good","B) Harmful","C) Learn","D) Test"],"correct":"B) Harmful","explanation":"തെറ്റായ ഉപയോഗം."},
{"question":"Ethical concern?","options":["A) Bias","B) Privacy","C) Security","D) All"],"correct":"D) All","explanation":"എല്ലാം പ്രധാനമാണ്."},
{"question":"Importance?","options":["A) Safe","B) Fast","C) Store","D) Hardware"],"correct":"A) Safe","explanation":"സുരക്ഷിത AI ഉപയോഗം."},
],
},

'AI Applications':{
   'english': [
{"question":"What is an AI application?","options":["A) Use of AI in real-world tasks","B) Programming language","C) Database","D) Hardware"],"correct":"A) Use of AI in real-world tasks","explanation":"AI applications solve real-world problems."},
{"question":"AI is used in healthcare for?","options":["A) Diagnosis","B) Gaming","C) Networking","D) Drawing"],"correct":"A) Diagnosis","explanation":"AI helps in disease detection."},
{"question":"AI in finance is used for?","options":["A) Fraud detection","B) Cooking","C) Drawing","D) Writing"],"correct":"A) Fraud detection","explanation":"AI detects suspicious transactions."},
{"question":"AI in education helps in?","options":["A) Personalized learning","B) Manual teaching","C) No learning","D) Only exams"],"correct":"A) Personalized learning","explanation":"AI adapts to student needs."},
{"question":"AI in transportation?","options":["A) Self-driving cars","B) Books","C) Phones","D) Pens"],"correct":"A) Self-driving cars","explanation":"AI powers autonomous vehicles."},
{"question":"AI in e-commerce?","options":["A) Product recommendations","B) Painting","C) Cooking","D) Singing"],"correct":"A) Product recommendations","explanation":"AI suggests products to users."},
{"question":"AI in agriculture?","options":["A) Crop monitoring","B) Coding","C) Networking","D) Drawing"],"correct":"A) Crop monitoring","explanation":"AI helps farmers analyze crops."},
{"question":"AI in security?","options":["A) Face recognition","B) Cooking","C) Drawing","D) Singing"],"correct":"A) Face recognition","explanation":"AI identifies individuals."},
{"question":"AI in entertainment?","options":["A) Movie recommendations","B) Farming","C) Coding","D) Networking"],"correct":"A) Movie recommendations","explanation":"AI suggests content."},
{"question":"AI in customer service?","options":["A) Chatbots","B) Cooking","C) Drawing","D) Singing"],"correct":"A) Chatbots","explanation":"AI chatbots assist customers."},
],

'tamil': [
{"question":"AI Application என்றால்?","options":["A) Real-world use","B) Language","C) DB","D) Hardware"],"correct":"A) Real-world use","explanation":"AI வாழ்க்கையில் பயன்படும்."},
{"question":"Healthcare?","options":["A) Diagnosis","B) Game","C) Network","D) Draw"],"correct":"A) Diagnosis","explanation":"நோய் கண்டறிதல்."},
{"question":"Finance?","options":["A) Fraud detect","B) Cook","C) Draw","D) Write"],"correct":"A) Fraud detect","explanation":"சந்தேகமான transaction கண்டறிதல்."},
{"question":"Education?","options":["A) Personal learning","B) Manual","C) None","D) Exam"],"correct":"A) Personal learning","explanation":"Student-க்கு பொருந்தும்."},
{"question":"Transport?","options":["A) Self drive","B) Book","C) Phone","D) Pen"],"correct":"A) Self drive","explanation":"AI vehicle இயக்கும்."},
{"question":"E-commerce?","options":["A) Recommend","B) Paint","C) Cook","D) Sing"],"correct":"A) Recommend","explanation":"Products suggest செய்யும்."},
{"question":"Agriculture?","options":["A) Crop monitor","B) Code","C) Network","D) Draw"],"correct":"A) Crop monitor","explanation":"பயிர் கண்காணிப்பு."},
{"question":"Security?","options":["A) Face recog","B) Cook","C) Draw","D) Sing"],"correct":"A) Face recog","explanation":"Person கண்டறிதல்."},
{"question":"Entertainment?","options":["A) Movie suggest","B) Farm","C) Code","D) Network"],"correct":"A) Movie suggest","explanation":"Content பரிந்துரை."},
{"question":"Customer service?","options":["A) Chatbot","B) Cook","C) Draw","D) Sing"],"correct":"A) Chatbot","explanation":"Customer help."},
],

'tanglish': [
{"question":"AI Application na?","options":["A) Real world use","B) Lang","C) DB","D) Hardware"],"correct":"A) Real world use","explanation":"AI real life la use aagum."},
{"question":"Healthcare?","options":["A) Diagnosis","B) Game","C) Network","D) Draw"],"correct":"A) Diagnosis","explanation":"Disease detect pannum."},
{"question":"Finance?","options":["A) Fraud detect","B) Cook","C) Draw","D) Write"],"correct":"A) Fraud detect","explanation":"Fraud identify pannum."},
{"question":"Education?","options":["A) Personal","B) Manual","C) None","D) Exam"],"correct":"A) Personal","explanation":"Custom learning."},
{"question":"Transport?","options":["A) Self drive","B) Book","C) Phone","D) Pen"],"correct":"A) Self drive","explanation":"AI car drive pannum."},
{"question":"E-commerce?","options":["A) Recommend","B) Paint","C) Cook","D) Sing"],"correct":"A) Recommend","explanation":"Products suggest pannum."},
{"question":"Agriculture?","options":["A) Crop monitor","B) Code","C) Network","D) Draw"],"correct":"A) Crop monitor","explanation":"Crop check pannum."},
{"question":"Security?","options":["A) Face recog","B) Cook","C) Draw","D) Sing"],"correct":"A) Face recog","explanation":"Person identify pannum."},
{"question":"Entertainment?","options":["A) Movie suggest","B) Farm","C) Code","D) Network"],"correct":"A) Movie suggest","explanation":"Content recommend pannum."},
{"question":"Customer service?","options":["A) Chatbot","B) Cook","C) Draw","D) Sing"],"correct":"A) Chatbot","explanation":"Customer support."},
],

'hindi': [
{"question":"AI Application क्या है?","options":["A) Real world use","B) Language","C) DB","D) Hardware"],"correct":"A) Real world use","explanation":"AI का उपयोग वास्तविक जीवन में।"},
{"question":"Healthcare?","options":["A) Diagnosis","B) Game","C) Network","D) Draw"],"correct":"A) Diagnosis","explanation":"बीमारी पहचान।"},
{"question":"Finance?","options":["A) Fraud detect","B) Cook","C) Draw","D) Write"],"correct":"A) Fraud detect","explanation":"Fraud पहचान।"},
{"question":"Education?","options":["A) Personal","B) Manual","C) None","D) Exam"],"correct":"A) Personal","explanation":"Personalized learning।"},
{"question":"Transport?","options":["A) Self drive","B) Book","C) Phone","D) Pen"],"correct":"A) Self drive","explanation":"Self driving cars।"},
{"question":"E-commerce?","options":["A) Recommend","B) Paint","C) Cook","D) Sing"],"correct":"A) Recommend","explanation":"Products सुझाव।"},
{"question":"Agriculture?","options":["A) Crop monitor","B) Code","C) Network","D) Draw"],"correct":"A) Crop monitor","explanation":"Farming में मदद।"},
{"question":"Security?","options":["A) Face recog","B) Cook","C) Draw","D) Sing"],"correct":"A) Face recog","explanation":"Person पहचान।"},
{"question":"Entertainment?","options":["A) Movie suggest","B) Farm","C) Code","D) Network"],"correct":"A) Movie suggest","explanation":"Content सुझाव।"},
{"question":"Customer service?","options":["A) Chatbot","B) Cook","C) Draw","D) Sing"],"correct":"A) Chatbot","explanation":"Customer सहायता।"},
],

'malayalam': [
{"question":"AI Application എന്താണ്?","options":["A) Real world use","B) Language","C) DB","D) Hardware"],"correct":"A) Real world use","explanation":"AI യുടെ യഥാർത്ഥ ഉപയോഗം."},
{"question":"Healthcare?","options":["A) Diagnosis","B) Game","C) Network","D) Draw"],"correct":"A) Diagnosis","explanation":"രോഗം കണ്ടെത്തൽ."},
{"question":"Finance?","options":["A) Fraud detect","B) Cook","C) Draw","D) Write"],"correct":"A) Fraud detect","explanation":"Fraud കണ്ടെത്തൽ."},
{"question":"Education?","options":["A) Personal","B) Manual","C) None","D) Exam"],"correct":"A) Personal","explanation":"Personalized learning."},
{"question":"Transport?","options":["A) Self drive","B) Book","C) Phone","D) Pen"],"correct":"A) Self drive","explanation":"Self driving cars."},
{"question":"E-commerce?","options":["A) Recommend","B) Paint","C) Cook","D) Sing"],"correct":"A) Recommend","explanation":"Products suggest ചെയ്യുന്നു."},
{"question":"Agriculture?","options":["A) Crop monitor","B) Code","C) Network","D) Draw"],"correct":"A) Crop monitor","explanation":"Crop monitoring."},
{"question":"Security?","options":["A) Face recog","B) Cook","C) Draw","D) Sing"],"correct":"A) Face recog","explanation":"Person തിരിച്ചറിയൽ."},
{"question":"Entertainment?","options":["A) Movie suggest","B) Farm","C) Code","D) Network"],"correct":"A) Movie suggest","explanation":"Content recommend."},
{"question":"Customer service?","options":["A) Chatbot","B) Cook","C) Draw","D) Sing"],"correct":"A) Chatbot","explanation":"Customer support."},
],
},

'Reasoning and Planning in AI ':{
   'english': [
{"question":"What is reasoning in AI?","options":["A) Thinking logically","B) Storing data","C) Networking","D) Coding"],"correct":"A) Thinking logically","explanation":"Reasoning helps AI make decisions based on logic."},
{"question":"What is planning in AI?","options":["A) Writing code","B) Deciding actions","C) Storing data","D) Drawing"],"correct":"B) Deciding actions","explanation":"Planning selects steps to achieve goals."},
{"question":"Which type of reasoning uses facts?","options":["A) Deductive","B) Random","C) Loop","D) Sorting"],"correct":"A) Deductive","explanation":"Deductive reasoning uses known facts."},
{"question":"Which reasoning is based on experience?","options":["A) Inductive","B) Deductive","C) Static","D) Binary"],"correct":"A) Inductive","explanation":"Inductive reasoning learns from examples."},
{"question":"What is a goal in AI planning?","options":["A) Final result","B) Code","C) Loop","D) Variable"],"correct":"A) Final result","explanation":"Goal is the desired outcome."},
{"question":"What is a state in AI?","options":["A) Condition of system","B) Code line","C) Variable","D) Loop"],"correct":"A) Condition of system","explanation":"State represents current situation."},
{"question":"What is search in planning?","options":["A) Finding solution path","B) Coding","C) Storing","D) Deleting"],"correct":"A) Finding solution path","explanation":"Search explores possible actions."},
{"question":"What is heuristic?","options":["A) Rule of thumb","B) Loop","C) Variable","D) Data"],"correct":"A) Rule of thumb","explanation":"Heuristic guides search efficiently."},
{"question":"Which algorithm is used in planning?","options":["A) A*","B) Bubble sort","C) Binary search","D) Merge"],"correct":"A) A*","explanation":"A* is widely used for pathfinding."},
{"question":"What is problem-solving in AI?","options":["A) Finding solution","B) Coding","C) Drawing","D) Saving"],"correct":"A) Finding solution","explanation":"AI solves problems using reasoning and planning."},
],

'tamil': [
{"question":"Reasoning என்றால்?","options":["A) Logical thinking","B) Data store","C) Network","D) Code"],"correct":"A) Logical thinking","explanation":"AI நியாயமாக முடிவு எடுக்க உதவும்."},
{"question":"Planning என்றால்?","options":["A) Code","B) Action decide","C) Store","D) Draw"],"correct":"B) Action decide","explanation":"Goal அடைய steps தேர்வு."},
{"question":"Fact-based reasoning?","options":["A) Deductive","B) Random","C) Loop","D) Sort"],"correct":"A) Deductive","explanation":"Known facts பயன்படுத்தும்."},
{"question":"Experience-based reasoning?","options":["A) Inductive","B) Deductive","C) Static","D) Binary"],"correct":"A) Inductive","explanation":"Examples-ல் இருந்து கற்றல்."},
{"question":"Goal என்றால்?","options":["A) Final result","B) Code","C) Loop","D) Variable"],"correct":"A) Final result","explanation":"இறுதி முடிவு."},
{"question":"State என்றால்?","options":["A) Condition","B) Code line","C) Variable","D) Loop"],"correct":"A) Condition","explanation":"Current situation."},
{"question":"Search என்றால்?","options":["A) Solution find","B) Code","C) Store","D) Delete"],"correct":"A) Solution find","explanation":"Possible paths தேடும்."},
{"question":"Heuristic?","options":["A) Rule","B) Loop","C) Variable","D) Data"],"correct":"A) Rule","explanation":"Search guide செய்யும்."},
{"question":"Planning algorithm?","options":["A) A*","B) Bubble","C) Binary","D) Merge"],"correct":"A) A*","explanation":"Path finding-க்கு பயன்படும்."},
{"question":"Problem solving?","options":["A) Solution find","B) Code","C) Draw","D) Save"],"correct":"A) Solution find","explanation":"AI பிரச்சனை தீர்க்கும்."},
],

'tanglish': [
{"question":"Reasoning na enna?","options":["A) Logical think","B) Store","C) Network","D) Code"],"correct":"A) Logical think","explanation":"AI logic use pannum."},
{"question":"Planning na?","options":["A) Code","B) Action decide","C) Store","D) Draw"],"correct":"B) Action decide","explanation":"Goal achieve panna steps."},
{"question":"Fact reasoning?","options":["A) Deductive","B) Random","C) Loop","D) Sort"],"correct":"A) Deductive","explanation":"Facts use pannum."},
{"question":"Experience reasoning?","options":["A) Inductive","B) Deductive","C) Static","D) Binary"],"correct":"A) Inductive","explanation":"Examples la irundhu kathukum."},
{"question":"Goal na?","options":["A) Final","B) Code","C) Loop","D) Variable"],"correct":"A) Final","explanation":"Final output."},
{"question":"State na?","options":["A) Condition","B) Code","C) Var","D) Loop"],"correct":"A) Condition","explanation":"Current situation."},
{"question":"Search na?","options":["A) Solution find","B) Code","C) Store","D) Delete"],"correct":"A) Solution find","explanation":"Paths explore pannum."},
{"question":"Heuristic?","options":["A) Rule","B) Loop","C) Var","D) Data"],"correct":"A) Rule","explanation":"Guide pannum."},
{"question":"Algorithm?","options":["A) A*","B) Bubble","C) Binary","D) Merge"],"correct":"A) A*","explanation":"Path find pannum."},
{"question":"Problem solving?","options":["A) Solution","B) Code","C) Draw","D) Save"],"correct":"A) Solution","explanation":"Problem solve pannum."},
],

'hindi': [
{"question":"Reasoning क्या है?","options":["A) Logical सोच","B) Store","C) Network","D) Code"],"correct":"A) Logical सोच","explanation":"AI तर्क से निर्णय लेता है।"},
{"question":"Planning क्या है?","options":["A) Code","B) Action decide","C) Store","D) Draw"],"correct":"B) Action decide","explanation":"Goal पाने के लिए steps।"},
{"question":"Fact reasoning?","options":["A) Deductive","B) Random","C) Loop","D) Sort"],"correct":"A) Deductive","explanation":"Facts का उपयोग।"},
{"question":"Experience reasoning?","options":["A) Inductive","B) Deductive","C) Static","D) Binary"],"correct":"A) Inductive","explanation":"Examples से सीखता है।"},
{"question":"Goal?","options":["A) Final","B) Code","C) Loop","D) Var"],"correct":"A) Final","explanation":"अंतिम परिणाम।"},
{"question":"State?","options":["A) Condition","B) Code","C) Var","D) Loop"],"correct":"A) Condition","explanation":"Current स्थिति।"},
{"question":"Search?","options":["A) Solution","B) Code","C) Store","D) Delete"],"correct":"A) Solution","explanation":"Paths खोजता है।"},
{"question":"Heuristic?","options":["A) Rule","B) Loop","C) Var","D) Data"],"correct":"A) Rule","explanation":"Guide करता है।"},
{"question":"Algorithm?","options":["A) A*","B) Bubble","C) Binary","D) Merge"],"correct":"A) A*","explanation":"Path finding।"},
{"question":"Problem solving?","options":["A) Solution","B) Code","C) Draw","D) Save"],"correct":"A) Solution","explanation":"समस्या हल करता है।"},
],

'malayalam': [
{"question":"Reasoning എന്താണ്?","options":["A) Logical ചിന്ത","B) Store","C) Network","D) Code"],"correct":"A) Logical ചിന്ത","explanation":"AI തർക്കത്തോടെ തീരുമാനിക്കുന്നു."},
{"question":"Planning എന്താണ്?","options":["A) Code","B) Action decide","C) Store","D) Draw"],"correct":"B) Action decide","explanation":"Goal നേടാൻ steps."},
{"question":"Fact reasoning?","options":["A) Deductive","B) Random","C) Loop","D) Sort"],"correct":"A) Deductive","explanation":"Facts ഉപയോഗിക്കുന്നു."},
{"question":"Experience reasoning?","options":["A) Inductive","B) Deductive","C) Static","D) Binary"],"correct":"A) Inductive","explanation":"Examples നിന്ന് പഠിക്കുന്നു."},
{"question":"Goal?","options":["A) Final","B) Code","C) Loop","D) Var"],"correct":"A) Final","explanation":"അവസാന ഫലം."},
{"question":"State?","options":["A) Condition","B) Code","C) Var","D) Loop"],"correct":"A) Condition","explanation":"Current സ്ഥിതി."},
{"question":"Search?","options":["A) Solution","B) Code","C) Store","D) Delete"],"correct":"A) Solution","explanation":"Paths കണ്ടെത്തുന്നു."},
{"question":"Heuristic?","options":["A) Rule","B) Loop","C) Var","D) Data"],"correct":"A) Rule","explanation":"Guide ചെയ്യുന്നു."},
{"question":"Algorithm?","options":["A) A*","B) Bubble","C) Binary","D) Merge"],"correct":"A) A*","explanation":"Path finding."},
{"question":"Problem solving?","options":["A) Solution","B) Code","C) Draw","D) Save"],"correct":"A) Solution","explanation":"പ്രശ്നം പരിഹരിക്കുന്നു."},
],
},

'Future of AI':{
   'english': [
{"question":"What is the future of AI?","options":["A) Advanced intelligent systems","B) No development","C) Only hardware","D) Only networking"],"correct":"A) Advanced intelligent systems","explanation":"AI will become more advanced and capable."},
{"question":"Which field will AI impact?","options":["A) Healthcare","B) Education","C) Business","D) All of the above"],"correct":"D) All of the above","explanation":"AI impacts multiple industries."},
{"question":"What is automation in AI?","options":["A) Manual work","B) Machine performing tasks","C) Writing code","D) Networking"],"correct":"B) Machine performing tasks","explanation":"AI automates repetitive tasks."},
{"question":"What is AI in healthcare?","options":["A) Surgery assistance","B) Gaming","C) Networking","D) Coding"],"correct":"A) Surgery assistance","explanation":"AI helps doctors in diagnosis and surgery."},
{"question":"What is job impact of AI?","options":["A) Job loss only","B) Job creation only","C) Both loss and creation","D) No impact"],"correct":"C) Both loss and creation","explanation":"AI changes job market."},
{"question":"What is smart city?","options":["A) Village","B) AI-powered city","C) Small town","D) Manual system"],"correct":"B) AI-powered city","explanation":"AI improves city management."},
{"question":"What is autonomous vehicle?","options":["A) Manual car","B) Self-driving car","C) Bicycle","D) Bus"],"correct":"B) Self-driving car","explanation":"AI enables vehicles to drive automatically."},
{"question":"What is AI in education?","options":["A) Personalized learning","B) Manual teaching","C) No learning","D) Only exams"],"correct":"A) Personalized learning","explanation":"AI customizes learning experience."},
{"question":"What is risk of AI?","options":["A) Bias","B) Privacy issues","C) Security risks","D) All of the above"],"correct":"D) All of the above","explanation":"AI has multiple risks."},
{"question":"Why is future AI important?","options":["A) Innovation","B) Efficiency","C) Growth","D) All of the above"],"correct":"D) All of the above","explanation":"AI drives progress and innovation."},
],

'tamil': [
{"question":"AI எதிர்காலம்?","options":["A) Advanced systems","B) No growth","C) Hardware மட்டும்","D) Network மட்டும்"],"correct":"A) Advanced systems","explanation":"AI அதிகமாக வளர்கிறது."},
{"question":"AI எந்த துறையில்?","options":["A) Healthcare","B) Education","C) Business","D) All"],"correct":"D) All","explanation":"அனைத்து துறைகளிலும் தாக்கம்."},
{"question":"Automation?","options":["A) Manual","B) Machine work","C) Code","D) Network"],"correct":"B) Machine work","explanation":"AI தானாக வேலை செய்யும்."},
{"question":"AI in healthcare?","options":["A) Surgery help","B) Game","C) Network","D) Code"],"correct":"A) Surgery help","explanation":"மருத்துவ உதவி."},
{"question":"Job impact?","options":["A) Loss","B) Create","C) Both","D) None"],"correct":"C) Both","explanation":"வேலை மாற்றம்."},
{"question":"Smart city?","options":["A) Village","B) AI city","C) Town","D) Manual"],"correct":"B) AI city","explanation":"AI நகர மேம்பாடு."},
{"question":"Autonomous vehicle?","options":["A) Manual","B) Self drive","C) Cycle","D) Bus"],"correct":"B) Self drive","explanation":"AI drive செய்கிறது."},
{"question":"AI in education?","options":["A) Personal learning","B) Manual","C) None","D) Exam"],"correct":"A) Personal learning","explanation":"Custom learning."},
{"question":"AI risk?","options":["A) Bias","B) Privacy","C) Security","D) All"],"correct":"D) All","explanation":"பல அபாயங்கள்."},
{"question":"Importance?","options":["A) Innovation","B) Efficiency","C) Growth","D) All"],"correct":"D) All","explanation":"AI வளர்ச்சி."},
],

'tanglish': [
{"question":"Future of AI na?","options":["A) Advanced systems","B) No growth","C) Hardware","D) Network"],"correct":"A) Advanced systems","explanation":"AI romba develop aagum."},
{"question":"AI impact?","options":["A) Health","B) Education","C) Business","D) All"],"correct":"D) All","explanation":"Ellathulayum impact irukum."},
{"question":"Automation?","options":["A) Manual","B) Machine work","C) Code","D) Network"],"correct":"B) Machine work","explanation":"Machines work pannum."},
{"question":"Healthcare?","options":["A) Surgery","B) Game","C) Network","D) Code"],"correct":"A) Surgery","explanation":"Doctors ku help pannum."},
{"question":"Job impact?","options":["A) Loss","B) Create","C) Both","D) None"],"correct":"C) Both","explanation":"Jobs change aagum."},
{"question":"Smart city?","options":["A) Village","B) AI city","C) Town","D) Manual"],"correct":"B) AI city","explanation":"AI manage pannum."},
{"question":"Autonomous vehicle?","options":["A) Manual","B) Self drive","C) Cycle","D) Bus"],"correct":"B) Self drive","explanation":"Self driving car."},
{"question":"Education?","options":["A) Personal","B) Manual","C) None","D) Exam"],"correct":"A) Personal","explanation":"Custom learning."},
{"question":"Risk?","options":["A) Bias","B) Privacy","C) Security","D) All"],"correct":"D) All","explanation":"Risks iruku."},
{"question":"Importance?","options":["A) Innovation","B) Efficiency","C) Growth","D) All"],"correct":"D) All","explanation":"Future growth."},
],

'hindi': [
{"question":"AI का भविष्य?","options":["A) Advanced systems","B) No growth","C) Hardware","D) Network"],"correct":"A) Advanced systems","explanation":"AI और उन्नत होगा।"},
{"question":"Impact?","options":["A) Health","B) Education","C) Business","D) All"],"correct":"D) All","explanation":"हर क्षेत्र में प्रभाव।"},
{"question":"Automation?","options":["A) Manual","B) Machine work","C) Code","D) Network"],"correct":"B) Machine work","explanation":"Machines काम करेंगी।"},
{"question":"Healthcare?","options":["A) Surgery","B) Game","C) Network","D) Code"],"correct":"A) Surgery","explanation":"Doctors को मदद।"},
{"question":"Job impact?","options":["A) Loss","B) Create","C) Both","D) None"],"correct":"C) Both","explanation":"Jobs बदलेंगे।"},
{"question":"Smart city?","options":["A) Village","B) AI city","C) Town","D) Manual"],"correct":"B) AI city","explanation":"AI city manage करेगा।"},
{"question":"Autonomous vehicle?","options":["A) Manual","B) Self drive","C) Cycle","D) Bus"],"correct":"B) Self drive","explanation":"Self driving car।"},
{"question":"Education?","options":["A) Personal","B) Manual","C) None","D) Exam"],"correct":"A) Personal","explanation":"Personalized learning।"},
{"question":"Risk?","options":["A) Bias","B) Privacy","C) Security","D) All"],"correct":"D) All","explanation":"कई जोखिम हैं।"},
{"question":"Importance?","options":["A) Innovation","B) Efficiency","C) Growth","D) All"],"correct":"D) All","explanation":"AI विकास लाता है।"},
],

'malayalam': [
{"question":"AIയുടെ ഭാവി?","options":["A) Advanced systems","B) No growth","C) Hardware","D) Network"],"correct":"A) Advanced systems","explanation":"AI കൂടുതൽ പുരോഗമിക്കും."},
{"question":"Impact?","options":["A) Health","B) Education","C) Business","D) All"],"correct":"D) All","explanation":"എല്ലാ മേഖലകളിലും ബാധിക്കും."},
{"question":"Automation?","options":["A) Manual","B) Machine work","C) Code","D) Network"],"correct":"B) Machine work","explanation":"Machines ജോലി ചെയ്യും."},
{"question":"Healthcare?","options":["A) Surgery","B) Game","C) Network","D) Code"],"correct":"A) Surgery","explanation":"Doctors-നെ സഹായിക്കുന്നു."},
{"question":"Job impact?","options":["A) Loss","B) Create","C) Both","D) None"],"correct":"C) Both","explanation":"Jobs മാറും."},
{"question":"Smart city?","options":["A) Village","B) AI city","C) Town","D) Manual"],"correct":"B) AI city","explanation":"AI city manage ചെയ്യും."},
{"question":"Autonomous vehicle?","options":["A) Manual","B) Self drive","C) Cycle","D) Bus"],"correct":"B) Self drive","explanation":"Self driving car."},
{"question":"Education?","options":["A) Personal","B) Manual","C) None","D) Exam"],"correct":"A) Personal","explanation":"Personalized learning."},
{"question":"Risk?","options":["A) Bias","B) Privacy","C) Security","D) All"],"correct":"D) All","explanation":"വിവിധ അപകടങ്ങൾ."},
{"question":"Importance?","options":["A) Innovation","B) Efficiency","C) Growth","D) All"],"correct":"D) All","explanation":"AI വളർച്ചയ്ക്ക് സഹായിക്കുന്നു."},
],
},#future of ai ends
'Expert Systems':{
'english': [
{"question":"What is an Expert System?","options":["A) AI system that mimics human expert","B) Database","C) Programming language","D) Hardware"],"correct":"A) AI system that mimics human expert","explanation":"Expert systems simulate decision-making of human experts."},
{"question":"Main component of Expert System?","options":["A) Knowledge base","B) Keyboard","C) Monitor","D) Network"],"correct":"A) Knowledge base","explanation":"Stores facts and rules."},
{"question":"What is inference engine?","options":["A) Processing unit","B) Input device","C) Storage","D) Output"],"correct":"A) Processing unit","explanation":"Applies rules to make decisions."},
{"question":"What is knowledge base?","options":["A) Data & rules","B) Code","C) Hardware","D) Memory only"],"correct":"A) Data & rules","explanation":"Contains expert knowledge."},
{"question":"What is rule in Expert System?","options":["A) IF-THEN statement","B) Loop","C) Variable","D) Function"],"correct":"A) IF-THEN statement","explanation":"Rules guide decision-making."},
{"question":"What is forward chaining?","options":["A) Data to goal","B) Goal to data","C) Random","D) Loop"],"correct":"A) Data to goal","explanation":"Starts from known facts."},
{"question":"What is backward chaining?","options":["A) Goal to data","B) Data to goal","C) Loop","D) Sort"],"correct":"A) Goal to data","explanation":"Starts from goal and works backward."},
{"question":"Application of Expert System?","options":["A) Medical diagnosis","B) Gaming","C) Networking","D) Drawing"],"correct":"A) Medical diagnosis","explanation":"Widely used in healthcare."},
{"question":"What is explanation facility?","options":["A) Explains decisions","B) Stores data","C) Input","D) Output"],"correct":"A) Explains decisions","explanation":"Helps users understand results."},
{"question":"Advantage of Expert System?","options":["A) Consistent decisions","B) Slow","C) Expensive","D) Limited"],"correct":"A) Consistent decisions","explanation":"Provides reliable results."},
],

'tamil': [
{"question":"Expert System என்றால்?","options":["A) மனித நிபுணரை போல AI","B) DB","C) Language","D) Hardware"],"correct":"A) மனித நிபுணரை போல AI","explanation":"மனித நிபுணர் முடிவை பின்பற்றும்."},
{"question":"Main component?","options":["A) Knowledge base","B) Keyboard","C) Monitor","D) Network"],"correct":"A) Knowledge base","explanation":"Facts & rules சேமிக்கும்."},
{"question":"Inference engine?","options":["A) Process","B) Input","C) Store","D) Output"],"correct":"A) Process","explanation":"Rules apply செய்து முடிவு."},
{"question":"Knowledge base?","options":["A) Data & rules","B) Code","C) Hardware","D) Memory"],"correct":"A) Data & rules","explanation":"Expert knowledge."},
{"question":"Rule?","options":["A) IF-THEN","B) Loop","C) Var","D) Func"],"correct":"A) IF-THEN","explanation":"Decision guide."},
{"question":"Forward chaining?","options":["A) Data→goal","B) Goal→data","C) Random","D) Loop"],"correct":"A) Data→goal","explanation":"Facts-ல் இருந்து தொடங்கும்."},
{"question":"Backward chaining?","options":["A) Goal→data","B) Data→goal","C) Loop","D) Sort"],"correct":"A) Goal→data","explanation":"Goal-ல் இருந்து தொடங்கும்."},
{"question":"Application?","options":["A) Medical","B) Game","C) Network","D) Draw"],"correct":"A) Medical","explanation":"Diagnosis பயன்பாடு."},
{"question":"Explanation facility?","options":["A) Explain","B) Store","C) Input","D) Output"],"correct":"A) Explain","explanation":"Result explain செய்யும்."},
{"question":"Advantage?","options":["A) Consistent","B) Slow","C) Costly","D) Limited"],"correct":"A) Consistent","explanation":"நிலையான முடிவு."},
],

'tanglish': [
{"question":"Expert System na?","options":["A) Human expert mathiri AI","B) DB","C) Lang","D) Hardware"],"correct":"A) Human expert mathiri AI","explanation":"Expert decision mimic pannum."},
{"question":"Main component?","options":["A) Knowledge base","B) Keyboard","C) Monitor","D) Network"],"correct":"A) Knowledge base","explanation":"Facts & rules store pannum."},
{"question":"Inference engine?","options":["A) Process","B) Input","C) Store","D) Output"],"correct":"A) Process","explanation":"Rules apply pannum."},
{"question":"Knowledge base?","options":["A) Data & rules","B) Code","C) Hardware","D) Memory"],"correct":"A) Data & rules","explanation":"Knowledge irukum."},
{"question":"Rule?","options":["A) IF-THEN","B) Loop","C) Var","D) Func"],"correct":"A) IF-THEN","explanation":"Decision rule."},
{"question":"Forward chaining?","options":["A) Data→goal","B) Goal→data","C) Random","D) Loop"],"correct":"A) Data→goal","explanation":"Facts la irundhu start."},
{"question":"Backward chaining?","options":["A) Goal→data","B) Data→goal","C) Loop","D) Sort"],"correct":"A) Goal→data","explanation":"Goal la irundhu start."},
{"question":"Application?","options":["A) Medical","B) Game","C) Network","D) Draw"],"correct":"A) Medical","explanation":"Diagnosis use."},
{"question":"Explanation facility?","options":["A) Explain","B) Store","C) Input","D) Output"],"correct":"A) Explain","explanation":"Result explain pannum."},
{"question":"Advantage?","options":["A) Consistent","B) Slow","C) Costly","D) Limited"],"correct":"A) Consistent","explanation":"Same result kudukum."},
],

'hindi': [
{"question":"Expert System क्या है?","options":["A) Human expert जैसा AI","B) DB","C) Language","D) Hardware"],"correct":"A) Human expert जैसा AI","explanation":"Expert के निर्णय को mimic करता है।"},
{"question":"Main component?","options":["A) Knowledge base","B) Keyboard","C) Monitor","D) Network"],"correct":"A) Knowledge base","explanation":"Facts और rules store करता है।"},
{"question":"Inference engine?","options":["A) Process","B) Input","C) Store","D) Output"],"correct":"A) Process","explanation":"Rules apply करता है।"},
{"question":"Knowledge base?","options":["A) Data & rules","B) Code","C) Hardware","D) Memory"],"correct":"A) Data & rules","explanation":"Expert knowledge।"},
{"question":"Rule?","options":["A) IF-THEN","B) Loop","C) Var","D) Func"],"correct":"A) IF-THEN","explanation":"Decision rules।"},
{"question":"Forward chaining?","options":["A) Data→goal","B) Goal→data","C) Random","D) Loop"],"correct":"A) Data→goal","explanation":"Facts से शुरू।"},
{"question":"Backward chaining?","options":["A) Goal→data","B) Data→goal","C) Loop","D) Sort"],"correct":"A) Goal→data","explanation":"Goal से शुरू।"},
{"question":"Application?","options":["A) Medical","B) Game","C) Network","D) Draw"],"correct":"A) Medical","explanation":"Diagnosis में उपयोग।"},
{"question":"Explanation facility?","options":["A) Explain","B) Store","C) Input","D) Output"],"correct":"A) Explain","explanation":"Result समझाता है।"},
{"question":"Advantage?","options":["A) Consistent","B) Slow","C) Costly","D) Limited"],"correct":"A) Consistent","explanation":"Reliable results।"},
],

'malayalam': [
{"question":"Expert System എന്താണ്?","options":["A) Human expert പോലുള്ള AI","B) DB","C) Language","D) Hardware"],"correct":"A) Human expert പോലുള്ള AI","explanation":"Expert decision mimic ചെയ്യുന്നു."},
{"question":"Main component?","options":["A) Knowledge base","B) Keyboard","C) Monitor","D) Network"],"correct":"A) Knowledge base","explanation":"Facts & rules store ചെയ്യുന്നു."},
{"question":"Inference engine?","options":["A) Process","B) Input","C) Store","D) Output"],"correct":"A) Process","explanation":"Rules apply ചെയ്യുന്നു."},
{"question":"Knowledge base?","options":["A) Data & rules","B) Code","C) Hardware","D) Memory"],"correct":"A) Data & rules","explanation":"Expert knowledge."},
{"question":"Rule?","options":["A) IF-THEN","B) Loop","C) Var","D) Func"],"correct":"A) IF-THEN","explanation":"Decision rules."},
{"question":"Forward chaining?","options":["A) Data→goal","B) Goal→data","C) Random","D) Loop"],"correct":"A) Data→goal","explanation":"Facts-ൽ നിന്ന് ആരംഭിക്കുന്നു."},
{"question":"Backward chaining?","options":["A) Goal→data","B) Data→goal","C) Loop","D) Sort"],"correct":"A) Goal→data","explanation":"Goal-ൽ നിന്ന് ആരംഭിക്കുന്നു."},
{"question":"Application?","options":["A) Medical","B) Game","C) Network","D) Draw"],"correct":"A) Medical","explanation":"Diagnosis ഉപയോഗിക്കുന്നു."},
{"question":"Explanation facility?","options":["A) Explain","B) Store","C) Input","D) Output"],"correct":"A) Explain","explanation":"Result വിശദീകരിക്കുന്നു."},
{"question":"Advantage?","options":["A) Consistent","B) Slow","C) Costly","D) Limited"],"correct":"A) Consistent","explanation":"Reliable results."},
],
}#expert systems ends
},  # end ai topics

# ─────────────────── ML ────────────────────────────────────────
'ml': {
'What is ML?': {
'english': [
  {"question":"What does ML stand for?","options":["A) Machine Language","B) Machine Learning","C) Meta Logic","D) Model Learning"],"correct":"B) Machine Learning","explanation":"ML = Machine Learning."},
  {"question":"ML is a subset of?","options":["A) Hardware","B) Networking","C) AI","D) Databases"],"correct":"C) AI","explanation":"ML is a subset of Artificial Intelligence."},
  {"question":"ML learns from?","options":["A) Programmer rules only","B) Data","C) Hardware specs","D) Network packets"],"correct":"B) Data","explanation":"ML algorithms learn patterns from data."},
  {"question":"Which is a type of ML?","options":["A) Supervised Learning","B) Hardware Learning","C) Network Learning","D) Script Learning"],"correct":"A) Supervised Learning","explanation":"Supervised Learning is a major type of ML."},
  {"question":"ML is used for?","options":["A) Only sorting files","B) Making predictions from data","C) Only formatting text","D) Only connecting hardware"],"correct":"B) Making predictions from data","explanation":"ML makes predictions and decisions from data."},
  {"question":"What does a ML model do?","options":["A) Stores data only","B) Learns patterns and predicts","C) Formats text","D) Controls hardware"],"correct":"B) Learns patterns and predicts","explanation":"ML models learn patterns to make predictions."},
  {"question":"Which Python library is used for ML?","options":["A) Django","B) React","C) scikit-learn","D) Bootstrap"],"correct":"C) scikit-learn","explanation":"scikit-learn is a popular Python ML library."},
  {"question":"Supervised learning needs?","options":["A) No data","B) Labelled data","C) Only images","D) Only text"],"correct":"B) Labelled data","explanation":"Supervised learning uses labelled input-output pairs."},
  {"question":"What is a training dataset?","options":["A) Data to test the model","B) Data to train/teach the model","C) Random data","D) Database tables"],"correct":"B) Data to train/teach the model","explanation":"Training data is used to fit the model."},
  {"question":"What is overfitting?","options":["A) Model too simple","B) Model memorises training data, fails on new data","C) No training done","D) Model runs too slow"],"correct":"B) Model memorises training data, fails on new data","explanation":"Overfitting = poor generalisation."},
  {"question":"ML applications include?","options":["A) Spam detection","B) OS kernel","C) Circuit design","D) Power supply"],"correct":"A) Spam detection","explanation":"Spam detection is a common ML application."},
  {"question":"What is accuracy in ML?","options":["A) Speed of model","B) Percentage of correct predictions","C) Size of dataset","D) Number of features"],"correct":"B) Percentage of correct predictions","explanation":"Accuracy = correct predictions / total × 100."},
],
'tamil': [
  {"question":"ML-ன் full form என்ன?","options":["A) Machine Language","B) Machine Learning","C) Meta Logic","D) Model Learning"],"correct":"B) Machine Learning","explanation":"ML = Machine Learning (இயந்திர கற்றல்)."},
  {"question":"ML எதன் subset?","options":["A) Hardware","B) Networking","C) AI","D) Databases"],"correct":"C) AI","explanation":"ML Artificial Intelligence-இன் subset."},
  {"question":"ML எதிலிருந்து கற்கிறது?","options":["A) Programmer rules மட்டும்","B) Data","C) Hardware specs","D) Network packets"],"correct":"B) Data","explanation":"ML algorithms data-லிருந்து patterns கற்கும்."},
  {"question":"ML-இன் வகை எது?","options":["A) Supervised Learning","B) Hardware Learning","C) Network Learning","D) Script Learning"],"correct":"A) Supervised Learning","explanation":"Supervised Learning ML-இன் முக்கிய வகை."},
  {"question":"ML எதற்கு பயன்படுகிறது?","options":["A) Files sort மட்டும்","B) Data-லிருந்து predictions","C) Text format மட்டும்","D) Hardware connect மட்டும்"],"correct":"B) Data-லிருந்து predictions","explanation":"ML data-லிருந்து predictions மற்றும் decisions செய்யும்."},
  {"question":"ML model என்ன செய்யும்?","options":["A) Data store மட்டும்","B) Patterns கற்று predict செய்யும்","C) Text format செய்யும்","D) Hardware control செய்யும்"],"correct":"B) Patterns கற்று predict செய்யும்","explanation":"ML models predictions செய்ய patterns கற்கும்."},
  {"question":"ML-க்கு எந்த Python library?","options":["A) Django","B) React","C) scikit-learn","D) Bootstrap"],"correct":"C) scikit-learn","explanation":"scikit-learn பிரபலமான Python ML library."},
  {"question":"Supervised learning-க்கு என்ன தேவை?","options":["A) Data இல்லை","B) Labelled data","C) Images மட்டும்","D) Text மட்டும்"],"correct":"B) Labelled data","explanation":"Supervised learning labelled input-output pairs பயன்படுத்தும்."},
  {"question":"Training dataset என்றால் என்ன?","options":["A) Model test செய்ய data","B) Model train செய்ய data","C) Random data","D) Database tables"],"correct":"B) Model train செய்ய data","explanation":"Training data model fit செய்ய பயன்படும்."},
  {"question":"Overfitting என்றால் என்ன?","options":["A) Model மிக simple","B) Training data memorize செய்து new data-ல் fail","C) Training இல்லை","D) Model மிக slow"],"correct":"B) Training data memorize செய்து new data-ல் fail","explanation":"Overfitting = poor generalisation."},
  {"question":"ML applications எது?","options":["A) Spam detection","B) OS kernel","C) Circuit design","D) Power supply"],"correct":"A) Spam detection","explanation":"Spam detection ஒரு பொதுவான ML application."},
  {"question":"ML-ல் accuracy என்றால் என்ன?","options":["A) Model வேகம்","B) சரியான predictions சதவீதம்","C) Dataset அளவு","D) Features எண்ணிக்கை"],"correct":"B) சரியான predictions சதவீதம்","explanation":"Accuracy = correct / total × 100."},
],
'tanglish': [
  {"question":"ML-oda full form enna?","options":["A) Machine Language","B) Machine Learning","C) Meta Logic","D) Model Learning"],"correct":"B) Machine Learning","explanation":"ML = Machine Learning."},
  {"question":"ML etho subset?","options":["A) Hardware","B) Networking","C) AI","D) Databases"],"correct":"C) AI","explanation":"ML Artificial Intelligence-oda subset."},
  {"question":"ML engirundhu kallukum?","options":["A) Programmer rules mattum","B) Data","C) Hardware specs","D) Network packets"],"correct":"B) Data","explanation":"ML algorithms data-la irundhu patterns kallukum."},
  {"question":"ML-oda type ethu?","options":["A) Supervised Learning","B) Hardware Learning","C) Network Learning","D) Script Learning"],"correct":"A) Supervised Learning","explanation":"Supervised Learning ML-oda mookiya type."},
  {"question":"ML endhatharku use aagum?","options":["A) Files sort mattum","B) Data-la irundhu predictions","C) Text format mattum","D) Hardware connect mattum"],"correct":"B) Data-la irundhu predictions","explanation":"ML data-la irundhu predictions-um decisions-um pannum."},
  {"question":"ML model enna pannum?","options":["A) Data store mattum","B) Patterns kalluthu predict pannum","C) Text format pannum","D) Hardware control pannum"],"correct":"B) Patterns kalluthu predict pannum","explanation":"ML models predictions panna patterns kallukum."},
  {"question":"ML-ku ethu Python library?","options":["A) Django","B) React","C) scikit-learn","D) Bootstrap"],"correct":"C) scikit-learn","explanation":"scikit-learn famous Python ML library."},
  {"question":"Supervised learning-ku enna vennum?","options":["A) Data vendam","B) Labelled data","C) Images mattum","D) Text mattum"],"correct":"B) Labelled data","explanation":"Supervised learning labelled input-output pairs use pannum."},
  {"question":"Training dataset enna?","options":["A) Model test panna data","B) Model train panna data","C) Random data","D) Database tables"],"correct":"B) Model train panna data","explanation":"Training data model fit panna use aagum."},
  {"question":"Overfitting enna?","options":["A) Model romba simple","B) Training data memorize panni new data-la fail","C) Training illai","D) Model romba slow"],"correct":"B) Training data memorize panni new data-la fail","explanation":"Overfitting = poor generalisation."},
  {"question":"ML application ethu?","options":["A) Spam detection","B) OS kernel","C) Circuit design","D) Power supply"],"correct":"A) Spam detection","explanation":"Spam detection oru common ML application."},
  {"question":"ML-la accuracy enna?","options":["A) Model vegam","B) Correct predictions percentage","C) Dataset size","D) Features count"],"correct":"B) Correct predictions percentage","explanation":"Accuracy = correct / total × 100."},
],
'hindi': [
  {"question":"ML का full form?","options":["A) Machine Language","B) Machine Learning","C) Meta Logic","D) Model Learning"],"correct":"B) Machine Learning","explanation":"ML = Machine Learning (मशीन लर्निंग)."},
  {"question":"ML किसका subset है?","options":["A) Hardware","B) Networking","C) AI","D) Databases"],"correct":"C) AI","explanation":"ML Artificial Intelligence का subset है।"},
  {"question":"ML किससे सीखता है?","options":["A) सिर्फ programmer rules","B) Data","C) Hardware specs","D) Network packets"],"correct":"B) Data","explanation":"ML algorithms data से patterns सीखते हैं।"},
  {"question":"ML का प्रकार कौन सा है?","options":["A) Supervised Learning","B) Hardware Learning","C) Network Learning","D) Script Learning"],"correct":"A) Supervised Learning","explanation":"Supervised Learning ML का मुख्य प्रकार है।"},
  {"question":"ML किसके लिए उपयोग होता है?","options":["A) सिर्फ files sort","B) Data से predictions","C) सिर्फ text format","D) सिर्फ hardware connect"],"correct":"B) Data से predictions","explanation":"ML data से predictions और decisions बनाता है।"},
  {"question":"ML model क्या करता है?","options":["A) सिर्फ data store","B) Patterns सीखकर predict करता है","C) Text format करता है","D) Hardware control करता है"],"correct":"B) Patterns सीखकर predict करता है","explanation":"ML models predictions के लिए patterns सीखते हैं।"},
  {"question":"ML के लिए Python library?","options":["A) Django","B) React","C) scikit-learn","D) Bootstrap"],"correct":"C) scikit-learn","explanation":"scikit-learn एक popular Python ML library है।"},
  {"question":"Supervised learning के लिए क्या चाहिए?","options":["A) कोई data नहीं","B) Labelled data","C) सिर्फ images","D) सिर्फ text"],"correct":"B) Labelled data","explanation":"Supervised learning labelled input-output pairs उपयोग करती है।"},
  {"question":"Training dataset क्या है?","options":["A) Model test करने का data","B) Model train करने का data","C) Random data","D) Database tables"],"correct":"B) Model train करने का data","explanation":"Training data से model fit किया जाता है।"},
  {"question":"Overfitting क्या है?","options":["A) Model बहुत simple","B) Training data याद कर नए data पर fail","C) Training नहीं हुई","D) Model बहुत slow"],"correct":"B) Training data याद कर नए data पर fail","explanation":"Overfitting = poor generalisation."},
  {"question":"ML application कौन सा है?","options":["A) Spam detection","B) OS kernel","C) Circuit design","D) Power supply"],"correct":"A) Spam detection","explanation":"Spam detection एक आम ML application है।"},
  {"question":"ML में accuracy क्या है?","options":["A) Model की speed","B) सही predictions का प्रतिशत","C) Dataset का size","D) Features की संख्या"],"correct":"B) सही predictions का प्रतिशत","explanation":"Accuracy = correct / total × 100."},
],
'malayalam': [
  {"question":"ML-ന്റെ full form?","options":["A) Machine Language","B) Machine Learning","C) Meta Logic","D) Model Learning"],"correct":"B) Machine Learning","explanation":"ML = Machine Learning (യന്ത്ര പഠനം)."},
  {"question":"ML ഏതിന്റെ subset?","options":["A) Hardware","B) Networking","C) AI","D) Databases"],"correct":"C) AI","explanation":"ML Artificial Intelligence-ന്റെ subset ആണ്."},
  {"question":"ML എവിടെ നിന്ന് പഠിക്കുന്നു?","options":["A) Programmer rules മാത്രം","B) Data","C) Hardware specs","D) Network packets"],"correct":"B) Data","explanation":"ML algorithms data-ൽ നിന്ന് patterns പഠിക്കുന്നു."},
  {"question":"ML-ന്റെ ഒരു type?","options":["A) Supervised Learning","B) Hardware Learning","C) Network Learning","D) Script Learning"],"correct":"A) Supervised Learning","explanation":"Supervised Learning ML-ന്റെ പ്രധാന type ആണ്."},
  {"question":"ML ഏതിന് ഉപയോഗിക്കുന്നു?","options":["A) Files sort മാത്രം","B) Data-ൽ നിന്ന് predictions","C) Text format മാത്രം","D) Hardware connect മാത്രം"],"correct":"B) Data-ൽ നിന്ന് predictions","explanation":"ML data-ൽ നിന്ന് predictions-ഉം decisions-ഉം ചെയ്യുന്നു."},
  {"question":"ML model എന്ത് ചെയ്യുന്നു?","options":["A) Data store മാത്രം","B) Patterns പഠിച്ച് predict ചെയ്യുന്നു","C) Text format ചെയ്യുന്നു","D) Hardware control ചെയ്യുന്നു"],"correct":"B) Patterns പഠിച്ച് predict ചെയ്യുന്നു","explanation":"ML models predictions ചെയ്യാൻ patterns പഠിക്കുന്നു."},
  {"question":"ML-ന് Python library?","options":["A) Django","B) React","C) scikit-learn","D) Bootstrap"],"correct":"C) scikit-learn","explanation":"scikit-learn ഒരു popular Python ML library ആണ്."},
  {"question":"Supervised learning-ന് എന്ത് വേണം?","options":["A) Data വേണ്ട","B) Labelled data","C) Images മാത്രം","D) Text മാത്രം"],"correct":"B) Labelled data","explanation":"Supervised learning labelled input-output pairs ഉപയോഗിക്കുന്നു."},
  {"question":"Training dataset എന്നാൽ?","options":["A) Model test ചെയ്യാൻ data","B) Model train ചെയ്യാൻ data","C) Random data","D) Database tables"],"correct":"B) Model train ചെയ്യാൻ data","explanation":"Training data model fit ചെയ്യാൻ ഉപയോഗിക്കുന്നു."},
  {"question":"Overfitting എന്നാൽ?","options":["A) Model വളരെ simple","B) Training data memorize ചെയ്ത് new data-ൽ fail","C) Training ഇല്ല","D) Model വളരെ slow"],"correct":"B) Training data memorize ചെയ്ത് new data-ൽ fail","explanation":"Overfitting = poor generalisation."},
  {"question":"ML application ഏതാണ്?","options":["A) Spam detection","B) OS kernel","C) Circuit design","D) Power supply"],"correct":"A) Spam detection","explanation":"Spam detection ഒരു common ML application ആണ്."},
  {"question":"ML-ൽ accuracy എന്നാൽ?","options":["A) Model-ന്റെ speed","B) ശരിയായ predictions-ന്റെ ശതമാനം","C) Dataset-ന്റെ size","D) Features-ന്റെ എണ്ണം"],"correct":"B) ശരിയായ predictions-ന്റെ ശതമാനം","explanation":"Accuracy = correct / total × 100."},
],
},  # end What is ML?
'Types of ML':{
'english': [
{"question":"What is Machine Learning?","options":["A) Learning from data","B) Manual coding","C) Hardware design","D) Networking"],"correct":"A) Learning from data","explanation":"ML enables systems to learn from data."},
{"question":"How many main types of ML?","options":["A) 3","B) 2","C) 4","D) 5"],"correct":"A) 3","explanation":"Supervised, Unsupervised, Reinforcement."},
{"question":"Supervised Learning means?","options":["A) Learning with labeled data","B) No data","C) Only testing","D) Manual work"],"correct":"A) Learning with labeled data","explanation":"Uses input-output pairs."},
{"question":"Unsupervised Learning means?","options":["A) No labeled data","B) Only labels","C) Manual coding","D) Testing only"],"correct":"A) No labeled data","explanation":"Finds hidden patterns."},
{"question":"Reinforcement Learning means?","options":["A) Learning with rewards","B) No learning","C) Only data storage","D) Coding"],"correct":"A) Learning with rewards","explanation":"Agent learns via rewards/penalties."},
{"question":"Example of supervised learning?","options":["A) Spam detection","B) Clustering","C) Gaming","D) Random search"],"correct":"A) Spam detection","explanation":"Uses labeled data."},
{"question":"Example of unsupervised learning?","options":["A) Clustering","B) Classification","C) Regression","D) Sorting"],"correct":"A) Clustering","explanation":"Groups similar data."},
{"question":"Example of reinforcement learning?","options":["A) Game playing AI","B) Sorting","C) Searching","D) Printing"],"correct":"A) Game playing AI","explanation":"Learns through actions and rewards."},
{"question":"Which ML type uses feedback?","options":["A) Reinforcement","B) Supervised","C) Unsupervised","D) None"],"correct":"A) Reinforcement","explanation":"Uses reward signals."},
{"question":"Which ML type finds hidden patterns?","options":["A) Unsupervised","B) Supervised","C) Reinforcement","D) All"],"correct":"A) Unsupervised","explanation":"Discovers structure in data."},
],

'tamil': [
{"question":"Machine Learning என்றால்?","options":["A) Data மூலம் கற்றல்","B) Manual coding","C) Hardware","D) Network"],"correct":"A) Data மூலம் கற்றல்","explanation":"Data-இல் இருந்து கற்றுக்கொள்கிறது."},
{"question":"ML வகைகள் எத்தனை?","options":["A) 3","B) 2","C) 4","D) 5"],"correct":"A) 3","explanation":"Supervised, Unsupervised, Reinforcement."},
{"question":"Supervised Learning?","options":["A) Labeled data","B) Data இல்லை","C) Testing","D) Manual"],"correct":"A) Labeled data","explanation":"Input-output data உண்டு."},
{"question":"Unsupervised Learning?","options":["A) Label இல்லை","B) Label மட்டும்","C) Coding","D) Test"],"correct":"A) Label இல்லை","explanation":"Pattern கண்டறியும்."},
{"question":"Reinforcement Learning?","options":["A) Reward மூலம்","B) இல்லை","C) Storage","D) Coding"],"correct":"A) Reward மூலம்","explanation":"Reward/penalty மூலம் கற்றல்."},
{"question":"Supervised example?","options":["A) Spam detect","B) Cluster","C) Game","D) Search"],"correct":"A) Spam detect","explanation":"Label data."},
{"question":"Unsupervised example?","options":["A) Cluster","B) Classify","C) Regression","D) Sort"],"correct":"A) Cluster","explanation":"Data group."},
{"question":"Reinforcement example?","options":["A) Game AI","B) Sort","C) Search","D) Print"],"correct":"A) Game AI","explanation":"Reward learning."},
{"question":"Feedback use?","options":["A) Reinforcement","B) Supervised","C) Unsupervised","D) None"],"correct":"A) Reinforcement","explanation":"Reward feedback."},
{"question":"Hidden pattern?","options":["A) Unsupervised","B) Supervised","C) Reinforcement","D) All"],"correct":"A) Unsupervised","explanation":"Pattern கண்டறியும்."},
],

'tanglish': [
{"question":"Machine Learning na?","options":["A) Data la irundhu kathukaradhu","B) Manual coding","C) Hardware","D) Network"],"correct":"A) Data la irundhu kathukaradhu","explanation":"Data use panni learn pannum."},
{"question":"ML types evlo?","options":["A) 3","B) 2","C) 4","D) 5"],"correct":"A) 3","explanation":"3 main types."},
{"question":"Supervised na?","options":["A) Labeled data","B) No data","C) Test","D) Manual"],"correct":"A) Labeled data","explanation":"Label irukum."},
{"question":"Unsupervised na?","options":["A) No label","B) Label only","C) Coding","D) Test"],"correct":"A) No label","explanation":"Pattern find pannum."},
{"question":"Reinforcement na?","options":["A) Reward","B) None","C) Storage","D) Coding"],"correct":"A) Reward","explanation":"Reward base learning."},
{"question":"Supervised example?","options":["A) Spam detect","B) Cluster","C) Game","D) Search"],"correct":"A) Spam detect","explanation":"Label use pannum."},
{"question":"Unsupervised example?","options":["A) Cluster","B) Classify","C) Regression","D) Sort"],"correct":"A) Cluster","explanation":"Group pannum."},
{"question":"Reinforcement example?","options":["A) Game AI","B) Sort","C) Search","D) Print"],"correct":"A) Game AI","explanation":"Reward learning."},
{"question":"Feedback use?","options":["A) Reinforcement","B) Supervised","C) Unsupervised","D) None"],"correct":"A) Reinforcement","explanation":"Reward feedback."},
{"question":"Hidden pattern?","options":["A) Unsupervised","B) Supervised","C) Reinforcement","D) All"],"correct":"A) Unsupervised","explanation":"Pattern kandupidikum."},
],

'hindi': [
{"question":"Machine Learning क्या है?","options":["A) Data से सीखना","B) Manual coding","C) Hardware","D) Network"],"correct":"A) Data से सीखना","explanation":"Data से सीखता है।"},
{"question":"ML के प्रकार कितने?","options":["A) 3","B) 2","C) 4","D) 5"],"correct":"A) 3","explanation":"3 मुख्य प्रकार।"},
{"question":"Supervised Learning?","options":["A) Labeled data","B) No data","C) Test","D) Manual"],"correct":"A) Labeled data","explanation":"Label के साथ सीखना।"},
{"question":"Unsupervised Learning?","options":["A) No label","B) Label only","C) Coding","D) Test"],"correct":"A) No label","explanation":"Pattern ढूंढता है।"},
{"question":"Reinforcement Learning?","options":["A) Reward","B) None","C) Storage","D) Coding"],"correct":"A) Reward","explanation":"Reward से सीखता है।"},
{"question":"Supervised example?","options":["A) Spam detect","B) Cluster","C) Game","D) Search"],"correct":"A) Spam detect","explanation":"Label data।"},
{"question":"Unsupervised example?","options":["A) Cluster","B) Classify","C) Regression","D) Sort"],"correct":"A) Cluster","explanation":"Grouping करता है।"},
{"question":"Reinforcement example?","options":["A) Game AI","B) Sort","C) Search","D) Print"],"correct":"A) Game AI","explanation":"Reward learning।"},
{"question":"Feedback use?","options":["A) Reinforcement","B) Supervised","C) Unsupervised","D) None"],"correct":"A) Reinforcement","explanation":"Feedback use करता है।"},
{"question":"Hidden pattern?","options":["A) Unsupervised","B) Supervised","C) Reinforcement","D) All"],"correct":"A) Unsupervised","explanation":"Pattern ढूंढता है।"},
],

'malayalam': [
{"question":"Machine Learning എന്താണ്?","options":["A) Data ഉപയോഗിച്ച് പഠിക്കൽ","B) Manual coding","C) Hardware","D) Network"],"correct":"A) Data ഉപയോഗിച്ച് പഠിക്കൽ","explanation":"Data ഉപയോഗിച്ച് പഠിക്കുന്നു."},
{"question":"ML types എത്ര?","options":["A) 3","B) 2","C) 4","D) 5"],"correct":"A) 3","explanation":"3 types."},
{"question":"Supervised Learning?","options":["A) Labeled data","B) No data","C) Test","D) Manual"],"correct":"A) Labeled data","explanation":"Label ഉള്ള data."},
{"question":"Unsupervised Learning?","options":["A) No label","B) Label only","C) Coding","D) Test"],"correct":"A) No label","explanation":"Pattern കണ്ടെത്തുന്നു."},
{"question":"Reinforcement Learning?","options":["A) Reward","B) None","C) Storage","D) Coding"],"correct":"A) Reward","explanation":"Reward ഉപയോഗിച്ച് പഠിക്കുന്നു."},
{"question":"Supervised example?","options":["A) Spam detect","B) Cluster","C) Game","D) Search"],"correct":"A) Spam detect","explanation":"Label data ഉപയോഗിക്കുന്നു."},
{"question":"Unsupervised example?","options":["A) Cluster","B) Classify","C) Regression","D) Sort"],"correct":"A) Cluster","explanation":"Grouping."},
{"question":"Reinforcement example?","options":["A) Game AI","B) Sort","C) Search","D) Print"],"correct":"A) Game AI","explanation":"Reward learning."},
{"question":"Feedback use?","options":["A) Reinforcement","B) Supervised","C) Unsupervised","D) None"],"correct":"A) Reinforcement","explanation":"Feedback ഉപയോഗിക്കുന്നു."},
{"question":"Hidden pattern?","options":["A) Unsupervised","B) Supervised","C) Reinforcement","D) All"],"correct":"A) Unsupervised","explanation":"Pattern കണ്ടെത്തുന്നു."},
],
},
'Data Preprocessing':{
 'english': [
{"question":"What is data preprocessing?","options":["A) Preparing data for ML","B) Training model","C) Testing model","D) Deployment"],"correct":"A) Preparing data for ML","explanation":"It cleans and prepares data."},
{"question":"Why is preprocessing needed?","options":["A) Improve accuracy","B) Reduce data","C) Increase errors","D) None"],"correct":"A) Improve accuracy","explanation":"Clean data improves performance."},
{"question":"Handling missing values is called?","options":["A) Data cleaning","B) Data mining","C) Data storing","D) Data testing"],"correct":"A) Data cleaning","explanation":"Missing values are handled in cleaning."},
{"question":"Normalization means?","options":["A) Scaling data","B) Removing data","C) Sorting data","D) Printing data"],"correct":"A) Scaling data","explanation":"Values are scaled to a range."},
{"question":"Standardization means?","options":["A) Mean=0, Std=1","B) Remove data","C) Sort data","D) Print data"],"correct":"A) Mean=0, Std=1","explanation":"Transforms data distribution."},
{"question":"Outliers are?","options":["A) Extreme values","B) Normal values","C) Missing values","D) Labels"],"correct":"A) Extreme values","explanation":"Values far from others."},
{"question":"Encoding categorical data means?","options":["A) Convert to numbers","B) Delete data","C) Sort data","D) Print data"],"correct":"A) Convert to numbers","explanation":"ML needs numeric input."},
{"question":"Train-test split is used for?","options":["A) Model evaluation","B) Data cleaning","C) Encoding","D) Scaling"],"correct":"A) Model evaluation","explanation":"Separate data for training/testing."},
{"question":"Feature scaling helps in?","options":["A) Faster learning","B) Slower learning","C) No change","D) Data loss"],"correct":"A) Faster learning","explanation":"Improves convergence."},
{"question":"Removing duplicates is part of?","options":["A) Data cleaning","B) Training","C) Testing","D) Deployment"],"correct":"A) Data cleaning","explanation":"Duplicate data is removed."},
],

'tamil': [
{"question":"Data preprocessing என்றால்?","options":["A) Data தயார் செய்தல்","B) Training","C) Testing","D) Deploy"],"correct":"A) Data தயார் செய்தல்","explanation":"MLக்கு data தயாராகும்."},
{"question":"ஏன் preprocessing?","options":["A) Accuracy improve","B) Data குறை","C) Error அதிகம்","D) None"],"correct":"A) Accuracy improve","explanation":"சுத்தமான data நல்ல முடிவு தரும்."},
{"question":"Missing values handle?","options":["A) Cleaning","B) Mining","C) Store","D) Test"],"correct":"A) Cleaning","explanation":"Cleaning-ல் handle செய்கிறோம்."},
{"question":"Normalization?","options":["A) Scale","B) Remove","C) Sort","D) Print"],"correct":"A) Scale","explanation":"Range-க்கு மாற்றும்."},
{"question":"Standardization?","options":["A) Mean0 Std1","B) Remove","C) Sort","D) Print"],"correct":"A) Mean0 Std1","explanation":"Distribution மாற்றம்."},
{"question":"Outliers?","options":["A) Extreme","B) Normal","C) Missing","D) Label"],"correct":"A) Extreme","explanation":"வெளியே உள்ள values."},
{"question":"Encoding?","options":["A) Number convert","B) Delete","C) Sort","D) Print"],"correct":"A) Number convert","explanation":"Number ஆக மாற்றம்."},
{"question":"Train-test split?","options":["A) Evaluation","B) Cleaning","C) Encode","D) Scale"],"correct":"A) Evaluation","explanation":"Model test செய்யும்."},
{"question":"Feature scaling?","options":["A) Fast learning","B) Slow","C) None","D) Loss"],"correct":"A) Fast learning","explanation":"Speed அதிகரிக்கும்."},
{"question":"Duplicate remove?","options":["A) Cleaning","B) Train","C) Test","D) Deploy"],"correct":"A) Cleaning","explanation":"Duplicate நீக்கும்."},
],

'tanglish': [
{"question":"Data preprocessing na?","options":["A) Data prepare","B) Train","C) Test","D) Deploy"],"correct":"A) Data prepare","explanation":"ML ku data ready pannum."},
{"question":"Why preprocessing?","options":["A) Accuracy increase","B) Data reduce","C) Error increase","D) None"],"correct":"A) Accuracy increase","explanation":"Clean data better result."},
{"question":"Missing values handle?","options":["A) Cleaning","B) Mining","C) Store","D) Test"],"correct":"A) Cleaning","explanation":"Cleaning la handle pannum."},
{"question":"Normalization?","options":["A) Scale","B) Remove","C) Sort","D) Print"],"correct":"A) Scale","explanation":"Range la convert pannum."},
{"question":"Standardization?","options":["A) Mean0 Std1","B) Remove","C) Sort","D) Print"],"correct":"A) Mean0 Std1","explanation":"Distribution change pannum."},
{"question":"Outliers?","options":["A) Extreme","B) Normal","C) Missing","D) Label"],"correct":"A) Extreme","explanation":"Far values."},
{"question":"Encoding?","options":["A) Number convert","B) Delete","C) Sort","D) Print"],"correct":"A) Number convert","explanation":"Number aagum."},
{"question":"Train-test split?","options":["A) Evaluation","B) Cleaning","C) Encode","D) Scale"],"correct":"A) Evaluation","explanation":"Model test pannum."},
{"question":"Feature scaling?","options":["A) Fast learning","B) Slow","C) None","D) Loss"],"correct":"A) Fast learning","explanation":"Speed improve."},
{"question":"Duplicate remove?","options":["A) Cleaning","B) Train","C) Test","D) Deploy"],"correct":"A) Cleaning","explanation":"Duplicate remove pannum."},
],

'hindi': [
{"question":"Data preprocessing क्या है?","options":["A) Data तैयार करना","B) Training","C) Testing","D) Deploy"],"correct":"A) Data तैयार करना","explanation":"ML के लिए data तैयार होता है।"},
{"question":"Preprocessing क्यों?","options":["A) Accuracy बढ़ाना","B) Data कम करना","C) Error बढ़ाना","D) None"],"correct":"A) Accuracy बढ़ाना","explanation":"Clean data बेहतर होता है।"},
{"question":"Missing values handle?","options":["A) Cleaning","B) Mining","C) Store","D) Test"],"correct":"A) Cleaning","explanation":"Cleaning में handle होता है।"},
{"question":"Normalization?","options":["A) Scale","B) Remove","C) Sort","D) Print"],"correct":"A) Scale","explanation":"Range में बदलना।"},
{"question":"Standardization?","options":["A) Mean0 Std1","B) Remove","C) Sort","D) Print"],"correct":"A) Mean0 Std1","explanation":"Distribution बदलना।"},
{"question":"Outliers?","options":["A) Extreme","B) Normal","C) Missing","D) Label"],"correct":"A) Extreme","explanation":"Extreme values।"},
{"question":"Encoding?","options":["A) Number convert","B) Delete","C) Sort","D) Print"],"correct":"A) Number convert","explanation":"Numbers में बदलना।"},
{"question":"Train-test split?","options":["A) Evaluation","B) Cleaning","C) Encode","D) Scale"],"correct":"A) Evaluation","explanation":"Model test के लिए।"},
{"question":"Feature scaling?","options":["A) Fast learning","B) Slow","C) None","D) Loss"],"correct":"A) Fast learning","explanation":"Speed बढ़ती है।"},
{"question":"Duplicate remove?","options":["A) Cleaning","B) Train","C) Test","D) Deploy"],"correct":"A) Cleaning","explanation":"Duplicate हटाना।"},
],

'malayalam': [
{"question":"Data preprocessing എന്താണ്?","options":["A) Data തയ്യാറാക്കൽ","B) Training","C) Testing","D) Deploy"],"correct":"A) Data തയ്യാറാക്കൽ","explanation":"ML-നായി data തയ്യാറാക്കുന്നു."},
{"question":"Preprocessing എന്തിന്?","options":["A) Accuracy വർധിപ്പിക്കാൻ","B) Data കുറയ്ക്കാൻ","C) Error വർധിപ്പിക്കാൻ","D) None"],"correct":"A) Accuracy വർധിപ്പിക്കാൻ","explanation":"Clean data നല്ലതാണ്."},
{"question":"Missing values handle?","options":["A) Cleaning","B) Mining","C) Store","D) Test"],"correct":"A) Cleaning","explanation":"Cleaning-ൽ handle ചെയ്യുന്നു."},
{"question":"Normalization?","options":["A) Scale","B) Remove","C) Sort","D) Print"],"correct":"A) Scale","explanation":"Range-ൽ മാറ്റുന്നു."},
{"question":"Standardization?","options":["A) Mean0 Std1","B) Remove","C) Sort","D) Print"],"correct":"A) Mean0 Std1","explanation":"Distribution മാറ്റുന്നു."},
{"question":"Outliers?","options":["A) Extreme","B) Normal","C) Missing","D) Label"],"correct":"A) Extreme","explanation":"Extreme values."},
{"question":"Encoding?","options":["A) Number convert","B) Delete","C) Sort","D) Print"],"correct":"A) Number convert","explanation":"Number ആക്കുന്നു."},
{"question":"Train-test split?","options":["A) Evaluation","B) Cleaning","C) Encode","D) Scale"],"correct":"A) Evaluation","explanation":"Model test ചെയ്യാൻ."},
{"question":"Feature scaling?","options":["A) Fast learning","B) Slow","C) None","D) Loss"],"correct":"A) Fast learning","explanation":"Speed വർധിക്കുന്നു."},
{"question":"Duplicate remove?","options":["A) Cleaning","B) Train","C) Test","D) Deploy"],"correct":"A) Cleaning","explanation":"Duplicate നീക്കം ചെയ്യുന്നു."},
],    
},
'Linear Regression':{
'english': [
{"question":"What is Linear Regression?","options":["A) Predict continuous values","B) Classification","C) Clustering","D) Sorting"],"correct":"A) Predict continuous values","explanation":"Used for predicting numeric output."},
{"question":"Type of learning?","options":["A) Supervised","B) Unsupervised","C) Reinforcement","D) None"],"correct":"A) Supervised","explanation":"Uses labeled data."},
{"question":"Linear regression predicts?","options":["A) Continuous values","B) Categories","C) Clusters","D) Labels only"],"correct":"A) Continuous values","explanation":"Output is numeric."},
{"question":"Equation form?","options":["A) y = mx + c","B) x = y + c","C) y = x^2","D) y = log x"],"correct":"A) y = mx + c","explanation":"Basic linear equation."},
{"question":"m represents?","options":["A) Slope","B) Intercept","C) Error","D) Data"],"correct":"A) Slope","explanation":"Rate of change."},
{"question":"c represents?","options":["A) Intercept","B) Slope","C) Error","D) Data"],"correct":"A) Intercept","explanation":"Value when x=0."},
{"question":"Cost function used?","options":["A) MSE","B) Accuracy","C) Precision","D) Recall"],"correct":"A) MSE","explanation":"Mean Squared Error."},
{"question":"Goal of regression?","options":["A) Minimize error","B) Maximize error","C) Sort data","D) Cluster"],"correct":"A) Minimize error","explanation":"Best fit line."},
{"question":"Best fit line means?","options":["A) Minimum error line","B) Random line","C) Maximum error","D) None"],"correct":"A) Minimum error line","explanation":"Closest to data points."},
{"question":"Example use?","options":["A) House price prediction","B) Spam detection","C) Clustering","D) Sorting"],"correct":"A) House price prediction","explanation":"Predict continuous values."},
],

'tamil': [
{"question":"Linear Regression என்றால்?","options":["A) Continuous value predict","B) Classification","C) Clustering","D) Sort"],"correct":"A) Continuous value predict","explanation":"எண்ணிக்கை மதிப்பு கணிப்பு."},
{"question":"Learning type?","options":["A) Supervised","B) Unsupervised","C) Reinforcement","D) None"],"correct":"A) Supervised","explanation":"Label data."},
{"question":"Predict என்ன?","options":["A) Continuous","B) Category","C) Cluster","D) Label"],"correct":"A) Continuous","explanation":"Numeric output."},
{"question":"Equation?","options":["A) y=mx+c","B) x=y+c","C) y=x^2","D) y=logx"],"correct":"A) y=mx+c","explanation":"Linear equation."},
{"question":"m என்ன?","options":["A) Slope","B) Intercept","C) Error","D) Data"],"correct":"A) Slope","explanation":"மாற்ற வீதம்."},
{"question":"c என்ன?","options":["A) Intercept","B) Slope","C) Error","D) Data"],"correct":"A) Intercept","explanation":"x=0 போது மதிப்பு."},
{"question":"Cost function?","options":["A) MSE","B) Accuracy","C) Precision","D) Recall"],"correct":"A) MSE","explanation":"Mean Squared Error."},
{"question":"Goal?","options":["A) Error குறை","B) Error அதிகம்","C) Sort","D) Cluster"],"correct":"A) Error குறை","explanation":"Best fit line."},
{"question":"Best fit line?","options":["A) குறைந்த error","B) Random","C) அதிக error","D) None"],"correct":"A) குறைந்த error","explanation":"Dataக்கு அருகில் இருக்கும்."},
{"question":"Example?","options":["A) House price","B) Spam","C) Cluster","D) Sort"],"correct":"A) House price","explanation":"Continuous predict."},
],

'tanglish': [
{"question":"Linear Regression na?","options":["A) Continuous predict","B) Classification","C) Clustering","D) Sort"],"correct":"A) Continuous predict","explanation":"Numeric output predict pannum."},
{"question":"Learning type?","options":["A) Supervised","B) Unsupervised","C) Reinforcement","D) None"],"correct":"A) Supervised","explanation":"Label data use pannum."},
{"question":"Predict enna?","options":["A) Continuous","B) Category","C) Cluster","D) Label"],"correct":"A) Continuous","explanation":"Numeric values."},
{"question":"Equation?","options":["A) y=mx+c","B) x=y+c","C) y=x^2","D) y=logx"],"correct":"A) y=mx+c","explanation":"Linear formula."},
{"question":"m na?","options":["A) Slope","B) Intercept","C) Error","D) Data"],"correct":"A) Slope","explanation":"Change rate."},
{"question":"c na?","options":["A) Intercept","B) Slope","C) Error","D) Data"],"correct":"A) Intercept","explanation":"x=0 value."},
{"question":"Cost function?","options":["A) MSE","B) Accuracy","C) Precision","D) Recall"],"correct":"A) MSE","explanation":"Error measure."},
{"question":"Goal?","options":["A) Min error","B) Max error","C) Sort","D) Cluster"],"correct":"A) Min error","explanation":"Best fit line."},
{"question":"Best fit line?","options":["A) Min error","B) Random","C) Max error","D) None"],"correct":"A) Min error","explanation":"Closest line."},
{"question":"Example?","options":["A) House price","B) Spam","C) Cluster","D) Sort"],"correct":"A) House price","explanation":"Continuous prediction."},
],

'hindi': [
{"question":"Linear Regression क्या है?","options":["A) Continuous predict","B) Classification","C) Clustering","D) Sort"],"correct":"A) Continuous predict","explanation":"Numeric output predict करता है।"},
{"question":"Learning type?","options":["A) Supervised","B) Unsupervised","C) Reinforcement","D) None"],"correct":"A) Supervised","explanation":"Label data use होता है।"},
{"question":"Predict क्या?","options":["A) Continuous","B) Category","C) Cluster","D) Label"],"correct":"A) Continuous","explanation":"Numeric values।"},
{"question":"Equation?","options":["A) y=mx+c","B) x=y+c","C) y=x^2","D) y=logx"],"correct":"A) y=mx+c","explanation":"Linear equation।"},
{"question":"m क्या है?","options":["A) Slope","B) Intercept","C) Error","D) Data"],"correct":"A) Slope","explanation":"Change rate।"},
{"question":"c क्या है?","options":["A) Intercept","B) Slope","C) Error","D) Data"],"correct":"A) Intercept","explanation":"x=0 value।"},
{"question":"Cost function?","options":["A) MSE","B) Accuracy","C) Precision","D) Recall"],"correct":"A) MSE","explanation":"Error measure।"},
{"question":"Goal?","options":["A) Min error","B) Max error","C) Sort","D) Cluster"],"correct":"A) Min error","explanation":"Best fit line।"},
{"question":"Best fit line?","options":["A) Min error","B) Random","C) Max error","D) None"],"correct":"A) Min error","explanation":"Closest line।"},
{"question":"Example?","options":["A) House price","B) Spam","C) Cluster","D) Sort"],"correct":"A) House price","explanation":"Continuous prediction।"},
],

'malayalam': [
{"question":"Linear Regression എന്താണ്?","options":["A) Continuous predict","B) Classification","C) Clustering","D) Sort"],"correct":"A) Continuous predict","explanation":"Numeric values predict ചെയ്യുന്നു."},
{"question":"Learning type?","options":["A) Supervised","B) Unsupervised","C) Reinforcement","D) None"],"correct":"A) Supervised","explanation":"Label data ഉപയോഗിക്കുന്നു."},
{"question":"Predict എന്ത്?","options":["A) Continuous","B) Category","C) Cluster","D) Label"],"correct":"A) Continuous","explanation":"Numeric output."},
{"question":"Equation?","options":["A) y=mx+c","B) x=y+c","C) y=x^2","D) y=logx"],"correct":"A) y=mx+c","explanation":"Linear equation."},
{"question":"m എന്ത്?","options":["A) Slope","B) Intercept","C) Error","D) Data"],"correct":"A) Slope","explanation":"Change rate."},
{"question":"c എന്ത്?","options":["A) Intercept","B) Slope","C) Error","D) Data"],"correct":"A) Intercept","explanation":"x=0 value."},
{"question":"Cost function?","options":["A) MSE","B) Accuracy","C) Precision","D) Recall"],"correct":"A) MSE","explanation":"Error measure."},
{"question":"Goal?","options":["A) Min error","B) Max error","C) Sort","D) Cluster"],"correct":"A) Min error","explanation":"Best fit line."},
{"question":"Best fit line?","options":["A) Min error","B) Random","C) Max error","D) None"],"correct":"A) Min error","explanation":"Closest line."},
{"question":"Example?","options":["A) House price","B) Spam","C) Cluster","D) Sort"],"correct":"A) House price","explanation":"Continuous prediction."},
],
},
'Logistic Regression':{
   
'english': [
{"question":"What is Logistic Regression?","options":["A) Classification algorithm","B) Regression only","C) Clustering","D) Sorting"],"correct":"A) Classification algorithm","explanation":"Used for classification problems."},
{"question":"Type of learning?","options":["A) Supervised","B) Unsupervised","C) Reinforcement","D) None"],"correct":"A) Supervised","explanation":"Uses labeled data."},
{"question":"Logistic regression predicts?","options":["A) Probability","B) Continuous values","C) Clusters","D) Sorting"],"correct":"A) Probability","explanation":"Outputs probability between 0 and 1."},
{"question":"Output range?","options":["A) 0 to 1","B) -∞ to ∞","C) 0 to 100","D) -1 to 1"],"correct":"A) 0 to 1","explanation":"Sigmoid function output."},
{"question":"Function used?","options":["A) Sigmoid","B) Linear","C) Square","D) Log"],"correct":"A) Sigmoid","explanation":"Maps values to probability."},
{"question":"Sigmoid formula?","options":["A) 1/(1+e^-x)","B) x^2","C) y=mx+c","D) log(x)"],"correct":"A) 1/(1+e^-x)","explanation":"Converts input to probability."},
{"question":"Used for?","options":["A) Binary classification","B) Clustering","C) Sorting","D) Regression only"],"correct":"A) Binary classification","explanation":"Classifies into two classes."},
{"question":"Decision boundary means?","options":["A) Separation line","B) Data point","C) Error","D) Cluster"],"correct":"A) Separation line","explanation":"Divides classes."},
{"question":"Example use?","options":["A) Spam detection","B) Price prediction","C) Clustering","D) Sorting"],"correct":"A) Spam detection","explanation":"Classifies spam or not."},
{"question":"Cost function used?","options":["A) Log loss","B) MSE","C) Accuracy","D) Recall"],"correct":"A) Log loss","explanation":"Used in classification."},
],

'tamil': [
{"question":"Logistic Regression என்றால்?","options":["A) Classification","B) Regression மட்டும்","C) Clustering","D) Sort"],"correct":"A) Classification","explanation":"Classificationக்கு பயன்படுத்தப்படும்."},
{"question":"Learning type?","options":["A) Supervised","B) Unsupervised","C) Reinforcement","D) None"],"correct":"A) Supervised","explanation":"Label data."},
{"question":"Predict என்ன?","options":["A) Probability","B) Continuous","C) Cluster","D) Sort"],"correct":"A) Probability","explanation":"0 முதல் 1 வரை மதிப்பு."},
{"question":"Output range?","options":["A) 0-1","B) ∞","C) 0-100","D) -1-1"],"correct":"A) 0-1","explanation":"Sigmoid output."},
{"question":"Function?","options":["A) Sigmoid","B) Linear","C) Square","D) Log"],"correct":"A) Sigmoid","explanation":"Probability map."},
{"question":"Formula?","options":["A) 1/(1+e^-x)","B) x^2","C) y=mx+c","D) log"],"correct":"A) 1/(1+e^-x)","explanation":"Sigmoid formula."},
{"question":"Use?","options":["A) Binary class","B) Cluster","C) Sort","D) Regression"],"correct":"A) Binary class","explanation":"2 class."},
{"question":"Decision boundary?","options":["A) Divide line","B) Point","C) Error","D) Cluster"],"correct":"A) Divide line","explanation":"Classes பிரிக்கும்."},
{"question":"Example?","options":["A) Spam","B) Price","C) Cluster","D) Sort"],"correct":"A) Spam","explanation":"Spam detection."},
{"question":"Cost function?","options":["A) Log loss","B) MSE","C) Accuracy","D) Recall"],"correct":"A) Log loss","explanation":"Classification error."},
],

'tanglish': [
{"question":"Logistic Regression na?","options":["A) Classification","B) Regression only","C) Clustering","D) Sort"],"correct":"A) Classification","explanation":"Classification ku use pannum."},
{"question":"Learning type?","options":["A) Supervised","B) Unsupervised","C) Reinforcement","D) None"],"correct":"A) Supervised","explanation":"Label data."},
{"question":"Predict enna?","options":["A) Probability","B) Continuous","C) Cluster","D) Sort"],"correct":"A) Probability","explanation":"0-1 value."},
{"question":"Output range?","options":["A) 0-1","B) ∞","C) 0-100","D) -1-1"],"correct":"A) 0-1","explanation":"Sigmoid output."},
{"question":"Function?","options":["A) Sigmoid","B) Linear","C) Square","D) Log"],"correct":"A) Sigmoid","explanation":"Probability map."},
{"question":"Formula?","options":["A) 1/(1+e^-x)","B) x^2","C) y=mx+c","D) log"],"correct":"A) 1/(1+e^-x)","explanation":"Sigmoid formula."},
{"question":"Use?","options":["A) Binary","B) Cluster","C) Sort","D) Regression"],"correct":"A) Binary","explanation":"2 class."},
{"question":"Decision boundary?","options":["A) Divide line","B) Point","C) Error","D) Cluster"],"correct":"A) Divide line","explanation":"Classes split pannum."},
{"question":"Example?","options":["A) Spam","B) Price","C) Cluster","D) Sort"],"correct":"A) Spam","explanation":"Spam detect pannum."},
{"question":"Cost function?","options":["A) Log loss","B) MSE","C) Accuracy","D) Recall"],"correct":"A) Log loss","explanation":"Error measure."},
],

'hindi': [
{"question":"Logistic Regression क्या है?","options":["A) Classification","B) Regression only","C) Clustering","D) Sort"],"correct":"A) Classification","explanation":"Classification के लिए।"},
{"question":"Learning type?","options":["A) Supervised","B) Unsupervised","C) Reinforcement","D) None"],"correct":"A) Supervised","explanation":"Label data।"},
{"question":"Predict क्या?","options":["A) Probability","B) Continuous","C) Cluster","D) Sort"],"correct":"A) Probability","explanation":"0-1 value।"},
{"question":"Output range?","options":["A) 0-1","B) ∞","C) 0-100","D) -1-1"],"correct":"A) 0-1","explanation":"Sigmoid output।"},
{"question":"Function?","options":["A) Sigmoid","B) Linear","C) Square","D) Log"],"correct":"A) Sigmoid","explanation":"Probability map।"},
{"question":"Formula?","options":["A) 1/(1+e^-x)","B) x^2","C) y=mx+c","D) log"],"correct":"A) 1/(1+e^-x)","explanation":"Sigmoid formula।"},
{"question":"Use?","options":["A) Binary","B) Cluster","C) Sort","D) Regression"],"correct":"A) Binary","explanation":"2 class।"},
{"question":"Decision boundary?","options":["A) Divide line","B) Point","C) Error","D) Cluster"],"correct":"A) Divide line","explanation":"Classes divide करता है।"},
{"question":"Example?","options":["A) Spam","B) Price","C) Cluster","D) Sort"],"correct":"A) Spam","explanation":"Spam detection।"},
{"question":"Cost function?","options":["A) Log loss","B) MSE","C) Accuracy","D) Recall"],"correct":"A) Log loss","explanation":"Error measure।"},
],

'malayalam': [
{"question":"Logistic Regression എന്താണ്?","options":["A) Classification","B) Regression only","C) Clustering","D) Sort"],"correct":"A) Classification","explanation":"Classification വേണ്ടി."},
{"question":"Learning type?","options":["A) Supervised","B) Unsupervised","C) Reinforcement","D) None"],"correct":"A) Supervised","explanation":"Label data ഉപയോഗിക്കുന്നു."},
{"question":"Predict എന്ത്?","options":["A) Probability","B) Continuous","C) Cluster","D) Sort"],"correct":"A) Probability","explanation":"0-1 value."},
{"question":"Output range?","options":["A) 0-1","B) ∞","C) 0-100","D) -1-1"],"correct":"A) 0-1","explanation":"Sigmoid output."},
{"question":"Function?","options":["A) Sigmoid","B) Linear","C) Square","D) Log"],"correct":"A) Sigmoid","explanation":"Probability map."},
{"question":"Formula?","options":["A) 1/(1+e^-x)","B) x^2","C) y=mx+c","D) log"],"correct":"A) 1/(1+e^-x)","explanation":"Sigmoid formula."},
{"question":"Use?","options":["A) Binary","B) Cluster","C) Sort","D) Regression"],"correct":"A) Binary","explanation":"2 class."},
{"question":"Decision boundary?","options":["A) Divide line","B) Point","C) Error","D) Cluster"],"correct":"A) Divide line","explanation":"Classes split ചെയ്യുന്നു."},
{"question":"Example?","options":["A) Spam","B) Price","C) Cluster","D) Sort"],"correct":"A) Spam","explanation":"Spam detection."},
{"question":"Cost function?","options":["A) Log loss","B) MSE","C) Accuracy","D) Recall"],"correct":"A) Log loss","explanation":"Error measure."},
],
},
'Decision Trees':{
'english': [
{"question":"What is a Decision Tree?","options":["A) Tree-like model","B) Neural network","C) Database","D) Loop"],"correct":"A) Tree-like model","explanation":"Model with nodes and branches."},
{"question":"Used for?","options":["A) Classification & Regression","B) Clustering","C) Sorting","D) Searching"],"correct":"A) Classification & Regression","explanation":"Works for both tasks."},
{"question":"Root node is?","options":["A) Top node","B) Leaf","C) Middle node","D) End"],"correct":"A) Top node","explanation":"Starting point of tree."},
{"question":"Leaf node is?","options":["A) Final output","B) Start","C) Middle","D) Error"],"correct":"A) Final output","explanation":"Represents decision result."},
{"question":"Internal node represents?","options":["A) Decision","B) Output","C) Data","D) Error"],"correct":"A) Decision","explanation":"Splits data."},
{"question":"Splitting means?","options":["A) Divide data","B) Join data","C) Delete data","D) Sort data"],"correct":"A) Divide data","explanation":"Creates branches."},
{"question":"Criterion used?","options":["A) Gini/Entropy","B) MSE only","C) Accuracy","D) Recall"],"correct":"A) Gini/Entropy","explanation":"Measures impurity."},
{"question":"Overfitting means?","options":["A) Too complex model","B) Simple model","C) No learning","D) Random"],"correct":"A) Too complex model","explanation":"Fits training data too well."},
{"question":"Pruning is?","options":["A) Reduce tree size","B) Increase tree","C) Delete data","D) Train model"],"correct":"A) Reduce tree size","explanation":"Avoids overfitting."},
{"question":"Example use?","options":["A) Loan approval","B) Sorting","C) Printing","D) Searching"],"correct":"A) Loan approval","explanation":"Decision making problem."},
],

'tamil': [
{"question":"Decision Tree என்றால்?","options":["A) Tree model","B) Neural","C) DB","D) Loop"],"correct":"A) Tree model","explanation":"Node-branch structure."},
{"question":"Use?","options":["A) Classification & Regression","B) Cluster","C) Sort","D) Search"],"correct":"A) Classification & Regression","explanation":"இரண்டுக்கும் பயன்படும்."},
{"question":"Root node?","options":["A) Top","B) Leaf","C) Middle","D) End"],"correct":"A) Top","explanation":"தொடக்கம்."},
{"question":"Leaf node?","options":["A) Final output","B) Start","C) Middle","D) Error"],"correct":"A) Final output","explanation":"முடிவு."},
{"question":"Internal node?","options":["A) Decision","B) Output","C) Data","D) Error"],"correct":"A) Decision","explanation":"Split செய்கிறது."},
{"question":"Splitting?","options":["A) Divide","B) Join","C) Delete","D) Sort"],"correct":"A) Divide","explanation":"Data பிரிப்பு."},
{"question":"Criterion?","options":["A) Gini/Entropy","B) MSE","C) Accuracy","D) Recall"],"correct":"A) Gini/Entropy","explanation":"Impurity measure."},
{"question":"Overfitting?","options":["A) Complex model","B) Simple","C) None","D) Random"],"correct":"A) Complex model","explanation":"Trainingக்கு அதிகமாக பொருந்தும்."},
{"question":"Pruning?","options":["A) Tree reduce","B) Increase","C) Delete data","D) Train"],"correct":"A) Tree reduce","explanation":"Overfitting குறைக்கும்."},
{"question":"Example?","options":["A) Loan","B) Sort","C) Print","D) Search"],"correct":"A) Loan","explanation":"Decision problem."},
],

'tanglish': [
{"question":"Decision Tree na?","options":["A) Tree model","B) Neural","C) DB","D) Loop"],"correct":"A) Tree model","explanation":"Node branch structure."},
{"question":"Use?","options":["A) Classification & Regression","B) Cluster","C) Sort","D) Search"],"correct":"A) Classification & Regression","explanation":"Both use pannum."},
{"question":"Root node?","options":["A) Top","B) Leaf","C) Middle","D) End"],"correct":"A) Top","explanation":"Start point."},
{"question":"Leaf node?","options":["A) Final","B) Start","C) Middle","D) Error"],"correct":"A) Final","explanation":"Output."},
{"question":"Internal node?","options":["A) Decision","B) Output","C) Data","D) Error"],"correct":"A) Decision","explanation":"Split pannum."},
{"question":"Splitting?","options":["A) Divide","B) Join","C) Delete","D) Sort"],"correct":"A) Divide","explanation":"Data divide pannum."},
{"question":"Criterion?","options":["A) Gini/Entropy","B) MSE","C) Accuracy","D) Recall"],"correct":"A) Gini/Entropy","explanation":"Impurity measure."},
{"question":"Overfitting?","options":["A) Complex","B) Simple","C) None","D) Random"],"correct":"A) Complex","explanation":"Too much fit."},
{"question":"Pruning?","options":["A) Reduce","B) Increase","C) Delete","D) Train"],"correct":"A) Reduce","explanation":"Overfitting reduce pannum."},
{"question":"Example?","options":["A) Loan","B) Sort","C) Print","D) Search"],"correct":"A) Loan","explanation":"Decision making."},
],

'hindi': [
{"question":"Decision Tree क्या है?","options":["A) Tree model","B) Neural","C) DB","D) Loop"],"correct":"A) Tree model","explanation":"Node और branch structure।"},
{"question":"Use?","options":["A) Classification & Regression","B) Cluster","C) Sort","D) Search"],"correct":"A) Classification & Regression","explanation":"दोनों में उपयोग।"},
{"question":"Root node?","options":["A) Top","B) Leaf","C) Middle","D) End"],"correct":"A) Top","explanation":"Start point।"},
{"question":"Leaf node?","options":["A) Final","B) Start","C) Middle","D) Error"],"correct":"A) Final","explanation":"Final output।"},
{"question":"Internal node?","options":["A) Decision","B) Output","C) Data","D) Error"],"correct":"A) Decision","explanation":"Split करता है।"},
{"question":"Splitting?","options":["A) Divide","B) Join","C) Delete","D) Sort"],"correct":"A) Divide","explanation":"Data divide करता है।"},
{"question":"Criterion?","options":["A) Gini/Entropy","B) MSE","C) Accuracy","D) Recall"],"correct":"A) Gini/Entropy","explanation":"Impurity measure।"},
{"question":"Overfitting?","options":["A) Complex","B) Simple","C) None","D) Random"],"correct":"A) Complex","explanation":"Training data पर ज्यादा fit।"},
{"question":"Pruning?","options":["A) Reduce","B) Increase","C) Delete","D) Train"],"correct":"A) Reduce","explanation":"Overfitting कम करता है।"},
{"question":"Example?","options":["A) Loan","B) Sort","C) Print","D) Search"],"correct":"A) Loan","explanation":"Decision problem।"},
],

'malayalam': [
{"question":"Decision Tree എന്താണ്?","options":["A) Tree model","B) Neural","C) DB","D) Loop"],"correct":"A) Tree model","explanation":"Node-branch structure."},
{"question":"Use?","options":["A) Classification & Regression","B) Cluster","C) Sort","D) Search"],"correct":"A) Classification & Regression","explanation":"രണ്ടിലും ഉപയോഗിക്കുന്നു."},
{"question":"Root node?","options":["A) Top","B) Leaf","C) Middle","D) End"],"correct":"A) Top","explanation":"Start point."},
{"question":"Leaf node?","options":["A) Final","B) Start","C) Middle","D) Error"],"correct":"A) Final","explanation":"Final output."},
{"question":"Internal node?","options":["A) Decision","B) Output","C) Data","D) Error"],"correct":"A) Decision","explanation":"Split ചെയ്യുന്നു."},
{"question":"Splitting?","options":["A) Divide","B) Join","C) Delete","D) Sort"],"correct":"A) Divide","explanation":"Data divide ചെയ്യുന്നു."},
{"question":"Criterion?","options":["A) Gini/Entropy","B) MSE","C) Accuracy","D) Recall"],"correct":"A) Gini/Entropy","explanation":"Impurity measure."},
{"question":"Overfitting?","options":["A) Complex","B) Simple","C) None","D) Random"],"correct":"A) Complex","explanation":"Training data-ൽ കൂടുതലായി fit."},
{"question":"Pruning?","options":["A) Reduce","B) Increase","C) Delete","D) Train"],"correct":"A) Reduce","explanation":"Overfitting കുറയ്ക്കുന്നു."},
{"question":"Example?","options":["A) Loan","B) Sort","C) Print","D) Search"],"correct":"A) Loan","explanation":"Decision making problem."},
],
},
'Random Forest':{
   'english': [
{"question":"What is Random Forest?","options":["A) Ensemble of decision trees","B) Single tree","C) Neural network","D) Loop"],"correct":"A) Ensemble of decision trees","explanation":"It combines multiple decision trees."},
{"question":"Random Forest is used for?","options":["A) Classification & Regression","B) Clustering","C) Sorting","D) Searching"],"correct":"A) Classification & Regression","explanation":"Works for both tasks."},
{"question":"Main idea behind Random Forest?","options":["A) Multiple trees","B) Single tree","C) No tree","D) Loop"],"correct":"A) Multiple trees","explanation":"Uses many trees for better accuracy."},
{"question":"Bagging means?","options":["A) Bootstrap aggregating","B) Sorting","C) Looping","D) Splitting"],"correct":"A) Bootstrap aggregating","explanation":"Training on random subsets."},
{"question":"Each tree is trained on?","options":["A) Random data subset","B) Full data","C) No data","D) Sorted data"],"correct":"A) Random data subset","explanation":"Uses bootstrapping."},
{"question":"Feature selection in Random Forest?","options":["A) Random features","B) All features","C) No features","D) Fixed features"],"correct":"A) Random features","explanation":"Adds randomness to model."},
{"question":"Overfitting in Random Forest?","options":["A) Reduced","B) Increased","C) Same","D) None"],"correct":"A) Reduced","explanation":"Combining trees reduces overfitting."},
{"question":"Output of classification?","options":["A) Majority voting","B) Average","C) Sum","D) Random"],"correct":"A) Majority voting","explanation":"Most votes decide result."},
{"question":"Output of regression?","options":["A) Average value","B) Majority vote","C) Random","D) Sum"],"correct":"A) Average value","explanation":"Average of outputs."},
{"question":"Advantage of Random Forest?","options":["A) High accuracy","B) Slow","C) Complex only","D) Limited use"],"correct":"A) High accuracy","explanation":"More robust than single tree."},
],

'tamil': [
{"question":"Random Forest என்றால்?","options":["A) பல decision trees","B) Single tree","C) Neural","D) Loop"],"correct":"A) பல decision trees","explanation":"பல trees இணைந்து வேலை செய்கிறது."},
{"question":"Use?","options":["A) Classification & Regression","B) Cluster","C) Sort","D) Search"],"correct":"A) Classification & Regression","explanation":"இரண்டுக்கும் பயன்படும்."},
{"question":"Main idea?","options":["A) Multiple trees","B) Single","C) None","D) Loop"],"correct":"A) Multiple trees","explanation":"பல trees பயன்படுத்தும்."},
{"question":"Bagging?","options":["A) Bootstrap","B) Sort","C) Loop","D) Split"],"correct":"A) Bootstrap","explanation":"Random subset training."},
{"question":"Tree training?","options":["A) Random data","B) Full data","C) None","D) Sorted"],"correct":"A) Random data","explanation":"Subset data பயன்படுத்தும்."},
{"question":"Feature selection?","options":["A) Random","B) All","C) None","D) Fixed"],"correct":"A) Random","explanation":"Random features."},
{"question":"Overfitting?","options":["A) Reduce","B) Increase","C) Same","D) None"],"correct":"A) Reduce","explanation":"Overfitting குறையும்."},
{"question":"Classification output?","options":["A) Voting","B) Avg","C) Sum","D) Random"],"correct":"A) Voting","explanation":"Majority vote."},
{"question":"Regression output?","options":["A) Average","B) Vote","C) Random","D) Sum"],"correct":"A) Average","explanation":"Mean value."},
{"question":"Advantage?","options":["A) High accuracy","B) Slow","C) Complex","D) Limited"],"correct":"A) High accuracy","explanation":"Better performance."},
],

'tanglish': [
{"question":"Random Forest na?","options":["A) Many decision trees","B) Single tree","C) Neural","D) Loop"],"correct":"A) Many decision trees","explanation":"Multiple trees use pannum."},
{"question":"Use?","options":["A) Classification & Regression","B) Cluster","C) Sort","D) Search"],"correct":"A) Classification & Regression","explanation":"Both use pannum."},
{"question":"Main idea?","options":["A) Multiple trees","B) Single","C) None","D) Loop"],"correct":"A) Multiple trees","explanation":"Many trees use pannum."},
{"question":"Bagging?","options":["A) Bootstrap","B) Sort","C) Loop","D) Split"],"correct":"A) Bootstrap","explanation":"Random subset training."},
{"question":"Tree training?","options":["A) Random data","B) Full","C) None","D) Sorted"],"correct":"A) Random data","explanation":"Subset data."},
{"question":"Feature selection?","options":["A) Random","B) All","C) None","D) Fixed"],"correct":"A) Random","explanation":"Random features."},
{"question":"Overfitting?","options":["A) Reduce","B) Increase","C) Same","D) None"],"correct":"A) Reduce","explanation":"Overfitting reduce pannum."},
{"question":"Classification output?","options":["A) Voting","B) Avg","C) Sum","D) Random"],"correct":"A) Voting","explanation":"Majority vote."},
{"question":"Regression output?","options":["A) Average","B) Vote","C) Random","D) Sum"],"correct":"A) Average","explanation":"Mean value."},
{"question":"Advantage?","options":["A) High accuracy","B) Slow","C) Complex","D) Limited"],"correct":"A) High accuracy","explanation":"Better performance."},
],

'hindi': [
{"question":"Random Forest क्या है?","options":["A) कई decision trees","B) Single tree","C) Neural","D) Loop"],"correct":"A) कई decision trees","explanation":"Multiple trees का समूह।"},
{"question":"Use?","options":["A) Classification & Regression","B) Cluster","C) Sort","D) Search"],"correct":"A) Classification & Regression","explanation":"दोनों में उपयोग।"},
{"question":"Main idea?","options":["A) Multiple trees","B) Single","C) None","D) Loop"],"correct":"A) Multiple trees","explanation":"कई trees उपयोग होते हैं।"},
{"question":"Bagging?","options":["A) Bootstrap","B) Sort","C) Loop","D) Split"],"correct":"A) Bootstrap","explanation":"Random subset training।"},
{"question":"Tree training?","options":["A) Random data","B) Full","C) None","D) Sorted"],"correct":"A) Random data","explanation":"Subset data।"},
{"question":"Feature selection?","options":["A) Random","B) All","C) None","D) Fixed"],"correct":"A) Random","explanation":"Random features।"},
{"question":"Overfitting?","options":["A) Reduce","B) Increase","C) Same","D) None"],"correct":"A) Reduce","explanation":"Overfitting कम होता है।"},
{"question":"Classification output?","options":["A) Voting","B) Avg","C) Sum","D) Random"],"correct":"A) Voting","explanation":"Majority vote।"},
{"question":"Regression output?","options":["A) Average","B) Vote","C) Random","D) Sum"],"correct":"A) Average","explanation":"Mean value।"},
{"question":"Advantage?","options":["A) High accuracy","B) Slow","C) Complex","D) Limited"],"correct":"A) High accuracy","explanation":"Better performance।"},
],

'malayalam': [
{"question":"Random Forest എന്താണ്?","options":["A) നിരവധി decision trees","B) Single tree","C) Neural","D) Loop"],"correct":"A) നിരവധി decision trees","explanation":"Multiple trees ചേർന്ന മോഡൽ."},
{"question":"Use?","options":["A) Classification & Regression","B) Cluster","C) Sort","D) Search"],"correct":"A) Classification & Regression","explanation":"രണ്ടിലും ഉപയോഗിക്കുന്നു."},
{"question":"Main idea?","options":["A) Multiple trees","B) Single","C) None","D) Loop"],"correct":"A) Multiple trees","explanation":"നിരവധി trees ഉപയോഗിക്കുന്നു."},
{"question":"Bagging?","options":["A) Bootstrap","B) Sort","C) Loop","D) Split"],"correct":"A) Bootstrap","explanation":"Random subset training."},
{"question":"Tree training?","options":["A) Random data","B) Full","C) None","D) Sorted"],"correct":"A) Random data","explanation":"Subset data ഉപയോഗിക്കുന്നു."},
{"question":"Feature selection?","options":["A) Random","B) All","C) None","D) Fixed"],"correct":"A) Random","explanation":"Random features."},
{"question":"Overfitting?","options":["A) Reduce","B) Increase","C) Same","D) None"],"correct":"A) Reduce","explanation":"Overfitting കുറയുന്നു."},
{"question":"Classification output?","options":["A) Voting","B) Avg","C) Sum","D) Random"],"correct":"A) Voting","explanation":"Majority vote."},
{"question":"Regression output?","options":["A) Average","B) Vote","C) Random","D) Sum"],"correct":"A) Average","explanation":"Mean value."},
{"question":"Advantage?","options":["A) High accuracy","B) Slow","C) Complex","D) Limited"],"correct":"A) High accuracy","explanation":"Better performance."},
],
},
'Support Vector Machine':{
'english': [
{"question":"What is SVM?","options":["A) Supervised learning model","B) Unsupervised","C) Neural network","D) Database"],"correct":"A) Supervised learning model","explanation":"Used for classification and regression."},
{"question":"SVM is mainly used for?","options":["A) Classification","B) Clustering","C) Sorting","D) Searching"],"correct":"A) Classification","explanation":"Primarily for classification tasks."},
{"question":"What is a hyperplane?","options":["A) Decision boundary","B) Data point","C) Feature","D) Loop"],"correct":"A) Decision boundary","explanation":"Separates classes."},
{"question":"Support vectors are?","options":["A) Closest data points to hyperplane","B) Far points","C) Random points","D) Errors"],"correct":"A) Closest data points to hyperplane","explanation":"They define the boundary."},
{"question":"Goal of SVM?","options":["A) Maximize margin","B) Minimize data","C) Sort data","D) Loop"],"correct":"A) Maximize margin","explanation":"Wider margin = better model."},
{"question":"Kernel trick is?","options":["A) Transform data","B) Sort data","C) Delete data","D) Loop"],"correct":"A) Transform data","explanation":"Maps data to higher dimension."},
{"question":"Linear SVM used when?","options":["A) Data is linearly separable","B) Complex data","C) Random","D) None"],"correct":"A) Data is linearly separable","explanation":"Simple separation."},
{"question":"Non-linear SVM uses?","options":["A) Kernel","B) Loop","C) Sort","D) Array"],"correct":"A) Kernel","explanation":"Handles complex data."},
{"question":"Margin means?","options":["A) Distance between hyperplane and nearest points","B) Data size","C) Error","D) Loop"],"correct":"A) Distance between hyperplane and nearest points","explanation":"Maximize this."},
{"question":"Advantage of SVM?","options":["A) High accuracy","B) Slow always","C) Limited","D) None"],"correct":"A) High accuracy","explanation":"Works well in high dimensions."},
],

'tamil': [
{"question":"SVM என்றால்?","options":["A) Supervised model","B) Unsupervised","C) Neural","D) DB"],"correct":"A) Supervised model","explanation":"Classificationக்கு பயன்படுத்தப்படும்."},
{"question":"Use?","options":["A) Classification","B) Cluster","C) Sort","D) Search"],"correct":"A) Classification","explanation":"முக்கியமாக classification."},
{"question":"Hyperplane?","options":["A) Boundary","B) Data","C) Feature","D) Loop"],"correct":"A) Boundary","explanation":"Classes பிரிக்கும்."},
{"question":"Support vectors?","options":["A) Closest points","B) Far","C) Random","D) Error"],"correct":"A) Closest points","explanation":"Boundary define செய்கிறது."},
{"question":"Goal?","options":["A) Max margin","B) Min data","C) Sort","D) Loop"],"correct":"A) Max margin","explanation":"Margin அதிகப்படுத்தும்."},
{"question":"Kernel?","options":["A) Transform","B) Sort","C) Delete","D) Loop"],"correct":"A) Transform","explanation":"Higher dimension."},
{"question":"Linear SVM?","options":["A) Linearly separable","B) Complex","C) Random","D) None"],"correct":"A) Linearly separable","explanation":"Simple data."},
{"question":"Non-linear SVM?","options":["A) Kernel","B) Loop","C) Sort","D) Array"],"correct":"A) Kernel","explanation":"Complex data."},
{"question":"Margin?","options":["A) Distance","B) Size","C) Error","D) Loop"],"correct":"A) Distance","explanation":"Maximize செய்ய வேண்டும்."},
{"question":"Advantage?","options":["A) High accuracy","B) Slow","C) Limited","D) None"],"correct":"A) High accuracy","explanation":"Good performance."},
],

'tanglish': [
{"question":"SVM na?","options":["A) Supervised model","B) Unsupervised","C) Neural","D) DB"],"correct":"A) Supervised model","explanation":"Classification ku use pannum."},
{"question":"Use?","options":["A) Classification","B) Cluster","C) Sort","D) Search"],"correct":"A) Classification","explanation":"Main use classification."},
{"question":"Hyperplane?","options":["A) Boundary","B) Data","C) Feature","D) Loop"],"correct":"A) Boundary","explanation":"Class separate pannum."},
{"question":"Support vectors?","options":["A) Closest","B) Far","C) Random","D) Error"],"correct":"A) Closest","explanation":"Boundary define pannum."},
{"question":"Goal?","options":["A) Max margin","B) Min","C) Sort","D) Loop"],"correct":"A) Max margin","explanation":"Margin increase pannum."},
{"question":"Kernel?","options":["A) Transform","B) Sort","C) Delete","D) Loop"],"correct":"A) Transform","explanation":"Higher dimension."},
{"question":"Linear SVM?","options":["A) Linearly separable","B) Complex","C) Random","D) None"],"correct":"A) Linearly separable","explanation":"Simple data."},
{"question":"Non-linear?","options":["A) Kernel","B) Loop","C) Sort","D) Array"],"correct":"A) Kernel","explanation":"Complex data."},
{"question":"Margin?","options":["A) Distance","B) Size","C) Error","D) Loop"],"correct":"A) Distance","explanation":"Maximize pannum."},
{"question":"Advantage?","options":["A) High accuracy","B) Slow","C) Limited","D) None"],"correct":"A) High accuracy","explanation":"Better result."},
],

'hindi': [
{"question":"SVM क्या है?","options":["A) Supervised model","B) Unsupervised","C) Neural","D) DB"],"correct":"A) Supervised model","explanation":"Classification के लिए उपयोग।"},
{"question":"Use?","options":["A) Classification","B) Cluster","C) Sort","D) Search"],"correct":"A) Classification","explanation":"मुख्य उपयोग classification।"},
{"question":"Hyperplane?","options":["A) Boundary","B) Data","C) Feature","D) Loop"],"correct":"A) Boundary","explanation":"Classes अलग करता है।"},
{"question":"Support vectors?","options":["A) Closest","B) Far","C) Random","D) Error"],"correct":"A) Closest","explanation":"Boundary define करते हैं।"},
{"question":"Goal?","options":["A) Max margin","B) Min","C) Sort","D) Loop"],"correct":"A) Max margin","explanation":"Margin बढ़ाना।"},
{"question":"Kernel?","options":["A) Transform","B) Sort","C) Delete","D) Loop"],"correct":"A) Transform","explanation":"Higher dimension में map करता है।"},
{"question":"Linear SVM?","options":["A) Linearly separable","B) Complex","C) Random","D) None"],"correct":"A) Linearly separable","explanation":"Simple data।"},
{"question":"Non-linear?","options":["A) Kernel","B) Loop","C) Sort","D) Array"],"correct":"A) Kernel","explanation":"Complex data handle करता है।"},
{"question":"Margin?","options":["A) Distance","B) Size","C) Error","D) Loop"],"correct":"A) Distance","explanation":"Maximize करना होता है।"},
{"question":"Advantage?","options":["A) High accuracy","B) Slow","C) Limited","D) None"],"correct":"A) High accuracy","explanation":"Better performance।"},
],

'malayalam': [
{"question":"SVM എന്താണ്?","options":["A) Supervised model","B) Unsupervised","C) Neural","D) DB"],"correct":"A) Supervised model","explanation":"Classificationക്ക് ഉപയോഗിക്കുന്നു."},
{"question":"Use?","options":["A) Classification","B) Cluster","C) Sort","D) Search"],"correct":"A) Classification","explanation":"പ്രധാനമായും classification."},
{"question":"Hyperplane?","options":["A) Boundary","B) Data","C) Feature","D) Loop"],"correct":"A) Boundary","explanation":"Classes വേർതിരിക്കുന്നു."},
{"question":"Support vectors?","options":["A) Closest","B) Far","C) Random","D) Error"],"correct":"A) Closest","explanation":"Boundary നിർവചിക്കുന്നു."},
{"question":"Goal?","options":["A) Max margin","B) Min","C) Sort","D) Loop"],"correct":"A) Max margin","explanation":"Margin വർധിപ്പിക്കുന്നു."},
{"question":"Kernel?","options":["A) Transform","B) Sort","C) Delete","D) Loop"],"correct":"A) Transform","explanation":"Higher dimension."},
{"question":"Linear SVM?","options":["A) Linearly separable","B) Complex","C) Random","D) None"],"correct":"A) Linearly separable","explanation":"Simple data."},
{"question":"Non-linear?","options":["A) Kernel","B) Loop","C) Sort","D) Array"],"correct":"A) Kernel","explanation":"Complex data handle ചെയ്യുന്നു."},
{"question":"Margin?","options":["A) Distance","B) Size","C) Error","D) Loop"],"correct":"A) Distance","explanation":"Maximize ചെയ്യണം."},
{"question":"Advantage?","options":["A) High accuracy","B) Slow","C) Limited","D) None"],"correct":"A) High accuracy","explanation":"Better performance."},
],  
},
'K-Means Clustering':{
  'english': [
{"question":"What is K-Means?","options":["A) Clustering algorithm","B) Classification","C) Regression","D) Sorting"],"correct":"A) Clustering algorithm","explanation":"Used to group data into clusters."},
{"question":"K in K-Means represents?","options":["A) Number of clusters","B) Data size","C) Features","D) Loop"],"correct":"A) Number of clusters","explanation":"User defines number of clusters."},
{"question":"Type of learning?","options":["A) Unsupervised","B) Supervised","C) Reinforcement","D) Semi"],"correct":"A) Unsupervised","explanation":"No labeled data required."},
{"question":"Centroid means?","options":["A) Center of cluster","B) Data point","C) Boundary","D) Error"],"correct":"A) Center of cluster","explanation":"Average position of points."},
{"question":"First step in K-Means?","options":["A) Initialize centroids","B) Train model","C) Sort data","D) Delete data"],"correct":"A) Initialize centroids","explanation":"Randomly assign centroids."},
{"question":"Distance metric used?","options":["A) Euclidean","B) Binary","C) Text","D) Random"],"correct":"A) Euclidean","explanation":"Measures distance between points."},
{"question":"Cluster assignment?","options":["A) Nearest centroid","B) Random","C) Largest value","D) Loop"],"correct":"A) Nearest centroid","explanation":"Points assigned to closest centroid."},
{"question":"Centroid update?","options":["A) Mean of points","B) Random","C) Delete","D) Fixed"],"correct":"A) Mean of points","explanation":"Recalculate cluster center."},
{"question":"Stopping condition?","options":["A) No change in centroids","B) Infinite loop","C) Delete data","D) Sort"],"correct":"A) No change in centroids","explanation":"Algorithm converges."},
{"question":"Disadvantage?","options":["A) Need to choose K","B) Always accurate","C) No computation","D) Simple"],"correct":"A) Need to choose K","explanation":"Choosing K is difficult."},
],

'tamil': [
{"question":"K-Means என்றால்?","options":["A) Clustering algorithm","B) Classification","C) Regression","D) Sort"],"correct":"A) Clustering algorithm","explanation":"Data-வை குழுக்களாக பிரிக்கும்."},
{"question":"K என்றால்?","options":["A) Clusters எண்ணிக்கை","B) Data size","C) Feature","D) Loop"],"correct":"A) Clusters எண்ணிக்கை","explanation":"User define செய்யும்."},
{"question":"Learning type?","options":["A) Unsupervised","B) Supervised","C) Reinforcement","D) Semi"],"correct":"A) Unsupervised","explanation":"Label இல்லை."},
{"question":"Centroid?","options":["A) Center","B) Data","C) Boundary","D) Error"],"correct":"A) Center","explanation":"Cluster மையம்."},
{"question":"First step?","options":["A) Initialize centroid","B) Train","C) Sort","D) Delete"],"correct":"A) Initialize centroid","explanation":"Random ஆரம்பம்."},
{"question":"Distance?","options":["A) Euclidean","B) Binary","C) Text","D) Random"],"correct":"A) Euclidean","explanation":"Distance measure."},
{"question":"Assignment?","options":["A) Nearest centroid","B) Random","C) Largest","D) Loop"],"correct":"A) Nearest centroid","explanation":"அருகில் assign."},
{"question":"Update?","options":["A) Mean","B) Random","C) Delete","D) Fixed"],"correct":"A) Mean","explanation":"Mean update."},
{"question":"Stop?","options":["A) No change","B) Infinite","C) Delete","D) Sort"],"correct":"A) No change","explanation":"Converge ஆகும்."},
{"question":"Disadvantage?","options":["A) K தேர்வு","B) Always accurate","C) No compute","D) Simple"],"correct":"A) K தேர்வு","explanation":"K தேர்வு கடினம்."},
],

'tanglish': [
{"question":"K-Means na?","options":["A) Clustering","B) Classification","C) Regression","D) Sort"],"correct":"A) Clustering","explanation":"Data group pannum."},
{"question":"K na?","options":["A) Cluster count","B) Size","C) Feature","D) Loop"],"correct":"A) Cluster count","explanation":"User define pannum."},
{"question":"Type?","options":["A) Unsupervised","B) Supervised","C) Reinforcement","D) Semi"],"correct":"A) Unsupervised","explanation":"Label illa."},
{"question":"Centroid?","options":["A) Center","B) Data","C) Boundary","D) Error"],"correct":"A) Center","explanation":"Cluster center."},
{"question":"First step?","options":["A) Initialize","B) Train","C) Sort","D) Delete"],"correct":"A) Initialize","explanation":"Random start."},
{"question":"Distance?","options":["A) Euclidean","B) Binary","C) Text","D) Random"],"correct":"A) Euclidean","explanation":"Distance measure."},
{"question":"Assignment?","options":["A) Nearest","B) Random","C) Largest","D) Loop"],"correct":"A) Nearest","explanation":"Closest centroid."},
{"question":"Update?","options":["A) Mean","B) Random","C) Delete","D) Fixed"],"correct":"A) Mean","explanation":"Mean calculate pannum."},
{"question":"Stop?","options":["A) No change","B) Infinite","C) Delete","D) Sort"],"correct":"A) No change","explanation":"Converge."},
{"question":"Disadvantage?","options":["A) K choose","B) Always accurate","C) No compute","D) Simple"],"correct":"A) K choose","explanation":"K choose kastam."},
],

'hindi': [
{"question":"K-Means क्या है?","options":["A) Clustering","B) Classification","C) Regression","D) Sort"],"correct":"A) Clustering","explanation":"Data को समूह में बांटता है।"},
{"question":"K क्या है?","options":["A) Cluster संख्या","B) Size","C) Feature","D) Loop"],"correct":"A) Cluster संख्या","explanation":"User define करता है।"},
{"question":"Type?","options":["A) Unsupervised","B) Supervised","C) Reinforcement","D) Semi"],"correct":"A) Unsupervised","explanation":"Label नहीं होता।"},
{"question":"Centroid?","options":["A) Center","B) Data","C) Boundary","D) Error"],"correct":"A) Center","explanation":"Cluster का center।"},
{"question":"First step?","options":["A) Initialize","B) Train","C) Sort","D) Delete"],"correct":"A) Initialize","explanation":"Random शुरू।"},
{"question":"Distance?","options":["A) Euclidean","B) Binary","C) Text","D) Random"],"correct":"A) Euclidean","explanation":"Distance measure।"},
{"question":"Assignment?","options":["A) Nearest","B) Random","C) Largest","D) Loop"],"correct":"A) Nearest","explanation":"Closest centroid।"},
{"question":"Update?","options":["A) Mean","B) Random","C) Delete","D) Fixed"],"correct":"A) Mean","explanation":"Mean calculate।"},
{"question":"Stop?","options":["A) No change","B) Infinite","C) Delete","D) Sort"],"correct":"A) No change","explanation":"Converge।"},
{"question":"Disadvantage?","options":["A) K choose","B) Always accurate","C) No compute","D) Simple"],"correct":"A) K choose","explanation":"K चुनना कठिन।"},
],

'malayalam': [
{"question":"K-Means എന്താണ്?","options":["A) Clustering","B) Classification","C) Regression","D) Sort"],"correct":"A) Clustering","explanation":"Data ഗ്രൂപ്പുകളായി വേർതിരിക്കുന്നു."},
{"question":"K എന്താണ്?","options":["A) Cluster എണ്ണം","B) Size","C) Feature","D) Loop"],"correct":"A) Cluster എണ്ണം","explanation":"User define ചെയ്യുന്നു."},
{"question":"Type?","options":["A) Unsupervised","B) Supervised","C) Reinforcement","D) Semi"],"correct":"A) Unsupervised","explanation":"Label ഇല്ല."},
{"question":"Centroid?","options":["A) Center","B) Data","C) Boundary","D) Error"],"correct":"A) Center","explanation":"Cluster center."},
{"question":"First step?","options":["A) Initialize","B) Train","C) Sort","D) Delete"],"correct":"A) Initialize","explanation":"Random start."},
{"question":"Distance?","options":["A) Euclidean","B) Binary","C) Text","D) Random"],"correct":"A) Euclidean","explanation":"Distance measure."},
{"question":"Assignment?","options":["A) Nearest","B) Random","C) Largest","D) Loop"],"correct":"A) Nearest","explanation":"Closest centroid."},
{"question":"Update?","options":["A) Mean","B) Random","C) Delete","D) Fixed"],"correct":"A) Mean","explanation":"Mean calculate ചെയ്യുന്നു."},
{"question":"Stop?","options":["A) No change","B) Infinite","C) Delete","D) Sort"],"correct":"A) No change","explanation":"Converge ചെയ്യുന്നു."},
{"question":"Disadvantage?","options":["A) K choose","B) Always accurate","C) No compute","D) Simple"],"correct":"A) K choose","explanation":"K തിരഞ്ഞെടുക്കൽ ബുദ്ധിമുട്ടാണ്."},
],
},#kmeans ends
'Neural Networks':{
   'english': [
{"question":"What is a Neural Network?","options":["A) Model inspired by human brain","B) Database","C) Loop","D) Sorting"],"correct":"A) Model inspired by human brain","explanation":"Mimics structure of neurons."},
{"question":"Basic unit of neural network?","options":["A) Neuron","B) Loop","C) Variable","D) Array"],"correct":"A) Neuron","explanation":"Smallest processing unit."},
{"question":"Layers in neural network?","options":["A) Input, Hidden, Output","B) Start, End","C) Top, Bottom","D) First, Last"],"correct":"A) Input, Hidden, Output","explanation":"Three main layers."},
{"question":"Activation function is?","options":["A) Decides output","B) Stores data","C) Loop","D) Sorting"],"correct":"A) Decides output","explanation":"Applies transformation."},
{"question":"Example of activation function?","options":["A) ReLU","B) Loop","C) Sort","D) Array"],"correct":"A) ReLU","explanation":"Common activation function."},
{"question":"Weights represent?","options":["A) Importance of input","B) Data size","C) Loop","D) Error"],"correct":"A) Importance of input","explanation":"Controls signal strength."},
{"question":"Bias is?","options":["A) Additional parameter","B) Loop","C) Array","D) Sort"],"correct":"A) Additional parameter","explanation":"Shifts output."},
{"question":"Forward propagation?","options":["A) Input to output flow","B) Output to input","C) Loop","D) Sort"],"correct":"A) Input to output flow","explanation":"Data moves forward."},
{"question":"Backpropagation?","options":["A) Error correction","B) Data storage","C) Loop","D) Sort"],"correct":"A) Error correction","explanation":"Updates weights."},
{"question":"Use of neural networks?","options":["A) Image & speech recognition","B) Sorting","C) Printing","D) Searching"],"correct":"A) Image & speech recognition","explanation":"Used in AI applications."},
],

'tamil': [
{"question":"Neural Network என்றால்?","options":["A) Brain model","B) DB","C) Loop","D) Sort"],"correct":"A) Brain model","explanation":"மனித மூளை போன்றது."},
{"question":"Basic unit?","options":["A) Neuron","B) Loop","C) Variable","D) Array"],"correct":"A) Neuron","explanation":"அடிப்படை அலகு."},
{"question":"Layers?","options":["A) Input, Hidden, Output","B) Start, End","C) Top, Bottom","D) First, Last"],"correct":"A) Input, Hidden, Output","explanation":"மூன்று பகுதிகள்."},
{"question":"Activation?","options":["A) Output decide","B) Store","C) Loop","D) Sort"],"correct":"A) Output decide","explanation":"Output தீர்மானிக்கும்."},
{"question":"Example?","options":["A) ReLU","B) Loop","C) Sort","D) Array"],"correct":"A) ReLU","explanation":"Common function."},
{"question":"Weights?","options":["A) Importance","B) Size","C) Loop","D) Error"],"correct":"A) Importance","explanation":"Input weight."},
{"question":"Bias?","options":["A) Extra param","B) Loop","C) Array","D) Sort"],"correct":"A) Extra param","explanation":"Output shift."},
{"question":"Forward?","options":["A) Input→Output","B) Output→Input","C) Loop","D) Sort"],"correct":"A) Input→Output","explanation":"Forward flow."},
{"question":"Backprop?","options":["A) Error fix","B) Store","C) Loop","D) Sort"],"correct":"A) Error fix","explanation":"Weights update."},
{"question":"Use?","options":["A) Image & speech","B) Sort","C) Print","D) Search"],"correct":"A) Image & speech","explanation":"AI பயன்பாடு."},
],

'tanglish': [
{"question":"Neural Network na?","options":["A) Brain model","B) DB","C) Loop","D) Sort"],"correct":"A) Brain model","explanation":"Human brain madhiri."},
{"question":"Basic unit?","options":["A) Neuron","B) Loop","C) Variable","D) Array"],"correct":"A) Neuron","explanation":"Small unit."},
{"question":"Layers?","options":["A) Input, Hidden, Output","B) Start, End","C) Top, Bottom","D) First, Last"],"correct":"A) Input, Hidden, Output","explanation":"3 layers."},
{"question":"Activation?","options":["A) Output decide","B) Store","C) Loop","D) Sort"],"correct":"A) Output decide","explanation":"Output decide pannum."},
{"question":"Example?","options":["A) ReLU","B) Loop","C) Sort","D) Array"],"correct":"A) ReLU","explanation":"Common function."},
{"question":"Weights?","options":["A) Importance","B) Size","C) Loop","D) Error"],"correct":"A) Importance","explanation":"Input importance."},
{"question":"Bias?","options":["A) Extra","B) Loop","C) Array","D) Sort"],"correct":"A) Extra","explanation":"Output shift."},
{"question":"Forward?","options":["A) Input→Output","B) Output→Input","C) Loop","D) Sort"],"correct":"A) Input→Output","explanation":"Forward flow."},
{"question":"Backprop?","options":["A) Error fix","B) Store","C) Loop","D) Sort"],"correct":"A) Error fix","explanation":"Weights update."},
{"question":"Use?","options":["A) Image & speech","B) Sort","C) Print","D) Search"],"correct":"A) Image & speech","explanation":"AI use."},
],

'hindi': [
{"question":"Neural Network क्या है?","options":["A) Brain model","B) DB","C) Loop","D) Sort"],"correct":"A) Brain model","explanation":"मानव मस्तिष्क से प्रेरित।"},
{"question":"Basic unit?","options":["A) Neuron","B) Loop","C) Variable","D) Array"],"correct":"A) Neuron","explanation":"सबसे छोटी इकाई।"},
{"question":"Layers?","options":["A) Input, Hidden, Output","B) Start, End","C) Top, Bottom","D) First, Last"],"correct":"A) Input, Hidden, Output","explanation":"तीन मुख्य layers।"},
{"question":"Activation?","options":["A) Output decide","B) Store","C) Loop","D) Sort"],"correct":"A) Output decide","explanation":"Output तय करता है।"},
{"question":"Example?","options":["A) ReLU","B) Loop","C) Sort","D) Array"],"correct":"A) ReLU","explanation":"Common function।"},
{"question":"Weights?","options":["A) Importance","B) Size","C) Loop","D) Error"],"correct":"A) Importance","explanation":"Input का महत्व।"},
{"question":"Bias?","options":["A) Extra","B) Loop","C) Array","D) Sort"],"correct":"A) Extra","explanation":"Output shift करता है।"},
{"question":"Forward?","options":["A) Input→Output","B) Output→Input","C) Loop","D) Sort"],"correct":"A) Input→Output","explanation":"Forward flow।"},
{"question":"Backprop?","options":["A) Error fix","B) Store","C) Loop","D) Sort"],"correct":"A) Error fix","explanation":"Weights update करता है।"},
{"question":"Use?","options":["A) Image & speech","B) Sort","C) Print","D) Search"],"correct":"A) Image & speech","explanation":"AI applications।"},
],

'malayalam': [
{"question":"Neural Network എന്താണ്?","options":["A) Brain model","B) DB","C) Loop","D) Sort"],"correct":"A) Brain model","explanation":"മനുഷ്യ മസ്തിഷ്കത്തിൽ നിന്നുള്ള പ്രചോദനം."},
{"question":"Basic unit?","options":["A) Neuron","B) Loop","C) Variable","D) Array"],"correct":"A) Neuron","explanation":"അടിസ്ഥാന ഘടകം."},
{"question":"Layers?","options":["A) Input, Hidden, Output","B) Start, End","C) Top, Bottom","D) First, Last"],"correct":"A) Input, Hidden, Output","explanation":"മൂന്ന് പ്രധാന ഘടകങ്ങൾ."},
{"question":"Activation?","options":["A) Output decide","B) Store","C) Loop","D) Sort"],"correct":"A) Output decide","explanation":"Output തീരുമാനിക്കുന്നു."},
{"question":"Example?","options":["A) ReLU","B) Loop","C) Sort","D) Array"],"correct":"A) ReLU","explanation":"Common function."},
{"question":"Weights?","options":["A) Importance","B) Size","C) Loop","D) Error"],"correct":"A) Importance","explanation":"Input importance."},
{"question":"Bias?","options":["A) Extra","B) Loop","C) Array","D) Sort"],"correct":"A) Extra","explanation":"Output shift."},
{"question":"Forward?","options":["A) Input→Output","B) Output→Input","C) Loop","D) Sort"],"correct":"A) Input→Output","explanation":"Forward flow."},
{"question":"Backprop?","options":["A) Error fix","B) Store","C) Loop","D) Sort"],"correct":"A) Error fix","explanation":"Weights update ചെയ്യുന്നു."},
{"question":"Use?","options":["A) Image & speech","B) Sort","C) Print","D) Search"],"correct":"A) Image & speech","explanation":"AI applications."},
],
},#neural ends
'Modal Evalution':{
   'english': [
{"question":"What is Model Evaluation?","options":["A) Measuring model performance","B) Training model","C) Cleaning data","D) Sorting"],"correct":"A) Measuring model performance","explanation":"Used to check how well model works."},
{"question":"Accuracy means?","options":["A) Correct predictions/total","B) Wrong predictions","C) Data size","D) Loop"],"correct":"A) Correct predictions/total","explanation":"Measures overall correctness."},
{"question":"Precision means?","options":["A) Correct positive/total predicted positive","B) Total data","C) Error rate","D) Loop"],"correct":"A) Correct positive/total predicted positive","explanation":"Focus on predicted positives."},
{"question":"Recall means?","options":["A) Correct positive/actual positive","B) Total data","C) Error rate","D) Loop"],"correct":"A) Correct positive/actual positive","explanation":"Measures detection ability."},
{"question":"F1-score is?","options":["A) Harmonic mean of precision & recall","B) Sum","C) Difference","D) Loop"],"correct":"A) Harmonic mean of precision & recall","explanation":"Balances precision and recall."},
{"question":"Confusion matrix shows?","options":["A) Prediction results","B) Data size","C) Loop","D) Sorting"],"correct":"A) Prediction results","explanation":"TP, TN, FP, FN values."},
{"question":"Overfitting means?","options":["A) High train, low test accuracy","B) Low train accuracy","C) Perfect model","D) Random"],"correct":"A) High train, low test accuracy","explanation":"Model memorizes training data."},
{"question":"Underfitting means?","options":["A) Poor performance on all data","B) High accuracy","C) Perfect model","D) Random"],"correct":"A) Poor performance on all data","explanation":"Model too simple."},
{"question":"Cross-validation is?","options":["A) Splitting data multiple times","B) Sorting","C) Loop","D) Delete"],"correct":"A) Splitting data multiple times","explanation":"Improves reliability."},
{"question":"ROC curve used for?","options":["A) Classification evaluation","B) Regression","C) Sorting","D) Loop"],"correct":"A) Classification evaluation","explanation":"Shows trade-off between TPR & FPR."},
],

'tamil': [
{"question":"Model Evaluation என்றால்?","options":["A) Performance measure","B) Train","C) Clean","D) Sort"],"correct":"A) Performance measure","explanation":"Model எப்படி வேலை செய்கிறது என்பதை பார்க்கும்."},
{"question":"Accuracy?","options":["A) Correct/total","B) Wrong","C) Size","D) Loop"],"correct":"A) Correct/total","explanation":"மொத்த சரியானது."},
{"question":"Precision?","options":["A) Correct positive/predicted positive","B) Total","C) Error","D) Loop"],"correct":"A) Correct positive/predicted positive","explanation":"Positive accuracy."},
{"question":"Recall?","options":["A) Correct positive/actual positive","B) Total","C) Error","D) Loop"],"correct":"A) Correct positive/actual positive","explanation":"Detection ability."},
{"question":"F1-score?","options":["A) Harmonic mean","B) Sum","C) Diff","D) Loop"],"correct":"A) Harmonic mean","explanation":"Precision + Recall balance."},
{"question":"Confusion matrix?","options":["A) Result table","B) Size","C) Loop","D) Sort"],"correct":"A) Result table","explanation":"TP TN FP FN."},
{"question":"Overfitting?","options":["A) High train low test","B) Low train","C) Perfect","D) Random"],"correct":"A) High train low test","explanation":"Train data மட்டும் fit."},
{"question":"Underfitting?","options":["A) Poor all","B) High","C) Perfect","D) Random"],"correct":"A) Poor all","explanation":"Model simple."},
{"question":"Cross-validation?","options":["A) Multiple split","B) Sort","C) Loop","D) Delete"],"correct":"A) Multiple split","explanation":"Reliable result."},
{"question":"ROC?","options":["A) Classification eval","B) Regression","C) Sort","D) Loop"],"correct":"A) Classification eval","explanation":"TPR vs FPR."},
],

'tanglish': [
{"question":"Model Evaluation na?","options":["A) Performance check","B) Train","C) Clean","D) Sort"],"correct":"A) Performance check","explanation":"Model eppadi work nu check."},
{"question":"Accuracy?","options":["A) Correct/total","B) Wrong","C) Size","D) Loop"],"correct":"A) Correct/total","explanation":"Overall correct."},
{"question":"Precision?","options":["A) Correct positive/predicted","B) Total","C) Error","D) Loop"],"correct":"A) Correct positive/predicted","explanation":"Positive accuracy."},
{"question":"Recall?","options":["A) Correct positive/actual","B) Total","C) Error","D) Loop"],"correct":"A) Correct positive/actual","explanation":"Detection power."},
{"question":"F1?","options":["A) Harmonic mean","B) Sum","C) Diff","D) Loop"],"correct":"A) Harmonic mean","explanation":"Balance."},
{"question":"Confusion matrix?","options":["A) Result","B) Size","C) Loop","D) Sort"],"correct":"A) Result","explanation":"TP TN FP FN."},
{"question":"Overfitting?","options":["A) High train low test","B) Low train","C) Perfect","D) Random"],"correct":"A) High train low test","explanation":"Over learn."},
{"question":"Underfitting?","options":["A) Poor","B) High","C) Perfect","D) Random"],"correct":"A) Poor","explanation":"Too simple."},
{"question":"Cross-validation?","options":["A) Multiple split","B) Sort","C) Loop","D) Delete"],"correct":"A) Multiple split","explanation":"Better eval."},
{"question":"ROC?","options":["A) Classification eval","B) Regression","C) Sort","D) Loop"],"correct":"A) Classification eval","explanation":"TPR vs FPR."},
],

'hindi': [
{"question":"Model Evaluation क्या है?","options":["A) Performance check","B) Train","C) Clean","D) Sort"],"correct":"A) Performance check","explanation":"Model की performance मापना।"},
{"question":"Accuracy?","options":["A) Correct/total","B) Wrong","C) Size","D) Loop"],"correct":"A) Correct/total","explanation":"कुल सही prediction।"},
{"question":"Precision?","options":["A) Correct positive/predicted","B) Total","C) Error","D) Loop"],"correct":"A) Correct positive/predicted","explanation":"Positive accuracy।"},
{"question":"Recall?","options":["A) Correct positive/actual","B) Total","C) Error","D) Loop"],"correct":"A) Correct positive/actual","explanation":"Detection ability।"},
{"question":"F1?","options":["A) Harmonic mean","B) Sum","C) Diff","D) Loop"],"correct":"A) Harmonic mean","explanation":"Balance measure।"},
{"question":"Confusion matrix?","options":["A) Result","B) Size","C) Loop","D) Sort"],"correct":"A) Result","explanation":"TP TN FP FN।"},
{"question":"Overfitting?","options":["A) High train low test","B) Low train","C) Perfect","D) Random"],"correct":"A) High train low test","explanation":"Train data पर ज्यादा fit।"},
{"question":"Underfitting?","options":["A) Poor","B) High","C) Perfect","D) Random"],"correct":"A) Poor","explanation":"Model बहुत simple।"},
{"question":"Cross-validation?","options":["A) Multiple split","B) Sort","C) Loop","D) Delete"],"correct":"A) Multiple split","explanation":"Better evaluation।"},
{"question":"ROC?","options":["A) Classification eval","B) Regression","C) Sort","D) Loop"],"correct":"A) Classification eval","explanation":"TPR vs FPR।"},
],

'malayalam': [
{"question":"Model Evaluation എന്താണ്?","options":["A) Performance check","B) Train","C) Clean","D) Sort"],"correct":"A) Performance check","explanation":"Model performance അളക്കുന്നത്."},
{"question":"Accuracy?","options":["A) Correct/total","B) Wrong","C) Size","D) Loop"],"correct":"A) Correct/total","explanation":"മൊത്തം ശരിയായത്."},
{"question":"Precision?","options":["A) Correct positive/predicted","B) Total","C) Error","D) Loop"],"correct":"A) Correct positive/predicted","explanation":"Positive accuracy."},
{"question":"Recall?","options":["A) Correct positive/actual","B) Total","C) Error","D) Loop"],"correct":"A) Correct positive/actual","explanation":"Detection ability."},
{"question":"F1?","options":["A) Harmonic mean","B) Sum","C) Diff","D) Loop"],"correct":"A) Harmonic mean","explanation":"Balance measure."},
{"question":"Confusion matrix?","options":["A) Result","B) Size","C) Loop","D) Sort"],"correct":"A) Result","explanation":"TP TN FP FN."},
{"question":"Overfitting?","options":["A) High train low test","B) Low train","C) Perfect","D) Random"],"correct":"A) High train low test","explanation":"Train data മാത്രം fit."},
{"question":"Underfitting?","options":["A) Poor","B) High","C) Perfect","D) Random"],"correct":"A) Poor","explanation":"Model simple."},
{"question":"Cross-validation?","options":["A) Multiple split","B) Sort","C) Loop","D) Delete"],"correct":"A) Multiple split","explanation":"Reliable result."},
{"question":"ROC?","options":["A) Classification eval","B) Regression","C) Sort","D) Loop"],"correct":"A) Classification eval","explanation":"TPR vs FPR."},
],
},
'ML Projects Lifecycle':{
'english': [
{"question":"What is ML project life cycle?","options":["A) Steps to build ML model","B) Only coding","C) Only testing","D) Only deployment"],"correct":"A) Steps to build ML model","explanation":"It includes all stages from data to deployment."},
{"question":"First step in ML life cycle?","options":["A) Problem definition","B) Model training","C) Deployment","D) Testing"],"correct":"A) Problem definition","explanation":"Understanding problem is first step."},
{"question":"Data collection means?","options":["A) Gathering data","B) Deleting data","C) Training model","D) Testing"],"correct":"A) Gathering data","explanation":"Collecting relevant data."},
{"question":"Data preprocessing includes?","options":["A) Cleaning & transforming data","B) Training model","C) Deployment","D) Looping"],"correct":"A) Cleaning & transforming data","explanation":"Prepare data for model."},
{"question":"Feature engineering means?","options":["A) Selecting useful features","B) Deleting model","C) Coding only","D) Looping"],"correct":"A) Selecting useful features","explanation":"Improves model performance."},
{"question":"Model training means?","options":["A) Learning from data","B) Deleting data","C) Sorting","D) Looping"],"correct":"A) Learning from data","explanation":"Model learns patterns."},
{"question":"Model evaluation means?","options":["A) Checking performance","B) Training again","C) Deleting","D) Looping"],"correct":"A) Checking performance","explanation":"Evaluate using metrics."},
{"question":"Model deployment means?","options":["A) Using model in real world","B) Training model","C) Deleting data","D) Looping"],"correct":"A) Using model in real world","explanation":"Make model available for users."},
{"question":"Monitoring means?","options":["A) Tracking model performance","B) Deleting model","C) Coding","D) Looping"],"correct":"A) Tracking model performance","explanation":"Check performance after deployment."},
{"question":"Which step improves data quality?","options":["A) Preprocessing","B) Deployment","C) Testing","D) Loop"],"correct":"A) Preprocessing","explanation":"Cleaning improves quality."}
],

'tamil': [
{"question":"ML life cycle என்ன?","options":["A) Model steps","B) Coding மட்டும்","C) Testing மட்டும்","D) Deployment மட்டும்"],"correct":"A) Model steps","explanation":"Data முதல் deployment வரை."},
{"question":"முதல் படி?","options":["A) Problem define","B) Train","C) Deploy","D) Test"],"correct":"A) Problem define","explanation":"Problem புரிந்துகொள்ளுதல் முக்கியம்."},
{"question":"Data collection?","options":["A) Data சேகரிப்பு","B) Delete","C) Train","D) Test"],"correct":"A) Data சேகரிப்பு","explanation":"தேவையான data சேகரிக்க வேண்டும்."},
{"question":"Preprocessing?","options":["A) Clean & transform","B) Train","C) Deploy","D) Loop"],"correct":"A) Clean & transform","explanation":"Data ready ஆக்கும்."},
{"question":"Feature engineering?","options":["A) Useful features","B) Delete","C) Coding","D) Loop"],"correct":"A) Useful features","explanation":"Performance improve."},
{"question":"Training?","options":["A) Learn","B) Delete","C) Sort","D) Loop"],"correct":"A) Learn","explanation":"Model pattern கற்கும்."},
{"question":"Evaluation?","options":["A) Performance check","B) Train","C) Delete","D) Loop"],"correct":"A) Performance check","explanation":"Metrics use."},
{"question":"Deployment?","options":["A) Real use","B) Train","C) Delete","D) Loop"],"correct":"A) Real use","explanation":"User use."},
{"question":"Monitoring?","options":["A) Track","B) Delete","C) Code","D) Loop"],"correct":"A) Track","explanation":"Performance check."},
{"question":"Quality improve step?","options":["A) Preprocessing","B) Deploy","C) Test","D) Loop"],"correct":"A) Preprocessing","explanation":"Clean data."}
],

'tanglish': [
{"question":"ML life cycle na?","options":["A) Steps build model","B) Coding","C) Testing","D) Deploy"],"correct":"A) Steps build model","explanation":"Full process."},
{"question":"First step?","options":["A) Problem define","B) Train","C) Deploy","D) Test"],"correct":"A) Problem define","explanation":"Important."},
{"question":"Data collection?","options":["A) Gather data","B) Delete","C) Train","D) Test"],"correct":"A) Gather data","explanation":"Collect data."},
{"question":"Preprocessing?","options":["A) Clean transform","B) Train","C) Deploy","D) Loop"],"correct":"A) Clean transform","explanation":"Prepare data."},
{"question":"Feature engineering?","options":["A) Useful features","B) Delete","C) Code","D) Loop"],"correct":"A) Useful features","explanation":"Improve performance."},
{"question":"Training?","options":["A) Learn","B) Delete","C) Sort","D) Loop"],"correct":"A) Learn","explanation":"Pattern learn."},
{"question":"Evaluation?","options":["A) Check","B) Train","C) Delete","D) Loop"],"correct":"A) Check","explanation":"Metrics use."},
{"question":"Deployment?","options":["A) Real use","B) Train","C) Delete","D) Loop"],"correct":"A) Real use","explanation":"Use in real."},
{"question":"Monitoring?","options":["A) Track","B) Delete","C) Code","D) Loop"],"correct":"A) Track","explanation":"Check performance."},
{"question":"Quality improve?","options":["A) Preprocessing","B) Deploy","C) Test","D) Loop"],"correct":"A) Preprocessing","explanation":"Clean data."}
],

'hindi': [
{"question":"ML life cycle क्या है?","options":["A) Model बनाने के steps","B) Coding","C) Testing","D) Deployment"],"correct":"A) Model बनाने के steps","explanation":"Data से deployment तक process."},
{"question":"पहला step?","options":["A) Problem define","B) Train","C) Deploy","D) Test"],"correct":"A) Problem define","explanation":"Problem समझना जरूरी।"},
{"question":"Data collection?","options":["A) Data इकट्ठा करना","B) Delete","C) Train","D) Test"],"correct":"A) Data इकट्ठा करना","explanation":"Relevant data लेना।"},
{"question":"Preprocessing?","options":["A) Clean transform","B) Train","C) Deploy","D) Loop"],"correct":"A) Clean transform","explanation":"Data prepare करना।"},
{"question":"Feature engineering?","options":["A) Useful features","B) Delete","C) Coding","D) Loop"],"correct":"A) Useful features","explanation":"Performance बढ़ाता है।"},
{"question":"Training?","options":["A) Learn","B) Delete","C) Sort","D) Loop"],"correct":"A) Learn","explanation":"Model सीखता है।"},
{"question":"Evaluation?","options":["A) Check","B) Train","C) Delete","D) Loop"],"correct":"A) Check","explanation":"Performance check।"},
{"question":"Deployment?","options":["A) Real use","B) Train","C) Delete","D) Loop"],"correct":"A) Real use","explanation":"Real world use।"},
{"question":"Monitoring?","options":["A) Track","B) Delete","C) Code","D) Loop"],"correct":"A) Track","explanation":"Performance track।"},
{"question":"Quality improve?","options":["A) Preprocessing","B) Deploy","C) Test","D) Loop"],"correct":"A) Preprocessing","explanation":"Data clean।"}
],

'malayalam': [
{"question":"ML life cycle എന്താണ്?","options":["A) Model steps","B) Coding","C) Testing","D) Deployment"],"correct":"A) Model steps","explanation":"Data മുതൽ deployment വരെ process."},
{"question":"First step?","options":["A) Problem define","B) Train","C) Deploy","D) Test"],"correct":"A) Problem define","explanation":"Problem മനസിലാക്കണം."},
{"question":"Data collection?","options":["A) Data ശേഖരണം","B) Delete","C) Train","D) Test"],"correct":"A) Data ശേഖരണം","explanation":"Relevant data എടുക്കണം."},
{"question":"Preprocessing?","options":["A) Clean transform","B) Train","C) Deploy","D) Loop"],"correct":"A) Clean transform","explanation":"Data തയ്യാറാക്കുന്നു."},
{"question":"Feature engineering?","options":["A) Useful features","B) Delete","C) Coding","D) Loop"],"correct":"A) Useful features","explanation":"Performance improve."},
{"question":"Training?","options":["A) Learn","B) Delete","C) Sort","D) Loop"],"correct":"A) Learn","explanation":"Model പഠിക്കുന്നു."},
{"question":"Evaluation?","options":["A) Check","B) Train","C) Delete","D) Loop"],"correct":"A) Check","explanation":"Performance check."},
{"question":"Deployment?","options":["A) Real use","B) Train","C) Delete","D) Loop"],"correct":"A) Real use","explanation":"Real world use."},
{"question":"Monitoring?","options":["A) Track","B) Delete","C) Code","D) Loop"],"correct":"A) Track","explanation":"Performance track."},
{"question":"Quality improve?","options":["A) Preprocessing","B) Deploy","C) Test","D) Loop"],"correct":"A) Preprocessing","explanation":"Clean data."}
],
}
},  # end ml topics

}  # end TOPIC_Q


# ═══════════════════════════════════════════════════════════════
# COURSE COMPLETION QUESTION BANK (20 questions per lang per iface)
# ═══════════════════════════════════════════════════════════════

COURSE_Q = {
'python': {
'english': [
  {"question":"Which keyword defines a function?","options":["A) func","B) def","C) function","D) define"],"correct":"B) def","explanation":"def defines a function."},
  {"question":"What does len([1,2,3]) return?","options":["A) 2","B) 3","C) 4","D) 1"],"correct":"B) 3","explanation":"len() counts elements."},
  {"question":"Which loop iterates over a sequence?","options":["A) foreach","B) while","C) for","D) loop"],"correct":"C) for","explanation":"for iterates over sequences."},
  {"question":"How to open a file for reading?","options":["A) open('f','w')","B) open('f','r')","C) open('f','a')","D) open('f','x')"],"correct":"B) open('f','r')","explanation":"'r' opens for reading."},
  {"question":"What handles exceptions in Python?","options":["A) catch","B) except","C) handle","D) error"],"correct":"B) except","explanation":"try/except handles errors."},
  {"question":"What is 'self' in a class?","options":["A) Global var","B) Current object","C) Built-in func","D) Class name"],"correct":"B) Current object","explanation":"self refers to the current instance."},
  {"question":"What does range(0,5) give?","options":["A) 0-5","B) 0-4","C) 1-5","D) 1-4"],"correct":"B) 0-4","explanation":"Stop is excluded in range."},
  {"question":"Which adds to end of list?","options":["A) add()","B) push()","C) append()","D) insert()"],"correct":"C) append()","explanation":"append() adds to end."},
  {"question":"What is a tuple?","options":["A) Mutable sequence","B) Immutable sequence","C) Dict type","D) Set type"],"correct":"B) Immutable sequence","explanation":"Tuples cannot be changed."},
  {"question":"What does import do?","options":["A) Export","B) Load module","C) Delete module","D) Create module"],"correct":"B) Load module","explanation":"import loads a module."},
  {"question":"What does 10 % 3 return?","options":["A) 3","B) 0","C) 1","D) 3.33"],"correct":"C) 1","explanation":"% gives remainder."},
  {"question":"What is bool(0)?","options":["A) True","B) False","C) 0","D) None"],"correct":"B) False","explanation":"0 is falsy."},
  {"question":"What does strip() do?","options":["A) Split","B) Remove end spaces","C) Reverse","D) Uppercase"],"correct":"B) Remove end spaces","explanation":"strip() removes whitespace."},
  {"question":"How do you define a class?","options":["A) def MyClass:","B) class MyClass:","C) object MyClass:","D) type MyClass:"],"correct":"B) class MyClass:","explanation":"class keyword defines a class."},
  {"question":"What is the power operator?","options":["A) ^","B) **","C) ^^","D) pow"],"correct":"B) **","explanation":"** is exponentiation."},
  {"question":"What does break do?","options":["A) Pause","B) Skip iteration","C) Exit loop","D) Return None"],"correct":"C) Exit loop","explanation":"break exits loop immediately."},
  {"question":"Which creates an empty dict?","options":["A) []","B) ()","C) {}","D) set()"],"correct":"C) {}","explanation":"Empty {} creates dictionary."},
  {"question":"What is 2**8?","options":["A) 16","B) 64","C) 128","D) 256"],"correct":"D) 256","explanation":"2 to power 8 = 256."},
  {"question":"What does pass do?","options":["A) Skip function","B) Nothing","C) Return zero","D) Continue"],"correct":"B) Nothing","explanation":"pass is a placeholder."},
  {"question":"Python module is?","options":["A) A variable","B) A reusable code file","C) A loop type","D) A class method"],"correct":"B) A reusable code file","explanation":"Modules are importable Python files."},
  {"question":"What is 'Hello'[0]?","options":["A) e","B) H","C) o","D) l"],"correct":"B) H","explanation":"Index 0 = first character."},
  {"question":"File writing mode?","options":["A) r","B) a","C) w","D) x"],"correct":"C) w","explanation":"'w' opens for writing."},
  {"question":"What does type('x') return?","options":["A) string","B) str","C) <class 'str'>","D) text"],"correct":"C) <class 'str'>","explanation":"type() returns class with brackets."},
  {"question":"What is d['a'] for dict d?","options":["A) Adds key a","B) Gets value for key a","C) Deletes key a","D) Lists all keys"],"correct":"B) Gets value for key a","explanation":"d['key'] retrieves the value."},
  {"question":"Which data type has no duplicates?","options":["A) list","B) tuple","C) dict","D) set"],"correct":"D) set","explanation":"set stores unique values only."},
],
'tamil': [
  {"question":"Function define செய்ய எந்த keyword?","options":["A) func","B) def","C) function","D) define"],"correct":"B) def","explanation":"def function define செய்யும்."},
  {"question":"len([1,2,3]) என்ன return செய்யும்?","options":["A) 2","B) 3","C) 4","D) 1"],"correct":"B) 3","explanation":"len() elements count தரும்."},
  {"question":"Sequence iterate செய்ய எந்த loop?","options":["A) foreach","B) while","C) for","D) loop"],"correct":"C) for","explanation":"for sequence iterate செய்யும்."},
  {"question":"Reading-க்கு file திறக்க?","options":["A) open('f','w')","B) open('f','r')","C) open('f','a')","D) open('f','x')"],"correct":"B) open('f','r')","explanation":"'r' reading-க்கு திறக்கும்."},
  {"question":"Exceptions handle செய்ய?","options":["A) catch","B) except","C) handle","D) error"],"correct":"B) except","explanation":"try/except errors handle செய்யும்."},
  {"question":"Class-ல் 'self' என்றால் என்ன?","options":["A) Global variable","B) தற்போதைய object","C) Built-in function","D) Class பெயர்"],"correct":"B) தற்போதைய object","explanation":"self current instance குறிக்கும்."},
  {"question":"range(0,5) என்ன தரும்?","options":["A) 0-5","B) 0-4","C) 1-5","D) 1-4"],"correct":"B) 0-4","explanation":"range-ல் stop include ஆகாது."},
  {"question":"List-ன் கடைசியில் சேர்க்க?","options":["A) add()","B) push()","C) append()","D) insert()"],"correct":"C) append()","explanation":"append() கடைசியில் சேர்க்கும்."},
  {"question":"Tuple என்றால் என்ன?","options":["A) Mutable sequence","B) Immutable sequence","C) Dict type","D) Set type"],"correct":"B) Immutable sequence","explanation":"Tuple மாற்ற முடியாது."},
  {"question":"import என்ன செய்யும்?","options":["A) Export","B) Module load","C) Module delete","D) Module create"],"correct":"B) Module load","explanation":"import module load செய்யும்."},
  {"question":"10 % 3 என்ன?","options":["A) 3","B) 0","C) 1","D) 3.33"],"correct":"C) 1","explanation":"% மீதம் தரும்."},
  {"question":"bool(0) என்ன?","options":["A) True","B) False","C) 0","D) None"],"correct":"B) False","explanation":"0 Python-ல் False."},
  {"question":"strip() என்ன செய்யும்?","options":["A) Split","B) இரு புறமும் spaces நீக்கும்","C) Reverse","D) Uppercase"],"correct":"B) இரு புறமும் spaces நீக்கும்","explanation":"strip() whitespace நீக்கும்."},
  {"question":"Class define செய்ய?","options":["A) def MyClass:","B) class MyClass:","C) object MyClass:","D) type MyClass:"],"correct":"B) class MyClass:","explanation":"class keyword class define செய்யும்."},
  {"question":"Power operator எது?","options":["A) ^","B) **","C) ^^","D) pow"],"correct":"B) **","explanation":"** exponentiation operator."},
  {"question":"break என்ன செய்யும்?","options":["A) Pause","B) Iteration skip","C) Loop விடும்","D) None return"],"correct":"C) Loop விடும்","explanation":"break loop உடனே நிறுத்தும்."},
  {"question":"Empty dict எப்படி?","options":["A) []","B) ()","C) {}","D) set()"],"correct":"C) {}","explanation":"Empty {} dictionary உருவாக்கும்."},
  {"question":"2**8 என்ன?","options":["A) 16","B) 64","C) 128","D) 256"],"correct":"D) 256","explanation":"2-ன் 8-வது power = 256."},
  {"question":"pass என்ன செய்யும்?","options":["A) Function skip","B) எதுவும் செய்யாது","C) Zero return","D) Continue"],"correct":"B) எதுவும் செய்யாது","explanation":"pass placeholder."},
  {"question":"Python module என்றால் என்ன?","options":["A) Variable","B) Reusable code file","C) Loop type","D) Class method"],"correct":"B) Reusable code file","explanation":"Modules import செய்யக்கூடிய Python files."},
  {"question":"'Hello'[0] என்ன?","options":["A) e","B) H","C) o","D) l"],"correct":"B) H","explanation":"Index 0 = முதல் character."},
  {"question":"File writing mode?","options":["A) r","B) a","C) w","D) x"],"correct":"C) w","explanation":"'w' writing-க்கு திறக்கும்."},
  {"question":"type('x') என்ன return செய்யும்?","options":["A) string","B) str","C) <class 'str'>","D) text"],"correct":"C) <class 'str'>","explanation":"type() class brackets-உடன் தரும்."},
  {"question":"d['a'] என்ன செய்யும்?","options":["A) Key a சேர்க்கும்","B) Key a-ன் value தரும்","C) Key a நீக்கும்","D) எல்லா keys காட்டும்"],"correct":"B) Key a-ன் value தரும்","explanation":"d['key'] value return செய்யும்."},
  {"question":"எந்த data type duplicates இல்லாமல் சேமிக்கும்?","options":["A) list","B) tuple","C) dict","D) set"],"correct":"D) set","explanation":"set unique values மட்டும் சேமிக்கும்."},
],
'tanglish': [
  {"question":"Function define panna ethu keyword?","options":["A) func","B) def","C) function","D) define"],"correct":"B) def","explanation":"def function define pannum."},
  {"question":"len([1,2,3]) enna return pannum?","options":["A) 2","B) 3","C) 4","D) 1"],"correct":"B) 3","explanation":"len() elements count tharum."},
  {"question":"Sequence iterate panna ethu loop?","options":["A) foreach","B) while","C) for","D) loop"],"correct":"C) for","explanation":"for sequence iterate pannum."},
  {"question":"Reading-ku file thiraka?","options":["A) open('f','w')","B) open('f','r')","C) open('f','a')","D) open('f','x')"],"correct":"B) open('f','r')","explanation":"'r' reading-ku thirakkum."},
  {"question":"Exceptions handle panna?","options":["A) catch","B) except","C) handle","D) error"],"correct":"B) except","explanation":"try/except errors handle pannum."},
  {"question":"Class-la 'self' enna?","options":["A) Global variable","B) Current object","C) Built-in function","D) Class name"],"correct":"B) Current object","explanation":"self current instance-a refer pannum."},
  {"question":"range(0,5) enna tharum?","options":["A) 0-5","B) 0-4","C) 1-5","D) 1-4"],"correct":"B) 0-4","explanation":"range-la stop include aagadu."},
  {"question":"List-oda last-la add panna?","options":["A) add()","B) push()","C) append()","D) insert()"],"correct":"C) append()","explanation":"append() last-la add pannum."},
  {"question":"Tuple enna?","options":["A) Mutable sequence","B) Immutable sequence","C) Dict type","D) Set type"],"correct":"B) Immutable sequence","explanation":"Tuple maara mudiyaadu."},
  {"question":"import enna pannum?","options":["A) Export","B) Module load","C) Module delete","D) Module create"],"correct":"B) Module load","explanation":"import module load pannum."},
  {"question":"10 % 3 enna?","options":["A) 3","B) 0","C) 1","D) 3.33"],"correct":"C) 1","explanation":"% remainder tharum."},
  {"question":"bool(0) enna?","options":["A) True","B) False","C) 0","D) None"],"correct":"B) False","explanation":"0 Python-la False."},
  {"question":"strip() enna pannum?","options":["A) Split","B) Irandu pakkamum spaces neekkum","C) Reverse","D) Uppercase"],"correct":"B) Irandu pakkamum spaces neekkum","explanation":"strip() whitespace neekkum."},
  {"question":"Class define panna?","options":["A) def MyClass:","B) class MyClass:","C) object MyClass:","D) type MyClass:"],"correct":"B) class MyClass:","explanation":"class keyword class define pannum."},
  {"question":"Power operator ethu?","options":["A) ^","B) **","C) ^^","D) pow"],"correct":"B) **","explanation":"** exponentiation operator."},
  {"question":"break enna pannum?","options":["A) Pause","B) Iteration skip","C) Loop vida vidum","D) None return"],"correct":"C) Loop vida vidum","explanation":"break loop-a udane nirutthum."},
  {"question":"Empty dict epdi?","options":["A) []","B) ()","C) {}","D) set()"],"correct":"C) {}","explanation":"Empty {} dictionary create pannum."},
  {"question":"2**8 enna?","options":["A) 16","B) 64","C) 128","D) 256"],"correct":"D) 256","explanation":"2-oda 8th power = 256."},
  {"question":"pass enna pannum?","options":["A) Function skip","B) Ethuvum pannadu","C) Zero return","D) Continue"],"correct":"B) Ethuvum pannadu","explanation":"pass placeholder."},
  {"question":"Python module enna?","options":["A) Variable","B) Reusable code file","C) Loop type","D) Class method"],"correct":"B) Reusable code file","explanation":"Modules import panna mudiyra Python files."},
  {"question":"'Hello'[0] enna?","options":["A) e","B) H","C) o","D) l"],"correct":"B) H","explanation":"Index 0 = first character."},
  {"question":"File writing mode?","options":["A) r","B) a","C) w","D) x"],"correct":"C) w","explanation":"'w' writing-ku thirakkum."},
  {"question":"type('x') enna return pannum?","options":["A) string","B) str","C) <class 'str'>","D) text"],"correct":"C) <class 'str'>","explanation":"type() class brackets-oda tharum."},
  {"question":"d['a'] enna pannum?","options":["A) Key a add pannum","B) Key a-oda value tharum","C) Key a neekum","D) Ella keys kaattum"],"correct":"B) Key a-oda value tharum","explanation":"d['key'] value return pannum."},
  {"question":"Ethu data type duplicates illama store pannum?","options":["A) list","B) tuple","C) dict","D) set"],"correct":"D) set","explanation":"set unique values mattum store pannum."},
],
'hindi': [
  {"question":"Function define करने का keyword?","options":["A) func","B) def","C) function","D) define"],"correct":"B) def","explanation":"def function define करता है।"},
  {"question":"len([1,2,3]) क्या return करेगा?","options":["A) 2","B) 3","C) 4","D) 1"],"correct":"B) 3","explanation":"len() elements गिनता है।"},
  {"question":"Sequence iterate करने का loop?","options":["A) foreach","B) while","C) for","D) loop"],"correct":"C) for","explanation":"for sequence iterate करता है।"},
  {"question":"Reading के लिए file खोलना?","options":["A) open('f','w')","B) open('f','r')","C) open('f','a')","D) open('f','x')"],"correct":"B) open('f','r')","explanation":"'r' reading के लिए खोलता है।"},
  {"question":"Exceptions handle करना?","options":["A) catch","B) except","C) handle","D) error"],"correct":"B) except","explanation":"try/except errors handle करता है।"},
  {"question":"Class में 'self' क्या है?","options":["A) Global variable","B) Current object","C) Built-in function","D) Class नाम"],"correct":"B) Current object","explanation":"self current instance को refer करता है।"},
  {"question":"range(0,5) क्या देता है?","options":["A) 0-5","B) 0-4","C) 1-5","D) 1-4"],"correct":"B) 0-4","explanation":"range में stop शामिल नहीं।"},
  {"question":"List के अंत में जोड़ना?","options":["A) add()","B) push()","C) append()","D) insert()"],"correct":"C) append()","explanation":"append() अंत में जोड़ता है।"},
  {"question":"Tuple क्या है?","options":["A) Mutable sequence","B) Immutable sequence","C) Dict type","D) Set type"],"correct":"B) Immutable sequence","explanation":"Tuple बदल नहीं सकते।"},
  {"question":"import क्या करता है?","options":["A) Export","B) Module load","C) Module delete","D) Module create"],"correct":"B) Module load","explanation":"import module load करता है।"},
  {"question":"10 % 3 क्या है?","options":["A) 3","B) 0","C) 1","D) 3.33"],"correct":"C) 1","explanation":"% शेषफल देता है।"},
  {"question":"bool(0) क्या है?","options":["A) True","B) False","C) 0","D) None"],"correct":"B) False","explanation":"Python में 0 False है।"},
  {"question":"strip() क्या करता है?","options":["A) Split","B) दोनों तरफ spaces हटाता है","C) Reverse","D) Uppercase"],"correct":"B) दोनों तरफ spaces हटाता है","explanation":"strip() whitespace हटाता है।"},
  {"question":"Class define करना?","options":["A) def MyClass:","B) class MyClass:","C) object MyClass:","D) type MyClass:"],"correct":"B) class MyClass:","explanation":"class keyword class बनाता है।"},
  {"question":"Power operator कौन सा?","options":["A) ^","B) **","C) ^^","D) pow"],"correct":"B) **","explanation":"** exponentiation operator है।"},
  {"question":"break क्या करता है?","options":["A) Pause","B) Iteration skip","C) Loop छोड़ता है","D) None return"],"correct":"C) Loop छोड़ता है","explanation":"break loop तुरंत बंद करता है।"},
  {"question":"Empty dict कैसे बनाएँ?","options":["A) []","B) ()","C) {}","D) set()"],"correct":"C) {}","explanation":"Empty {} dictionary बनाता है।"},
  {"question":"2**8 कितना?","options":["A) 16","B) 64","C) 128","D) 256"],"correct":"D) 256","explanation":"2 की घात 8 = 256."},
  {"question":"pass क्या करता है?","options":["A) Function skip","B) कुछ नहीं","C) Zero return","D) Continue"],"correct":"B) कुछ नहीं","explanation":"pass placeholder है।"},
  {"question":"Python module क्या है?","options":["A) Variable","B) Reusable code file","C) Loop type","D) Class method"],"correct":"B) Reusable code file","explanation":"Modules import किए जाने वाले Python files हैं।"},
  {"question":"'Hello'[0] क्या है?","options":["A) e","B) H","C) o","D) l"],"correct":"B) H","explanation":"Index 0 = पहला character."},
  {"question":"File writing mode?","options":["A) r","B) a","C) w","D) x"],"correct":"C) w","explanation":"'w' writing के लिए खोलता है।"},
  {"question":"type('x') क्या return करेगा?","options":["A) string","B) str","C) <class 'str'>","D) text"],"correct":"C) <class 'str'>","explanation":"type() brackets के साथ class देता है।"},
  {"question":"d['a'] क्या करता है?","options":["A) Key a जोड़ता है","B) Key a की value देता है","C) Key a हटाता है","D) सब keys दिखाता है"],"correct":"B) Key a की value देता है","explanation":"d['key'] value return करता है।"},
  {"question":"कौन सा data type duplicates नहीं रखता?","options":["A) list","B) tuple","C) dict","D) set"],"correct":"D) set","explanation":"set unique values ही रखता है।"},
],
'malayalam': [
  {"question":"Function define ചെയ്യാൻ ഏത് keyword?","options":["A) func","B) def","C) function","D) define"],"correct":"B) def","explanation":"def function define ചെയ്യുന്നു."},
  {"question":"len([1,2,3]) എന്ത് return ചെയ്യും?","options":["A) 2","B) 3","C) 4","D) 1"],"correct":"B) 3","explanation":"len() elements എണ്ണുന്നു."},
  {"question":"Sequence iterate ചെയ്യാൻ ഏത് loop?","options":["A) foreach","B) while","C) for","D) loop"],"correct":"C) for","explanation":"for sequence iterate ചെയ്യുന്നു."},
  {"question":"Reading-ന് file തുറക്കാൻ?","options":["A) open('f','w')","B) open('f','r')","C) open('f','a')","D) open('f','x')"],"correct":"B) open('f','r')","explanation":"'r' reading-ന് തുറക്കുന്നു."},
  {"question":"Exceptions handle ചെയ്യാൻ?","options":["A) catch","B) except","C) handle","D) error"],"correct":"B) except","explanation":"try/except errors handle ചെയ്യുന്നു."},
  {"question":"Class-ൽ 'self' എന്നാൽ?","options":["A) Global variable","B) നിലവിലെ object","C) Built-in function","D) Class name"],"correct":"B) നിലവിലെ object","explanation":"self current instance-നെ refer ചെയ്യുന്നു."},
  {"question":"range(0,5) എന്ത് നൽകും?","options":["A) 0-5","B) 0-4","C) 1-5","D) 1-4"],"correct":"B) 0-4","explanation":"range-ൽ stop ഉൾപ്പെടില്ല."},
  {"question":"List-ന്റെ അവസാനം add ചെയ്യാൻ?","options":["A) add()","B) push()","C) append()","D) insert()"],"correct":"C) append()","explanation":"append() അവസാനം add ചെയ്യുന്നു."},
  {"question":"Tuple എന്നാൽ?","options":["A) Mutable sequence","B) Immutable sequence","C) Dict type","D) Set type"],"correct":"B) Immutable sequence","explanation":"Tuple മാറ്റാൻ കഴിയില്ല."},
  {"question":"import എന്ത് ചെയ്യുന്നു?","options":["A) Export","B) Module load","C) Module delete","D) Module create"],"correct":"B) Module load","explanation":"import module load ചെയ്യുന്നു."},
  {"question":"10 % 3 എന്ത്?","options":["A) 3","B) 0","C) 1","D) 3.33"],"correct":"C) 1","explanation":"% remainder നൽകുന്നു."},
  {"question":"bool(0) എന്ത്?","options":["A) True","B) False","C) 0","D) None"],"correct":"B) False","explanation":"Python-ൽ 0 False ആണ്."},
  {"question":"strip() എന്ത് ചെയ്യുന്നു?","options":["A) Split","B) ഇരുവശത്തും spaces നീക്കൽ","C) Reverse","D) Uppercase"],"correct":"B) ഇരുവശത്തും spaces നീക്കൽ","explanation":"strip() whitespace നീക്കുന്നു."},
  {"question":"Class define ചെയ്യാൻ?","options":["A) def MyClass:","B) class MyClass:","C) object MyClass:","D) type MyClass:"],"correct":"B) class MyClass:","explanation":"class keyword class ഉണ്ടാക്കുന്നു."},
  {"question":"Power operator ഏതാണ്?","options":["A) ^","B) **","C) ^^","D) pow"],"correct":"B) **","explanation":"** exponentiation operator ആണ്."},
  {"question":"break എന്ത് ചെയ്യുന്നു?","options":["A) Pause","B) Iteration skip","C) Loop-ൽ നിന്ന് പുറത്ത്","D) None return"],"correct":"C) Loop-ൽ നിന്ന് പുറത്ത്","explanation":"break loop ഉടൻ നിർത്തുന്നു."},
  {"question":"Empty dict എങ്ങനെ?","options":["A) []","B) ()","C) {}","D) set()"],"correct":"C) {}","explanation":"Empty {} dictionary ഉണ്ടാക്കുന്നു."},
  {"question":"2**8 എത്ര?","options":["A) 16","B) 64","C) 128","D) 256"],"correct":"D) 256","explanation":"2-ന്റെ 8-ആം power = 256."},
  {"question":"pass എന്ത് ചെയ്യുന്നു?","options":["A) Function skip","B) ഒന്നും ചെയ്യുന്നില്ല","C) Zero return","D) Continue"],"correct":"B) ഒന്നും ചെയ്യുന്നില്ല","explanation":"pass placeholder ആണ്."},
  {"question":"Python module എന്നാൽ?","options":["A) Variable","B) Reusable code file","C) Loop type","D) Class method"],"correct":"B) Reusable code file","explanation":"Modules import ചെയ്യാൻ കഴിയുന്ന Python files."},
  {"question":"'Hello'[0] എന്ത്?","options":["A) e","B) H","C) o","D) l"],"correct":"B) H","explanation":"Index 0 = ആദ്യ character."},
  {"question":"File writing mode?","options":["A) r","B) a","C) w","D) x"],"correct":"C) w","explanation":"'w' writing-ന് തുറക്കുന്നു."},
  {"question":"type('x') എന്ത് return ചെയ്യും?","options":["A) string","B) str","C) <class 'str'>","D) text"],"correct":"C) <class 'str'>","explanation":"type() brackets-ഉമായി class നൽകുന്നു."},
  {"question":"d['a'] എന്ത് ചെയ്യുന്നു?","options":["A) Key a add ചെയ്യുന്നു","B) Key a-ന്റെ value നൽകുന്നു","C) Key a നീക്കുന്നു","D) എല്ലാ keys കാണിക്കുന്നു"],"correct":"B) Key a-ന്റെ value നൽകുന്നു","explanation":"d['key'] value return ചെയ്യുന്നു."},
  {"question":"Duplicates ഇല്ലാതെ store ചെയ്യുന്ന data type?","options":["A) list","B) tuple","C) dict","D) set"],"correct":"D) set","explanation":"set unique values മാത്രം store ചെയ്യുന്നു."},
],
},
# Java, AI, ML course questions — use english as base, fallback for other langs
'java': {
'english': [
  {"question":"Java entry point?","options":["A) start()","B) main()","C) run()","D) begin()"],"correct":"B) main()","explanation":"public static void main() is Java's entry point."},
  {"question":"How to print in Java?","options":["A) print()","B) echo()","C) System.out.println()","D) console.log()"],"correct":"C) System.out.println()","explanation":"System.out.println() prints in Java."},
  {"question":"Object creation keyword?","options":["A) create","B) make","C) object","D) new"],"correct":"D) new","explanation":"new creates objects in Java."},
  {"question":"Inheritance keyword?","options":["A) inherits","B) extends","C) implements","D) super"],"correct":"B) extends","explanation":"extends inherits from parent class."},
  {"question":"Exception handling keyword?","options":["A) except","B) handle","C) catch","D) error"],"correct":"C) catch","explanation":"try/catch handles exceptions in Java."},
  {"question":"Interface keyword?","options":["A) extends","B) implements","C) interface","D) abstract"],"correct":"B) implements","explanation":"implements uses an interface."},
  {"question":"What is int size in Java?","options":["A) 2 bytes","B) 4 bytes","C) 8 bytes","D) 1 byte"],"correct":"B) 4 bytes","explanation":"int is 32-bit (4 bytes)."},
  {"question":"Which allows duplicates?","options":["A) Set","B) Map","C) List","D) TreeSet"],"correct":"C) List","explanation":"List allows duplicates."},
  {"question":"What does static mean?","options":["A) Cannot change","B) Belongs to class not instance","C) Private method","D) Final variable"],"correct":"B) Belongs to class not instance","explanation":"static members belong to the class."},
  {"question":"What is a constructor?","options":["A) Returns value","B) Called on object creation","C) Interface method","D) Static method"],"correct":"B) Called on object creation","explanation":"Constructor initializes the object."},
  {"question":"Prevent inheritance with?","options":["A) static","B) private","C) final","D) abstract"],"correct":"C) final","explanation":"final class cannot be extended."},
  {"question":"What is polymorphism?","options":["A) Multiple classes","B) One method, many forms","C) Multiple inheritance","D) Static binding"],"correct":"B) One method, many forms","explanation":"Polymorphism = same method, different behaviour."},
  {"question":"Auto-imported Java package?","options":["A) java.io","B) java.util","C) java.lang","D) java.net"],"correct":"C) java.lang","explanation":"java.lang is auto-imported."},
  {"question":"10 % 3 in Java?","options":["A) 3","B) 1","C) 0","D) 3.33"],"correct":"B) 1","explanation":"% gives remainder."},
  {"question":"What is encapsulation?","options":["A) Using loops","B) Hiding data with private + getters/setters","C) Extending class","D) Method overloading"],"correct":"B) Hiding data with private + getters/setters","explanation":"Encapsulation restricts direct data access."},
  {"question":"What is abstraction?","options":["A) Showing all details","B) Hiding complexity, showing essentials","C) Creating objects","D) Using arrays"],"correct":"B) Hiding complexity, showing essentials","explanation":"Abstraction hides complexity."},
  {"question":"JVM stands for?","options":["A) Java Virtual Memory","B) Java Variable Method","C) Java Virtual Machine","D) Java Version Manager"],"correct":"C) Java Virtual Machine","explanation":"JVM runs Java bytecode."},
  {"question":"Java file extension?","options":["A) .py","B) .class","C) .java","D) .cpp"],"correct":"C) .java","explanation":"Java source files use .java."},
  {"question":"What is method overloading?","options":["A) Same name different parameters","B) Override parent method","C) Multiple inheritance","D) Static method"],"correct":"A) Same name different parameters","explanation":"Overloading = same name, different params."},
  {"question":"Public modifier means?","options":["A) Only in class","B) Only in package","C) Accessible everywhere","D) Only subclasses"],"correct":"C) Accessible everywhere","explanation":"public is accessible from anywhere."},
  {"question":"String in Java is?","options":["A) Primitive type","B) Object/Reference type","C) int subtype","D) char array only"],"correct":"B) Object/Reference type","explanation":"String is an object in Java."},
  {"question":"What is ArrayList?","options":["A) Fixed size array","B) Resizable List implementation","C) A Set","D) A Map"],"correct":"B) Resizable List implementation","explanation":"ArrayList is a resizable array-based List."},
  {"question":"Thread in Java is?","options":["A) A database connection","B) A lightweight process","C) A variable","D) A method"],"correct":"B) A lightweight process","explanation":"Threads enable concurrent execution."},
  {"question":"What does void mean?","options":["A) Empty string","B) No return value","C) Null","D) Boolean false"],"correct":"B) No return value","explanation":"void means the method returns nothing."},
  {"question":"What is an array in Java?","options":["A) Variable size collection","B) Fixed size same-type elements","C) Dictionary","D) Set"],"correct":"B) Fixed size same-type elements","explanation":"Arrays hold fixed-size elements of same type."},
],
'tamil': [
  {"question":"Java entry point?","options":["A) start()","B) main()","C) run()","D) begin()"],"correct":"B) main()","explanation":"public static void main() Java-இன் entry point."},
  {"question":"Java-ல் print செய்ய?","options":["A) print()","B) echo()","C) System.out.println()","D) console.log()"],"correct":"C) System.out.println()","explanation":"System.out.println() Java-ல் print செய்யும்."},
  {"question":"Object create செய்ய keyword?","options":["A) create","B) make","C) object","D) new"],"correct":"D) new","explanation":"new Java-ல் objects create செய்யும்."},
  {"question":"Inheritance keyword?","options":["A) inherits","B) extends","C) implements","D) super"],"correct":"B) extends","explanation":"extends parent class-ல் இருந்து inherit செய்யும்."},
  {"question":"Exception handling keyword?","options":["A) except","B) handle","C) catch","D) error"],"correct":"C) catch","explanation":"try/catch Java-ல் exceptions handle செய்யும்."},
  {"question":"Interface keyword?","options":["A) extends","B) implements","C) interface","D) abstract"],"correct":"B) implements","explanation":"implements interface-ஐ use செய்யும்."},
  {"question":"Java-ல் int size என்ன?","options":["A) 2 bytes","B) 4 bytes","C) 8 bytes","D) 1 byte"],"correct":"B) 4 bytes","explanation":"int 32-bit (4 bytes)."},
  {"question":"Duplicates allow செய்வது?","options":["A) Set","B) Map","C) List","D) TreeSet"],"correct":"C) List","explanation":"List duplicates allow செய்யும்."},
  {"question":"static என்றால் என்ன?","options":["A) மாற்ற முடியாத","B) Class-க்கு சொந்தமானது, instance-க்கு அல்ல","C) Private method","D) Final variable"],"correct":"B) Class-க்கு சொந்தமானது, instance-க்கு அல்ல","explanation":"static members class-க்கு சொந்தமானவை."},
  {"question":"Constructor என்றால் என்ன?","options":["A) Value return செய்யும்","B) Object create ஆகும்போது call ஆகும்","C) Interface method","D) Static method"],"correct":"B) Object create ஆகும்போது call ஆகும்","explanation":"Constructor object-ஐ initialize செய்யும்."},
  {"question":"Inheritance தடுக்க எந்த keyword?","options":["A) static","B) private","C) final","D) abstract"],"correct":"C) final","explanation":"final class extend செய்ய முடியாது."},
  {"question":"Polymorphism என்றால் என்ன?","options":["A) Multiple classes","B) ஒரே method, பல வடிவங்கள்","C) Multiple inheritance","D) Static binding"],"correct":"B) ஒரே method, பல வடிவங்கள்","explanation":"Polymorphism = same method, different behaviour."},
  {"question":"Auto-import ஆகும் Java package?","options":["A) java.io","B) java.util","C) java.lang","D) java.net"],"correct":"C) java.lang","explanation":"java.lang automatically import ஆகும்."},
  {"question":"Java-ல் 10 % 3?","options":["A) 3","B) 1","C) 0","D) 3.33"],"correct":"B) 1","explanation":"% மீதம் தரும்."},
  {"question":"Encapsulation என்றால் என்ன?","options":["A) Loops பயன்படுத்துவது","B) private + getters/setters மூலம் data மறைத்தல்","C) Class extend செய்வது","D) Method overloading"],"correct":"B) private + getters/setters மூலம் data மறைத்தல்","explanation":"Encapsulation data-ஐ நேரடியாக access தடுக்கும்."},
  {"question":"Abstraction என்றால் என்ன?","options":["A) எல்லாவற்றையும் காட்டுவது","B) Complexity மறைத்து essentials காட்டுவது","C) Objects create செய்வது","D) Arrays பயன்படுத்துவது"],"correct":"B) Complexity மறைத்து essentials காட்டுவது","explanation":"Abstraction complexity மறைக்கும்."},
  {"question":"JVM என்றால் என்ன?","options":["A) Java Virtual Memory","B) Java Variable Method","C) Java Virtual Machine","D) Java Version Manager"],"correct":"C) Java Virtual Machine","explanation":"JVM Java bytecode run செய்யும்."},
  {"question":"Java file extension?","options":["A) .py","B) .class","C) .java","D) .cpp"],"correct":"C) .java","explanation":"Java source files .java பயன்படுத்துகின்றன."},
  {"question":"Method overloading என்றால் என்ன?","options":["A) ஒரே பெயர் வேவ்வேறு parameters","B) Parent method override","C) Multiple inheritance","D) Static method"],"correct":"A) ஒரே பெயர் வேவ்வேறு parameters","explanation":"Overloading = same name, different params."},
  {"question":"public modifier என்றால் என்ன?","options":["A) Class-ல் மட்டும்","B) Package-ல் மட்டும்","C) எங்கும் access செய்யலாம்","D) Subclasses மட்டும்"],"correct":"C) எங்கும் access செய்யலாம்","explanation":"public எங்கிருந்தும் access செய்யலாம்."},
  {"question":"Java-ல் String என்பது?","options":["A) Primitive type","B) Object/Reference type","C) int subtype","D) char array மட்டும்"],"correct":"B) Object/Reference type","explanation":"String Java-ல் object ஆகும்."},
  {"question":"ArrayList என்றால் என்ன?","options":["A) Fixed size array","B) Resizable List implementation","C) Set","D) Map"],"correct":"B) Resizable List implementation","explanation":"ArrayList resizable array-based List."},
  {"question":"Java-ல் Thread என்றால் என்ன?","options":["A) Database connection","B) Lightweight process","C) Variable","D) Method"],"correct":"B) Lightweight process","explanation":"Threads concurrent execution enable செய்யும்."},
  {"question":"void என்றால் என்ன?","options":["A) Empty string","B) Return value இல்லை","C) Null","D) Boolean false"],"correct":"B) Return value இல்லை","explanation":"void method எந்த value-ம் return செய்யாது."},
  {"question":"Java-ல் array என்றால் என்ன?","options":["A) Variable size collection","B) Fixed size same-type elements","C) Dictionary","D) Set"],"correct":"B) Fixed size same-type elements","explanation":"Arrays fixed size same type elements சேமிக்கும்."},
],
'tanglish': [
  {"question":"Java entry point?","options":["A) start()","B) main()","C) run()","D) begin()"],"correct":"B) main()","explanation":"public static void main() Java-oda entry point."},
  {"question":"Java-la print panna?","options":["A) print()","B) echo()","C) System.out.println()","D) console.log()"],"correct":"C) System.out.println()","explanation":"System.out.println() Java-la print pannum."},
  {"question":"Object create panna keyword?","options":["A) create","B) make","C) object","D) new"],"correct":"D) new","explanation":"new Java-la objects create pannum."},
  {"question":"Inheritance keyword?","options":["A) inherits","B) extends","C) implements","D) super"],"correct":"B) extends","explanation":"extends parent class-la irundhu inherit pannum."},
  {"question":"Exception handling keyword?","options":["A) except","B) handle","C) catch","D) error"],"correct":"C) catch","explanation":"try/catch Java-la exceptions handle pannum."},
  {"question":"Interface keyword?","options":["A) extends","B) implements","C) interface","D) abstract"],"correct":"B) implements","explanation":"implements interface-a use pannum."},
  {"question":"Java-la int size enna?","options":["A) 2 bytes","B) 4 bytes","C) 8 bytes","D) 1 byte"],"correct":"B) 4 bytes","explanation":"int 32-bit (4 bytes)."},
  {"question":"Duplicates allow pannuvathu?","options":["A) Set","B) Map","C) List","D) TreeSet"],"correct":"C) List","explanation":"List duplicates allow pannum."},
  {"question":"static enna?","options":["A) Maara mudiyaadha","B) Class-ku sonnatha, instance-ku illa","C) Private method","D) Final variable"],"correct":"B) Class-ku sonnatha, instance-ku illa","explanation":"static members class-ku sonnatha."},
  {"question":"Constructor enna?","options":["A) Value return pannum","B) Object create aagum pothu call aagum","C) Interface method","D) Static method"],"correct":"B) Object create aagum pothu call aagum","explanation":"Constructor object-a initialize pannum."},
  {"question":"Inheritance restrict panna keyword?","options":["A) static","B) private","C) final","D) abstract"],"correct":"C) final","explanation":"final class extend panna mudiyaadu."},
  {"question":"Polymorphism enna?","options":["A) Multiple classes","B) Ore method, pala forms","C) Multiple inheritance","D) Static binding"],"correct":"B) Ore method, pala forms","explanation":"Polymorphism = same method, different behaviour."},
  {"question":"Auto-import aagra Java package?","options":["A) java.io","B) java.util","C) java.lang","D) java.net"],"correct":"C) java.lang","explanation":"java.lang automatic-a import aagum."},
  {"question":"Java-la 10 % 3?","options":["A) 3","B) 1","C) 0","D) 3.33"],"correct":"B) 1","explanation":"% remainder tharum."},
  {"question":"Encapsulation enna?","options":["A) Loops use pannuvathu","B) private + getters/setters-la data maraipathu","C) Class extend pannuvathu","D) Method overloading"],"correct":"B) private + getters/setters-la data maraipathu","explanation":"Encapsulation data-a direct access restrict pannum."},
  {"question":"Abstraction enna?","options":["A) Ellaamae kaattuvathu","B) Complexity marachu essentials kaattuvathu","C) Objects create pannuvathu","D) Arrays use pannuvathu"],"correct":"B) Complexity marachu essentials kaattuvathu","explanation":"Abstraction complexity maraikum."},
  {"question":"JVM enna?","options":["A) Java Virtual Memory","B) Java Variable Method","C) Java Virtual Machine","D) Java Version Manager"],"correct":"C) Java Virtual Machine","explanation":"JVM Java bytecode run pannum."},
  {"question":"Java file extension?","options":["A) .py","B) .class","C) .java","D) .cpp"],"correct":"C) .java","explanation":"Java source files .java use pannum."},
  {"question":"Method overloading enna?","options":["A) Ore peyar different parameters","B) Parent method override","C) Multiple inheritance","D) Static method"],"correct":"A) Ore peyar different parameters","explanation":"Overloading = same name, different params."},
  {"question":"public modifier enna?","options":["A) Class-la mattum","B) Package-la mattum","C) Engum access pannalaam","D) Subclasses mattum"],"correct":"C) Engum access pannalaam","explanation":"public everywhere access pannalaam."},
  {"question":"Java-la String enbathu?","options":["A) Primitive type","B) Object/Reference type","C) int subtype","D) char array mattum"],"correct":"B) Object/Reference type","explanation":"String Java-la object aagum."},
  {"question":"ArrayList enna?","options":["A) Fixed size array","B) Resizable List implementation","C) Set","D) Map"],"correct":"B) Resizable List implementation","explanation":"ArrayList resizable array-based List."},
  {"question":"Java-la Thread enna?","options":["A) Database connection","B) Lightweight process","C) Variable","D) Method"],"correct":"B) Lightweight process","explanation":"Threads concurrent execution enable pannum."},
  {"question":"void enna?","options":["A) Empty string","B) Return value illai","C) Null","D) Boolean false"],"correct":"B) Return value illai","explanation":"void method ethu value-um return pannadu."},
  {"question":"Java-la array enna?","options":["A) Variable size collection","B) Fixed size same-type elements","C) Dictionary","D) Set"],"correct":"B) Fixed size same-type elements","explanation":"Arrays fixed size same type elements store pannum."},
],
'hindi': [
  {"question":"Java entry point?","options":["A) start()","B) main()","C) run()","D) begin()"],"correct":"B) main()","explanation":"public static void main() Java का entry point है।"},
  {"question":"Java में print कैसे करें?","options":["A) print()","B) echo()","C) System.out.println()","D) console.log()"],"correct":"C) System.out.println()","explanation":"System.out.println() Java में print करता है।"},
  {"question":"Object बनाने का keyword?","options":["A) create","B) make","C) object","D) new"],"correct":"D) new","explanation":"new Java में objects बनाता है।"},
  {"question":"Inheritance keyword?","options":["A) inherits","B) extends","C) implements","D) super"],"correct":"B) extends","explanation":"extends parent class से inherit करता है।"},
  {"question":"Exception handling keyword?","options":["A) except","B) handle","C) catch","D) error"],"correct":"C) catch","explanation":"try/catch Java में exceptions handle करता है।"},
  {"question":"Interface keyword?","options":["A) extends","B) implements","C) interface","D) abstract"],"correct":"B) implements","explanation":"implements interface उपयोग करता है।"},
  {"question":"Java में int size?","options":["A) 2 bytes","B) 4 bytes","C) 8 bytes","D) 1 byte"],"correct":"B) 4 bytes","explanation":"int 32-bit (4 bytes) है।"},
  {"question":"Duplicates allow करता है?","options":["A) Set","B) Map","C) List","D) TreeSet"],"correct":"C) List","explanation":"List duplicates allow करती है।"},
  {"question":"static का मतलब?","options":["A) बदल नहीं सकते","B) Class का है, instance का नहीं","C) Private method","D) Final variable"],"correct":"B) Class का है, instance का नहीं","explanation":"static members class के होते हैं।"},
  {"question":"Constructor क्या है?","options":["A) Value return करता है","B) Object बनने पर call होता है","C) Interface method","D) Static method"],"correct":"B) Object बनने पर call होता है","explanation":"Constructor object initialize करता है।"},
  {"question":"Inheritance रोकने का keyword?","options":["A) static","B) private","C) final","D) abstract"],"correct":"C) final","explanation":"final class extend नहीं हो सकती।"},
  {"question":"Polymorphism क्या है?","options":["A) Multiple classes","B) एक method, कई forms","C) Multiple inheritance","D) Static binding"],"correct":"B) एक method, कई forms","explanation":"Polymorphism = same method, different behaviour."},
  {"question":"Auto-import Java package?","options":["A) java.io","B) java.util","C) java.lang","D) java.net"],"correct":"C) java.lang","explanation":"java.lang automatically import होता है।"},
  {"question":"Java में 10 % 3?","options":["A) 3","B) 1","C) 0","D) 3.33"],"correct":"B) 1","explanation":"% शेषफल देता है।"},
  {"question":"Encapsulation क्या है?","options":["A) Loops उपयोग","B) private + getters/setters से data छुपाना","C) Class extend करना","D) Method overloading"],"correct":"B) private + getters/setters से data छुपाना","explanation":"Encapsulation direct data access रोकता है।"},
  {"question":"Abstraction क्या है?","options":["A) सब दिखाना","B) Complexity छुपाकर essentials दिखाना","C) Objects बनाना","D) Arrays उपयोग"],"correct":"B) Complexity छुपाकर essentials दिखाना","explanation":"Abstraction complexity छुपाता है।"},
  {"question":"JVM का मतलब?","options":["A) Java Virtual Memory","B) Java Variable Method","C) Java Virtual Machine","D) Java Version Manager"],"correct":"C) Java Virtual Machine","explanation":"JVM Java bytecode चलाता है।"},
  {"question":"Java file extension?","options":["A) .py","B) .class","C) .java","D) .cpp"],"correct":"C) .java","explanation":"Java source files .java उपयोग करती हैं।"},
  {"question":"Method overloading क्या है?","options":["A) एक नाम, अलग parameters","B) Parent method override","C) Multiple inheritance","D) Static method"],"correct":"A) एक नाम, अलग parameters","explanation":"Overloading = same name, different params."},
  {"question":"public modifier का मतलब?","options":["A) सिर्फ class में","B) सिर्फ package में","C) हर जगह से accessible","D) सिर्फ subclasses में"],"correct":"C) हर जगह से accessible","explanation":"public हर जगह से accessible है।"},
  {"question":"Java में String क्या है?","options":["A) Primitive type","B) Object/Reference type","C) int subtype","D) सिर्फ char array"],"correct":"B) Object/Reference type","explanation":"String Java में object है।"},
  {"question":"ArrayList क्या है?","options":["A) Fixed size array","B) Resizable List implementation","C) Set","D) Map"],"correct":"B) Resizable List implementation","explanation":"ArrayList resizable array-based List है।"},
  {"question":"Java में Thread क्या है?","options":["A) Database connection","B) Lightweight process","C) Variable","D) Method"],"correct":"B) Lightweight process","explanation":"Threads concurrent execution enable करते हैं।"},
  {"question":"void का मतलब?","options":["A) Empty string","B) कोई return value नहीं","C) Null","D) Boolean false"],"correct":"B) कोई return value नहीं","explanation":"void method कुछ return नहीं करती।"},
  {"question":"Java में array क्या है?","options":["A) Variable size collection","B) Fixed size same-type elements","C) Dictionary","D) Set"],"correct":"B) Fixed size same-type elements","explanation":"Arrays fixed size same type elements रखते हैं।"},
],
'malayalam': [
  {"question":"Java entry point?","options":["A) start()","B) main()","C) run()","D) begin()"],"correct":"B) main()","explanation":"public static void main() Java-ന്റെ entry point ആണ്."},
  {"question":"Java-ൽ print ചെയ്യാൻ?","options":["A) print()","B) echo()","C) System.out.println()","D) console.log()"],"correct":"C) System.out.println()","explanation":"System.out.println() Java-ൽ print ചെയ്യുന്നു."},
  {"question":"Object ഉണ്ടാക്കാൻ keyword?","options":["A) create","B) make","C) object","D) new"],"correct":"D) new","explanation":"new Java-ൽ objects ഉണ്ടാക്കുന്നു."},
  {"question":"Inheritance keyword?","options":["A) inherits","B) extends","C) implements","D) super"],"correct":"B) extends","explanation":"extends parent class-ൽ നിന്ന് inherit ചെയ്യുന്നു."},
  {"question":"Exception handling keyword?","options":["A) except","B) handle","C) catch","D) error"],"correct":"C) catch","explanation":"try/catch Java-ൽ exceptions handle ചെയ്യുന്നു."},
  {"question":"Interface keyword?","options":["A) extends","B) implements","C) interface","D) abstract"],"correct":"B) implements","explanation":"implements interface ഉപയോഗിക്കുന്നു."},
  {"question":"Java-ൽ int size?","options":["A) 2 bytes","B) 4 bytes","C) 8 bytes","D) 1 byte"],"correct":"B) 4 bytes","explanation":"int 32-bit (4 bytes) ആണ്."},
  {"question":"Duplicates allow ചെയ്യുന്നത്?","options":["A) Set","B) Map","C) List","D) TreeSet"],"correct":"C) List","explanation":"List duplicates allow ചെയ്യുന്നു."},
  {"question":"static എന്നാൽ?","options":["A) മാറ്റാൻ കഴിയില്ല","B) Class-ന്റേത്, instance-ന്റേതല്ല","C) Private method","D) Final variable"],"correct":"B) Class-ന്റേത്, instance-ന്റേതല്ല","explanation":"static members class-ന്റേതാണ്."},
  {"question":"Constructor എന്നാൽ?","options":["A) Value return ചെയ്യുന്നു","B) Object ഉണ്ടാകുമ്പോൾ call ആകുന്നു","C) Interface method","D) Static method"],"correct":"B) Object ഉണ്ടാകുമ്പോൾ call ആകുന്നു","explanation":"Constructor object initialize ചെയ്യുന്നു."},
  {"question":"Inheritance തടയാൻ keyword?","options":["A) static","B) private","C) final","D) abstract"],"correct":"C) final","explanation":"final class extend ചെയ്യാൻ കഴിയില്ല."},
  {"question":"Polymorphism എന്നാൽ?","options":["A) Multiple classes","B) ഒരു method, പല forms","C) Multiple inheritance","D) Static binding"],"correct":"B) ഒരു method, പല forms","explanation":"Polymorphism = same method, different behaviour."},
  {"question":"Auto-import ആകുന്ന Java package?","options":["A) java.io","B) java.util","C) java.lang","D) java.net"],"correct":"C) java.lang","explanation":"java.lang automatically import ആകുന്നു."},
  {"question":"Java-ൽ 10 % 3?","options":["A) 3","B) 1","C) 0","D) 3.33"],"correct":"B) 1","explanation":"% remainder നൽകുന്നു."},
  {"question":"Encapsulation എന്നാൽ?","options":["A) Loops ഉപയോഗം","B) private + getters/setters ഉപയോഗിച്ച് data മറയ്ക്കൽ","C) Class extend ചെയ്യൽ","D) Method overloading"],"correct":"B) private + getters/setters ഉപയോഗിച്ച് data മറയ്ക്കൽ","explanation":"Encapsulation direct data access തടയുന്നു."},
  {"question":"Abstraction എന്നാൽ?","options":["A) എല്ലാം കാണിക്കൽ","B) Complexity മറച്ച് essentials കാണിക്കൽ","C) Objects ഉണ്ടാക്കൽ","D) Arrays ഉപയോഗം"],"correct":"B) Complexity മറച്ച് essentials കാണിക്കൽ","explanation":"Abstraction complexity മറയ്ക്കുന്നു."},
  {"question":"JVM എന്നാൽ?","options":["A) Java Virtual Memory","B) Java Variable Method","C) Java Virtual Machine","D) Java Version Manager"],"correct":"C) Java Virtual Machine","explanation":"JVM Java bytecode run ചെയ്യുന്നു."},
  {"question":"Java file extension?","options":["A) .py","B) .class","C) .java","D) .cpp"],"correct":"C) .java","explanation":"Java source files .java ഉപയോഗിക്കുന്നു."},
  {"question":"Method overloading എന്നാൽ?","options":["A) ഒരേ പേര്, വ്യത്യസ്ത parameters","B) Parent method override","C) Multiple inheritance","D) Static method"],"correct":"A) ഒരേ പേര്, വ്യത്യസ്ത parameters","explanation":"Overloading = same name, different params."},
  {"question":"public modifier എന്നാൽ?","options":["A) Class-ൽ മാത്രം","B) Package-ൽ മാത്രം","C) എവിടെ നിന്നും accessible","D) Subclasses മാത്രം"],"correct":"C) എവിടെ നിന്നും accessible","explanation":"public എവിടെ നിന്നും accessible ആണ്."},
  {"question":"Java-ൽ String?","options":["A) Primitive type","B) Object/Reference type","C) int subtype","D) char array മാത്രം"],"correct":"B) Object/Reference type","explanation":"String Java-ൽ object ആണ്."},
  {"question":"ArrayList എന്നാൽ?","options":["A) Fixed size array","B) Resizable List implementation","C) Set","D) Map"],"correct":"B) Resizable List implementation","explanation":"ArrayList resizable array-based List ആണ്."},
  {"question":"Java-ൽ Thread?","options":["A) Database connection","B) Lightweight process","C) Variable","D) Method"],"correct":"B) Lightweight process","explanation":"Threads concurrent execution enable ചെയ്യുന്നു."},
  {"question":"void എന്നാൽ?","options":["A) Empty string","B) Return value ഇല്ല","C) Null","D) Boolean false"],"correct":"B) Return value ഇല്ല","explanation":"void method ഒന്നും return ചെയ്യുന്നില്ല."},
  {"question":"Java-ൽ array?","options":["A) Variable size collection","B) Fixed size same-type elements","C) Dictionary","D) Set"],"correct":"B) Fixed size same-type elements","explanation":"Arrays fixed size same type elements hold ചെയ്യുന്നു."},
],
},
'ai': {
'english': [
  {"question":"AI stands for?","options":["A) Automated Interface","B) Artificial Intelligence","C) Automatic Integration","D) Advanced Internet"],"correct":"B) Artificial Intelligence","explanation":"AI = Artificial Intelligence."},
  {"question":"Who coined the term AI?","options":["A) Alan Turing","B) John McCarthy","C) Elon Musk","D) Bill Gates"],"correct":"B) John McCarthy","explanation":"John McCarthy coined AI in 1956."},
  {"question":"AI simulates?","options":["A) Computer programs","B) Human intelligence","C) Hardware","D) Networks"],"correct":"B) Human intelligence","explanation":"AI simulates human intelligence."},
  {"question":"NLP stands for?","options":["A) Network Layer Protocol","B) Natural Language Processing","C) Numeric Learning","D) None"],"correct":"B) Natural Language Processing","explanation":"NLP = Natural Language Processing."},
  {"question":"Computer Vision helps machines?","options":["A) Speak","B) See and interpret images","C) Write code","D) Control hardware"],"correct":"B) See and interpret images","explanation":"Computer Vision enables machines to see."},
  {"question":"Turing Test measures?","options":["A) Internet speed","B) Machine intelligence","C) Programming skill","D) Hardware speed"],"correct":"B) Machine intelligence","explanation":"Turing Test measures machine intelligence."},
  {"question":"ChatGPT is made by?","options":["A) Google","B) Meta","C) OpenAI","D) Microsoft"],"correct":"C) OpenAI","explanation":"ChatGPT was made by OpenAI."},
  {"question":"Narrow AI is designed for?","options":["A) Everything","B) One specific task","C) General reasoning","D) Hardware"],"correct":"B) One specific task","explanation":"Narrow AI handles one specific task."},
  {"question":"Deep Learning uses?","options":["A) Simple rules","B) Layered neural networks","C) SQL","D) Expert systems"],"correct":"B) Layered neural networks","explanation":"Deep Learning uses multiple neural layers."},
  {"question":"BFS explores nodes?","options":["A) Deepest first","B) Level by level","C) Randomly","D) Alphabetically"],"correct":"B) Level by level","explanation":"BFS = Breadth First Search, level by level."},
  {"question":"Expert system uses?","options":["A) Big data","B) Knowledge base and inference engine","C) Only neural networks","D) Cloud"],"correct":"B) Knowledge base and inference engine","explanation":"Expert systems use knowledge bases."},
  {"question":"A* algorithm finds?","options":["A) Longest path","B) Shortest path efficiently","C) All paths","D) Random path"],"correct":"B) Shortest path efficiently","explanation":"A* uses heuristics for shortest path."},
  {"question":"AI ethics covers?","options":["A) Hardware cost","B) Bias, privacy, fairness","C) Processing speed","D) Memory"],"correct":"B) Bias, privacy, fairness","explanation":"AI ethics covers bias, privacy, fairness."},
  {"question":"Reactive AI has?","options":["A) Memory","B) No memory","C) Future prediction","D) Self-awareness"],"correct":"B) No memory","explanation":"Reactive machines have no memory."},
  {"question":"AlphaGo was made by?","options":["A) OpenAI","B) DeepMind","C) IBM","D) Tesla"],"correct":"B) DeepMind","explanation":"AlphaGo was made by Google DeepMind."},
  {"question":"Chatbot uses which AI?","options":["A) Computer Vision","B) NLP","C) Robotics","D) Expert systems only"],"correct":"B) NLP","explanation":"Chatbots use Natural Language Processing."},
  {"question":"AI in healthcare example?","options":["A) ATMs","B) Disease diagnosis from X-rays","C) Traffic lights","D) Pumps"],"correct":"B) Disease diagnosis from X-rays","explanation":"AI detects diseases in medical images."},
  {"question":"Reinforcement learning uses?","options":["A) Labelled data","B) Reward and penalty","C) Clustering","D) Images only"],"correct":"B) Reward and penalty","explanation":"RL uses reward signals."},
  {"question":"Machine translation example?","options":["A) Calculator","B) Google Translate","C) Notepad","D) Alarm"],"correct":"B) Google Translate","explanation":"Google Translate is machine translation."},
  {"question":"Super AI has?","options":["A) No intelligence","B) Self-awareness beyond human","C) Only language skill","D) Only vision"],"correct":"B) Self-awareness beyond human","explanation":"Super AI surpasses human intelligence."},
  {"question":"Knowledge representation helps AI?","options":["A) Store files","B) Reason and make decisions","C) Speed up network","D) Format data"],"correct":"B) Reason and make decisions","explanation":"Knowledge representation enables AI reasoning."},
  {"question":"DFS explores?","options":["A) Level by level","B) Depth first","C) Randomly","D) Alphabetically"],"correct":"B) Depth first","explanation":"DFS = Depth First Search."},
  {"question":"AI recommendation system example?","options":["A) USB drive","B) Netflix suggestions","C) Printer","D) Keyboard"],"correct":"B) Netflix suggestions","explanation":"Netflix uses ML for recommendations."},
  {"question":"General AI can?","options":["A) Only one task","B) Any intellectual task","C) Only vision","D) Only speech"],"correct":"B) Any intellectual task","explanation":"General AI matches human-level reasoning."},
  {"question":"Limited Memory AI uses?","options":["A) No data","B) Past experiences","C) Only current input","D) Future data"],"correct":"B) Past experiences","explanation":"Limited Memory AI uses past data for decisions."},
],
'tamil': [
  {"question":"AI என்றால் என்ன?","options":["A) Automated Interface","B) Artificial Intelligence","C) Automatic Integration","D) Advanced Internet"],"correct":"B) Artificial Intelligence","explanation":"AI = Artificial Intelligence (செயற்கை நுண்ணறிவு)."},
  {"question":"AI என்ற வார்த்தை யார் உருவாக்கினார்?","options":["A) Alan Turing","B) John McCarthy","C) Elon Musk","D) Bill Gates"],"correct":"B) John McCarthy","explanation":"John McCarthy 1956-ல் AI உருவாக்கினார்."},
  {"question":"AI என்ன simulate செய்கிறது?","options":["A) Computer programs","B) Human intelligence","C) Hardware","D) Networks"],"correct":"B) Human intelligence","explanation":"AI human intelligence simulate செய்கிறது."},
  {"question":"NLP என்றால் என்ன?","options":["A) Network Layer Protocol","B) Natural Language Processing","C) Numeric Learning","D) எதுவுமில்லை"],"correct":"B) Natural Language Processing","explanation":"NLP = Natural Language Processing."},
  {"question":"Computer Vision machines-ஐ என்ன செய்ய வைக்கும்?","options":["A) பேச","B) Images பார்க்க மற்றும் interpret செய்ய","C) Code எழுத","D) Hardware control செய்ய"],"correct":"B) Images பார்க்க மற்றும் interpret செய்ய","explanation":"Computer Vision machines-ஐ பார்க்க வைக்கிறது."},
  {"question":"Turing Test என்ன அளவிடுகிறது?","options":["A) Internet வேகம்","B) Machine intelligence","C) Programming skill","D) Hardware வேகம்"],"correct":"B) Machine intelligence","explanation":"Turing Test machine intelligence அளவிடுகிறது."},
  {"question":"ChatGPT-ஐ உருவாக்கியது?","options":["A) Google","B) Meta","C) OpenAI","D) Microsoft"],"correct":"C) OpenAI","explanation":"ChatGPT-ஐ OpenAI உருவாக்கியது."},
  {"question":"Narrow AI எதற்கு?","options":["A) எல்லாவற்றிற்கும்","B) ஒரு குறிப்பிட்ட task-க்கு","C) General reasoning","D) Hardware"],"correct":"B) ஒரு குறிப்பிட்ட task-க்கு","explanation":"Narrow AI ஒரு specific task handle செய்யும்."},
  {"question":"Deep Learning என்ன பயன்படுத்துகிறது?","options":["A) Simple rules","B) Layered neural networks","C) SQL","D) Expert systems"],"correct":"B) Layered neural networks","explanation":"Deep Learning multiple neural layers பயன்படுத்துகிறது."},
  {"question":"BFS nodes-ஐ எப்படி explore செய்யும்?","options":["A) ஆழமான முதலில்","B) Level by level","C) Random-ஆக","D) Alphabetically"],"correct":"B) Level by level","explanation":"BFS level by level explore செய்யும்."},
  {"question":"Expert system என்ன பயன்படுத்துகிறது?","options":["A) Big data","B) Knowledge base மற்றும் inference engine","C) Neural networks மட்டும்","D) Cloud"],"correct":"B) Knowledge base மற்றும் inference engine","explanation":"Expert systems knowledge bases பயன்படுத்துகின்றன."},
  {"question":"A* algorithm என்ன கண்டுபிடிக்கும்?","options":["A) Longest path","B) Shortest path efficiently","C) All paths","D) Random path"],"correct":"B) Shortest path efficiently","explanation":"A* heuristics மூலம் shortest path கண்டுபிடிக்கும்."},
  {"question":"AI ethics என்ன cover செய்கிறது?","options":["A) Hardware cost","B) Bias, privacy, fairness","C) Processing speed","D) Memory"],"correct":"B) Bias, privacy, fairness","explanation":"AI ethics bias, privacy, fairness cover செய்யும்."},
  {"question":"Reactive AI-க்கு என்ன இல்லை?","options":["A) Memory","B) Memory இல்லை","C) Future prediction","D) Self-awareness"],"correct":"B) Memory இல்லை","explanation":"Reactive machines-க்கு memory இல்லை."},
  {"question":"AlphaGo-ஐ உருவாக்கியது?","options":["A) OpenAI","B) DeepMind","C) IBM","D) Tesla"],"correct":"B) DeepMind","explanation":"AlphaGo-ஐ Google DeepMind உருவாக்கியது."},
  {"question":"Chatbot எந்த AI பயன்படுத்துகிறது?","options":["A) Computer Vision","B) NLP","C) Robotics","D) Expert systems மட்டும்"],"correct":"B) NLP","explanation":"Chatbots Natural Language Processing பயன்படுத்துகின்றன."},
  {"question":"Healthcare-ல் AI உதாரணம்?","options":["A) ATMs","B) X-ray-ல் நோய் கண்டுபிடிப்பு","C) Traffic lights","D) Pumps"],"correct":"B) X-ray-ல் நோய் கண்டுபிடிப்பு","explanation":"AI medical images-ல் நோய் கண்டறியும்."},
  {"question":"Reinforcement learning என்ன பயன்படுத்துகிறது?","options":["A) Labelled data","B) Reward மற்றும் penalty","C) Clustering","D) Images மட்டும்"],"correct":"B) Reward மற்றும் penalty","explanation":"RL reward signals பயன்படுத்துகிறது."},
  {"question":"Machine translation உதாரணம்?","options":["A) Calculator","B) Google Translate","C) Notepad","D) Alarm"],"correct":"B) Google Translate","explanation":"Google Translate machine translation system."},
  {"question":"Super AI-க்கு என்ன இருக்கும்?","options":["A) Intelligence இல்லை","B) மனித அளவை தாண்டிய self-awareness","C) Language skill மட்டும்","D) Vision மட்டும்"],"correct":"B) மனித அளவை தாண்டிய self-awareness","explanation":"Super AI மனித intelligence-ஐ தாண்டியது."},
  {"question":"Knowledge representation AI-க்கு என்ன உதவுகிறது?","options":["A) Files சேமிக்க","B) Reason செய்து decisions எடுக்க","C) Network வேகமாக்க","D) Data format செய்ய"],"correct":"B) Reason செய்து decisions எடுக்க","explanation":"Knowledge representation AI reasoning enable செய்யும்."},
  {"question":"DFS எப்படி explore செய்யும்?","options":["A) Level by level","B) ஆழமான முதலில்","C) Random-ஆக","D) Alphabetically"],"correct":"B) ஆழமான முதலில்","explanation":"DFS = Depth First Search."},
  {"question":"AI recommendation system உதாரணம்?","options":["A) USB drive","B) Netflix suggestions","C) Printer","D) Keyboard"],"correct":"B) Netflix suggestions","explanation":"Netflix ML மூலம் recommendations தரும்."},
  {"question":"General AI என்ன செய்யும்?","options":["A) ஒரு task மட்டும்","B) எந்த intellectual task-உம்","C) Vision மட்டும்","D) Speech மட்டும்"],"correct":"B) எந்த intellectual task-உம்","explanation":"General AI மனித நிலை reasoning பெறும்."},
  {"question":"Limited Memory AI என்ன பயன்படுத்துகிறது?","options":["A) Data இல்லை","B) Past experiences","C) Current input மட்டும்","D) Future data"],"correct":"B) Past experiences","explanation":"Limited Memory AI past data பயன்படுத்தி decisions செய்யும்."},
],
'tanglish': [
  {"question":"AI enna?","options":["A) Automated Interface","B) Artificial Intelligence","C) Automatic Integration","D) Advanced Internet"],"correct":"B) Artificial Intelligence","explanation":"AI = Artificial Intelligence."},
  {"question":"AI nu peru vachinathu yaar?","options":["A) Alan Turing","B) John McCarthy","C) Elon Musk","D) Bill Gates"],"correct":"B) John McCarthy","explanation":"John McCarthy 1956-la AI peru vachinaaru."},
  {"question":"AI enna simulate pannum?","options":["A) Computer programs","B) Human intelligence","C) Hardware","D) Networks"],"correct":"B) Human intelligence","explanation":"AI human intelligence simulate pannum."},
  {"question":"NLP enna?","options":["A) Network Layer Protocol","B) Natural Language Processing","C) Numeric Learning","D) Ethuvumilla"],"correct":"B) Natural Language Processing","explanation":"NLP = Natural Language Processing."},
  {"question":"Computer Vision machines-a enna seyyra vaikkum?","options":["A) Pesara","B) Images paarkka-um interpret seyyra","C) Code ezhuda","D) Hardware control seyyra"],"correct":"B) Images paarkka-um interpret seyyra","explanation":"Computer Vision machines-a paarka vaikkum."},
  {"question":"Turing Test enna measure pannum?","options":["A) Internet vegam","B) Machine intelligence","C) Programming skill","D) Hardware vegam"],"correct":"B) Machine intelligence","explanation":"Turing Test machine intelligence measure pannum."},
  {"question":"ChatGPT-a create pannathu?","options":["A) Google","B) Meta","C) OpenAI","D) Microsoft"],"correct":"C) OpenAI","explanation":"ChatGPT-a OpenAI create pannatu."},
  {"question":"Narrow AI endhatharku?","options":["A) Ellaavatharku","B) Oru specific task-ku","C) General reasoning","D) Hardware"],"correct":"B) Oru specific task-ku","explanation":"Narrow AI oru specific task handle pannum."},
  {"question":"Deep Learning enna use pannum?","options":["A) Simple rules","B) Layered neural networks","C) SQL","D) Expert systems"],"correct":"B) Layered neural networks","explanation":"Deep Learning multiple neural layers use pannum."},
  {"question":"BFS nodes-a epdi explore pannum?","options":["A) Aalamana mudhala","B) Level by level","C) Random-a","D) Alphabetically"],"correct":"B) Level by level","explanation":"BFS level by level explore pannum."},
  {"question":"Expert system enna use pannum?","options":["A) Big data","B) Knowledge base-um inference engine-um","C) Neural networks mattum","D) Cloud"],"correct":"B) Knowledge base-um inference engine-um","explanation":"Expert systems knowledge bases use pannum."},
  {"question":"A* algorithm enna kandupidikkum?","options":["A) Longest path","B) Shortest path efficiently","C) All paths","D) Random path"],"correct":"B) Shortest path efficiently","explanation":"A* heuristics use panni shortest path kandupidikkum."},
  {"question":"AI ethics enna cover pannum?","options":["A) Hardware cost","B) Bias, privacy, fairness","C) Processing speed","D) Memory"],"correct":"B) Bias, privacy, fairness","explanation":"AI ethics bias, privacy, fairness cover pannum."},
  {"question":"Reactive AI-ku enna illai?","options":["A) Memory irukku","B) Memory illai","C) Future prediction","D) Self-awareness"],"correct":"B) Memory illai","explanation":"Reactive machines-ku memory illai."},
  {"question":"AlphaGo-a create pannathu?","options":["A) OpenAI","B) DeepMind","C) IBM","D) Tesla"],"correct":"B) DeepMind","explanation":"AlphaGo-a Google DeepMind create pannatu."},
  {"question":"Chatbot ethu AI use pannum?","options":["A) Computer Vision","B) NLP","C) Robotics","D) Expert systems mattum"],"correct":"B) NLP","explanation":"Chatbots Natural Language Processing use pannum."},
  {"question":"Healthcare-la AI example?","options":["A) ATMs","B) X-ray-la noi kandupudippu","C) Traffic lights","D) Pumps"],"correct":"B) X-ray-la noi kandupudippu","explanation":"AI medical images-la noi kandrupidikkum."},
  {"question":"Reinforcement learning enna use pannum?","options":["A) Labelled data","B) Reward-um penalty-um","C) Clustering","D) Images mattum"],"correct":"B) Reward-um penalty-um","explanation":"RL reward signals use pannum."},
  {"question":"Machine translation example?","options":["A) Calculator","B) Google Translate","C) Notepad","D) Alarm"],"correct":"B) Google Translate","explanation":"Google Translate machine translation system."},
  {"question":"Super AI-ku enna irukkum?","options":["A) Intelligence illai","B) Manushana thandiya self-awareness","C) Language skill mattum","D) Vision mattum"],"correct":"B) Manushana thandiya self-awareness","explanation":"Super AI human intelligence-a thandiyathu."},
  {"question":"Knowledge representation AI-ku enna udhavum?","options":["A) Files store seyyra","B) Reason panni decisions edukka","C) Network vegamaakka","D) Data format seyyra"],"correct":"B) Reason panni decisions edukka","explanation":"Knowledge representation AI reasoning enable pannum."},
  {"question":"DFS epdi explore pannum?","options":["A) Level by level","B) Aalamana mudhala","C) Random-a","D) Alphabetically"],"correct":"B) Aalamana mudhala","explanation":"DFS = Depth First Search."},
  {"question":"AI recommendation system example?","options":["A) USB drive","B) Netflix suggestions","C) Printer","D) Keyboard"],"correct":"B) Netflix suggestions","explanation":"Netflix ML use panni recommendations tharum."},
  {"question":"General AI enna seyyum?","options":["A) Oru task mattum","B) Yedha intellectual task-um","C) Vision mattum","D) Speech mattum"],"correct":"B) Yedha intellectual task-um","explanation":"General AI human level reasoning perum."},
  {"question":"Limited Memory AI enna use pannum?","options":["A) Data illai","B) Past experiences","C) Current input mattum","D) Future data"],"correct":"B) Past experiences","explanation":"Limited Memory AI past data use panni decisions pannum."},
],
'hindi': [
  {"question":"AI का मतलब?","options":["A) Automated Interface","B) Artificial Intelligence","C) Automatic Integration","D) Advanced Internet"],"correct":"B) Artificial Intelligence","explanation":"AI = Artificial Intelligence (कृत्रिम बुद्धिमत्ता)."},
  {"question":"AI शब्द किसने बनाया?","options":["A) Alan Turing","B) John McCarthy","C) Elon Musk","D) Bill Gates"],"correct":"B) John McCarthy","explanation":"John McCarthy ने 1956 में AI बनाया।"},
  {"question":"AI क्या simulate करता है?","options":["A) Computer programs","B) Human intelligence","C) Hardware","D) Networks"],"correct":"B) Human intelligence","explanation":"AI human intelligence simulate करता है।"},
  {"question":"NLP का मतलब?","options":["A) Network Layer Protocol","B) Natural Language Processing","C) Numeric Learning","D) कोई नहीं"],"correct":"B) Natural Language Processing","explanation":"NLP = Natural Language Processing."},
  {"question":"Computer Vision मशीनों को क्या करने में मदद करता है?","options":["A) बोलना","B) Images देखना और interpret करना","C) Code लिखना","D) Hardware control"],"correct":"B) Images देखना और interpret करना","explanation":"Computer Vision मशीनों को देखने में सक्षम बनाता है।"},
  {"question":"Turing Test क्या मापता है?","options":["A) Internet speed","B) Machine intelligence","C) Programming skill","D) Hardware speed"],"correct":"B) Machine intelligence","explanation":"Turing Test machine intelligence मापता है।"},
  {"question":"ChatGPT किसने बनाया?","options":["A) Google","B) Meta","C) OpenAI","D) Microsoft"],"correct":"C) OpenAI","explanation":"ChatGPT OpenAI ने बनाया।"},
  {"question":"Narrow AI किसके लिए?","options":["A) सब कुछ","B) एक specific task","C) General reasoning","D) Hardware"],"correct":"B) एक specific task","explanation":"Narrow AI एक specific task handle करता है।"},
  {"question":"Deep Learning क्या उपयोग करता है?","options":["A) Simple rules","B) Layered neural networks","C) SQL","D) Expert systems"],"correct":"B) Layered neural networks","explanation":"Deep Learning multiple neural layers उपयोग करता है।"},
  {"question":"BFS nodes कैसे explore करता है?","options":["A) सबसे गहरे पहले","B) Level by level","C) Randomly","D) Alphabetically"],"correct":"B) Level by level","explanation":"BFS level by level explore करता है।"},
  {"question":"Expert system क्या उपयोग करता है?","options":["A) Big data","B) Knowledge base और inference engine","C) सिर्फ neural networks","D) Cloud"],"correct":"B) Knowledge base और inference engine","explanation":"Expert systems knowledge bases उपयोग करते हैं।"},
  {"question":"A* algorithm क्या ढूंढता है?","options":["A) Longest path","B) Shortest path efficiently","C) All paths","D) Random path"],"correct":"B) Shortest path efficiently","explanation":"A* heuristics से shortest path ढूंढता है।"},
  {"question":"AI ethics में क्या शामिल है?","options":["A) Hardware cost","B) Bias, privacy, fairness","C) Processing speed","D) Memory"],"correct":"B) Bias, privacy, fairness","explanation":"AI ethics में bias, privacy, fairness शामिल हैं।"},
  {"question":"Reactive AI में क्या नहीं है?","options":["A) Memory है","B) Memory नहीं","C) Future prediction","D) Self-awareness"],"correct":"B) Memory नहीं","explanation":"Reactive machines में memory नहीं होती।"},
  {"question":"AlphaGo किसने बनाया?","options":["A) OpenAI","B) DeepMind","C) IBM","D) Tesla"],"correct":"B) DeepMind","explanation":"AlphaGo Google DeepMind ने बनाया।"},
  {"question":"Chatbot कौन सा AI उपयोग करता है?","options":["A) Computer Vision","B) NLP","C) Robotics","D) सिर्फ Expert systems"],"correct":"B) NLP","explanation":"Chatbots Natural Language Processing उपयोग करते हैं।"},
  {"question":"Healthcare में AI उदाहरण?","options":["A) ATMs","B) X-ray से बीमारी पहचान","C) Traffic lights","D) Pumps"],"correct":"B) X-ray से बीमारी पहचान","explanation":"AI medical images में बीमारी पहचानता है।"},
  {"question":"Reinforcement learning क्या उपयोग करता है?","options":["A) Labelled data","B) Reward और penalty","C) Clustering","D) सिर्फ images"],"correct":"B) Reward और penalty","explanation":"RL reward signals उपयोग करता है।"},
  {"question":"Machine translation उदाहरण?","options":["A) Calculator","B) Google Translate","C) Notepad","D) Alarm"],"correct":"B) Google Translate","explanation":"Google Translate machine translation system है।"},
  {"question":"Super AI में क्या है?","options":["A) Intelligence नहीं","B) मानव से परे self-awareness","C) सिर्फ language skill","D) सिर्फ vision"],"correct":"B) मानव से परे self-awareness","explanation":"Super AI मानव intelligence से आगे है।"},
  {"question":"Knowledge representation AI को क्या देता है?","options":["A) Files store करना","B) Reason और decisions लेना","C) Network तेज करना","D) Data format करना"],"correct":"B) Reason और decisions लेना","explanation":"Knowledge representation AI reasoning enable करता है।"},
  {"question":"DFS कैसे explore करता है?","options":["A) Level by level","B) सबसे गहरे पहले","C) Randomly","D) Alphabetically"],"correct":"B) सबसे गहरे पहले","explanation":"DFS = Depth First Search."},
  {"question":"AI recommendation system उदाहरण?","options":["A) USB drive","B) Netflix suggestions","C) Printer","D) Keyboard"],"correct":"B) Netflix suggestions","explanation":"Netflix ML से recommendations देता है।"},
  {"question":"General AI क्या कर सकता है?","options":["A) सिर्फ एक task","B) कोई भी intellectual task","C) सिर्फ vision","D) सिर्फ speech"],"correct":"B) कोई भी intellectual task","explanation":"General AI मानव-स्तरीय reasoning करता है।"},
  {"question":"Limited Memory AI क्या उपयोग करता है?","options":["A) कोई data नहीं","B) Past experiences","C) सिर्फ current input","D) Future data"],"correct":"B) Past experiences","explanation":"Limited Memory AI past data से decisions लेता है।"},
],
'malayalam': [
  {"question":"AI-ന്റെ അർത്ഥം?","options":["A) Automated Interface","B) Artificial Intelligence","C) Automatic Integration","D) Advanced Internet"],"correct":"B) Artificial Intelligence","explanation":"AI = Artificial Intelligence (കൃത്രിമ ബുദ്ധി)."},
  {"question":"AI പദം ആരാണ് ഉണ്ടാക്കിയത്?","options":["A) Alan Turing","B) John McCarthy","C) Elon Musk","D) Bill Gates"],"correct":"B) John McCarthy","explanation":"John McCarthy 1956-ൽ AI ഉണ്ടാക്കി."},
  {"question":"AI എന്ത് simulate ചെയ്യുന്നു?","options":["A) Computer programs","B) Human intelligence","C) Hardware","D) Networks"],"correct":"B) Human intelligence","explanation":"AI human intelligence simulate ചെയ്യുന്നു."},
  {"question":"NLP-ന്റെ അർത്ഥം?","options":["A) Network Layer Protocol","B) Natural Language Processing","C) Numeric Learning","D) ഒന്നുമില്ല"],"correct":"B) Natural Language Processing","explanation":"NLP = Natural Language Processing."},
  {"question":"Computer Vision machines-നെ എന്ത് ചെയ്യാൻ സഹായിക്കുന്നു?","options":["A) സംസാരിക്കാൻ","B) Images കാണാനും interpret ചെയ്യാനും","C) Code എഴുതാൻ","D) Hardware control"],"correct":"B) Images കാണാനും interpret ചെയ്യാനും","explanation":"Computer Vision machines-നെ കാണാൻ പ്രാപ്തരാക്കുന്നു."},
  {"question":"Turing Test എന്ത് അളക്കുന്നു?","options":["A) Internet speed","B) Machine intelligence","C) Programming skill","D) Hardware speed"],"correct":"B) Machine intelligence","explanation":"Turing Test machine intelligence അളക്കുന്നു."},
  {"question":"ChatGPT ഉണ്ടാക്കിയത്?","options":["A) Google","B) Meta","C) OpenAI","D) Microsoft"],"correct":"C) OpenAI","explanation":"ChatGPT OpenAI ഉണ്ടാക്കി."},
  {"question":"Narrow AI ഏതിനായി?","options":["A) എല്ലാം","B) ഒരു specific task","C) General reasoning","D) Hardware"],"correct":"B) ഒരു specific task","explanation":"Narrow AI ഒരു specific task handle ചെയ്യുന്നു."},
  {"question":"Deep Learning എന്ത് ഉപയോഗിക്കുന്നു?","options":["A) Simple rules","B) Layered neural networks","C) SQL","D) Expert systems"],"correct":"B) Layered neural networks","explanation":"Deep Learning multiple neural layers ഉപയോഗിക്കുന്നു."},
  {"question":"BFS nodes എങ്ങനെ explore ചെയ്യുന്നു?","options":["A) ആഴത്തിൽ ആദ്യം","B) Level by level","C) Randomly","D) Alphabetically"],"correct":"B) Level by level","explanation":"BFS level by level explore ചെയ്യുന്നു."},
  {"question":"Expert system എന്ത് ഉപയോഗിക്കുന്നു?","options":["A) Big data","B) Knowledge base-ഉം inference engine-ഉം","C) Neural networks മാത്രം","D) Cloud"],"correct":"B) Knowledge base-ഉം inference engine-ഉം","explanation":"Expert systems knowledge bases ഉപയോഗിക്കുന്നു."},
  {"question":"A* algorithm എന്ത് കണ്ടെത്തുന്നു?","options":["A) ഏറ്റവും നീണ്ട വഴി","B) ഏറ്റവും ചെറിയ വഴി efficiently","C) എല്ലാ വഴികളും","D) Random വഴി"],"correct":"B) ഏറ്റവും ചെറിയ വഴി efficiently","explanation":"A* heuristics ഉപയോഗിച്ച് shortest path കണ്ടെത്തുന്നു."},
  {"question":"AI ethics ഉൾക്കൊള്ളുന്നത്?","options":["A) Hardware cost","B) Bias, privacy, fairness","C) Processing speed","D) Memory"],"correct":"B) Bias, privacy, fairness","explanation":"AI ethics bias, privacy, fairness ഉൾക്കൊള്ളുന്നു."},
  {"question":"Reactive AI-ൽ ഇല്ലാത്തത്?","options":["A) Memory ഉണ്ട്","B) Memory ഇല്ല","C) Future prediction","D) Self-awareness"],"correct":"B) Memory ഇല്ല","explanation":"Reactive machines-ൽ memory ഇല്ല."},
  {"question":"AlphaGo ഉണ്ടാക്കിയത്?","options":["A) OpenAI","B) DeepMind","C) IBM","D) Tesla"],"correct":"B) DeepMind","explanation":"AlphaGo Google DeepMind ഉണ്ടാക്കി."},
  {"question":"Chatbot ഏത് AI ഉപയോഗിക്കുന്നു?","options":["A) Computer Vision","B) NLP","C) Robotics","D) Expert systems മാത്രം"],"correct":"B) NLP","explanation":"Chatbots Natural Language Processing ഉപയോഗിക്കുന്നു."},
  {"question":"Healthcare-ൽ AI ഉദാഹരണം?","options":["A) ATMs","B) X-ray-ൽ രോഗ നിർണ്ണയം","C) Traffic lights","D) Pumps"],"correct":"B) X-ray-ൽ രോഗ നിർണ്ണയം","explanation":"AI medical images-ൽ രോഗം കണ്ടെത്തുന്നു."},
  {"question":"Reinforcement learning എന്ത് ഉപയോഗിക്കുന്നു?","options":["A) Labelled data","B) Reward-ഉം penalty-ഉം","C) Clustering","D) Images മാത്രം"],"correct":"B) Reward-ഉം penalty-ഉം","explanation":"RL reward signals ഉപയോഗിക്കുന്നു."},
  {"question":"Machine translation ഉദാഹരണം?","options":["A) Calculator","B) Google Translate","C) Notepad","D) Alarm"],"correct":"B) Google Translate","explanation":"Google Translate machine translation system ആണ്."},
  {"question":"Super AI-ൽ ഉള്ളത്?","options":["A) Intelligence ഇല്ല","B) മനുഷ്യനെ കടന്ന self-awareness","C) Language skill മാത്രം","D) Vision മാത്രം"],"correct":"B) മനുഷ്യനെ കടന്ന self-awareness","explanation":"Super AI human intelligence കടന്നു."},
  {"question":"Knowledge representation AI-ന് എന്ത് നൽകുന്നു?","options":["A) Files store ചെയ്യൽ","B) Reason ചെയ്ത് decisions എടുക്കൽ","C) Network വേഗത്തിലാക്കൽ","D) Data format ചെയ്യൽ"],"correct":"B) Reason ചെയ്ത് decisions എടുക്കൽ","explanation":"Knowledge representation AI reasoning enable ചെയ്യുന്നു."},
  {"question":"DFS എങ്ങനെ explore ചെയ്യുന്നു?","options":["A) Level by level","B) ആഴത്തിൽ ആദ്യം","C) Randomly","D) Alphabetically"],"correct":"B) ആഴത്തിൽ ആദ്യം","explanation":"DFS = Depth First Search."},
  {"question":"AI recommendation system ഉദാഹരണം?","options":["A) USB drive","B) Netflix suggestions","C) Printer","D) Keyboard"],"correct":"B) Netflix suggestions","explanation":"Netflix ML ഉപയോഗിച്ച് recommendations നൽകുന്നു."},
  {"question":"General AI എന്ത് ചെയ്യും?","options":["A) ഒരു task മാത്രം","B) ഏതൊരു intellectual task-ഉം","C) Vision മാത്രം","D) Speech മാത്രം"],"correct":"B) ഏതൊരു intellectual task-ഉം","explanation":"General AI human level reasoning ചെയ്യും."},
  {"question":"Limited Memory AI എന്ത് ഉപയോഗിക്കുന്നു?","options":["A) Data ഇല്ല","B) Past experiences","C) Current input മാത്രം","D) Future data"],"correct":"B) Past experiences","explanation":"Limited Memory AI past data ഉപയോഗിച്ച് decisions ചെയ്യുന്നു."},
],
},
'ml': {
'english': [
  {"question":"ML stands for?","options":["A) Machine Language","B) Machine Learning","C) Meta Logic","D) Model Learning"],"correct":"B) Machine Learning","explanation":"ML = Machine Learning."},
  {"question":"ML is a subset of?","options":["A) Hardware","B) Networking","C) AI","D) Databases"],"correct":"C) AI","explanation":"ML is a subset of AI."},
  {"question":"Supervised learning needs?","options":["A) No data","B) Labelled data","C) Images only","D) Text only"],"correct":"B) Labelled data","explanation":"Supervised learning uses labelled pairs."},
  {"question":"Which separates classes with hyperplane?","options":["A) K-Means","B) Decision Tree","C) Linear Regression","D) SVM"],"correct":"D) SVM","explanation":"SVM finds optimal separating hyperplane."},
  {"question":"Linear Regression predicts?","options":["A) Category","B) Continuous numeric value","C) Cluster","D) Image"],"correct":"B) Continuous numeric value","explanation":"Linear regression predicts continuous values."},
  {"question":"What is overfitting?","options":["A) Model too simple","B) Memorises training, fails new data","C) No training","D) Too slow"],"correct":"B) Memorises training, fails new data","explanation":"Overfitting = poor generalisation."},
  {"question":"K-Means does?","options":["A) Regression","B) Clustering","C) Classification","D) Dimensionality reduction"],"correct":"B) Clustering","explanation":"K-Means clusters similar data."},
  {"question":"Feature in ML is?","options":["A) Output","B) Input variable","C) Model file","D) Hyperparameter"],"correct":"B) Input variable","explanation":"Features are input variables."},
  {"question":"Accuracy in ML?","options":["A) Model speed","B) Correct predictions %","C) Dataset size","D) Feature count"],"correct":"B) Correct predictions %","explanation":"Accuracy = correct / total × 100."},
  {"question":"Logistic Regression does?","options":["A) Regression","B) Clustering","C) Classification","D) Dimensionality reduction"],"correct":"C) Classification","explanation":"Logistic Regression classifies categories."},
  {"question":"Decision tree splits?","options":["A) All at once","B) At each node based on condition","C) Randomly","D) Alphabetically"],"correct":"B) At each node based on condition","explanation":"Decision trees split data at each node."},
  {"question":"Random Forest is?","options":["A) One large tree","B) Collection of decision trees","C) Neural network","D) Cleaning method"],"correct":"B) Collection of decision trees","explanation":"Random Forest combines many trees."},
  {"question":"Data preprocessing does?","options":["A) Visualise","B) Clean and prepare for training","C) Deploy model","D) Write algorithm"],"correct":"B) Clean and prepare for training","explanation":"Preprocessing handles missing values, scaling."},
  {"question":"Unsupervised learning finds?","options":["A) Labels","B) Patterns in unlabelled data","C) Rules","D) Supervised output"],"correct":"B) Patterns in unlabelled data","explanation":"Unsupervised finds hidden patterns."},
  {"question":"Confusion matrix shows?","options":["A) Model speed","B) TP, FP, TN, FN","C) Training loss","D) Feature importance"],"correct":"B) TP, FP, TN, FN","explanation":"Confusion matrix shows prediction accuracy details."},
  {"question":"Cross-validation is for?","options":["A) Speed","B) Reliable evaluation","C) Cleaning","D) Visualisation"],"correct":"B) Reliable evaluation","explanation":"Cross-validation tests on different subsets."},
  {"question":"scikit-learn is?","options":["A) Web framework","B) ML library for Python","C) Database","D) Frontend tool"],"correct":"B) ML library for Python","explanation":"scikit-learn is a popular Python ML library."},
  {"question":"Gradient descent does?","options":["A) Dataset loading","B) Minimises loss","C) Classification","D) Data cleaning"],"correct":"B) Minimises loss","explanation":"Gradient descent adjusts weights to reduce error."},
  {"question":"Reinforcement ML uses?","options":["A) Labels","B) Reward/penalty","C) Clustering","D) Images"],"correct":"B) Reward/penalty","explanation":"RL uses reward signals to learn."},
  {"question":"Label in ML is?","options":["A) Input feature","B) Correct output in training","C) Model architecture","D) Batch size"],"correct":"B) Correct output in training","explanation":"Labels are correct target outputs."},
  {"question":"PCA stands for?","options":["A) Principal Component Analysis","B) Predictive Classification","C) Pattern Count","D) Primary Clustering"],"correct":"A) Principal Component Analysis","explanation":"PCA reduces dimensionality."},
  {"question":"MSE is used for?","options":["A) Classification","B) Regression evaluation","C) Clustering","D) Feature selection"],"correct":"B) Regression evaluation","explanation":"MSE measures regression prediction error."},
  {"question":"Hyperparameter is?","options":["A) Output","B) Setting before training","C) Input feature","D) Label"],"correct":"B) Setting before training","explanation":"Hyperparameters control learning."},
  {"question":"First step in ML project?","options":["A) Train model","B) Deploy","C) Collect and understand data","D) Evaluate"],"correct":"C) Collect and understand data","explanation":"Every ML project starts with data."},
  {"question":"Neural network is inspired by?","options":["A) Computer circuits","B) Human brain","C) Databases","D) Rule engines"],"correct":"B) Human brain","explanation":"Neural networks model biological neurons."},
],
'tamil': [
  {"question":"ML என்றால் என்ன?","options":["A) Machine Language","B) Machine Learning","C) Meta Logic","D) Model Learning"],"correct":"B) Machine Learning","explanation":"ML = Machine Learning."},
  {"question":"ML எதன் subset?","options":["A) Hardware","B) Networking","C) AI","D) Databases"],"correct":"C) AI","explanation":"ML AI-இன் subset."},
  {"question":"Supervised learning-க்கு என்ன தேவை?","options":["A) Data இல்லை","B) Labelled data","C) Images மட்டும்","D) Text மட்டும்"],"correct":"B) Labelled data","explanation":"Supervised learning labelled pairs பயன்படுத்துகிறது."},
  {"question":"Classes-ஐ hyperplane மூலம் பிரிக்கும் algorithm?","options":["A) K-Means","B) Decision Tree","C) Linear Regression","D) SVM"],"correct":"D) SVM","explanation":"SVM optimal separating hyperplane கண்டுபிடிக்கும்."},
  {"question":"Linear Regression என்ன predict செய்யும்?","options":["A) Category","B) Continuous numeric value","C) Cluster","D) Image"],"correct":"B) Continuous numeric value","explanation":"Linear regression continuous values predict செய்யும்."},
  {"question":"Overfitting என்றால் என்ன?","options":["A) Model மிக simple","B) Training memorize செய்து new data-ல் fail","C) Training இல்லை","D) மிக slow"],"correct":"B) Training memorize செய்து new data-ல் fail","explanation":"Overfitting = poor generalisation."},
  {"question":"K-Means என்ன செய்யும்?","options":["A) Regression","B) Clustering","C) Classification","D) Dimensionality reduction"],"correct":"B) Clustering","explanation":"K-Means similar data cluster செய்யும்."},
  {"question":"ML-ல் feature என்றால் என்ன?","options":["A) Output","B) Input variable","C) Model file","D) Hyperparameter"],"correct":"B) Input variable","explanation":"Features input variables ஆகும்."},
  {"question":"ML-ல் accuracy என்றால் என்ன?","options":["A) Model வேகம்","B) சரியான predictions சதவீதம்","C) Dataset அளவு","D) Feature count"],"correct":"B) சரியான predictions சதவீதம்","explanation":"Accuracy = correct / total × 100."},
  {"question":"Logistic Regression என்ன செய்யும்?","options":["A) Regression","B) Clustering","C) Classification","D) Dimensionality reduction"],"correct":"C) Classification","explanation":"Logistic Regression categories-ல் classify செய்யும்."},
  {"question":"Decision tree எப்படி பிரிக்கும்?","options":["A) ஒரே நேரத்தில்","B) ஒவ்வொரு node-லும் condition-ல்","C) Random-ஆக","D) Alphabetically"],"correct":"B) ஒவ்வொரு node-லும் condition-ல்","explanation":"Decision trees ஒவ்வொரு node-லும் பிரிக்கும்."},
  {"question":"Random Forest என்றால் என்ன?","options":["A) ஒரு பெரிய tree","B) பல decision trees collection","C) Neural network","D) Cleaning method"],"correct":"B) பல decision trees collection","explanation":"Random Forest பல trees combine செய்யும்."},
  {"question":"Data preprocessing என்ன செய்யும்?","options":["A) Visualize","B) Training-க்கு clean மற்றும் prepare","C) Model deploy","D) Algorithm எழுவது"],"correct":"B) Training-க்கு clean மற்றும் prepare","explanation":"Preprocessing missing values, scaling handle செய்யும்."},
  {"question":"Unsupervised learning என்ன கண்டுபிடிக்கும்?","options":["A) Labels","B) Unlabelled data-ல் patterns","C) Rules","D) Supervised output"],"correct":"B) Unlabelled data-ல் patterns","explanation":"Unsupervised hidden patterns கண்டுபிடிக்கும்."},
  {"question":"Confusion matrix என்ன காட்டுகிறது?","options":["A) Model வேகம்","B) TP, FP, TN, FN","C) Training loss","D) Feature importance"],"correct":"B) TP, FP, TN, FN","explanation":"Confusion matrix prediction accuracy காட்டும்."},
  {"question":"Cross-validation எதற்கு?","options":["A) வேகம்","B) Reliable evaluation","C) Cleaning","D) Visualisation"],"correct":"B) Reliable evaluation","explanation":"Cross-validation different subsets-ல் test செய்யும்."},
  {"question":"scikit-learn என்றால் என்ன?","options":["A) Web framework","B) Python ML library","C) Database","D) Frontend tool"],"correct":"B) Python ML library","explanation":"scikit-learn பிரபலமான Python ML library."},
  {"question":"Gradient descent என்ன செய்யும்?","options":["A) Dataset load","B) Loss minimize செய்யும்","C) Classification","D) Data cleaning"],"correct":"B) Loss minimize செய்யும்","explanation":"Gradient descent error குறைக்க weights adjust செய்யும்."},
  {"question":"Reinforcement ML என்ன பயன்படுத்துகிறது?","options":["A) Labels","B) Reward/penalty","C) Clustering","D) Images"],"correct":"B) Reward/penalty","explanation":"RL reward signals மூலம் கற்கும்."},
  {"question":"ML-ல் label என்றால் என்ன?","options":["A) Input feature","B) Training-ல் சரியான output","C) Model architecture","D) Batch size"],"correct":"B) Training-ல் சரியான output","explanation":"Labels correct target outputs ஆகும்."},
  {"question":"PCA என்றால் என்ன?","options":["A) Principal Component Analysis","B) Predictive Classification","C) Pattern Count","D) Primary Clustering"],"correct":"A) Principal Component Analysis","explanation":"PCA dimensionality குறைக்கும்."},
  {"question":"MSE எதற்கு பயன்படுகிறது?","options":["A) Classification","B) Regression evaluation","C) Clustering","D) Feature selection"],"correct":"B) Regression evaluation","explanation":"MSE regression prediction error அளவிடும்."},
  {"question":"Hyperparameter என்றால் என்ன?","options":["A) Output","B) Training முன்பு setting","C) Input feature","D) Label"],"correct":"B) Training முன்பு setting","explanation":"Hyperparameters learning control செய்யும்."},
  {"question":"ML project-ன் முதல் step?","options":["A) Model train","B) Deploy","C) Data collect மற்றும் புரிந்துகொள்ளல்","D) Evaluate"],"correct":"C) Data collect மற்றும் புரிந்துகொள்ளல்","explanation":"எல்லா ML project-உம் data-வில் தொடங்கும்."},
  {"question":"Neural network எதிலிருந்து inspired?","options":["A) Computer circuits","B) Human brain","C) Databases","D) Rule engines"],"correct":"B) Human brain","explanation":"Neural networks biological neurons model செய்யும்."},
],
'tanglish': [
  {"question":"ML enna?","options":["A) Machine Language","B) Machine Learning","C) Meta Logic","D) Model Learning"],"correct":"B) Machine Learning","explanation":"ML = Machine Learning."},
  {"question":"ML etho subset?","options":["A) Hardware","B) Networking","C) AI","D) Databases"],"correct":"C) AI","explanation":"ML AI-oda subset."},
  {"question":"Supervised learning-ku enna vennum?","options":["A) Data vendam","B) Labelled data","C) Images mattum","D) Text mattum"],"correct":"B) Labelled data","explanation":"Supervised learning labelled pairs use pannum."},
  {"question":"Classes-a hyperplane-la piraikka ethu algorithm?","options":["A) K-Means","B) Decision Tree","C) Linear Regression","D) SVM"],"correct":"D) SVM","explanation":"SVM optimal separating hyperplane kandupidikkum."},
  {"question":"Linear Regression enna predict pannum?","options":["A) Category","B) Continuous numeric value","C) Cluster","D) Image"],"correct":"B) Continuous numeric value","explanation":"Linear regression continuous values predict pannum."},
  {"question":"Overfitting enna?","options":["A) Model romba simple","B) Training memorize panni new data-la fail","C) Training illai","D) Romba slow"],"correct":"B) Training memorize panni new data-la fail","explanation":"Overfitting = poor generalisation."},
  {"question":"K-Means enna pannum?","options":["A) Regression","B) Clustering","C) Classification","D) Dimensionality reduction"],"correct":"B) Clustering","explanation":"K-Means similar data cluster pannum."},
  {"question":"ML-la feature enna?","options":["A) Output","B) Input variable","C) Model file","D) Hyperparameter"],"correct":"B) Input variable","explanation":"Features input variables aagum."},
  {"question":"ML-la accuracy enna?","options":["A) Model vegam","B) Correct predictions percentage","C) Dataset size","D) Feature count"],"correct":"B) Correct predictions percentage","explanation":"Accuracy = correct / total × 100."},
  {"question":"Logistic Regression enna pannum?","options":["A) Regression","B) Clustering","C) Classification","D) Dimensionality reduction"],"correct":"C) Classification","explanation":"Logistic Regression categories-la classify pannum."},
  {"question":"Decision tree epdi pirikum?","options":["A) Ore neratthil","B) Oru node-lum condition-la","C) Random-a","D) Alphabetically"],"correct":"B) Oru node-lum condition-la","explanation":"Decision trees oru node-lum data pirikum."},
  {"question":"Random Forest enna?","options":["A) Oru periya tree","B) Pala decision trees collection","C) Neural network","D) Cleaning method"],"correct":"B) Pala decision trees collection","explanation":"Random Forest pala trees combine pannum."},
  {"question":"Data preprocessing enna pannum?","options":["A) Visualize","B) Training-ku clean-um prepare-um","C) Model deploy","D) Algorithm ezhuthuvathu"],"correct":"B) Training-ku clean-um prepare-um","explanation":"Preprocessing missing values, scaling handle pannum."},
  {"question":"Unsupervised learning enna kandupidikkum?","options":["A) Labels","B) Unlabelled data-la patterns","C) Rules","D) Supervised output"],"correct":"B) Unlabelled data-la patterns","explanation":"Unsupervised hidden patterns kandupidikkum."},
  {"question":"Confusion matrix enna kaattum?","options":["A) Model vegam","B) TP, FP, TN, FN","C) Training loss","D) Feature importance"],"correct":"B) TP, FP, TN, FN","explanation":"Confusion matrix prediction accuracy kaattum."},
  {"question":"Cross-validation endhatharku?","options":["A) Vegam","B) Reliable evaluation","C) Cleaning","D) Visualisation"],"correct":"B) Reliable evaluation","explanation":"Cross-validation different subsets-la test pannum."},
  {"question":"scikit-learn enna?","options":["A) Web framework","B) Python ML library","C) Database","D) Frontend tool"],"correct":"B) Python ML library","explanation":"scikit-learn famous Python ML library."},
  {"question":"Gradient descent enna pannum?","options":["A) Dataset load","B) Loss minimize pannum","C) Classification","D) Data cleaning"],"correct":"B) Loss minimize pannum","explanation":"Gradient descent error kuraikka weights adjust pannum."},
  {"question":"Reinforcement ML enna use pannum?","options":["A) Labels","B) Reward/penalty","C) Clustering","D) Images"],"correct":"B) Reward/penalty","explanation":"RL reward signals use panni kallukum."},
  {"question":"ML-la label enna?","options":["A) Input feature","B) Training-la correct output","C) Model architecture","D) Batch size"],"correct":"B) Training-la correct output","explanation":"Labels correct target outputs aagum."},
  {"question":"PCA enna?","options":["A) Principal Component Analysis","B) Predictive Classification","C) Pattern Count","D) Primary Clustering"],"correct":"A) Principal Component Analysis","explanation":"PCA dimensionality kuraikum."},
  {"question":"MSE endhatharku use aagum?","options":["A) Classification","B) Regression evaluation","C) Clustering","D) Feature selection"],"correct":"B) Regression evaluation","explanation":"MSE regression prediction error alaveedum."},
  {"question":"Hyperparameter enna?","options":["A) Output","B) Training munnadi setting","C) Input feature","D) Label"],"correct":"B) Training munnadi setting","explanation":"Hyperparameters learning control pannum."},
  {"question":"ML project-oda first step?","options":["A) Model train","B) Deploy","C) Data collect-um purinjukolluvathu-um","D) Evaluate"],"correct":"C) Data collect-um purinjukolluvathu-um","explanation":"Ella ML project-um data-la thodangum."},
  {"question":"Neural network engirundhu inspired?","options":["A) Computer circuits","B) Human brain","C) Databases","D) Rule engines"],"correct":"B) Human brain","explanation":"Neural networks biological neurons model pannum."},
],
'hindi': [
  {"question":"ML का मतलब?","options":["A) Machine Language","B) Machine Learning","C) Meta Logic","D) Model Learning"],"correct":"B) Machine Learning","explanation":"ML = Machine Learning."},
  {"question":"ML किसका subset?","options":["A) Hardware","B) Networking","C) AI","D) Databases"],"correct":"C) AI","explanation":"ML AI का subset है।"},
  {"question":"Supervised learning के लिए क्या चाहिए?","options":["A) कोई data नहीं","B) Labelled data","C) सिर्फ images","D) सिर्फ text"],"correct":"B) Labelled data","explanation":"Supervised learning labelled pairs उपयोग करता है।"},
  {"question":"Classes को hyperplane से अलग करता है?","options":["A) K-Means","B) Decision Tree","C) Linear Regression","D) SVM"],"correct":"D) SVM","explanation":"SVM optimal separating hyperplane ढूंढता है।"},
  {"question":"Linear Regression क्या predict करता है?","options":["A) Category","B) Continuous numeric value","C) Cluster","D) Image"],"correct":"B) Continuous numeric value","explanation":"Linear regression continuous values predict करता है।"},
  {"question":"Overfitting क्या है?","options":["A) Model बहुत simple","B) Training याद करके new data पर fail","C) Training नहीं","D) बहुत slow"],"correct":"B) Training याद करके new data पर fail","explanation":"Overfitting = poor generalisation."},
  {"question":"K-Means क्या करता है?","options":["A) Regression","B) Clustering","C) Classification","D) Dimensionality reduction"],"correct":"B) Clustering","explanation":"K-Means similar data cluster करता है।"},
  {"question":"ML में feature क्या है?","options":["A) Output","B) Input variable","C) Model file","D) Hyperparameter"],"correct":"B) Input variable","explanation":"Features input variables हैं।"},
  {"question":"ML में accuracy क्या है?","options":["A) Model speed","B) सही predictions का प्रतिशत","C) Dataset size","D) Feature count"],"correct":"B) सही predictions का प्रतिशत","explanation":"Accuracy = correct / total × 100."},
  {"question":"Logistic Regression क्या करता है?","options":["A) Regression","B) Clustering","C) Classification","D) Dimensionality reduction"],"correct":"C) Classification","explanation":"Logistic Regression categories classify करता है।"},
  {"question":"Decision tree कैसे split करता है?","options":["A) एक साथ","B) हर node पर condition से","C) Randomly","D) Alphabetically"],"correct":"B) हर node पर condition से","explanation":"Decision trees हर node पर data split करते हैं।"},
  {"question":"Random Forest क्या है?","options":["A) एक बड़ा tree","B) कई decision trees का collection","C) Neural network","D) Cleaning method"],"correct":"B) कई decision trees का collection","explanation":"Random Forest कई trees combine करता है।"},
  {"question":"Data preprocessing क्या करता है?","options":["A) Visualize","B) Training के लिए clean और prepare","C) Model deploy","D) Algorithm लिखना"],"correct":"B) Training के लिए clean और prepare","explanation":"Preprocessing missing values, scaling handle करता है।"},
  {"question":"Unsupervised learning क्या ढूंढता है?","options":["A) Labels","B) Unlabelled data में patterns","C) Rules","D) Supervised output"],"correct":"B) Unlabelled data में patterns","explanation":"Unsupervised hidden patterns ढूंढता है।"},
  {"question":"Confusion matrix क्या दिखाता है?","options":["A) Model speed","B) TP, FP, TN, FN","C) Training loss","D) Feature importance"],"correct":"B) TP, FP, TN, FN","explanation":"Confusion matrix prediction accuracy दिखाता है।"},
  {"question":"Cross-validation किसके लिए?","options":["A) Speed","B) Reliable evaluation","C) Cleaning","D) Visualisation"],"correct":"B) Reliable evaluation","explanation":"Cross-validation different subsets पर test करता है।"},
  {"question":"scikit-learn क्या है?","options":["A) Web framework","B) Python ML library","C) Database","D) Frontend tool"],"correct":"B) Python ML library","explanation":"scikit-learn popular Python ML library है।"},
  {"question":"Gradient descent क्या करता है?","options":["A) Dataset load","B) Loss minimize करता है","C) Classification","D) Data cleaning"],"correct":"B) Loss minimize करता है","explanation":"Gradient descent error कम करने के लिए weights adjust करता है।"},
  {"question":"Reinforcement ML क्या उपयोग करता है?","options":["A) Labels","B) Reward/penalty","C) Clustering","D) Images"],"correct":"B) Reward/penalty","explanation":"RL reward signals से सीखता है।"},
  {"question":"ML में label क्या है?","options":["A) Input feature","B) Training में सही output","C) Model architecture","D) Batch size"],"correct":"B) Training में सही output","explanation":"Labels correct target outputs हैं।"},
  {"question":"PCA का मतलब?","options":["A) Principal Component Analysis","B) Predictive Classification","C) Pattern Count","D) Primary Clustering"],"correct":"A) Principal Component Analysis","explanation":"PCA dimensionality कम करता है।"},
  {"question":"MSE किसके लिए?","options":["A) Classification","B) Regression evaluation","C) Clustering","D) Feature selection"],"correct":"B) Regression evaluation","explanation":"MSE regression prediction error मापता है।"},
  {"question":"Hyperparameter क्या है?","options":["A) Output","B) Training से पहले setting","C) Input feature","D) Label"],"correct":"B) Training से पहले setting","explanation":"Hyperparameters learning control करते हैं।"},
  {"question":"ML project का पहला step?","options":["A) Model train","B) Deploy","C) Data collect और समझना","D) Evaluate"],"correct":"C) Data collect और समझना","explanation":"हर ML project data से शुरू होता है।"},
  {"question":"Neural network किससे inspired?","options":["A) Computer circuits","B) Human brain","C) Databases","D) Rule engines"],"correct":"B) Human brain","explanation":"Neural networks biological neurons model करते हैं।"},
],
'malayalam': [
{"question":"ML എന്നത് എന്താണ്?","options":["A) മെഷീൻ ലാംഗ്വേജ്","B) മെഷീൻ ലേണിംഗ്","C) മെറ്റ ലോജിക്","D) മോഡൽ ലേണിംഗ്"],"correct":"B) മെഷീൻ ലേണിംഗ്","explanation":"ML = മെഷീൻ ലേണിംഗ്."},
{"question":"ML എന്തിന്റെ ഉപവിഭാഗമാണ്?","options":["A) ഹാർഡ്‌വെയർ","B) നെറ്റ്വർക്കിംഗ്","C) AI","D) ഡാറ്റാബേസുകൾ"],"correct":"C) AI","explanation":"ML, AI-യുടെ ഉപവിഭാഗമാണ്."},
{"question":"Supervised learning എന്ത് ആവശ്യമാണ്?","options":["A) ഡാറ്റ ഇല്ല","B) ലേബൽ ചെയ്ത ഡാറ്റ","C) ചിത്രങ്ങൾ മാത്രം","D) ടെക്സ്റ്റ് മാത്രം"],"correct":"B) ലേബൽ ചെയ്ത ഡാറ്റ","explanation":"Supervised learning ലേബൽ ചെയ്ത ഡാറ്റ ഉപയോഗിക്കുന്നു."},
{"question":"Hyperplane ഉപയോഗിച്ച് ക്ലാസുകൾ വേർതിരിക്കുന്നത് ഏത്?","options":["A) K-Means","B) Decision Tree","C) Linear Regression","D) SVM"],"correct":"D) SVM","explanation":"SVM മികച്ച hyperplane കണ്ടെത്തുന്നു."},
{"question":"Linear Regression എന്ത് പ്രവചിക്കുന്നു?","options":["A) വർഗ്ഗം","B) തുടർച്ചയായ സംഖ്യാ മൂല്യം","C) ക്ലസ്റ്റർ","D) ചിത്രം"],"correct":"B) തുടർച്ചയായ സംഖ്യാ മൂല്യം","explanation":"Linear Regression തുടർച്ചയായ മൂല്യങ്ങൾ പ്രവചിക്കുന്നു."},
{"question":"Overfitting എന്താണ്?","options":["A) മോഡൽ വളരെ ലളിതം","B) ട്രെയിനിംഗ് ഡാറ്റ ഓർത്ത് പുതിയ ഡാറ്റയിൽ പരാജയപ്പെടുന്നു","C) ട്രെയിനിംഗ് ഇല്ല","D) വളരെ മന്ദഗതി"],"correct":"B) ട്രെയിനിംഗ് ഡാറ്റ ഓർത്ത് പുതിയ ഡാറ്റയിൽ പരാജയപ്പെടുന്നു","explanation":"Overfitting = പുതിയ ഡാറ്റയിൽ മോശം പ്രകടനം."},
{"question":"K-Means എന്ത് ചെയ്യുന്നു?","options":["A) Regression","B) Clustering","C) Classification","D) Dimensionality reduction"],"correct":"B) Clustering","explanation":"K-Means സമാന ഡാറ്റ ഗ്രൂപ്പുകളാക്കുന്നു."},
{"question":"ML-ൽ Feature എന്നത് എന്താണ്?","options":["A) ഔട്ട്പുട്ട്","B) ഇൻപുട്ട് വേരിയബിൾ","C) മോഡൽ ഫയൽ","D) ഹൈപ്പർപരാമീറ്റർ"],"correct":"B) ഇൻപുട്ട് വേരിയബിൾ","explanation":"Features ഇൻപുട്ട് വേരിയബിളുകളാണ്."},
{"question":"ML-ൽ Accuracy എന്താണ്?","options":["A) മോഡൽ വേഗം","B) ശരിയായ പ്രവചനങ്ങളുടെ ശതമാനം","C) ഡാറ്റാസെറ്റ് വലിപ്പം","D) ഫീച്ചറുകളുടെ എണ്ണം"],"correct":"B) ശരിയായ പ്രവചനങ്ങളുടെ ശതമാനം","explanation":"Accuracy = ശരിയായ പ്രവചനങ്ങൾ / ആകെ × 100."},
{"question":"Logistic Regression എന്ത് ചെയ്യുന്നു?","options":["A) Regression","B) Clustering","C) Classification","D) Dimensionality reduction"],"correct":"C) Classification","explanation":"Logistic Regression വർഗ്ഗീകരണം നടത്തുന്നു."},
{"question":"Decision Tree എങ്ങനെ വിഭജിക്കുന്നു?","options":["A) ഒരുമിച്ച്","B) ഓരോ നോഡിലും നിബന്ധന അടിസ്ഥാനത്തിൽ","C) യാദൃശ്ചികമായി","D) അക്ഷരമാലാക്രമത്തിൽ"],"correct":"B) ഓരോ നോഡിലും നിബന്ധന അടിസ്ഥാനത്തിൽ","explanation":"Decision Tree ഓരോ നോഡിലും ഡാറ്റ വിഭജിക്കുന്നു."},
{"question":"Random Forest എന്താണ്?","options":["A) ഒരു വലിയ ട്രീ","B) പല Decision Tree-കളുടെ കൂട്ടം","C) Neural Network","D) Cleaning method"],"correct":"B) പല Decision Tree-കളുടെ കൂട്ടം","explanation":"Random Forest പല ട്രീകളെ കൂട്ടിച്ചേർക്കുന്നു."},
{"question":"Data preprocessing എന്ത് ചെയ്യുന്നു?","options":["A) Visualise","B) ട്രെയിനിംഗിന് ഡാറ്റ ശുദ്ധീകരിക്കുകയും തയ്യാറാക്കുകയും ചെയ്യുന്നു","C) മോഡൽ deploy ചെയ്യുക","D) ആൽഗോരിതം എഴുതുക"],"correct":"B) ട്രെയിനിംഗിന് ഡാറ്റ ശുദ്ധീകരിക്കുകയും തയ്യാറാക്കുകയും ചെയ്യുന്നു","explanation":"Preprocessing missing values, scaling എന്നിവ കൈകാര്യം ചെയ്യുന്നു."},
{"question":"Unsupervised learning എന്ത് കണ്ടെത്തുന്നു?","options":["A) ലേബലുകൾ","B) ലേബൽ ഇല്ലാത്ത ഡാറ്റയിൽ pattern-കൾ","C) നിയമങ്ങൾ","D) supervised output"],"correct":"B) ലേബൽ ഇല്ലാത്ത ഡാറ്റയിൽ pattern-കൾ","explanation":"Unsupervised learning മറഞ്ഞിരിക്കുന്ന pattern-കൾ കണ്ടെത്തുന്നു."},
{"question":"Confusion matrix എന്ത് കാണിക്കുന്നു?","options":["A) മോഡൽ വേഗം","B) TP, FP, TN, FN","C) ട്രെയിനിംഗ് loss","D) feature importance"],"correct":"B) TP, FP, TN, FN","explanation":"Confusion matrix പ്രവചനങ്ങളുടെ വിശദാംശങ്ങൾ കാണിക്കുന്നു."},
{"question":"Cross-validation എന്തിനാണ്?","options":["A) വേഗം","B) വിശ്വസനീയമായ മൂല്യനിർണ്ണയം","C) Cleaning","D) Visualisation"],"correct":"B) വിശ്വസനീയമായ മൂല്യനിർണ്ണയം","explanation":"Cross-validation വിവിധ subset-കളിൽ പരിശോധിക്കുന്നു."},
{"question":"scikit-learn എന്താണ്?","options":["A) Web framework","B) Python-നുള്ള ML ലൈബ്രറി","C) Database","D) Frontend tool"],"correct":"B) Python-നുള്ള ML ലൈബ്രറി","explanation":"scikit-learn ഒരു പ്രശസ്ത Python ML ലൈബ്രറിയാണ്."},
{"question":"Gradient descent എന്ത് ചെയ്യുന്നു?","options":["A) Dataset loading","B) Loss കുറയ്ക്കുന്നു","C) Classification","D) Data cleaning"],"correct":"B) Loss കുറയ്ക്കുന്നു","explanation":"Gradient descent error കുറയ്ക്കാൻ weights ക്രമീകരിക്കുന്നു."},
{"question":"Reinforcement ML എന്ത് ഉപയോഗിക്കുന്നു?","options":["A) Labels","B) Reward/penalty","C) Clustering","D) Images"],"correct":"B) Reward/penalty","explanation":"RL reward signals ഉപയോഗിക്കുന്നു."},
{"question":"ML-ൽ Label എന്താണ്?","options":["A) Input feature","B) ശരിയായ output","C) Model architecture","D) Batch size"],"correct":"B) ശരിയായ output","explanation":"Label-കൾ ശരിയായ target output ആണ്."},
{"question":"PCA എന്നത് എന്താണ്?","options":["A) Principal Component Analysis","B) Predictive Classification","C) Pattern Count","D) Primary Clustering"],"correct":"A) Principal Component Analysis","explanation":"PCA dimensionality കുറയ്ക്കാൻ ഉപയോഗിക്കുന്നു."},
{"question":"MSE എന്തിനാണ് ഉപയോഗിക്കുന്നത്?","options":["A) Classification","B) Regression evaluation","C) Clustering","D) Feature selection"],"correct":"B) Regression evaluation","explanation":"MSE regression error അളക്കുന്നു."},
{"question":"Hyperparameter എന്താണ്?","options":["A) Output","B) ട്രെയിനിംഗിന് മുൻപ് നിശ്ചയിക്കുന്ന setting","C) Input feature","D) Label"],"correct":"B) ട്രെയിനിംഗിന് മുൻപ് നിശ്ചയിക്കുന്ന setting","explanation":"Hyperparameters learning നിയന്ത്രിക്കുന്നു."},
{"question":"ML project-ലെ ആദ്യ ഘട്ടം?","options":["A) Train model","B) Deploy","C) ഡാറ്റ ശേഖരിക്കുകയും മനസ്സിലാക്കുകയും ചെയ്യുക","D) Evaluate"],"correct":"C) ഡാറ്റ ശേഖരിക്കുകയും മനസ്സിലാക്കുകയും ചെയ്യുക","explanation":"എല്ലാ ML project-ഉം ഡാറ്റയിൽ നിന്ന് തുടങ്ങുന്നു."},
{"question":"Neural network എന്തിൽ നിന്ന് പ്രചോദനം നേടിയതാണ്?","options":["A) കമ്പ്യൂട്ടർ സർക്ക്യൂട്ടുകൾ","B) മനുഷ്യ മസ്തിഷ്കം","C) ഡാറ്റാബേസുകൾ","D) rule engines"],"correct":"B) മനുഷ്യ മസ്തിഷ്കം","explanation":"Neural network മനുഷ്യ നാഡീവ്യൂഹത്തിൽ നിന്ന് പ്രചോദനം നേടുന്നു."}]

}}




# ─────────────────────────────────────────
# Pick Helpers
# ─────────────────────────────────────────
def pick_topic_q(prog_lang, topic_name, iface, n=10):
  lang_map = TOPIC_Q.get(prog_lang, {}).get(topic_name, {})
  pool = lang_map.get(iface) or lang_map.get('english') or []
  if not pool:
    pool = generic_questions(topic_name, prog_lang, 12)
  qs = [dict(q) for q in pool]
  random.shuffle(qs)
  for i, q in enumerate(qs[:n]):
    q['id'] = i + 1
  return qs[:n]


def pick_course_q(prog_lang, iface, n=20):
  lang_map = COURSE_Q.get(prog_lang, {})
  pool = lang_map.get(iface) or lang_map.get('english') or []
  if not pool:
    pool = generic_questions(prog_lang, prog_lang, 25)
  qs = [dict(q) for q in pool]
  random.shuffle(qs)
  for i, q in enumerate(qs[:n]):
    q['id'] = i + 1
  return qs[:n]
def update_leaderboard(user, prog_lang):
  topic_attempts = TopicTestAttempt.objects.filter(
      user=user, programming_language=prog_lang, passed=True
)
  total_topic_score = sum(a.score for a in topic_attempts)
  topics_done = topic_attempts.values('topic_id').distinct().count()
  LeaderboardEntry.objects.update_or_create(
      user=user, programming_language=prog_lang,
      defaults={
          'total_score': total_topic_score,
          'topics_completed': topics_done,
          'course_test_score': 0,
    }
)


# ─────────────────────────────────────────
# API Views
# ─────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_topic_test(request):
  topic_id = request.query_params.get('topic_id')
  iface    = request.query_params.get('interface_language', 'english')
  try:
    topic = Topic.objects.get(id=topic_id)
  except Topic.DoesNotExist:
    return Response({'error': 'Topic not found.'}, status=404)
  questions = pick_topic_q(topic.programming_language, topic.name, iface)
  return Response({
'questions': questions,
'topic_id': topic.id,
'topic_name': topic.name,
'language': topic.programming_language,
'total': len(questions),
'pass_mark': 7,
})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_topic_test(request):
    topic_id     = request.data.get('topic_id')
    user_answers = request.data.get('answers', {})
    questions    = request.data.get('questions', [])
    iface        = request.data.get('interface_language', 'english')

    try:
        topic = Topic.objects.get(id=topic_id)
    except Topic.DoesNotExist:
        return Response({'error': 'Topic not found.'}, status=404)

    score = 0
    results = []
    for q in questions:
        # Normalize question id — always compare as string
        qid = str(q.get('id', ''))
        # Try both string and int key
        user_ans = user_answers.get(qid) or user_answers.get(int(qid) if qid.isdigit() else qid) or ''
        correct  = q.get('correct', '').strip()
        is_ok    = user_ans.strip() == correct

        if is_ok:
            score += 1

        results.append({
            'id':             q.get('id'),
            'question':       q.get('question', ''),
            'your_answer':    user_ans,
            'correct_answer': correct,
            'is_correct':     is_ok,
            'explanation':    q.get('explanation', ''),
        })

    passed  = score >= 7
    is_weak = not passed

    attempt = TopicTestAttempt.objects.create(
        user=request.user,
        topic_id=topic.id,
        topic_name=topic.name,
        programming_language=topic.programming_language,
        score=score,
        total_questions=10,
        passed=passed,
        is_weak=is_weak,
        interface_language=iface,
    )

    if passed:
        progress, _ = UserProgress.objects.get_or_create(user=request.user, topic=topic)
        progress.completed = True
        progress.completed_at = timezone.now()
        progress.save()
        update_leaderboard(request.user, topic.programming_language)

    return Response({
        'score':      score,
        'total':      10,
        'passed':     passed,
        'is_weak':    is_weak,
        'attempt_id': attempt.id,
        'results':    results,
        'message': (
            f'✅ Excellent! You scored {score}/10 — Topic passed! Next topic unlocked.'
            if passed else
            f'⚠️ You scored {score}/10 (need 7/10). This is a weak topic — review the lesson and try again!'
        ),
    })
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generate_course_test(request):
    lang = request.query_params.get('language', 'python')
    iface = request.query_params.get('interface_language', 'english')
    topics = Topic.objects.filter(programming_language=lang)
    for topic in topics:
        passed = TopicTestAttempt.objects.filter(
            user=request.user, topic_id=topic.id, passed=True
        ).exists()
        if not passed:
            return Response({
                'error': f'Pass all topic tests first. "{topic.name}" is not yet passed.',
                'locked': True,
            }, status=403)

    questions = pick_course_q(lang, iface)
    return Response({
        'questions': questions,
        'language': lang,
        'total': len(questions),
        'pass_mark': 17,
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_course_test(request):
    lang         = request.data.get('language', 'python')
    iface        = request.data.get('interface_language', 'english')
    paired       = request.data.get('paired', [])   # new reliable format
    questions    = request.data.get('questions', [])
    user_answers = request.data.get('answers', {})

    score   = 0
    results = []

    # ── Method 1: use paired array (most reliable) ──────────────
    if paired:
        for item in paired:
            selected = (item.get('selected') or '').strip()
            correct  = (item.get('correct') or '').strip()
            is_ok    = (selected == correct) and (selected != '')
            if is_ok:
                score += 1
            results.append({
                'id':             item.get('question_id'),
                'question':       item.get('question', ''),
                'your_answer':    selected,
                'correct_answer': correct,
                'is_correct':     is_ok,
                'explanation':    item.get('explanation', ''),
            })

    # ── Method 2: legacy fallback — match by any key variant ────
    else:
        for idx, q in enumerate(questions):
            correct = (q.get('correct') or '').strip()
            # try every possible key the frontend might send
            qid_str  = str(q.get('id', idx + 1))
            qid_int  = int(qid_str) if qid_str.isdigit() else idx + 1
            qid_idx  = str(idx + 1)  # 1-based index as string

            user_ans = (
                user_answers.get(qid_str) or
                user_answers.get(qid_int) or
                user_answers.get(qid_idx) or
                user_answers.get(str(idx)) or
                ''
            ).strip()

            is_ok = (user_ans == correct) and (user_ans != '')
            if is_ok:
                score += 1

            results.append({
                'id':             q.get('id'),
                'question':       q.get('question', ''),
                'your_answer':    user_ans,
                'correct_answer': correct,
                'is_correct':     is_ok,
                'explanation':    q.get('explanation', ''),
            })

    passed  = score >= 17
    attempt = CourseTestAttempt.objects.create(
        user=request.user,
        programming_language=lang,
        score=score,
        total_questions=len(results),
        passed=passed,
        interface_language=iface,
    )

    cert_generated = False
    cert_id        = None
    pdf_url        = None
    email_sent     = False

    if passed:
        from certificates.models import Certificate
        from certificates.utils import generate_certificate_pdf
        from django.core.mail import EmailMessage
        from django.conf import settings
        import uuid
        from datetime import datetime

        existing = Certificate.objects.filter(
            user=request.user, programming_language=lang
        ).first()

        if not existing:
            cert_id_str = str(uuid.uuid4())[:12].upper()
            issued_date = datetime.now().strftime('%d %B %Y')
            user_name   = request.user.full_name or request.user.username

            filepath, relative_path = generate_certificate_pdf(
                user_name=user_name,
                language=lang,
                score=score,
                certificate_id=cert_id_str,
                issued_date=issued_date,
            )
            cert = Certificate.objects.create(
                user=request.user,
                programming_language=lang,
                score=score,
                certificate_id=cert_id_str,
                pdf_path=relative_path,
            )
            try:
                email = EmailMessage(
                    subject=f'🎓 Your CodeMentor Certificate — {lang.upper()}',
                    body=f"""Dear {user_name},

Congratulations! You have successfully completed the {lang.upper()} course on CodeMentor.

Your Score : {score}/20
Certificate ID : {cert_id_str}
Date Issued : {issued_date}

Please find your certificate attached to this email.

Keep learning!
— CodeMentor Team""",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[request.user.email],
                )
                email.attach_file(filepath)
                email.send()
                cert.email_sent = True
                cert.save()
                email_sent = True
            except Exception as e:
                print(f'Email error: {e}')

            cert_generated = True
            cert_id        = cert_id_str
            pdf_url        = f"{settings.MEDIA_URL}{relative_path}"
        else:
            cert_generated = True
            cert_id        = existing.certificate_id
            pdf_url        = f"{settings.MEDIA_URL}{existing.pdf_path}"
            email_sent     = existing.email_sent

    return Response({
        'score':          score,
        'total':          len(results),
        'passed':         passed,
        'attempt_id':     attempt.id,
        'results':        results,
        'cert_generated': cert_generated,
        'cert_id':        cert_id,
        'pdf_url':        pdf_url,
        'email_sent':     email_sent,
        'message': (
            f'🎉 You scored {score}/20 — Certificate sent to {request.user.email}!'
            if passed and email_sent else
            f'🎉 You scored {score}/20 — Certificate generated!'
            if passed else
            f'You scored {score}/20. You need 17/20 to pass. Keep practicing!'
        ),
    })
   

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def topic_test_status(request):
    lang = request.query_params.get('language', 'python')
    topics = Topic.objects.filter(programming_language=lang).order_by('order')
    data = []
    for t in topics:
        best = TopicTestAttempt.objects.filter(
            user=request.user, topic_id=t.id
        ).order_by('-score').first()
        data.append({
            'topic_id': t.id,
            'topic_name': t.name,
            'order': t.order,
            'passed': best.passed if best else False,
            'best_score': best.score if best else None,
            'is_weak': best.is_weak if best else False,
        })
    return Response({'statuses': data})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def leaderboard(request):
    lang = request.query_params.get('language', 'python')
    entries = (
        LeaderboardEntry.objects
        .filter(programming_language=lang)
        .select_related('user')
        .order_by('-total_score', '-topics_completed')[:50]
    )

    data = []
    my_rank = None
    for i, e in enumerate(entries):
        row = {
            'rank': i + 1,
            'username': e.user.full_name or e.user.username,
            'total_score': e.total_score,
            'topics_completed': e.topics_completed,
            'is_me': e.user_id == request.user.id,
        }
        if e.user_id == request.user.id:
            my_rank = i + 1
        data.append(row)
    return Response({'language': lang, 'leaderboard': data, 'my_rank': my_rank})



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_code(request):
    code     = request.data.get('code', '')
    language = request.data.get('language', 'python')

    if not code.strip():
        return Response({'stdout': '', 'stderr': '', 'compile_err': 'No code provided.'})

    # ── PYTHON: run locally via subprocess ─────────────────────
    if language == 'python':
        return _run_python(code)

    # ── JAVA: compile & run locally via subprocess ─────────────
    elif language == 'java':
        return _run_java(code)

    else:
        return Response({'error': f'Unsupported language: {language}'}, status=400)


def _run_python(code):
    """Run Python code safely in a subprocess."""
    # Block dangerous imports
    blocked = ['import os', 'import sys', 'import subprocess',
                'import socket', 'import requests', '__import__',
                'open(', 'eval(', 'exec(', 'compile(']
    for b in blocked:
        if b in code:
            return Response({
                'stdout': '',
                'stderr': f'SecurityError: "{b}" is not allowed in the practice editor.',
                'compile_err': '',
            })

    try:
        result = subprocess.run(
            ['python3', '-c', code],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return Response({
            'stdout':      result.stdout,
            'stderr':      result.stderr,
            'compile_err': '',
        })
    except subprocess.TimeoutExpired:
        return Response({
            'stdout':      '',
            'stderr':      '⏱ Time limit exceeded (10 seconds).',
            'compile_err': '',
        })
    except Exception as e:
        return Response({
            'stdout':      '',
            'stderr':      '',
            'compile_err': f'Server error: {str(e)}',
        })


def _run_java(code):
    """Compile and run Java code using local javac/java."""
    # Extract public class name from code
    match = re.search(r'public\s+class\s+(\w+)', code)
    class_name = match.group(1) if match else 'Main'

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            java_file = os.path.join(tmpdir, f'{class_name}.java')
            with open(java_file, 'w') as f:
                f.write(code)

            # ── Compile ──────────────────────────────────────
            compile_result = subprocess.run(
                ['javac', java_file],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=tmpdir,
            )

            if compile_result.returncode != 0:
                # Clean up error path to show only filename not full path
                err = compile_result.stderr.replace(tmpdir + '/', '')
                return Response({
                    'stdout':      '',
                    'stderr':      '',
                    'compile_err': err,
                })

            # ── Run ──────────────────────────────────────────
            run_result = subprocess.run(
                ['java', '-cp', tmpdir, class_name],
                capture_output=True,
                text=True,
                timeout=10,
            )

            return Response({
                'stdout':      run_result.stdout,
                'stderr':      run_result.stderr,
                'compile_err': '',
            })

    except FileNotFoundError:
        # javac not installed — fallback message
        return Response({
            'stdout':      '',
            'stderr':      '',
            'compile_err': (
                '⚠️ Java compiler not found on server.\n'
                'Run: sudo apt install default-jdk -y\n'
                'Then restart Django.'
            ),
        })
    except subprocess.TimeoutExpired:
        return Response({
            'stdout':      '',
            'stderr':      '⏱ Time limit exceeded (10 seconds).',
            'compile_err': '',
        })
    except Exception as e:
        return Response({
            'stdout':      '',
            'stderr':      '',
            'compile_err': f'Server error: {str(e)}',
        })