# SesMetin Pro - Türkçe Ses Tanıma ve Konuşmacı Ayrıştırma (STT + Diarization)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![UI: CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter%20v2.0-blueviolet.svg)](https://github.com/TomSchimansky/CustomTkinter)
[![GitHub Repo](https://img.shields.io/badge/GitHub-The0Sanity%2FSpeech--To--Text-success.svg)](https://github.com/The0Sanity/Speech-To-Text.git)

MP4 ve MP3 (ve diğer tüm video/ses) dosyalarınızı **tamamen yerel (offline)** olarak Türkçe metne dönüştüren, ortamdaki farklı konuşmacıları otomatik tespit edip **"X1", "X2"** şeklinde etiketleyen minimalist ve sade bir masaüstü uygulamasıdır.

Intel Core i3 CPU ve 8 GB RAM gibi standart donanımlarda yüksek performans ve düşük bellek tüketimi için **CPU INT8 (CTranslate2)** optimizasyonuna sahiptir.

---

## Temel Özellikler

- **Minimalist Arayüz Tasarımı:**
  - **Karanlık ve Aydınlık Tema:** Gece modu ve Gündüz modu arasında tek tıkla geçiş.
  - **Çok Adımlı İlerleme Göstergesi (Process Stepper):** 5 aşamalı boru hattını (Medya Hazırlığı, İyileştirme, Whisper STT, Konuşmacı Ayrımı, Hizalama) sade metinlerle izleme.
  - **Canlı Metrik Şeridi (Stats Ribbon):** Toplam konuşma süresi, konuşmacı sayısı, toplam kelime adedi ve WPM (dakika başına kelime) göstergeleri.
  - **Entegre Ses Önizleme (Audio Player Bar):** Yüklenen veya indirilen ses dosyasını arayüzden doğrudan dinleme, duraklatma ve kontrol etme.
- **Gelişmiş Transkript Düzenleme:**
  - **Canlı Arama ve Filtreleme:** Metin, konuşmacı veya zaman damgasına göre anında eşleşme sayımı ve süzme.
  - **Bul ve Değiştir (Find & Replace):** Transkript genelinde kelimeleri tek tek veya topluca tek tıkla değiştirme.
  - **Konuşmacı Yönetim Paneli (Speaker Manager):** Her konuşmacının toplam konuşma süresini ve konuşma sayısını görüntüleme, isimleri tek ekrandan kolayca güncelleme.
  - **Hızlı Segment Kopyalama:** Her konuşma kartındaki kopyalama butonu ve bildirim balonları (Toast).
- **Kapsamlı Dışa Aktarım Desteği (6 Format):**
  - **`.txt`**: Zaman damgalı, temiz ve okunabilir transkript raporu.
  - **`.srt`**: Standart video oynatıcılar ve YouTube için altyazı.
  - **`.vtt`**: Modern web oynatıcıları ve HTML5 `<track>` için WebVTT altyazısı.
  - **`.json`**: Detaylı zamanlama ve kelime analizi içeren tam meta veri JSON'ı.
  - **`.csv`**: Excel / Sheets uyumlu tablolu döküm.
  - **`.md`**: Obsidian, Notion ve GitHub uyumlu sade Markdown belgesi.
  - **Panoya Kopyalama**: Biçimlendirilmiş tek tıkla pano aktarımı.
- **100% Çevrimdışı (Offline):** İnternet bağlantısı veya bulut API'si gerektirmeden doğrudan bilgisayarınızın işlemcisi üzerinde çalışır.
- **YouTube Otomatik İndirme:** YouTube linki girildiğinde `yt-dlp` ile sesi otomatik indirir ve transkribe eder.
- **Tüm Medya Formatları Desteği:** FFmpeg entegrasyonu ile `.mp4`, `.mp3`, `.wav`, `.m4a`, `.aac`, `.mkv`, `.flac`, `.ogg` dosyalarını otomatik dönüştürür.
- **Ses Ön-İyileştirme (Audio Enhancement):** 
  - 80Hz Yüksek Geçiren Filtre ile alt frekans dip gürültülerini ve uğultuları keser.
  - Gürültü Kapısı (Noise Gate) ile sessiz bölümleri bastırır.
  - Peak Normalizasyonu ile kısık ve patlayan sesleri dengeler.
- **Hassas Ses Tespiti (VAD) ve Halüsinasyon Temizliği:**
  - Hızlı ve fısıltılı konuşmaları kaçırmayan VAD eşiği.
  - Tekrarlayan kelime/öbek hatalarını ve YouTube overlay kalıplarını temizler.

---

## Hızlı Başlangıç

### 1. Tek Tıkla Başlatma (Sıfır Kurulum Zahmeti)
`run.bat` dosyasına çift tıklamanız yeterlidir.
- Sanal ortam (`venv`) ve gerekli kütüphaneler yoksa arka planda otomatik olarak kurulur.
- Bağımlılıklar zaten yüklüyse doğrudan uygulama başlatılır. Manuel ortam (`env`) yapılandırma gereksinimi kaldırılmıştır.

### 2. Komut Satırından Başlatma
PowerShell veya Terminal üzerinden:
```powershell
.\run.bat
```
veya
```powershell
python main.py
```

---

## Kurulum ve Sistem Gereksinimleri

- **Python:** 3.10 veya üzeri.
- **FFmpeg:** Ses ve video dönüştürmeleri için sistemde FFmpeg bulunmalıdır. Kurulu değilse:
  ```powershell
  winget install Gyan.FFmpeg.Shared
  ```

---

## Kullanım Rehberi

1. **Uygulamayı Başlatın:** `run.bat` dosyasını çalıştırın.
2. **Girdi Belirleyin:**
   - **Yerel Dosya:** "Yerel Dosya" sekmesinden bilgisayarınızdaki bir video veya ses dosyasını seçin. "Önizle" butonu ile ses dosyasını dinleyebilirsiniz.
   - **YouTube:** "YouTube" sekmesine video bağlantısını yapıştırın ve "Bilgi Al" butonuna basın.
3. **Ayarları Yapılandırın:**
   - **Whisper Modeli:** `small (Dengeli - Hızlı)`, `medium (Yüksek Doğruluk)` veya `large-v3-turbo (En Yüksek Kalite)`.
   - **VAD Hassasiyeti:** `Yüksek (Fısıltı/Hızlı)` veya `Normal (Standart)`.
   - **Ses Ön-İyileştirme:** Gürültü ve arka plan seslerini filtrelemek için açık tutulması önerilir.
   - **Konuşmacı Sayısı:** Tek kişi için "1", mülakat için "2" veya otomatik tespit.
4. **İşlemi Başlatın:** "Transkripsiyonu Başlat" butonuna tıklayın. Süreç göstergesi ile her aşamayı canlı izleyin.
5. **İnceleyin ve Düzenleyin:**
   - Segment metinlerini doğrudan kutucuklardan düzenleyebilirsiniz.
   - İsim değiştirmek için konuşmacı rozetine tıklayabilir veya "Konuşmacıları Yönet" penceresini kullanabilirsiniz.
   - "Bul & Değiştir" ile transkriptteki kelimeleri tek seferde güncelleyin.
6. **Dışa Aktarın:** Alt bardaki butonlar (`TXT`, `SRT`, `VTT`, `JSON`, `CSV`, `MD`) veya "Panoya Kopyala" ile çıktınızı kaydedin.

---

## Proje Mimarisi

```
Speech-To-Text/
├── main.py                  # Uygulama giriş noktası ve FFmpeg ortam yapılandırması
├── settings.json            # Kullanıcı tercihleri ve yapılandırma
├── requirements.txt         # Bağımlılık listesi
├── run.bat                  # Tek tıkla otomatik bağımlılık kontrolü ve başlatma betiği
├── PRODUCT.md               # Ürün ve tasarım manifestosu
├── src/
│   ├── aligner.py           # Metin-konuşmacı hizalama, istatistik ve arama motoru
│   ├── audio_enhancer.py    # Gürültü filtresi, 80Hz yüksek geçiren filtre ve normalizasyon
│   ├── audio_processor.py   # FFmpeg ses ayrıştırma ve medya analizleri
│   ├── config.py            # Dizinler ve ayar yöneticisi
│   ├── diarizer.py          # Akustik ve Pyannote konuşmacı ayrıştırma motoru
│   ├── exporter.py          # TXT, SRT, VTT, JSON, CSV ve Markdown dışa aktarıcılar
│   ├── text_postprocessor.py# Türkçe karakter, noktalama ve halüsinasyon filtresi
│   ├── transcriber.py       # CTranslate2 optimize Faster-Whisper motoru
│   ├── youtube_downloader.py# yt-dlp tabanlı YouTube ses indirici
│   └── ui/
│       ├── app.py           # Minimalist CustomTkinter masaüstü arayüzü
│       ├── components.py    # Sade kartlar, stepper, metrikler, ses oynatıcı ve diyaloglar
│       └── style.py         # Tasarım tokenleri, renk paletleri ve tema sistemi
└── tests/                   # Kapsamlı birim ve entegrasyon testleri
```

---

## Testleri Çalıştırma

Tüm test paketini çalıştırmak için:
```powershell
.\venv\Scripts\python.exe -m unittest discover tests
```

---

## Lisans

Bu proje MIT lisansı ile lisanslanmıştır.
Repo Adresi: `https://github.com/The0Sanity/Speech-To-Text.git`
