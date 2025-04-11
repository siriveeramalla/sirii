from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login,authenticate
from django.contrib.auth.decorators import login_required
from .forms import SignupForm,RoomForm
from .models import Room,RoomContent
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils import timezone
from .models import UserStatus
from django.contrib.auth import logout
from django.contrib.sessions.models import Session
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from django.core.cache import cache

@csrf_exempt
def update_editing_status(request, room_id):
    if request.method == "POST" and request.user.is_authenticated:
        cache_key = f"editing:{room_id}:{request.user.username}"
        cache.set(cache_key, True, timeout=10)  # user is "editing" for 10 seconds
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)

def get_editing_users(request, room_id):
    room = Room.objects.get(id=room_id)
    users = room.participants.all().values_list('username', flat=True)
    editing_users = []

    for username in users:
        cache_key = f"editing:{room_id}:{username}"
        if cache.get(cache_key):
            editing_users.append(username)

    return JsonResponse({'editing': editing_users})

def home(request):
    return render(request,"home.html")
def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect("dashboard")
        else:
            return render(request, "register.html", {"form": form})
    else:
        form = UserCreationForm()
    return render(request, "register.html", {"form": form})
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
@login_required
def save_document(request, room_id):
    if request.method == "POST":
        data = json.loads(request.body)
        content = data.get("content", "")
        room = get_object_or_404(Room, id=room_id)

        room_content, created = RoomContent.objects.get_or_create(room=room)
        room_content.content = content
        room_content.save()

        return JsonResponse({"status": "success"})
def get_document(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    room_content, created = RoomContent.objects.get_or_create(room=room)
    return JsonResponse({'content': room_content.content})

def get_active_users(request, room_id):
    sessions = Session.objects.filter(expire_date__gte=now())
    active_user_ids = []

    for session in sessions:
        data = session.get_decoded()
        user_id = data.get('_auth_user_id')
        if user_id:
            active_user_ids.append(int(user_id))

    users_in_room = UserStatus.objects.filter(room_id=room_id, user_id__in=active_user_ids)
    # Only show users who are really logged in
    return JsonResponse({
        "users": [u.user.username for u in users_in_room]
    })
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()

            # Check for active sessions of the same user
            sessions = Session.objects.filter(expire_date__gte=timezone.now())
            for session in sessions:
                data = session.get_decoded()
                if str(user.id) == str(data.get('_auth_user_id')):
                    return render(request, 'login.html', {
                        'form': form,
                        'message': "You're already logged in from another device."
                    })

            login(request, user)

            # Update UserStatus (optional but good for tracking)
            UserStatus.objects.update_or_create(user=user, defaults={'is_logged_in': True})

            return redirect('dashboard')
    else:
        form = AuthenticationForm()

    return render(request, 'login.html', {'form': form})
def custom_logout(request):
    if request.user.is_authenticated:
        try:
            status = UserStatus.objects.get(user=request.user)
            status.is_logged_in = False
            status.save()
        except UserStatus.DoesNotExist:
            pass
    logout(request)
    return redirect('home')