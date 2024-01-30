from django.shortcuts import render, redirect, get_object_or_404
from . forms import *
from . models import *
from django.contrib import messages
from django.http.response import StreamingHttpResponse
from django.http.response import StreamingHttpResponse, HttpResponse
from dashboard.camera import VideoCamera, IPWebCam
from PIL import Image
from io import BytesIO
import base64
import mediapipe as mp
import cv2
from dashboard.emotionDetection import face_emotion_detection
from dashboard.eyeGazeDetection import iris_position_detection
from dashboard.checkLocation import process_frame
import pyttsx3
import threading
import cv2
import time
import ast
from django.http import StreamingHttpResponse
from django.views.decorators import gzip
import os
import openai
import speech_recognition as sr
from collections import Counter


questions = []
questions_copy = []
answers = []
topic = ""
subtopic = ""
expertise = ""
number = 0
answers_feedback = []
# API_KEY = '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' old_key
# API_KEY = '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' old
API_KEY = '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'
os.environ["OPENAI_API_KEY"] = API_KEY
openai.api_key = os.getenv("OPENAI_API_KEY")
stop_streaming = False
emotions = []
directions = []
position = []
location = []

def home(request):
    print(emotions, directions, position, location, questions, answers, answers_feedback)
    print(len(questions), len(answers), len(answers_feedback))
    # get_answer_feedback()
    print(answers_feedback)
    return render(request, 'dashboard/home.html')

