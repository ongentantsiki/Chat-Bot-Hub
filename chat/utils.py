from gtts import gTTS
from django.core.files.base import ContentFile
import io

def mime_dictionary():
    return {
        'image/jpeg': 'img',
        'image/png': 'img',
        'application/pdf': 'pdf',
        'text/plain': 'txt'
    }

def generate_tts_file(text):
    mp3 = gTTS(text=text, tld='com', lang='en')
    buffer = io.BytesIO()
    mp3.write_to_fp(buffer)
    buffer.seek(0)
    return buffer.getvalue()