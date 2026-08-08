[app]
title = YouTube Downloader
package.name = ytdownloader
package.domain = com.example.ytdownloader
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy==2.1.0,yt-dlp,android
orientation = portrait
fullscreen = 0
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25c
android.accept_sdk_license = True
p4a.branch = master
# Incluir el binario ffmpeg desde la carpeta ffmpeg_bin
android.add_src = ffmpeg_bin