def feedback(request):
    global questions
    global questions_copy
    global answers
    global answers_feedback
    tab = request.GET.get('tab', 'coaching')
    emotion_counts = Counter(emotions)
    print("infeedback")
    length = len(emotions)
    up = ((emotion_counts['Fear'] + emotion_counts['Angry'] + emotion_counts['Disgust'] + emotion_counts['Sad']) / length) * 100
    happy = (emotion_counts['Happy'] / length) * 100
    neutral = (emotion_counts['Neutral'] / length) * 100
    surprise = (emotion_counts['Surprise'] / length) * 100
    feedback = api_call(generate_prompt_emotion_feedback())
    ec_center = int((directions[0] / directions[1]) * 100)
    get_answer_feedback()
    print(questions)
    print(questions_copy)
    print(answers)
    print(answers_feedback)
    text = ""
    # questions_list = [(questions[i], answers[i], answers_feedback[3 * i], answers_feedback[3 * i + 1]) for i in range(len(questions) - 1)]
    suggestion = answers_feedback[-1]
    context = {'tab': tab, 'up': int(up), 'happy': int(happy), 'neutral': int(neutral), 'surprise': int(surprise), 'max': max(emotions), 'feedback': feedback[1:], 'ec_center': ec_center, 'loc1': location[0] > location[2] - location[0], 'loc2': location[1] > location[2] - location[1], 'questions': questions, 'answers': answers, 'answers_feedback': answers_feedback, 'indices': range(len(answers)), 'suggestion': suggestion, 'text': text, 'num': len(answers)}
    print(context)
    # context = {'tab': 'coaching', 'up': 0, 'happy': 0, 'neutral': 100, 'surprise': 0, 'max': 100, 'feedback': '\n\nDear [Name],\n\nDuring your interview, you showed a neutral emotion, which can be beneficial as it indicates a calm and composed demeanor. However, it is essential to showcase a range of emotions to convey your passion and enthusiasm for the role. By being too neutral, it may come across as disinterested. I advise you to practice showing more positive emotions like excitement and confidence to leave a lasting impression on the interviewer.\n\nBest of luck!\n[Your Name]', 'ec_center': 91, 'loc1': False, 'loc2': True, 'questions': ['\n\n1. What is the difference between a static and non-static method in Java?', '\n2. Can you explain the concept of encapsulation in Java?', '\n3. How do you handle exceptions in Java?', '\n4. What is the purpose of the "this" keyword in Java?', '\n5. How does inheritance work in Java?', '\n6. Can you give an example of a Java program without using a main() method?', '\n7. What is the difference between a primitive data type and a reference data type in Java?', '\n8. Can you explain the difference between == and .equals() in Java?', '\n9. How do you declare and initialize an array in Java?', '\n10. Can you give an example of using polymorphism in Java?', 'thank you'], 'answers': ['Java is a programming language'], 'answers_feedback': [' ', '(correctness = 0%); A better answer would be - There is no correct answer as the question is incomplete and does not specify which aspect of Java is being asked about.\n\n(correctness = 0%); A better answer would be - Encapsulation in Java refers to the practice of hiding the internal workings of an object and only exposing necessary information through methods and interfaces. This allows for better control and security of the data within an object.\n(correctness = 0%); A better answer would be - Exceptions in Java are handled using try-catch blocks. The try block contains the code that may potentially throw an exception, while the catch block handles the exception and provides a solution or alternative code to be executed.\n(correctness = 0%); A better answer would be - The "this" keyword in Java refers to the current object and is used to differentiate between instance variables and local variables with the same name.\n(correctness = 0%); A better answer would be - Inheritance in Java allows for the creation of a new class by extending an existing class. This allows for code reuse and the ability to create more specialized classes.\n(correctness = 0%); A better answer would be - Yes, we can create a Java program without using a main() method by creating a static block or using a constructor.\n(correctness = 0%); A better answer would be - Primitive data types in Java are basic data types that hold a single value, while reference data types refer to objects and hold a reference to the object\'s location in memory.\n(correctness = 0%); A better answer would be - The "==" operator in Java is used for comparing primitive data types for equality, while the .equals() method is used for comparing objects for equality based on their values.\n(correctness = 0%); A better answer would be - To declare and initialize an array in Java, we use the syntax: data_type[] array_name = new data_type[length]. For example, int[] numbers = new int[5];\n(correctness = 0%); A better answer would be - Polymorphism in Java refers to the ability of an object to take on multiple forms. An example of this is method overloading, where a class can have multiple methods with the same name but with different parameters. \nthank you', ''], 'indices': range(0, 1), 'suggestion': '', 'text': '\n\n1. What is the difference between a static and non-static method in Java?<br/>Your Answer: Java is a programming language<br/> <br/>(correctness = 0%); A better answer would be - There is no correct answer as the question is incomplete and does not specify which aspect of Java is being asked about.\n\n(correctness = 0%); A better answer would be - Encapsulation in Java refers to the practice of hiding the internal workings of an object and only exposing necessary information through methods and interfaces. This allows for better control and security of the data within an object.\n(correctness = 0%); A better answer would be - Exceptions in Java are handled using try-catch blocks. The try block contains the code that may potentially throw an exception, while the catch block handles the exception and provides a solution or alternative code to be executed.\n(correctness = 0%); A better answer would be - The "this" keyword in Java refers to the current object and is used to differentiate between instance variables and local variables with the same name.\n(correctness = 0%); A better answer would be - Inheritance in Java allows for the creation of a new class by extending an existing class. This allows for code reuse and the ability to create more specialized classes.\n(correctness = 0%); A better answer would be - Yes, we can create a Java program without using a main() method by creating a static block or using a constructor.\n(correctness = 0%); A better answer would be - Primitive data types in Java are basic data types that hold a single value, while reference data types refer to objects and hold a reference to the object\'s location in memory.\n(correctness = 0%); A better answer would be - The "==" operator in Java is used for comparing primitive data types for equality, while the .equals() method is used for comparing objects for equality based on their values.\n(correctness = 0%); A better answer would be - To declare and initialize an array in Java, we use the syntax: data_type[] array_name = new data_type[length]. For example, int[] numbers = new int[5];\n(correctness = 0%); A better answer would be - Polymorphism in Java refers to the ability of an object to take on multiple forms. An example of this is method overloading, where a class can have multiple methods with the same name but with different parameters. \nthank you', 'num': 1} 
    print(context)
    tab = context['tab']
    up = context['up']
    happy = context['happy']
    neutral = context['neutral']
    surprise = context['surprise']
    max_emotions = context['max']
    feedback = context['feedback']
    ec_center = context['ec_center']
    loc1 = context['loc1']
    loc2 = context['loc2']
    questions = context['questions']
    answers = context['answers']
    answers_feedback = context['answers_feedback']
    indices = list(context['indices'])
    num = context['num']

