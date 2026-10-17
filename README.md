# 🎙️ Türkçe Ses Tanıma ve Konuşmacı Ayrıştırma Aracı (STT + Diarization)

MP4 ve MP3 (ve diğer tüm video/ses) dosyalarınızı **tamamen yerel (offline)** olarak Türkçe metne dönüştüren, ortamdaki farklı konuşmacıları otomatik tespit edip **"X1", "X2"** şeklinde etiketleyen modern bir masaüstü uygulamasıdır.

Intel Core i3 CPU ve 8 GB RAM gibi standart donanımlarda yüksek performans ve düşük bellek tüketimi için **CPU INT8 (CTranslate2)** optimizasyonuna sahiptir.

---

## ✨ Özellikler

- **100% Çevrimdışı (Offline):** İnternet bağlantısı veya bulut API'si gerektirmeden doğrudan bilgisayarınızın işlemcisi üzerinde çalışır.
- **YouTube Linki Desteği (Otomatik İndirme):** Herhangi bir YouTube video adresini (`https://www.youtube.com/watch?v=...`) yapıştırarak videonun sesini (`yt-dlp` ile) arka planda otomatik indirebilir ve anında Türkçe transkripsiyonunu alabilirsiniz.
- **Tüm Medya Formatları Desteği:** FFmpeg entegrasyonu ile yerel `.mp4`, `.mp3`, `.wav`, `.m4a`, `.aac`, `.mkv`, `.flac`, `.ogg` dosyalarını otomatik 16kHz WAV formatına dönüştürür.
- **Yüksek Doğrulukta Türkçe Konuşma Tanıma:** OpenAI Whisper mimarisinin CTranslate2 optimize edilmiş sürümü (`faster-whisper`) ile Türkçe sesleri yüksek doğrulukla metne döker.
- **🎧 Ses Ön-İyileştirme (Audio Enhancement):** 
  - 80Hz Yüksek Geçiren Filtre ile alt frekans dip gürültülerini, uğultuları ve cızırtıları keser.
  - Gürültü Kapısı (Noise Gate) ile sessiz veya düşük arka plan kısımlarını bastırır.
  - Peak Normalizasyonu ile kısık ve patlayan sesleri dengeler, fısıltı ve hızlı konuşmaları Whisper için netleştirir.
- **🎯 Hassas Ses Tespiti (VAD - Voice Activity Detection):**
  - Sessiz kelimelerin ve hızlı konuşmaların baş/son harflerinin kırpılmasını önlemek için 250ms konuşma tamponu (`speech_pad_ms`) ve 0.35 hassas eşik kullanır.
- **✨ Türkçe Metin Son-İşleme & Halüsinasyon Temizliği:**
  - Whisper'ın tekrarlayan cümle hatalarını, YouTube overlay metinlerini (`[Müzik]`, `abone olun` vb.) otomatik temizler.
  - Türkçe karakter ve noktalama işaretlerini kurallara uygun hale getirir.
- **Konuşmacı Ayrıştırma (Speaker Diarization):** 
  - Farklı konuşmacıları akustik parmak izleri (Perde/F0, Harmonikler, Spektral Ağırlık Merkezi) üzerinden ayırır.
  - Tek kişilik videolarda (monolog/YouTube yorumcu) tek konuşmacıyı doğru tespit eder.
  - Konuşmacıları otomatik olarak **`X1`**, **`X2`**, **`X3`** şeklinde etiketler.
- **Konuşmacı İsimlerini Tek Tıkla Güncelleme:**
  - Arayüzden örneğin **"X1"** etiketini **"Ahmet Yılmaz"** veya **"Mülakatçı"** yaparak tüm transkriptte anında güncelleyebilirsiniz.
- **Doğrudan Düzenleme & Arama:** Transkript metinlerini arayüzde doğrudan klavye ile düzenleyebilir, kelime veya konuşmacı araması yapabilirsiniz.
- **Çoklu Dışa Aktarım Formatları:**
  - **`.txt`**: Zaman damgalı, temiz ve okunabilir transkript raporu.
  - **`.srt`**: Video oynatıcılar ve YouTube için konuşmacı etiketli standart altyazı.
  - **`.json`**: Detaylı zamanlama ve kelime analizi içeren veri formatı.
  - **Panoya Kopyalama**: Tek tıkla metni kopyalama.
- **Modern Masaüstü Arayüzü:** `CustomTkinter` ile hazırlanmış, koyu temalı (Dark Mode), akıcı ve kullanıcı dostu grafik arayüz.

---

## 🚀 Hızlı Başlangıç

### 1. Tek Tıkla Başlatma
Uygulama dizinindeki **`run.bat`** dosyasına çift tıklamanız yeterlidir!

### 2. Komut Satırından Çalıştırma
PowerShell veya Komut Satırı üzerinden:
```powershell
.\venv\Scripts\python.exe main.py
```

---

## 🛠️ Kurulum (Yeni Bir Bilgisayarda)

Eğer projeyi sıfırdan kuruyorsanız:

