from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login,authenticate
from django.contrib.auth.decorators import login_required
from .forms import SignupForm,RoomForm
from .models import Room
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

def home(request):
    return render(request,"home.html")
def register(request):
    if request.method == "POST":
        username = request.POST.get("username")  # ✅ Use .get() to avoid KeyError
        password = request.POST.get("password")
        
        if not username or not password:  # ✅ Check if fields are empty
            return render(request, "register.html", {"error": "All fields are required."})
        
        user = User.objects.create_user(username=username, password=password)
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("dashboard")  # Change to your actual dashboard URL

    return render(request, "register.html")
@login_required
def dashboard(request):
    rooms = Room.objects.all()  # Get all rooms
    return render(request, "dashboard.html", {"rooms": rooms})
@login_required
def create_room(request):
    if request.method == "POST":
        room_name = request.POST.get("room_name")
        room_password = request.POST.get("room_password")

        if Room.objects.filter(name=room_name).exists():
            return render(request, "create_room.html", {"error": "Room name already exists!"})

        Room.objects.create(name=room_name, password=room_password, admin=request.user)
        return redirect("home")

    return render(request, "create_room.html")
@login_required
def join_room(request, room_id):
    room = Room.objects.get(id=room_id)

    if request.method == "POST":
        entered_password = request.POST.get("password")
        if entered_password == room.password:
            room.participants.add(request.user)
            return redirect("room", room_id=room.id)
        else:
            messages.error(request, "Incorrect password. Try again.")
    
    return render(request, "join_room.html", {"room": room})
@login_required
def room_view(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    return render(request, "document.html", {"room": room})
def document_view(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    return render(request, "document.html", {"room": room})

@csrf_exempt
def save_document(request, room_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            room = Room.objects.get(id=room_id)
            room.content = data.get("content", "")
            room.save()
            return JsonResponse({"status": "success"})
        except Room.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Room not found"}, status=404)
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)
def get_document(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    return JsonResponse({"content": room.content})

@csrf_exempt
def save_document(request, room_id):
    if request.method == "POST":
        room = get_object_or_404(Room, id=room_id)
        data = json.loads(request.body)
        room.content = data.get("content", "")
        room.save()
        return JsonResponse({"message": "Document saved successfully!"})
def get_active_users(request, room_id):
    room = Room.objects.get(id=room_id)
    users = room.participants.all().values_list('username', flat=True)
    return JsonResponse({'users': list(users)})