# Create an object of YourModel
    Interview_Feedback.objects.create(
        topic=topic,
        subtopic=subtopic,
        expertise=expertise,
        number=number,
        up=up,
        happy=happy,
        neutral=neutral,
        surprise=surprise,
        max_emotions=max_emotions,
        feedback=feedback,
        ec_center=ec_center,
        loc1=loc1,
        loc2=loc2,
        questions=questions,
        answers=answers,
        answers_feedback=answers_feedback,
        indices=indices,
        num=num
    )
    return render(request, 'dashboard/feedback.html', context)
    # print(emotions, directions, position)
    # return render(request, 'dashboard/feedback.html')


def get_answer_feedback():
    global answers_feedback
    feedback = api_call(generate_prompt_answer_feedback(questions, answers))
    print("feedback = ", feedback)
    answers_feedback = feedback.split('$')
    # print(answers_feedback)

def delete_interview(request, interview_id):
    interview = Interview_Feedback.objects.get(id=interview_id)

    interview.delete()
    print("nikky")
    messages.success(request, 'Interview deleted successfully.')
    return redirect("history")

def check_feedback(request, interview_id):
    print("jshfjdshfjshdfjsjfdj")
    interview_feedback = Interview_Feedback.objects.get(id=interview_id)
    up_value = interview_feedback.up
    happy_value = interview_feedback.happy
    neutral_value = interview_feedback.neutral
    surprise_value = interview_feedback.surprise
    max_emotions_value = interview_feedback.max_emotions
    feedback_value = interview_feedback.feedback
    ec_center_value = interview_feedback.ec_center
    loc1_value = interview_feedback.loc1
    loc2_value = interview_feedback.loc2
    questions_value = ast.literal_eval(interview_feedback.questions)
    answers_value = ast.literal_eval(interview_feedback.answers)
    answers_feedback_value = ast.literal_eval(interview_feedback.answers_feedback)
    indices_value = list(interview_feedback.indices)
    num_value = interview_feedback.num
    print(questions_value)
    # You can also create a dictionary with all field names and their values
    context = {
        'up': up_value,
        'happy': happy_value,
        'neutral': neutral_value,
        'surprise': surprise_value,
        'max_emotions': max_emotions_value,
        'feedback': feedback_value,
        'ec_center': ec_center_value,
        'loc1': loc1_value,
        'loc2': loc2_value,
        'questions': questions_value,
        'answers': answers_value,
        'answers_feedback': answers_feedback_value,
        'indices': indices_value,
        'num': num_value,
    }
    return render(request, 'dashboard/feedback.html', context)


def checkPosition(request):
    return render(request, 'dashboard/checkPosition.html')


def history(request):
    context = {'interviews': Interview_Feedback.objects.all()}
    return render(request, 'dashboard/history.html', context)


def takeInterview(request):
    if request.method == 'POST':
        form = InterviewForm(request.POST)
        global topic
        global subtopic
        global expertise
        global number
        if form.is_valid():
            # Interview.objects.create(
            #     topic=request.POST['topic'],
            #     subtopic=request.POST['subtopic'],
            #     expertise=request.POST['expertise'],
            #     number=request.POST['number']
            # )
            messages.success(
                request, f'interview scheduled succesfully!')
            topic=request.POST['topic']
            subtopic=request.POST['subtopic']
            expertise=request.POST['expertise']
            number=request.POST['number']
            response = api_call(generate_prompt_questions(request.POST['topic'], request.POST['expertise'], request.POST['number'], request.POST['subtopic']))
            global questions
            global questions_copy
            global answers
            global answers_feedback
            global emotions
            global directions
            global position
            global location
            questions = []
            # answers = []
            answers_feedback = []
            emotions = []
            directions = []
            position = []
            location = []
            questions = list(response.split('$'))
            while questions == []:
                response = api_call(generate_prompt_questions(request.POST['topic'], request.POST['expertise'], request.POST['number'], request.POST['subtopic']))
                questions = list(response.split('$'))
            questions_copy = questions
            questions[-1] = "thank you"
            answers = []
            print("questions", questions)
            return render(request, 'dashboard/camera.html', {'questions': questions})
    else:
        form = InterviewForm()

    context = {'form': form}
    return render(request, 'dashboard/takeInterview.html', context)

