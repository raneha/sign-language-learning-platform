import random
import time
import cv2
import numpy as np
import tensorflow as tf
import mediapipe as mp
import base64
import json
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import SignupForm, LoginForm
from .models import ASLPractice

model = tf.keras.models.load_model("sign_language/asl_mobilenet_model.h5")
classes = [chr(i) for i in range(65, 91)]

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)

LETTERS_LEVEL_1 = list("ABCELOVWUY")
LETTERS_LEVEL_2 = list("DFKRSIXM")
LETTERS_LEVEL_3 = list("GHPQJZNT")
WORDS = ["HELLO","PVG","LOVE", "MOM","CAT","DOG"]

def user_login(request):
    if request.user.is_authenticated:
        return redirect('aslearn')
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('aslearn')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    return render(request, 'sign_language/firstPage.html', {'form': form})

def signup(request):
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully! Please log in.")
            return redirect('login')
    else:
        form = SignupForm()
    return render(request, 'sign_language/signup.html', {'form': form})

@login_required(login_url='login')
def aslearn(request):
    return render(request, 'sign_language/ASLEARN.html')

@login_required(login_url='login')
def learn(request):
    return render(request, 'sign_language/learn.html')

@login_required
def select_level(request):
    return render(request, "sign_language/select_level.html")

@login_required
def practice(request, level):
    if level == "level-1":
        letter_list = LETTERS_LEVEL_1
    elif level == "level-2":
        letter_list = LETTERS_LEVEL_2
    elif level == "level-3":
        letter_list = LETTERS_LEVEL_3
    elif level == "level-4":
        letter_list = WORDS
    else:
        return redirect("select_level")

    if level != "level-4":
        if "practice_letters" not in request.session or request.session.get("current_level") != level:
            request.session["practice_letters"] = letter_list.copy()
            request.session["current_letter_index"] = 0
            request.session["current_level"] = level

        current_index = request.session["current_letter_index"]
        if current_index >= len(request.session["practice_letters"]):
            return redirect("select_level")

        target_text = request.session["practice_letters"][current_index]
        return render(request, "sign_language/practice.html", {
            "level": level,
            "target_text": target_text,
            "video_url": f"media/VideoSign/{target_text}.mp4",
        })
    else:
        if "word_list" not in request.session or request.session.get("current_level") != level:
            request.session["word_list"] = letter_list.copy()
            request.session["current_word_index"] = 0
            request.session["current_letter_index"] = 0
            request.session["current_level"] = level

        word_idx = request.session["current_word_index"]
        if word_idx >= len(request.session["word_list"]):
            return redirect("select_level")

        current_word = request.session["word_list"][word_idx]
        current_letter_index = request.session["current_letter_index"]
        target_letter = current_word[current_letter_index]

        completed_part = current_word[:current_letter_index]
        return render(request, "sign_language/practice.html", {
            "level": level,
            "target_text": target_letter,
            "current_word": current_word,
            "completed_part": completed_part,
            "video_url": f"media/VideoSign/{target_letter}.mp4",
        })

@csrf_exempt
@require_POST
def detect_asl(request):
    data = json.loads(request.body)
    frame_data = data.get("frame")
    current_level = data.get("current_level")
    target_text = data.get("target_text")
    current_word = data.get("current_word")

    if not frame_data:
        return JsonResponse({"error": "No frame received"}, status=400)

    encoded_data = frame_data.split(',')[1]
    nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    h, w, _ = frame.shape

    detected_letter = None
    accuracy = 0
    bbox = None
    letter_success = False

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            x_min, y_min = w, h
            x_max, y_max = 0, 0

            for lm in hand_landmarks.landmark:
                x, y = int(lm.x * w), int(lm.y * h)
                x_min, y_min = min(x_min, x), min(y_min, y)
                x_max, y_max = max(x_max, x), max(y_max, y)

            margin = 50
            x_min, y_min = max(x_min - margin, 0), max(y_min - margin, 0)
            x_max, y_max = min(x_max + margin, w), min(y_max + margin, h)

            hand_roi = frame[y_min:y_max, x_min:x_max]
            if hand_roi.size > 0:
                img = cv2.resize(hand_roi, (224, 224))
                img = img / 255.0
                img = np.expand_dims(img, axis=0)

                predictions = model.predict(img)
                predicted_idx = np.argmax(predictions[0])
                detected_letter = classes[predicted_idx]
                accuracy = predictions[0][predicted_idx] * 100

                print(f'Detected Letter:{detected_letter} with Accuracy:{accuracy}')

                bbox = {"x_min": x_min, "y_min": y_min, "x_max": x_max, "y_max": y_max}

                if detected_letter == target_text and accuracy >= 50:
                    letter_success = True

                    end_time = time.time()
                    time_taken = data.get("time_taken", 0)
                    frames_taken = data.get("frames_taken", 0)

                    ASLPractice.objects.create(
                        user=request.user,
                        level=current_level,
                        target_text=target_text,
                        accuracy=accuracy,
                        frames_taken=frames_taken,
                        time_taken=time_taken,
                        score = accuracy/10
                    )

    return JsonResponse({
        "letter": detected_letter,
        "accuracy": accuracy,
        "bbox": bbox,
        "letter_success": letter_success
    })

@login_required
def next_practice(request, level):
    if level != "level-4":
        current_index = request.session.get("current_letter_index", 0)
        request.session["current_letter_index"] = current_index + 1
    else:
        current_word_index = request.session.get("current_word_index", 0)
        request.session["current_word_index"] = current_word_index + 1
        request.session["current_letter_index"] = 0
        request.session.pop("word_completed", None)

    return redirect("practice", level=level)


@login_required
def performance(request):
    user_performance = ASLPractice.objects.filter(user=request.user).order_by("-timestamp")
    return render(request, "sign_language/performance.html", {"user_performance": user_performance})