1. **Otomatik Kurulum:**
   - **`setup_env.bat`** dosyasına çift tıklayın. Sanal ortamı oluşturup gerekli kütüphaneleri otomatik olarak kuracaktır.
2. **FFmpeg:**
   - FFmpeg sisteminizde kurulu değilse PowerShell üzerinden tek komutla kurabilirsiniz:
     ```powershell
     winget install Gyan.FFmpeg.Shared
     ```

---

## 📋 Kullanım Adımları

1. **Uygulamayı Açın:** `run.bat` dosyasına tıklayın.
2. **Girdi Seçin (Yerel Dosya veya YouTube):**
   - **Yerel Dosya:** "📁 Yerel Dosya" sekmesinden bilgisayarınızdaki bir video veya ses dosyasını seçin.
   - **YouTube:** "🔴 YouTube Linki" sekmesine geçerek YouTube video linkini yapıştırın. "Bilgi Getir" ile başlık ve süreyi görebilirsiniz.
3. **Ayarları Belirleyin:**
   - **Whisper Modeli:** `small (Dengeli - Hızlı)`, `medium (Yüksek Doğruluk)` veya `large-v3-turbo (En Yüksek Türkçe Kalitesi)`.
   - **VAD Hassasiyeti:** `Yüksek (Fısıltı/Hızlı sesleri kaçırmaz)` varsayılandır.
   - **Ses Ön-İyileştirme:** Gürültü ve arka plan seslerini filtrelemek için varsayılan olarak açıktır.
   - **Konuşmacı Sayısı:** Biliniyorsa (örn: tek kişi için "1 Konuşmacı", mülakat için "2 Konuşmacı") seçebilir veya "Otomatik Tespit" olarak bırakabilirsiniz.
   - **Etiket Biçimi:** `X (X1, X2...)` varsayılandır.
4. **Başlatın:** Yeşil renkli **"Transkripsiyonu Başlat"** butonuna basın.
5. **İlerlemeyi Takip Edin:**
   - Adım 1/4: Ses ayrıştırılıyor (FFmpeg)
   - Adım 1.5/4: Ses ön-iyileştirme (Gürültü kapısı, 80Hz filtre, normalizasyon)
   - Adım 2/4: Türkçe konuşma tanıma yapılıyor (Faster-Whisper + Türkçe Prompt)
   - Adım 3/4: Konuşmacılar ayrıştırılıyor (Diarization)
   - Adım 4/4: Hizalama, Türkçe son-işleme ve birleştirme
6. **Sonucu İnceleyin & Düzenleyin:**
   - Sağ taraftaki ekranda `[00:01 - 00:05] X1: ...` şeklinde konuşmalar listelenecektir.
   - Konuşmacı isimlerini değiştirmek için üstteki **"🏷️ Konuşmacı İsmini Değiştir"** butonunu kullanabilirsiniz.
7. **Kaydedin:** `TXT`, `SRT` veya `JSON` butonlarına tıklayarak transkriptinizi istediğiniz formatta dışa aktarın.

---

## 📂 Proje Yapısı

```
E:\Speech-To-Text\
│
├── src\
│   ├── config.py              # Uygulama ve dizin yapılandırması
│   ├── audio_processor.py     # FFmpeg ses ayrıştırma ve dönüştürme
│   ├── audio_enhancer.py      # Gürültü filtresi, normalizasyon ve iyileştirme
│   ├── transcriber.py         # Faster-Whisper Türkçe konuşma tanıma
│   ├── text_postprocessor.py  # Halüsinasyon temizliği ve Türkçe metin düzeltici
│   ├── diarizer.py            # Konuşmacı ayrıştırma (X1, X2) algoritması
│   ├── aligner.py             # Zaman ve konuşmacı hizalama motoru
│   ├── exporter.py            # TXT, SRT, JSON ve CSV çıktı üretici
│   ├── youtube_downloader.py  # Anti-bot YouTube ses indirme motoru
│   └── ui\
│       ├── app.py             # CustomTkinter ana pencere ve iş parçacıkları
│       ├── components.py      # Özel arayüz kartları ve iletişim pencereleri
│       └── style.py           # Renk paletleri ve konuşmacı rozet renkleri
│
├── models\                    # Yerel model önbelleği
├── outputs\                   # Otomatik kaydedilen transkriptler
├── tests\
│   ├── test_pipeline.py       # Temel boru hattı testleri
│   ├── test_youtube.py        # YouTube bağlantı testleri
│   └── test_accuracy_enhancements.py # Doğruluk ve ses iyileştirme testleri
├── main.py                    # Başlatıcı
├── requirements.txt           # Bağımlılıklar
├── run.bat                    # Tek tıkla başlatıcı
├── setup_env.bat              # Tek tıkla kurulum
└── README.md                  # Kullanım kılavuzu
```

---

## 🧪 Testleri Çalıştırma

Tüm testleri çalıştırmak için:
```powershell
.\venv\Scripts\python.exe -m unittest tests/test_accuracy_enhancements.py tests/test_pipeline.py
```
*(16 test, 0.8 saniyede başarıyla tamamlanır).*
