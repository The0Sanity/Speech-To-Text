# SesMetin Pro - Türkçe Ses Tanıma ve Konuşmacı Ayrıştırma (STT + Diarization)

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![UI: Flet Desktop](https://img.shields.io/badge/UI-Flet%20Flutter%20Native-0078d4.svg)](https://flet.dev)
[![GitHub Repo](https://img.shields.io/badge/GitHub-The0Sanity%2FSpeech--To--Text-success.svg)](https://github.com/The0Sanity/Speech-To-Text.git)

MP4 ve MP3 (ve diğer tüm video/ses) dosyalarınızı **tamamen yerel (offline)** olarak Türkçe metne dönüştüren, ortamdaki farklı konuşmacıları otomatik tespit edip **"X1", "X2"** şeklinde etiketleyen, Flet ve Flutter motoruyla çalışan modern, minimalist bir masaüstü uygulamasıdır.

Intel Core i3 CPU ve 8 GB RAM gibi standart donanımlarda yüksek performans ve düşük bellek tüketimi için **CPU INT8 (CTranslate2)** optimizasyonuna sahiptir.

---

## Temel Özellikler

- **Modern Flet Masaüstü Arayüzü:**
  - **Windows 11 Fluent Dark Tasarım:** Flutter GPU donanım hızlandırmalı 60 FPS akıcı render.
  - **Sıfır Emoji İlkesi:** Kurumsal, sade ve profesyonel tipografi ve simgeler.
  - **Salt Tıklanabilir Açılır Menüler:** Model, dil, VAD ve konuşmacı açılır menüleri yalnızca tıklanabilir, elle yazmaya kapalıdır.
  - **Duyarlı ve Akıllı Pencere Düzeni:** Minimum 960x640 boyut garantisi, otomatik ekran ortalama ve yumuşak açılış geçişi.
  - **Çok Adımlı İlerleme Göstergesi (Process Stepper):** 5 aşamalı boru hattını (Medya Hazırlığı, İyileştirme, Whisper STT, Konuşmacı Ayrımı, Hizalama) canlı izleme.
  - **Canlı Metrik Şeridi (Stats Ribbon):** Toplam konuşma süresi, konuşmacı sayısı, toplam kelime adedi ve WPM (dakika başına kelime) göstergeleri.
  - **Entegre Ses Oynatıcı Barı (Audio Player Bar):** Yüklenen veya indirilen ses dosyasını arayüzden doğrudan dinleme, duraklatma ve zaman kontrolü.
- **Gelişmiş Transkript Düzenleme:**
  - **Canlı Arama ve Filtreleme:** Metin veya konuşmacıya göre anında eşleşme sayımı ve süzme.
  - **Bul ve Değiştir (Find & Replace):** Transkript genelinde kelimeleri topluca tek tıkla değiştirme.
  - **Konuşmacı Yönetim Paneli (Speaker Manager):** Konuşmacı isimlerini tek ekrandan kolayca güncelleme.
  - **Hızlı Segment Kopyalama:** Her konuşma kartındaki kopyalama butonu ve bildirim balonları.
- **Kapsamlı Dışa Aktarım Desteği (6 Format):**
  - **`.txt`**: Zaman damgalı, temiz ve okunabilir transkript raporu.
  - **`.srt`**: Standart video oynatıcılar ve YouTube için altyazı.
  - **`.vtt`**: Modern web oynatıcıları ve HTML5 `<track>` için WebVTT altyazısı.
  - **`.json`**: Detaylı zamanlama ve kelime analizi içeren tam meta veri JSON'ı.
  - **`.csv`**: Excel / Sheets uyumlu tablolu döküm.
  - **`.md`**: Obsidian, Notion ve GitHub uyumlu sade Markdown belgesi.
  - **Panoya Kopyala**: Biçimlendirilmiş tek tıkla pano aktarımı.
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
- Sanal ortam (`venv`) ve gerekli kütüphaneler (`flet`, `faster_whisper` vb.) yoksa arka planda otomatik olarak kurulur.
- Bağımlılıklar zaten yüklüyse doğrudan modern Flet uygulaması başlatılır. Manuel ortam (`env`) yapılandırma gereksinimi kaldırılmıştır.

> [!NOTE]
> **Windows Defender SmartScreen ve Güvenlik Bildirimi:**
> Açık kaynaklı ve bağımsız `.exe` yayınlarında Windows ilk açılışta *"Windows kişisel bilgisayarınızı korudu"* ekranı gösterebilir. Bu bilinen standart bir Windows koruma uyarısıdır. Uygulamayı başlatmak için **"Ek bilgi" (More info)** bağlantısına tıklayıp **"Yine de çalıştır" (Run anyway)** butonunu seçebilirsiniz. Uygulama UPX sıkıştırmasından arındırılmış, tam PE sürüm meta verileriyle donatılmış ve Authenticode ile dijital olarak imzalanmıştır.

### 2. Komut Satırından Başlatma
PowerShell veya Terminal üzerinden:
```powershell
.\run.bat
```
veya doğrudan Python ile:
```powershell
python main.py
```
*(Gerek duyulursa `--gui=tk` parametresi ile CustomTkinter arayüzü de çalıştırılabilir).*

---

## Kurulum ve Sistem Gereksinimleri

- **Python:** 3.10 veya üzeri.
- **FFmpeg:** Ses ve video dönüştürmeleri için sistemde FFmpeg bulunmalıdır. Kurulu değilse:
  ```powershell
  winget install Gyan.FFmpeg.Shared
  ```

---

## Proje Mimarisi

```
Speech-To-Text/
├── main.py                  # Uygulama giriş noktası ve UI başlatıcı
├── settings.json            # Kullanıcı tercihleri ve yapılandırma
├── requirements.txt         # Bağımlılık listesi (Flet, Faster-Whisper vb.)
├── run.bat                  # Tek tıkla otomatik bağımlılık kontrolü ve başlatma betiği
├── docs/                    # Proje belgeleri ve mimari planları
│   ├── NEXT_VERSIONS_ROADMAP.md # Gelecek surumler ve sifir kurulum mimari yol haritasi
│   ├── PRODUCT.md           # Ürün ve tasarım manifestosu
│   └── turkish_stt_diarization_plan.md # Mimari planlama dokümanı
├── src/
│   ├── aligner.py           # Metin-konuşmacı hizalama, istatistik ve arama motoru
│   ├── audio_enhancer.py    # Gürültü filtresi, 80Hz yüksek geçiren filtre ve normalizasyon
│   ├── audio_processor.py   # FFmpeg ses ayrıştırma ve medya analizleri
│   ├── bootstrapper.py      # Otomatik bagimlilik ve FFmpeg kurulum yoneticisi
│   ├── config.py            # Dizinler, kalici kayit ve ayar yoneticisi
│   ├── diarizer.py          # Akustik ve Pyannote konuşmacı ayrıştırma motoru
│   ├── exporter.py          # TXT, SRT, VTT, JSON, CSV ve Markdown dışa aktarıcılar
│   ├── text_postprocessor.py# Türkçe karakter, noktalama ve halüsinasyon filtresi
│   ├── transcriber.py       # CTranslate2 optimize Faster-Whisper motoru
│   ├── updater.py           # Otomatik guncelleme motoru (GitHub Releases)
│   ├── youtube_downloader.py# yt-dlp tabanlı YouTube ses indirici
│   └── ui/                  # Modern Flet Masaustu Arayuzu
│       ├── app.py           # Ana uygulama penceresi, kontroller ve boru hattı bağlantısı
│       ├── components.py    # MetricCard, ProcessStepper, AudioPlayerBar, TurnCard
│       ├── style.py         # Tema tokenleri ve palet
│       └── theme.py         # Windows 11 Fluent dark renk paleti ve konuşmacı renkleri
└── tests/                   # Kapsamlı birim ve entegrasyon testleri
```

---

## Testleri Çalıştırma

Tüm test paketini çalıştırmak için:
```powershell
.\venv\Scripts\python.exe -m unittest discover tests
```

---

## Lisans ve Görsel Atıf Şartı (License & Visual Attribution)

Bu proje MIT Lisansı ve Zorunlu Görsel Atıf Şartı (MIT License with Prominent Visual Attribution Requirement) altında lisanslanmıştır.

**Zorunlu Görsel Atıf Kuralı:**
Bu projenin kaynak kodunu, bileşenlerini veya türevlerini kullanan tüm kişi ve kuruluşlar, kendi uygulamalarının veya kullanıcı arayüzlerinin **ana ekranında/üst menü çubuğunda** doğrudan görülebilecek şekilde bu depoya (`https://github.com/The0Sanity/Speech-To-Text`) tıklanabilir görsel bir atıf (link/badge) yerleştirmekle yükümlüdür. Bu atfı alt menülere, ayarlara veya görünmeyen köşelere gizlemek kesinlikle yasaktır.

Detaylar için [LICENSE](LICENSE) belgesini inceleyiniz.
Repo Adresi: `https://github.com/The0Sanity/Speech-To-Text`

