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
    if request.method == 'POST':
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
            file = request.FILES.get('file') # from session_detail.html <input type="file" name="file">
            # (tu wykonaj walidację pliku — patrz sekcja 4)
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
                #mime_map = mime_dictionary() # import z utils.py
                Attachments.objects.create(
                    message=msg,
                    file=file,
                    file_type=mime_to_type.get(file.content_type, 'txt'), # or file_type=mime_map().get(file.content_type,)
                    size=file.size
                    )
            reply = ask_openrouter(msg) # odpowiedz bota. Tu przekazujemy cały obiekt message, bo funkcja build_user_content() w openrouter.py potrafi z niego wyciągnąć zarówno tekst, jak i załączniki
            assistant_msg = ChatMessage.objects.create(session=session, role='assistant', content=reply) # Nie zapisujemy audio do msg, bo msg oznacza wiadomość użytkownika. Audio ma należeć do assistant_msg.
            audio_bytes = generate_tts_file(reply)
            audio = AudioMessage.objects.create(message=assistant_msg)
            audio.audio_file.save('reply.mp3', ContentFile(audio_bytes))
        return redirect('session_detail', session_id=session.id)
    return render(request, 'chat/session_detail.html', {'session': session})