from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from .models import ChatSession, ChatMessage, Attachments
from .openrouter import ask_openrouter

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
    session = get_object_or_404(ChatSession, id=session_id, user=request.user)
    if request.method == 'POST':
        text = request.POST.get('message', '').strip()
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
            reply = ask_openrouter(text)
            ChatMessage.objects.create(session=session, role='assistant', content=reply)
        return redirect('session_detail', session_id=session.id)
    return render(request, 'chat/session_detail.html', {'session': session})