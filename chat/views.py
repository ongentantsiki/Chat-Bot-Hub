from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from .models import ChatSession, ChatMessage, Attachments, AudioMessage
from django.core.files.base import ContentFile
from .openrouter import ask_openrouter
from .utils import mime_dictionary, generate_tts_file

def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'chat/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'chat/login.html', {'form': form})

@login_required
def logout_view(request):
    if request.method == 'POST': # if 'DIALOG' or 'GET'?
        logout(request)
        return redirect('login')
    return render(request, 'chat/logout.html')

@login_required
def home(request):
    sessions = ChatSession.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'chat/home.html', {'sessions': sessions})

@login_required
def session_create(request):
    if request.method == 'POST':
        name = request.POST.get('name') or 'New chat'
        s = ChatSession.objects.create(name=name, user=request.user)
        return redirect('session_detail', session_id=s.id)
    return render(request, 'chat/session_form.html')

@login_required
def session_detail(request, session_id):
    ALLOWED = ['text/plain', 'application/pdf', 'image/jpeg', 'image/png']
    MAX_SIZE = 5 * 1024 * 1024  # 5 MB
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    tts_error = None
    if request.method == 'POST':
        if 'generate_tts' in request.POST:
            message_id = request.POST.get('message_id')
            if message_id:
                msg = get_object_or_404(ChatMessage, id=message_id, session=session, role='assistant')
                if not msg.audio.exists():
                    try:
                        audio_bytes = generate_tts_file(msg.content)
                        audio = AudioMessage.objects.create(message=msg)
                        audio.audio_file.save(f'reply_{msg.id}.mp3', ContentFile(audio_bytes))
                    except Exception:
                        tts_error = "It appears that server can not create audio message now."
            if tts_error:
                return render(request, 'chat/session_detail.html', {'session': session, 'tts_error': tts_error})
            return redirect('session_detail', session_id=session.id)
        
        text = request.POST.get('message', '').strip()
        if not text and 'file' in request.FILES:
            return render(request, 'chat/session_detail.html', {
                'session': session,
                'error': 'Wiadomość nie może być pusta'
                })
        if not text and 'file' in request.FILES:
            return render(request, 'chat/session_detail.html', {
                'session': session,
                'error': 'Wiadomość nie może być pusta'
                })
        if text:
            file = request.FILES.get('file')
            msg = ChatMessage.objects.create(session=session, role='user', content=text)
            if file:
                if msg.attachments.exists():
                    return render(request, 'chat/session_detail.html', {
                        'session': session,
                        'error': 'Możesz dodać tylko 1 plik do wiadomości'
                    })
                if file.size > MAX_SIZE:
                    return render(request, 'chat/session_detail.html', {
                        'session': session,
                        'error': 'Plik za duży (max 5 MB)'
                    })
                if file.content_type not in ALLOWED:
                    return render(request, 'chat/session_detail.html', {
                        'session': session,
                        'error': 'Nieobsługiwany typ pliku'
                    })
                mime_to_type = {
                    'text/plain': 'txt',
                    'application/pdf': 'pdf',
                    'image/jpeg': 'img',
                    'image/png': 'img',
                    }
                Attachments.objects.create(
                    message=msg,
                    file=file,
                    file_type=mime_to_type.get(file.content_type, 'txt'),
                    size=file.size
                    )
            reply = ask_openrouter(msg)
            assistant_msg = ChatMessage.objects.create(session=session, role='assistant', content=reply)
            # Removed automatic audio generation
        return redirect('session_detail', session_id=session.id)
    return render(request, 'chat/session_detail.html', {'session': session})