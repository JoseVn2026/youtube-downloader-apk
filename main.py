import os
import re
import sys
import threading
import shutil
import yt_dlp
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.utils import platform

# En Android, el binario ffmpeg compilado por la receta estará disponible en el PATH.
# Si no, se puede forzar la ubicación típica.
FFMPEG_PATH = "ffmpeg"  # yt-dlp lo buscará en PATH automáticamente

def descargar_video(url, formato_id, destino, progress_callback, done_callback):
    def hook(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            if total:
                percent = downloaded / total * 100
                speed = d.get('speed', 0)
                Clock.schedule_once(lambda dt: progress_callback(percent, speed))
        elif d['status'] == 'finished':
            Clock.schedule_once(lambda dt: done_callback(destino))
    try:
        ydl_opts = {
            'format': formato_id,
            'outtmpl': destino,
            'merge_output_format': 'mp4',
            'progress_hooks': [hook],
            'ffmpeg_location': FFMPEG_PATH,   # se usará el ffmpeg del sistema
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        Clock.schedule_once(lambda dt: done_callback(str(e)))

class YouTubeApp(App):
    def build(self):
        self.title = "YouTube Downloader"
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        layout.add_widget(Label(text="URL del video:", size_hint=(1, 0.1)))
        self.url_input = TextInput(hint_text="Pega el enlace aquí", size_hint=(1, 0.1))
        layout.add_widget(self.url_input)

        self.btn_analizar = Button(text="🔍 Analizar", size_hint=(1, 0.1))
        self.btn_analizar.bind(on_press=self.analizar)
        layout.add_widget(self.btn_analizar)

        self.spinner = Spinner(text='Primero analiza', values=[], size_hint=(1, 0.1))
        layout.add_widget(self.spinner)

        self.progress = ProgressBar(max=100, value=0, size_hint=(1, 0.1))
        layout.add_widget(self.progress)

        self.btn_descargar = Button(text="⬇️ Descargar", size_hint=(1, 0.1), disabled=True)
        self.btn_descargar.bind(on_press=self.descargar)
        layout.add_widget(self.btn_descargar)

        self.estado = Label(text="Listo", size_hint=(1, 0.1))
        layout.add_widget(self.estado)

        return layout

    def analizar(self, instance):
        url = self.url_input.text.strip()
        if not url:
            self.estado.text = "Introduce una URL"
            return
        self.estado.text = "Analizando..."
        threading.Thread(target=self._fetch_formats, args=(url,), daemon=True).start()

    def _fetch_formats(self, url):
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                self.title_video = info.get('title', 'video')
                formats = info.get('formats', [])
                opciones = ['⭐ Mejor calidad']
                for f in formats:
                    if f.get('height') and f.get('acodec') != 'none':
                        opciones.append(f"{f['height']}p (combinado)")
                    elif f.get('height') and f.get('acodec') == 'none':
                        opciones.append(f"{f['height']}p + audio")
                opciones = sorted(set(opciones), key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0, reverse=True)
                opciones.append('🎵 Solo audio MP3')
                self.formatos = opciones
                Clock.schedule_once(lambda dt: self._actualizar_spinner(opciones))
        except Exception as e:
            Clock.schedule_once(lambda dt: setattr(self, 'estado', Label(text=f"Error: {e}")))

    def _actualizar_spinner(self, opciones):
        self.spinner.values = opciones
        self.spinner.text = opciones[0]
        self.btn_descargar.disabled = False
        self.estado.text = f"✅ {len(opciones)-2} formatos"

    def descargar(self, instance):
        seleccion = self.spinner.text
        if seleccion not in self.spinner.values:
            return
        url = self.url_input.text.strip()
        es_audio = 'audio' in seleccion.lower()
        ext = '.mp3' if es_audio else '.mp4'
        destino = os.path.join('/sdcard/Download', re.sub(r'[\\/*?:"<>|]', '_', self.title_video) + ext)
        fmt = 'bestaudio/best' if es_audio else 'bestvideo+bestaudio/best'
        self.progress.value = 0
        self.estado.text = "Descargando..."
        threading.Thread(target=descargar_video, args=(url, fmt, destino, self.update_progress, self.finalizado), daemon=True).start()

    def update_progress(self, percent, speed):
        self.progress.value = percent
        self.estado.text = f"Descargando... {percent:.1f}%"

    def finalizado(self, resultado):
        if isinstance(resultado, str) and os.path.exists(resultado):
            self.estado.text = f"✅ Guardado en {resultado}"
        else:
            self.estado.text = f"❌ Error: {resultado}"

if __name__ == '__main__':
    YouTubeApp().run()
