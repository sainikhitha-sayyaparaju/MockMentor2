from django.shortcuts import render, redirect
from . forms import *
from . models import *
from django.contrib import messages
from django.http.response import StreamingHttpResponse
from django.http.response import StreamingHttpResponse, HttpResponse
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import EmailMessage, send_mail
from MockMentor import settings
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import authenticate, login, logout
# from . tokens import generate_token
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
from django.http import StreamingHttpResponse
from django.views.decorators import gzip
import os
import openai
import speech_recognition as sr
from collections import Counter


questions = []
answers = []
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

def signup(request):
    if request.method == "POST":
        username = request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']
        
        if User.objects.filter(username=username):
            messages.error(request, "Username already exist! Please try some other username.")
            return redirect('home')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email Already Registered!!")
            return redirect('home')
        
        if len(username)>20:
            messages.error(request, "Username must be under 20 charcters!!")
            return redirect('home')
        
        if pass1 != pass2:
            messages.error(request, "Passwords didn't matched!!")
            return redirect('home')
        
        if not username.isalnum():
            messages.error(request, "Username must be Alpha-Numeric!!")
            return redirect('home')
        
        myuser = User.objects.create_user(username, email, pass1)
        myuser.first_name = fname
        myuser.last_name = lname
        # myuser.is_active = False
        myuser.save()
        messages.success(request, "Your Account has been created succesfully!! Please check your email to confirm your email address in order to activate your account.")
        
        # Welcome Email
        subject = "Welcome to GFG- Django Login!!"
        message = "Hello"        
        from_email = settings.EMAIL_HOST_USER
        to_list = [myuser.email]
        print(from_email)
        print(to_list)
        send_mail(subject, message, from_email, to_list, fail_silently=True)
        
        return redirect('signin')
        
    return render(request, 'dashboard/signup.html')

def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        pass1 = request.POST['pass1']
        
        user = authenticate(username=username, password=pass1)
        
        if user is not None:
            login(request, user)
            fname = user.first_name
            # messages.success(request, "Logged In Sucessfully!!")
            request.session['authenticated_user'] = {
                'first_name': user.first_name,
                # Add other user details as needed
            }
            return render(request, "dashboard/home.html")
        else:
            messages.error(request, "Bad Credentials!!")
            return redirect('home')
    
    return render(request, 'dashboard/signin.html')

def user_profile(request):
    authenticated_user = request.session.get('authenticated_user', None)
    
    if authenticated_user:
        first_name = authenticated_user['first_name']

        # Access other user details as needed
        return render(request, 'dashboard/user_profile.html', {'first_name': first_name})
    
    

def signout(request):
    logout(request)
    messages.success(request, "Logged Out Successfully!!")
    return redirect('home')

def feedback(request):
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
    text = questions[0] + '<br/>' + 'Your Answer: ' + answers[0] + '<br/>' + answers_feedback[0] + '<br/>' + answers_feedback[1]
    # questions_list = [(questions[i], answers[i], answers_feedback[3 * i], answers_feedback[3 * i + 1]) for i in range(len(questions) - 1)]
    suggestion = answers_feedback[-1]
    context = {'tab': tab, 'up': int(up), 'happy': int(happy), 'neutral': int(neutral), 'surprise': int(surprise), 'max': max(emotions), 'feedback': feedback[1:], 'ec_center': ec_center, 'loc1': location[0] > location[2] - location[0], 'loc2': location[1] > location[2] - location[1], 'questions': questions, 'answers': answers, 'answers_feedback': answers_feedback, 'indices': range(len(answers)), 'suggestion': suggestion, 'text': text, 'num': len(answers)}
    print(context)
    return render(request, 'dashboard/feedback.html', context)
    # print(emotions, directions, position)
    # return render(request, 'dashboard/feedback.html')


def get_answer_feedback():
    global answers_feedback
    feedback = api_call(generate_prompt_answer_feedback(questions, answers))
    print("feedback = ", feedback)
    answers_feedback = feedback.split('$')
    # print(answers_feedback)

def getCam(request):
    return render(request, 'dashboard/camera.html')

def checkPosition(request):
    return render(request, 'dashboard/checkPosition.html')


def history(request):
    context = {'interviews': Interview.objects.all()}
    return render(request, 'dashboard/history.html', context)


def takeInterview(request):
    if request.method == 'POST':
        form = InterviewForm(request.POST)
        if form. is_valid():
            Interview.objects.create(
                topic=request.POST['topic'],
                subtopic=request.POST['subtopic'],
                expertise=request.POST['expertise'],
                number=request.POST['number']
            )
            messages.success(
                request, f'interview scheduled succesfully!')
            response = api_call(generate_prompt_questions(request.POST['topic'], request.POST['expertise'], request.POST['number'], request.POST['subtopic']))
            global questions
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
            print(request.POST['number'])
            questions = list(response.split('$'))
            questions[-1] = "thank you"
            print("questions", questions)
            return render(request, 'dashboard/camera.html', {'questions': questions})
    else:
        form = InterviewForm()

    context = {'form': form}
    return render(request, 'dashboard/takeInterview.html', context)

def generate_prompt_questions(topic, expertise, number, specialization):
    if specialization != "":
        return f'generate {number} of {expertise} interview questions in the topic {topic} on {specialization}. give me just the questions. give me the questions in a single line without numbering the questions, add a dollar symbol after each question'
    if topic == "behavioral":
        return f'generate {number} behavioral questions that can be asked in a HR interview, start the questions with tell me about yourself. give me just the questions. give me the questions in a single line without numbering the questions, add a dollar symbol after each question'
    return f'generate {number} of {expertise} interview questions on the topic {topic}. give me just the questions. give me the questions in a single line without numbering the questions, add a dollar symbol after each question'

def generate_prompt_answer_feedback(question, answer):
    return f'I will give you some questions and answers in the form of a list. for each question give what percent of the answer is correct in the format ( correctness = %) and then for each question give the correct answer for the question with in 150 to 200 words in the format (A better answer would be - ). Give the entire response in a single line and keep a $ symbol after you complete answering a question. give response for each question and put $ symbol after it. question: {question}. answer: {answer}.'
    

def generate_prompt_emotion_feedback():
    return f'{emotions} These are the different emotion showed by  a person during his interview. Give him an advise consisting of 50 words. before starting the advise, tell his his previously show emotions, how that can effect his interview, what is dominant etc'

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
   
def stop_streaming_view(request):
    stop_stream()
    return HttpResponse("Streaming stopped.")