def generate_prompt_questions(topic, expertise, number, specialization):
    if specialization != "":
        return f'generate {number} of {expertise} interview questions in the topic {topic} on {specialization}. Give the questions that are asked in the real time interview for a Engineering Computer science student. If the expertise is low give very basic questions, if the expertise is medium then give normal questions and if the expertise is high give tough questions. give me just the questions. give me the questions in a single line without giving numbers to the questions, add a dollar symbol after each question(at the end of each question)'
    if topic == "behavioral":
        return f'generate {number} behavioral questions that can be asked in a HR interview, start the questions with tell me about yourself. give me just the questions. give me the questions in a single line without giving numbers to the questions, add a dollar symbol after each question(at the end of each question)'
    return f'generate {number} of {expertise} interview questions on the topic {topic}. Give the questions that are asked in the real time interview for a Engineering Computer science student. If the expertise is low give very basic questions, if the expertise is medium then give normal questions and if the expertise is high give tough questions. give me just the questions. give me the questions in a single line without giving numbers to the questions, add a dollar symbol after each question(at the end of each question)'

def generate_prompt_answer_feedback(question, answer):
    return f'I will give you some questions and answers in the form of a list. for each question answer pair, give me what would be a better answer. give the entire response in a single line and put a "$" symbol after each answer . question: {question}. answer: {answer}.'
    

def generate_prompt_emotion_feedback():
    return f'{emotions} These are the different emotion showed by  a person during his interview. Give him an advise consisting of 50 words. before starting the advise, tell his previously show emotions, how that can effect his interview, what is dominant etc'

def api_call(promptt):
    response = openai.Completion.create(engine='gpt-3.5-turbo-instruct',
                                        prompt = promptt,
                                        temperature = 0.7,
                                        max_tokens = 1024)["choices"][0]["text"]
    return response

def speak(text):
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")
    engine.setProperty('voice', voices[1].id)
    engine.setProperty('rate', 140)
    engine.say(text)
    engine.runAndWait()

# Function to ask questions in a loop
def ask_questions():
    global answers
    for question in questions:
        threading.Thread(target=speak, args=(question,)).start()
        time.sleep(10)
        text = transcribe_audio()
        print("Transcript:", text)
        if text != "":
            answers.append(text)
        time.sleep(5)

def transcribe_audio():
    recognizer = sr.Recognizer()
    # recognizer.dynamic_energy_threshold = False
    # recognizer.energy_threshold = 400
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Listening...")
        audio_data = recognizer.listen(source)
        print("nikky")

    try:

        text = recognizer.recognize_google(audio_data)
        return text
    except sr.UnknownValueError:
        return ""


def stop_stream():
    global stop_streaming
    stop_streaming = True

def video_stream(main_interview):
    global emotions
    global directions
    global position
    global location
    emotions = []
    directions = [0,0]
    position = []
    location = [0, 0, 0]
    cap = cv2.VideoCapture(0)
    while not stop_streaming:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_flip = cv2.flip(frame, 1)
        if main_interview:
            cen, dis, tot = process_frame(frame_flip, False)
            location[0] += cen
            location[1] += dis
            location[2] += tot
            map_face_mesh = mp.solutions.face_mesh
            with map_face_mesh.FaceMesh(max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5) as face_mesh:
                results = face_mesh.process(frame_flip)
                em = face_emotion_detection(frame_flip)
                emotions.append(em)
                if results.multi_face_landmarks:
                    dir = iris_position_detection(frame_flip, results, True)
                    if dir == 'center':
                        directions[0] += 1
                    directions[1] += 1
        else:
            process_frame(frame_flip)
            # pass
        _, buffer = cv2.imencode('.jpg', frame_flip)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')



@gzip.gzip_page
def main_interview(request):
    print("que", questions)
    audio_thread = threading.Thread(target=ask_questions)
    audio_thread.start()

    def generate():
        for frame in video_stream(True):
            yield frame
        print()
    
    return StreamingHttpResponse(generate(), content_type='multipart/x-mixed-replace;boundary=frame')

@gzip.gzip_page
def checkPositionVideo(request):

    def generate():
        for frame in video_stream(False):
            yield frame
        print()
    
    return StreamingHttpResponse(generate(), content_type='multipart/x-mixed-replace;boundary=frame')
   
# def stop_streaming_view(request):
#     stop_stream()
#     return HttpResponse("Streaming stopped.")