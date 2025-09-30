from datetime import date, timedelta
import json
from django.http import JsonResponse
from django.shortcuts import redirect, render
from .models import QuestionAnswer
from .forms import UserForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from groq import Groq
from django.conf import settings



# Initialize Groq client
client = Groq(api_key=settings.GROQ_API_KEY)


@login_required(login_url="signin")
def index(request):
    today = date.today()
    yesterday = date.today() - timedelta(days=1)
    seven_days_ago = date.today() - timedelta(days=7)
    
    questions = QuestionAnswer.objects.filter(user=request.user)
    t_questions = questions.filter(created=today)
    y_questions = questions.filter(created=yesterday)
    s_questions = questions.filter(created__gte=seven_days_ago, created__lte=today)
    
    context = {"t_questions": t_questions, "y_questions": y_questions, "s_questions": s_questions}
    return render(request, "chatapp/index.html", context)


def signup(request):
    if request.user.is_authenticated:
        return redirect('index')
    form = UserForm()
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            username = request.POST["username"]
            password = request.POST["password1"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index')
    context = {"form": form}
    return render(request, "chatapp/signup.html", context)


def signin(request):
    err = None
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            err = "Invalid credentials"
        
    context = {"error": err}
    return render(request, "chatapp/signin.html", context)


def signout(request):
    logout(request)
    return redirect("signin")


# ---------------- Groq AI Function ---------------- #
def ask_groq(message):
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # ✅ Groq model
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": message}
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"


def getValue(request):
    data = json.loads(request.body)
    message = data["msg"] 
    response = ask_groq(message)
    QuestionAnswer.objects.create(user=request.user, question=message, answer=response)
    return JsonResponse({"msg": message, "res": response})
